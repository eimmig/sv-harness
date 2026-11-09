#!/usr/bin/env bash
# Injecao de falhas na consistencia dos eventos (devolutiva do TCC 2, 2026-11-08).
#
# Durante uma carga do 02-carga.sh:
#   F1 - reinicia o RabbitMQ (pod apagado; a fila quorum fica no PVC rabbitmq-data);
#   F2 - apaga todas as replicas do stats-service (consumidor);
#   F3 - apaga as replicas do bets-service (registro e relay do outbox).
# Depois da carga, com o 02-carga.sh ja reconciliado:
#   F4 - publica o mesmo BetCreated tres vezes (mesmo eventId);
#   F5 - publica o BetSettled de uma aposta antes do seu BetCreated.
# Saida: contagens finais (do 02-carga.sh), situacao por aposta nos dois bancos e o resultado
# de F4 e F5.
#
# Uso: 06-falhas.sh [apostas] [threads]
source "$(dirname "$0")/lib.sh"
PY="${PYTHON:-python3}"
require kubectl curl "$PY"

N_BETS="${1:-30000}"
WORKERS="${2:-64}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CARGA="$OUT/carga"
RMQ="http://localhost:15672/api"

wait_ready() {
  # com o no saturado, varias JVMs subindo juntas podem estourar a startup probe e reiniciar;
  # a recuperacao e registrada no log em vez de abortar a carga (rodada de 2026-11-08 19:42)
  local t0=$SECONDS
  if kubectl -n "$NS" rollout status "deploy/$1" --timeout=900s >>"$OUT/log.txt" 2>&1; then
    log "$1 pronto em $((SECONDS - t0)) s"
  else
    log "$1 nao ficou pronto em 900 s"
  fi
  k get pods -l "app=$1" >>"$OUT/log.txt" 2>&1 || true
}

log "saida em $OUT, $N_BETS apostas, $WORKERS threads"
OUT="$CARGA" bash "$HERE/02-carga.sh" "$N_BETS" "$WORKERS" >"$OUT/carga.console.txt" 2>&1 &
CARGA_PID=$!

for _ in $(seq 1 120); do
  grep -q "inicio da carga" "$CARGA/02-carga.txt" 2>/dev/null && break
  sleep 5
done
grep -q "inicio da carga" "$CARGA/02-carga.txt" || { log "a carga nao comecou"; exit 1; }

sleep 60
log "F1: reiniciando o RabbitMQ"
k delete pod -l app=rabbitmq --wait=false >>"$OUT/log.txt" 2>&1
wait_ready rabbitmq
log "F1: RabbitMQ pronto de novo"

sleep 60
log "F2: apagando as replicas do stats-service"
k delete pod -l app=stats-service --wait=false >>"$OUT/log.txt" 2>&1
wait_ready stats-service
log "F2: stats-service pronto de novo"

sleep 60
log "F3: apagando as replicas do bets-service"
k delete pod -l app=bets-service --wait=false >>"$OUT/log.txt" 2>&1
wait_ready bets-service
log "F3: bets-service pronto de novo"

log "esperando a carga e a reconciliacao do 02-carga.sh"
wait "$CARGA_PID" || log "02-carga.sh terminou com erro (ver carga.console.txt)"

SLUG="$(grep -m1 "Criando tenant" "$CARGA/02-carga.txt" | sed -E "s/.*tenant '([^']+)'.*/\1/")"
log "tenant: $SLUG"
{
  echo "## Servico de Apostas (situacao, quantidade)"
  psql_bets "select status, count(*) from \"tenant_${SLUG}\".bet group by status order by status"
  echo "## Servico de Estatisticas (situacao, quantidade)"
  psql_stats "select lower(status), count(*) from \"tenant_${SLUG}\".fact_bet group by status order by 1"
  echo "## Apostas com situacao diferente nos dois bancos"
  psql_bets "select id || ':' || status from \"tenant_${SLUG}\".bet order by id" >"$OUT/bets-estado.txt"
  psql_stats "select id || ':' || lower(status) from \"tenant_${SLUG}\".fact_bet order by id" >"$OUT/stats-estado.txt"
  diff "$OUT/bets-estado.txt" "$OUT/stats-estado.txt" | grep -c '^[<>]' || true
} | tee "$OUT/06-estado.txt"

