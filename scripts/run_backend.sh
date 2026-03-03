#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/kyleparker/Documents/New project 2/data/Personal AI assistant"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/dev/null

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
