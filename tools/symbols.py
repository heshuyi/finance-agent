"""A 股代码 → 市场/数据源标识映射。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedSymbol:
    code: str
    region: str
    name: str = ""


_NAME_BY_CODE: dict[str, str] = {
    "600519": "贵州茅台",
    "300750": "宁德时代",
    "002594": "比亚迪",
}


def resolve_a_share(symbol: str, symbol_name: str = "") -> ResolvedSymbol:
    code = symbol.strip()
    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"无效的 A 股代码: {symbol}")

    if code.startswith(("5", "6", "9")):
        region = "SH"
    elif code.startswith(("0", "2", "3")):
        region = "SZ"
    else:
        region = "SH"

    name = symbol_name or _NAME_BY_CODE.get(code, "")
    return ResolvedSymbol(code=code, region=region, name=name)


def to_ashare_code(resolved: ResolvedSymbol) -> str:
    """Ashare / 新浪 / 腾讯行情代码，如 sh600519、sz300750。"""
    prefix = "sh" if resolved.region == "SH" else "sz"
    return f"{prefix}{resolved.code}"


def to_akshare_daily_symbol(resolved: ResolvedSymbol) -> str:
    """AKShare stock_zh_a_daily 代码格式。"""
    return to_ashare_code(resolved)
