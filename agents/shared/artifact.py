"""统一 Artifact 结构与构建工具。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

DISCLAIMER = "本输出由 AI 生成，不构成投资建议。请自行判断并承担投资风险。"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_artifact_id() -> str:
    return str(uuid.uuid4())


def make_claim(
    statement: str,
    *,
    verified: bool = True,
    source_type: str = "market_data",
    source_name: str = "FinTeam Mock Connector",
    excerpt: str = "",
    url: Optional[str] = None,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "source_name": source_name,
        "quoted_at": now_iso(),
        "excerpt": excerpt,
    }
    if url:
        evidence["url"] = url
    return {
        "statement": statement,
        "verified": verified,
        "source_type": source_type,
        "evidence": [evidence],
    }


def make_artifact(
    *,
    task_id: str,
    agent_id: str,
    artifact_type: str,
    claims: list[dict[str, Any]],
    confidence: float = 0.8,
    errors: Optional[list[dict[str, Any]]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "artifact_id": new_artifact_id(),
        "task_id": task_id,
        "agent_id": agent_id,
        "artifact_type": artifact_type,
        "confidence": confidence,
        "created_at": now_iso(),
        "claims": claims,
        "errors": errors or [],
        "metadata": metadata or {},
        "disclaimer": DISCLAIMER,
    }
