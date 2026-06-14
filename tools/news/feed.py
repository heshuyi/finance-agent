"""资讯聚合 — 授权 API 优先，公开列表接口可选（带本地缓存）。"""

from __future__ import annotations

from agents.shared.artifact import now_iso
from tools.cache import fetch_with_cache
from tools.news.crawler.base import NEWS_FETCH_ENABLED
from tools.news.crawler.eastmoney import fetch_eastmoney_stock_news
from tools.news.finnhub import fetch_finnhub_news
from tools.news.merge import merge_news_items
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def _fetch_live_news(symbol: str, symbol_name: str, *, limit: int) -> ToolResult:
    errors: list = []
    sources: list[str] = []

    finnhub = fetch_finnhub_news(symbol, limit=limit)
    if finnhub.ok and finnhub.data.get("mode") == "live":
        finnhub_items = finnhub.data.get("items") or []
        if finnhub_items:
            sources.append("Finnhub")
    else:
        if not finnhub.ok:
            errors.extend(finnhub.errors)
        finnhub_items = []

    public_items: list = []
    if NEWS_FETCH_ENABLED:
        public = fetch_eastmoney_stock_news(symbol, symbol_name, limit=limit)
        if public.ok:
            public_items = public.data.get("items") or []
            if public_items:
                sources.append("EastMoney")
        else:
            errors.extend(public.errors)

    items = merge_news_items(public_items, finnhub_items, limit=limit)

    if items:
        mode = "live"
        hint = None
    else:
        mode = "empty"
        hint = (
            "未获取到资讯：建议配置 FINNHUB_API_KEY（授权 API）；"
            "或在确认合规前提下设置 NEWS_FETCH_ENABLED=true 启用东方财富公开列表接口"
        )

    result = ToolResult.success(
        {
            "symbol": symbol,
            "items": items,
            "sources": sources,
            "source": "+".join(sources) if sources else "none",
            "mode": mode,
            "hint": hint,
            "public_api_count": len(public_items),
            "licensed_api_count": len(finnhub_items),
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
