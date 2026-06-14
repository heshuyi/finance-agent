"""AntiSellAgent — 建议持有（opening / rebuttal）。"""

from __future__ import annotations

from agents.shared.debate import run_debate_side


def run_anti_sell(payload: dict) -> dict:
    return run_debate_side("anti_sell", payload)
