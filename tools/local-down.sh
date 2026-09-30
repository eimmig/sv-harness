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
      winpid="$(cat "/proc/$pid/winpid" 2>/dev/null || true)"
      if [[ -n "$winpid" ]] && command -v taskkill >/dev/null 2>&1; then
        taskkill //PID "$winpid" //T //F >/dev/null 2>&1 && echo "parado: $name (pid $pid)"
      else
        kill "$pid" 2>/dev/null && echo "parado: $name (pid $pid)"
      fi
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
else
  echo "nenhum pid file encontrado - servicos locais podem ja estar parados"
fi

# No Windows o pid do bash nem sempre bate com o da JVM (wrapper javapath + java.exe) e o
# pids pode estar vazio: varre as JVMs que rodam jars de services/*/target para nao deixar
# nenhuma segurando o jar (o proximo `clean package` falharia ao apagar jar em uso).
if command -v powershell.exe >/dev/null 2>&1; then
  win_root="$(cygpath -w "$ROOT_DIR" 2>/dev/null || echo "$ROOT_DIR")"
  ROOT_WIN="$win_root" powershell.exe -NoProfile -Command '
    $root = ($env:ROOT_WIN -replace "/", "\").TrimEnd("\") + "\services\"
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" } | ForEach-Object {
      $cmd = $_.CommandLine -replace "/", "\"
      if ($cmd -and $cmd.Contains($root) -and $cmd -match "\\target\\") {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Output "parado: JVM pid $($_.ProcessId)"
      }
    }' | tr -d '\r'
fi

echo "== infra: docker compose down (volumes preservados) =="
(cd "$ROOT_DIR/infra" && docker compose down)
