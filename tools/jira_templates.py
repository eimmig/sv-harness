#!/usr/bin/env python3
"""Templates de story e sub-task do Jira, em Atlassian Document Format (ADF).

Separado de `jira_story.py` de proposito: aquele script cuida de ler o harness e
falar com a API; este cuida so de *como a issue se parece* para quem abre o Jira.
Mudar o visual das issues nao deveria exigir mexer na logica de rede.

Principio: a issue e escrita para uma pessoa lendo no board — titulo curto, objetivo
na primeira linha, passos verificaveis, e o material tecnico longo (plan review,
convencao de branch) recolhido em blocos `expand` para nao poluir a leitura.

A fonte da verdade continua sendo o `feature_list.json` do harness. Nada aqui inventa
conteudo: os templates so formatam os campos que a feature/subtask ja tem.

Campos lidos de cada feature:
    name          titulo curto (vira o summary da story)
    goal          1-2 frases: o que esta story entrega. Opcional; cai para description.
    description   contexto completo
    scope         lista de itens que entram no escopo. Opcional.
    dependencies  lista de ids no mesmo harness
    plan_review   texto do Plan Reviewer (recolhido num expand)
    subtasks      lista de subtasks

Campos lidos de cada subtask:
    name          titulo curto (vira o summary da sub-task)
    detail        1-2 frases explicando o passo. Opcional.
    checklist     lista de passos verificaveis. Opcional.
    owner         "agente" (default) ou "usuario" — sinaliza acao manual.
"""

from __future__ import annotations

# --- nos ADF basicos ------------------------------------------------------------


def text(value: str, marks: list[str] | None = None) -> dict:
    node: dict = {"type": "text", "text": value}
    if marks:
        node["marks"] = [{"type": mark} for mark in marks]
    return node


def link(value: str, href: str) -> dict:
    return {
        "type": "text",
        "text": value,
        "marks": [{"type": "link", "attrs": {"href": href}}],
    }


def paragraph(*nodes) -> dict:
    """Aceita str (vira texto simples) ou nos ADF ja montados."""
    content = [text(n) if isinstance(n, str) else n for n in nodes]
    return {"type": "paragraph", "content": content}


def heading(value: str, level: int = 3) -> dict:
    return {"type": "heading", "attrs": {"level": level}, "content": [text(value)]}


def bullet_list(items: list) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [item if isinstance(item, dict) else paragraph(item)],
            }
            for item in items
        ],
    }


def ordered_list(items: list) -> dict:
    return {
        "type": "orderedList",
        "content": [
            {
                "type": "listItem",
                "content": [item if isinstance(item, dict) else paragraph(item)],
            }
            for item in items
        ],
    }


def panel(kind: str, *nodes) -> dict:
    """kind: info | note | success | warning | error."""
    return {
        "type": "panel",
        "attrs": {"panelType": kind},
        "content": [n if isinstance(n, dict) else paragraph(n) for n in nodes],
    }


def expand(title: str, *nodes) -> dict:
    """Bloco recolhivel — usado para o material tecnico longo."""
    return {
        "type": "expand",
        "attrs": {"title": title},
        "content": [n if isinstance(n, dict) else paragraph(n) for n in nodes],
    }


def code_block(value: str, language: str = "bash") -> dict:
    return {
        "type": "codeBlock",
        "attrs": {"language": language},
        "content": [{"type": "text", "text": value}],
    }


def rule() -> dict:
    return {"type": "rule"}


def doc(*nodes) -> dict:
    return {"type": "doc", "version": 1, "content": list(nodes)}


# --- helpers --------------------------------------------------------------------

MAX_SUMMARY = 240  # o Jira rejeita summary acima de 255


def _clip(value: str, limit: int = MAX_SUMMARY) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def _first_sentences(value: str, count: int = 2) -> str:
    """Fallback de `goal`: as primeiras frases da description."""
    parts = " ".join(value.split()).split(". ")
    return _clip(". ".join(parts[:count]).rstrip(".") + ".", 400)


