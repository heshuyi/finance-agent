"""AntiBuyAgent — 不建议买入论证。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_anti_buy(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    facts = [c["statement"] for c in verified if c.get("verified")][:3]

    claims = [
        make_claim(
            f"{symbol_name} 当前估值处于历史较高分位，短期安全边际不足",
            source_type="model_inference",
            verified=False,
            source_name="AntiBuyAgent 推断",
        ),
        make_claim(
            f"已验证数据参考：{'；'.join(facts) if facts else '数据有限'}",
            source_type="market_data",
            verified=bool(facts),
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="anti_buy",
        artifact_type="BearCase_NoBuy",
        claims=claims,
        confidence=0.72,
        metadata={"thesis": "估值与预期已较充分反映，不建议追高", "risks": ["业绩不及预期", "行业政策变化"]},
    )
