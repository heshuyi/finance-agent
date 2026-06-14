"""子 Agent 共用 LLM 调用与输出解析。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agents.shared.artifact import DISCLAIMER, make_claim
from agents.shared.llm import get_chat_model, llm_configured


def invoke_agent_text(*, system: str, user: str, fallback: str) -> str:
    if not llm_configured():
        return fallback
    model = get_chat_model(temperature=0.35)
    response = model.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])
    return str(response.content).strip()


def text_to_claims(
    text: str,
    *,
    agent_label: str,
    verified_facts: list[str] | None = None,
    max_claims: int = 4,
) -> list[dict]:
    claims = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•*").strip()
        if not line or len(line) < 8:
            continue
        is_inference = "推断" in line or "可能" in line or "预计" in line
        claims.append(
            make_claim(
                line[:300],
                source_type="model_inference" if is_inference else "market_data",
                verified=not is_inference and bool(verified_facts),
                source_name=agent_label,
            )
        )
        if len(claims) >= max_claims:
            break

    if not claims:
        claims.append(
            make_claim(
                text[:400] or "（无输出）",
                source_type="model_inference",
                verified=False,
                source_name=agent_label,
            )
        )

    if verified_facts:
        claims.append(
            make_claim(
                "已验证事实参考：" + "；".join(verified_facts[:3]),
                source_type="market_data",
                verified=True,
                source_name="DataVerificationAgent",
            )
        )
    return claims


def extract_thesis(text: str, default: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("核心观点", "结论", "论点", "thesis", "**")):
            return line.lstrip("*").replace("核心观点：", "").replace("结论：", "").strip() or default
    first = next((ln.strip() for ln in text.splitlines() if len(ln.strip()) > 10), "")
    return first[:200] or default
