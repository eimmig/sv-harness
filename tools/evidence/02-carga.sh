#!/usr/bin/env bash
source "$(dirname "$0")/lib.sh"
require kubectl curl python3
python3 -c "import requests" 2>/dev/null || { echo "instale: sudo apt install python3-requests" >&2; exit 1; }

N_BETS="${1:-50000}"
WORKERS="${2:-64}"
GATEWAY="${GATEWAY:-$BASE_URL}"

log "saida em $OUT, $N_BETS apostas, $WORKERS threads"
snapshot 02-antes

port_forward svc/auth-service 18081:8081
sample_loop "$OUT/02-hpa.txt" kubectl -n "$NS" get hpa
sample_loop "$OUT/02-pods.txt" kubectl -n "$NS" get pods
sample_loop "$OUT/02-top.txt" kubectl -n "$NS" top pods
sample_loop "$OUT/02-filas.txt" kubectl -n "$NS" exec deploy/rabbitmq -- rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers

ADMIN_API_KEY="$(secret ADMIN_API_KEY)" python3 "$TOOLS_DIR/load_test_bets.py" \
  --n-bets "$N_BETS" --workers "$WORKERS" \
  --auth-base-url http://localhost:18081 --gateway-base-url "$GATEWAY" \
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
log "carga concluida; arquivos em $OUT"
