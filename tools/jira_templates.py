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
    goal          1-2 frases: o que esta story entrega. Opcional; cai para as
                  primeiras frases de `description`.
    description   contexto completo
    scope         lista de itens que entram no escopo. Opcional.
    dependencies  lista de ids no mesmo harness
    plan_review   texto do Plan Reviewer. NAO aparece na story quando preenchido —
                  os achados ja foram absorvidos pelas subtarefas, repeti-los seria
                  a mesma decisao contada duas vezes. Vazio faz a story nascer com
                  o aviso de "Plan Review pendente".
    evidence      evidencia de conclusao (vira comentario). Texto simples ou,
                  preferido, objeto legivel:
                      {"resumo": "uma frase",
                       "secoes": [{"titulo": ..., "itens": [...]}, ...]}
                  O comentario sai com resumo e um subtitulo por secao — nao como
                  um paragrafo unico concatenado.
    subtasks      lista de subtasks

Campos lidos de cada subtask:
    name          titulo curto (vira o summary da sub-task)
    detail        1-2 frases explicando o passo. Opcional.
    checklist     lista de passos verificaveis. Opcional.
    validation    como validar o passo. Opcional.
    owner         "agente" (default) ou "usuario" — sinaliza acao manual.

Em qualquer campo de texto, trecho entre `crases` vira codigo na issue.
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


def rich(value: str) -> list[dict]:
    """Quebra `crase` em nos de codigo — nome de arquivo, comando, id.

    Sem isto, `feature_list.json` e `git checkout -b` saem como prosa e o passo
    vira um paragrafo cinza onde nada se destaca.
    """
    partes = str(value).split("`")
    return [
        text(parte, ["code"] if i % 2 else None)
        for i, parte in enumerate(partes)
        if parte
    ]


def paragraph(*nodes) -> dict:
    """Aceita str (crases viram codigo) ou nos ADF ja montados."""
    content: list[dict] = []
    for node in nodes:
        content += rich(node) if isinstance(node, str) else [node]
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


def story_summary(harness_label: str, feature: dict) -> str:
    return _clip(f"[{harness_label}] {feature['name']}")


def subtask_summary(subtask: dict) -> str:
    return _clip(subtask["name"])


# --- templates ------------------------------------------------------------------


def _texto(titulo: str, valor) -> list[dict]:
    """Seção de texto corrido. Vazia vira lista vazia — não gera título órfão."""
    conteudo = (valor or "").strip() if isinstance(valor, str) else ""
    return [heading(titulo), paragraph(conteudo)] if conteudo else []


def _lista(titulo: str, itens, numerada: bool = False) -> list[dict]:
    """Seção de lista. Vazia vira lista vazia — não gera título órfão."""
    itens = [i for i in (itens or []) if i]
    if not itens:
        return []
    return [heading(titulo), (ordered_list if numerada else bullet_list)(itens)]


def _passos_section(subtasks: list[dict]) -> list[dict]:
    """As subtarefas já criadas, com a chave do Jira ao lado quando existir."""
    if not subtasks:
        return []
    return [
        heading("Passos"),
        ordered_list(
            [
                paragraph(
                    text(s["name"]),
                    text(f"  ({s['jira']})" if s.get("jira") else "", ["code"]),
                )
                for s in subtasks
            ]
        ),
    ]


def _review_section(feature: dict) -> list[dict]:
    """Só o aviso de Plan Review pendente. Revisão feita não aparece na issue.

    Os achados do Plan Reviewer já foram absorvidos pelas subtarefas — repeti-los
    na descrição seria a mesma decisão contada duas vezes, e a segunda cópia
    envelhece calada. O texto integral continua em `plan_review`, no
    `feature_list.json`, que é onde a rastreabilidade vive.
    """
    if (feature.get("plan_review") or "").strip():
        return []
    return [
        panel(
            "warning",
            "Plan Review pendente — rodar o Plan Reviewer antes de mover esta "
            "story para In Progress (CLAUDE.md da raiz, passo 9).",
        )
    ]


def story_description(harness: str, feature: dict) -> dict:
    goal = feature.get("goal") or _first_sentences(feature.get("description", ""))
    nodes: list[dict] = [panel("info", paragraph(text(goal, ["strong"])))]

    nodes += _lista("O que entra", feature.get("scope"))
    nodes += _passos_section(feature.get("subtasks") or [])

    deps = feature.get("dependencies") or []
    nodes += _lista("Depende de", [f"{harness} :: {dep}" for dep in deps])

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

    Carrega um hash do proprio conteudo: rodar o sync de novo nao duplica o
    comentario, mas uma evidencia editada no harness gera um comentario novo em
    vez de a issue ficar com a versao velha.
    """
    import hashlib
    import json

    evidence = feature.get("evidence") or ""
    canonico = (
        evidence
        if isinstance(evidence, str)
        else json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    )
    digest = hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:8]
    return f"harness-evidence:{harness}:{feature['id']}:{digest}"


def _evidence_body(evidence) -> list[dict]:
    """Corpo do comentário de evidência, em blocos legíveis.

    Evidência costuma ter perguntas distintas — o que foi entregue, como isso foi
    verificado, o que fugiu do plano. Concatenar tudo num parágrafo único produz
    um bloco que ninguém lê no board, então cada seção vira um subtítulo com sua
    lista, no mesmo formato das descrições das tarefas.
    """
    if isinstance(evidence, str):
        blocos = evidence.split("\n\n")
        return [paragraph(bloco.strip()) for bloco in blocos if bloco.strip()]

    nodes: list[dict] = []
    resumo = (evidence.get("resumo") or "").strip()
    if resumo:
        nodes.append(paragraph(resumo))
    for secao in evidence.get("secoes") or []:
        titulo = (secao.get("titulo") or "").strip()
        itens = [item for item in (secao.get("itens") or []) if str(item).strip()]
        if titulo:
            nodes.append(heading(titulo, 4))
        if itens:
            nodes.append(bullet_list(itens))
    return nodes


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
        *_evidence_body(feature.get("evidence") or ""),
        rule(),
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

    nodes += _lista("Passos", subtask.get("checklist"), numerada=True)
    nodes += _texto("Como validar", subtask.get("validation"))

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
