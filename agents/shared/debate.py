"""多空辩论共用逻辑 — opening / rebuttal 模式。"""

from __future__ import annotations

from typing import Any

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact

DEBATE_SIDES: dict[str, dict[str, str]] = {
    "pro_buy": {
        "label": "多方",
        "artifact_type": "BullCase",
        "opening_system": "你是支持买入方的投研分析师。基于已验证事实与投研上下文，阐述支持买入的开篇立场。",
        "rebuttal_system": "你是支持买入方的投研分析师。请针对空方的开篇观点进行反驳，并强化己方买入理由。",
    },
    "anti_buy": {
        "label": "空方",
        "artifact_type": "BearCase_NoBuy",
        "opening_system": "你是不建议买入方的投研分析师。基于已验证事实与投研上下文，阐述不建议买入的开篇立场。",
        "rebuttal_system": "你是不建议买入方的投研分析师。请针对多方的开篇与反驳进行再反驳，并强化己方观望/不买入理由。",
    },
    "pro_sell": {
        "label": "建议卖出",
        "artifact_type": "BullSellCase",
        "opening_system": "你是建议卖出/减仓方的投研分析师。结合持仓与基本面，阐述卖出理由。",
        "rebuttal_system": "你是建议卖出方。请反驳持有方的观点，强化减仓理由。",
    },
    "anti_sell": {
        "label": "建议持有",
        "artifact_type": "HoldCase",
        "opening_system": "你是建议持有方的投研分析师。结合持仓与基本面，阐述不宜卖出的理由。",
        "rebuttal_system": "你是建议持有方。请反驳卖出方的开篇与反驳，强化持有理由。",
    },
}


def _artifact_text(artifact: dict[str, Any] | None) -> str:
    if not artifact:
        return "（对方暂无发言）"
    lines = []
    thesis = (artifact.get("metadata") or {}).get("thesis")
    if thesis:
        lines.append(f"核心观点：{thesis}")
    for c in artifact.get("claims") or []:
        lines.append(f"- {c.get('statement', '')}")
    return "\n".join(lines) or "（无内容）"


def run_debate_side(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    cfg = DEBATE_SIDES[agent_id]
    mode = payload.get("mode") or "opening"
    task_id = payload["task_id"]
    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    verified = (payload.get("verified_data") or {}).get("metadata", {}).get("verified_claims") or []
    ai_context = (payload.get("verified_data") or {}).get("metadata", {}).get("ai_context") or ""
    facts = [c["statement"] for c in verified if c.get("verified")][:5]
    position = payload.get("position") or {}
    pos_txt = ""
    if position.get("cost_price") is not None:
        pos_txt = f"\n持仓成本 {position['cost_price']}，盈亏约 {position.get('profit_pct', '?')}%"

    opponent_opening = payload.get("opponent_opening")
    opponent_rebuttal = payload.get("opponent_rebuttal")
    self_opening = payload.get("self_opening")
    self_rebuttal = payload.get("self_rebuttal")

    if mode == "opening":
        system = cfg["opening_system"]
        user = (
            f"标的：{symbol_name}{pos_txt}\n已验证事实：\n"
            + "\n".join(f"- {f}" for f in facts)
            + f"\n\n投研上下文：\n{ai_context[:3000]}\n\n"
            "请输出开篇立场：核心观点 + 2-4 条论据 + 主要风险。"
        )
        fallback = f"{cfg['label']}开篇：基于已验证事实，{symbol_name} 存在分歧，详见上下文。"
    else:
        system = cfg["rebuttal_system"]
        parts = [f"标的：{symbol_name}{pos_txt}", f"己方开篇：\n{_artifact_text(self_opening)}"]
        if opponent_opening:
            parts.append(f"对方开篇：\n{_artifact_text(opponent_opening)}")
        if opponent_rebuttal:
            parts.append(f"对方反驳：\n{_artifact_text(opponent_rebuttal)}")
        if self_rebuttal:
            parts.append(f"己方上一轮反驳：\n{_artifact_text(self_rebuttal)}")
        parts.append("请针对性反驳并总结己方立场，2-4 条。")
        user = "\n\n".join(parts)
        fallback = f"{cfg['label']}反驳：对方论点存在瑕疵，建议结合估值与催化剂再观察。"

    text = invoke_agent_text(system=system, user=user, fallback=fallback)

    return make_artifact(
        task_id=task_id,
        agent_id=agent_id,
        artifact_type=cfg["artifact_type"],
        claims=text_to_claims(text, agent_label=cfg["label"], verified_facts=facts, max_claims=5),
        confidence=0.75 if mode == "opening" else 0.72,
        metadata={
            "thesis": extract_thesis(text, f"{cfg['label']}观点"),
            "debate_mode": "开篇" if mode == "opening" else "反驳",
            "debate_round": payload.get("debate_round", 1),
            "public_text": text,
        },
    )
