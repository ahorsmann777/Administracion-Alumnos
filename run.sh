#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install -q -r backend/requirements.txt

exec ./.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000