# CLAUDE.md

Plataforma escalável para gestão de bankroll e análise estatística de apostas esportivas —
implementação de código do TCC 2 de Eduardo Mateus Immig (UTFPR), a partir da especificação
entregue no TCC 1. Arquitetura de microsserviços: Java/Spring Boot (auth, bets, stats),
Python (integração Telegram), Angular/TypeScript (web), PostgreSQL, RabbitMQ, Redis, Docker.

## Harness multinível — leia isto primeiro

Este projeto tem **dois níveis de harness — e não é um monorepo** (decisão de 2026-08-02, ver
`docs/DECISIONS-LOG.md`):

- **Este nível (raiz)**: invariantes que atravessam todos os serviços, backlog em nível de
  *epic* (uma linha por serviço em `feature_list.json`), e verificação agregada (`./init.sh`).
  **Esta pasta é um repositório Git próprio** (`sv-harness`, ver `docs/DECISIONS-LOG.md`
  2026-08-19 — reverte o "a raiz nunca vai para o GitHub" anterior), versionando **só** docs +
  harness: `CLAUDE.md`, `docs/`, `feature_list.json`, `progress.md`, `session-handoff.md`,
  `init.sh`, `tools/`. O `.gitignore` da raiz exclui `/services/`, `/infra/` e `/apps/` —
  aquelas pastas são repositórios independentes e **nunca** podem ser adicionadas aqui (git
  gravaria gitlink de submódulo órfão, apontando para SHA que ninguém consegue clonar).
- **Cada serviço** (`services/api-gateway/`, `services/auth-service/`, `services/bets-service/`,
  `services/stats-service/`, `services/telegram-integration/`, `apps/web/`) **e também `infra/`**
  (Docker Compose + teste de resiliência cross-service — sem serviço de aplicação próprio, mas
  com harness completo igual aos demais, ver `docs/DECISIONS-LOG.md` "Topologia"): tem seu
  próprio `CLAUDE.md`, `feature_list.json` granular, `init.sh` e `progress.md`, escopados àquela
  pasta — **e é seu próprio repositório Git independente, hospedado em seu próprio repo
  GitHub** (7 repositórios de código no total: 6 serviços + `infra/`; mais o `sv-harness` da
  raiz, que não contém código de aplicação). As pastas continuam aninhadas dentro
  desta árvore só por conveniência de trabalhar localmente com tudo à vista; git-wise, cada uma é
  isolada da raiz e das demais (não há um repositório "pai" enxergando todas — o repositório da
  raiz ignora `/services/`, `/infra/` e `/apps/`, então não enxerga nenhuma).

O Claude Code lê `CLAUDE.md` do diretório de trabalho atual **e** dos diretórios ancestrais —
trabalhar dentro de `services/bets-service/` carrega este arquivo *e* o `CLAUDE.md` daquele
serviço ao mesmo tempo. Quando estiver implementando uma feature específica de um serviço, o
`CLAUDE.md` daquele serviço tem prioridade sobre detalhes operacionais (comandos de build,
convenções de código); este arquivo tem prioridade sobre decisões de arquitetura cross-service.

A documentação de arquitetura e requisitos vive em um **vault Obsidian** em `docs/` — comece
por `docs/Index.md`. Não duplique conteúdo de arquitetura aqui neste arquivo; se um `CLAUDE.md`
de serviço e o vault divergirem, o vault é a fonte da verdade sobre o *quê/porquê*, e o
`CLAUDE.md` do serviço sobre o *como trabalhar*.

## Fluxo de início de sessão (Startup Workflow)

Antes de escrever código:

1. Confirme o diretório de trabalho (`pwd`).
2. Leia este arquivo por completo.
3. Leia `docs/Index.md` e, a partir dele: a visão geral em `docs/ARCHITECTURE.md`, a nota do
   serviço específico em `docs/services/`, e as convenções cross-service em
   `docs/CONVENTIONS.md`, `docs/TESTING.md`, `docs/API-CONTRACTS.md`,
   `docs/OBSERVABILITY-AND-CONFIG.md` e **`docs/AGENT-SKILLS.md`** — essas cinco notas existem
   justamente para que nenhuma sessão precise decidir de novo arquitetura interna, build tool,
   formato de erro, ou qual skill de agente usar em cada etapa.
