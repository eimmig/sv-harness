#!/usr/bin/env bash
# C2 com o banco do Servico de Estatisticas nos valores da bateria de 2026-11-08 (500m/512Mi).
# Depois de infra feat-014 (2026-11-09) producao usa 2000m/2Gi; esta configuracao isola o efeito
# das somas diarias de stats-service feat-036 (trigger em fact_bet e recalculo agendado) na
# comparacao com as rodadas c2 daquela bateria. Desfazer: kubectl apply -f infra/k8s/postgres.yaml.
set -euo pipefail
NS="${NS:-default}"
HERE="$(cd "$(dirname "$0")" && pwd)"
kubectl -n "$NS" apply -f "$HERE/../../infra/k8s/hpa.yaml"
kubectl -n "$NS" set resources deploy/postgres-stats --requests=cpu=100m,memory=256Mi --limits=cpu=500m,memory=512Mi
kubectl -n "$NS" rollout status deploy/postgres-stats --timeout=300s
