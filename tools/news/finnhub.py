"""Finnhub 公司新闻 API。"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import httpx

from agents.shared.artifact import now_iso
from tools.news.merge import normalize_item
from tools.symbols import resolve_a_share
from tools.types import ToolResult

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")


def _map_symbol_to_finnhub(symbol: str) -> str:
    resolved = resolve_a_share(symbol)
    suffix = "SS" if resolved.region == "SH" else "SZ"
    return f"{resolved.code}.{suffix}"


def fetch_finnhub_news(symbol: str, *, limit: int = 10) -> ToolResult:
    if not FINNHUB_API_KEY:
        return ToolResult.success(
            {"items": [], "mode": "unconfigured"},
            source="Finnhub",
        )

    ticker = _map_symbol_to_finnhub(symbol)
    today = date.today().isoformat()
    params = {
        "symbol": ticker,
        "from": "2025-01-01",
        "to": today,
        "token": FINNHUB_API_KEY,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(f"{FINNHUB_BASE_URL}/company-news", params=params)
    except httpx.HTTPError as exc:
        return ToolResult.failure("FINNHUB_NETWORK", str(exc), source="Finnhub")

    if response.status_code != 200:
        return ToolResult.failure(
            "FINNHUB_HTTP",
            f"HTTP {response.status_code}",
            source="Finnhub",
        )

    raw: list[dict[str, Any]] = response.json()
    items = [
        normalize_item(
            headline=item.get("headline", ""),
            summary=item.get("summary", ""),
            source=item.get("source", "Finnhub"),
            url=item.get("url", ""),
            published_at=item.get("datetime"),
            channel="finnhub",
        )
        for item in raw[:limit]
        if item.get("headline")
    ]

    return ToolResult.success(
        {"symbol": symbol, "ticker": ticker, "items": items, "mode": "live"},
        source="Finnhub",
        fetched_at=now_iso(),
    )
