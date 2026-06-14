"""投研群聊时间线 — team_feed 构建与追加。"""

from __future__ import annotations

import uuid
from typing import Any

from agents.shared.artifact import now_iso

AGENT_PERSONAS: dict[str, dict[str, str]] = {
    "finteam_main": {"display_name": "主编排", "role": "system"},
    "data_collector": {"display_name": "数据员", "role": "staff"},
    "verification": {"display_name": "核查员", "role": "staff"},
    "authenticity": {"display_name": "验真员", "role": "staff"},
    "pro_buy": {"display_name": "多方", "role": "bull"},
    "anti_buy": {"display_name": "空方", "role": "bear"},
    "pro_sell": {"display_name": "建议卖", "role": "bull"},
    "anti_sell": {"display_name": "建议持", "role": "bear"},
    "arbitrator": {"display_name": "仲裁官", "role": "judge"},
}

PHASE_LABELS: dict[str, str] = {
    "planning": "任务规划",
    "data": "数据获取",
    "verify": "交叉核查",
    "auth": "真伪验证",
    "debate_r1": "辩论·开篇",
    "debate_r2": "辩论·多方反驳",
    "debate_r3": "辩论·空方反驳",
    "judgment": "终裁仲裁",
}


def new_feed_id() -> str:
    return str(uuid.uuid4())


def make_feed_message(
    *,
    agent_id: str,
    content: str,
    phase: str,
    round_num: int = 0,
    display_name: str | None = None,
    role: str | None = None,
) -> dict[str, Any]:
    persona = AGENT_PERSONAS.get(agent_id, {"display_name": agent_id, "role": "staff"})
    return {
        "id": new_feed_id(),
        "agent_id": agent_id,
        "display_name": display_name or persona["display_name"],
        "role": role or persona["role"],
        "phase": phase,
        "round": round_num,
        "content": content,
        "created_at": now_iso(),
    }


def append_feed(
    feed: list[dict[str, Any]] | None,
    message: dict[str, Any],
) -> list[dict[str, Any]]:
    out = list(feed or [])
    out.append(message)
    return out


def artifact_to_feed_summary(agent_id: str, artifact: dict[str, Any] | None) -> str:
    if not artifact:
        return "（无输出）"
    lines: list[str] = []
    thesis = (artifact.get("metadata") or {}).get("thesis")
    if thesis:
        lines.append(f"**核心观点**：{thesis}")
    for claim in (artifact.get("claims") or [])[:5]:
        stmt = claim.get("statement", "")
        if stmt:
            tag = "✓" if claim.get("verified") else "?"
            lines.append(f"- [{tag}] {stmt}")
    mode = (artifact.get("metadata") or {}).get("debate_mode")
    if mode:
        lines.insert(0, f"（{mode}）")
    return "\n".join(lines) if lines else "（已完成，暂无摘要）"


def format_arbitration_feed(arbitration: dict[str, Any]) -> str:
    parts = [
        f"**倾向**：{arbitration.get('stance', '观望')}",
        f"**何时可考虑买入**：{arbitration.get('when_to_buy', '—')}",
        f"**何时可能转为可买**：{arbitration.get('when_may_buy_later', '—')}",
        f"**多方摘要**：{arbitration.get('bull_case_summary', '—')}",
        f"**空方摘要**：{arbitration.get('bear_case_summary', '—')}",
        f"**核心分歧**：{arbitration.get('key_disagreements', '—')}",
        "",
        arbitration.get("reasoning", ""),
    ]
    return "\n".join(p for p in parts if p)


def debate_pair_for_intent(intent: str) -> tuple[str, str]:
    if intent == "sell_analysis":
        return "pro_sell", "anti_sell"
    return "pro_buy", "anti_buy"
