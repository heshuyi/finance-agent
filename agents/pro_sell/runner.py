"""ProSellAgent — 建议卖出 / 减仓论证。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim


def run_pro_sell(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    facts = [c["statement"] for c in verified if c.get("verified")][:3]

    claims = [
        make_claim(
            f"{symbol_name} 估值偏高或盈利预期已反映，建议考虑减仓锁定收益",
            source_type="model_inference",
            verified=False,
            source_name="ProSellAgent 推断",
        ),
        make_claim(
            f"已验证数据：{'；'.join(facts) if facts else '数据有限'}",
            source_type="market_data",
            verified=bool(facts),
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="pro_sell",
        artifact_type="SellCase",
        claims=claims,
        confidence=0.68,
        metadata={"thesis": "短期性价比下降，可分批减仓", "risks": ["卖飞风险", "趋势延续"]},
    )
