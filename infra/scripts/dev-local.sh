#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

cd "$ROOT_DIR"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

if [[ ! -d "$ROOT_DIR/node_modules" ]]; then
  npm install --prefix "$ROOT_DIR"
fi

"$ROOT_DIR/infra/scripts/setup-api.sh"

set -a
source "$ROOT_DIR/.env"
set +a

exec npx --prefix "$ROOT_DIR" concurrently \
  -k \
  -n api,web \
  -c blue,green \
  "cd $API_DIR && .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000" \
  "npm run dev --workspace @crypto-intel/web"
