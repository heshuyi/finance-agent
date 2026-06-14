"""Ashare A 股行情备选源（新浪/腾讯双内核）。"""

from __future__ import annotations

from typing import Any

from tools.market.vendor.Ashare import get_price
from tools.symbols import ResolvedSymbol, to_ashare_code


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_ashare_market(resolved: ResolvedSymbol, *, count: int = 5) -> dict[str, Any]:
    code = to_ashare_code(resolved)
    df = get_price(code, frequency="1d", count=count)
    if df is None or df.empty:
        raise RuntimeError("Ashare 未返回行情数据")

    latest = df.tail(1).iloc[0]
    prev = df.tail(2).head(1).iloc[0] if len(df) >= 2 else latest
    close = _safe_float(latest.get("close"))
    prev_close = _safe_float(prev.get("close"))
    change_pct = None
    if close is not None and prev_close:
        change_pct = round((close - prev_close) / prev_close * 100, 2)

    kline_preview = []
    for idx, row in df.tail(3).iterrows():
        kline_preview.append(
            {
                "date": str(idx),
                "o": _safe_float(row.get("open")),
                "h": _safe_float(row.get("high")),
                "l": _safe_float(row.get("low")),
                "c": _safe_float(row.get("close")),
                "v": _safe_float(row.get("volume")),
            }
        )

    return {
        "symbol": resolved.code,
        "symbol_name": resolved.name or resolved.code,
        "region": resolved.region,
        "price": close,
        "daily_change_pct": change_pct,
        "volume": _safe_float(latest.get("volume")),
        "trade_date": str(df.tail(1).index[0]),
        "kline_preview": kline_preview,
        "source": "Ashare",
        "mode": "live",
        "api_refs": {"kline": "get_price(frequency=1d)"},
    }
