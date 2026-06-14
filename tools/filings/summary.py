"""公告标题事件归纳（不读 PDF）。"""

from __future__ import annotations

from agents.shared.llm import get_chat_model, llm_configured
from langchain_core.messages import HumanMessage, SystemMessage


FILING_SUMMARY_SYSTEM = """你是 A 股公告解读助手。仅根据公告标题列表归纳事件与可能影响。
规则：不构成投资建议；无法从标题判断的写「待查阅全文」；每条附序号引用标题。"""


def summarize_filing_titles(
    symbol_name: str,
    items: list[dict],
    *,
    max_items: int = 5,
) -> str:
    titles = [
        f"{i + 1}. {item.get('title', '')}"
        for i, item in enumerate(items[:max_items])
        if item.get("title")
    ]
    if not titles:
        return "【公告事件】近期无法定公告标题可供解读"

    if not llm_configured():
        return "【公告事件】\n" + "\n".join(titles) + "\n（配置 GEMINI_API_KEY 后可获得影响解读）"

    model = get_chat_model(temperature=0.2)
    response = model.invoke([
        SystemMessage(content=FILING_SUMMARY_SYSTEM),
        HumanMessage(
            content=(
                f"标的：{symbol_name}\n公告标题：\n"
                + "\n".join(titles)
                + "\n\n请输出：重要事件列表（每条：事件 + 可能影响一句话），不超过 5 条。"
            )
        ),
    ])
    return f"【公告事件解读】\n{response.content}"
