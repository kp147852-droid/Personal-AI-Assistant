#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/kyleparker/Documents/New project 2/data/AI assistant"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/dev/null

PORT="${BIND_PORT:-8000}"
exec uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
