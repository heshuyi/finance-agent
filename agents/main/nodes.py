"""MainAgent LangGraph nodes — M2 A2A + HITL。"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from a2a.client import send_task_async
from a2a.types import TaskStatus
from agents.shared.artifact import DISCLAIMER
from agents.shared.intent import parse_user_text
from agents.shared.llm import get_chat_model, llm_configured
from agents.shared.state import MainAgentState, empty_sub_agent_status, new_task_id

PIPELINE_INTENTS = {"buy_analysis", "sell_analysis", "verify_only"}

CHAT_CONTEXT_KEYWORDS = (
    "行情", "股价", "价格", "涨跌", "市值", "估值", "PE", "pe", "pb", "PB",
    "新闻", "资讯", "公告", "财报", "营收", "净利", "走势", "怎么样", "如何",
)

CHAT_RESPONSE_SYSTEM = """你是 FinTeam 主 Agent，基于提供的「投研数据上下文」回答用户问题。
这些数据来自公开渠道或用户配置的授权 API，仅供个人投研辅助参考。

硬性规则：
- 不构成投资建议，不得承诺收益、必涨、稳赚等表述
- 明确标注数据来源（行情/资讯/法定公告）
- 资讯与公告仅作事件参考，不代表官方背书
- 数据不足或来源冲突时如实说明，不编造
- 回答简洁专业，末尾附免责声明
"""

SYSTEM_PROMPT = """你是 FinTeam Agent 的主编排 Agent（投研团队负责人）。
子 Agent 已通过 Tool 拉取行情、资讯、公告等事实数据，并整理为「投研数据上下文」供你分析。
你的任务是解读这些事实，而非复述原始数据。

