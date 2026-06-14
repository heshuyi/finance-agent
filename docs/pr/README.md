# Pull Request 需求索引

本目录存放各 PR 的**中文需求说明**，与 GitHub Pull Request 一一对应。开发时以 PR 文档为验收依据。

| PR | 分支 | 里程碑 | 状态 |
|----|------|--------|------|
| [PR-001](PR-001-产品文档.md) | `docs/prd` | 产品文档 | 待合并 |
| [PR-002](PR-002-M0-后端.md) | `feat/m0-backend` | M0 后端 | 待合并 |
| [PR-003](PR-003-M0-前端.md) | `feat/m0-frontend` | M0 前端 | 待合并 |
| [PR-004](PR-004-M1-A2A子Agent.md) | `feat/m1-a2a` | M1 A2A | 待合并 |
| [PR-005](PR-005-M2-验真与卖出辩论.md) | `feat/m2-auth-sell` | M2 | 待合并 |
| [PR-006](PR-006-M3-持久化与回放.md) | `feat/m3-persist` | M3 | 待合并 |

## 合并顺序

```
PR-001 → PR-002 → PR-003 → PR-004 → PR-005 → PR-006
```

## 规范

- 每个 PR 文档包含：背景、需求范围、功能清单、验收标准、非目标
- 代码提交 message 引用 PR 编号，如 `feat(m1): 实现 A2A Task 调度 (#4)`
