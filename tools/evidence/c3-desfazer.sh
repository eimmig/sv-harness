#!/usr/bin/env bash
# Volta da configuracao C3 para a de producao (valores de infra/k8s/*.yaml).
set -euo pipefail
NS="${NS:-default}"
for d in api-gateway auth-service bets-service stats-service; do
  kubectl -n "$NS" set resources "deploy/$d" --requests=cpu=100m
done
kubectl -n "$NS" set resources deploy/postgres-stats --requests=cpu=100m,memory=256Mi --limits=cpu=500m,memory=512Mi
kubectl -n "$NS" set env deploy/stats-service SPRING_RABBITMQ_LISTENER_SIMPLE_CONCURRENCY-
for d in postgres-stats api-gateway auth-service bets-service stats-service; do
  kubectl -n "$NS" rollout status "deploy/$d" --timeout=300s
done
