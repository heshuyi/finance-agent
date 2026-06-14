"""DataVerificationAgent — 多免费源交叉核查 DataBundle。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim
from tools.verification.cross_check import cross_check_data_bundle


def run_verification(payload: dict) -> dict:
    task_id = payload["task_id"]
    data_bundle = payload.get("data_bundle") or {}
    prior_claims = data_bundle.get("claims") or []
    meta = data_bundle.get("metadata") or {}

    market_bundle = meta.get("market_bundle") or {}
    fin_bundle = meta.get("financials_bundle") or {}
    valuation = meta.get("valuation")

    cross = cross_check_data_bundle(
        market={
            "price": market_bundle.get("price"),
            "pe_ttm": market_bundle.get("pe_ttm") or fin_bundle.get("pe_ttm"),
            "source": market_bundle.get("source", "AKShare"),
        },
        financials={
            "pe_ttm": fin_bundle.get("pe_ttm"),
            "source": fin_bundle.get("source", "AKShare"),
        },
        valuation=valuation,
        symbol=meta.get("symbol") or market_bundle.get("symbol") or "",
        region=market_bundle.get("region") or fin_bundle.get("region") or "",
    )

    verified = []
    for c in prior_claims:
        if c.get("source_type") == "model_inference":
            verified.append({**c, "verified": False})
        else:
            verified.append({**c, "verified": not cross["discrepancies"] or c.get("source_type") != "financial_report"})

    claims = [
        make_claim(
            f"交叉核查：{len(cross['verified_fields'])} 项字段一致，"
            f"发现 {len(cross['discrepancies'])} 处偏差",
            source_type="market_data",
            source_name="DataVerificationAgent",
        ),
    ]
    for d in cross["discrepancies"][:3]:
        claims.append(
            make_claim(
                d["message"],
                verified=True,
                source_type="market_data",
                source_name="DataVerificationAgent",
            )
        )

    return make_artifact(
        task_id=task_id,
        agent_id="verification",
        artifact_type="VerifiedData",
        claims=claims,
        confidence=cross["confidence"],
        metadata={
            "verified_claims": verified,
            "discrepancies": cross["discrepancies"],
            "cross_check": cross,
            "ai_context": meta.get("ai_context"),
        },
    )
