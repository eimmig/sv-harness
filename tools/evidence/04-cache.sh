#!/usr/bin/env bash
source "$(dirname "$0")/lib.sh"
require kubectl curl python3

SLUG="${1:?uso: 04-cache.sh <slug> <email> <senha> [requisicoes]}"
EMAIL="${2:?uso: 04-cache.sh <slug> <email> <senha> [requisicoes]}"
PASSWORD="${3:?uso: 04-cache.sh <slug> <email> <senha> [requisicoes]}"
REQUESTS="${4:-50}"

log "saida em $OUT"

TOKEN="$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H 'content-type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")"
[ -n "$TOKEN" ] || { log "login falhou"; exit 1; }

stats_time() {
  curl -s -o /dev/null -w '%{http_code} %{time_total}\n' -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/statistics"
}

hits_misses() { redis info stats | grep -E "keyspace_(hits|misses)" | tr -d '\r'; }

log "limpando as chaves do tenant para forcar cache miss"
for key in $(redis --scan --pattern "*${SLUG}*" | tr -d '\r'); do redis del "$key" >/dev/null; done
redis --scan --pattern "*${SLUG}*" >"$OUT/04-chaves-antes.txt" || true

hits_misses >"$OUT/04-redis-antes.txt"

log "requisicao 1 (cache miss, calcula no banco OLAP)"
echo "miss $(stats_time)" | tee "$OUT/04-tempos.txt"

log "requisicoes 2 a $REQUESTS (cache hit)"
for _ in $(seq 2 "$REQUESTS"); do
  echo "hit $(stats_time)" >>"$OUT/04-tempos.txt"
done

hits_misses >"$OUT/04-redis-depois.txt"
redis --scan --pattern "*${SLUG}*" | tr -d '\r' >"$OUT/04-chaves-depois.txt"

{
  echo "## chaves do tenant e TTL (segundos)"
  while read -r key; do
    [ -n "$key" ] && echo "$key  ttl=$(redis ttl "$key" | tr -d '\r')"
  done <"$OUT/04-chaves-depois.txt"
  echo
  echo "## conteudo da chave do dashboard consolidado"
  dash="$(grep -m1 "dashboard" "$OUT/04-chaves-depois.txt" || true)"
  [ -n "$dash" ] && redis get "$dash" | python3 -m json.tool | head -40
} >"$OUT/04-redis-chaves.txt" 2>&1

python3 - "$OUT/04-tempos.txt" <<'PY' | tee "$OUT/04-resumo.txt"
import sys
miss, hit = [], []
for line in open(sys.argv[1]):
    kind, code, seconds = line.split()
    (miss if kind == "miss" else hit).append(float(seconds) * 1000)
hit.sort()
def pct(values, p):
    return values[min(len(values) - 1, int(len(values) * p))]
print(f"primeira requisicao (miss)      : {miss[0]:.1f} ms")
if hit:
    print(f"requisicoes com cache (n={len(hit)})   : p50={pct(hit, .50):.1f} ms  p95={pct(hit, .95):.1f} ms  max={hit[-1]:.1f} ms")
    print(f"RNF03 (< 300 ms com cache quente): {'PASS' if pct(hit, .95) < 300 else 'FAIL'}")
PY

{
  echo "## hits e misses do Redis antes das requisicoes"
  cat "$OUT/04-redis-antes.txt"
  echo "## hits e misses do Redis depois das requisicoes"
  cat "$OUT/04-redis-depois.txt"
} | tee "$OUT/04-redis-delta.txt"
