"""A2A Gateway HTTP 服务（可选，供子 Agent 远程调度）。"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from a2a.registry import invoke_agent, list_agent_ids
from a2a.types import TaskRequest, TaskResponse, TaskStatus

app = FastAPI(title="FinTeam A2A Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_auth(request: Request) -> None:
    api_key = os.getenv("A2A_API_KEY")
    if not api_key:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Invalid A2A API Key")


@app.get("/health")
def health():
    return {"status": "ok", "agents": list_agent_ids()}


@app.get("/.well-known/agent-card.json")
def gateway_card():
    return {
        "name": "FinTeamA2AGateway",
        "description": "FinTeam 子 Agent A2A 网关",
        "version": "0.1.0",
        "capabilities": {"streaming": False},
        "skills": [{"id": aid, "name": aid} for aid in list_agent_ids()],
    }


@app.post("/a2a/tasks/send", response_model=TaskResponse)
async def send_task(request: Request, body: TaskRequest):
    _check_auth(request)
    try:
        artifact = invoke_agent(body.agent_id, body.input)
        return TaskResponse(
            task_id=body.task_id,
            agent_id=body.agent_id,
            status=TaskStatus.COMPLETED,
            artifact=artifact,
            progress=100,
            message="完成",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        return TaskResponse(
            task_id=body.task_id,
            agent_id=body.agent_id,
            status=TaskStatus.FAILED,
            error=str(exc),
            message=str(exc),
        )
