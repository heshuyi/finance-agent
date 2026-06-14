"""ProBuyAgent — 支持买入论证（LLM + ai_context）。"""

from __future__ import annotations

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact

PRO_BUY_SYSTEM = """你是支持买入方的投研分析师。基于已验证事实与投研数据上下文，论证支持买入的理由。
规则：不构成投资建议；推断须标注；至少 2 条可溯源论点；承认主要风险。"""


def run_pro_buy(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    ai_context = (payload.get("verified_data") or {}).get("metadata", {}).get("ai_context") or ""
    facts = [c["statement"] for c in verified if c.get("verified")][:5]

    user_prompt = (
        f"标的：{symbol_name}\n已验证事实：\n"
        + "\n".join(f"- {f}" for f in facts)
        + f"\n\n投研上下文：\n{ai_context[:3000]}\n\n"
        "请输出：核心观点、支持买入的 2-4 条论据、主要风险。"
    )
    fallback = f"{symbol_name}：基于已验证事实，中长期配置视角存在支撑，但需关注估值与宏观风险。"
    text = invoke_agent_text(system=PRO_BUY_SYSTEM, user=user_prompt, fallback=fallback)

    return make_artifact(
        task_id=task_id,
        agent_id="pro_buy",
        artifact_type="BullCase",
        claims=text_to_claims(text, agent_label="ProBuyAgent", verified_facts=facts, max_claims=4),
        confidence=0.75,
        metadata={
            "thesis": extract_thesis(text, "中长期基本面支撑逢低布局视角"),
            "risks": ["估值分位偏高", "宏观与行业不确定性"],
        },
    )
