"""ProBuyAgent — 支持买入论证。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_pro_buy(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    facts = [c["statement"] for c in verified if c.get("verified")][:3]

    claims = [
        make_claim(
            f"{symbol_name} 品牌与现金流护城河较强，适合长期配置视角",
            source_type="model_inference",
            verified=False,
            source_name="ProBuyAgent 推断",
        ),
        make_claim(
            f"基于已验证事实：{'；'.join(facts) if facts else '数据有限'}",
            source_type="market_data",
            verified=bool(facts),
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="pro_buy",
        artifact_type="BullCase",
        claims=claims,
        confidence=0.7,
        metadata={"thesis": "中长期品牌与盈利稳定性支持逢低布局", "risks": ["估值分位偏高", "宏观消费不确定"]},
    )
