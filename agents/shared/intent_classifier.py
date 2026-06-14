"""LLM 智能意图分类 — 低置信度回退关键词规则。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.shared.intent import ParsedIntent, parse_user_text
from agents.shared.llm import get_chat_model, llm_configured
from agents.shared.state import Intent
from tools.symbols import find_symbol_in_text, lookup_name_by_code

INTENT_SYSTEM = """你是 A 股投研助手的路由分类器。根据用户输入判断意图并提取标的。

意图类型（仅选其一）：
- buy_analysis：是否值得买入、能不能买、分析某股
- sell_analysis：是否卖出、减仓、清仓、持仓处置
- verify_only：核实新闻/消息真伪
- data_query：查行情、PE、估值、新闻、公告等数据
- general：其他通用问题

输出 JSON，字段：
intent, symbol(6位代码或空), symbol_name, confidence(0-1), reason(一句话)

规则：有持仓成本且问卖/减 → sell_analysis；明确查数 → data_query。"""


@dataclass
class ClassifiedIntent:
    intent: Intent
    symbol: str
    symbol_name: str
    planned_agents: list[str]
    position: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    reason: str = ""
    source: str = "rules"


def _planned_for_intent(intent: Intent) -> list[str]:
    mapping: dict[Intent, list[str]] = {
        "buy_analysis": ["data_collector", "verification", "authenticity", "pro_buy", "anti_buy"],
        "sell_analysis": ["data_collector", "verification", "authenticity", "pro_sell", "anti_sell"],
        "verify_only": ["data_collector", "verification", "authenticity"],
        "data_query": [],
        "general": [],
    }
    return list(mapping.get(intent, []))


def _normalize_intent(raw: str) -> Intent:
    allowed: set[Intent] = {
        "buy_analysis", "sell_analysis", "verify_only", "data_query", "general",
    }
    return raw if raw in allowed else "general"


def _parse_llm_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def classify_intent(text: str) -> ClassifiedIntent:
    """LLM 分类；失败或低置信度时回退 parse_user_text。"""
    fallback = parse_user_text(text)
    base = ClassifiedIntent(
        intent=fallback.intent,
        symbol=fallback.symbol,
        symbol_name=fallback.symbol_name,
        planned_agents=fallback.planned_agents,
        position=fallback.position,
        confidence=0.6,
        reason="关键词规则",
        source="rules",
    )

    if not llm_configured():
        return base

    model = get_chat_model(temperature=0.1)
    try:
        response = model.invoke([
            SystemMessage(content=INTENT_SYSTEM),
            HumanMessage(content=f"用户输入：{text}"),
        ])
        data = _parse_llm_json(str(response.content))
    except Exception:
        return base

    if not data:
        return base

    confidence = float(data.get("confidence") or 0)
    if confidence < 0.55:
        return base

    intent = _normalize_intent(str(data.get("intent") or fallback.intent))
    symbol = str(data.get("symbol") or "").strip()
    symbol_name = str(data.get("symbol_name") or "").strip()

    if not symbol:
        symbol, symbol_name = find_symbol_in_text(text)
    if symbol and not symbol_name:
        symbol_name = lookup_name_by_code(symbol)

    planned = _planned_for_intent(intent)
    if "持仓" in text and intent == "general":
        intent = "sell_analysis"
        planned = _planned_for_intent("sell_analysis")

    return ClassifiedIntent(
        intent=intent,
        symbol=symbol or fallback.symbol,
        symbol_name=symbol_name or fallback.symbol_name,
        planned_agents=planned,
        position=fallback.position,
        confidence=confidence,
        reason=str(data.get("reason") or ""),
        source="llm",
    )


def to_parsed_intent(c: ClassifiedIntent) -> ParsedIntent:
    return ParsedIntent(
        intent=c.intent,
        symbol=c.symbol,
        symbol_name=c.symbol_name,
        planned_agents=c.planned_agents,
        position=c.position,
    )
