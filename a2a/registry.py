"""子 Agent 注册表 — 将 agent_id 映射到 LangGraph 执行函数。"""

from __future__ import annotations

from typing import Any, Callable

from agents.anti_buy.runner import run_anti_buy
from agents.data_collector.runner import run_data_collector
from agents.pro_buy.runner import run_pro_buy
from agents.verification.runner import run_verification

AgentRunner = Callable[[dict[str, Any]], dict[str, Any]]

REGISTRY: dict[str, AgentRunner] = {
    "data_collector": run_data_collector,
    "verification": run_verification,
    "pro_buy": run_pro_buy,
    "anti_buy": run_anti_buy,
}


def invoke_agent(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    runner = REGISTRY.get(agent_id)
    if not runner:
        raise KeyError(f"未知子 Agent: {agent_id}")
    return runner(payload)


def list_agent_ids() -> list[str]:
    return list(REGISTRY.keys())
