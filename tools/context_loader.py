"""为 Agent 节点加载投研分析上下文（行情/财报/资讯/公告）。"""

from __future__ import annotations

from tools.ai_context import build_analysis_context
from tools.filings.cninfo import fetch_filings
from tools.financials.info import fetch_financials
from tools.market.bundle import fetch_market_bundle
from tools.news.feed import fetch_news_feed


def load_analysis_context(
    symbol: str,
    symbol_name: str = "",
    *,
    limit: int = 5,
    include_filings: bool = True,
    include_news: bool = True,
) -> str:
    """拉取多源数据并格式化为 LLM 分析上下文。"""
    market = fetch_market_bundle(symbol, symbol_name)
    financials = fetch_financials(symbol, symbol_name)
    news = fetch_news_feed(symbol, symbol_name=symbol_name, limit=limit) if include_news else None
    filings = fetch_filings(symbol, symbol_name, limit=limit) if include_filings else None

    name = (
        market.data.get("symbol_name")
        or financials.data.get("symbol_name")
        or symbol_name
        or symbol
    )
    return build_analysis_context(
        market=market.data if market.ok else None,
        financials=financials.data if financials.ok else None,
        news=news.data if news and news.ok else None,
        filings=filings.data if filings and filings.ok else None,
        symbol=symbol,
        symbol_name=name,
    )
