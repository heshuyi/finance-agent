"""SQLite 连接与 schema 初始化。"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/finteam.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    symbol TEXT,
    symbol_name TEXT,
    intent TEXT NOT NULL,
    phase TEXT NOT NULL,
    user_query TEXT,
    final_report TEXT,
    artifacts TEXT,
    sub_agent_status TEXT,
    human_decision TEXT,
    errors TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    artifact_type TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_task_id ON artifacts(task_id);

CREATE TABLE IF NOT EXISTS content_cache (
    cache_key TEXT PRIMARY KEY,
    cache_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    payload TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_content_cache_symbol ON content_cache(symbol, cache_type);
CREATE INDEX IF NOT EXISTS idx_content_cache_fetched_at ON content_cache(fetched_at DESC);
"""


def get_db_path() -> Path:
    raw = os.getenv("FINTEAM_DB_PATH", "")
    return Path(raw) if raw else DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    owns = conn is None
    db = conn or get_connection()
    try:
        db.executescript(SCHEMA_SQL)
        db.commit()
    finally:
        if owns:
            db.close()
