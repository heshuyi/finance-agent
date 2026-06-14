"""ArbitratorAgent — 结构化终裁仲裁。"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.shared.agent_llm import invoke_agent_text
from agents.shared.artifact import DISCLAIMER, make_artifact, make_claim
from agents.shared.llm import get_chat_model, llm_configured

ARBITRATOR_SYSTEM = """你是 FinTeam 仲裁官。综合多方与空方三轮辩论及已验证事实，给出结构化终裁。
不构成投资建议。必须输出 JSON：
{
  "stance": "倾向买入|倾向观望|倾向不买入" 或卖出场景对应措辞,
  "when_to_buy": "若倾向买，什么条件/价位/催化剂下可考虑",
  "when_may_buy_later": "若倾向不买，什么变化后可能转为可买",
  "bull_case_summary": "多方核心论据摘要",
  "bear_case_summary": "空方核心论据摘要",
  "key_disagreements": "双方核心分歧",
  "reasoning": "仲裁推理过程"
}"""


def _parse_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def _format_transcript(transcript: dict[str, Any]) -> str:
    lines = []
    for key, label in [
        ("opening_pro", "多方开篇"),
        ("opening_anti", "空方开篇"),
        ("rebuttal_pro", "多方反驳"),
        ("rebuttal_anti", "空方再反驳"),
    ]:
        art = transcript.get(key)
        if art:
            meta = art.get("metadata") or {}
            lines.append(f"### {label}\n{meta.get('public_text') or meta.get('thesis', '')}")
    return "\n\n".join(lines)


def run_arbitrator(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    intent = payload.get("intent") or "buy_analysis"
    transcript = payload.get("debate_transcript") or {}
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    ai_context = (payload.get("verified_data") or {}).get("metadata", {}).get("ai_context") or ""
    facts = [c["statement"] for c in verified if c.get("verified")][:6]

    user_prompt = (
        f"标的：{symbol_name}\n意图：{intent}\n\n"
        f"已验证事实：\n" + "\n".join(f"- {f}" for f in facts)
        + f"\n\n辩论记录：\n{_format_transcript(transcript)}\n\n"
        f"投研上下文摘要：\n{ai_context[:2000]}"
    )

    arbitration: dict[str, Any] = {}
    if llm_configured():
        model = get_chat_model(temperature=0.2)
        try:
            response = model.invoke([
                SystemMessage(content=ARBITRATOR_SYSTEM),
                HumanMessage(content=user_prompt),
            ])
            arbitration = _parse_json(str(response.content))
        except Exception:
            arbitration = {}

    if not arbitration:
        fallback = invoke_agent_text(
            system=ARBITRATOR_SYSTEM,
            user=user_prompt,
            fallback="综合多空分歧，建议观望，待估值与催化剂明朗后再评估。",
        )
        arbitration = {
            "stance": "倾向观望",
            "when_to_buy": "待 PE 分位回落或出现明确业绩催化",
            "when_may_buy_later": "若营收增速改善且估值回归合理区间",
            "bull_case_summary": (transcript.get("opening_pro") or {}).get("metadata", {}).get("thesis", ""),
            "bear_case_summary": (transcript.get("opening_anti") or {}).get("metadata", {}).get("thesis", ""),
            "key_disagreements": "估值分位与成长预期",
            "reasoning": fallback,
        }

    content_lines = [
        f"**倾向**：{arbitration.get('stance', '观望')}",
        f"**何时可考虑买入**：{arbitration.get('when_to_buy', '—')}",
        f"**何时可能转为可买**：{arbitration.get('when_may_buy_later', '—')}",
        f"**核心分歧**：{arbitration.get('key_disagreements', '—')}",
        "",
        arbitration.get("reasoning", ""),
    ]
    public_text = "\n".join(content_lines)

    claims = [
        make_claim(
            f"仲裁倾向：{arbitration.get('stance', '观望')}",
            source_type="model_inference",
            verified=False,
            source_name="仲裁官",
        ),
        make_claim(
            f"何时买：{arbitration.get('when_to_buy', '—')}",
            source_type="model_inference",
            verified=False,
            source_name="仲裁官",
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="arbitrator",
        artifact_type="Arbitration",
        claims=claims,
        confidence=0.8,
        metadata={
            "arbitration": {**arbitration, "disclaimer": DISCLAIMER},
            "public_text": public_text,
        },
    )
