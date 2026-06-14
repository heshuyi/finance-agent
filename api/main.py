"""FastAPI entry — AG-UI endpoint for MainAgent."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.main.graph import build_main_graph
from storage.checkpoint import close_checkpointer, init_checkpointer
from storage.db import get_db_path, init_db
from storage.tasks import get_task, list_tasks

load_dotenv()

AGENT_NAME = "finteam_main"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    checkpointer = await init_checkpointer()
    graph = build_main_graph(checkpointer)
    agent = LangGraphAgent(
        name=AGENT_NAME,
        graph=graph,
        description="FinTeam 主 Agent — 金融投研团队编排与终裁",
    )
    add_langgraph_fastapi_endpoint(app, agent, path="/agent")
    app.state.main_graph = graph
    yield
    await close_checkpointer()


app = FastAPI(title="FinTeam Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    from agents.shared.llm import llm_configured, llm_provider_label

    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "milestone": "M3",
        "db": str(get_db_path()),
        "llm": llm_provider_label() if llm_configured() else "未配置",
    }


@app.get("/tasks")
def tasks_index(limit: int = 20, offset: int = 0):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    return list_tasks(limit=limit, offset=offset)


@app.get("/tasks/{task_id}")
def tasks_show(task_id: str):
    record = get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
