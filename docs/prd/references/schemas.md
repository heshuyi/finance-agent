# FinTeam Agent — JSON Schema 附录

本文档定义 Artifact、AG-UI State、MainAgent State 的 JSON Schema，实现时可直接转为 Pydantic / Zod 模型。

---

## 1. Artifact Schema（统一子 Agent 输出）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FinTeamAgentArtifact",
  "type": "object",
  "required": [
    "artifact_id", "task_id", "agent_id", "artifact_type",
    "confidence", "created_at", "claims", "disclaimer"
  ],
  "properties": {
    "artifact_id": { "type": "string", "format": "uuid" },
    "task_id": { "type": "string", "format": "uuid" },
    "agent_id": {
      "type": "string",
      "enum": [
        "main", "data_collector", "verification", "authenticity",
        "pro_buy", "anti_buy", "pro_sell", "anti_sell"
      ]
    },
    "artifact_type": {
      "type": "string",
      "enum": [
        "DataBundle", "VerifiedData", "AuthenticityReport",
        "BullCase", "BearCase_NoBuy", "SellCase", "HoldCase", "FinalJudgment"
      ]
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "created_at": { "type": "string", "format": "date-time" },
    "claims": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["statement", "verified", "source_type", "evidence"],
        "properties": {
          "statement": { "type": "string" },
          "verified": { "type": "boolean" },
          "source_type": {
            "type": "string",
            "enum": ["market_data", "filing", "news", "financial_report", "macro", "model_inference"]
          },
          "evidence": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["source_name", "quoted_at"],
              "properties": {
                "url": { "type": "string" },
                "source_name": { "type": "string" },
                "quoted_at": { "type": "string", "format": "date-time" },
                "excerpt": { "type": "string" }
              }
            }
          }
        }
      }
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "message": { "type": "string" },
          "recoverable": { "type": "boolean" }
        }
      }
    },
    "metadata": { "type": "object" },
    "disclaimer": {
      "type": "string",
      "const": "本输出由 AI 生成，不构成投资建议。请自行判断并承担投资风险。"
    }
  }
}
```

---

## 2. AG-UI State Schema（前端同步）

```json
{
  "title": "FinTeamAgentAGUIState",
  "type": "object",
  "required": ["task_id", "phase", "progress", "sub_agent_status"],
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "symbol": { "type": "string" },
    "symbol_name": { "type": "string" },
    "intent": {
      "type": "string",
      "enum": ["buy_analysis", "sell_analysis", "verify_only", "data_query"]
    },
    "phase": {
      "type": "string",
      "enum": ["planning", "data", "verify", "auth", "debate", "judgment", "done", "cancelled"]
    },
    "progress": { "type": "number", "minimum": 0, "maximum": 100 },
    "sub_agent_status": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["agent_id", "status", "updated_at"],
        "properties": {
          "agent_id": { "type": "string" },
          "status": {
            "type": "string",
            "enum": ["pending", "working", "completed", "failed", "timeout"]
          },
          "message": { "type": "string" },
          "updated_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "artifacts_preview": { "type": "object" },
    "awaiting_human": {
      "type": "object",
      "properties": {
        "reason": { "type": "string" },
        "options": { "type": "array", "items": { "type": "string" } }
      }
    },
    "final_report": { "type": ["object", "null"] }
  }
}
```

---

## 3. MainAgent LangGraph State

```python
# agents/shared/state.py — TypedDict 参考实现
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class SubAgentStatus(TypedDict):
    agent_id: str
    status: str  # pending | working | completed | failed | timeout
    message: Optional[str]
    updated_at: str

class MainAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task_id: str
    symbol: str
    symbol_name: Optional[str]
    intent: str
    phase: str
    progress: int
    planned_agents: list[str]
    artifacts: dict[str, dict]       # agent_id -> Artifact
    sub_agent_status: list[SubAgentStatus]
    human_decision: Optional[str]   # continue | abort
    final_report: Optional[dict]
    errors: list[dict]
```
