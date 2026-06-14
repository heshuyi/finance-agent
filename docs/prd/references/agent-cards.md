# FinTeam Agent — A2A Agent Card 样例

每个子 Agent 在 `/.well-known/agent-card.json` 暴露以下结构。完整 8 个 Agent 遵循同一模板，此处列出 3 个代表样例。

---

## DataCollectorAgent

```json
{
  "name": "DataCollectorAgent",
  "description": "拉取行情、财报、公告、宏观数据，输出带溯源的 DataBundle",
  "version": "0.1.0",
  "supportedInterfaces": [
    {
      "url": "http://localhost:8001/a2a",
      "protocolBinding": "HTTP+JSON"
    }
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "fetch-market-data",
      "name": "市场数据采集",
      "description": "按标的与时间窗拉取行情与估值指标",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    },
    {
      "id": "fetch-filings",
      "name": "公告采集",
      "description": "拉取交易所公告与新闻",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "authentication": {
    "schemes": ["Bearer"]
  }
}
```

---

## DataVerificationAgent

```json
{
  "name": "DataVerificationAgent",
  "description": "交叉核对多源数据，检查单位与口径一致性",
  "version": "0.1.0",
  "supportedInterfaces": [
    {
      "url": "http://localhost:8002/a2a",
      "protocolBinding": "HTTP+JSON"
    }
  ],
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "cross-verify-data",
      "name": "数据交叉核查",
      "description": "输入 DataBundle，输出 VerifiedData 与 discrepancies",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "authentication": {
    "schemes": ["Bearer"]
  }
}
```

---

## ProBuyAgent

```json
{
  "name": "ProBuyAgent",
  "description": "基于已验真数据，论证支持买入的多空论据",
  "version": "0.1.0",
  "supportedInterfaces": [
    {
      "url": "http://localhost:8005/a2a",
      "protocolBinding": "HTTP+JSON"
    }
  ],
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "bull-case",
      "name": "买入论证",
      "description": "输出 BullCase Artifact，含论点、证据、风险",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "authentication": {
    "schemes": ["Bearer"]
  }
}
```

---

## 端口规划（建议）

| Agent | 端口 |
|-------|------|
| MainAgent (AG-UI API) | 8000 |
| DataCollector | 8001 |
| Verification | 8002 |
| Authenticity | 8003 |
| ProBuy | 8005 |
| AntiBuy | 8006 |
| ProSell | 8007 |
| AntiSell | 8008 |
