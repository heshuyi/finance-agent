"""AuthenticityAgent — 信息真伪验证。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_authenticity(payload: dict) -> dict:
    task_id = payload["task_id"]
    verified_data = payload.get("verified_data") or {}
    claims_in = verified_data.get("metadata", {}).get("verified_claims") or []

    suspicious_items = []
    trusted_items = []
    for c in claims_in:
        if c.get("source_type") == "model_inference" or not c.get("verified"):
            suspicious_items.append(c.get("statement", ""))
        else:
            trusted_items.append(c.get("statement", ""))

    # mock：若存在模型推断类数据，标记存疑以触发 HITL
    has_suspicious = len(suspicious_items) > 0

    status_claims = [
        make_claim(
            f"已验真 {len(trusted_items)} 条，存疑 {len(suspicious_items)} 条",
            source_type="market_data",
            source_name="AuthenticityAgent",
        ),
    ]
    if suspicious_items:
        status_claims.append(
            make_claim(
                "存疑项：" + "；".join(suspicious_items[:3]),
                verified=False,
                source_type="model_inference",
                source_name="AuthenticityAgent",
            )
        )

    return make_artifact(
        task_id=task_id,
        agent_id="authenticity",
        artifact_type="AuthenticityReport",
        claims=status_claims,
        confidence=0.9 if not has_suspicious else 0.55,
        metadata={
            "items": [
                {"statement": s, "status": "suspicious"} for s in suspicious_items
            ]
            + [{"statement": s, "status": "trusted"} for s in trusted_items[:5]],
            "has_suspicious": has_suspicious,
        },
    )
