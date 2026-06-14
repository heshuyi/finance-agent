#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export A2A_GATEWAY_URL="${A2A_GATEWAY_URL:-http://127.0.0.1:8001}"
exec uvicorn a2a.server:app --host 0.0.0.0 --port "${A2A_PORT:-8001}" --reload
