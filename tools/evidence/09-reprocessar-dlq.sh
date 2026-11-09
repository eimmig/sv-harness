#!/usr/bin/env bash
# Reprocessa a DLQ depois de uma bateria e reconcilia as organizacoes afetadas (devolutiva do
# TCC 2, 2026-11-08). Na configuracao C3, o no saturado fez a sonda de vivacidade do RabbitMQ
# estourar o tempo limite, e o kubelet reiniciou o broker de 4 a 6 vezes por rodada. Cada reinicio
# reentrega as mensagens que estavam com os consumidores sem confirmacao; as que passam do
# delivery-limit da fila quorum vao para a DLQ, mesmo ja processadas.
#
# Passos: (1) reconciliacao de cada organizacao antes; (2) para cada mensagem da DLQ, se o eventId
# ja esta em processed_event; (3) drena a DLQ e republica cada mensagem no exchange bets.events com
# a routing key original (o consumo idempotente descarta as ja processadas); (4) reconciliacao
# depois.
#
# Uso: 09-reprocessar-dlq.sh <slug> [<slug> ...]
source "$(dirname "$0")/lib.sh"
require kubectl curl
PY="${PYTHON:-python3}"
RMQ="http://localhost:15672/api"

reconcile() {
  local slug="$1" bets settled fact processed
  bets="$(psql_bets "select count(*) from \"tenant_${slug}\".bet")"
  settled="$(psql_bets "select count(*) from \"tenant_${slug}\".bet where status <> 'pending'")"
  fact="$(psql_stats "select count(*) from \"tenant_${slug}\".fact_bet")"
  processed="$(psql_stats "select count(*) from \"tenant_${slug}\".processed_event")"
  printf '%-20s esperados=%-7s processados=%-7s %s   apostas=%-7s fact_bet=%-7s %s\n' "$slug" \
    "$((bets + settled))" "$processed" "$([ "$processed" = "$((bets + settled))" ] && echo PASS || echo FAIL)" \
    "$bets" "$fact" "$([ "$fact" = "$bets" ] && echo PASS || echo FAIL)"
}

log "saida em $OUT"
port_forward svc/rabbitmq 15672:15672

{ echo "## antes do reprocessamento ($(date -Is))"; for s in "$@"; do reconcile "$s"; done
  echo "mensagens na DLQ: $(queue_depth stats.bet-events.dlq)"; } | tee "$OUT/09-antes.txt"

echo '{"count": 1000, "ackmode": "ack_requeue_false", "encoding": "auto"}' \
  | rabbit_api -X POST -d @- "$RMQ/queues/%2F/stats.bet-events.dlq/get" >"$OUT/09-dlq.json"

# eventId de cada mensagem e se ja estava processado
"$PY" - "$OUT/09-dlq.json" >"$OUT/09-dlq-ids.tsv" <<'PY'
import json, sys
for m in json.load(open(sys.argv[1], encoding="utf-8")):
    p = json.loads(m["payload"])
    h = m["properties"].get("headers", {})
    print("\t".join([p["tenantId"], p["eventId"], p["eventType"], h.get("x-first-death-reason", "?"),
                     str(h.get("x-delivery-count", "?"))]))
PY
{
  echo "## mensagens drenadas da DLQ, por organizacao, motivo e se o evento ja estava processado"
  while IFS=$'\t' read -r tenant id type reason count; do
    done_="$(psql_stats "select count(*) from \"tenant_${tenant}\".processed_event where event_id = '${id}'")"
    printf '%s\t%s\t%s\tentregas=%s\tja_processado=%s\n' "$tenant" "$type" "$reason" "$count" "$done_"
  done <"$OUT/09-dlq-ids.tsv" | sort | uniq -c
} | tee "$OUT/09-dlq-resumo.txt"

# republica com a routing key original (x-death[0].routing-keys[0])
"$PY" - "$OUT/09-dlq.json" <<'PY' >"$OUT/09-republicar.jsonl"
import json, sys
for m in json.load(open(sys.argv[1], encoding="utf-8")):
    rk = m["properties"]["headers"]["x-death"][0]["routing-keys"][0]
    print(json.dumps({"properties": {"delivery_mode": 2, "content_type": "application/json"},
                      "routing_key": rk, "payload": m["payload"], "payload_encoding": "string"}))
PY
n=0
while IFS= read -r body; do
  printf '%s' "$body" | rabbit_api -X POST -d @- "$RMQ/exchanges/%2F/bets.events/publish" >>"$OUT/09-publicacoes.txt"
  echo >>"$OUT/09-publicacoes.txt"; n=$((n + 1))
done <"$OUT/09-republicar.jsonl"
log "republicadas $n mensagens"

for _ in $(seq 1 30); do
  [ "$(queue_depth stats.bet-events)" = "0" ] && break
  sleep 5
done
sleep 5
{ echo "## depois do reprocessamento ($(date -Is))"; for s in "$@"; do reconcile "$s"; done
  echo "mensagens na DLQ: $(queue_depth stats.bet-events.dlq)"; } | tee "$OUT/09-depois.txt"
