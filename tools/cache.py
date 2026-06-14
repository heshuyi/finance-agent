"""本地内容缓存 — 优先读本地，超过 3 个月自动失效。"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from agents.shared.artifact import now_iso
from storage.db import get_connection, init_db
from tools.types import ToolResult

CACHE_TTL_DAYS = int(os.getenv("CONTENT_CACHE_TTL_DAYS", "90"))


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _is_fresh(fetched_at: str, ttl_days: int = CACHE_TTL_DAYS) -> bool:
    try:
        fetched = _parse_iso(fetched_at)
    except ValueError:
        return False
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - fetched <= timedelta(days=ttl_days)


class LocalCache:
    def __init__(self) -> None:
        init_db()

    def get(self, cache_key: str) -> Optional[dict[str, Any]]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT payload, fetched_at FROM content_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return None
        if not _is_fresh(row["fetched_at"]):
            self.delete(cache_key)
            return None
        payload = json.loads(row["payload"])
        payload["_from_cache"] = True
        payload["_cached_at"] = row["fetched_at"]
        return payload

    def set(self, cache_key: str, *, cache_type: str, symbol: str, payload: dict[str, Any]) -> None:
        fetched_at = now_iso()
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO content_cache (cache_key, cache_type, symbol, payload, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at
                """,
                (cache_key, cache_type, symbol, json.dumps(payload, ensure_ascii=False), fetched_at),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, cache_key: str) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM content_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
        finally:
            conn.close()


_cache: Optional[LocalCache] = None


def get_local_cache() -> LocalCache:
    global _cache
    if _cache is None:
        _cache = LocalCache()
    return _cache


def make_cache_key(cache_type: str, symbol: str, suffix: str = "") -> str:
    base = f"{cache_type}:{symbol.strip()}"
    return f"{base}:{suffix}" if suffix else base


def fetch_with_cache(
    *,
    cache_type: str,
    symbol: str,
    suffix: str = "",
    source: str,
    fetcher: Callable[[], ToolResult],
) -> ToolResult:
    """先读本地缓存（3 个月内），过期则重新拉取并写回。"""
    cache = get_local_cache()
    key = make_cache_key(cache_type, symbol, suffix)
    cached = cache.get(key)
    if cached is not None:
        return ToolResult.success(cached, source=source, fetched_at=cached.get("_cached_at"))

    result = fetcher()
    if result.ok and result.data:
        to_store = {**result.data, "_cached_at": result.fetched_at or now_iso()}
        cache.set(key, cache_type=cache_type, symbol=symbol, payload=to_store)
        return ToolResult.success(
            {**to_store, "_from_cache": False},
            source=source,
            fetched_at=to_store["_cached_at"],
        )
    return result
