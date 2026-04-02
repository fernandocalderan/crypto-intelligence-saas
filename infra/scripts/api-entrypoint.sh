#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${DATABASE_URL:-}" ]]; then
  python -m db.init_db
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
