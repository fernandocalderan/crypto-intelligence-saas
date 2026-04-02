#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${DATABASE_URL:-}" ]]; then
  max_attempts="${API_INIT_DB_MAX_ATTEMPTS:-10}"
  attempt=1

  until python -m db.init_db; do
    if (( attempt >= max_attempts )); then
      echo "[api-entrypoint] init_db failed after ${attempt} attempts"
      exit 1
    fi

    echo "[api-entrypoint] init_db failed on attempt ${attempt}/${max_attempts}; retrying in 2s"
    attempt=$((attempt + 1))
    sleep 2
  done
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
