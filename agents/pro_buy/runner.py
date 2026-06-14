"""ProBuyAgent — 支持买入（opening / rebuttal）。"""

from __future__ import annotations

from agents.shared.debate import run_debate_side


def run_pro_buy(payload: dict) -> dict:
    return run_debate_side("pro_buy", payload)
