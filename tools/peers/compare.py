"""同行业估值横向对比（AKShare 免费数据）。"""

from __future__ import annotations

from typing import Any

from tools.cache import fetch_with_cache
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _fetch_industry(resolved) -> str:
    import akshare as ak

    try:
        info = ak.stock_individual_info_em(symbol=resolved.code)
        if info is not None and not info.empty:
            row = info[info["item"] == "行业"]
            if not row.empty:
                return str(row.iloc[0]["value"]).strip()
    except Exception:
        pass
    return ""


def _fetch_live_peers(symbol: str, symbol_name: str, *, limit: int = 3) -> ToolResult:
    import akshare as ak

    resolved = resolve_a_share(symbol, symbol_name)
    industry = _fetch_industry(resolved)
    if not industry:
        return ToolResult.success(
            {
                "symbol": resolved.code,
                "symbol_name": resolved.name or symbol_name,
                "industry": "",
                "peers": [],
                "mode": "empty",
                "hint": "未能识别行业，跳过同业对比",
            },
            source="AKShare",
        )

    try:
        spot = ak.stock_zh_a_spot_em()
    except Exception as exc:
        return ToolResult.failure("AKSHARE_SPOT", str(exc), source="AKShare")

    peers: list[dict[str, Any]] = []
    for _, row in spot.iterrows():
        code = str(row.get("代码", "")).zfill(6)
        if code == resolved.code:
            continue
        name = str(row.get("名称", ""))
        pe = _safe_float(row.get("市盈率-动态"))
        pb = _safe_float(row.get("市净率"))
        ind = str(row.get("所属行业", "") or row.get("行业", "") or "")
        if industry and industry not in ind and ind not in industry:
            continue
        peers.append(
            {
                "symbol": code,
                "symbol_name": name,
                "pe_ttm": pe,
                "pb": pb,
                "industry": ind or industry,
            }
        )
        if len(peers) >= limit:
            break

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name,
            "industry": industry,
            "peers": peers,
            "mode": "live" if peers else "empty",
            "source": "AKShare",
            "api_ref": "stock_zh_a_spot_em",
        },
        source="AKShare",
    )


def fetch_peer_comparison(symbol: str, symbol_name: str = "", *, limit: int = 3) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="peers",
        symbol=resolved.code,
        suffix=f"limit={limit}",
        source="AKShare",
        fetcher=lambda: _fetch_live_peers(resolved.code, resolved.name or symbol_name, limit=limit),
    )
