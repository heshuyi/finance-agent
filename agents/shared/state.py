"""MainAgent LangGraph state — synced to AG-UI frontend."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class SubAgentStatus(TypedDict):
    agent_id: str
    status: Literal["pending", "working", "completed", "failed", "timeout"]
    message: Optional[str]
    updated_at: str


Phase = Literal[
    "planning", "data", "verify", "auth", "debate", "judgment", "done", "cancelled",
]
Intent = Literal["buy_analysis", "sell_analysis", "verify_only", "data_query", "general"]


class MainAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task_id: str
    symbol: str
    symbol_name: str
    intent: Intent
    phase: Phase
    progress: int
    planned_agents: list[str]
    sub_agent_status: list[SubAgentStatus]
    artifacts: dict
    artifacts_preview: dict
    awaiting_human: Optional[dict]
    human_decision: Optional[str]
    final_report: Optional[dict]
    errors: list[dict]


SUB_AGENT_IDS = [
    "data_collector", "verification", "authenticity",
    "pro_buy", "anti_buy", "pro_sell", "anti_sell",
]


def empty_sub_agent_status(updated_at: str) -> list[SubAgentStatus]:
    return [
        {"agent_id": agent_id, "status": "pending", "message": None, "updated_at": updated_at}
        for agent_id in SUB_AGENT_IDS
    ]


def new_task_id() -> str:
    return str(uuid.uuid4())
