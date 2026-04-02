#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

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

is_port_listening() {
  local port="$1"
  ss -ltnH "( sport = :$port )" 2>/dev/null | grep -q .
}

listener_pids() {
  local port="$1"
  ss -ltnp "( sport = :$port )" 2>/dev/null | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u
}

wait_for_port_release() {
  local port="$1"
  local attempts="${2:-20}"

  for ((i = 0; i < attempts; i += 1)); do
    if ! is_port_listening "$port"; then
      return 0
    fi
    sleep 0.25
  done

  return 1
}

stop_compose_service_if_running() {
  local service="$1"

  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi

  if ! docker info >/dev/null 2>&1; then
    return 0
  fi

  if ! docker compose ps --services --filter status=running 2>/dev/null | grep -qx "$service"; then
    return 0
  fi

  echo "[dev] stopping docker compose service '$service' to free local dev ports"
  docker compose stop "$service" >/dev/null
}

stop_stale_processes_on_port() {
  local port="$1"
  local role="$2"
  local pid

  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue

    local cmdline
    cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"

    if [[ "$cmdline" == *"$ROOT_DIR"* ]] || [[ "$cmdline" == *"uvicorn main:app"* ]] || [[ "$cmdline" == *"next-server"* ]] || [[ "$cmdline" == *"next dev"* ]]; then
      echo "[dev] stopping stale $role process on :$port ($pid)"
      kill "$pid" 2>/dev/null || true
    fi
  done < <(listener_pids "$port")

  wait_for_port_release "$port" || true
}

ensure_port_available() {
  local port="$1"
  local role="$2"

  if is_port_listening "$port"; then
    echo "[dev] port $port is still busy; stop the conflicting process and retry"
    echo "[dev] hint: ss -ltnp '( sport = :$port )'"
    exit 1
  fi
}

stop_compose_service_if_running api
stop_compose_service_if_running web
stop_stale_processes_on_port "$API_PORT" api
stop_stale_processes_on_port "$WEB_PORT" web
ensure_port_available "$API_PORT" api
ensure_port_available "$WEB_PORT" web

exec npx --prefix "$ROOT_DIR" concurrently \
  -k \
  -n api,web \
  -c blue,green \
  "cd $API_DIR && .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port $API_PORT" \
  "cd $WEB_DIR && ../../node_modules/.bin/next dev --hostname 0.0.0.0 --port $WEB_PORT"
