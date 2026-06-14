"""AntiBuyAgent — 不建议买入论证（LLM + ai_context）。"""

from __future__ import annotations

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact

ANTI_BUY_SYSTEM = """你是不建议买入方的投研分析师。基于已验证事实与投研数据上下文，论证暂不买入或观望的理由。
规则：不构成投资建议；推断须标注；至少 2 条可溯源论点；承认看多方的合理点。"""


def run_anti_buy(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    ai_context = (payload.get("verified_data") or {}).get("metadata", {}).get("ai_context") or ""
    facts = [c["statement"] for c in verified if c.get("verified")][:5]

    user_prompt = (
        f"标的：{symbol_name}\n已验证事实：\n"
        + "\n".join(f"- {f}" for f in facts)
        + f"\n\n投研上下文：\n{ai_context[:3000]}\n\n"
        "请输出：核心观点、不建议买入的 2-4 条论据、主要风险。"
    )
    fallback = f"{symbol_name}：估值或预期已较充分反映，短期安全边际不足，不建议追高。"
    text = invoke_agent_text(system=ANTI_BUY_SYSTEM, user=user_prompt, fallback=fallback)

    return make_artifact(
        task_id=task_id,
        agent_id="anti_buy",
        artifact_type="BearCase_NoBuy",
        claims=text_to_claims(text, agent_label="AntiBuyAgent", verified_facts=facts, max_claims=4),
        confidence=0.72,
        metadata={
            "thesis": extract_thesis(text, "估值与预期已较充分反映，不建议追高"),
            "risks": ["业绩不及预期", "行业政策变化"],
        },
    )
