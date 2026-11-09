#!/usr/bin/env bash
# Configuracao C3 da bateria (devolutiva do TCC 2, 2026-11-08): mesma topologia e mesmo HPA da
# C2, com tres ajustes, cada um ligado a um gargalo medido na C2:
#   1. request de CPU das aplicacoes de 100m para 250m: com 100m, um unico login (hash de senha)
#      levava o auth-service a 278% do request e o HPA criava 3 replicas, cada uma gastando 500m
#      so para subir a JVM num no ja saturado;
#   2. banco do Servico de Estatisticas de 500m/512Mi para 2000m/2Gi (igual ao de apostas): na C2
#      ele ficou no limite de 500 mCPU durante todo o consumo da fila;
#   3. dois consumidores por replica do stats-service (padrao do Spring e 1): a fila chegou a
#      96.822 eventos com quatro replicas.
# Limites das aplicacoes (500m) e teto do HPA (4 replicas) continuam iguais.
set -euo pipefail
NS="${NS:-default}"
HERE="$(cd "$(dirname "$0")" && pwd)"
kubectl -n "$NS" apply -f "$HERE/../../infra/k8s/hpa.yaml"
for d in api-gateway auth-service bets-service stats-service; do
  kubectl -n "$NS" set resources "deploy/$d" --requests=cpu=250m
done
kubectl -n "$NS" set resources deploy/postgres-stats --requests=cpu=500m,memory=1Gi --limits=cpu=2000m,memory=2Gi
kubectl -n "$NS" set env deploy/stats-service SPRING_RABBITMQ_LISTENER_SIMPLE_CONCURRENCY=2
for d in postgres-stats api-gateway auth-service bets-service stats-service; do
  kubectl -n "$NS" rollout status "deploy/$d" --timeout=300s
done
