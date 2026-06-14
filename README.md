# FinTeam Agent

金融投研多 Agent 系统 — LangGraph + A2A + AG-UI，**个人本地自用**。

> **部署范围**：仅在本机运行（`127.0.0.1`），无线上 / 公网部署需求。数据与 API Key 留在本地；**历史研判**与**历史对话**均存入本地 SQLite（`data/finteam.db`）。

## 架构

| 层级 | 技术 |
|------|------|
| 用户界面 | Next.js + AG-UI / CopilotKit |
| 主 Agent | LangGraph + FastAPI (`ag-ui-langgraph`) |
| 子 Agent | LangGraph 服务，A2A 通信（M1+） |

## 环境要求

- Python 3.12+（pyenv 管理，见 `.python-version`）
- Node.js 20+
- OpenAI 兼容 API Key

## 快速开始

### 1. Python 后端

```bash
pyenv install -s 3.12.3   # 若尚未安装
python -m venv .venv
source .venv/bin/activate
pip install -e . -i https://pypi.org/simple

cp .env.example .env
# 编辑 .env 填入 GEMINI_API_KEY（Google AI Studio）

export PYTHONPATH="$(pwd)"
./scripts/dev-api.sh
# API: http://127.0.0.1:8000/health
# AG-UI: http://127.0.0.1:8000/agent
```

### 2. Next.js 前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:3000
```

## 分支与 PR

详见 [docs/pr/README.md](docs/pr/README.md)。PR-001～PR-010 已全部合并至 `main`。

## 文档

- [PRD](docs/prd/financial-team-agent-prd.md)
- [Schema 附录](docs/prd/references/schemas.md)
- [Agent Card 样例](docs/prd/references/agent-cards.md)
- [PR 需求索引](docs/pr/README.md)

## GitNexus 代码图谱

本仓库已接入 [GitNexus](https://github.com/ozankasikci/gitnexus)（MCP：`user-gitnexus`），索引名 **finance-agent**。

```bash
# 首次 / 大改后重建索引（索引文件在 .gitnexus/，不入库）
npx gitnexus analyze

# 查看索引状态
npx gitnexus status
```

Agent 协作说明见根目录 `AGENTS.md`；Cursor 规则见 `.cursor/rules/gitnexus.mdc`。

## 里程碑

- **M0**：MainAgent 对话 + AG-UI 流式 + 任务状态同步
- **M1**：A2A 子 Agent 流水线 + 买入辩论
- **M2**：验真 + HITL + 卖出辩论 + 终裁报告
- **M3**：SQLite 持久化 + 历史研判回放
- **M3+**：CopilotKit Threads + 投研 Tools + 快问快答 `ai_context`
- **M4**：AKShare 估值分位 + 财报指标 + 同业对比 + 子 Agent LLM 化 + 持仓情境
