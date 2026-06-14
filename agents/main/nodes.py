"""MainAgent LangGraph nodes — M1 A2A 调度。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from a2a.client import send_task_async
from a2a.types import TaskStatus
from agents.shared.artifact import DISCLAIMER
from agents.shared.intent import parse_user_text
from agents.shared.llm import get_chat_model, llm_configured
from agents.shared.state import MainAgentState, empty_sub_agent_status, new_task_id

PIPELINE_INTENTS = {"buy_analysis", "sell_analysis", "verify_only", "data_query"}

SYSTEM_PROMPT = """你是 FinTeam Agent 的主编排 Agent（投研团队负责人）。
你已调度数据、核查、辩论子 Agent 完成分析，请基于提供的 Artifact 摘要给出综合研判。

硬性规则：
- 不构成投资建议，末尾附免责声明
- 仅引用已验证（verified=true）的数据作为核心论据
- 标注多空分歧与未决问题
- 语气专业、简洁
"""

DEBATE_AGENTS = ("pro_buy", "anti_buy")


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _last_human_text(state: MainAgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def _set_agent_status(
    status_list: list[dict],
    agent_id: str,
    status: str,
    message: str | None = None,
) -> None:
    now = _now_iso()
    for row in status_list:
        if row["agent_id"] == agent_id:
            row["status"] = status
            row["message"] = message
            row["updated_at"] = now


def should_run_pipeline(state: MainAgentState) -> str:
    intent = state.get("intent", "general")
    planned = state.get("planned_agents") or []
    if intent in PIPELINE_INTENTS and planned:
        return "dispatch_pipeline"
    return "chat_response"


def prepare_task(state: MainAgentState) -> dict:
    text = _last_human_text(state)
    parsed = parse_user_text(text)
    now = _now_iso()
    sub_status = empty_sub_agent_status(now)
    for row in sub_status:
        if row["agent_id"] in parsed.planned_agents:
            row["message"] = "等待 A2A 调度"

    return {
        "task_id": state.get("task_id") or new_task_id(),
        "symbol": parsed.symbol,
        "symbol_name": parsed.symbol_name,
        "intent": parsed.intent,
        "phase": "planning",
        "progress": 10,
        "planned_agents": parsed.planned_agents,
        "sub_agent_status": sub_status,
        "artifacts": {},
        "artifacts_preview": {"user_query": text[:500]},
        "human_decision": None,
        "final_report": None,
        "errors": [],
    }


async def _run_agent(
    state: MainAgentState,
    agent_id: str,
    skill_id: str,
    input_data: dict[str, Any],
) -> tuple[dict[str, Any], list[dict], list[dict]]:
    sub_status = state["sub_agent_status"]
    artifacts = dict(state.get("artifacts") or {})
    errors = list(state.get("errors") or [])
    task_id = state["task_id"]

    _set_agent_status(sub_status, agent_id, "working", "A2A 执行中…")
    result = await send_task_async(agent_id, skill_id, task_id, input_data)

    if result.status == TaskStatus.COMPLETED and result.artifact:
        artifacts[agent_id] = result.artifact
        _set_agent_status(sub_status, agent_id, "completed", "完成")
    else:
        errors.append({"agent_id": agent_id, "error": result.error or result.message})
        _set_agent_status(sub_status, agent_id, "failed", result.error or "失败")

    return artifacts, sub_status, errors


def dispatch_pipeline(state: MainAgentState) -> dict:
    return _run_async(_dispatch_pipeline_async(state))


async def _dispatch_pipeline_async(state: MainAgentState) -> dict:
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])
    work_state = {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors}

    if "data_collector" in state.get("planned_agents", []):
        artifacts, sub_status, errors = await _run_agent(
            {**work_state, "sub_agent_status": sub_status, "artifacts": artifacts, "errors": errors},
            "data_collector",
            "fetch-market-data",
            {
                "task_id": state["task_id"],
                "symbol": state.get("symbol"),
                "symbol_name": state.get("symbol_name"),
            },
        )
        work_state.update({"artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors})

    if "verification" in state.get("planned_agents", []) and artifacts.get("data_collector"):
        artifacts, sub_status, errors = await _run_agent(
            {**work_state, "sub_agent_status": sub_status, "artifacts": artifacts, "errors": errors},
            "verification",
            "cross-verify-data",
            {"task_id": state["task_id"], "data_bundle": artifacts["data_collector"]},
        )

    phase = "verify" if artifacts.get("verification") else "data"
    progress = 45 if phase == "verify" else 30
    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "phase": phase,
        "progress": progress,
    }


def should_run_debate(state: MainAgentState) -> str:
    if state.get("intent") == "buy_analysis" and "pro_buy" in (state.get("planned_agents") or []):
        return "dispatch_debate"
    return "synthesize_judgment"


def dispatch_debate(state: MainAgentState) -> dict:
    return _run_async(_dispatch_debate_async(state))


async def _dispatch_debate_async(state: MainAgentState) -> dict:
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])
    base_input = {
        "task_id": state["task_id"],
        "symbol": state.get("symbol"),
        "symbol_name": state.get("symbol_name"),
        "verified_data": artifacts.get("verification"),
    }

    async def run_one(agent_id: str, skill: str) -> None:
        nonlocal artifacts, sub_status, errors
        ws = {**state, "artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors}
        artifacts, sub_status, errors = await _run_agent(ws, agent_id, skill, base_input)

    await asyncio.gather(
        run_one("pro_buy", "bull-case"),
        run_one("anti_buy", "bear-case-no-buy"),
    )

    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "phase": "debate",
        "progress": 75,
    }


def synthesize_judgment(state: MainAgentState) -> dict:
    artifacts = state.get("artifacts") or {}
    summary_lines = []
    for aid, art in artifacts.items():
        claims = art.get("claims") or []
        summary_lines.append(f"### {aid}\n" + "\n".join(f"- {c.get('statement')}" for c in claims[:4]))

    artifact_text = "\n\n".join(summary_lines) or "（无子 Agent 输出）"
    text = _last_human_text(state)
    symbol_label = state.get("symbol_name") or state.get("symbol") or "标的"

    if llm_configured():
        model = get_chat_model()
        response = model.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"用户问题：{text}\n标的：{symbol_label}\n\n"
                    f"子 Agent Artifact 摘要：\n{artifact_text}\n\n"
                    "请输出：一句话结论、已验证事实、多方观点、核心分歧、未决问题、免责声明。"
                )
            ),
        ])
        content = str(response.content)
    else:
        pro = artifacts.get("pro_buy", {}).get("metadata", {}).get("thesis", "")
        anti = artifacts.get("anti_buy", {}).get("metadata", {}).get("thesis", "")
        content = (
            f"## 综合研判：{symbol_label}\n\n"
            f"**一句话结论（倾向性，非投资建议）**：多空存在分歧，建议结合估值与持仓自行判断。\n\n"
            f"**支持买入**：{pro or '见 pro_buy Artifact'}\n\n"
            f"**不建议买入**：{anti or '见 anti_buy Artifact'}\n\n"
            f"**子 Agent 输出摘要**：\n{artifact_text}\n\n"
            f"免责声明：{DISCLAIMER}"
        )

    final_report = {
        "symbol": symbol_label,
        "task_id": state["task_id"],
        "content": content,
        "artifacts": {k: v.get("artifact_id") for k, v in artifacts.items()},
        "disclaimer": DISCLAIMER,
    }

    return {
        "messages": [AIMessage(content=content)],
        "final_report": final_report,
        "phase": "done",
        "progress": 100,
        "artifacts_preview": {**state.get("artifacts_preview", {}), "final_summary": content[:400]},
    }


def chat_response(state: MainAgentState) -> dict:
    """通用问答（无流水线）。"""
    text = _last_human_text(state)
    context = f"意图: {state.get('intent')}\n标的: {state.get('symbol_name') or state.get('symbol') or '未识别'}"

    if llm_configured():
        model = get_chat_model()
        response = model.invoke([
            SystemMessage(content="你是 FinTeam 主 Agent，简洁专业回答投研问题。不构成投资建议。"),
            HumanMessage(content=f"{text}\n\n{context}"),
        ])
        content = str(response.content)
    else:
        content = f"已收到：{text}\n\n（未配置 GEMINI_API_KEY，请配置后获得完整回复）\n\n{DISCLAIMER}"

    return {
        "messages": [AIMessage(content=content)],
        "phase": "done",
        "progress": 100,
    }
