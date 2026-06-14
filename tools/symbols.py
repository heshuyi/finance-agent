"""A 股代码 → 市场/数据源标识映射 + 全市场简称解析。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


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


@lru_cache(maxsize=1)
def _load_code_name_pairs() -> list[tuple[str, str]]:
    """AKShare 全市场代码表，失败时回退硬编码。"""
    try:
        import akshare as ak

        df = ak.stock_info_a_code_name()
        pairs = [
            (str(row["code"]).zfill(6), str(row["name"]).strip())
            for _, row in df.iterrows()
            if row.get("code") and row.get("name")
        ]
        if pairs:
            return pairs
    except Exception:
        pass
    return list(_NAME_BY_CODE.items())


@lru_cache(maxsize=1)
def _name_to_code_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for code, name in _load_code_name_pairs():
        index[name] = code
    return index


@lru_cache(maxsize=1)
def _code_to_name_index() -> dict[str, str]:
    return {code: name for code, name in _load_code_name_pairs()}


def lookup_name_by_code(code: str) -> str:
    return _code_to_name_index().get(code.zfill(6), _NAME_BY_CODE.get(code, ""))


def lookup_code_by_name(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    index = _name_to_code_index()
    if name in index:
        return index[name]
    for stock_name, code in index.items():
        if name in stock_name or stock_name in name:
            return code
    return ""


def find_symbol_in_text(text: str) -> tuple[str, str]:
    """从文本中解析 A 股代码或简称。返回 (code, name)。"""
    import re

    code_match = re.search(r"\b([036]\d{5})\b", text)
    if code_match:
        code = code_match.group(1)
        return code, lookup_name_by_code(code)

    # 按名称长度降序，优先匹配更长简称
    index = _name_to_code_index()
    for name in sorted(index.keys(), key=len, reverse=True):
        if len(name) >= 2 and name in text:
            return index[name], name

    return "", ""


def resolve_a_share(symbol: str, symbol_name: str = "") -> ResolvedSymbol:
    code = symbol.strip()
    name = symbol_name.strip()

    if not code and name:
        code = lookup_code_by_name(name)

    if not code.isdigit() or len(code) != 6:
        if name:
            looked = lookup_code_by_name(name)
            if looked:
                code = looked
        if not code.isdigit() or len(code) != 6:
            raise ValueError(f"无效的 A 股代码: {symbol or name}")

    code = code.zfill(6)

    if code.startswith(("5", "6", "9")):
        region = "SH"
    elif code.startswith(("0", "2", "3")):
        region = "SZ"
    else:
        region = "SH"

    if not name:
        name = lookup_name_by_code(code)
    return ResolvedSymbol(code=code, region=region, name=name)


def to_ashare_code(resolved: ResolvedSymbol) -> str:
    """Ashare / 新浪 / 腾讯行情代码，如 sh600519、sz300750。"""
    prefix = "sh" if resolved.region == "SH" else "sz"
    return f"{prefix}{resolved.code}"


def to_akshare_daily_symbol(resolved: ResolvedSymbol) -> str:
    """AKShare stock_zh_a_daily 代码格式。"""
    return to_ashare_code(resolved)
