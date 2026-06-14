"""DataCollectorAgent — 通过 tools 层拉取行情、财报、资讯、公告、估值、同业。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim
from tools.ai_context import build_analysis_context
from tools.filings.cninfo import fetch_filings
from tools.filings.summary import summarize_filing_titles
from tools.financials.indicators import fetch_financial_indicators
from tools.financials.info import fetch_financials
from tools.market.bundle import fetch_market_bundle
from tools.news.feed import fetch_news_feed
from tools.peers.compare import fetch_peer_comparison
from tools.valuation.history import fetch_valuation_history


def _cache_note(data: dict) -> str:
    if data.get("_from_cache"):
        return "（本地缓存）"
    return ""


def run_data_collector(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol = payload.get("symbol") or "600519"
    symbol_name = payload.get("symbol_name") or ""
    position = payload.get("position") or {}

    market = fetch_market_bundle(symbol, symbol_name)
    financials = fetch_financials(symbol, symbol_name)
    valuation = fetch_valuation_history(symbol, symbol_name)
    indicators = fetch_financial_indicators(symbol, symbol_name)
    peers = fetch_peer_comparison(symbol, symbol_name)
    news = fetch_news_feed(symbol, symbol_name=symbol_name, limit=5)
    filings = fetch_filings(symbol, symbol_name, limit=5)

    bundle = market.data
    fin = financials.data
    val = valuation.data if valuation.ok else {}
    symbol = bundle.get("symbol") or fin.get("symbol") or symbol
    symbol_name = bundle.get("symbol_name") or fin.get("symbol_name") or symbol_name or symbol
    source_name = bundle.get("source", "FinTeam Connector")
    mode = bundle.get("mode", "unknown")

    claims = []
    errors = []

    if bundle.get("price") is not None:
        claims.append(
            make_claim(
                f"{symbol_name}（{symbol}）最新价 {bundle['price']} 元{_cache_note(bundle)}",
                source_type="market_data",
                source_name=source_name,
                excerpt=f"price={bundle['price']}",
            )
        )

    pe = fin.get("pe_ttm") or bundle.get("pe_ttm") or (val.get("latest") or {}).get("pe_ttm")
    if pe is not None:
        claims.append(
            make_claim(
                f"{symbol_name}（{symbol}）当前 PE-TTM 为 {round(float(pe), 2)}{_cache_note(fin)}",
                source_type="financial_report",
                source_name=fin.get("source", source_name),
                excerpt=f"PE_TTM={pe}",
            )
        )

    pe_pct = val.get("pe_percentile_1y")
    if pe_pct is not None:
        claims.append(
            make_claim(
                f"{symbol_name} PE-TTM 近一年历史分位约 {pe_pct}%（AKShare 估值序列）",
                source_type="financial_report",
                source_name="AKShare",
                excerpt=f"pe_percentile_1y={pe_pct}",
            )
        )

    pb_pct = val.get("pb_percentile_1y")
    if pb_pct is not None:
        claims.append(
            make_claim(
                f"{symbol_name} PB 近一年历史分位约 {pb_pct}%",
                source_type="financial_report",
                source_name="AKShare",
                excerpt=f"pb_percentile_1y={pb_pct}",
            )
        )

    if fin.get("market_cap") is not None:
        claims.append(
            make_claim(
                f"{symbol_name} 总市值约 {fin['market_cap']}{_cache_note(fin)}",
                source_type="financial_report",
                source_name=fin.get("source", source_name),
            )
        )

    if bundle.get("daily_change_pct") is not None:
        claims.append(
            make_claim(
                f"{symbol_name} 最新交易日涨跌幅约 {bundle['daily_change_pct']}%",
                source_type="market_data",
                source_name=source_name,
            )
        )

    for h in (indicators.data.get("highlights") or [])[:2] if indicators.ok else []:
        claims.append(
            make_claim(h, source_type="financial_report", source_name="AKShare"),
        )

    peer_rows = peers.data.get("peers") or [] if peers.ok else []
    if peer_rows:
        peer_txt = "；".join(
            f"{p.get('symbol_name')} PE={p.get('pe_ttm', '-')}" for p in peer_rows[:3]
        )
        claims.append(
            make_claim(
                f"同业对比（{peers.data.get('industry', '')}）：{peer_txt}",
                source_type="financial_report",
                source_name="AKShare",
            )
        )

    for tool_result in (market, financials, valuation, indicators, peers, news, filings):
        if not tool_result.ok:
            for err in tool_result.errors:
                errors.append({"code": err.code, "message": err.message, "source": err.source})

    news_items = news.data.get("items") or []
    for item in news_items[:3]:
        claims.append(
            make_claim(
                item.get("headline", "") or item.get("title", ""),
                source_type="news",
                source_name=item.get("source") or news.data.get("source", "News"),
                excerpt=(item.get("summary") or "")[:200],
                url=item.get("url"),
            )
        )

    filing_items = filings.data.get("items") or []
    for item in filing_items[:3]:
        claims.append(
            make_claim(
                item.get("title", ""),
                source_type="filing",
                source_name=item.get("source", "巨潮资讯"),
                url=item.get("url"),
            )
        )

    filings_data = filings.data
    event_summary = ""
    if filing_items:
        event_summary = summarize_filing_titles(symbol_name, filing_items, max_items=5)
        filings_data = {**filings.data, "event_summary": event_summary}

    pos = dict(position)
    if pos and bundle.get("price") is not None:
        pos["current_price"] = bundle.get("price")
        if pos.get("cost_price") is not None:
            try:
                pos["profit_pct"] = round(
                    (float(pos["current_price"]) - float(pos["cost_price"]))
                    / float(pos["cost_price"])
                    * 100,
                    2,
                )
            except (TypeError, ValueError, ZeroDivisionError):
                pass

    confidence = 0.85 if mode == "live" else 0.7 if mode == "mock" else 0.5
    if val.get("pe_percentile_1y") is not None:
        confidence = min(0.92, confidence + 0.03)

    ai_context = build_analysis_context(
        market=bundle,
        financials=fin,
        news=news.data,
        filings=filings_data,
        valuation=val or None,
        indicators=indicators.data if indicators.ok else None,
        peers=peers.data if peers.ok else None,
        position=pos or None,
        symbol=symbol,
        symbol_name=symbol_name,
    )

    return make_artifact(
        task_id=task_id,
        agent_id="data_collector",
        artifact_type="DataBundle",
        claims=claims,
        confidence=confidence,
        errors=errors,
        metadata={
            "symbol": symbol,
            "symbol_name": symbol_name,
            "market_mode": mode,
            "market_source": source_name,
            "market_bundle": bundle,
            "financials_bundle": fin,
            "valuation": val,
            "indicators": indicators.data if indicators.ok else None,
            "peers": peers.data if peers.ok else None,
            "position": pos,
            "filing_event_summary": event_summary,
            "fetched_at": market.fetched_at,
            "news_count": len(news_items),
            "filings_count": len(filing_items),
            "ai_context": ai_context,
        },
    )
