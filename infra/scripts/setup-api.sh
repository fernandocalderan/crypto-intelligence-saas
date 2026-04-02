#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

if [[ ! -d "$API_DIR/.venv" ]]; then
  python3 -m venv "$API_DIR/.venv"
fi

"$API_DIR/.venv/bin/pip" install --upgrade pip >/dev/null
"$API_DIR/.venv/bin/pip" install -r "$API_DIR/requirements.txt" >/dev/null

