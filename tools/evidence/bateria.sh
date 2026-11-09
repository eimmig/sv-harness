#!/usr/bin/env bash
# Bateria de rodadas do 02-carga.sh, alternando configuracoes para que a ordem e o
# horario nao favorecam nenhuma delas. Antes de cada rodada, aplica a configuracao
# e espera o ambiente voltar ao repouso (uma replica por servico, fila vazia, no
# abaixo de 30% de CPU).
#
# Uso: bateria.sh <raiz-da-saida> <repeticoes> <apostas> <threads> <config>...
#   configs: c1 (uma replica, sem HPA) | c2 (HPA de infra/k8s/hpa.yaml)
#            | <nome> com um arquivo <nome>.sh ao lado, que aplica a configuracao
set -euo pipefail
ROOT="$1"; REPS="$2"; N="$3"; W="$4"; shift 4
CONFIGS=("$@")
HERE="$(cd "$(dirname "$0")" && pwd)"
NS="${NS:-default}"
APPS=(api-gateway auth-service bets-service stats-service)
mkdir -p "$ROOT"
HPA_MANIFEST="${HPA_MANIFEST:-$HERE/../../infra/k8s/hpa.yaml}"

blog() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$ROOT/bateria.log"; }

[ -s "$HPA_MANIFEST" ] || { echo "manifesto do HPA nao encontrado: $HPA_MANIFEST" >&2; exit 1; }
cp "$HPA_MANIFEST" "$ROOT/hpa.yaml"

apply_config() {
  case "$1" in
    c1)
      kubectl -n "$NS" delete hpa "${APPS[@]}" --ignore-not-found
      for d in "${APPS[@]}"; do kubectl -n "$NS" scale deploy/"$d" --replicas=1; done
      ;;
    c2)
      kubectl -n "$NS" apply -f "$HPA_MANIFEST"
      ;;
    *)
      bash "$HERE/$1.sh"
      ;;
  esac
}

wait_idle() {
  # tres checagens seguidas em repouso, porque o metrics-server atrasa de 15 a 60 s
  local calm=0
  for _ in $(seq 1 120); do
    local ok=1
    for d in "${APPS[@]}"; do
      local r
      r="$(kubectl -n "$NS" get deploy "$d" -o jsonpath='{.status.readyReplicas}/{.status.replicas}')"
      [ "$r" = "1/1" ] || ok=0
    done
    local q cpu
    q="$(kubectl -n "$NS" exec deploy/rabbitmq -- rabbitmqctl list_queues -q name messages \
      | awk '$1 == "stats.bet-events" { print $2 }')"
    [ "${q:-1}" = "0" ] || ok=0
    cpu="$(kubectl top node --no-headers 2>/dev/null | awk '{ sub("%", "", $3); print $3 }')"
    [ -n "$cpu" ] && [ "$cpu" -lt 30 ] || ok=0
    if [ "$ok" = 1 ]; then calm=$((calm + 1)); else calm=0; fi
    [ "$calm" -ge 3 ] && return 0
    sleep 15
  done
  blog "ambiente nao voltou ao repouso em 30 min"
  return 1
}

for rep in $(seq 1 "$REPS"); do
  for cfg in "${CONFIGS[@]}"; do
    out="$ROOT/$cfg-r$rep"
    if [ -f "$out/02-resumo.txt" ]; then
      blog "pulando $cfg-r$rep (ja concluida)"
      continue
    fi
    blog "aplicando $cfg para a rodada $rep"
    apply_config "$cfg" >>"$ROOT/bateria.log" 2>&1
    wait_idle
    kubectl -n "$NS" get hpa >"$ROOT/$cfg-r$rep.hpa-antes.txt" 2>&1 || true
    blog "iniciando $cfg-r$rep"
    if OUT="$out" bash "$HERE/02-carga.sh" "$N" "$W" >"$ROOT/$cfg-r$rep.console.txt" 2>&1; then
      blog "concluida $cfg-r$rep: $(grep -m1 'tempo total' "$out/02-carga.txt" || true)"
    else
      blog "FALHOU $cfg-r$rep (ver $cfg-r$rep.console.txt)"
    fi
  done
done
blog "bateria encerrada"
