"""MainAgent LangGraph nodes."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.shared.intent import parse_user_text
from agents.shared.state import MainAgentState, empty_sub_agent_status, new_task_id

SYSTEM_PROMPT = """你是 FinTeam Agent 的主编排 Agent（投研团队负责人）。
你的职责：
1. 理解用户的投研诉求（查数、买入分析、卖出分析、信息验真等）
2. 说明你将如何调度团队（数据获取、核查、验真、多空辩论、终裁）
3. 当前为 M0 阶段：子 Agent 尚未全部接入，请如实说明将执行的流水线，并给出初步分析框架

硬性规则：
- 不构成投资建议，末尾附简短免责
- 不编造具体财务数字；无数据时说明将由数据 Agent 获取
- 语气专业、简洁
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _last_human_text(state: MainAgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def prepare_task(state: MainAgentState) -> dict:
    """Parse intent and initialize AG-UI sync fields."""
    text = _last_human_text(state)
    parsed = parse_user_text(text)
    now = _now_iso()

    sub_status = empty_sub_agent_status(now)
    for row in sub_status:
        if row["agent_id"] in parsed.planned_agents:
            row["status"] = "pending"
            row["message"] = "等待调度（M1 接入 A2A）"

    preview = {
        "user_query": text[:500],
        "note": "M0：子 Agent 流水线将在 M1 通过 A2A 自动执行",
    }

    return {
        "task_id": state.get("task_id") or new_task_id(),
        "symbol": parsed.symbol,
        "symbol_name": parsed.symbol_name,
        "intent": parsed.intent,
        "phase": "planning",
        "progress": 15,
        "planned_agents": parsed.planned_agents,
        "sub_agent_status": sub_status,
        "artifacts_preview": preview,
        "human_decision": None,
        "final_report": None,
        "errors": [],
    }


def chat_response(state: MainAgentState) -> dict:
    """LLM response with task context; updates phase to done for M0."""
    text = _last_human_text(state)
    parsed = parse_user_text(text)

    context = (
        f"任务ID: {state.get('task_id')}\n"
        f"意图: {state.get('intent', parsed.intent)}\n"
        f"标的代码: {state.get('symbol') or '未识别'}\n"
        f"标的名称: {state.get('symbol_name') or '未识别'}\n"
        f"计划调度子Agent: {', '.join(state.get('planned_agents') or []) or '无（通用问答）'}\n"
    )

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0.3,
    )

    if not os.getenv("OPENAI_API_KEY"):
        content = (
            f"已收到您的诉求。\n\n{context}\n"
            "【M0 提示】未配置 OPENAI_API_KEY，这是离线占位回复。"
            "请在项目根目录复制 .env.example 为 .env 并填入 API Key 后重启 API。\n\n"
            "计划流水线：取数 → 核查 → 验真 → 多空辩论 → 主 Agent 终裁（M1 起自动执行）。\n\n"
            "免责声明：本输出由 AI 生成，不构成投资建议。"
        )
    else:
        response = model.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"用户问题：{text}\n\n当前任务上下文：\n{context}"),
        ])
        content = str(response.content)

    now = _now_iso()
    sub_status = state.get("sub_agent_status") or empty_sub_agent_status(now)
    for row in sub_status:
        if row["agent_id"] in (state.get("planned_agents") or []):
            row["status"] = "pending"
            row["message"] = "M1 将通过 A2A 自动调度"

    return {
        "messages": [AIMessage(content=content)],
        "phase": "done",
        "progress": 100,
        "sub_agent_status": sub_status,
        "artifacts_preview": {
            **(state.get("artifacts_preview") or {}),
            "assistant_summary": content[:300],
        },
    }
