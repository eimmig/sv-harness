#!/usr/bin/env bash
# Derruba o ambiente subido por tools/local-up.sh: mata os processos locais
# (Java, uv, ng serve) e desce a infra (docker compose down, sem -v - dados ficam).
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/tools/.local-run/pids"

if [[ -f "$PID_FILE" ]]; then
  while IFS=: read -r name pid; do
    [[ -z "${pid:-}" ]] && continue
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && echo "parado: $name (pid $pid)"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
else
  echo "nenhum pid file encontrado - servicos locais podem ja estar parados"
fi

echo "== infra: docker compose down (volumes preservados) =="
(cd "$ROOT_DIR/infra" && docker compose down)
