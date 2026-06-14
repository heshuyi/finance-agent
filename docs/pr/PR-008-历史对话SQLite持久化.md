# PR-008：历史对话 SQLite 持久化

| 字段 | 内容 |
|------|------|
| 对应分支 | `feat/pr008-chat-sqlite` |
| 类型 | 功能 |
| 里程碑 | M3+ |
| 依赖 | PR-007 |

## 背景

PR-007 使用 `InMemoryAgentRunner` 保存 CopilotKit 会话线程，**重启前端后历史对话丢失**。本地自用场景下，历史对话应与历史研判一样写入 SQLite。

## 需求范围

### 必须交付

1. **Schema** — `chat_threads`、`chat_runs` 表（与 `data/finteam.db` 共用）
2. **SqliteAgentRunner** — 替代 `InMemoryAgentRunner`，兼容 CopilotKit `instanceof` 检查
3. **持久化** — 每轮 run 结束后写入 events + messages；切换线程时从 DB 加载
4. **侧栏** — 历史对话列表重启后仍可见

## 验收标准

- [ ] 完成一次对话后重启 `npm run dev`，历史对话仍出现在侧栏
- [ ] 点击历史线程可恢复消息上下文
- [ ] `GET /api/copilotkit/threads` 正常返回
- [ ] `npm run build` 通过

## 非目标

- 多用户隔离
- 云端同步
