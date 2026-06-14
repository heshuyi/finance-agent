"""Task / Artifact 持久化读写。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from storage.db import get_connection, init_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)


def save_task_record(
    *,
    task_id: str,
    symbol: str | None,
    symbol_name: str | None,
    intent: str,
    phase: str,
    user_query: str | None,
    final_report: dict | None,
    artifacts: dict[str, Any],
    sub_agent_status: list[dict] | None,
    human_decision: str | None,
    errors: list[dict] | None,
) -> None:
    init_db()
    now = _now_iso()
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT created_at FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        created_at = existing["created_at"] if existing else now

        conn.execute(
            """
            INSERT INTO tasks (
                task_id, symbol, symbol_name, intent, phase, user_query,
                final_report, artifacts, sub_agent_status, human_decision,
                errors, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                symbol = excluded.symbol,
                symbol_name = excluded.symbol_name,
                intent = excluded.intent,
                phase = excluded.phase,
                user_query = excluded.user_query,
                final_report = excluded.final_report,
                artifacts = excluded.artifacts,
                sub_agent_status = excluded.sub_agent_status,
                human_decision = excluded.human_decision,
                errors = excluded.errors,
                updated_at = excluded.updated_at
            """,
            (
                task_id,
                symbol or "",
                symbol_name or "",
                intent,
                phase,
                user_query or "",
                _json_dumps(final_report) if final_report else None,
                _json_dumps(artifacts or {}),
                _json_dumps(sub_agent_status or []),
                human_decision,
                _json_dumps(errors or []),
                created_at,
                now,
            ),
        )

        conn.execute("DELETE FROM artifacts WHERE task_id = ?", (task_id,))
        for agent_id, artifact in (artifacts or {}).items():
            if not isinstance(artifact, dict):
                continue
            artifact_id = artifact.get("artifact_id") or f"{task_id}:{agent_id}"
            conn.execute(
                """
                INSERT INTO artifacts (
                    artifact_id, task_id, agent_id, artifact_type, payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    task_id,
                    agent_id,
                    artifact.get("artifact_type"),
                    _json_dumps(artifact),
                    artifact.get("created_at") or now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def list_tasks(*, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    init_db()
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        rows = conn.execute(
            """
            SELECT task_id, symbol, symbol_name, intent, phase, user_query,
                   final_report, created_at, updated_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        tasks = []
        for row in rows:
            final_report = _json_loads(row["final_report"])
            summary = ""
            if isinstance(final_report, dict):
                content = final_report.get("content") or ""
                summary = content[:200]
            tasks.append({
                "task_id": row["task_id"],
                "symbol": row["symbol"],
                "symbol_name": row["symbol_name"],
                "intent": row["intent"],
                "phase": row["phase"],
                "user_query": row["user_query"],
                "summary": summary,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        return {"tasks": tasks, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


def get_task(task_id: str) -> Optional[dict[str, Any]]:
    init_db()
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None

        artifact_rows = conn.execute(
            "SELECT payload FROM artifacts WHERE task_id = ? ORDER BY created_at",
            (task_id,),
        ).fetchall()
        artifacts_from_table = [_json_loads(r["payload"]) for r in artifact_rows]

        return {
            "task_id": row["task_id"],
            "symbol": row["symbol"],
            "symbol_name": row["symbol_name"],
            "intent": row["intent"],
            "phase": row["phase"],
            "user_query": row["user_query"],
            "final_report": _json_loads(row["final_report"]),
            "artifacts": _json_loads(row["artifacts"]) or {},
            "artifact_chain": artifacts_from_table,
            "sub_agent_status": _json_loads(row["sub_agent_status"]) or [],
            "human_decision": row["human_decision"],
            "errors": _json_loads(row["errors"]) or [],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()
