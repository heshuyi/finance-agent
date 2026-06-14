"""DataCollectorAgent — 通过 tools 层拉取行情、财报、资讯、公告。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim
from tools.filings.cninfo import fetch_filings
from tools.financials.info import fetch_financials
from tools.market.bundle import fetch_market_bundle
from tools.news.feed import fetch_news_feed
from tools.ai_context import build_analysis_context


def _cache_note(data: dict) -> str:
    if data.get("_from_cache"):
        return "（本地缓存）"
    return ""


def run_data_collector(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol = payload.get("symbol") or "600519"
    symbol_name = payload.get("symbol_name") or ""

    market = fetch_market_bundle(symbol, symbol_name)
    financials = fetch_financials(symbol, symbol_name)
    news = fetch_news_feed(symbol, symbol_name=symbol_name, limit=5)
    filings = fetch_filings(symbol, symbol_name, limit=5)

    bundle = market.data
    fin = financials.data
    symbol = bundle.get("symbol") or fin.get("symbol") or symbol
    symbol_name = bundle.get("symbol_name") or fin.get("symbol_name") or symbol_name or symbol
    source_name = bundle.get("source", "FinTeam Connector")
    mode = bundle.get("mode", "unknown")
    api_url = "https://api.itick.org" if mode == "live" and source_name == "iTick" else None
    cache_suffix = _cache_note(bundle)

    claims = []
    errors = []

    if bundle.get("price") is not None:
        claims.append(
            make_claim(
                f"{symbol_name}（{symbol}）最新价 {bundle['price']} 元{cache_suffix}",
                source_type="market_data",
                source_name=source_name,
                excerpt=f"price={bundle['price']}",
                url=api_url,
            )
        )

    pe = fin.get("pe_ttm") or bundle.get("pe_ttm")
    if pe is not None:
        claims.append(
            make_claim(
                f"{symbol_name}（{symbol}）当前 PE-TTM 为 {round(float(pe), 2)}{_cache_note(fin)}",
                source_type="financial_report",
                source_name=fin.get("source", source_name),
                excerpt=f"PE_TTM={pe}",
                url=api_url,
            )
        )

    if fin.get("market_cap") is not None:
        claims.append(
            make_claim(
                f"{symbol_name} 总市值约 {fin['market_cap']}{_cache_note(fin)}",
                source_type="financial_report",
                source_name=fin.get("source", source_name),
                excerpt=f"market_cap={fin['market_cap']}",
            )
        )

    if bundle.get("daily_change_pct") is not None:
        claims.append(
            make_claim(
                f"{symbol_name} 最新交易日涨跌幅约 {bundle['daily_change_pct']}%{cache_suffix}",
                source_type="market_data",
                source_name=source_name,
                excerpt=f"daily_change_pct={bundle['daily_change_pct']}",
                url=api_url,
            )
        )

    if mode == "mock":
        claims.append(
            make_claim(
                f"{symbol_name} 近五年 PE 分位约 72%（mock 估算）",
                source_type="model_inference",
                verified=False,
                source_name="FinTeam 模型估算",
            )
        )

    for tool_result in (market, financials, news, filings):
        if not tool_result.ok:
            for err in tool_result.errors:
                errors.append({"code": err.code, "message": err.message, "source": err.source})

    news_items = news.data.get("items") or []
    for item in news_items[:3]:
        claims.append(
            make_claim(
                item.get("headline", ""),
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
                excerpt=item.get("sec_name", ""),
                url=item.get("url"),
            )
        )

    if not news_items and news.data.get("hint"):
        errors.append(
            {
                "code": "NEWS_EMPTY",
                "message": news.data.get("hint", "未获取到资讯"),
                "source": "NewsAggregator",
            }
        )

    confidence = 0.85 if mode == "live" else 0.7 if mode == "mock" else 0.5

    ai_context = build_analysis_context(
        market=bundle,
        financials=fin,
        news=news.data,
        filings=filings.data,
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
            "market_from_cache": bundle.get("_from_cache", False),
            "financials_from_cache": fin.get("_from_cache", False),
            "fetched_at": market.fetched_at,
            "news_count": len(news_items),
            "news_mode": news.data.get("mode"),
            "news_sources": news.data.get("sources", []),
            "news_from_cache": news.data.get("_from_cache", False),
            "filings_count": len(filing_items),
            "filings_from_cache": filings.data.get("_from_cache", False),
            "ai_context": ai_context,
        },
    )
