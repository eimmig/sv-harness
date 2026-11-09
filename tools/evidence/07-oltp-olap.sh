#!/usr/bin/env bash
# Compara a mesma agregacao do dashboard no banco transacional (bets-service: bet + bet_result)
# e no dimensional (stats-service: fact_bet + dimensoes), para o mesmo tenant de uma carga
# (devolutiva do TCC 2, 2026-11-08: "nao ha comparacao com consulta direta nas tabelas
# transacionais"). Cada consulta roda uma vez para aquecer o cache do PostgreSQL e depois N
# vezes com EXPLAIN ANALYZE; registra o Execution Time de cada uma.
#
# Uso: 07-oltp-olap.sh <slug-do-tenant> [repeticoes]
source "$(dirname "$0")/lib.sh"
require kubectl
SLUG="$1"
REPS="${2:-10}"
B="\"tenant_${SLUG}\""

OLTP_OVERALL="SELECT SUM(b.stake), SUM(r.profit),
  SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END), SUM(CASE WHEN b.status = 'lost' THEN 1 ELSE 0 END),
  SUM(CASE WHEN b.status = 'void' THEN 1 ELSE 0 END), AVG(b.odd), COUNT(*)
  FROM $B.bet b JOIN $B.bet_result r ON r.bet_id = b.id
  WHERE b.status <> 'pending' AND b.bet_date BETWEEN DATE '1900-01-01' AND DATE '2100-12-31'"
OLTP_SPORT="SELECT s.id, s.name, SUM(b.stake), SUM(r.profit),
  SUM(CASE WHEN b.status = 'won' THEN 1 ELSE 0 END), SUM(CASE WHEN b.status = 'lost' THEN 1 ELSE 0 END),
  AVG(b.odd), COUNT(*)
  FROM $B.bet b JOIN $B.bet_result r ON r.bet_id = b.id JOIN $B.sport s ON s.id = b.sport_id
  WHERE b.status <> 'pending' AND b.bet_date BETWEEN DATE '1900-01-01' AND DATE '2100-12-31'
  GROUP BY s.id, s.name"
OLAP_OVERALL="SELECT SUM(f.stake), SUM(f.profit),
  SUM(CASE WHEN f.is_win THEN 1 ELSE 0 END), SUM(CASE WHEN f.status = 'lost' THEN 1 ELSE 0 END),
  SUM(CASE WHEN f.status = 'void' THEN 1 ELSE 0 END), AVG(f.odd), COUNT(*)
  FROM $B.fact_bet f JOIN $B.dim_date d ON d.id = f.date_id
  WHERE f.status <> 'pending' AND make_date(d.year, d.month, d.day) BETWEEN DATE '1900-01-01' AND DATE '2100-12-31'"
OLAP_SPORT="SELECT s.id, s.name, SUM(f.stake), SUM(f.profit),
  SUM(CASE WHEN f.is_win THEN 1 ELSE 0 END), SUM(CASE WHEN f.status = 'lost' THEN 1 ELSE 0 END),
  AVG(f.odd), COUNT(*)
  FROM $B.fact_bet f JOIN $B.dim_date d ON d.id = f.date_id JOIN $B.dim_sport s ON s.id = f.sport_id
  WHERE f.status <> 'pending' AND make_date(d.year, d.month, d.day) BETWEEN DATE '1900-01-01' AND DATE '2100-12-31'
  GROUP BY s.id, s.name"

measure() {
  local name="$1" db="$2" sql="$3"
  "$db" "$sql" >"$OUT/07-$name-resultado.txt"
  for _ in $(seq 1 "$REPS"); do
    "$db" "EXPLAIN (ANALYZE, SUMMARY ON) $sql" | awk -v n="$name" '/Execution Time/ { print n, $3 }'
  done | tee -a "$OUT/07-tempos.txt"
  "$db" "EXPLAIN (ANALYZE, BUFFERS) $sql" >"$OUT/07-$name-plano.txt"
}

log "tenant $SLUG, $REPS repeticoes"
psql_bets "SELECT status, count(*) FROM $B.bet GROUP BY status ORDER BY 1" >"$OUT/07-volume-oltp.txt"
psql_stats "SELECT status, count(*) FROM $B.fact_bet GROUP BY status ORDER BY 1" >"$OUT/07-volume-olap.txt"
measure oltp-geral psql_bets "$OLTP_OVERALL"
measure olap-geral psql_stats "$OLAP_OVERALL"
measure oltp-esporte psql_bets "$OLTP_SPORT"
measure olap-esporte psql_stats "$OLAP_SPORT"

awk '{ t[$1] = t[$1] " " $2 } END {
  for (k in t) {
    n = split(t[k], v, " "); asort(v)
    m = (n % 2) ? v[(n + 1) / 2] : (v[n / 2] + v[n / 2 + 1]) / 2
    printf "%-14s n=%d mediana=%.1f ms min=%.1f max=%.1f\n", k, n, m, v[1], v[n]
  }
}' "$OUT/07-tempos.txt" | sort | tee "$OUT/07-resumo.txt"
