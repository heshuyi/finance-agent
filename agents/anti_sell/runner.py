"""AntiSellAgent — 不建议卖出 / 建议持有。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_anti_sell(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    facts = [c["statement"] for c in verified if c.get("verified")][:3]

    claims = [
        make_claim(
            f"{symbol_name} 基本面未恶化，若无更好标的可继续持有",
            source_type="model_inference",
            verified=False,
            source_name="AntiSellAgent 推断",
        ),
        make_claim(
            f"已验证数据：{'；'.join(facts) if facts else '数据有限'}",
            source_type="market_data",
            verified=bool(facts),
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="anti_sell",
        artifact_type="HoldCase",
        claims=claims,
        confidence=0.7,
        metadata={"thesis": "龙头地位稳固，不宜因短期波动轻易清仓", "risks": ["估值回调", "行业周期"]},
    )
