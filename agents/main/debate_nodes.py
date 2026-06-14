"""多轮辩论与仲裁节点 — M5。"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from agents.main.nodes import (
    _cancelled,
    _cancelled_result,
    _run_agent,
    _run_async,
)
from agents.shared.artifact import DISCLAIMER
from agents.shared.team_feed import (
    append_feed,
    artifact_to_feed_summary,
    debate_pair_for_intent,
    format_arbitration_feed,
    make_feed_message,
)
from agents.shared.state import MainAgentState


def _append_artifact_feed(
    feed: list[dict] | None,
    agent_id: str,
    artifact: dict | None,
    phase: str,
    round_num: int = 0,
) -> list[dict]:
    return append_feed(
        feed,
        make_feed_message(
            agent_id=agent_id,
            content=artifact_to_feed_summary(agent_id, artifact),
            phase=phase,
            round_num=round_num,
        ),
    )


def _debate_agents(state: MainAgentState) -> tuple[str, str]:
    intent = state.get("intent", "buy_analysis")
    return debate_pair_for_intent(intent)


def _base_input(state: MainAgentState) -> dict[str, Any]:
    artifacts = state.get("artifacts") or {}
    return {
        "task_id": state["task_id"],
        "symbol": state.get("symbol"),
        "symbol_name": state.get("symbol_name"),
        "verified_data": artifacts.get("verification"),
        "position": state.get("position") or {},
        "intent": state.get("intent"),
    }


async def _run_debate_agent(
    state: MainAgentState,
    agent_id: str,
    skill: str,
    extra: dict[str, Any],
) -> tuple[dict, list, list, dict | None]:
    ws = {
        **state,
        "artifacts": dict(state.get("artifacts") or {}),
        "sub_agent_status": [dict(r) for r in state.get("sub_agent_status") or []],
        "errors": list(state.get("errors") or []),
    }
    input_data = {**_base_input(state), **extra}
    artifacts, sub_status, errors = await _run_agent(ws, agent_id, skill, input_data)
    art = artifacts.get(agent_id)
    return artifacts, sub_status, errors, art


def debate_opening(state: MainAgentState, config: RunnableConfig) -> dict:
    return _run_async(_debate_opening_async(state, config))


async def _debate_opening_async(state: MainAgentState, config: RunnableConfig | None) -> dict:
    if _cancelled(state, config):
        return _cancelled_result(state)

    pro_id, anti_id = _debate_agents(state)
    feed = list(state.get("team_feed") or [])
    transcript = dict(state.get("debate_transcript") or {})
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])

    async def open_pro():
        return await _run_debate_agent(
            {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors},
            pro_id,
            "bull-case-opening",
            {"mode": "opening", "debate_round": 1},
        )

    async def open_anti():
        return await _run_debate_agent(
            {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors},
            anti_id,
            "bear-case-opening",
            {"mode": "opening", "debate_round": 1},
        )

    (pa, ps, pe, pro_art), (aa, as_, ae, anti_art) = await asyncio.gather(open_pro(), open_anti())
    artifacts.update(pa)
    artifacts.update(aa)
    errors.extend(pe)
    errors.extend(ae)
    by_id = {r["agent_id"]: r for r in sub_status}
    for row in ps + as_:
        by_id[row["agent_id"]] = row
    sub_status = list(by_id.values())

    if pro_art:
        transcript["opening_pro"] = pro_art
        feed = _append_artifact_feed(feed, pro_id, pro_art, "debate_r1", 1)
    if anti_art:
        transcript["opening_anti"] = anti_art
        feed = _append_artifact_feed(feed, anti_id, anti_art, "debate_r1", 1)

    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "team_feed": feed,
        "debate_transcript": transcript,
        "phase": "debate_r1",
        "progress": 65,
    }


def debate_pro_rebuttal(state: MainAgentState, config: RunnableConfig) -> dict:
    return _run_async(_debate_pro_rebuttal_async(state, config))


async def _debate_pro_rebuttal_async(state: MainAgentState, config: RunnableConfig | None) -> dict:
    if _cancelled(state, config):
        return _cancelled_result(state)

    pro_id, anti_id = _debate_agents(state)
    transcript = dict(state.get("debate_transcript") or {})
    feed = list(state.get("team_feed") or [])
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])

    artifacts, sub_status, errors, pro_art = await _run_debate_agent(
        {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors},
        pro_id,
        "bull-case-rebuttal",
        {
            "mode": "rebuttal",
            "debate_round": 2,
            "opponent_opening": transcript.get("opening_anti"),
            "self_opening": transcript.get("opening_pro"),
        },
    )

    if pro_art:
        transcript["rebuttal_pro"] = pro_art
        feed = _append_artifact_feed(feed, pro_id, pro_art, "debate_r2", 2)

    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "team_feed": feed,
        "debate_transcript": transcript,
        "phase": "debate_r2",
        "progress": 75,
    }


def debate_anti_rebuttal(state: MainAgentState, config: RunnableConfig) -> dict:
    return _run_async(_debate_anti_rebuttal_async(state, config))


async def _debate_anti_rebuttal_async(state: MainAgentState, config: RunnableConfig | None) -> dict:
    if _cancelled(state, config):
        return _cancelled_result(state)

    pro_id, anti_id = _debate_agents(state)
    transcript = dict(state.get("debate_transcript") or {})
    feed = list(state.get("team_feed") or [])
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])

    artifacts, sub_status, errors, anti_art = await _run_debate_agent(
        {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors},
        anti_id,
        "bear-case-rebuttal",
        {
            "mode": "rebuttal",
            "debate_round": 3,
            "opponent_opening": transcript.get("opening_pro"),
            "opponent_rebuttal": transcript.get("rebuttal_pro"),
            "self_opening": transcript.get("opening_anti"),
        },
    )

    if anti_art:
        transcript["rebuttal_anti"] = anti_art
        feed = _append_artifact_feed(feed, anti_id, anti_art, "debate_r3", 3)

    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "team_feed": feed,
        "debate_transcript": transcript,
        "phase": "debate_r3",
        "progress": 85,
    }


def arbitrate(state: MainAgentState, config: RunnableConfig) -> dict:
    return _run_async(_arbitrate_async(state, config))


async def _arbitrate_async(state: MainAgentState, config: RunnableConfig | None) -> dict:
    if _cancelled(state, config):
        return _cancelled_result(state)

    feed = list(state.get("team_feed") or [])
    transcript = dict(state.get("debate_transcript") or {})
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])

    input_data = {
        **_base_input(state),
        "debate_transcript": transcript,
    }

    artifacts, sub_status, errors, arb_art = await _run_debate_agent(
        {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors},
        "arbitrator",
        "final-arbitration",
        input_data,
    )

    arbitration = (arb_art or {}).get("metadata", {}).get("arbitration") or {}
    public_text = (arb_art or {}).get("metadata", {}).get("public_text") or format_arbitration_feed(arbitration)
    content = public_text
    if DISCLAIMER not in content:
        content = f"{content}\n\n{DISCLAIMER}"

    if arb_art:
        feed = append_feed(
            feed,
            make_feed_message(
                agent_id="arbitrator",
                content=public_text,
                phase="judgment",
                round_num=0,
            ),
        )

    symbol_label = state.get("symbol_name") or state.get("symbol") or "标的"
    final_report = {
        "symbol": symbol_label,
        "task_id": state["task_id"],
        "intent": state.get("intent", "general"),
        "content": content,
        "position": state.get("position") or None,
        "arbitration": arbitration,
        "artifacts": {k: v.get("artifact_id") for k, v in artifacts.items() if isinstance(v, dict)},
        "debate": transcript,
        "debate_transcript": transcript,
        "disclaimer": DISCLAIMER,
    }

    return {
        "messages": [AIMessage(content=content)],
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "team_feed": feed,
        "debate_transcript": transcript,
        "final_report": final_report,
        "phase": "done",
        "progress": 100,
        "artifacts_preview": {
            **(state.get("artifacts_preview") or {}),
            "final_summary": content[:400],
        },
        "awaiting_human": None,
    }


def should_after_debate(state: MainAgentState) -> str:
    phase = state.get("phase")
    if state.get("phase") == "cancelled" or state.get("user_cancelled"):
        return "persist_task"
    if phase == "debate_r1":
        return "debate_pro_rebuttal"
    if phase == "debate_r2":
        return "debate_anti_rebuttal"
    if phase == "debate_r3":
        return "arbitrate"
    return "arbitrate"
