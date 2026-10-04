#!/usr/bin/env bash
set -euo pipefail

NS="${NS:-default}"
OUT="${OUT:-$PWD/evidence/$(date +%Y%m%d-%H%M%S)}"
BASE_URL="${BASE_URL:-http://localhost}"
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$OUT"
BG_PIDS=()

log() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$OUT/log.txt"; }

k() { kubectl -n "$NS" "$@"; }

secret() { k get secret stakevault-secrets -o "jsonpath={.data.$1}" | base64 -d; }

psql_bets() { k exec deploy/postgres-bets -- psql -U bets_user -d bets -tAc "$1"; }

psql_stats() { k exec deploy/postgres-stats -- psql -U stats_user -d stats -tAc "$1"; }

queue_depth() {
  k exec deploy/rabbitmq -- rabbitmqctl list_queues -q name messages_ready messages_unacknowledged \
    | awk -v q="$1" '$1 == q { print $2 + $3 }'
}

snapshot() {
  local name="$1"
  {
    echo "## $(date -Is)"
    k get pods -o wide
    echo
    k get hpa
    echo
    k top pods 2>&1
    echo
    k exec deploy/rabbitmq -- rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
  } >"$OUT/$name.txt" 2>&1 || true
}

sample_loop() {
  local file="$1"
  shift
  (
    while true; do
      { echo "## $(date -Is)"; "$@"; } >>"$file" 2>&1 || true
      sleep 10
    done
  ) &
  BG_PIDS+=("$!")
}

port_forward() {
  k port-forward "$1" "$2" >/dev/null 2>&1 &
  local pid=$!
  BG_PIDS+=("$pid")
  sleep 3
  kill -0 "$pid" 2>/dev/null || { echo "port-forward $1 $2 falhou: porta local em uso por um kubectl antigo? (ss -ltnp | grep ${2%%:*})" >&2; exit 1; }
}

cleanup() {
  for pid in "${BG_PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT

require() {
  for tool in "$@"; do
    command -v "$tool" >/dev/null 2>&1 || { echo "falta o comando: $tool" >&2; exit 1; }
  done
}

rabbit_api() {
  curl -s -u "$(secret RABBITMQ_USER):$(secret RABBITMQ_PASSWORD)" -H 'content-type: application/json' "$@"
}

redis() {
  k exec deploy/redis -- sh -c 'exec redis-cli --no-auth-warning -a "$REDIS_PASSWORD" "$@"' sh "$@"
}
