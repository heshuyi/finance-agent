#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
exec python -m api.main
