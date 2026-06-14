"""FastAPI entry — AG-UI endpoint for MainAgent."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.main.graph import main_graph

load_dotenv()

AGENT_NAME = "finteam_main"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="FinTeam Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

langgraph_agent = LangGraphAgent(
    name=AGENT_NAME,
    graph=main_graph,
    description="FinTeam 主 Agent — 金融投研团队编排与终裁",
)

add_langgraph_fastapi_endpoint(app, langgraph_agent, path="/agent")


@app.get("/health")
def health():
    from agents.shared.llm import llm_configured, llm_provider_label

    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "milestone": "M2",
        "llm": llm_provider_label() if llm_configured() else "未配置",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