def _split_review(review: str) -> tuple[str, list[str]]:
    """Separa o veredito dos achados no texto do Plan Reviewer.

    Formato produzido pelas sessoes: "<data>, Plan Reviewer ... Veredito: X.
    Achados corrigidos ...: (BLOCKER) ...; (MAJOR) ...;"
    Sem regex fragil: quebra pelos marcadores de severidade, que sao a unica
    convencao estavel do texto. Se nao encontrar nenhum, devolve o texto inteiro.
    """
    flat = " ".join(review.split())
    verdict = ""
    for marker in ("Veredito:", "Verdict:"):
        if marker in flat:
            verdict = flat.split(marker, 1)[1].split(".", 1)[0].strip()
            break

    findings: list[str] = []
    for severity in ("(BLOCKER)", "(MAJOR)", "(MINOR)"):
        chunk = flat
        while severity in chunk:
            _, _, rest = chunk.partition(severity)
            end = len(rest)
            for stop in ("; (BLOCKER)", "; (MAJOR)", "; (MINOR)"):
                if stop in rest:
                    end = min(end, rest.index(stop))
            findings.append(f"{severity[1:-1]} — {rest[:end].strip().rstrip(';')}")
            chunk = rest
    return verdict, findings


def story_summary(harness_label: str, feature: dict) -> str:
    return _clip(f"[{harness_label}] {feature['name']}")


def subtask_summary(subtask: dict) -> str:
    return _clip(subtask["name"])


# --- templates ------------------------------------------------------------------


def _review_section(feature: dict) -> list[dict]:
    """Veredito e achados do Plan Reviewer; texto completo recolhido."""
    review = (feature.get("plan_review") or "").strip()
    if not review:
        return [
            panel(
                "warning",
                "Plan Review pendente — rodar o Plan Reviewer antes de mover esta "
                "story para In Progress (CLAUDE.md da raiz, passo 9).",
            )
        ]

    verdict, findings = _split_review(review)
    nodes = [heading("Revisão do plano")]
    if verdict:
        nodes.append(
            panel(
                "success" if verdict.upper().startswith("READY") else "note",
                paragraph(text("Veredito: ", ["strong"]), text(verdict)),
            )
        )
    if findings:
        nodes.append(paragraph("Corrigido no plano antes de escrever qualquer código:"))
        nodes.append(bullet_list(findings))
    nodes.append(expand("Texto completo da revisão", paragraph(review)))
    return nodes


def story_description(harness: str, feature: dict) -> dict:
    goal = feature.get("goal") or _first_sentences(feature.get("description", ""))
    nodes: list[dict] = [panel("info", paragraph(text(goal, ["strong"])))]

    scope = feature.get("scope") or []
    if scope:
        nodes += [heading("O que entra"), bullet_list(scope)]

    subtasks = feature.get("subtasks") or []
    if subtasks:
        nodes.append(heading("Passos"))
        nodes.append(
            ordered_list(
                [
                    paragraph(
                        text(s["name"]),
                        text(
                            f"  ({s['jira']})" if s.get("jira") else "",
                            ["code"],
                        ),
                    )
                    for s in subtasks
                ]
            )
        )

    deps = feature.get("dependencies") or []
    if deps:
        nodes += [
            heading("Depende de"),
            bullet_list([f"{harness} :: {dep}" for dep in deps]),
        ]

    nodes += _review_section(feature)

    nodes.append(heading("Definição de pronto"))
    nodes.append(
        bullet_list(
            [
                "Todas as subtarefas concluídas.",
                f"./init.sh de {harness} passando.",
                "Delivery Reviewer e Test Suite Auditor rodados.",
                "CHANGELOG.md com entrada em [Unreleased].",
                "Campo evidence preenchido no feature_list.json.",
            ]
        )
    )
    nodes.append(
        paragraph(
            text("A checklist normativa completa vive em "),
            text(f"{harness}/CLAUDE.md", ["code"]),
            text(" — esta lista é um resumo, não a fonte da verdade."),
        )
    )

    nodes.append(rule())
    nodes.append(
        expand(
            "Rastreabilidade e fluxo de branch",
            bullet_list(
                [
                    paragraph(
                        text("Fonte da verdade: "),
                        text(f"{harness}/feature_list.json :: {feature['id']}", ["code"]),
                    ),
                    paragraph(
                        text("Status no harness quando esta story foi criada: "),
                        text(feature.get("status", "?"), ["code"]),
                    ),
                    "Esta story é um espelho. Status, dependências e evidência são "
                    "decididos no harness, nunca aqui.",
                ]
            ),
            paragraph(text("Branches:", ["strong"])),
            code_block(
                "develop\n"
                f"  └── feature/{feature.get('jira') or '<chave-da-story>'}\n"
                "        ├── subtask/<chave-da-subtarefa>\n"
                "        └── ...\n\n"
                "# merge sobe um nível por vez, sempre --no-ff"
            ),
        )
    )
    return doc(*nodes)


