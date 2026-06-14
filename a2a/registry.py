"""子 Agent 注册表 — 将 agent_id 映射到 LangGraph 执行函数。"""

from __future__ import annotations

from typing import Any, Callable

from agents.arbitrator.runner import run_arbitrator
from agents.anti_buy.runner import run_anti_buy
from agents.anti_sell.runner import run_anti_sell
from agents.authenticity.runner import run_authenticity
from agents.data_collector.runner import run_data_collector
from agents.pro_buy.runner import run_pro_buy
from agents.pro_sell.runner import run_pro_sell
from agents.verification.runner import run_verification

AgentRunner = Callable[[dict[str, Any]], dict[str, Any]]

REGISTRY: dict[str, AgentRunner] = {
    "data_collector": run_data_collector,
    "verification": run_verification,
    "authenticity": run_authenticity,
    "pro_buy": run_pro_buy,
    "anti_buy": run_anti_buy,
    "pro_sell": run_pro_sell,
    "anti_sell": run_anti_sell,
    "arbitrator": run_arbitrator,
}


def invoke_agent(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    runner = REGISTRY.get(agent_id)
    if not runner:
        raise KeyError(f"未知子 Agent: {agent_id}")
    return runner(payload)


def list_agent_ids() -> list[str]:
    return list(REGISTRY.keys())
