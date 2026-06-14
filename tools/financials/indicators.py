"""AKShare 财务分析指标（营收/净利同比等）。"""

from __future__ import annotations

from typing import Any

from tools.cache import fetch_with_cache
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fetch_live_indicators(symbol: str, symbol_name: str) -> ToolResult:
    import akshare as ak

    resolved = resolve_a_share(symbol, symbol_name)
    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=resolved.code, indicator="主要指标")
    except Exception as exc:
        return ToolResult.failure("AKSHARE_INDICATORS", str(exc), source="AKShare")

    if df is None or df.empty:
        return ToolResult.failure("AKSHARE_INDICATORS_EMPTY", "财务指标为空", source="AKShare")

    # 取最近几期（列通常为报告期）
    periods: list[dict[str, Any]] = []
    for col in list(df.columns)[-4:]:
        row_data: dict[str, Any] = {"period": str(col)}
        for idx, metric in enumerate(df.index):
            if idx > 12:
                break
            val = df.loc[metric, col] if col in df.columns else None
            if val is not None and str(val) not in ("", "nan", "NaN"):
                row_data[str(metric)[:40]] = str(val)
        if len(row_data) > 1:
            periods.append(row_data)

    # 提取常用字段
    highlights: list[str] = []
    if periods:
        latest = periods[-1]
        for key in ("归母净利润", "营业总收入", "净利润", "每股收益"):
            for k, v in latest.items():
                if key in k and k != "period":
                    highlights.append(f"{latest['period']} {k}: {v}")
                    break

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name or resolved.code,
            "source": "AKShare",
            "mode": "live",
            "api_ref": "stock_financial_analysis_indicator_em",
            "periods": periods[-4:],
            "highlights": highlights[:6],
        },
        source="AKShare",
    )


def fetch_financial_indicators(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="indicators",
        symbol=resolved.code,
        source="AKShare",
        fetcher=lambda: _fetch_live_indicators(resolved.code, resolved.name or symbol_name),
    )
