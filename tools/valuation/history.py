"""AKShare 估值历史序列与分位。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from tools.cache import fetch_with_cache
from tools.symbols import resolve_a_share
from tools.types import ToolResult
from tools.valuation.percentile import compute_percentile, sample_series


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _fetch_live_valuation(symbol: str, symbol_name: str, *, days: int = 365) -> ToolResult:
    import akshare as ak

    resolved = resolve_a_share(symbol, symbol_name)
    try:
        df = ak.stock_value_em(symbol=resolved.code)
    except Exception as exc:
        return ToolResult.failure("AKSHARE_VALUATION", str(exc), source="AKShare")

    if df is None or df.empty:
        return ToolResult.failure("AKSHARE_EMPTY", "估值历史为空", source="AKShare")

    date_col = "数据日期"
    if date_col not in df.columns:
        return ToolResult.failure("AKSHARE_SCHEMA", "缺少数据日期列", source="AKShare")

    cutoff = datetime.now() - timedelta(days=days)
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        trade_date = str(row.get(date_col, ""))
        try:
            dt = datetime.strptime(trade_date[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if dt < cutoff:
            continue
        pe = _safe_float(row.get("PE(TTM)"))
        pb = _safe_float(row.get("市净率"))
        rows.append(
            {
                "trade_date": trade_date[:10],
                "pe_ttm": pe,
                "pb": pb,
                "close": _safe_float(row.get("当日收盘价")),
            }
        )

    if not rows:
        return ToolResult.failure("AKSHARE_RANGE", f"近 {days} 日无估值数据", source="AKShare")

    latest = rows[-1]
    pe_series = [r["pe_ttm"] for r in rows if r.get("pe_ttm") is not None]
    pb_series = [r["pb"] for r in rows if r.get("pb") is not None]

    pe_pct = compute_percentile(pe_series, latest.get("pe_ttm"))
    pb_pct = compute_percentile(pb_series, latest.get("pb"))

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name or resolved.code,
            "source": "AKShare",
            "mode": "live",
            "api_ref": "stock_value_em",
            "days": days,
            "sample_count": len(rows),
            "latest": latest,
            "pe_percentile_1y": pe_pct,
            "pb_percentile_1y": pb_pct,
            "series_sample": sample_series(rows, "pe_ttm"),
            "pe_series": pe_series,
            "pb_series": pb_series,
        },
        source="AKShare",
    )


def fetch_valuation_history(
    symbol: str,
    symbol_name: str = "",
    *,
    days: int = 365,
) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="valuation",
        symbol=resolved.code,
        suffix=f"days={days}",
        source="AKShare",
        fetcher=lambda: _fetch_live_valuation(resolved.code, resolved.name or symbol_name, days=days),
    )
