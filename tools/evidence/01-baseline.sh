#!/usr/bin/env bash
source "$(dirname "$0")/lib.sh"
require kubectl

log "saida em $OUT"
snapshot 01-baseline

{
  echo "## versoes e capacidade"
  k exec deploy/postgres-bets -- psql -U bets_user -d bets -tAc "show server_version"
  k exec deploy/redis -- sh -c 'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" info server' | grep redis_version
  kubectl describe nodes | grep -A8 "Allocated resources"
  kubectl get deploy -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image
} >"$OUT/01-versoes.txt" 2>&1 || true

cat "$OUT/01-baseline.txt" "$OUT/01-versoes.txt"
log "baseline salvo"
