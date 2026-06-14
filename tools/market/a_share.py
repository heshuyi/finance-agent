"""A 股行情/财报统一拉取 — AKShare 优先，Ashare / iTick 回退。"""

from __future__ import annotations

import os
from typing import Any, Callable

from agents.shared.artifact import now_iso
from tools.itick.client import get_itick_client
from tools.market.akshare_quote import fetch_akshare_financials, fetch_akshare_market
from tools.market.ashare_quote import fetch_ashare_market
from tools.symbols import ResolvedSymbol, resolve_a_share
from tools.types import ToolError, ToolResult

A_SHARE_MARKET_PROVIDER = os.getenv("A_SHARE_MARKET_PROVIDER", "auto").lower()


def _mock_bundle(symbol: str, symbol_name: str) -> dict[str, Any]:
    mock_quotes: dict[str, dict] = {
        "600519": {"name": "贵州茅台", "pe_ttm": 28.5, "price": 1680.0},
        "300750": {"name": "宁德时代", "pe_ttm": 22.1, "price": 198.5},
        "002594": {"name": "比亚迪", "pe_ttm": 24.3, "price": 245.0},
    }
    quote = mock_quotes.get(symbol, {"name": symbol_name or symbol, "pe_ttm": 25.0, "price": 100.0})
    return {
        "symbol": symbol,
        "symbol_name": quote.get("name") or symbol_name or symbol,
        "price": quote["price"],
        "pe_ttm": quote["pe_ttm"],
        "source": "FinTeam Mock Connector",
        "mode": "mock",
    }


def _mock_financials(symbol: str, symbol_name: str) -> dict[str, Any]:
    bundle = _mock_bundle(symbol, symbol_name)
    return {**bundle, "market_cap": None, "currency": "CNY"}


def _fetch_itick_market(resolved: ResolvedSymbol) -> dict[str, Any]:
    client = get_itick_client()
    if not client.configured:
        raise RuntimeError("iTick 未配置")

    tick = client.get_stock_tick(resolved.region, resolved.code)
    info = client.get_stock_info(resolved.region, resolved.code)
    kline = client.get_stock_kline(resolved.region, resolved.code, k_type=8, limit=5)
    if not tick.ok:
        raise RuntimeError(tick.errors[0].message if tick.errors else "iTick tick 失败")

    tick_data = tick.data if isinstance(tick.data, dict) else {}
    info_data = info.data if info.ok and isinstance(info.data, dict) else {}
    kline_rows = kline.data if kline.ok and isinstance(kline.data, list) else []
    latest_kline = kline_rows[-1] if kline_rows else {}
    change_pct = None
    if latest_kline and latest_kline.get("o"):
        change_pct = round(
            (float(latest_kline.get("c", 0)) - float(latest_kline["o"]))
            / float(latest_kline["o"])
            * 100,
            2,
        )

    return {
        "symbol": resolved.code,
        "symbol_name": info_data.get("n") or resolved.name or resolved.code,
        "region": resolved.region,
        "price": tick_data.get("ld"),
        "pe_ttm": info_data.get("pet"),
        "tick_at": tick_data.get("t"),
        "volume": tick_data.get("v"),
        "daily_change_pct": change_pct,
        "kline_preview": kline_rows[-3:],
        "source": "iTick",
        "mode": "live",
    }


def _fetch_itick_financials(resolved: ResolvedSymbol) -> dict[str, Any]:
    client = get_itick_client()
    if not client.configured:
        raise RuntimeError("iTick 未配置")
    info = client.get_stock_info(resolved.region, resolved.code)
    if not info.ok:
        raise RuntimeError(info.errors[0].message if info.errors else "iTick info 失败")
    info_data = info.data if isinstance(info.data, dict) else {}
    return {
        "symbol": resolved.code,
        "symbol_name": info_data.get("n") or resolved.name or resolved.code,
        "region": resolved.region,
        "industry": info_data.get("i"),
        "exchange": info_data.get("e"),
        "pe_ttm": info_data.get("pet"),
        "market_cap": info_data.get("mcb"),
        "total_shares": info_data.get("tso"),
        "currency": info_data.get("fcc") or "CNY",
        "website": info_data.get("wu"),
        "profile": (info_data.get("bd") or "")[:500],
        "source": "iTick",
        "mode": "live",
    }


def _try_providers(
    resolved: ResolvedSymbol,
    providers: list[tuple[str, Callable[[], dict[str, Any]]]],
) -> tuple[dict[str, Any], list[ToolError]]:
    errors: list[ToolError] = []
    for name, fetcher in providers:
        try:
            return fetcher(), errors
        except Exception as exc:
            errors.append(ToolError(code="PROVIDER_FALLBACK", message=f"{name}: {exc}", source=name))
    raise RuntimeError(errors[-1].message if errors else "所有行情源均失败")


def _market_provider_chain(resolved: ResolvedSymbol) -> list[tuple[str, Callable[[], dict[str, Any]]]]:
    preference = A_SHARE_MARKET_PROVIDER
    if preference == "akshare":
        return [("AKShare", lambda: fetch_akshare_market(resolved))]
    if preference == "ashare":
        return [("Ashare", lambda: fetch_ashare_market(resolved))]
    if preference == "itick":
        return [("iTick", lambda: _fetch_itick_market(resolved))]
    return [
        ("AKShare", lambda: fetch_akshare_market(resolved)),
        ("Ashare", lambda: fetch_ashare_market(resolved)),
        ("iTick", lambda: _fetch_itick_market(resolved)),
    ]


def _financials_provider_chain(resolved: ResolvedSymbol) -> list[tuple[str, Callable[[], dict[str, Any]]]]:
    preference = A_SHARE_MARKET_PROVIDER
    if preference == "akshare":
        return [("AKShare", lambda: fetch_akshare_financials(resolved))]
    if preference == "itick":
        return [("iTick", lambda: _fetch_itick_financials(resolved))]
    return [
        ("AKShare", lambda: fetch_akshare_financials(resolved)),
        ("iTick", lambda: _fetch_itick_financials(resolved)),
    ]


def fetch_a_share_market(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    try:
        data, provider_errors = _try_providers(resolved, _market_provider_chain(resolved))
        result = ToolResult.success(
            data,
            source=data.get("source", "A-Share"),
            fetched_at=now_iso(),
        )
        result.errors = provider_errors
        return result
    except Exception as exc:
        data = _mock_bundle(resolved.code, resolved.name)
        data["fallback_reason"] = str(exc)
        return ToolResult.success(data, source="FinTeam Mock Connector")


def fetch_a_share_financials(symbol: str, symbol_name: str = "") -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    try:
        data, provider_errors = _try_providers(resolved, _financials_provider_chain(resolved))
        result = ToolResult.success(
            data,
            source=data.get("source", "A-Share"),
            fetched_at=now_iso(),
        )
        result.errors = provider_errors
        return result
    except Exception as exc:
        data = _mock_financials(resolved.code, resolved.name)
        data["fallback_reason"] = str(exc)
        return ToolResult.success(data, source="FinTeam Mock Connector")
