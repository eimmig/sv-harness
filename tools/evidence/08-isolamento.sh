#!/usr/bin/env bash
# Evidencia do isolamento por schema (devolutiva do TCC 2, 2026-11-08: "foi testado?").
# Usa duas organizacoes criadas por rodadas do 02-carga.sh (o 02-carga.txt de cada uma traz o
# e-mail e a senha do administrador): lista os schemas e as contagens nos dois bancos e mostra,
# pela API, que o token de A so ve as apostas de A e recebe 404 ao pedir uma aposta de B.
#
# Uso: 08-isolamento.sh <pasta-da-rodada-A> <pasta-da-rodada-B>
source "$(dirname "$0")/lib.sh"
PY="${PYTHON:-python3}"
require kubectl curl "$PY"
GATEWAY="${GATEWAY:-$BASE_URL}"
CURL=(curl -s)
[ "${INSECURE:-0}" = 1 ] && CURL+=(-k)

creds() {
  local f="$1/02-carga.txt"
  SLUG_X="$(grep -m1 'tenant slug' "$f" | awk '{ print $NF }')"
  EMAIL_X="$(grep -m1 'admin email ' "$f" | awk '{ print $NF }')"
  PASS_X="$(grep -m1 'admin password' "$f" | awk '{ print $NF }')"
}
login() {
  "${CURL[@]}" -H 'content-type: application/json' -X POST "$GATEWAY/api/v1/auth/login" \
    -d "{\"slug\":\"$1\",\"email\":\"$2\",\"password\":\"$3\"}" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['token'])"
}
api() { "${CURL[@]}" -H "Authorization: Bearer $1" "$GATEWAY$2"; }
status_of() { "${CURL[@]}" -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $1" "$GATEWAY$2"; }
total() { "$PY" -c "import json,sys; print(json.load(sys.stdin)['totalElements'])"; }

creds "$1"; SLUG_A="$SLUG_X"; TOKEN_A="$(login "$SLUG_X" "$EMAIL_X" "$PASS_X")"
creds "$2"; SLUG_B="$SLUG_X"; TOKEN_B="$(login "$SLUG_X" "$EMAIL_X" "$PASS_X")"
log "organizacoes: A=$SLUG_A B=$SLUG_B"

{
  echo "## schemas de organizacao e apostas em cada um (banco de apostas)"
  for s in $(psql_bets "select schema_name from information_schema.schemata where schema_name like 'tenant_%' order by 1"); do
    echo "$s $(psql_bets "select count(*) from \"$s\".bet")"
  done
  echo "## schemas de organizacao e linhas da tabela fato (banco de estatisticas)"
  for s in $(psql_stats "select schema_name from information_schema.schemata where schema_name like 'tenant_%' order by 1"); do
    echo "$s $(psql_stats "select count(*) from \"$s\".fact_bet")"
  done
} | tee "$OUT/08-schemas.txt"

BET_B="$(psql_bets "select id from \"tenant_${SLUG_B}\".bet limit 1")"
BET_A="$(psql_bets "select id from \"tenant_${SLUG_A}\".bet limit 1")"
{
  echo "apostas no schema de A (banco)       : $(psql_bets "select count(*) from \"tenant_${SLUG_A}\".bet")"
  echo "apostas listadas pela API com token A: $(api "$TOKEN_A" '/api/v1/bets?size=1' | total)"
  echo "apostas no schema de B (banco)       : $(psql_bets "select count(*) from \"tenant_${SLUG_B}\".bet")"
  echo "apostas listadas pela API com token B: $(api "$TOKEN_B" '/api/v1/bets?size=1' | total)"
  echo "GET aposta de A com token A          : HTTP $(status_of "$TOKEN_A" "/api/v1/bets/$BET_A")"
  echo "GET aposta de B com token A          : HTTP $(status_of "$TOKEN_A" "/api/v1/bets/$BET_B")"
  echo "GET aposta de A com token B          : HTTP $(status_of "$TOKEN_B" "/api/v1/bets/$BET_A")"
} | tee "$OUT/08-api.txt"
