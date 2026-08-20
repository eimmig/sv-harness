# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-08-17

## Objetivo atual

- Fechar as pendências de harness acumuladas e destravar `epic-002` (`auth-service`), o primeiro
  epic de serviço de aplicação do projeto.
- Situação: 1 de 8 epics `done` (`epic-001`, infra). **Nenhum código de aplicação escrito ainda**
  — os 6 repositórios de serviço têm `main` vazio, sem nenhum commit.

## Concluído nesta sessão (2026-08-17)

- [x] `infra/` saiu do estado sujo: campos `jira`/`subtasks` commitados (`c7c89ed`), correção do
      RNF06 commitada (`5c7582c`), ambos publicados em `origin/develop`. Working tree limpo.
- [x] **Conventional Commits 1.0.0, sempre em inglês** — decisão do usuário. Formato completo
      (tipos, imperativo, footers `Refs:`/`Feature:`, `!` + `BREAKING CHANGE:`) em
      `docs/CONVENTIONS.md` seção "Git". O inglês vale **só** para a mensagem de commit; vault,
      `CHANGELOG.md` e `progress.md` seguem em português.
- [x] **RNF06 / `epic-007` resolvido** (pendência aberta desde 2026-08-01): PDF do TCC 1 lido, a
      tabela tem 6 RNFs e nenhum é de tolerância a falha. Citação removida; a base do epic passou
      a ser a prosa da seção 4.1 (p. 30) e do capítulo de arquitetura. Nenhum RNF novo criado.
- [x] **SonarCloud** deixou de ser pendência aberta e virou passo agendado para
      `services/auth-service/feat-001`.
- [x] Corrigidos dois `sonar-project.properties` (`apps/web`, `services/telegram-integration`) que
      citavam caminhos de workflow da era monorepo.
- [x] Verificado que o item 11 do `DECISIONS-LOG.md` **já estava resolvido** desde 2026-08-02 — a
      nota do `progress.md` que o dava como aberto estava stale.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| `tools/.jira.env` não existe | **Bloqueia `epic-002`.** O nome da branch vem da chave do Jira, então a story precisa existir antes da branch. `tools/.jira.env.example` está completo; o script foi validado com `--dry-run` (funciona, só falta credencial). Usuário optou por configurar. |
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005`. Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila — redeclaração divergente derruba o canal com `PRECONDITION_FAILED` em loop. Armadilha de runtime, ver `docs/API-CONTRACTS.md`. |
| 6 repositórios sem commit inicial | Cada um precisa de commit em `main` + `develop` no início do seu primeiro epic. Passo 1 do setup em `docs/CI-CD.md`. |
| `infra`: `main` está atrás de `develop` | `origin/main` ainda no bootstrap; os 5 commits (incluindo a entrega de `epic-001`) estão só em `develop`. Merge `develop` → `main` não feito — decisão pendente do usuário, não é defeito. |
| `gh` CLI não instalado | Não dá para conferir resultado de pipeline de CI a partir daqui. Verificar em github.com/eimmig/sv-infra-backend/actions. |

## Próxima sessão — por onde começar

1. Confirmar se `tools/.jira.env` já existe e está preenchido
   (`python tools/jira_story.py --harness services/auth-service --feature feat-001 --dry-run`
   valida o payload sem gastar credencial).
2. Rodar `./init.sh` na raiz (deve sair `0`) e `services/auth-service/init.sh`
   (falha esperada: sem `pom.xml` ainda).
3. Iniciar **`epic-002` (`auth-service`)** — único epic elegível: dependia só de `epic-001`.
   Ordem obrigatória antes de codificar, ver `CLAUDE.md` da raiz:
   `Plan Reviewer` → preencher `plan_review` **e** `subtasks` → `tools/jira_story.py` →
   `git checkout -b feature/<chave>`.
4. Junto de `auth-service/feat-001`: commit inicial em `main` + `develop`, e o setup do
   SonarCloud (passos 2–4 de `docs/CI-CD.md`), agora agendado para este momento.
