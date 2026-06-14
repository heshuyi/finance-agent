"""MainAgent LangGraph definition."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.main.nodes import chat_response, prepare_task
from agents.shared.state import MainAgentState, empty_sub_agent_status, new_task_id


def _default_state() -> dict:
    return {
        "task_id": new_task_id(),
        "symbol": "",
        "symbol_name": "",
        "intent": "general",
        "phase": "planning",
        "progress": 0,
        "planned_agents": [],
        "sub_agent_status": empty_sub_agent_status(""),
        "artifacts_preview": {},
        "human_decision": None,
        "final_report": None,
        "errors": [],
    }


def build_main_graph():
    graph = StateGraph(MainAgentState)
    graph.add_node("prepare_task", prepare_task)
    graph.add_node("chat_response", chat_response)
    graph.add_edge(START, "prepare_task")
    graph.add_edge("prepare_task", "chat_response")
    graph.add_edge("chat_response", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


main_graph = build_main_graph()