4. Rode `./init.sh` na raiz para uma verificação agregada de ferramentas e do estado de cada
   sub-harness. Se a sessão for sobre um serviço específico, rode também o `init.sh` daquele
   serviço.
5. Leia `feature_list.json` da raiz para escolher **um epic** `not-started` cujas dependências
   já estejam `done` **e** cujo serviço (`harness`) não tenha outro epic `in-progress` neste
   momento — trabalho em paralelo entre serviços diferentes é permitido, ver "Regras de
   trabalho".
6. Entre na pasta do serviço daquele epic e leia o `feature_list.json` de lá para escolher a
   feature granular específica a trabalhar.
7. Leia o `progress.md` da raiz e, se existir trabalho recente naquele serviço, o `progress.md`
   do serviço também.
8. Dentro da pasta do serviço, revise os últimos commits (`git log --oneline -5`). A raiz
   também é um repositório (`sv-harness`), mas o histórico relevante para implementar uma
   feature é o do serviço — o da raiz só registra mudanças de docs/harness.
9. **Antes de escrever qualquer código**: rode o `Plan Reviewer` (claude-code-skills, Review
   Suite) contra o plano de implementação da feature escolhida — prioritário sobre simplesmente
   começar a codificar a partir da leitura do `feature_list.json`. Ver `docs/AGENT-SKILLS.md`
   para o mapeamento completo de skills por etapa (arquitetura, desenvolvimento, testes,
   validação). **Registre o resultado no campo `plan_review` daquela feature** antes de mudar o
   status para `in-progress` — ver "Regras de trabalho".

Se a verificação básica (`./init.sh`) estiver falhando, conserte isso antes de adicionar
qualquer escopo novo.

## Regras de trabalho

- **Skills de agente (Caveman + claude-code-skills) são prioritárias em toda etapa** — não uma
  opção entre outras, a ferramenta padrão para arquitetura, desenvolvimento, testes e validação.
  **Instaladas em 2026-08-02** (escopo `user`, ver `docs/DECISIONS-LOG.md`) — se uma sessão
  não as enxergar disponíveis, reinicie a sessão do Claude Code antes de assumir que precisam
  ser reinstaladas. Mapeamento completo (qual skill em qual etapa, e a ressalva de nunca deixar
  a Architecture Suite gerar decisão/diagrama paralelo a este vault) em `docs/AGENT-SKILLS.md`.
  **A análise dessas skills é sempre apresentada em português** ao usuário, mesmo quando o
  output contract da skill é documentado em inglês — ver `docs/AGENT-SKILLS.md` seção "Idioma
  das análises".