port_forward svc/rabbitmq 15672:15672

publish() {
  "$PY" - "$1" "$2" <<'PYEOF' | rabbit_api -X POST -d @- "$RMQ/exchanges/%2F/bets.events/publish"
import json, sys
print(json.dumps({"properties": {"delivery_mode": 2, "content_type": "application/json"},
                  "routing_key": sys.argv[1], "payload": sys.argv[2], "payload_encoding": "string"}))
PYEOF
  echo
}

# eventos sinteticos com dimensoes proprias, para nao alterar as contagens da carga
EVENTS="$("$PY" - "$SLUG" <<'PYEOF'
import json, sys, uuid, datetime
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
dims = {"bettingHouseId": str(uuid.uuid4()), "bettingHouseName": "Falhas House",
        "sportId": str(uuid.uuid4()), "sportName": "Falhas Sport",
        "leagueId": str(uuid.uuid4()), "leagueName": "Falhas League",
        "marketId": str(uuid.uuid4()), "marketName": "Falhas Market",
        "tipsterId": None, "tipsterName": None}
def created(bet_id):
    p = dict(dims, betId=bet_id, ticketNumber=None, team1Id=None, team1=None, team2Id=None, team2=None,
             description=None, betType=None, playType=None, stake=100.0, odd=2.0, status="pending", betDate=now)
    return {"eventId": str(uuid.uuid4()), "eventType": "BetCreated", "schemaVersion": 1, "occurredAt": now,
            "tenantId": sys.argv[1], "userId": str(uuid.uuid4()), "payload": p}
def settled(bet_id):
    p = dict(dims, betId=bet_id, team1Id=None, team1Name=None, team2Id=None, team2Name=None,
             stake=100.0, odd=2.0, status="won", profit=100.0, settledAt=now)
    return {"eventId": str(uuid.uuid4()), "eventType": "BetSettled", "schemaVersion": 1, "occurredAt": now,
            "tenantId": sys.argv[1], "userId": str(uuid.uuid4()), "payload": p}
dup, late = str(uuid.uuid4()), str(uuid.uuid4())
out = {"dup_bet": dup, "dup_event": created(dup), "late_bet": late,
       "late_settled": settled(late), "late_created": created(late)}
print(json.dumps(out))
PYEOF
)"
field() { "$PY" -c "import json,sys; v=json.loads(sys.argv[1])[sys.argv[2]]; print(v if isinstance(v,str) else json.dumps(v))" "$EVENTS" "$1"; }
DUP_BET="$(field dup_bet)"
LATE_BET="$(field late_bet)"
DUP_EVENT="$(field dup_event)"
DUP_EVENT_ID="$("$PY" -c "import json,sys; print(json.loads(sys.argv[1])['eventId'])" "$DUP_EVENT")"

log "F4: mesmo BetCreated publicado tres vezes (eventId $DUP_EVENT_ID)"
for _ in 1 2 3; do publish bet.created "$DUP_EVENT" >>"$OUT/06-publicacoes.txt"; done
log "F5: BetSettled antes do BetCreated (aposta $LATE_BET)"
publish bet.settled "$(field late_settled)" >>"$OUT/06-publicacoes.txt"
sleep 5
publish bet.created "$(field late_created)" >>"$OUT/06-publicacoes.txt"
sleep 15

{
  echo "F4 linhas em processed_event com o eventId : $(psql_stats "select count(*) from \"tenant_${SLUG}\".processed_event where event_id = '$DUP_EVENT_ID'")"
  echo "F4 linhas em fact_bet para a aposta         : $(psql_stats "select count(*) from \"tenant_${SLUG}\".fact_bet where id = '$DUP_BET'")"
  echo "F5 situacao final em fact_bet               : $(psql_stats "select lower(status) || ' lucro=' || profit from \"tenant_${SLUG}\".fact_bet where id = '$LATE_BET'")"
  echo "mensagens na DLQ                            : $(queue_depth stats.bet-events.dlq)"
} | tee "$OUT/06-resultado.txt"
log "fim; arquivos em $OUT"
