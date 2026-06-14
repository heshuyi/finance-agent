"""巨潮资讯公告爬虫 Tool。"""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from typing import Any

import httpx

from agents.shared.artifact import now_iso
from tools.cache import fetch_with_cache
from tools.news.crawler.base import CRAWLER_ENABLED, crawler_client
from tools.symbols import ResolvedSymbol, resolve_a_share
from tools.types import ToolResult

CNINFO_QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STOCK_LIST_URL = "http://www.cninfo.com.cn/new/data/szse_stock.json"
CNINFO_PDF_BASE = "http://static.cninfo.com.cn/"


@lru_cache(maxsize=1)
def _load_cninfo_stock_index() -> dict[str, dict[str, str]]:
    try:
        with crawler_client() as client:
            response = client.get(CNINFO_STOCK_LIST_URL)
        if response.status_code != 200:
            return {}
        data = json.loads(response.content.decode("utf-8", errors="ignore"))
        stocks = data.get("stockList") or []
        return {
            str(item.get("code")): {
                "org_id": item.get("orgId", ""),
                "name": item.get("zwjc", ""),
            }
            for item in stocks
            if item.get("code")
        }
    except Exception:
        return {}


def _cninfo_column(resolved: ResolvedSymbol) -> str:
    return "sse" if resolved.region == "SH" else "szse"


def _cninfo_stock_param(resolved: ResolvedSymbol) -> str:
    index = _load_cninfo_stock_index()
    meta = index.get(resolved.code) or {}
    org_id = meta.get("org_id") or ""
    if org_id:
        return f"{resolved.code},{org_id}"
    return f"{resolved.code},"


def _format_announcement_time(ms: int | None) -> str | None:
    if not ms:
        return None
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _fetch_live_filings(symbol: str, symbol_name: str, *, limit: int) -> ToolResult:
    if not CRAWLER_ENABLED:
        return ToolResult.success({"items": [], "mode": "disabled"}, source="CNINFO")

    resolved = resolve_a_share(symbol, symbol_name)
    end = date.today()
    start = end - timedelta(days=90)
    payload = {
        "pageNum": 1,
        "pageSize": str(limit),
        "column": _cninfo_column(resolved),
        "tabName": "fulltext",
        "stock": _cninfo_stock_param(resolved),
        "searchkey": "",
        "plate": "",
        "category": "",
        "trade": "",
        "seDate": f"{start.isoformat()}~{end.isoformat()}",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FinTeamBot/1.0)",
        "Referer": "https://www.cninfo.com.cn/",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
            response = client.post(CNINFO_QUERY_URL, data=payload)
    except httpx.HTTPError as exc:
        return ToolResult.failure("CNINFO_NETWORK", str(exc), source="CNINFO")

    if response.status_code != 200:
        return ToolResult.failure("CNINFO_HTTP", f"HTTP {response.status_code}", source="CNINFO")

    body = response.json()
    raw = body.get("announcements") or []
    items = []
    for row in raw[:limit]:
        if row.get("secCode") != resolved.code:
            continue
        adjunct = row.get("adjunctUrl") or ""
        items.append(
            {
                "title": row.get("announcementTitle", ""),
                "sec_name": row.get("secName", ""),
                "published_at": _format_announcement_time(row.get("announcementTime")),
                "url": f"{CNINFO_PDF_BASE}{adjunct}" if adjunct else "",
                "adjunct_type": row.get("adjunctType", ""),
                "source": "巨潮资讯",
                "channel": "cninfo",
            }
        )

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name,
            "items": items,
            "mode": "live",
            "source": "CNINFO",
        },
        source="CNINFO",
        fetched_at=now_iso(),
    )


def fetch_filings(symbol: str, symbol_name: str = "", *, limit: int = 10) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="filings",
        symbol=resolved.code,
        suffix=f"limit={limit}",
        source="CNINFO",
        fetcher=lambda: _fetch_live_filings(resolved.code, resolved.name, limit=limit),
    )