- **WIP máximo 1 por lane de serviço — paralelismo entre serviços é permitido (multi-agent)**:
  mesmo princípio do WIP máximo 1 usado no TCC 1 (ver `docs/REQUIREMENTS.md` seção "Método de
  trabalho"), aplicado por serviço em vez de globalmente, para permitir várias sessões/agentes
  trabalhando ao mesmo tempo — cada uma em um serviço diferente.
  - **Dentro de um mesmo serviço**: uma feature `in-progress` por vez no `feature_list.json`
    daquele serviço. Isso não muda.
  - **Entre serviços**: pode haver vários epics `in-progress` ao mesmo tempo na raiz — um por
    harness (`harness` em `feature_list.json`) — desde que as `dependencies` de cada epic já
    estejam `done`. `epic-001` e `epic-007` compartilham o harness `infra/` — como
    `epic-007` depende de `epic-004`/`epic-005` (bem mais à frente), na prática eles nunca
    disputam WIP entre si, mas nunca marque os dois `in-progress` ao mesmo tempo mesmo assim.
  - Antes de marcar um epic como `in-progress` em `feature_list.json` da raiz, releia o arquivo
    para confirmar que nenhum outro agente já reivindicou aquele epic (ou outro epic do mesmo
    serviço) nesse meio-tempo. Se a sua tentativa de salvar a reivindicação esbarrar num
    conflito (arquivo já mudou), outra sessão chegou primeiro — não sobrescreva; escolha outro
    epic elegível.
  - Nunca trabalhe em dois epics do mesmo serviço ao mesmo tempo em sessões paralelas.
- **Database per Service**: nunca compartilhe schema de banco entre serviços. Cada serviço
  Java tem seu próprio banco Postgres.
- **Consistência eventual é intencional**: o registro de uma aposta (síncrono) nunca deve
  esperar o processamento estatístico (assíncrono via RabbitMQ). Não "simplifique" isso
  tornando síncrono.
- **Contratos entre serviços mudam junto com a documentação**: o payload dos eventos
  `BetCreated`/`BetSettled` (produzidos por `bets-service`, consumidos por `stats-service`) é um
  contrato compartilhado — qualquer mudança neles atualiza as notas de ambos os serviços no
  vault no mesmo commit. Rotas de API, query params e nomes/valores de evento são sempre em
  inglês (ver `docs/API-CONTRACTS.md`); UI e mensagens de erro são sempre localizadas em
  `pt-BR`/`en-US`/`es`, os três sempre em sincronia (ver `docs/CONVENTIONS.md` seção
  "Internacionalização (i18n)") — não misturar as duas coisas.
- **Regras de negócio (RN01–RN09) são normativas, não sugestões**: implemente exatamente como
  descrito em `docs/REQUIREMENTS.md`.
- **Convenções (`docs/CONVENTIONS.md`, `docs/TESTING.md`, `docs/API-CONTRACTS.md`,
  `docs/OBSERVABILITY-AND-CONFIG.md`) também são normativas**: arquitetura hexagonal, Maven,
  formato de erro RFC 7807, meta de cobertura 80%, etc. já estão decididos — não escolha uma
  alternativa diferente por serviço ou por sessão. Se uma convenção parecer errada para uma
  situação específica, pare e peça confirmação ao usuário antes de desviar, e atualize a nota
  correspondente no mesmo commit.
- **Toda feature vira uma story no Jira — espelho, não fonte da verdade** (decisão de
  2026-08-03, reverte o "este projeto não usa Jira" anterior; ver `docs/DECISIONS-LOG.md`):
  depois de rodar o `Plan Reviewer` e preencher `plan_review`, crie a story com
  `python tools/jira_story.py --harness <pasta> --feature <id>`. O script lê o
  `feature_list.json` daquele harness, monta a story (contexto, dependências, análise do plan
  review, ponteiro para a Definição de Pronto) e grava a chave da issue de volta no campo `jira`
  da feature. **A direção é sempre harness → Jira, nunca o contrário**: status, dependências,
  WIP e evidência continuam sendo decididos no `feature_list.json`; o Jira existe para
  rastreabilidade e para a banca. Nenhuma sessão deve consultar o Jira para saber o que fazer,
  nem tratar divergência entre os dois como bug do harness — o JSON está certo por definição.
  **A branch de trabalho é nomeada pela chave do Jira** (`feature/SV-12`, não
  `feature/feat-001`), então a story precisa existir antes da branch — a ordem é: `Plan Reviewer`
  → `plan_review` preenchido → `jira_story.py` → `git checkout -b feature/<chave>`. Como a chave
  fica gravada no campo `jira` da feature, sessão sem rede continua sabendo o nome da branch.
  Credenciais em `tools/.jira.env` (ver `tools/.jira.env.example`), fora de qualquer um dos 7
  repositórios.
- **A issue do Jira é escrita para uma pessoa, não para um log**: o visual das issues vive em
  `tools/jira_templates.py` (ADF: painéis, listas, blocos recolhíveis), separado da lógica de
  rede em `tools/jira_story.py` — mudar como a issue se parece não deveria exigir mexer no
  script que fala com a API. Para isso a feature e cada subtask têm campos próprios de
  apresentação, todos opcionais e todos preenchidos a partir do que já foi decidido, nunca
  inventados: na feature, `goal` (1–2 frases sobre o que ela entrega) e `scope` (o que entra);
  na subtask, `detail` (por que este passo existe), `checklist` (passos verificáveis),
  `validation` (como saber que terminou) e `owner` (`agente` ou `usuario` — passo manual ganha
  aviso na issue). **`name` é título curto** (o que aparece no board); o texto longo vai nos
  outros campos, nunca no título. Trecho entre crases em qualquer campo de texto vira código
  inline na issue (`rich()`). `plan_review` **não aparece na story quando preenchido** — os
  achados já foram absorvidos pelas subtarefas, repeti-los seria a mesma decisão contada duas
  vezes; vazio, a story nasce com aviso de pendência. `evidence` aceita string (como antes) ou
  objeto `{"resumo": ..., "secoes": [{"titulo": ..., "itens": [...]}]}` — o comentário de
  evidência sai com um subtítulo por seção, não um parágrafo único concatenado; preferir o
  objeto para evidência com mais de uma pergunta respondida (o que foi feito / como foi
  verificado / o que divergiu do plano). Reescrever issues já criadas:
  `python tools/jira_story.py --harness <pasta> --feature <id> --update` — mexe só em
  `summary`/`description`, nunca em status, sprint ou responsável.
- **Ciclo de vida no board é derivado do JSON, nunca decidido no Jira**:
  `python tools/jira_story.py --harness <pasta> --feature <id> --sync-status` move a story e as
  sub-tasks. O board reproduz o Kanban do TCC 1 (`docs/REQUIREMENTS.md`, "Método de trabalho") e
  os cinco status saem do `feature_list.json` sem nenhum campo novo:

  | Estado no harness | Story | Sub-tasks |
  |---|---|---|
  | feature `not-started` | `Backlog` | `Backlog` |
  | feature `in-progress`, nenhuma subtask iniciada | `To Do` | `To Do` |
  | feature `in-progress`, alguma subtask iniciada | `In Progress` | por status: `not-started` → `To Do`, `in-progress` → `In Progress`, `done` → `Done` |
  | feature `in-progress`, **todas** as subtasks `done` | `Review` | `Done` |
  | feature `done` | `Done` | `Done` |

  **`Review` é o estado "código pronto, falta provar"**: a story fica lá até a suíte planejada
  ter rodado — unitários, integração e E2E, os que se aplicarem àquele harness (ver
  `docs/TESTING.md`) — e a Definição de Pronto daquele `CLAUDE.md` estar satisfeita, com
  `evidence` preenchida. É isso que autoriza a feature a virar `done` no JSON; só então a story
  sai de `Review`. Rode o `--sync-status` **depois** de mudar status no JSON, nunca antes: quem
  decide continua sendo o harness.

  O `--sync-status` também **publica a `evidence` como comentário na story**, assim que o campo
  estiver preenchido — é o registro, na própria issue, de que a Definição de Pronto foi cumprida.
  Idempotente: rodar de novo não duplica. Se a `evidence` for editada no harness, entra um
  comentário novo em vez de o antigo ser alterado, e o histórico da issue preserva as duas
  versões.
  - **O board é vivo — rode `--sync-status` a cada transição real de status, não só uma vez no
    fim da feature** (erro cometido em 2026-09-04, `feat-002` de `auth-service`: várias subtasks
    pularam direto de `not-started` para `done` no JSON sem nunca passar por `in-progress`, e o
    `--sync-status` só rodou no final — a story ficou presa em `To Do` durante todo o
    desenvolvimento em vez de refletir `In Progress`, e o Jira nunca mostrou nada em andamento).
    Prática correta: ao começar a trabalhar numa subtask, marque-a `in-progress` no
    `feature_list.json` e rode `--sync-status` **antes** de escrever qualquer código; ao terminar
    (código + testes + `/code-review`), marque `done` e rode `--sync-status` de novo — dois
    disparos por subtask, não um só no fim. O mesmo vale para a feature: ela vira `in-progress`
    no JSON (com `--sync-status` rodado) no momento em que a primeira subtask começa, não depois.
- **Feature se quebra em subtasks; a story do Jira as espelha como sub-tasks**: o campo
  `subtasks` de cada feature (irmão de `jira`) lista os passos de implementação, cada um com
  `id` (`feat-001.3`), `name`, `status` e `jira`. **Eles saem do `Plan Reviewer`** — o veredito
  daquela skill já entrega os menores passos ordenados por dependência; preencha `subtasks` a
  partir dele, no mesmo momento em que preenche `plan_review`, antes de criar a story. Subtask
  descoberta durante a implementação é acrescentada ao array (e criada no Jira) em vez de virar
  trabalho invisível.
  - **Uma branch por issue, aninhadas em quatro níveis**: `develop` → `feature/<chave-da-story>`
    → `subtask/<chave-da-subtask>`. Cada branch leva **o código da sua própria issue no Jira**
    (`feature/SV-12` para a story, `subtask/SV-13` para a subtask), e a branch da subtask sai da
    branch da story, não de `develop`. O merge sobe um nível de cada vez: subtask → story →
    `develop`, sempre `--no-ff`.
    > Por que a subtask tem prefixo próprio em vez de `feature/SV-12/SV-13`: o Git guarda ref
    > como arquivo em `.git/refs/heads/`, então `feature/SV-12` (arquivo) e `feature/SV-12/`
    > (diretório) não coexistem — o segundo `checkout -b` falha com `cannot lock ref`. O vínculo
    > pai/filho fica no `feature_list.json` e na própria sub-task do Jira, que já aponta para o
    > parent.
  - **Dois gates, de peso diferente**:
    - **Merge subtask → branch da story**: exige a **pipeline de CI do GitHub passando** naquele
      PR (changelog, i18n, build, testes). **Não** exige o `./init.sh` local nem as skills de
      revisão — um estado intermediário raramente passa no gate de cobertura (um
      `docker-compose.yml` sem o RabbitMQ ainda não sobe; `mvn verify` num serviço pela metade
      também não). O SonarCloud é pulado nesses PRs de propósito: cobertura parcial de uma
      feature em andamento reprovaria o quality gate sem indicar defeito real.
    - **Merge story → `develop`**: gate completo — `./init.sh`, `Delivery Reviewer`,
      `Test Suite Auditor` (+ `Persistence Auditor` nos serviços com banco), CI inteira incluindo
      SonarCloud, `evidence` preenchida e todas as `subtasks` `done`. Não afrouxe este.
  - **Cada subtask adiciona a própria linha no `CHANGELOG.md`** em `[Unreleased]`, no PR dela —
    as linhas se acumulam na branch da story até o merge em `develop`. É o que a CI valida em
    **todo** PR, inclusive os de subtask (ver `docs/CI-CD.md`).
  - **WIP dentro da feature**: uma subtask `in-progress` por vez. A regra de WIP máximo 1 por
    lane de serviço continua valendo por cima disso — uma feature `in-progress` por serviço.
  - A feature só vira `done` quando **todas** as subtasks estiverem `done` **e** a Definição de
    Pronto daquele harness for satisfeita — subtask concluída não dispensa `init.sh`,
    `Delivery Reviewer`, `Test Suite Auditor` nem `evidence`.
- **`plan_review` é pré-requisito de `in-progress`, do mesmo jeito que `evidence` é de `done`**:
  cada feature no `feature_list.json` de um harness tem um campo `plan_review`. Ele é preenchido
  com o resultado do `Plan Reviewer` (data, veredito, achados corrigidos no plano antes de
  codificar) **antes** de a feature virar `in-progress` — feature `in-progress` ou `done` com
  `plan_review` vazio é sinal de que o passo 9 do Startup Workflow foi pulado. Se o veredito for
  `BLOCKED` por uma decisão que só o usuário pode tomar, pergunte antes de codificar e registre a
  decisão junto. Os epics do `feature_list.json` da raiz **não** têm esse campo: nenhum epic é
  implementado diretamente, o trabalho real acontece nas features do harness correspondente.
- **Harness se retroalimenta pela nota do vault, não por um log de lições à parte**: toda
  descoberta com valor além da sessão atual — bug cuja causa raiz não era óbvia, lacuna de
  especificação, edge case não coberto, gotcha de configuração/lib — vira edição na nota do
  vault correspondente ao assunto (`docs/CONVENTIONS.md`, `docs/API-CONTRACTS.md`,
  `docs/TESTING.md`, `docs/OBSERVABILITY-AND-CONFIG.md`, `docs/services/<nome>.md`, etc.), no
  mesmo commit da correção — não um arquivo de "lessons learned" separado. `docs/DECISIONS-LOG.md`
  continua reservado só para decisões que divergem/estendem o TCC 1 (ver aquela nota); isto aqui
  é mais amplo — qualquer nota do vault é destino válido, pela nota do assunto, não por tipo de
  entrada.
- **Git**: cada serviço (incluindo `infra/`) é seu próprio repositório, com 4 níveis de branch —
  `main` (estável) ← `develop` (integração) ← `feature/<chave-da-story>` ←
  `subtask/<chave-da-subtask>`. Cada branch leva o código da sua própria issue no Jira (ex.:
  `feature/SV-12`, `subtask/SV-13`), e a da subtask sai da branch da story. `bugfix/<chave>` sai
  de `develop` como a story; `spike/<slug>` não tem issue e continua em kebab-case. Merge sobe um
  nível por vez, sempre `--no-ff`. Merge de branch de trabalho → `develop` só
  depois do `./init.sh` daquele repositório passar; merge `develop` → `main` quando estável o
  suficiente para ser uma entrega. **Mensagem de commit: Conventional Commits 1.0.0, sempre em
  inglês** (`feat(bets): add manual bet registration`), com `Refs: <chave-jira>` e
  `Feature: <id>` no rodapé; `!` + footer `BREAKING CHANGE:` quando um contrato entre serviços
  muda. O inglês vale só para o commit — `CHANGELOG.md`, `progress.md` e o vault seguem em
  português. Ver `docs/CONVENTIONS.md` seção "Git" para o detalhe completo.
- **Verificação obrigatória**: não declare uma feature concluída sem rodar o `init.sh` (ou
  comando de build/test) do serviço tocado.
- **Escopo restrito (stay in scope)**: não edite arquivos de um serviço fora da feature ativa
  daquele serviço, e não edite mais de um serviço na mesma feature a menos que a própria
  feature seja definida como cross-service (ex.: contrato de evento).
- **Estado limpo ao final (clean, restartable state)**: a próxima sessão precisa conseguir
  rodar `./init.sh` (raiz e do serviço tocado) imediatamente.

## Artefatos obrigatórios

Raiz:
- `feature_list.json` — backlog de epics (um por serviço/marco).
- `docs/Index.md` — porta de entrada do vault Obsidian (arquitetura, requisitos, notas por
  serviço).
- `progress.md`, `session-handoff.md` — continuidade cross-service entre sessões.
- `init.sh` — verificação agregada (ferramentas + status de cada sub-harness).

Cada serviço (`services/<nome>/`, `apps/web/` ou `infra/` — raiz do seu próprio repositório
Git):
- `CLAUDE.md` — convenções e comandos daquela stack.
- `feature_list.json` — backlog granular daquele serviço.
- `progress.md`, `session-handoff.md` — continuidade daquele serviço.
- `init.sh` — build/test daquele serviço.
- `CHANGELOG.md` — mudanças notáveis daquele serviço (Keep a Changelog), atualizado a cada
  feature — ver `docs/CI-CD.md`.
- `.github/workflows/ci.yml` — pipeline de CI daquele repositório (changelog, i18n, build,
  testes, SonarCloud) — ver `docs/CI-CD.md`.
- `.github/scripts/` — scripts de validação usados por `ci.yml` (duplicados em cada um dos 7
  repositórios, não compartilhados — ver `docs/CI-CD.md`; `infra/` só tem o script de changelog,
  sem i18n).

## Definição de pronto (Definition of Done)

Um **epic** da raiz só está `done` quando a(s) feature(s) correspondente(s) no
`feature_list.json` do harness daquele epic estiverem `done` — todo epic tem um `harness` (campo
em `feature_list.json`), incluindo `epic-001`/`epic-007`, que compartilham o harness `infra/`
(ver `docs/DECISIONS-LOG.md` "Topologia"). Uma **feature** de qualquer harness (serviço de
aplicação ou `infra/`) só está `done` quando TODOS os itens abaixo forem verdadeiros (done only
when):

- [ ] O comportamento alvo está implementado no serviço correto.
- [ ] A verificação real rodou (`init.sh` do serviço, testes, build) e passou.
- [ ] As regras de negócio relevantes (RN01–RN09) foram respeitadas, quando aplicável.
- [ ] `Delivery Reviewer` e `Test Suite Auditor` (claude-code-skills, ver
      `docs/AGENT-SKILLS.md`) rodados contra a feature antes de marcar `done`.
- [ ] Evidência registrada no `feature_list.json` do serviço (campo `evidence`) e/ou no
      `progress.md` do serviço.
- [ ] `./init.sh` do serviço (e da raiz) continua rodando sem erro.

## Fim de sessão (End of Session)

Antes de encerrar (before ending a session):

1. Atualize o `progress.md` do serviço tocado (e o da raiz, se o trabalho afetou mais de um
   serviço ou fechou um epic).
2. Atualize o `feature_list.json` do serviço (status e evidência) e, se um epic foi concluído
   ou iniciado, o `feature_list.json` da raiz também.
3. Registre riscos/bloqueios não resolvidos.
4. Faça commit quando o trabalho estiver em estado seguro, em **Conventional Commits 1.0.0 e
   sempre em inglês**, com `Refs: <chave-jira>` e `Feature: <id>` no rodapé — ver
   `docs/CONVENTIONS.md` seção "Git".
5. Deixe o repositório pronto para a próxima sessão rodar `./init.sh` (raiz e do serviço)
   imediatamente.

## Verificação

```bash
./init.sh                              # agregada: ferramentas + status de cada sub-harness
cd services/<nome> && ./init.sh        # verificação daquele serviço especificamente
cd apps/web && ./init.sh               # verificação do frontend
```

Não existe comando único de build/test para "o projeto inteiro" — não é um monorepo, cada
serviço é seu próprio repositório e evolui/é verificado de forma independente (é a razão de
existir a arquitetura de microsserviços).

## Escalação

- **Decisões de arquitetura cross-service**: consulte `docs/ARCHITECTURE.md` (vault); se a
  dúvida não estiver coberta lá, pergunte ao usuário — não reinterprete decisões já tomadas no
  TCC 1 (ver seção "Decisões que não devem ser reinterpretadas" naquela nota).
- **Decisões específicas de um serviço**: consulte o `CLAUDE.md` e a nota `docs/services/`
  daquele serviço primeiro.
- **Requisito ambíguo**: consulte `docs/REQUIREMENTS.md`; se ainda ambíguo, pergunte ao usuário.
- **Falhas repetidas de teste**: atualize o `progress.md` do serviço e sinalize para revisão
  humana.
- **Ambiguidade de escopo**: releia a `description` e `dependencies` do epic ativo na raiz e da
  feature ativa no serviço.
