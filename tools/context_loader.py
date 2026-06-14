"""为 Agent 节点加载投研分析上下文（行情/财报/资讯/公告/估值/同业）。"""

from __future__ import annotations

from typing import Any

from tools.ai_context import build_analysis_context
from tools.filings.cninfo import fetch_filings
from tools.filings.summary import summarize_filing_titles
from tools.financials.indicators import fetch_financial_indicators
from tools.financials.info import fetch_financials
from tools.market.bundle import fetch_market_bundle
from tools.news.feed import fetch_news_feed
from tools.peers.compare import fetch_peer_comparison
from tools.valuation.history import fetch_valuation_history


def load_analysis_context(
    symbol: str,
    symbol_name: str = "",
    *,
    limit: int = 5,
    include_filings: bool = True,
    include_news: bool = True,
    include_valuation: bool = True,
    include_indicators: bool = True,
    include_peers: bool = True,
    position: dict[str, Any] | None = None,
) -> str:
    """拉取多源数据并格式化为 LLM 分析上下文。"""
    market = fetch_market_bundle(symbol, symbol_name)
    financials = fetch_financials(symbol, symbol_name)
    valuation = fetch_valuation_history(symbol, symbol_name) if include_valuation else None
    indicators = fetch_financial_indicators(symbol, symbol_name) if include_indicators else None
    peers = fetch_peer_comparison(symbol, symbol_name) if include_peers else None
    news = fetch_news_feed(symbol, symbol_name=symbol_name, limit=limit) if include_news else None
    filings = fetch_filings(symbol, symbol_name, limit=limit) if include_filings else None

    name = (
        market.data.get("symbol_name")
        or financials.data.get("symbol_name")
        or symbol_name
        or symbol
    )

    filings_data = filings.data if filings and filings.ok else None
    if filings_data and filings_data.get("items"):
        filings_data = {
            **filings_data,
            "event_summary": summarize_filing_titles(
                name,
                filings_data.get("items") or [],
                max_items=limit,
            ),
        }

    pos = dict(position) if position else None
    if pos and market.ok and market.data.get("price") is not None:
        pos["current_price"] = market.data.get("price")
        cost = pos.get("cost_price")
        if cost is not None:
            try:
                pos["profit_pct"] = round(
                    (float(pos["current_price"]) - float(cost)) / float(cost) * 100,
                    2,
                )
            except (TypeError, ValueError, ZeroDivisionError):
                pass

    return build_analysis_context(
        market=market.data if market.ok else None,
        financials=financials.data if financials.ok else None,
        news=news.data if news and news.ok else None,
        filings=filings_data,
        valuation=valuation.data if valuation and valuation.ok else None,
        indicators=indicators.data if indicators and indicators.ok else None,
        peers=peers.data if peers and peers.ok else None,
        position=pos,
        symbol=symbol,
        symbol_name=name,
    )
