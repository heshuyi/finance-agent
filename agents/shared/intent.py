"""Lightweight intent and symbol extraction — 全市场简称 + 持仓解析。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agents.shared.state import Intent
from tools.symbols import find_symbol_in_text

_SYMBOL_CODE = re.compile(r"\b([036]\d{5})\b")
_COST_RE = re.compile(
    r"(?:成本|买入价|持仓价|成交价|均价)[^\d]{0,6}(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_QTY_RE = re.compile(r"(?:持仓|持有|买了)[^\d]{0,4}(\d+(?:\.\d+)?)\s*(?:股|手)?")
_PROFIT_RE = re.compile(r"(?:盈利|赚了|浮盈|收益率)[^\d]{0,4}(\d+(?:\.\d+)?)\s*%?")


@dataclass
class ParsedIntent:
    intent: Intent
    symbol: str
    symbol_name: str
    planned_agents: list[str]
    position: dict[str, Any] = field(default_factory=dict)


def _parse_position(text: str) -> dict[str, Any]:
    position: dict[str, Any] = {}
    cost = _COST_RE.search(text)
    if cost:
        position["cost_price"] = float(cost.group(1))
    qty = _QTY_RE.search(text)
    if qty:
        position["quantity"] = float(qty.group(1))
    profit = _PROFIT_RE.search(text)
    if profit:
        position["profit_pct"] = float(profit.group(1))
    return position


def parse_user_text(text: str) -> ParsedIntent:
    code_match = _SYMBOL_CODE.search(text)
    if code_match:
        symbol = code_match.group(1)
        from tools.symbols import lookup_name_by_code

        symbol_name = lookup_name_by_code(symbol)
    else:
        symbol, symbol_name = find_symbol_in_text(text)

    position = _parse_position(text)

    if any(k in text for k in ("卖出", "减仓", "清仓", "止盈")) or (
        "持仓" in text and any(k in text for k in ("卖", "减", "清", "止盈", "成本", "盈利"))
    ):
        intent: Intent = "sell_analysis"
        planned = ["data_collector", "verification", "authenticity", "pro_sell", "anti_sell"]
    elif any(k in text for k in ("核实", "验真", "真假", "是否真实")):
        intent = "verify_only"
        planned = ["data_collector", "verification", "authenticity"]
    elif any(
        k in text
        for k in (
            "PE", "pe", "PB", "pb", "估值", "分位", "营收", "查", "走势",
            "新闻", "资讯", "公告", "行情", "股价", "净利", "同比",
        )
    ):
        intent = "data_query"
        planned = []
    elif any(k in text for k in ("买入", "值得买", "能不能买", "分析")):
        intent = "buy_analysis"
        planned = ["data_collector", "verification", "authenticity", "pro_buy", "anti_buy"]
    else:
        intent = "general"
        planned = []

    if "持仓" in text and intent == "general":
        intent = "sell_analysis"
        planned = ["data_collector", "verification", "authenticity", "pro_sell", "anti_sell"]

    return ParsedIntent(
        intent=intent,
        symbol=symbol,
        symbol_name=symbol_name,
        planned_agents=planned,
        position=position,
    )
