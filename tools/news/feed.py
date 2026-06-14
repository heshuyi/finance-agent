"""资讯聚合 — 爬虫 + API 多源合并（带本地缓存）。"""

from __future__ import annotations

from agents.shared.artifact import now_iso
from tools.cache import fetch_with_cache
from tools.news.crawler.eastmoney import crawl_eastmoney_stock_news
from tools.news.finnhub import fetch_finnhub_news
from tools.news.merge import merge_news_items
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def _fetch_live_news(symbol: str, symbol_name: str, *, limit: int) -> ToolResult:
    errors = []
    sources: list[str] = []

    crawled = crawl_eastmoney_stock_news(symbol, symbol_name, limit=limit)
    if crawled.ok:
        crawler_items = crawled.data.get("items") or []
        if crawler_items:
            sources.append("EastMoney")
    else:
        errors.extend(crawled.errors)
        crawler_items = []

    finnhub = fetch_finnhub_news(symbol, limit=limit)
    if finnhub.ok and finnhub.data.get("mode") == "live":
        finnhub_items = finnhub.data.get("items") or []
        if finnhub_items:
            sources.append("Finnhub")
    else:
        if not finnhub.ok:
            errors.extend(finnhub.errors)
        finnhub_items = []

    items = merge_news_items(crawler_items, finnhub_items, limit=limit)

    if items:
        mode = "live"
        hint = None
    else:
        mode = "empty"
        hint = (
            "未获取到新闻：可检查网络或开启 NEWS_CRAWLER_ENABLED；"
            "亦可配置 FINNHUB_API_KEY 作为补充源"
        )

    result = ToolResult.success(
        {
            "symbol": symbol,
            "items": items,
            "sources": sources,
            "source": "+".join(sources) if sources else "none",
            "mode": mode,
            "hint": hint,
            "crawler_count": len(crawler_items),
            "api_count": len(finnhub_items),
        },
        source="+".join(sources) if sources else "NewsAggregator",
        fetched_at=now_iso(),
    )
    result.errors = errors
    return result


def fetch_news_feed(
    symbol: str,
    *,
    symbol_name: str = "",
    limit: int = 10,
) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="news",
        symbol=resolved.code,
        suffix=f"limit={limit}",
        source="NewsAggregator",
        fetcher=lambda: _fetch_live_news(resolved.code, resolved.name, limit=limit),
    )
