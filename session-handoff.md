# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-04

## Objetivo atual

- `epic-002` (`auth-service`) fechado — backlog inteiro (`feat-001..007`) `done`.
- `epic-003` (`bets-service`) **iniciado** — `feat-001` (setup do projeto) entregue e mergeado em
  `develop`. Resto do backlog (`feat-002`..`feat-009`) segue `not-started`.
- Situação: 3 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service). `epic-003` é o primeiro epic de `bets-service` com código real.
  `epic-008` (`api-gateway`) continua elegível (dependia só de `epic-002`, já `done`) e pode
  avançar em paralelo em outra sessão — nenhuma outra sessão o reivindicou ainda.

## Concluído nesta sessão (2026-09-04)

- [x] **`auth-service feat-007` fechado** — pipeline de CI formalizada, `epic-002` marcado
      `done`.
- [x] **`bets-service feat-001` implementado e mergeado em `develop`** — bootstrap Spring Boot
      4.1.1/Java 25/Maven hexagonal, Postgres dev/test/prod, provisionamento de schema de tenant
      + filtro `X-Tenant-Id` + rota admin (bundlada, decisão do Plan Reviewer), JaCoCo 80% (real
      97%+), i18n completo (foi além do residual permanente de `auth-service`), health checks,
      `.env.example` + logging estruturado, CI já endurecida desde a primeira subtask. 9
      subtasks (SV-61..69, story SV-60). Achado real na revisão final (encoding UTF-8 em filtro
      RFC 7807) corrigido e documentado. Evidência completa em
      `services/bets-service/feature_list.json` e `services/bets-service/progress.md`.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005`. Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| 4 repositórios ainda sem código de aplicação | `stats-service`, `api-gateway`, `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. |
| `infra`: `main` está atrás de `develop` | Merge `develop` → `main` não feito — decisão pendente do usuário, não é defeito. |
| `sv-api-gateway`/`sv-stats-backend`: `ci.yml` ainda com as 3 armadilhas antigas | Portar o `ci.yml` já endurecido de `sv-auth-backend`/`sv-bets-backend` (equivalentes hoje) como primeira subtask do próprio `feat-001`, proativamente — ver `docs/CI-CD.md`. |
| Mecanismos reaproveitáveis de `auth-service`/`bets-service` para `stats-service` | Multi-tenancy do Hibernate por schema, `Persistable`/`AttributeConverter`, migration eager + `InitializingBean`, gate de zero issue do SonarCloud, i18n retrofit em filtro (mecanismo provado, não mais residual) — todos documentados em `docs/CONVENTIONS.md`/`docs/CI-CD.md`. Aplicar desde o início de `epic-004`, não redescobrir. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`bets-service feat-002`** (Catálogos base — `SPORT`/`LEAGUE`/`MARKET`/`TIPSTER`) é a
   próxima feature elegível de `epic-003` — primeira a introduzir JPA/Hibernate multi-tenancy
   neste serviço. Plan Reviewer antes de codificar.
3. Alternativa em paralelo (sessão/serviço diferente): **`epic-008` (`api-gateway`)** —
   dependências (`epic-002`) já `done`, ainda não reivindicado. Sem regra de negócio própria
   (só roteamento/autenticação PASETO) — mais simples que `bets-service`, mas sem ele
   `bets-service`/`stats-service` continuam confiando direto em `X-User-Id`/`X-Tenant-Id` do
   chamador.
4. `epic-004` (`stats-service`), `epic-005` (`telegram-integration`) e `epic-006` (`web`)
   continuam **não elegíveis** (dependem de `epic-003` `done`, não apenas `in-progress`).
