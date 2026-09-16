#!/usr/bin/env python3
"""Aplica o RBAC de CI (infra/k8s/ci-deployer-rbac.yaml) no cluster k3s de producao,
gera um token de longa duracao pro ServiceAccount `ci-deployer` e distribui como o
secret `KUBE_CONFIG` nos 6 repositorios de aplicacao, via `gh`.

Roda contra o kubeconfig ja configurado no ambiente do operador (variavel KUBECONFIG
ou ~/.kube/config, o padrao do kubectl) - este script nunca guarda nem assume nenhuma
credencial de cluster propria, so usa a que o operador ja tem. Precisa ser rodado por
alguem com acesso real ao cluster de producao - nao roda numa sessao sem essa
conectividade (ver infra/CLAUDE.md secao "CD automatico").

O token e a menor coisa privilegiada que este script produz: nunca e impresso (mesmo
--check so mostra se o secret ja existe em cada repo, nao o valor). Mesmo padrao de
tools/sonar_setup.py (SONAR_TOKEN) - so que aqui a credencial nao vem de um arquivo
.env local, e mintada na hora a partir do cluster real.

Duracao do token via TokenRequest API (`kubectl create token`, nao a Secret estatica
tipo kubernetes.io/service-account-token - essa forma legada de token que nunca expira
sozinho e desencorajada pela documentacao oficial do Kubernetes desde a 1.24). Default
8760h (1 ano) - precisa ser rodado de novo antes de expirar (sem rotacao automatica,
mesmo tradeoff aceito para o restante das credenciais deste projeto - PASETO_LOCAL_KEY,
ADMIN_API_KEY etc. tambem sao estaticas).

Uso:

    python tools/kube_deploy_setup.py --check              # so verifica, nao aplica nem grava
    python tools/kube_deploy_setup.py                       # aplica RBAC + gera token (1 ano) + distribui
    python tools/kube_deploy_setup.py --duration 4380h       # duracao customizada (ex.: 6 meses)
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RBAC_MANIFEST = ROOT / "infra" / "k8s" / "ci-deployer-rbac.yaml"
SERVICE_ACCOUNT = "ci-deployer"
DEFAULT_DURATION = "8760h"
DURATION_RE = re.compile(r"^\d+[hms]$")

# pasta local -> repositorio GitHub. Mesma lista de tools/sonar_setup.py (os 6 de
# aplicacao) - `infra` fica de fora: nao tem job de deploy proprio, so provisiona o
# RBAC do lado do cluster.
REPOS = {
    "services/api-gateway": "sv-api-gateway",
    "services/auth-service": "sv-auth-backend",
    "services/bets-service": "sv-bets-backend",
    "services/stats-service": "sv-stats-backend",
    "services/telegram-integration": "sv-telegram-integration-backend",
    "apps/web": "sv-frontend",
}
GH = pathlib.Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GitHub CLI" / "gh.exe"


def kubectl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["kubectl", *args], capture_output=True, text=True)


def require_cluster_reachable() -> None:
    result = kubectl(["cluster-info"])
    if result.returncode != 0:
        sys.exit(
            "ERRO: kubectl nao consegue falar com o cluster (contexto atual: "
            + kubectl(["config", "current-context"]).stdout.strip()
            + "). Aponte o kubeconfig pro k3s de producao antes de rodar este script.\n"
            + result.stderr.strip()
        )


def apply_rbac() -> None:
    if not RBAC_MANIFEST.exists():
        sys.exit(f"ERRO: {RBAC_MANIFEST} nao existe.")
    result = kubectl(["apply", "-f", str(RBAC_MANIFEST)])
    if result.returncode != 0:
        sys.exit(f"ERRO ao aplicar {RBAC_MANIFEST}:\n{result.stderr.strip()}")
    print(result.stdout.strip())


def mint_token(duration: str) -> str:
    if not DURATION_RE.match(duration):
        sys.exit(f"ERRO: --duration invalido '{duration}' (esperado ex.: 8760h, 30m, 45s).")
    result = kubectl(["create", "token", SERVICE_ACCOUNT, "--duration", duration])
    if result.returncode != 0:
        sys.exit(f"ERRO ao gerar token pro ServiceAccount '{SERVICE_ACCOUNT}':\n{result.stderr.strip()}")
    return result.stdout.strip()


def current_cluster_info() -> tuple[str, str]:
    """(server, ca-data-base64) do contexto kubectl atual, via `kubectl config view --minify`."""
    result = kubectl(["config", "view", "--minify", "--raw", "-o", "json"])
    if result.returncode != 0:
        sys.exit(f"ERRO ao ler o kubeconfig atual:\n{result.stderr.strip()}")
    config = json.loads(result.stdout)
    cluster = config["clusters"][0]["cluster"]
    server = cluster["server"]
    ca_data = cluster.get("certificate-authority-data")
    if not ca_data:
        sys.exit(
            "ERRO: o cluster atual nao tem certificate-authority-data no kubeconfig "
            "(certificado via arquivo separado?) - ajuste build_kubeconfig() pra esse caso."
        )
    return server, ca_data


def build_kubeconfig(server: str, ca_data: str, token: str) -> str:
    """Kubeconfig minimo e autocontido - so o necessario pro `kubectl rollout restart`
    do job de deploy, sem nenhum outro contexto/usuario do kubeconfig do operador."""
    return f"""apiVersion: v1
