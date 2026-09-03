#!/usr/bin/env python3
"""Cria (ou atualiza) a story do Jira que espelha uma feature do harness.

O `feature_list.json` de cada harness continua sendo a fonte da verdade: status,
dependencias, WIP e `plan_review` sao decididos la. O Jira e um espelho, criado a
partir do JSON para rastreabilidade — nada volta do Jira para o harness, exceto a
chave da issue, gravada no campo `jira` da feature para fechar o vinculo.

A branch de trabalho e nomeada pela chave (`feature/SV-12`), entao rode este script
DEPOIS de preencher `plan_review` e ANTES de criar a branch. Como a chave fica
gravada no JSON, sessao sem rede continua sabendo o nome da branch.

Uso:
    python tools/jira_story.py --harness infra --feature feat-001 --dry-run
    python tools/jira_story.py --harness infra --feature feat-001

Credenciais (nunca commitadas — esta pasta raiz nao e um repositorio Git):
    JIRA_URL         https://<seu-site>.atlassian.net
    JIRA_EMAIL       e-mail da conta Atlassian
    JIRA_API_TOKEN   token gerado em id.atlassian.com/manage-profile/security/api-tokens
    JIRA_PROJECT     chave do projeto (ex.: SV)

Opcionais, para Jira em outro idioma (o nome do tipo de issue e localizado):
    JIRA_STORY_TYPE    default "Story"    (em pt-BR costuma ser "Historia")
    JIRA_SUBTASK_TYPE  default "Sub-task" (em pt-BR costuma ser "Subtarefa")

Podem vir do ambiente ou de tools/.jira.env (formato CHAVE=valor).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import jira_templates as tpl  # noqa: E402  (depende do sys.path acima)

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "tools" / ".jira.env"
REQUIRED_ENV = ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT")
ISSUE_API = "/rest/api/3/issue"


def load_env() -> dict[str, str]:
    """Ambiente primeiro; tools/.jira.env preenche o que faltar."""
    env = {key: os.environ[key] for key in REQUIRED_ENV if os.environ.get(key)}
    if ENV_FILE.exists():
        with io.open(ENV_FILE, encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env.setdefault(key.strip(), value.strip())
    return env


def save(path: pathlib.Path, data: dict) -> None:
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def append_changelog_lines(harness: str, base_url: str, entries: list[tuple[str, str]]) -> None:
    """Acrescenta uma linha `- [CHAVE](url) - titulo` em [Unreleased] por entrada nova.

    Cada entrada e (chave-jira, titulo) — story ou subtask, escrito no exato momento
    em que a issue e criada, para ninguem precisar lembrar do formato depois. So a
    linha e apensada; nada mais no arquivo e reescrito. Idempotente: chave ja
    presente no arquivo e pulada (permite rodar de novo sem duplicar).
    """
    path = ROOT / harness / "CHANGELOG.md"
    if not path.exists() or not entries:
        return
    text = path.read_text(encoding="utf-8")
    new_lines = [
        f"- [{key}]({base_url}/browse/{key}) - {title}"
        for key, title in entries
        if f"[{key}]" not in text
    ]
    if not new_lines:
        return

    marker = "## [Unreleased]"
    idx = text.find(marker)
    if idx == -1:
        return
    section_start = idx + len(marker)
    next_heading = text.find("\n## ", section_start)
    insert_at = len(text) if next_heading == -1 else next_heading
    existing = text[:insert_at]  # marcador + linhas ja presentes na secao
    rest = text[insert_at:]  # proxima secao (ou vazio, se [Unreleased] for a ultima)
    text = existing.rstrip("\n") + "\n" + "\n".join(new_lines) + (
        "\n\n" + rest.lstrip("\n") if rest.strip() else "\n"
    )
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def load_feature(harness: str, feature_id: str) -> tuple[pathlib.Path, dict, dict]:
    path = ROOT / harness / "feature_list.json"
    if not path.exists():
        sys.exit(f"ERRO: {path} nao existe. Harness invalido?")
    with io.open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    for feature in data["features"]:
        if feature["id"] == feature_id:
            return path, data, feature
    known = ", ".join(f["id"] for f in data["features"])
    sys.exit(f"ERRO: {feature_id} nao existe em {path}. Disponiveis: {known}")


# --- Jira REST ------------------------------------------------------------------


def jira_request(
    env: dict[str, str], method: str, path: str, payload: dict | None = None
) -> dict:
    url = env["JIRA_URL"].rstrip("/") + path
    token = base64.b64encode(
        f"{env['JIRA_EMAIL']}:{env['JIRA_API_TOKEN']}".encode()
    ).decode()
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        method=method,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        sys.exit(f"ERRO Jira {error.code} em {method} {path}:\n{detail}")
    except urllib.error.URLError as error:
        sys.exit(f"ERRO de rede ao falar com o Jira: {error.reason}")


def jira_get(env: dict[str, str], path: str) -> dict:
    return jira_request(env, "GET", path)


def require_env() -> dict[str, str]:
    env = load_env()
    missing = [key for key in REQUIRED_ENV if not env.get(key)]
    if missing:
        sys.exit(
            "ERRO: faltam credenciais: "
            + ", ".join(missing)
            + f"\nDefina no ambiente ou em {ENV_FILE}. Ver o cabecalho deste script."
        )
    return env


"""Ciclo de vida da story e das sub-tasks no board.

