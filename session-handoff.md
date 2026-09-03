# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-03

## Objetivo atual

- `epic-002` (`auth-service`) iniciado — `feat-001` (setup do projeto) entregue e mergeado em
  `develop`. RF01/RF02 e o resto do backlog de `auth-service` (`feat-002`..`feat-006`) seguem
  `not-started`.
- Situação: 2 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud). `epic-002`
  é o primeiro epic de serviço de aplicação com código real — os outros 5 serviços (`bets-service`,
  `stats-service`, `api-gateway`, `telegram-integration`, `web`) continuam com `main`/`develop`
  vazios, só o commit de bootstrap.

## Concluído nesta sessão (2026-09-03)

- [x] **`auth-service feat-001` implementado e mergeado em `develop`** — Spring Boot 4.1.1,
      layout hexagonal, conexão Postgres por profile, provisionamento de schema de tenant +
      migração lazy por requisição, gate JaCoCo 80%, i18n, health checks, logging JSON
      estruturado. 9 subtasks (SV-11..SV-19). Evidência completa em
      `services/auth-service/feature_list.json` e `services/auth-service/progress.md`.
- [x] **`groupId` corrigido**: `com.eduardoimmig.betting` → `com.stakevault.betting`, em
      `docs/CONVENTIONS.md` e nos arquivos já commitados de `auth-service`.
- [x] **`CHANGELOG.md` de todo repositório de aplicação virou índice de issues do Jira** (uma
      linha `- [chave](url) - título` por story/subtask, escrita automaticamente por
      `tools/jira_story.py`), não mais Keep a Changelog com prosa. Gate de changelog na CI mudou
      de "todo PR" para "só PR story→develop". `docs/CONVENTIONS.md`, `docs/CI-CD.md`,
      `tools/jira_story.py` atualizados.
- [x] **`/code-review` (skill builtin) vira etapa obrigatória antes de cada PR de subtask** —
      `docs/CONVENTIONS.md`, `docs/AGENT-SKILLS.md`. Achou e corrigiu problemas reais em 5 das 9
      subtasks desta sessão (ver evidência de `feat-001`).
- [x] **Análise das skills sempre em português** — `docs/AGENT-SKILLS.md` seção "Idioma das
      análises", registrado antes de iniciar `feat-001`.
- [x] 3 gotchas de guarda-por-marcador na CI, reais e documentados em `docs/CI-CD.md` para os
      outros 5 repositórios (i18n, goal `jacoco:report` solto, atalho `sonar:sonar`).

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005`. Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| 5 repositórios ainda sem código de aplicação | `bets-service`, `stats-service`, `api-gateway`, `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. |
| `infra`: `main` está atrás de `develop` | Merge `develop` → `main` não feito — decisão pendente do usuário, não é defeito. |
| GitGuardian só escaneia `pull_request` | Achado real em `auth-service feat-001.9`: um valor de exemplo em `.env.example` só foi flagado no PR final, não nas 8 PRs de subtask anteriores. Ver `services/auth-service/progress.md`. Vale revisar `.env.example` de cada novo serviço com placeholder sem formato de senha real (`CHANGE_ME`) antes da primeira PR que o toque. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Continuar `epic-002` (`auth-service`): `feat-002` (entidades `USER`/`TELEGRAM_ACCOUNT`,
   primeiras migrations Flyway reais) é a próxima feature elegível — `Plan Reviewer` antes de
   codificar, mesmo fluxo já validado ponta a ponta em `feat-001`.
3. `epic-008` (`api-gateway`) **ainda não é elegível** — depende de `epic-002` `done` (regra de
   WIP em `CLAUDE.md` raiz: dependências precisam estar `done`, não apenas `in-progress`), e
   `epic-002` só tem `feat-001` de um backlog de 6 features feito. Continuar em `auth-service`.
