"""AntiBuyAgent — 不建议买入（opening / rebuttal）。"""

from __future__ import annotations

from agents.shared.debate import run_debate_side


def run_anti_buy(payload: dict) -> dict:
    return run_debate_side("anti_buy", payload)