def evidence_marker(harness: str, feature: dict) -> str:
    """Marcador estavel no rodape do comentario de evidencia.

    Carrega um hash do proprio texto: rodar o sync de novo nao duplica o
    comentario, mas uma evidencia editada no harness gera um comentario novo em
    vez de a issue ficar com a versao velha.
    """
    import hashlib

    digest = hashlib.sha256((feature.get("evidence") or "").encode("utf-8")).hexdigest()[:8]
    return f"harness-evidence:{harness}:{feature['id']}:{digest}"


def evidence_comment(harness: str, feature: dict) -> dict:
    """Comentario que registra na issue a evidencia de conclusao da feature."""
    return doc(
        panel(
            "success",
            paragraph(
                text("Evidência de conclusão", ["strong"]),
                text(" — registrada em "),
                text(f"{harness}/feature_list.json :: {feature['id']}", ["code"]),
                text(", campo "),
                text("evidence", ["code"]),
                text("."),
            ),
        ),
        paragraph(feature.get("evidence") or ""),
        paragraph(text(evidence_marker(harness, feature), ["code"])),
    )


def subtask_description(harness: str, feature: dict, subtask: dict) -> dict:
    owner = (subtask.get("owner") or "agente").lower()
    detail = subtask.get("detail") or subtask["name"]

    nodes: list[dict] = [panel("info", paragraph(text(detail, ["strong"])))]

    if owner == "usuario":
        nodes.append(
            panel(
                "warning",
                "Passo manual — depende de acesso a UI web (SonarCloud/GitHub). "
                "Não pode ser executado pelo agente.",
            )
        )

    checklist = subtask.get("checklist") or []
    if checklist:
        nodes += [heading("Passos"), ordered_list(checklist)]

    validation = subtask.get("validation")
    if validation:
        nodes += [heading("Como validar"), paragraph(validation)]

    nodes.append(rule())
    nodes.append(
        expand(
            "Rastreabilidade e gate de merge",
            bullet_list(
                [
                    paragraph(
                        text("Fonte da verdade: "),
                        text(
                            f"{harness}/feature_list.json :: {feature['id']} > "
                            f"subtasks > {subtask['id']}",
                            ["code"],
                        ),
                    ),
                    paragraph(
                        text("Branch: sai da branch da story ("),
                        text(f"feature/{feature.get('jira') or '<chave-da-story>'}", ["code"]),
                        text("), não de develop. Merge --no-ff de volta nela."),
                    ),
                    "Gate para mergear: pipeline de CI do PR passando (changelog, "
                    "i18n, build, testes). Não exige ./init.sh local nem as skills de "
                    "revisão — o gate completo roda uma vez, na story.",
                    "Esta subtarefa adiciona a própria linha em [Unreleased] do "
                    "CHANGELOG.md, no PR dela.",
                ]
            ),
        )
    )
    return doc(*nodes)
