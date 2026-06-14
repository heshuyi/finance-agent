"""多免费源交叉核查。"""

from __future__ import annotations

from typing import Any


def _f(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def cross_check_data_bundle(
    market: dict[str, Any] | None,
    financials: dict[str, Any] | None,
    valuation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """对比行情、财报、估值历史中的关键字段。"""
    discrepancies: list[dict[str, str]] = []
    verified_fields: list[str] = []

    m_price = _f((market or {}).get("price"))
    f_pe = _f((financials or {}).get("pe_ttm"))
    m_pe = _f((market or {}).get("pe_ttm"))
    v_pe = _f(((valuation or {}).get("latest") or {}).get("pe_ttm"))

    if m_price is not None:
        verified_fields.append("price")

    if f_pe is not None and m_pe is not None:
        diff_pct = abs(f_pe - m_pe) / max(f_pe, m_pe) * 100
        if diff_pct > 5:
            discrepancies.append(
                {
                    "field": "pe_ttm",
                    "message": f"财报 PE-TTM({f_pe}) 与行情 PE-TTM({m_pe}) 偏差 {diff_pct:.1f}%",
                    "sources": f"{financials.get('source')} vs {market.get('source')}",
                }
            )
        else:
            verified_fields.append("pe_ttm")

    if v_pe is not None and m_pe is not None:
        diff_pct = abs(v_pe - m_pe) / max(v_pe, m_pe) * 100
        if diff_pct > 8:
            discrepancies.append(
                {
                    "field": "pe_ttm_history",
                    "message": f"估值历史 PE({v_pe}) 与行情 PE({m_pe}) 偏差 {diff_pct:.1f}%",
                    "sources": f"{valuation.get('source')} vs {market.get('source')}",
                }
            )

    val_close = _f(((valuation or {}).get("latest") or {}).get("close"))
    if val_close is not None and m_price is not None:
        diff_pct = abs(val_close - m_price) / max(val_close, m_price) * 100
        if diff_pct > 3:
            discrepancies.append(
                {
                    "field": "close_price",
                    "message": f"估值序列收盘价({val_close}) 与行情价({m_price}) 偏差 {diff_pct:.1f}%",
                    "sources": f"{valuation.get('source')} vs {market.get('source')}",
                }
            )
        else:
            verified_fields.append("close_price")

    confidence = 0.88 if not discrepancies else max(0.55, 0.88 - 0.1 * len(discrepancies))

    return {
        "verified_fields": verified_fields,
        "discrepancies": discrepancies,
        "confidence": round(confidence, 2),
        "cross_check_passed": len(discrepancies) == 0,
    }
