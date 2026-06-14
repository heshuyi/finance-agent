"""将 Tool 原始数据整理为供 LLM 分析用的上下文文本。"""

from __future__ import annotations

from typing import Any

from tools.compliance import DATA_USE_NOTICE


def _fmt_num(value: Any, *, suffix: str = "") -> str:
    if value is None:
        return "未知"
    if isinstance(value, float) and value > 1e9:
        return f"{value / 1e8:.2f} 亿{suffix}"
    if isinstance(value, (int, float)):
        return f"{value}{suffix}"
    return str(value)


def build_market_context(data: dict[str, Any]) -> str:
    lines = [
        f"【行情快照】{data.get('symbol_name') or ''}（{data.get('symbol')}）",
        f"- 数据源: {data.get('source', '未知')} | 模式: {data.get('mode', '未知')}",
    ]
    if data.get("trade_date"):
        lines.append(f"- 交易日: {data['trade_date']}")
    if data.get("price") is not None:
        lines.append(f"- 最新价: {data['price']} 元")
    if data.get("daily_change_pct") is not None:
        lines.append(f"- 涨跌幅: {data['daily_change_pct']}%")
    if data.get("pe_ttm") is not None:
        lines.append(f"- PE-TTM: {round(float(data['pe_ttm']), 2)}")
    if data.get("volume") is not None:
        lines.append(f"- 成交量: {_fmt_num(data['volume'])}")
    if data.get("_from_cache"):
        lines.append("- 注: 以上行情来自本地缓存（3 个月内）")
    return "\n".join(lines)


def build_financials_context(data: dict[str, Any]) -> str:
    lines = [
        f"【基本面】{data.get('symbol_name') or ''}（{data.get('symbol')}）",
        f"- 数据源: {data.get('source', '未知')}",
    ]
    for label, key in [
        ("PE-TTM", "pe_ttm"),
        ("PE(静)", "pe_static"),
        ("市净率 PB", "pb"),
        ("总市值", "market_cap"),
        ("流通市值", "float_market_cap"),
    ]:
        if data.get(key) is not None:
            val = data[key]
            if key in {"market_cap", "float_market_cap"}:
                lines.append(f"- {label}: {_fmt_num(val)}")
            else:
                lines.append(f"- {label}: {round(float(val), 2) if isinstance(val, (int, float)) else val}")
    return "\n".join(lines)


def build_news_context(data: dict[str, Any], *, max_items: int = 5) -> str:
    items = data.get("items") or []
    if not items:
        return "【相关资讯】暂无可用新闻（不影响其他数据分析）"
    lines = [f"【相关资讯】共 {len(items)} 条，供事件与情绪分析："]
    for idx, item in enumerate(items[:max_items], 1):
        headline = item.get("headline") or item.get("title") or ""
        source = item.get("source") or ""
        summary = (item.get("summary") or "")[:120]
        lines.append(f"{idx}. [{source}] {headline}")
        if summary:
            lines.append(f"   摘要: {summary}")
    return "\n".join(lines)


def build_filings_context(data: dict[str, Any], *, max_items: int = 5) -> str:
    items = data.get("items") or []
    if not items:
        return "【交易所公告】暂无近期公告"
    lines = [f"【交易所公告】共 {len(items)} 条，供合规与事件分析："]
    for idx, item in enumerate(items[:max_items], 1):
        title = item.get("title") or ""
        published = item.get("published_at") or ""
        lines.append(f"{idx}. {title}" + (f"（{published}）" if published else ""))
    return "\n".join(lines)


def build_analysis_context(
    *,
    market: dict[str, Any] | None = None,
    financials: dict[str, Any] | None = None,
    news: dict[str, Any] | None = None,
    filings: dict[str, Any] | None = None,
    symbol: str = "",
    symbol_name: str = "",
) -> str:
    """
    合并多源数据为一段 LLM 可直接消费的投研上下文。
    设计原则：给用户看结论，给 AI 看这些结构化事实。
    """
    header = f"=== 投研数据上下文（供 AI 分析，非投资建议）===\n标的: {symbol_name or symbol or '未指定'}"
    sections = [header]
    if market:
        sections.append(build_market_context(market))
    if financials:
        sections.append(build_financials_context(financials))
    if news:
        sections.append(build_news_context(news))
    if filings:
        sections.append(build_filings_context(filings))
    sections.append("=== 请基于以上事实进行分析，标注数据来源；无法确认处请明确说明 ===")
    sections.append(f"【合规说明】{DATA_USE_NOTICE}")
    return "\n\n".join(sections)
