"""AntiSellAgent — 不建议卖出/持有论证（LLM + ai_context + 持仓）。"""

from __future__ import annotations

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact

ANTI_SELL_SYSTEM = """你是建议持有方的投研分析师。结合基本面与持仓情境，论证不宜轻易卖出/清仓的理由。
规则：不构成投资建议；推断须标注；若有持仓盈亏须纳入分析。"""


def run_anti_sell(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    ai_context = (payload.get("verified_data") or {}).get("metadata", {}).get("ai_context") or ""
    position = payload.get("position") or {}
    facts = [c["statement"] for c in verified if c.get("verified")][:5]

    pos_txt = ""
    if position:
        pos_txt = f"\n持仓情境：成本 {position.get('cost_price', '?')}，盈亏约 {position.get('profit_pct', '?')}%"

    user_prompt = (
        f"标的：{symbol_name}{pos_txt}\n已验证事实：\n"
        + "\n".join(f"- {f}" for f in facts)
        + f"\n\n投研上下文：\n{ai_context[:3000]}\n\n"
        "请输出：核心观点、建议持有的 2-4 条论据。"
    )
    fallback = f"{symbol_name}：龙头地位与中长期逻辑仍在，不宜因短期波动轻易清仓。"
    text = invoke_agent_text(system=ANTI_SELL_SYSTEM, user=user_prompt, fallback=fallback)

    return make_artifact(
        task_id=task_id,
        agent_id="anti_sell",
        artifact_type="HoldCase",
        claims=text_to_claims(text, agent_label="AntiSellAgent", verified_facts=facts, max_claims=4),
        confidence=0.73,
        metadata={
            "thesis": extract_thesis(text, "中长期逻辑仍在，不宜轻易清仓"),
            "risks": ["估值回调", "行业周期"],
            "position": position,
        },
    )
