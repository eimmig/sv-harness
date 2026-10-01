#!/usr/bin/env bash
source "$(dirname "$0")/lib.sh"
require kubectl curl python3

RMQ="http://localhost:15672/api"
SLUG="dlq-$(date +%s)"

make_event() {
  python3 - "$1" <<'PY'
import json, sys, uuid, datetime
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
print(json.dumps({
    "eventId": str(uuid.uuid4()), "eventType": "BetCreated", "schemaVersion": 1, "occurredAt": now,
    "tenantId": sys.argv[1], "userId": str(uuid.uuid4()),
    "payload": {
        "betId": str(uuid.uuid4()), "bettingHouseId": str(uuid.uuid4()), "bettingHouseName": "House",
        "sportId": str(uuid.uuid4()), "sportName": "Sport", "leagueId": str(uuid.uuid4()), "leagueName": "League",
        "marketId": str(uuid.uuid4()), "marketName": "Market", "tipsterId": None, "tipsterName": None,
        "ticketNumber": None, "team1Id": None, "team1": None, "team2": None, "description": None,
        "betType": None, "playType": None, "stake": 100.0, "odd": 1.5, "status": "pending", "betDate": now,
    },
}))
PY
}

publish() {
  python3 - "$1" "$2" <<'PY' | rabbit_api -X POST -d @- "$RMQ/exchanges/%2F/bets.events/publish"
import json, sys
print(json.dumps({"properties": {"delivery_mode": 2, "content_type": "application/json"},
                  "routing_key": sys.argv[1], "payload": sys.argv[2], "payload_encoding": "string"}))
PY
  echo
}

dlq_get() {
  python3 -c "import json; print(json.dumps({'count': 50, 'ackmode': '$1', 'encoding': 'auto'}))" \
    | rabbit_api -X POST -d @- "$RMQ/queues/%2F/stats.bet-events.dlq/get"
}

log "saida em $OUT"
port_forward svc/rabbitmq 15672:15672
port_forward svc/auth-service 18081:8081

log "esvaziando fila principal e DLQ"
rabbit_api -X DELETE "$RMQ/queues/%2F/stats.bet-events/contents" >/dev/null || true
rabbit_api -X DELETE "$RMQ/queues/%2F/stats.bet-events.dlq/contents" >/dev/null || true
snapshot 03-antes

log "cenario A: mensagem fora do contrato (vai direto para a DLQ)"
publish bet.created '{"eventId":"nao-e-uuid","eventType":"BetCreated"}' | tee -a "$OUT/03-publicacoes.txt"

log "cenario B: evento valido de um tenant que ainda nao existe (retry e depois DLQ)"
EVENT_B="$(make_event "$SLUG")"
BET_B="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['payload']['betId'])" "$EVENT_B")"
publish bet.created "$EVENT_B" | tee -a "$OUT/03-publicacoes.txt"

log "esperando o consumidor esgotar as tentativas"
for _ in $(seq 1 30); do
  dlq="$(queue_depth stats.bet-events.dlq)"
  [ "${dlq:-0}" -ge 2 ] && break
  sleep 2
done
snapshot 03-durante
dlq_get ack_requeue_true | python3 -m json.tool >"$OUT/03-dlq-mensagens.json"
k logs deploy/stats-service --since=10m | grep -iE "reject|retry|attempt|dead|unprovision|tenant|schema" >"$OUT/03-logs-stats.txt" || true

log "DLQ tem ${dlq:-?} mensagens (esperado 2); conteudo em 03-dlq-mensagens.json"

if [ -t 0 ]; then
  read -r -p "Tire agora as capturas da DLQ na interface do RabbitMQ e aperte Enter para continuar... " _
fi

log "recuperacao: provisionar o tenant e republicar a mensagem do cenario B"
curl -s -X POST localhost:18081/api/v1/admin/tenants -H "X-Admin-Api-Key: $(secret ADMIN_API_KEY)" \
  -H 'content-type: application/json' -d "{\"slug\":\"$SLUG\",\"tenantName\":\"DLQ\"}" >"$OUT/03-tenant.json"

dlq_get ack_requeue_false >"$OUT/03-dlq-drenada.json"
python3 - "$SLUG" "$OUT/03-dlq-drenada.json" >"$OUT/03-reenvio.json" <<'PY'
import json, sys
for msg in json.load(open(sys.argv[2])):
    if sys.argv[1] in msg["payload"]:
        print(msg["payload"])
        break
PY
[ -s "$OUT/03-reenvio.json" ] || { log "mensagem do cenario B nao encontrada na DLQ"; exit 1; }
publish bet.created "$(cat "$OUT/03-reenvio.json")" | tee -a "$OUT/03-publicacoes.txt"

for _ in $(seq 1 30); do
  found="$(psql_stats "select count(*) from \"tenant_${SLUG}\".fact_bet where id = '${BET_B}'" 2>/dev/null || echo 0)"
  [ "$found" = "1" ] && break
  sleep 2
done

{
  echo "tenant do cenario B          : $SLUG"
  echo "aposta do cenario B          : $BET_B"
  echo "linhas em fact_bet (esperado 1) : ${found:-0}   $([ "${found:-0}" = "1" ] && echo PASS || echo FAIL)"
  echo "mensagens na DLQ depois de drenar : $(queue_depth stats.bet-events.dlq)"
} | tee "$OUT/03-resultado.txt"
snapshot 03-depois
