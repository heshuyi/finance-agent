"""行情类 Tool — AKShare / Ashare 免费 A 股接口（带本地缓存）。"""

from __future__ import annotations

from tools.cache import fetch_with_cache
from tools.market.a_share import fetch_a_share_market
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def fetch_market_bundle(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="market",
        symbol=resolved.code,
        source="AKShare",
        fetcher=lambda: fetch_a_share_market(resolved.code, resolved.name),
    )