kind: Config
clusters:
  - name: stakevault
    cluster:
      server: {server}
      certificate-authority-data: {ca_data}
contexts:
  - name: ci-deployer
    context:
      cluster: stakevault
      user: ci-deployer
current-context: ci-deployer
users:
  - name: ci-deployer
    user:
      token: {token}
"""


def gh(args: list[str], token: str | None, input_text: str | None = None) -> subprocess.CompletedProcess:
    environ = dict(os.environ)
    if token:
        environ["GH_TOKEN"] = token
    return subprocess.run([str(GH), *args], capture_output=True, text=True, env=environ, input=input_text)


def github_token() -> str:
    """GH_TOKEN do ambiente; senao, a credencial que o git ja usa para github.com."""
    if os.environ.get("GH_TOKEN"):
        return os.environ["GH_TOKEN"]
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            return line.partition("=")[2]
    sys.exit("ERRO: sem GH_TOKEN e sem credencial armazenada para github.com.")


def fix_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def report_check(token_gh: str) -> None:
    sa = kubectl(["get", "serviceaccount", SERVICE_ACCOUNT])
    print(f"ServiceAccount '{SERVICE_ACCOUNT}': {'OK' if sa.returncode == 0 else 'FALTA (rode sem --check)'}")
    print()
    for folder, repo in REPOS.items():
        slug = f"eimmig/{repo}"
        secrets = gh(["secret", "list", "--repo", slug], token_gh).stdout
        print(f"{folder:34s} KUBE_CONFIG={'sim' if 'KUBE_CONFIG' in secrets else 'NAO'}")


def distribute_kubeconfig(token_gh: str, kubeconfig: str) -> None:
    print()
    for folder, repo in REPOS.items():
        slug = f"eimmig/{repo}"
        result = gh(["secret", "set", "KUBE_CONFIG", "--repo", slug, "--body", kubeconfig], token_gh)
        status = "ok" if result.returncode == 0 else "FALHOU"
        detail = "" if status == "ok" else f"  {result.stderr.strip()[:120]}"
        print(f"{folder:34s} KUBE_CONFIG: {status}{detail}")


def main() -> None:
    fix_console_encoding()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="so verifica cluster/RBAC/secrets existentes, nao aplica nem grava")
    parser.add_argument("--duration", default=DEFAULT_DURATION,
                        help=f"duracao do token via TokenRequest API (default {DEFAULT_DURATION})")
    args = parser.parse_args()

    if not GH.exists():
        sys.exit(f"ERRO: gh nao encontrado em {GH}. Instale com: winget install GitHub.cli")

    require_cluster_reachable()
    token_gh = github_token()

    if args.check:
        report_check(token_gh)
        return

    apply_rbac()
    sa_token = mint_token(args.duration)
    server, ca_data = current_cluster_info()
    kubeconfig = build_kubeconfig(server, ca_data, sa_token)

    distribute_kubeconfig(token_gh, kubeconfig)

    print(f"\nToken valido por {args.duration} a partir de agora - rode este script de novo antes de expirar.")


if __name__ == "__main__":
    main()
