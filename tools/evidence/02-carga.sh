#!/usr/bin/env bash
source "$(dirname "$0")/lib.sh"
PY="${PYTHON:-python3}"
require kubectl curl "$PY"
"$PY" -c "import requests" 2>/dev/null || { echo "instale: sudo apt install python3-requests" >&2; exit 1; }

N_BETS="${1:-50000}"
WORKERS="${2:-64}"
GATEWAY="${GATEWAY:-$BASE_URL}"
# PING_HOST: com o gerador fora do servidor, mede o RTT ate ele durante a carga.
PING_HOST="${PING_HOST:-}"

# Deslocamento do relogio do servidor em relacao ao de quem roda o script, para
# comparar os instantes do gerador com os do banco (atraso_consistencia.py).
clock_offset() {
  local before server after
  before="$(date +%s.%N)"
  server="$(psql_stats "select extract(epoch from clock_timestamp())")"
  after="$(date +%s.%N)"
  awk -v b="$before" -v s="$server" -v a="$after" \
    'BEGIN { printf "offset_s=%.3f rtt_s=%.3f\n", s - (a + b) / 2, a - b }'
}

log "saida em $OUT, $N_BETS apostas, $WORKERS threads, gerador em $(hostname), gateway $GATEWAY"
{ echo "## antes"; clock_offset; } >>"$OUT/02-relogio.txt"
snapshot 02-antes
kubectl get nodes -o wide >"$OUT/02-no.txt" 2>&1 || true

port_forward svc/auth-service 18081:8081
sample_loop "$OUT/02-hpa.txt" kubectl -n "$NS" get hpa
sample_loop "$OUT/02-pods.txt" kubectl -n "$NS" get pods
sample_loop "$OUT/02-top.txt" kubectl -n "$NS" top pods
sample_loop "$OUT/02-filas.txt" kubectl -n "$NS" exec deploy/rabbitmq -- rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
sample_loop "$OUT/02-top-no.txt" kubectl top node
if [ -n "$PING_HOST" ]; then
  if ping -c 1 127.0.0.1 >/dev/null 2>&1; then
    sample_loop "$OUT/02-ping.txt" ping -c 3 "$PING_HOST"
  else
    sample_loop "$OUT/02-ping.txt" ping -n 3 "$PING_HOST"
  fi
fi

ADMIN_API_KEY="$(secret ADMIN_API_KEY)" "$PY" "$TOOLS_DIR/load_test_bets.py" \
  --n-bets "$N_BETS" --workers "$WORKERS" \
  --auth-base-url http://localhost:18081 --gateway-base-url "$GATEWAY" \
  --latency-csv "$OUT/02-latencias.csv" \
  2>&1 | tee "$OUT/02-carga.txt"

SLUG="$(grep -m1 "Criando tenant" "$OUT/02-carga.txt" | sed -E "s/.*tenant '([^']+)'.*/\1/")"
[ -n "$SLUG" ] || { log "nao achei o slug do tenant no log da carga"; exit 1; }
log "tenant da carga: $SLUG"

log "esperando o outbox e a fila drenarem (ate 30 min)"
calm=0
for _ in $(seq 1 180); do
  outbox="$(psql_bets "select count(*) from public.outbox_event")"
  fila="$(queue_depth stats.bet-events)"
  log "outbox=$outbox fila=${fila:-?}"
  if [ "$outbox" = "0" ] && [ "${fila:-1}" = "0" ]; then calm=$((calm + 1)); else calm=0; fi
  [ "$calm" -ge 3 ] && break
  sleep 10
done

bets="$(psql_bets "select count(*) from \"tenant_${SLUG}\".bet")"
settled="$(psql_bets "select count(*) from \"tenant_${SLUG}\".bet where status <> 'pending'")"
fact="$(psql_stats "select count(*) from \"tenant_${SLUG}\".fact_bet")"
processed="$(psql_stats "select count(*) from \"tenant_${SLUG}\".processed_event")"
outbox="$(psql_bets "select count(*) from public.outbox_event")"
dlq="$(queue_depth stats.bet-events.dlq)"
expected=$((bets + settled))

verdict() { [ "$1" = "$2" ] && echo PASS || echo FAIL; }

{
  echo "tenant                              : $SLUG"
  echo "apostas em bets-service             : $bets"
  echo "  das quais liquidadas              : $settled"
  echo "eventos esperados (criadas+liquid.) : $expected"
  echo "eventos processados no stats        : $processed   $(verdict "$processed" "$expected")"
  echo "linhas em fact_bet                  : $fact   $(verdict "$fact" "$bets")"
  echo "pendentes no outbox                 : $outbox   $(verdict "$outbox" 0)"
  echo "mensagens na DLQ                    : ${dlq:-?}   $(verdict "${dlq:-x}" 0)"
} | tee "$OUT/02-reconciliacao.txt"

snapshot 02-depois
k describe hpa >"$OUT/02-hpa-eventos.txt" 2>&1 || true
k get events --sort-by=.lastTimestamp >"$OUT/02-eventos.txt" 2>&1 || true
{ echo "## depois"; clock_offset; } >>"$OUT/02-relogio.txt"
psql_stats "select extract(epoch from processed_at) from \"tenant_${SLUG}\".processed_event order by 1" \
  >"$OUT/02-processados.txt"
"$PY" "$(dirname "$0")/atraso_consistencia.py" "$OUT" | tee "$OUT/02-atraso.txt"
"$PY" "$(dirname "$0")/resumo_carga.py" "$OUT" | tee "$OUT/02-resumo.txt"
log "carga concluida; arquivos em $OUT"
