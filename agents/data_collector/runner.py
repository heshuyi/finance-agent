"""DataCollectorAgent — mock 市场数据。"""

from __future__ import annotations

from agents.shared.artifact import make_artifact, make_claim

MOCK_QUOTES: dict[str, dict] = {
    "600519": {"name": "贵州茅台", "pe_ttm": 28.5, "price": 1680.0},
    "300750": {"name": "宁德时代", "pe_ttm": 22.1, "price": 198.5},
    "002594": {"name": "比亚迪", "pe_ttm": 24.3, "price": 245.0},
}


def run_data_collector(payload: dict) -> dict:
    task_id = payload["task_id"]
    symbol = payload.get("symbol") or "600519"
    symbol_name = payload.get("symbol_name") or MOCK_QUOTES.get(symbol, {}).get("name", symbol)
    quote = MOCK_QUOTES.get(symbol, {"name": symbol_name, "pe_ttm": 25.0, "price": 100.0})

    claims = [
        make_claim(
            f"{symbol_name}（{symbol}）当前 PE-TTM 为 {quote['pe_ttm']}",
            source_type="market_data",
            excerpt=f"PE_TTM={quote['pe_ttm']}",
        ),
        make_claim(
            f"{symbol_name}（{symbol}）最新价 {quote['price']} 元",
            source_type="market_data",
            excerpt=f"price={quote['price']}",
        ),
        make_claim(
            f"{symbol_name} 近五年 PE 分位约 72%（mock 估算）",
            source_type="model_inference",
            verified=False,
            source_name="FinTeam 模型估算",
        ),
    ]

    return make_artifact(
        task_id=task_id,
        agent_id="data_collector",
        artifact_type="DataBundle",
        claims=claims,
        confidence=0.85,
        metadata={"symbol": symbol, "symbol_name": symbol_name},
    )
