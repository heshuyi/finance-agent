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
    summary = data.get("event_summary")
    if summary:
        lines.append("")
        lines.append(summary)
    return "\n".join(lines)


def build_valuation_context(data: dict[str, Any]) -> str:
    latest = data.get("latest") or {}
    lines = [
        f"【估值历史】{data.get('symbol_name') or ''}（{data.get('symbol')}）",
        f"- 数据源: {data.get('source', 'AKShare')} | 样本: 近 {data.get('days', 365)} 日 {data.get('sample_count', 0)} 点",
    ]
    if latest.get("trade_date"):
        lines.append(f"- 最新估值日: {latest['trade_date']}")
    if latest.get("pe_ttm") is not None:
        lines.append(f"- PE-TTM: {round(float(latest['pe_ttm']), 2)}")
    if data.get("pe_percentile_1y") is not None:
        lines.append(f"- PE 近一年分位: {data['pe_percentile_1y']}%（越高表示相对历史越贵）")
    if latest.get("pb") is not None:
        lines.append(f"- PB: {round(float(latest['pb']), 2)}")
    if data.get("pb_percentile_1y") is not None:
        lines.append(f"- PB 近一年分位: {data['pb_percentile_1y']}%")
    samples = data.get("series_sample") or []
    if samples:
        lines.append("- PE 走势采样（日期: PE）:")
        for row in samples:
            pe = row.get("pe_ttm")
            if pe is not None:
                lines.append(f"  · {row.get('trade_date', '?')}: {round(float(pe), 2)}")
    return "\n".join(lines)


def build_indicators_context(data: dict[str, Any]) -> str:
    highlights = data.get("highlights") or []
    if not highlights:
        return "【财务指标趋势】暂无可用指标数据"
    lines = [f"【财务指标趋势】{data.get('symbol_name') or data.get('symbol')}"]
    lines.extend(f"- {h}" for h in highlights[:6])
    return "\n".join(lines)


def build_peers_context(data: dict[str, Any]) -> str:
    peers = data.get("peers") or []
    industry = data.get("industry") or "未知"
    if not peers:
        return f"【同业对比】行业: {industry}（暂无同业样本）"
    lines = [
        f"【同业对比】{data.get('symbol_name')} 所属行业: {industry}",
        "代码 | 名称 | PE(动)/EPS | PB",
    ]
    for p in peers:
        pe = p.get("pe_ttm")
        pb = p.get("pb")
        pe_label = p.get("metric_note", "PE(动)")
        pe_s = round(float(pe), 2) if pe is not None else "-"
        pb_s = round(float(pb), 2) if pb is not None else "-"
        lines.append(f"{p.get('symbol')} | {p.get('symbol_name')} | {pe_s} ({pe_label}) | {pb_s}")
    return "\n".join(lines)


def build_position_context(position: dict[str, Any] | None) -> str:
    if not position:
        return ""
    lines = ["【持仓情境】"]
    if position.get("cost_price") is not None:
        lines.append(f"- 持仓成本: {position['cost_price']} 元")
    if position.get("quantity") is not None:
        lines.append(f"- 持仓数量: {position['quantity']}")
    if position.get("profit_pct") is not None:
        lines.append(f"- 估算盈亏: {position['profit_pct']}%")
    elif position.get("current_price") is not None and position.get("cost_price") is not None:
        cost = float(position["cost_price"])
        cur = float(position["current_price"])
        if cost > 0:
            pct = round((cur - cost) / cost * 100, 2)
            lines.append(f"- 估算盈亏: {pct}%（现价 {cur} vs 成本 {cost}）")
    return "\n".join(lines) if len(lines) > 1 else ""


def build_analysis_context(
    *,
    market: dict[str, Any] | None = None,
    financials: dict[str, Any] | None = None,
    news: dict[str, Any] | None = None,
    filings: dict[str, Any] | None = None,
    valuation: dict[str, Any] | None = None,
    indicators: dict[str, Any] | None = None,
    peers: dict[str, Any] | None = None,
    position: dict[str, Any] | None = None,
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
    if valuation:
        sections.append(build_valuation_context(valuation))
    if indicators:
        sections.append(build_indicators_context(indicators))
    if peers:
        sections.append(build_peers_context(peers))
    pos_ctx = build_position_context(position)
    if pos_ctx:
        sections.append(pos_ctx)
    if news:
        sections.append(build_news_context(news))
    if filings:
        sections.append(build_filings_context(filings))
    sections.append("=== 请基于以上事实进行分析，标注数据来源；无法确认处请明确说明 ===")
    sections.append(f"【合规说明】{DATA_USE_NOTICE}")
    return "\n\n".join(sections)
