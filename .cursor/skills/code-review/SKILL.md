---
name: code-review
description: >-
  Review FinTeam Agent code changes for correctness, security, scope, and
  merge readiness. Use when the user asks for code review, pre-commit review,
  PR review, or before committing changes on feat/* branches.
---

# FinTeam Code Review

## When to Use

- User asks for code review before commit/PR
- Large multi-file change on `feat/*` branches
- Reviewing tools layer, CopilotKit, or LangGraph changes

## Workflow

```
1. git status + git diff [base]...HEAD     → scope of change
2. Map changes to PR doc (docs/pr/)       → acceptance alignment
3. Read critical paths (see checklist)    → logic & integration
4. Run verification commands            → build / smoke tests
5. Classify findings                    → block / fix / note
6. Fix blockers, re-verify              → only then commit
```

## Critical Paths (always read if touched)

| Area | Files |
|------|-------|
| Agent routing | `agents/main/nodes.py`, `agents/main/graph.py`, `agents/shared/intent.py` |
| Data tools | `tools/**/*.py`, `agents/data_collector/runner.py` |
| API | `api/main.py`, `api/tools_routes.py` |
| CopilotKit | `frontend/src/lib/copilot-runtime.ts`, `frontend/src/app/api/copilotkit/**` |
| Persistence | `storage/db.py`, `storage/tasks.py`, `tools/cache.py` |
| Frontend tools | `frontend/src/lib/tools-api.ts`, `FinTeamFrontendTools.tsx` |

## Review Checklist

### Correctness
- [ ] Intent routing: `buy_analysis`/`sell_analysis`/`verify_only` still use pipeline
- [ ] `data_query` / `general` with symbol → `chat_response` + `ai_context`
- [ ] `copilotRuntime` passed correctly (not `.instance`)
- [ ] `GET /api/copilotkit/threads` reachable (multi-route handler)
- [ ] Tool failures degrade gracefully (no crash, user gets message)
- [ ] Cache TTL respected; stale data not served past `CONTENT_CACHE_TTL_DAYS`

### Security
- [ ] No secrets in code or committed `.env`
- [ ] API keys only via env vars documented in `.env.example`
- [ ] User input (symbol) validated before external fetch
- [ ] No SSRF from crawler URL construction

### Scope & Quality
- [ ] Changes match stated PR scope; no unrelated refactors
- [ ] Matches existing naming, types, and module layout
- [ ] No dead imports or duplicate logic (prefer `context_loader` reuse)
- [ ] Frontend `npm run build` passes
- [ ] Python imports resolve (`PYTHONPATH=.` smoke test)

### Data Design
- [ ] Raw tool JSON not shown to end users; `ai_context` for LLM
- [ ] `claims[]` still populated for pipeline artifacts
- [ ] Disclaimer present in user-facing LLM output

## Severity Labels

| Label | Action |
|-------|--------|
| **BLOCKER** | Must fix before commit |
| **SHOULD FIX** | Fix now if small; else note in commit message |
| **NOTE** | Document only; OK to merge |

## Verification Commands

```bash
# Frontend
cd frontend && npm run build

# Backend routing smoke
cd .. && PYTHONPATH=. python -c "
from agents.main.nodes import prepare_task, should_run_pipeline
from langchain_core.messages import HumanMessage
cases = [
  ('查一下 600519 最新行情', 'chat_response'),
  ('分析茅台能不能买', 'dispatch_pipeline'),
]
for text, expect in cases:
    s = {'messages': [HumanMessage(content=text)]}
    p = prepare_task(s)
    r = should_run_pipeline({**s, **p})
    assert r == expect, f'{text}: {r} != {expect}'
print('routing ok')
"

# Threads endpoint (frontend dev server running)
curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3000/api/copilotkit/threads?agentId=finteam_main'
```

## Review Output Template

```markdown
## Code Review: <branch or PR>

**Verdict: APPROVE / FIX THEN COMMIT / REQUEST CHANGES**

### Summary
- N files, main areas: ...

### Findings
1. **[BLOCKER|SHOULD FIX|NOTE]** ...

### Verification
- [x] or [ ] build / routing / API checks

### Commit Recommendation
<one-line why + suggested message>
```

## Commit Rules

- Only commit after **APPROVE** or all **BLOCKER**s fixed
- Message references PR when applicable: `feat(pr007): ...`
- Never commit `.env`, credentials, or `data/*.db`
- Use HEREDOC for commit message
