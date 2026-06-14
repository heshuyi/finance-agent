"""资讯条目归一化与合并。"""

from __future__ import annotations

from typing import Any


def normalize_item(
    *,
    headline: str,
    url: str = "",
    summary: str = "",
    source: str = "",
    published_at: str | int | None = None,
    channel: str = "",
) -> dict[str, Any]:
    return {
        "headline": headline.strip(),
        "summary": (summary or "").strip(),
        "source": source.strip(),
        "url": url.strip(),
        "published_at": published_at,
        "channel": channel,
    }


def merge_news_items(
    *groups: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for group in groups:
        for item in group:
            headline = item.get("headline", "").strip()
            if not headline:
                continue
            key = headline.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged
