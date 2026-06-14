"""AuthenticityAgent — 资讯/公告与事实交叉验真（LLM + 规则）。"""

from __future__ import annotations

from agents.shared.agent_llm import extract_thesis, invoke_agent_text, text_to_claims
from agents.shared.artifact import make_artifact, make_claim

AUTH_SYSTEM = """你是 FinTeam 真伪验证 Agent。根据已验证事实、资讯标题、公告标题判断信息可信度。
规则：不构成投资建议；无依据的传闻标为存疑；仅基于给定材料，不编造。"""


def run_authenticity(payload: dict) -> dict:
    task_id = payload["task_id"]
    verified_data = payload.get("verified_data") or {}
    claims_in = verified_data.get("metadata", {}).get("verified_claims") or []
    ai_context = verified_data.get("metadata", {}).get("ai_context") or ""

    suspicious_items = []
    trusted_items = []
    for c in claims_in:
        if c.get("source_type") in ("model_inference", "news") or not c.get("verified"):
            suspicious_items.append(c.get("statement", ""))
        else:
            trusted_items.append(c.get("statement", ""))

    symbol_name = payload.get("symbol_name") or payload.get("symbol") or "标的"
    user_prompt = (
        f"标的：{symbol_name}\n"
        f"已验证事实 {len(trusted_items)} 条，待研判 {len(suspicious_items)} 条。\n"
        f"存疑/资讯项：{'；'.join(suspicious_items[:5]) or '无'}\n"
        f"可信项：{'；'.join(trusted_items[:5]) or '无'}\n\n"
        f"投研上下文摘要：\n{ai_context[:2500]}\n\n"
        "请输出：1) 验真结论 2) 存疑项及原因 3) 建议是否继续分析"
    )
    fallback = (
        f"验真完成：可信 {len(trusted_items)} 条，存疑 {len(suspicious_items)} 条。"
        + ("存在存疑项，建议人工确认。" if suspicious_items else "未发现重大存疑。")
    )
    llm_text = invoke_agent_text(system=AUTH_SYSTEM, user=user_prompt, fallback=fallback)

    has_suspicious = len(suspicious_items) > 0 or "存疑" in llm_text

    status_claims = text_to_claims(
        llm_text,
        agent_label="AuthenticityAgent",
        verified_facts=trusted_items[:3],
        max_claims=4,
    )

    return make_artifact(
        task_id=task_id,
        agent_id="authenticity",
        artifact_type="AuthenticityReport",
        claims=status_claims,
        confidence=0.9 if not has_suspicious else 0.55,
        metadata={
            "items": [
                {"statement": s, "status": "suspicious"} for s in suspicious_items[:5]
            ]
            + [{"statement": s, "status": "trusted"} for s in trusted_items[:5]],
            "has_suspicious": has_suspicious,
            "thesis": extract_thesis(llm_text, fallback),
        },
    )
