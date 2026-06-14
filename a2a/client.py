"""A2A Client — MainAgent 调度子 Agent。"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

import httpx

from a2a.registry import invoke_agent
from a2a.types import TaskRequest, TaskResponse, TaskStatus

DEFAULT_TIMEOUT = float(os.getenv("A2A_TIMEOUT_SEC", "120"))
GATEWAY_URL = os.getenv("A2A_GATEWAY_URL", "").rstrip("/")


async def send_task_async(
    agent_id: str,
    skill_id: str,
    task_id: str,
    input_data: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> TaskResponse:
    request = TaskRequest(
        task_id=task_id,
        agent_id=agent_id,
        skill_id=skill_id,
        input=input_data,
    )

    if GATEWAY_URL:
        return await _send_http(request, timeout=timeout)

    return await asyncio.to_thread(_send_local, request)


def send_task(
    agent_id: str,
    skill_id: str,
    task_id: str,
    input_data: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> TaskResponse:
    return asyncio.run(send_task_async(agent_id, skill_id, task_id, input_data, timeout=timeout))


def _send_local(request: TaskRequest) -> TaskResponse:
    try:
        artifact = invoke_agent(request.agent_id, request.input)
        return TaskResponse(
            task_id=request.task_id,
            agent_id=request.agent_id,
            status=TaskStatus.COMPLETED,
            artifact=artifact,
            progress=100,
            message="完成",
        )
    except Exception as exc:  # noqa: BLE001
        return TaskResponse(
            task_id=request.task_id,
            agent_id=request.agent_id,
            status=TaskStatus.FAILED,
            error=str(exc),
            message=str(exc),
        )


async def _send_http(request: TaskRequest, *, timeout: float) -> TaskResponse:
    headers: dict[str, str] = {}
    api_key = os.getenv("A2A_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=timeout, proxy=os.getenv("https_proxy")) as client:
        resp = await client.post(
            f"{GATEWAY_URL}/a2a/tasks/send",
            json=request.model_dump(),
            headers=headers,
        )
        resp.raise_for_status()
        return TaskResponse.model_validate(resp.json())