硬性规则：
- 不构成投资建议，末尾附免责声明
- 仅引用已验证（verified=true）的数据作为核心论据
- 标注多空分歧与未决问题
- 语气专业、简洁
"""

DEBATE_CONFIG: dict[str, list[tuple[str, str]]] = {
    "buy_analysis": [
        ("pro_buy", "bull-case"),
        ("anti_buy", "bear-case-no-buy"),
    ],
    "sell_analysis": [
        ("pro_sell", "bull-sell-case"),
        ("anti_sell", "bear-hold-case"),
    ],
}


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


def _should_load_chat_context(state: MainAgentState) -> bool:
    symbol = state.get("symbol")
    if symbol:
        return True
    text = _last_human_text(state)
    return any(k in text for k in CHAT_CONTEXT_KEYWORDS)


def _resolve_chat_symbol(state: MainAgentState) -> tuple[str, str]:
    symbol = state.get("symbol") or ""
    name = state.get("symbol_name") or ""
    if symbol:
        return symbol, name
    parsed = parse_user_text(_last_human_text(state))
    return parsed.symbol, parsed.symbol_name


def _load_chat_ai_context(state: MainAgentState) -> str | None:
    if not _should_load_chat_context(state):
        return None
    symbol, name = _resolve_chat_symbol(state)
    if not symbol:
        return None
    from tools.context_loader import load_analysis_context

    try:
        return load_analysis_context(symbol, name, limit=5)
    except Exception as exc:
        return f"（投研数据拉取失败: {exc}，请基于已有信息回答）"


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


def _auth_needs_human(state: MainAgentState) -> bool:
    if state.get("human_decision"):
        return False
    auth = (state.get("artifacts") or {}).get("authenticity") or {}
    return bool(auth.get("metadata", {}).get("has_suspicious"))


def _next_debate_or_synth(state: MainAgentState) -> str:
    intent = state.get("intent", "general")
    planned = state.get("planned_agents") or []
    if intent in DEBATE_CONFIG and any(aid in planned for aid, _ in DEBATE_CONFIG[intent]):
        return "dispatch_debate"
    return "synthesize_judgment"


def should_run_pipeline(state: MainAgentState) -> str:
    intent = state.get("intent", "general")
    planned = state.get("planned_agents") or []
    # 行情/新闻/公告类轻量查询：注入 ai_context 后直接快答，不走子 Agent 流水线
    if intent == "data_query":
        return "chat_response"
    if intent in PIPELINE_INTENTS and planned:
        return "dispatch_pipeline"
    return "chat_response"


def should_after_pipeline(state: MainAgentState) -> str:
    if _auth_needs_human(state):
        return "await_human"
    return _next_debate_or_synth(state)


def should_after_await_human(state: MainAgentState) -> str:
    if state.get("human_decision") == "abort":
        return "cancel_task"
    return _next_debate_or_synth(state)


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
        "awaiting_human": None,
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
        work_state.update({"artifacts": artifacts, "sub_agent_status": sub_status, "errors": errors})

    if "authenticity" in state.get("planned_agents", []) and artifacts.get("verification"):
        artifacts, sub_status, errors = await _run_agent(
            {**work_state, "sub_agent_status": sub_status, "artifacts": artifacts, "errors": errors},
            "authenticity",
            "verify-authenticity",
            {"task_id": state["task_id"], "verified_data": artifacts["verification"]},
        )

    if artifacts.get("authenticity"):
        phase = "auth"
        progress = 55
    elif artifacts.get("verification"):
        phase = "verify"
        progress = 45
    else:
        phase = "data"
        progress = 30

    auth = artifacts.get("authenticity") or {}
    awaiting_human = None
    if auth.get("metadata", {}).get("has_suspicious"):
        items = auth.get("metadata", {}).get("items") or []
        suspicious = [i["statement"] for i in items if i.get("status") == "suspicious"]
        awaiting_human = {
            "reason": "验真发现存疑信息，需人工确认是否继续",
            "options": ["continue", "abort"],
            "suspicious_items": suspicious[:5],
        }

    return {
        "artifacts": artifacts,
        "sub_agent_status": sub_status,
        "errors": errors,
        "phase": phase,
        "progress": progress,
        "awaiting_human": awaiting_human,
    }


def await_human(state: MainAgentState) -> dict:
    """LangGraph interrupt — 验真存疑时等待用户确认。"""
    auth = (state.get("artifacts") or {}).get("authenticity") or {}
    items = auth.get("metadata", {}).get("items") or []
    suspicious = [i["statement"] for i in items if i.get("status") == "suspicious"]
    payload = state.get("awaiting_human") or {
        "reason": "验真发现存疑信息，是否继续后续辩论与终裁？",
        "suspicious_items": suspicious[:5],
        "options": ["continue", "abort"],
    }

    decision = interrupt(payload)
    normalized = "continue" if decision in ("continue", "继续", True) else "abort"

    return {
        "human_decision": normalized,
        "awaiting_human": None,
        "phase": "debate" if normalized == "continue" else "cancelled",
        "progress": 60 if normalized == "continue" else 100,
    }


def cancel_task(state: MainAgentState) -> dict:
    return {
        "messages": [AIMessage(content="已终止：验真存疑项未通过人工确认，本次分析已取消。")],
        "phase": "cancelled",
        "progress": 100,
        "awaiting_human": None,
        "final_report": None,
    }


def dispatch_debate(state: MainAgentState) -> dict:
    return _run_async(_dispatch_debate_async(state))


async def _dispatch_debate_async(state: MainAgentState) -> dict:
    artifacts = dict(state.get("artifacts") or {})
    sub_status = list(state.get("sub_agent_status") or [])
    errors = list(state.get("errors") or [])
    intent = state.get("intent", "buy_analysis")
    pairs = DEBATE_CONFIG.get(intent, DEBATE_CONFIG["buy_analysis"])

    base_input = {
        "task_id": state["task_id"],
        "symbol": state.get("symbol"),
        "symbol_name": state.get("symbol_name"),
        "verified_data": artifacts.get("verification"),
    }

    async def run_one(agent_id: str, skill: str) -> tuple[dict, list, list]:
        ws = {
            **state,
            "artifacts": dict(artifacts),
            "sub_agent_status": [dict(r) for r in sub_status],
            "errors": list(errors),
        }
        return await _run_agent(ws, agent_id, skill, base_input)

    results = await asyncio.gather(*(run_one(aid, skill) for aid, skill in pairs))
    for new_arts, new_sts, new_errs in results:
        artifacts.update(new_arts)
        errors.extend(new_errs)
        by_id = {r["agent_id"]: r for r in sub_status}
        for row in new_sts:
            by_id[row["agent_id"]] = row
        sub_status = list(by_id.values())

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

    data_bundle = artifacts.get("data_collector") or {}
    ai_context = (data_bundle.get("metadata") or {}).get("ai_context")
    if ai_context:
        summary_lines.append(f"### 投研数据上下文（data_collector）\n{ai_context}")

    for aid, art in artifacts.items():
        if aid == "data_collector" and ai_context:
            continue
        claims = art.get("claims") or []
        summary_lines.append(f"### {aid}\n" + "\n".join(f"- {c.get('statement')}" for c in claims[:4]))

    artifact_text = "\n\n".join(summary_lines) or "（无子 Agent 输出）"
    text = _last_human_text(state)
    symbol_label = state.get("symbol_name") or state.get("symbol") or "标的"
    intent = state.get("intent", "general")

    if llm_configured():
        model = get_chat_model()
        response = model.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"用户问题：{text}\n标的：{symbol_label}\n意图：{intent}\n\n"
                    f"子 Agent Artifact 摘要：\n{artifact_text}\n\n"
                    "请输出：一句话结论、已验证事实、多方观点、核心分歧、未决问题、免责声明。"
                )
            ),
        ])
        content = str(response.content)
    else:
        pro = artifacts.get("pro_buy", {}).get("metadata", {}).get("thesis", "")
        anti = artifacts.get("anti_buy", {}).get("metadata", {}).get("thesis", "")
        pro_sell = artifacts.get("pro_sell", {}).get("metadata", {}).get("thesis", "")
        anti_sell = artifacts.get("anti_sell", {}).get("metadata", {}).get("thesis", "")
        content = (
            f"## 综合研判：{symbol_label}\n\n"
            f"**一句话结论（倾向性，非投资建议）**：多空存在分歧，建议结合估值与持仓自行判断。\n\n"
        )
        if intent == "sell_analysis":
            content += (
                f"**建议卖出**：{pro_sell or '见 pro_sell Artifact'}\n\n"
                f"**建议持有**：{anti_sell or '见 anti_sell Artifact'}\n\n"
            )
        elif intent == "buy_analysis":
            content += (
                f"**支持买入**：{pro or '见 pro_buy Artifact'}\n\n"
                f"**不建议买入**：{anti or '见 anti_buy Artifact'}\n\n"
            )
        content += f"**子 Agent 输出摘要**：\n{artifact_text}\n\n免责声明：{DISCLAIMER}"

    final_report = {
        "symbol": symbol_label,
        "task_id": state["task_id"],
        "intent": intent,
        "content": content,
        "artifacts": {k: v.get("artifact_id") for k, v in artifacts.items()},
        "debate": {
            "pro_buy": artifacts.get("pro_buy"),
            "anti_buy": artifacts.get("anti_buy"),
            "pro_sell": artifacts.get("pro_sell"),
            "anti_sell": artifacts.get("anti_sell"),
        },
        "disclaimer": DISCLAIMER,
    }

    return {
        "messages": [AIMessage(content=content)],
        "final_report": final_report,
        "phase": "done",
        "progress": 100,
        "artifacts_preview": {**state.get("artifacts_preview", {}), "final_summary": content[:400]},
        "awaiting_human": None,
    }


def chat_response(state: MainAgentState) -> dict:
    """通用问答（无流水线）— 有标的时自动注入投研数据上下文供 AI 分析。"""
    text = _last_human_text(state)
    symbol = state.get("symbol_name") or state.get("symbol") or "未识别"
    ai_context = _load_chat_ai_context(state)

    user_parts = [f"用户问题：{text}", f"标的：{symbol}"]
    if ai_context:
        user_parts.append(f"\n投研数据上下文（供分析，勿原样复述）：\n{ai_context}")
    else:
        user_parts.append("\n（未识别标的或未触发数据拉取，请基于常识简要回答并提示用户提供股票代码）")

    if llm_configured():
        model = get_chat_model()
        response = model.invoke([
            SystemMessage(content=CHAT_RESPONSE_SYSTEM),
            HumanMessage(content="\n".join(user_parts)),
        ])
        content = str(response.content)
        if DISCLAIMER not in content:
            content = f"{content}\n\n{DISCLAIMER}"
    else:
        if ai_context:
            content = (
                f"已收到：{text}\n\n"
                f"（未配置 GEMINI_API_KEY，以下为拉取到的投研数据上下文，配置 LLM 后可获得分析解读）\n\n"
                f"{ai_context}\n\n{DISCLAIMER}"
            )
        else:
            content = f"已收到：{text}\n\n（未配置 GEMINI_API_KEY，请配置后获得完整回复）\n\n{DISCLAIMER}"

    preview = dict(state.get("artifacts_preview") or {})
    if ai_context:
        preview["ai_context"] = ai_context[:2000]

    return {
        "messages": [AIMessage(content=content)],
        "phase": "done",
        "progress": 100,
        "artifacts_preview": preview,
        "final_report": {"type": "chat", "content": content},
    }


def persist_task(state: MainAgentState) -> dict:
    """研判结束后写入 SQLite（Task + Artifact 链）。"""
    from storage.tasks import save_task_record

    preview = state.get("artifacts_preview") or {}
    save_task_record(
        task_id=state["task_id"],
        symbol=state.get("symbol"),
        symbol_name=state.get("symbol_name"),
        intent=state.get("intent", "general"),
        phase=state.get("phase", "done"),
        user_query=preview.get("user_query"),
        final_report=state.get("final_report"),
        artifacts=state.get("artifacts") or {},
        sub_agent_status=state.get("sub_agent_status"),
        human_decision=state.get("human_decision"),
        errors=state.get("errors"),
    )
    return {}
