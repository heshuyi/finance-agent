#!/usr/bin/env python3
"""PR-011 端到端验收脚本 — 直接跑 MainAgent graph（无需浏览器）。"""

from __future__ import annotations

import json
import sys
import uuid

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agents.main.graph import build_main_graph
from agents.shared.llm import llm_configured
from storage.tasks import get_task


def _run_graph(graph, text: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=text)]}
    state: dict = {}

    for chunk in graph.stream(inputs, config=config, stream_mode="values"):
        state = chunk

    snap = graph.get_state(config)
    while snap.next:
        state = graph.invoke(Command(resume="continue"), config=config)
        snap = graph.get_state(config)

    return state


def _assert_phases(feed: list[dict], expected_phases: list[str], label: str) -> None:
    phases = [m.get("phase") for m in feed]
    for p in expected_phases:
        if p not in phases:
            raise AssertionError(f"{label}: team_feed 缺少 phase={p}, got={phases}")


def _assert_arbitration(final_report: dict | None, label: str) -> None:
    if not final_report:
        raise AssertionError(f"{label}: 无 final_report")
    arb = final_report.get("arbitration") or {}
    for key in ("stance", "when_to_buy", "when_may_buy_later", "key_disagreements"):
        if not arb.get(key):
            raise AssertionError(f"{label}: arbitration 缺少 {key}: {arb}")


def verify_buy(graph) -> dict:
    text = "隆基绿能值得买吗"
    state = _run_graph(graph, text, f"verify-buy-{uuid.uuid4()}")
    if state.get("intent") != "buy_analysis":
        raise AssertionError(f"buy intent 期望 buy_analysis, got {state.get('intent')}")

    feed = state.get("team_feed") or []
    _assert_phases(
        feed,
        ["planning", "data", "verify", "auth", "debate_r1", "debate_r2", "debate_r3", "judgment"],
        "buy",
    )

    transcript = state.get("debate_transcript") or {}
    for key in ("opening_pro", "opening_anti", "rebuttal_pro", "rebuttal_anti"):
        if key not in transcript:
            raise AssertionError(f"buy: debate_transcript 缺少 {key}")

    _assert_arbitration(state.get("final_report"), "buy")

    task = get_task(state["task_id"])
    if not task or not task.get("team_feed"):
        raise AssertionError("buy: 持久化 team_feed 为空")

    print(f"[PASS] buy_analysis: task_id={state['task_id']}, feed={len(feed)} msgs")
    return state


def verify_sell(graph) -> dict:
    text = "300750 成本 180 是否减仓"
    state = _run_graph(graph, text, f"verify-sell-{uuid.uuid4()}")
    if state.get("intent") != "sell_analysis":
        raise AssertionError(f"sell intent 期望 sell_analysis, got {state.get('intent')}")

    feed = state.get("team_feed") or []
    _assert_phases(feed, ["planning", "debate_r1", "debate_r2", "debate_r3", "judgment"], "sell")

    transcript = state.get("debate_transcript") or {}
    if "opening_pro" not in transcript or "opening_anti" not in transcript:
        raise AssertionError(f"sell: 辩论记录不完整 {list(transcript)}")

    agents = {m.get("agent_id") for m in feed if str(m.get("phase", "")).startswith("debate")}
    if not ({"pro_sell", "anti_sell"} & agents):
        raise AssertionError(f"sell: 群聊未出现 pro_sell/anti_sell, agents={agents}")

    _assert_arbitration(state.get("final_report"), "sell")
    print(f"[PASS] sell_analysis: task_id={state['task_id']}, feed={len(feed)} msgs")
    return state


def main() -> int:
    print(f"LLM configured: {llm_configured()}")
    graph = build_main_graph(MemorySaver())
    results = {}

    try:
        results["buy"] = verify_buy(graph)
        results["sell"] = verify_sell(graph)
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    summary = {
        "llm_configured": llm_configured(),
        "buy_task_id": results["buy"]["task_id"],
        "sell_task_id": results["sell"]["task_id"],
        "buy_feed_len": len(results["buy"].get("team_feed") or []),
        "sell_feed_len": len(results["sell"].get("team_feed") or []),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
