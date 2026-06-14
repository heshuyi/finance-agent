"""Tool 层通用类型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolError:
    code: str
    message: str
    source: str = ""


@dataclass
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[ToolError] = field(default_factory=list)
    source: str = ""
    fetched_at: Optional[str] = None

    @classmethod
    def success(
        cls,
        data: dict[str, Any],
        *,
        source: str,
        fetched_at: Optional[str] = None,
    ) -> "ToolResult":
        return cls(ok=True, data=data, source=source, fetched_at=fetched_at)

    @classmethod
    def failure(cls, code: str, message: str, *, source: str = "") -> "ToolResult":
        return cls(ok=False, errors=[ToolError(code=code, message=message, source=source)])
