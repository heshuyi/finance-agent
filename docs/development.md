# 开发流程：分支与 PR

本项目采用 **分支 + Pull Request** 管理开发，每个功能/文档独立分支，合并前可 review。

## 分支规范

| 分支前缀 | 用途 | 示例 |
|----------|------|------|
| `docs/` | 文档、PRD | `docs/prd` |
| `feat/` | 新功能 | `feat/m0-backend`, `feat/m1-a2a` |
| `fix/` | Bug 修复 | `fix/a2a-timeout` |
| `chore/` | 工具链、配置 | `chore/ci` |

## 当前分支

```
main                 ← 稳定基线
├── docs/prd         ← PR #1 产品文档
├── feat/m0-backend  ← PR #2 Python 后端
└── feat/m0-frontend ← PR #3 Next.js 前端
```

查看分支图：

```bash
git log --oneline --all --graph
```

## 本地开发

### 仅后端（feat/m0-backend）

```bash
git checkout feat/m0-backend
source .venv/bin/activate
pip install -e . -i https://pypi.org/simple
cp .env.example .env   # 填入 OPENAI_API_KEY
export PYTHONPATH="$(pwd)"
./scripts/dev-api.sh
```

### 仅前端（feat/m0-frontend）

```bash
git checkout feat/m0-frontend
cd frontend && npm install && npm run dev
```

### 全栈联调

合并 backend + frontend 到本地工作分支：

```bash
git checkout -b dev/local main
git merge feat/m0-backend
git merge feat/m0-frontend
# 可选：git merge docs/prd
```

然后同时启动 API 与前端。

## 创建 Pull Request

### 1. 登录 GitHub CLI（首次）

```bash
gh auth login
```

### 2. 创建远程仓库并推送

```bash
# 在 GitHub 创建空仓库 fundAgents 后：
git remote add origin git@github.com:<你的用户名>/fundAgents.git
git push -u origin main
git push -u origin docs/prd feat/m0-backend feat/m0-frontend
```

### 3. 为每个分支开 PR

```bash
# PR #1 文档
gh pr create --base main --head docs/prd \
  --title "docs: FinTeam Agent PRD" \
  --body "## Summary
- 完整 PRD（LangGraph + A2A + AG-UI）
- Schema / Agent Card / 终裁样例附录

## Test plan
- [ ] 评审架构与里程碑
- [ ] 确认 MVP 范围"

# PR #2 后端
gh pr create --base main --head feat/m0-backend \
  --title "feat(m0): MainAgent LangGraph backend" \
  --body "## Summary
- MainAgent LangGraph（意图解析 + 任务状态）
- FastAPI + ag-ui-langgraph AG-UI endpoint

## Test plan
- [ ] \`curl http://127.0.0.1:8000/health\` 返回 ok
- [ ] 配置 OPENAI_API_KEY 后 POST /agent 流式响应"

# PR #3 前端
gh pr create --base main --head feat/m0-frontend \
  --title "feat(m0): Next.js AG-UI frontend" \
  --body "## Summary
- CopilotKit + HttpAgent 连接 MainAgent
- 对话页 + 子 Agent 状态面板

## Test plan
- [ ] 启动 API 后访问 localhost:3000 可对话
- [ ] 进度条与 phase 随 MainAgent state 更新"
```

### 4. 合并顺序建议

1. `docs/prd` → `main`
2. `feat/m0-backend` → `main`
3. `feat/m0-frontend` → `main`（依赖 backend 已合并或本地 API 运行）

## 下一步分支（M1）

```bash
git checkout main && git pull
git checkout -b feat/m1-a2a
```

M1 内容：A2A Gateway、DataCollector / Verification 子 Agent、流水线进度。
