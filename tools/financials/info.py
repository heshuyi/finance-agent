"""财报指标 Tool — AKShare 估值数据 + 本地缓存。"""

from __future__ import annotations

from tools.cache import fetch_with_cache
from tools.market.a_share import fetch_a_share_financials
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def fetch_financials(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="financials",
        symbol=resolved.code,
        source="AKShare",
        fetcher=lambda: fetch_a_share_financials(resolved.code, resolved.name),
    )
