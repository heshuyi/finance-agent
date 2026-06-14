"""AKShare A 股行情与估值数据。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from tools.symbols import ResolvedSymbol, to_akshare_daily_symbol


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_akshare_market(resolved: ResolvedSymbol) -> dict[str, Any]:
    import akshare as ak

    valuation = ak.stock_value_em(symbol=resolved.code)
    latest_val = valuation.tail(1).iloc[0]

    daily_symbol = to_akshare_daily_symbol(resolved)
    daily = ak.stock_zh_a_daily(symbol=daily_symbol)
    latest_daily = daily.tail(1).iloc[0]

    kline_preview = []
    for _, row in daily.tail(3).iterrows():
        kline_preview.append(
            {
                "date": str(row.get("date", "")),
                "o": _safe_float(row.get("open")),
                "h": _safe_float(row.get("high")),
                "l": _safe_float(row.get("low")),
                "c": _safe_float(row.get("close")),
                "v": _safe_float(row.get("volume")),
            }
        )

    price = _safe_float(latest_val.get("当日收盘价")) or _safe_float(latest_daily.get("close"))
    change_pct = _safe_float(latest_val.get("当日涨跌幅"))
    if change_pct is None:
        change_pct = _safe_float(latest_daily.get("turnover"))

    return {
        "symbol": resolved.code,
        "symbol_name": resolved.name or resolved.code,
        "region": resolved.region,
        "price": price,
        "pe_ttm": _safe_float(latest_val.get("PE(TTM)")),
        "pb": _safe_float(latest_val.get("市净率")),
        "market_cap": _safe_float(latest_val.get("总市值")),
        "daily_change_pct": round(change_pct, 2) if change_pct is not None else None,
        "volume": _safe_float(latest_daily.get("volume")),
        "amount": _safe_float(latest_daily.get("amount")),
        "trade_date": str(latest_val.get("数据日期") or latest_daily.get("date") or ""),
        "kline_preview": kline_preview,
        "source": "AKShare",
        "mode": "live",
        "api_refs": {
            "valuation": "stock_value_em",
            "daily": "stock_zh_a_daily",
        },
    }


def fetch_akshare_financials(resolved: ResolvedSymbol) -> dict[str, Any]:
    import akshare as ak

    valuation = ak.stock_value_em(symbol=resolved.code)
    latest = valuation.tail(1).iloc[0]

    return {
        "symbol": resolved.code,
        "symbol_name": resolved.name or resolved.code,
        "region": resolved.region,
        "pe_ttm": _safe_float(latest.get("PE(TTM)")),
        "pe_static": _safe_float(latest.get("PE(静)")),
        "pb": _safe_float(latest.get("市净率")),
        "peg": _safe_float(latest.get("PEG值")),
        "ps": _safe_float(latest.get("市销率")),
        "market_cap": _safe_float(latest.get("总市值")),
        "float_market_cap": _safe_float(latest.get("流通市值")),
        "total_shares": _safe_float(latest.get("总股本")),
        "float_shares": _safe_float(latest.get("流通股本")),
        "currency": "CNY",
        "trade_date": str(latest.get("数据日期") or ""),
        "source": "AKShare",
        "mode": "live",
    }


def fetch_akshare_hist_start_date(days: int = 30) -> str:
    start = datetime.now() - timedelta(days=days)
    return start.strftime("%Y%m%d")
