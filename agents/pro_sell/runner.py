"""ProSellAgent — 建议卖出（opening / rebuttal）。"""

from __future__ import annotations

from agents.shared.debate import run_debate_side


def run_pro_sell(payload: dict) -> dict:
    return run_debate_side("pro_sell", payload)
