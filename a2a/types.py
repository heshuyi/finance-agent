"""A2A Task / Artifact 数据模型。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskRequest(BaseModel):
    task_id: str
    agent_id: str
    skill_id: str
    input: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    agent_id: str
    status: TaskStatus
    artifact: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    progress: int = 0
    message: Optional[str] = None
