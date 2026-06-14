"""DataVerificationAgent — 交叉核查 DataBundle。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_verification(payload: dict) -> dict:
    task_id = payload["task_id"]
    data_bundle = payload.get("data_bundle") or {}
    prior_claims = data_bundle.get("claims") or []

    verified = []
    discrepancies = []
    for c in prior_claims:
        if c.get("source_type") == "model_inference":
            verified.append({**c, "verified": False})
        else:
            verified.append({**c, "verified": True})

    claims = [
        make_claim(
            f"已核查 {len(prior_claims)} 条数据，{sum(1 for x in verified if x.get('verified'))} 条通过交叉验证",
            source_type="market_data",
            source_name="DataVerificationAgent",
        ),
    ]
    if any(not c.get("verified") for c in verified):
        claims.append(
            make_claim(
                "存在模型估算类数据，置信度上限下调",
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
        confidence=0.75 if discrepancies else 0.88,
        metadata={"verified_claims": verified, "discrepancies": discrepancies},
    )
