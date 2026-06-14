"""Lightweight intent and symbol extraction (M0)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agents.shared.state import Intent

_SYMBOL_CODE = re.compile(r"\b([036]\d{5})\b")
_SYMBOL_NAME_HINTS: dict[str, str] = {
    "贵州茅台": "600519",
    "茅台": "600519",
    "宁德时代": "300750",
    "比亚迪": "002594",
}


@dataclass
class ParsedIntent:
    intent: Intent
    symbol: str
    symbol_name: str
    planned_agents: list[str]


def parse_user_text(text: str) -> ParsedIntent:
    symbol = ""
    symbol_name = ""

    code_match = _SYMBOL_CODE.search(text)
    if code_match:
        symbol = code_match.group(1)

    for name, code in _SYMBOL_NAME_HINTS.items():
        if name in text:
            symbol_name = name
            if not symbol:
                symbol = code
            break

    if any(k in text for k in ("卖出", "减仓", "清仓", "止盈")):
        intent: Intent = "sell_analysis"
        planned = ["data_collector", "verification", "pro_sell", "anti_sell"]
    elif any(k in text for k in ("核实", "验真", "真假", "是否真实")):
        intent = "verify_only"
        planned = ["data_collector", "verification", "authenticity"]
    elif any(k in text for k in ("PE", "pe", "估值", "营收", "查", "走势", "净值")):
        intent = "data_query"
        planned = ["data_collector", "verification"]
    elif any(k in text for k in ("买入", "值得买", "能不能买", "分析")):
        intent = "buy_analysis"
        planned = ["data_collector", "verification", "pro_buy", "anti_buy"]
    else:
        intent = "general"
        planned = []

    if "持仓" in text and intent == "general":
        intent = "sell_analysis"
        planned = ["data_collector", "verification", "pro_sell", "anti_sell"]

    return ParsedIntent(intent=intent, symbol=symbol, symbol_name=symbol_name, planned_agents=planned)
