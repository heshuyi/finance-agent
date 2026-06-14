"""ProSellAgent — 建议卖出论证（LLM + ai_context + 持仓）。"""

from __future__ import annotations

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact

PRO_SELL_SYSTEM = """你是建议卖出/减仓方的投研分析师。结合估值、基本面与持仓盈亏情境，论证减仓理由。
规则：不构成投资建议；推断须标注；若有持仓成本/盈亏须纳入分析。"""


def run_pro_sell(payload: dict) -> dict:
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
        "请输出：核心观点、建议卖出/减仓的 2-4 条论据。"
    )
    fallback = f"{symbol_name}：估值偏高或盈利已部分兑现，可考虑减仓锁定收益。"
    text = invoke_agent_text(system=PRO_SELL_SYSTEM, user=user_prompt, fallback=fallback)

    return make_artifact(
        task_id=task_id,
        agent_id="pro_sell",
        artifact_type="BullSellCase",
        claims=text_to_claims(text, agent_label="ProSellAgent", verified_facts=facts, max_claims=4),
        confidence=0.74,
        metadata={
            "thesis": extract_thesis(text, "估值或预期充分，建议考虑减仓"),
            "risks": ["踏空反弹", "趋势延续"],
            "position": position,
        },
    )
