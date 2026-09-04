# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-04

## Objetivo atual

- `epic-002` (`auth-service`) **fechado** — backlog inteiro (`feat-001..007`) `done`. Última
  feature (`feat-007`, pipeline de CI) foi só fechamento formal, sem código novo — ver
  `progress.md`.
- Situação: 3 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service). `epic-003` (`bets-service`) e `epic-008` (`api-gateway`) ficam elegíveis agora —
  ambos dependiam só de `epic-002`. Nenhum dos dois é `in-progress` ainda; podem avançar em
  paralelo (serviços diferentes, WIP=1 por serviço).

## Concluído nesta sessão (2026-09-04)

- [x] **`auth-service feat-007` (Pipeline de CI) implementado e mergeado em `develop`** — Plan
      Reviewer confirmou que não sobrava peça de CI faltando (setup/gate já provados em produção
      desde `epic-009`/`feat-001..006`); único achado real foi a `description` da feature estar
      desatualizada (5→6 passos, atalho `mvn sonar:sonar` incorreto). 2 subtasks (SV-58/59, story
      SV-57). Evidência completa em `services/auth-service/feature_list.json` e
      `services/auth-service/progress.md`.
- [x] **`epic-002` marcado `done`** na raiz.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005`. Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| 5 repositórios ainda sem código de aplicação | `bets-service`, `stats-service`, `api-gateway`, `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. |
| `infra`: `main` está atrás de `develop` | Merge `develop` → `main` não feito — decisão pendente do usuário, não é defeito. |
| Mecanismos reaproveitáveis de `auth-service` para os outros 2 serviços Java com banco (`bets-service`/`stats-service`) | Multi-tenancy do Hibernate por schema, padrão `Persistable`/`AttributeConverter`, migration eager para schema `public` + `InitializingBean` (não `ApplicationRunner`), gate de zero issue do SonarCloud (`validate-sonar-issues.py` + `sonar.qualitygate.wait` condicional) — todos documentados em `docs/CONVENTIONS.md`/`docs/CI-CD.md`, mas ainda não *aplicados* em nenhum outro serviço. Replicar ao bootstrapar `epic-003`/`epic-004` em vez de redescobrir. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Escolher entre **`epic-003` (`bets-service`)** ou **`epic-008` (`api-gateway`)** — ambos
   elegíveis agora, dependências (`epic-002`) `done`. Podem rodar em paralelo (sessões/serviços
   diferentes) por causa do WIP=1-por-serviço; não escolha os dois na mesma sessão.
   - `bets-service` é o próximo natural do fluxo de negócio (casas de apostas, aposta, bankroll,
     eventos `BetCreated`/`BetSettled`) e o primeiro a reaproveitar os mecanismos de
     `auth-service` listados acima.
   - `api-gateway` não tem regra de negócio própria (só roteamento/autenticação PASETO) — mais
     simples, mas sem ele `bets-service`/`stats-service` continuam confiando direto em
     `X-User-Id`/`X-Tenant-Id` do chamador (mesmo modelo já usado em `auth-service feat-004`).
3. `epic-005` (`telegram-integration`) e `epic-006` (`web`) continuam **não elegíveis**
   (dependem de `epic-003`/`epic-004`/`epic-008` ainda não `done`).
