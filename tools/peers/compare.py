"""同行业估值横向对比（AKShare 免费数据）。"""

from __future__ import annotations

from datetime import date
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


def _quarter_end_dates(max_quarters: int = 6) -> list[str]:
    """最近若干季度末 YYYYMMDD，供业绩报表接口使用。"""
    today = date.today()
    y, m = today.year, today.month
    anchors = []
    for qm in (3, 6, 9, 12):
        if qm <= m:
            anchors.append(date(y, qm, [31, 30, 30, 31][qm // 3 - 1]))
    for qm in (12, 9, 6, 3):
        anchors.append(date(y - 1, qm, [31, 30, 30, 31][qm // 3 - 1]))
    unique = sorted({d.strftime("%Y%m%d") for d in anchors}, reverse=True)
    return unique[:max_quarters]


def _fetch_industry_from_yjbb(resolved) -> tuple[str, list[dict[str, Any]]]:
    import akshare as ak

    for report_date in _quarter_end_dates():
        try:
            df = ak.stock_yjbb_em(date=report_date)
        except Exception:
            continue
        if df is None or df.empty:
            continue
        code_col = "股票代码"
        row = df[df[code_col].astype(str).str.zfill(6) == resolved.code]
        if row.empty:
            continue
        target = row.iloc[0]
        industry = str(target.get("所处行业") or "").strip()
        if not industry:
            continue
        same = df[
            (df["所处行业"] == industry)
            & (df[code_col].astype(str).str.zfill(6) != resolved.code)
        ]
        peers: list[dict[str, Any]] = []
        for _, peer in same.head(5).iterrows():
            peers.append(
                {
                    "symbol": str(peer.get(code_col)).zfill(6),
                    "symbol_name": str(peer.get("股票简称") or ""),
                    "pe_ttm": _safe_float(peer.get("每股收益")),
                    "pb": None,
                    "industry": industry,
                    "metric_note": "每股收益(业绩报表)",
                }
            )
        return industry, peers
    return "", []


def _fetch_industry_from_info(resolved) -> str:
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


def _fetch_peers_from_spot(resolved, industry: str, *, limit: int) -> list[dict[str, Any]]:
    import akshare as ak

    try:
        spot = ak.stock_zh_a_spot_em()
    except Exception:
        return []

    peers: list[dict[str, Any]] = []
    for _, row in spot.iterrows():
        code = str(row.get("代码", "")).zfill(6)
        if code == resolved.code:
            continue
        ind = str(row.get("所属行业", "") or row.get("行业", "") or "")
        if industry and industry not in ind and ind not in industry:
            continue
        peers.append(
            {
                "symbol": code,
                "symbol_name": str(row.get("名称", "")),
                "pe_ttm": _safe_float(row.get("市盈率-动态")),
                "pb": _safe_float(row.get("市净率")),
                "industry": ind or industry,
            }
        )
        if len(peers) >= limit:
            break
    return peers


def _fetch_live_peers(symbol: str, symbol_name: str, *, limit: int = 3) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    industry, peers = _fetch_industry_from_yjbb(resolved)
    api_ref = "stock_yjbb_em"

    if not industry:
        industry = _fetch_industry_from_info(resolved)
        api_ref = "stock_individual_info_em"

    if not peers and industry:
        peers = _fetch_peers_from_spot(resolved, industry, limit=limit)
        if peers:
            api_ref = "stock_zh_a_spot_em"

    peers = peers[:limit]

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

    return ToolResult.success(
        {
            "symbol": resolved.code,
            "symbol_name": resolved.name or symbol_name,
            "industry": industry,
            "peers": peers,
            "mode": "live" if peers else "empty",
            "source": "AKShare",
            "api_ref": api_ref,
        },
        source="AKShare",
    )


def fetch_peer_comparison(symbol: str, symbol_name: str = "", *, limit: int = 3) -> ToolResult:
    resolved = resolve_a_share(symbol, symbol_name)
    return fetch_with_cache(
        cache_type="peers",
        symbol=resolved.code,
        suffix=f"limit={limit}&v=2",
        source="AKShare",
        fetcher=lambda: _fetch_live_peers(resolved.code, resolved.name or symbol_name, limit=limit),
    )
