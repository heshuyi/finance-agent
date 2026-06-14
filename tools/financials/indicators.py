"""AKShare 财务分析指标（营收/净利同比等）。"""

from __future__ import annotations

from typing import Any

from tools.cache import fetch_with_cache
from tools.symbols import resolve_a_share
from tools.types import ToolResult


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"false", "nan", "none", "--"}:
        return None
    return text


def _fetch_from_ths(resolved) -> tuple[list[dict[str, Any]], list[str], str]:
    import akshare as ak

    df = ak.stock_financial_abstract_ths(symbol=resolved.code)
    if df is None or df.empty:
        return [], [], "stock_financial_abstract_ths"

    recent = df.tail(4)
    periods: list[dict[str, Any]] = []
    highlights: list[str] = []

    for _, row in recent.iterrows():
        period = _clean(row.get("报告期")) or ""
        entry: dict[str, Any] = {"period": period}
        for col in row.index:
            val = _clean(row.get(col))
            if val:
                entry[str(col)] = val
        if len(entry) > 1:
            periods.append(entry)

    if periods:
        latest = periods[-1]
        mapping = [
            ("净利润", "净利润"),
            ("净利润同比增长率", "净利同比"),
            ("营业总收入", "营收"),
            ("营业总收入同比增长率", "营收同比"),
            ("基本每股收益", "EPS"),
        ]
        for src, label in mapping:
            val = latest.get(src)
            if val:
                highlights.append(f"{latest['period']} {label}: {val}")

    return periods, highlights[:6], "stock_financial_abstract_ths"


def _fetch_live_indicators(symbol: str, symbol_name: str) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    try:
        periods, highlights, api_ref = _fetch_from_ths(resolved)
    except Exception as exc:
        return ToolResult.failure("AKSHARE_INDICATORS", str(exc), source="AKShare")

    if not periods:
        return ToolResult.success(
            {
                "symbol": resolved.code,
                "symbol_name": resolved.name or symbol_name or resolved.code,
                "source": "AKShare",
                "mode": "empty",
                "api_ref": api_ref,
                "periods": [],
                "highlights": [],
                "hint": "暂无财务指标数据",
            },
            source="AKShare",
        )

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name or resolved.code,
            "source": "AKShare",
            "mode": "live",
            "api_ref": api_ref,
            "periods": periods,
            "highlights": highlights,
        },
        source="AKShare",
    )


def fetch_financial_indicators(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="indicators",
        symbol=resolved.code,
        suffix="ths-v2",
        source="AKShare",
        fetcher=lambda: _fetch_live_indicators(resolved.code, resolved.name or symbol_name),
    )
