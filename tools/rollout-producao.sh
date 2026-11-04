#!/usr/bin/env bash
# Rollout manual no k3s de producao. Uso:
#   bash tools/rollout-producao.sh backend   # auth-service + stats-service
#   bash tools/rollout-producao.sh web       # release develop -> main do web + rollout
# HOST=<ip> sobrescreve o IP do servidor (nao e fixo).
set -euo pipefail

HOST="${HOST:-192.168.2.124}"
kube() { ssh "eduardo@${HOST}" "KUBECONFIG=~/.kube/config kubectl $*"; }

restart() {
  for d in "$@"; do
    kube rollout restart "deployment/${d}"
  done
  for d in "$@"; do
    kube rollout status "deployment/${d}" --timeout=300s
    kube get pods -l "app=${d}" -o "custom-columns=POD:.metadata.name,IMAGE:.status.containerStatuses[0].imageID"
  done
}

case "${1:-}" in
  backend)
    restart auth-service stats-service
    echo "Conferir: GET https://${HOST}/api/v1/telegram-links/me com token valido responde 200."
    ;;
  web)
    cd "$(dirname "$0")/../apps/web"
    pr=$(gh pr create --base main --head develop \
      --title "Release develop to main: feat-078, feat-072" \
      --body "Release of feat-078 (Telegram link status) and feat-072 (single unit base)." \
      | grep -o '[0-9]*$')
    gh pr checks "$pr" --watch
    gh pr merge "$pr" --merge
    sha=$(gh pr view "$pr" --json mergeCommit -q .mergeCommit.oid)
    echo "Esperando o build-and-push-image do merge ${sha}..."
    until run=$(gh run list --branch main --json databaseId,headSha \
        -q ".[] | select(.headSha==\"${sha}\") | .databaseId" | head -1) && [ -n "$run" ]; do
      sleep 10
    done
    while :; do
      c=$(gh run view "$run" --json jobs \
        -q '.jobs[] | select(.name=="build-and-push-image") | .conclusion')
      [ "$c" = "success" ] && break
      if [ -n "$c" ]; then echo "build-and-push-image: ${c}" >&2; exit 1; fi
      sleep 15
    done
    restart web
    echo "Conferir a tela Vincular Telegram por https://${HOST}."
    ;;
  *)
    echo "uso: $0 backend|web" >&2
    exit 1
    ;;
esac
