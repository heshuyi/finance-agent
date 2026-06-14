#!/usr/bin/env bash
# 推送所有分支并在 GitHub 创建 PR（需先 gh auth login 成功）
set -euo pipefail

cd "$(dirname "$0")/.."
source scripts/proxy-env.sh

echo "==> 检查 gh 登录状态..."
gh auth status

GITHUB_USER="$(gh api user -q .login)"
REPO_NAME="${1:-finance-agent}"
REMOTE="origin"

echo "==> GitHub 用户: $GITHUB_USER"
echo "==> 仓库名: $GITHUB_USER/$REPO_NAME"

if ! git remote get-url "$REMOTE" &>/dev/null; then
  echo "==> 创建远程仓库并添加 origin..."
  gh repo create "$REPO_NAME" --private --source=. --remote="$REMOTE" --push=false \
    || gh repo create "$GITHUB_USER/$REPO_NAME" --private --source=. --remote="$REMOTE" --push=false
else
  echo "==> 已存在 remote: $(git remote get-url "$REMOTE")"
fi

git config http.proxy http://127.0.0.1:12334
git config https.proxy http://127.0.0.1:12334

BRANCHES=(main docs/prd feat/m0-backend feat/m0-frontend)

echo "==> 推送分支..."
for b in "${BRANCHES[@]}"; do
  git push -u "$REMOTE" "$b" 2>/dev/null || git push "$REMOTE" "$b"
done

echo "==> 创建 Pull Requests..."

if ! gh pr view 1 &>/dev/null; then
  gh pr create --base main --head docs/prd \
    --title "docs: FinTeam Agent PRD" \
    --body "$(cat <<'EOF'
## Summary
- 完整 PRD（LangGraph + A2A + AG-UI 架构）
- Schema / Agent Card / 终裁报告样例附录
- PRD 空白模板供后续复用

## Test plan
- [ ] 评审架构与 Agent 分工
- [ ] 确认 M0–M3 里程碑范围
EOF
)"
fi

if ! gh pr list --head feat/m0-backend --json number -q '.[0].number' 2>/dev/null | grep -q .; then
  gh pr create --base main --head feat/m0-backend \
    --title "feat(m0): MainAgent LangGraph backend with AG-UI endpoint" \
    --body "$(cat <<'EOF'
## Summary
- MainAgent LangGraph：意图解析、任务状态初始化
- FastAPI + ag-ui-langgraph 暴露 `/agent` 流式端点
- 开发脚本 `scripts/dev-api.sh`

## Test plan
- [ ] `curl http://127.0.0.1:8000/health` 返回 ok
- [ ] 配置 `.env` 中 `OPENAI_API_KEY` 后 AG-UI 端点可流式响应
EOF
)"
fi

if ! gh pr list --head feat/m0-frontend --json number -q '.[0].number' 2>/dev/null | grep -q .; then
  gh pr create --base main --head feat/m0-frontend \
    --title "feat(m0): Next.js AG-UI frontend with CopilotKit chat" \
    --body "$(cat <<'EOF'
## Summary
- CopilotKit + HttpAgent 连接 MainAgent
- 对话页 + 子 Agent 状态面板（AG-UI State 同步）
- 开发脚本 `scripts/dev-frontend.sh`

## Test plan
- [ ] 启动 API 后访问 http://localhost:3000 可对话
- [ ] 发起买入分析请求，进度与 phase 随 state 更新
EOF
)"
fi

echo ""
echo "==> 完成！PR 列表："
gh pr list
echo ""
echo "仓库地址: https://github.com/$GITHUB_USER/$REPO_NAME"
