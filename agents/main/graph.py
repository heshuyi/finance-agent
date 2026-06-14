"""MainAgent LangGraph — M5 A2A + HITL + 多轮辩论 + SQLite 持久化。"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from agents.main.debate_nodes import (
    arbitrate,
    debate_anti_rebuttal,
    debate_opening,
    debate_pro_rebuttal,
    should_after_debate,
)
from agents.main.nodes import (
    await_human,
    cancel_task,
    chat_response,
    dispatch_pipeline,
    persist_task,
    prepare_task,
    should_after_await_human,
    should_after_pipeline,
    should_run_pipeline,
    synthesize_judgment,
)
from agents.shared.state import MainAgentState


def build_main_graph(checkpointer: BaseCheckpointSaver):
    graph = StateGraph(MainAgentState)
    graph.add_node("prepare_task", prepare_task)
    graph.add_node("dispatch_pipeline", dispatch_pipeline)
    graph.add_node("await_human", await_human)
    graph.add_node("cancel_task", cancel_task)
    graph.add_node("debate_opening", debate_opening)
    graph.add_node("debate_pro_rebuttal", debate_pro_rebuttal)
    graph.add_node("debate_anti_rebuttal", debate_anti_rebuttal)
    graph.add_node("arbitrate", arbitrate)
    graph.add_node("synthesize_judgment", synthesize_judgment)
    graph.add_node("persist_task", persist_task)
    graph.add_node("chat_response", chat_response)

    graph.add_edge(START, "prepare_task")
    graph.add_conditional_edges("prepare_task", should_run_pipeline, {
        "dispatch_pipeline": "dispatch_pipeline",
        "chat_response": "chat_response",
    })
    graph.add_conditional_edges("dispatch_pipeline", should_after_pipeline, {
        "await_human": "await_human",
        "debate_opening": "debate_opening",
        "synthesize_judgment": "synthesize_judgment",
        "persist_task": "persist_task",
    })
    graph.add_conditional_edges("await_human", should_after_await_human, {
        "cancel_task": "cancel_task",
        "debate_opening": "debate_opening",
        "synthesize_judgment": "synthesize_judgment",
    })
    graph.add_conditional_edges("debate_opening", should_after_debate, {
        "debate_pro_rebuttal": "debate_pro_rebuttal",
        "arbitrate": "arbitrate",
        "persist_task": "persist_task",
    })
    graph.add_conditional_edges("debate_pro_rebuttal", should_after_debate, {
        "debate_anti_rebuttal": "debate_anti_rebuttal",
        "arbitrate": "arbitrate",
        "persist_task": "persist_task",
    })
    graph.add_conditional_edges("debate_anti_rebuttal", should_after_debate, {
        "arbitrate": "arbitrate",
        "persist_task": "persist_task",
    })
    graph.add_edge("arbitrate", "persist_task")
    graph.add_edge("synthesize_judgment", "persist_task")
    graph.add_edge("cancel_task", "persist_task")
    graph.add_edge("persist_task", END)
    graph.add_edge("chat_response", "persist_task")

    return graph.compile(checkpointer=checkpointer)
