"""估值分位计算。"""

from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def compute_percentile(series: list[float], current: float | None) -> float | None:
    """当前值在样本序列中的百分位（0–100）。"""
    current_f = _to_float(current)
    if current_f is None:
        return None
    valid = [x for x in series if _to_float(x) is not None]
    if len(valid) < 5:
        return None
    below = sum(1 for x in valid if x <= current_f)
    return round(below / len(valid) * 100, 1)


def sample_series(rows: list[dict[str, Any]], key: str, *, max_points: int = 12) -> list[dict[str, Any]]:
    """对历史序列均匀采样，便于展示。"""
    if not rows:
        return []
    if len(rows) <= max_points:
        return rows
    step = max(1, len(rows) // max_points)
    sampled = rows[::step]
    if sampled[-1] != rows[-1]:
        sampled.append(rows[-1])
    return sampled[:max_points]
