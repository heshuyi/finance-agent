# PR-004：M1 A2A 子 Agent 流水线（取数 + 核查 + 买入辩论）

| 字段 | 内容 |
|------|------|
| 对应分支 | `feat/m1-a2a` |
| 类型 | 功能 |
| 里程碑 | M1 |
| 依赖 | PR-002、PR-003 已合并 |

## 背景

M0 主 Agent 仅模拟调度计划。M1 需实现自研 A2A 协议，MainAgent 通过 A2A Client 调度子 Agent，完成「取数 → 核查 → 买入/不买入辩论」闭环，并在 AG-UI 进度条中反映真实阶段。

## 需求范围

### 必须交付

1. **A2A 基础设施** `a2a/`
   - `types.py` — Task、Artifact、AgentCard 数据模型
   - `server.py` — JSON-RPC + SSE Task 生命周期（子 Agent 挂载点）
   - `client.py` — MainAgent 调用子 Agent 的 A2A Client
   - `agent_cards/` — 各子 Agent 注册 JSON

2. **子 Agent LangGraph 服务**
   - `agents/data_collector/` — 拉取标的 mock/占位数据，输出 `DataBundle` Artifact
   - `agents/verification/` — 交叉核查，输出 `VerifiedData`
   - `agents/pro_buy/` — 支持买入论证 `BullCase`
   - `agents/anti_buy/` — 不建议买入 `BearCase_NoBuy`

3. **MainAgent 升级**
   - 节点 `dispatch_pipeline` — 串行 A2A：data → verify
   - 节点 `dispatch_debate` — 并行 A2A：pro_buy + anti_buy
   - 节点 `synthesize_judgment` — 汇总 Artifact 终裁草稿
   - 更新 phase：data → verify → debate → judgment → done

4. **共享 Schema** `agents/shared/artifact.py` — 统一 Artifact 结构

5. **启动脚本**
   - `scripts/dev-subagents.sh` — 本地启动子 Agent 服务

### 非目标（M1 不做）

- AuthenticityAgent（M2）
- ProSell / AntiSell（M2）
- 真实行情 API（可用 mock，接口预留 `tools/`）

## 验收标准

- [ ] MainAgent 发起买入分析时，依次调度 data_collector → verification → pro_buy/anti_buy
- [ ] 各子 Agent 返回符合 Artifact Schema 的 JSON，含 `claims[]` 与 `disclaimer`
- [ ] AG-UI 状态面板 sub_agent 从 pending → working → completed 实时更新
- [ ] 单个子 Agent 超时（120s）不阻塞其他 Agent，终裁标注缺失视角
- [ ] `curl` 子 Agent `/.well-known/agent-card.json` 返回 Agent Card

## 技术约束

- A2A 遵循开放规范（Task + Artifact + SSE）
- 子 Agent 均为独立 LangGraph + FastAPI 或同进程注册
