# Pull Request 需求索引

本目录存放各 PR 的**中文需求说明**，与 GitHub Pull Request 一一对应。开发时以 PR 文档为验收依据。

| PR | 分支 | GitHub | 里程碑 | 状态 |
|----|------|--------|--------|------|
| [PR-001](PR-001-产品文档.md) | `docs/prd` | [#1](https://github.com/heshuyi/finance-agent/pull/1) | 产品文档 | 已合并 |
| [PR-002](PR-002-M0-后端.md) | `feat/m0-backend` | [#2](https://github.com/heshuyi/finance-agent/pull/2) | M0 后端 | 已合并 |
| [PR-003](PR-003-M0-前端.md) | `feat/m0-frontend` | [#3](https://github.com/heshuyi/finance-agent/pull/3) | M0 前端 | 已合并 |
| [PR-004](PR-004-M1-A2A子Agent.md) | `feat/m1-a2a` | [#4](https://github.com/heshuyi/finance-agent/pull/4) | M1 A2A | 已合并 |
| [PR-005](PR-005-M2-验真与卖出辩论.md) | `feat/m2-auth-sell` | [#5](https://github.com/heshuyi/finance-agent/pull/5) | M2 | 已合并 |
| [PR-006](PR-006-M3-持久化与回放.md) | `feat/m3-persist` | [#6](https://github.com/heshuyi/finance-agent/pull/6) | M3 | 已合并 |
| [PR-007](PR-007-历史对话与联调修复.md) | `feat/pr007-history-chat` | [#7](https://github.com/heshuyi/finance-agent/pull/7) | M3+ | 已合并 |
| [PR-008](PR-008-历史对话SQLite持久化.md) | `feat/pr008-chat-sqlite` | [#8](https://github.com/heshuyi/finance-agent/pull/8) | M3+ | 已合并 |
| GitNexus 接入 | `feat/gitnexus` | [#9](https://github.com/heshuyi/finance-agent/pull/9) | 工具 | 已合并 |
| [PR-010](PR-010-A股免费数据与研判增强.md) | `feat/pr010-a-share-free-data` | [#10](https://github.com/heshuyi/finance-agent/pull/10) | M4 | 已合并 |
| [PR-011](PR-011-智能意图与多轮群聊辩论.md) | `feat/pr011-debate-groupchat` | [#11](https://github.com/heshuyi/finance-agent/pull/11) | M5 | 待合并（验收已通过） |

## 合并顺序

```
PR-001 → … → PR-010 → PR-011
```

## 规范

- 每个 PR 文档包含：背景、需求范围、功能清单、验收标准、非目标
- 代码提交 message 引用 PR 编号，如 `feat(m1): 实现 A2A Task 调度 (#4)`