O board reproduz o Kanban do TCC 1 (ver docs/REQUIREMENTS.md, "Metodo de trabalho"):
Opcoes -> Selecionado -> Em Execucao -> Verificacao -> Entregue, aqui como Backlog ->
To Do -> In Progress -> Review -> Done.

Os cinco status sao DERIVADOS do feature_list.json — nenhum campo novo, nenhuma
decisao tomada aqui. O ciclo combinado da story com as subtasks:

    feature not-started ................ story e subtasks em Backlog
    feature in-progress,
      nenhuma subtask iniciada ......... story e subtasks em To Do
      alguma subtask iniciada .......... story em In Progress
                                         subtask por status: not-started -> To Do,
                                         in-progress -> In Progress, done -> Done
      todas as subtasks done ........... story em Review
    feature done ....................... story e subtasks em Done

Review e o estado "codigo pronto, falta provar": a story fica la ate a suite planejada
ter rodado — unitarios, integracao e E2E, os que se aplicarem aquele harness — e a
Definicao de Pronto daquele CLAUDE.md estar satisfeita (evidence preenchida). E' isso
que autoriza a feature a virar `done` no JSON, e so entao a story sai de Review.
"""
BACKLOG, TODO, IN_PROGRESS, REVIEW, DONE = (
    "Backlog", "To Do", "In Progress", "Review", "Done"
)
SUBTASK_STATUS = {
    "not-started": TODO,
    "in-progress": IN_PROGRESS,
    "done": DONE,
}


def story_status(feature: dict) -> str:
    status = feature.get("status")
    if status == "done":
        return DONE
    if status != "in-progress":
        return BACKLOG

    subtasks = feature.get("subtasks") or []
    if not subtasks:
        return IN_PROGRESS
    if all(s.get("status") == "done" for s in subtasks):
        return REVIEW
    if any(s.get("status") in ("in-progress", "done") for s in subtasks):
        return IN_PROGRESS
    return TODO  # selecionada, nenhuma subtarefa comecou


def subtask_status(feature: dict, subtask: dict) -> str:
    if feature.get("status") == "not-started":
        return BACKLOG
    return SUBTASK_STATUS.get(subtask.get("status"), TODO)


def transition_issue(env, key: str, target: str) -> str:
    """Move uma issue para `target`. Devolve o que aconteceu, para o log."""
    current = jira_get(env, f"/rest/api/3/issue/{key}?fields=status")["fields"]["status"]["name"]
    if current == target:
        return f"ja em {target}"

    available = jira_get(env, f"/rest/api/3/issue/{key}/transitions")["transitions"]
    match = next((t for t in available if t["to"]["name"] == target), None)
    if not match:
        options = ", ".join(t["to"]["name"] for t in available)
        return f"sem transicao para '{target}' (disponiveis: {options})"

    jira_request(env, "POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": match["id"]}})
    return f"{current} -> {target}"


def adf_text(node) -> str:
    """Achata um documento ADF em texto puro, para procurar marcadores."""
    if isinstance(node, dict):
        return node.get("text", "") + "".join(adf_text(c) for c in node.get("content", []))
    if isinstance(node, list):
        return "".join(adf_text(c) for c in node)
    return ""


def post_evidence(env, harness: str, feature: dict) -> str:
    """Publica a evidencia de conclusao como comentario. Idempotente.

    O rodape do comentario carrega um marcador com hash do texto: rodar de novo
    nao duplica, mas evidencia editada no harness vira um comentario novo — o
    historico de comentarios preserva as duas versoes, que e o comportamento
    desejado num registro de rastreabilidade.
    """
    evidence = feature.get("evidence") or ""
    empty = not evidence.strip() if isinstance(evidence, str) else not evidence
    if empty:
        return "sem evidence preenchida — nada publicado"

    key = feature["jira"]
    marker = tpl.evidence_marker(harness, feature)
    existing = jira_get(env, f"/rest/api/3/issue/{key}/comment?maxResults=100")
    for comment in existing.get("comments", []):
        if marker in adf_text(comment.get("body")):
            return "evidencia ja comentada (mesmo conteudo)"

    stale = sum(
        1
        for c in existing.get("comments", [])
        if f"harness-evidence:{harness}:{feature['id']}:" in adf_text(c.get("body"))
    )
    jira_request(
        env, "POST", f"/rest/api/3/issue/{key}/comment",
        {"body": tpl.evidence_comment(harness, feature)},
    )
    return "evidencia comentada" + (f" (versao {stale + 1} — texto mudou no harness)" if stale else "")


def sync_status(env, harness: str, feature, subtasks) -> None:
    target = story_status(feature)
    print(f"Story {feature['jira']}: {transition_issue(env, feature['jira'], target)}")
    if target == REVIEW:
        print("    (Review: rodar a suite de testes planejada e preencher evidence "
              "antes de marcar a feature done no feature_list.json)")
    if feature.get("evidence"):
        print(f"    {post_evidence(env, harness, feature)}")
    for subtask in subtasks:
        key = subtask.get("jira")
        if not key:
            print(f"  (pulada) {subtask['id']} ainda nao tem sub-task no Jira")
            continue
        moved = transition_issue(env, key, subtask_status(feature, subtask))
        print(f"  {key:10s} {subtask['id']}  {moved}")


def rewrite_issues(env, feature, subtasks, story_payload, subtask_payload, path, data) -> None:
    """--update: reescreve summary/description da story e das sub-tasks.

    So toca esses dois campos de proposito: status, sprint, assignee e estimativa
    sao decididos no Jira (ou no harness, no caso de status) e nao devem ser
    sobrescritos por um re-render de template.

    Subtask sem chave e CRIADA aqui. E' o caso da subtarefa descoberta durante a
    implementacao, que o CLAUDE.md da raiz manda acrescentar ao array em vez de
    deixar virar trabalho invisivel — sem isso, ela existiria so no JSON.
    """
    story_key = feature["jira"]
    only = ("summary", "description")

    def put(key: str, fields: dict) -> None:
        jira_request(env, "PUT", f"/rest/api/3/issue/{key}", {"fields": {k: fields[k] for k in only}})

    put(story_key, story_payload["fields"])
    base = env["JIRA_URL"].rstrip("/")
    print(f"Story atualizada: {story_key}  {base}/browse/{story_key}")

    new_entries: list[tuple[str, str]] = []
    for subtask in subtasks:
        key = subtask.get("jira")
        if key:
            put(key, subtask_payload(subtask, story_key)["fields"])
            note = ""
        else:
            key = jira_request(
                env, "POST", ISSUE_API, subtask_payload(subtask, story_key)
            )["key"]
            subtask["jira"] = key
            save(path, data)  # grava uma a uma: falha no meio nao deixa issue orfa
            new_entries.append((key, subtask["name"]))
            note = "  (nova)"
        print(f"  {key:10s} {subtask['id']}  {tpl.subtask_summary(subtask)[:52]}{note}")

    if new_entries:
        harness = str(path.parent.relative_to(ROOT))
        append_changelog_lines(harness, base, new_entries)
        print(f"Linhas do CHANGELOG.md acrescentadas para {len(new_entries)} subtarefa(s) nova(s)")


def main() -> None:
    # O console do Windows abre em cp1252 e quebra ao imprimir acento vindo do
    # feature_list.json (que e UTF-8). Vale para o dry-run e para os resumos.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", required=True, help="ex.: infra, services/auth-service")
    parser.add_argument("--feature", required=True, help="ex.: feat-001")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra o payload e nao chama o Jira (nao exige credencial)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="reescreve titulo e descricao da story e das sub-tasks ja criadas "
        "(usa as chaves gravadas no feature_list.json; nao cria issue nova)",
    )
    parser.add_argument(
        "--sync-status",
        action="store_true",
        help="move story e sub-tasks para o status derivado do harness "
        "(Backlog -> To Do -> In Progress -> Review -> Done; ver o ciclo documentado "
        "acima de story_status)",
    )
    args = parser.parse_args()

    path, data, feature = load_feature(args.harness, args.feature)
    existing = feature.get("jira")
    mirroring = args.update or args.sync_status

    if mirroring and not existing:
        sys.exit(f"{args.feature} ainda nao tem story no Jira — rode sem flags para criar.")

    if existing and not args.dry_run and not mirroring:
        sys.exit(
            f"{args.feature} ja tem a story {existing}. "
            "Use --update para reescrever titulo/descricao, --sync-status para mover "
            "as issues, ou apague o campo 'jira' se realmente quiser criar outra."
        )

    env = {} if args.dry_run else require_env()

    project = env.get("JIRA_PROJECT", "<JIRA_PROJECT>")
    story_type = env.get("JIRA_STORY_TYPE", "Story")
    subtask_type = env.get("JIRA_SUBTASK_TYPE", "Sub-task")
    label_harness = args.harness.strip("/").replace("/", "-")
    subtasks = feature.get("subtasks") or []

    story_payload = {
        "fields": {
            "project": {"key": project},
            "summary": tpl.story_summary(label_harness, feature),
            "issuetype": {"name": story_type},
            "labels": [label_harness, feature["id"]],
            "description": tpl.story_description(args.harness, feature),
        }
    }

    def subtask_payload(subtask: dict, parent_key: str) -> dict:
        summary = tpl.subtask_summary(subtask)
        return {
            "fields": {
                "project": {"key": project},
                "parent": {"key": parent_key},
                "summary": summary,
                "issuetype": {"name": subtask_type},
                "description": tpl.subtask_description(args.harness, feature, subtask),
            }
        }

    if args.dry_run:
        print(json.dumps(story_payload, indent=2, ensure_ascii=False))
        for subtask in subtasks:
            print(json.dumps(subtask_payload(subtask, "<CHAVE-DA-STORY>"), indent=2, ensure_ascii=False))
        print(
            f"\n(dry-run: nada enviado — 1 story + {len(subtasks)} subtarefas)",
            file=sys.stderr,
        )
        return

    if args.update:
        rewrite_issues(env, feature, subtasks, story_payload, subtask_payload, path, data)
    if args.sync_status:
        sync_status(env, args.harness, feature, subtasks)
    if mirroring:
        return

    created = jira_request(env, "POST", ISSUE_API, story_payload)
    story_key = created["key"]
    feature["jira"] = story_key
    save(path, data)  # grava antes das subtarefas: se uma falhar, a story nao vira orfa

    for subtask in subtasks:
        result = jira_request(
            env, "POST", "/rest/api/3/issue", subtask_payload(subtask, story_key)
        )
        subtask["jira"] = result["key"]
        save(path, data)

    base = env["JIRA_URL"].rstrip("/")
    entries = [(story_key, feature["name"])] + [
        (subtask["jira"], subtask["name"]) for subtask in subtasks
    ]
    append_changelog_lines(args.harness, base, entries)

    print(f"Story criada: {story_key}  {base}/browse/{story_key}")
    for subtask in subtasks:
        print(f"  {subtask['jira']:10s} {subtask['id']}  {subtask['name'][:60]}")
    print(f"\nChaves gravadas em {path.relative_to(ROOT)} :: {feature['id']}")
    print(f"Linhas do CHANGELOG.md acrescentadas em {args.harness}/CHANGELOG.md")
    print()
    print(f"Proximo passo, dentro de {args.harness}/:")
    print("  git checkout develop")
    print(f"  git checkout -b feature/{story_key}          # branch da story")
    first = subtasks[0]["jira"] if subtasks else "<chave-da-subtarefa>"
    print(f"  git checkout -b subtask/{first}         # a partir da branch da story")
    print()
    print("  # ao terminar a subtarefa (init.sh NAO e exigido aqui):")
    print(f"  git checkout feature/{story_key} && git merge --no-ff subtask/{first}")
    print()
    print("  # ao terminar a feature inteira, na branch da story:")
    print("  #   todas as subtasks done + CHANGELOG.md + init.sh + Delivery Reviewer")
    print(f"  git checkout develop && git merge --no-ff feature/{story_key}")


if __name__ == "__main__":
    main()
