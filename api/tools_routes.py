"""FastAPI Tool 查询端点 — 供前端 CopilotKit Tools 与外部调用。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from tools.context_loader import load_analysis_context
from tools.filings.cninfo import fetch_filings
from tools.financials.indicators import fetch_financial_indicators
from tools.financials.info import fetch_financials
from tools.market.bundle import fetch_market_bundle
from tools.news.feed import fetch_news_feed
from tools.peers.compare import fetch_peer_comparison
from tools.symbols import resolve_a_share
from tools.valuation.history import fetch_valuation_history
from tools.ai_context import (
    build_filings_context,
    build_financials_context,
    build_indicators_context,
    build_market_context,
    build_news_context,
    build_peers_context,
    build_valuation_context,
)
from tools.types import ToolResult

router = APIRouter(prefix="/tools", tags=["tools"])


def _serialize(result: ToolResult, *, ai_context: str | None = None) -> dict[str, Any]:
    payload = {
        "ok": result.ok,
        "data": result.data,
        "source": result.source,
        "fetched_at": result.fetched_at,
        "from_cache": bool((result.data or {}).get("_from_cache")),
        "errors": [{"code": e.code, "message": e.message, "source": e.source} for e in result.errors],
    }
    if ai_context:
        payload["ai_context"] = ai_context
    return payload


def _require_symbol(symbol: str | None, symbol_name: str = "") -> str:
    if not symbol or not symbol.strip():
        raise HTTPException(status_code=400, detail="symbol is required")
    sym = symbol.strip()
    try:
        resolve_a_share(sym, symbol_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return sym


@router.get("/market")
def tools_market(
    symbol: str = Query(..., description="A 股代码，如 600519"),
    symbol_name: str = Query("", description="标的名称，可选"),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_market_bundle(sym, symbol_name)
    ctx = build_market_context(result.data) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/financials")
def tools_financials(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_financials(sym, symbol_name)
    ctx = build_financials_context(result.data) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/valuation")
def tools_valuation(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
    days: int = Query(365, ge=30, le=730),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_valuation_history(sym, symbol_name, days=days)
    ctx = build_valuation_context(result.data) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/indicators")
def tools_indicators(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_financial_indicators(sym, symbol_name)
    ctx = build_indicators_context(result.data) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/peers")
def tools_peers(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
    limit: int = Query(3, ge=1, le=5),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_peer_comparison(sym, symbol_name, limit=limit)
    ctx = build_peers_context(result.data) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/news")
def tools_news(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
    limit: int = Query(10, ge=1, le=30),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_news_feed(sym, symbol_name=symbol_name, limit=limit)
    ctx = build_news_context(result.data, max_items=limit) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/filings")
def tools_filings(
    symbol: str = Query(...),
    symbol_name: str = Query(""),
    limit: int = Query(10, ge=1, le=30),
):
    sym = _require_symbol(symbol, symbol_name)
    result = fetch_filings(sym, symbol_name, limit=limit)
    ctx = build_filings_context(result.data, max_items=limit) if result.ok else None
    return _serialize(result, ai_context=ctx)


@router.get("/context")
def tools_full_context(
    symbol: str = Query(..., description="A 股代码"),
    symbol_name: str = Query("", description="标的名称"),
    limit: int = Query(5, ge=1, le=15),
):
    """合并行情/财报/估值/同业/资讯/公告，返回供 LLM 分析用的完整上下文。"""
    sym = _require_symbol(symbol, symbol_name)
    ai_context = load_analysis_context(sym, symbol_name, limit=limit)
    market = fetch_market_bundle(sym, symbol_name)
    return {
        "ok": True,
        "symbol": sym,
        "symbol_name": market.data.get("symbol_name") or symbol_name or sym,
        "ai_context": ai_context,
        "from_cache": bool(market.data.get("_from_cache")),
    }
