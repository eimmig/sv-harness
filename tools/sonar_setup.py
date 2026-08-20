#!/usr/bin/env python3
"""Distribui a credencial do SonarCloud para os 6 repositorios de aplicacao.

Le tools/.sonar.env (ver tools/.sonar.env.example), confere contra a API do
SonarCloud que o token e a organizacao existem e que os 6 projetos ja foram
criados, e so entao grava em cada repositorio do GitHub, via `gh`:

    secret   SONAR_TOKEN          (sensivel)
    variable SONAR_ORGANIZATION   (nao e sensivel — e' so a org key)

Sao configurados por repositorio porque o GitHub nao compartilha secrets nem
variables entre repositorios distintos. `infra` fica de fora: a pipeline dele
nao chama o Sonar (sem codigo de aplicacao para analisar).

O token nunca e impresso. Uso:

    python tools/sonar_setup.py --check     # so verifica, nao grava nada
    python tools/sonar_setup.py
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "tools" / ".sonar.env"
SONAR_API = "https://sonarcloud.io/api"

# pasta local -> repositorio GitHub. `infra` de proposito fora: sem SonarCloud.
REPOS = {
    "services/api-gateway": "sv-api-gateway",
    "services/auth-service": "sv-auth-backend",
    "services/bets-service": "sv-bets-backend",
    "services/stats-service": "sv-stats-backend",
    "services/telegram-integration": "sv-telegram-integration-backend",
    "apps/web": "sv-frontend",
}
GH = pathlib.Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GitHub CLI" / "gh.exe"


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.exit(f"ERRO: {ENV_FILE} nao existe. Copie de tools/.sonar.env.example.")
    env = {}
    with io.open(ENV_FILE, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    missing = [k for k in ("SONAR_TOKEN", "SONAR_ORGANIZATION") if not env.get(k)]
    if missing:
        sys.exit(f"ERRO: faltam valores em {ENV_FILE}: {', '.join(missing)}")
    if env["SONAR_TOKEN"].startswith("cole-o-token"):
        sys.exit(f"ERRO: SONAR_TOKEN em {ENV_FILE} ainda e o placeholder.")
    return env


def sonar_get(token: str, path: str) -> dict:
    """A API do SonarCloud autentica com o token como usuario e senha vazia."""
    auth = base64.b64encode(f"{token}:".encode()).decode()
    request = urllib.request.Request(
        f"{SONAR_API}{path}",
        headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 401:
            sys.exit("ERRO: SonarCloud recusou o token (401). Gere outro em "
                     "https://sonarcloud.io/account/security e atualize o .sonar.env.")
        sys.exit(f"ERRO SonarCloud {error.code} em {path}: {error.reason}")
    except urllib.error.URLError as error:
        sys.exit(f"ERRO de rede ao falar com o SonarCloud: {error.reason}")


def check_sonar(env: dict[str, str]) -> list[str]:
    """Confere organizacao e projetos. Devolve as chaves de projeto faltantes."""
    org = env["SONAR_ORGANIZATION"]
    found = sonar_get(env["SONAR_TOKEN"], f"/organizations/search?organizations={org}")
    if not found.get("organizations"):
        sys.exit(f"ERRO: organizacao '{org}' nao encontrada com este token.")
    print(f"OK   organizacao '{org}' ({found['organizations'][0].get('name')})")

    listed = sonar_get(env["SONAR_TOKEN"], f"/projects/search?organization={org}&ps=100")
    have = {p["key"] for p in listed.get("components", [])}
    missing = []
    for repo in REPOS.values():
        key = f"{org}_{repo}"
        mark = "OK  " if key in have else "FALTA"
        print(f"{mark} projeto {key}")
        if key not in have:
            missing.append(key)
    return missing


def gh(args: list[str], token: str | None = None) -> subprocess.CompletedProcess:
    environ = dict(os.environ)
    if token:
        environ["GH_TOKEN"] = token
    return subprocess.run([str(GH), *args], capture_output=True, text=True, env=environ)


def github_token() -> str:
    """GH_TOKEN do ambiente; senao, a credencial que o git ja usa para github.com.

    `gh auth login --with-token` recusa essa credencial por falta do escopo
    read:org, mas GH_TOKEN pula essa validacao e `repo` basta aqui.
    """
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


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="so verifica organizacao/projetos/segredos, nao grava")
    args = parser.parse_args()

    if not GH.exists():
        sys.exit(f"ERRO: gh nao encontrado em {GH}. Instale com: winget install GitHub.cli")

    env = load_env()
    missing = check_sonar(env)
    if missing and not args.check:
        sys.exit(
            "\nERRO: crie estes projetos no SonarCloud antes de distribuir a credencial:\n  "
            + "\n  ".join(missing)
            + "\n(Analyze new project, importando o repositorio correspondente do GitHub.)"
        )

    token = github_token()
    print()
    for folder, repo in REPOS.items():
        slug = f"eimmig/{repo}"
        if args.check:
            secrets = gh(["secret", "list", "--repo", slug], token).stdout
            variables = gh(["variable", "list", "--repo", slug], token).stdout
            print(f"{folder:34s} SONAR_TOKEN={'sim' if 'SONAR_TOKEN' in secrets else 'NAO':3s}  "
                  f"SONAR_ORGANIZATION={'sim' if 'SONAR_ORGANIZATION' in variables else 'NAO'}")
            continue

        one = gh(["secret", "set", "SONAR_TOKEN", "--repo", slug,
                  "--body", env["SONAR_TOKEN"]], token)
        two = gh(["variable", "set", "SONAR_ORGANIZATION", "--repo", slug,
                  "--body", env["SONAR_ORGANIZATION"]], token)
        status = "ok" if one.returncode == 0 and two.returncode == 0 else "FALHOU"
        detail = "" if status == "ok" else f"  {(one.stderr or two.stderr).strip()[:120]}"
        print(f"{folder:34s} secret + variable: {status}{detail}")


if __name__ == "__main__":
    main()
