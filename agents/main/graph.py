"""MainAgent LangGraph — M2 A2A + HITL 编排。"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.main.nodes import (
    await_human,
    cancel_task,
    chat_response,
    dispatch_debate,
    dispatch_pipeline,
    prepare_task,
    should_after_await_human,
    should_after_pipeline,
    should_run_pipeline,
    synthesize_judgment,
)
from agents.shared.state import MainAgentState


def build_main_graph():
    graph = StateGraph(MainAgentState)
    graph.add_node("prepare_task", prepare_task)
    graph.add_node("dispatch_pipeline", dispatch_pipeline)
    graph.add_node("await_human", await_human)
    graph.add_node("cancel_task", cancel_task)
    graph.add_node("dispatch_debate", dispatch_debate)
    graph.add_node("synthesize_judgment", synthesize_judgment)
    graph.add_node("chat_response", chat_response)

    graph.add_edge(START, "prepare_task")
    graph.add_conditional_edges("prepare_task", should_run_pipeline, {
        "dispatch_pipeline": "dispatch_pipeline",
        "chat_response": "chat_response",
    })
    graph.add_conditional_edges("dispatch_pipeline", should_after_pipeline, {
        "await_human": "await_human",
        "dispatch_debate": "dispatch_debate",
        "synthesize_judgment": "synthesize_judgment",
    })
    graph.add_conditional_edges("await_human", should_after_await_human, {
        "cancel_task": "cancel_task",
        "dispatch_debate": "dispatch_debate",
        "synthesize_judgment": "synthesize_judgment",
    })
    graph.add_edge("dispatch_debate", "synthesize_judgment")
    graph.add_edge("synthesize_judgment", END)
    graph.add_edge("cancel_task", END)
    graph.add_edge("chat_response", END)

    return graph.compile(checkpointer=MemorySaver())


main_graph = build_main_graph()
