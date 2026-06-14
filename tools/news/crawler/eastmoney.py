"""东方财富个股资讯爬虫。"""

from __future__ import annotations

import re
from typing import Any

import httpx

from agents.shared.artifact import now_iso
from tools.news.crawler.base import CRAWLER_ENABLED, DIGEST_LIMIT, FETCH_DIGEST, crawler_client
from tools.news.merge import normalize_item
from tools.symbols import ResolvedSymbol, resolve_a_share
from tools.types import ToolResult

EASTMONEY_LIST_URL = "https://np-listapi.eastmoney.com/comm/wap/getListInfo"


def _eastmoney_market_code(resolved: ResolvedSymbol) -> str:
    market = "1" if resolved.region == "SH" else "0"
    return f"{market}.{resolved.code}"


def _fetch_article_digest(client: httpx.Client, url: str) -> str:
    if not url:
        return ""
    try:
        response = client.get(url)
    except httpx.HTTPError:
        return ""
    if response.status_code != 200:
        return ""
    match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', response.text)
    if not match:
        return ""
    return match.group(1).strip()[:400]


def crawl_eastmoney_stock_news(
    symbol: str,
    symbol_name: str = "",
    *,
    limit: int = 10,
) -> ToolResult:
    """
    爬取东方财富个股相关新闻列表。

    接口来源：个股资讯列表 JSON API（非浏览器模拟），字段含标题、媒体、发布时间、原文链接。
    可选抓取文章页 meta description 作为摘要。
    """
    if not CRAWLER_ENABLED:
        return ToolResult.success(
            {"items": [], "mode": "disabled"},
            source="EastMoney",
        )

    resolved = resolve_a_share(symbol, symbol_name)
    params = {
        "client": "wap",
        "type": "1",
        "pageSize": str(limit),
        "pageIndex": "1",
        "mTypeAndCode": _eastmoney_market_code(resolved),
    }

    try:
        with crawler_client() as client:
            client.headers["Referer"] = "https://finance.eastmoney.com/"
            response = client.get(EASTMONEY_LIST_URL, params=params)
    except Exception as exc:  # httpx + network
        return ToolResult.failure("EASTMONEY_NETWORK", str(exc), source="EastMoney")

    if response.status_code != 200:
        return ToolResult.failure(
            "EASTMONEY_HTTP",
            f"HTTP {response.status_code}",
            source="EastMoney",
        )

    payload = response.json()
    if payload.get("code") != 1:
        return ToolResult.failure(
            "EASTMONEY_API",
            str(payload.get("message") or payload),
            source="EastMoney",
        )

    raw_list: list[dict[str, Any]] = (payload.get("data") or {}).get("list") or []
    items: list[dict[str, Any]] = []

    with crawler_client() as client:
        client.headers["Referer"] = "https://finance.eastmoney.com/"
        for idx, row in enumerate(raw_list[:limit]):
            url = row.get("Art_Url") or row.get("Art_OriginUrl") or ""
            summary = ""
            if FETCH_DIGEST and idx < DIGEST_LIMIT and url:
                summary = _fetch_article_digest(client, url)

            items.append(
                normalize_item(
                    headline=row.get("Art_Title", ""),
                    summary=summary,
                    source=row.get("Art_MediaName") or "东方财富",
                    url=url,
                    published_at=row.get("Art_ShowTime"),
                    channel="eastmoney",
                )
            )

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name,
            "items": items,
            "mode": "live",
            "crawler": "eastmoney",
        },
        source="EastMoney",
        fetched_at=now_iso(),
    )
