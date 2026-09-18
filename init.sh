#!/usr/bin/env bash
# Root-level verification for the bankroll management platform. This is NOT a monorepo:
# each service folder below is its own independent Git repository (nested here only for
# local convenience). This script is the aggregated dashboard for a multi-level harness:
# it checks tooling shared across all services, then reports (but does not gate on) the
# status of each service's own init.sh. A service failing its own init.sh before its epic
# has started is expected and does not fail this script — only missing *shared* tooling
# does. Run the service's own ./init.sh from inside services/<name>/ (or apps/web/) for a
# real pass/fail gate on that service's work.
set -euo pipefail

fail=0

check_tool() {
  local name="$1" cmds="$2" min_hint="$3"
  local cmd version
  for cmd in $cmds; do
    if command -v "$cmd" >/dev/null 2>&1; then
      version="$("$cmd" --version 2>&1 | head -n1 || true)"
      if [[ "$version" =~ [0-9] ]]; then
        echo "OK   $name found ($version) — resolved as '$cmd'"
        return 0
      fi
      # Windows sometimes ships a fake stub (Microsoft Store app execution alias) that
      # resolves on PATH but only prints a redirect message instead of a version — skip
      # it and try the next candidate command instead of failing immediately.
    fi
  done
  echo "MISS $name not found on PATH (need $min_hint) — tried: $cmds"
  fail=1
}

echo "== Shared tooling =="
check_tool "Docker" "docker" "Docker 24.x+"
check_tool "Java" "java" "Java 25 (JDK)"
check_tool "Node.js" "node" "Node.js compatible with Angular 22.x"
check_tool "npm" "npm" "npm (bundled with Node.js)"
# Windows' official python.org installer only ships 'python.exe', not 'python3' — try
# both, in that order, since 'python3' is the POSIX-conventional name where it exists.
check_tool "Python" "python3 python" "Python 3.12+"

echo ""
echo "== CI/CD workflows (informational — does not affect this script's exit code) =="
echo "   See docs/CI-CD.md. Each harness is its own repo — workflow lives inside its own folder,"
echo "   and only runs once that repo exists on GitHub (+ SonarCloud, for application services)."
for svc_path in "infra" "services/api-gateway" "services/auth-service" "services/bets-service" \
                "services/stats-service" "services/telegram-integration" "apps/web"; do
  if [[ -f "$svc_path/.github/workflows/ci.yml" ]]; then
    echo "OK   $svc_path/.github/workflows/ci.yml present"
  else
    echo "MISS $svc_path/.github/workflows/ci.yml not created yet"
  fi
done

echo ""
echo "== Sub-harness status (informational — does not affect this script's exit code) =="
for svc_path in "infra" "services/api-gateway" "services/auth-service" "services/bets-service" \
                "services/stats-service" "services/telegram-integration" "apps/web"; do
  if [[ ! -d "$svc_path" ]]; then
    echo "----  $svc_path not created yet"
    continue
  fi
  if [[ ! -f "$svc_path/init.sh" ]]; then
    echo "WARN $svc_path exists but has no init.sh (harness incomplete)"
    continue
  fi
  echo "..   running $svc_path/init.sh"
  if (cd "$svc_path" && ./init.sh >/tmp/root-init-sub.log 2>&1); then
    echo "OK   $svc_path/init.sh passed"
  else
    echo "FAIL $svc_path/init.sh failed (expected until that epic is under way) — see feature_list.json there"
    tail -n 5 /tmp/root-init-sub.log | sed 's/^/     | /'
  fi
done

echo ""
if [[ "$fail" -ne 0 ]]; then
  echo "Missing required shared tooling above. Install it before starting epic-001."
  exit 1
fi

echo "Shared tooling check passed. See feature_list.json for the next epic to pick up,"
echo "then drill into that service's own feature_list.json for the granular next step."
