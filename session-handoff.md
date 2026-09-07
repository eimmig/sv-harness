# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-07

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service) e `epic-004` (stats-service) — `done`.
- `epic-008` (api-gateway) **em andamento** — `feat-001` (setup) e `feat-002` (validação PASETO)
  entregues e mergeadas em `develop`. Resto do backlog (`feat-003`..`feat-006`) segue
  `not-started`.
- Situação: 5 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service, `epic-003` bets-service, `epic-004` stats-service). `epic-008` é o único
  `in-progress` no momento.

## Concluído nesta sessão (2026-09-07)

- [x] **`api-gateway feat-001` implementado e mergeado em `develop`** — bootstrap Spring Boot
      4.1.1/Java 25/Maven, Spring Cloud Gateway Server WebMVC (decisão nova, ver
      `docs/DECISIONS-LOG.md`), gate JaCoCo 80%, scaffold de i18n, health checks do Actuator,
      logging estruturado ECS. 6 subtasks (SV-148..153, story SV-147).
- [x] **`api-gateway feat-002` implementado e mergeado em `develop`** — `PasetoAuthenticationFilter`
      valida `Authorization: Bearer <token>` (decisão de transporte nova, ver
      `docs/API-CONTRACTS.md`), injeta `X-User-Id`/`X-Tenant-Id`, nunca repassa o token original
      nem aceita identidade do cliente. 4 subtasks (SV-155..158, story SV-154). Achados reais
      corrigidos: NPE em claim nula, claims ausentes não validadas, `Authorization` vazando pro
      downstream, limite de expiração incorreto (`/code-review`); filtro bloqueando
      `/actuator/health` do `feat-001.4` (só visto rodando a suíte completa); `java:S1075` do
      SonarCloud (path/delimitador hardcoded, 2 rodadas de correção); cobertura assimétrica de
      teste (Test Suite Auditor).
- [x] **Lacuna de backlog fechada**: `api-gateway feat-006` (filtro `X-Correlation-Id`) criada —
      o backlog original de `feat-001..005` nunca atribuiu essa responsabilidade a nenhuma
      feature, apesar de `docs/OBSERVABILITY-AND-CONFIG.md` já documentá-la como responsabilidade
      do Gateway e `bets-service` já depender dela (`BetEventEnvelope.correlationId`).
- [x] **Dois achados reais corrigidos na documentação, antes/durante a codificação de
      `feat-001`**: groupId antigo em `services/api-gateway/CLAUDE.md`; `docs/CI-CD.md` já
      alertava sobre as 3 armadilhas de sequenciamento de subtask no `ci.yml` (o Plan Review
      original buscou por palavra-chave em vez de ler a nota inteira e não pegou o aviso).

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, falta `epic-005`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| 2 repositórios ainda sem código de aplicação | `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. `api-gateway` já tem `feat-001`/`feat-002`. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`api-gateway feat-003`** (Roteamento para auth-service/bets-service/stats-service) é a
   próxima feature natural de `epic-008` — primeira a dar propósito real ao serviço além de só
   validar token isoladamente. Plan Reviewer antes de codificar — **ler `docs/CONVENTIONS.md` e
   `docs/CI-CD.md` inteiros**, não só buscar por palavra-chave (lição de `feat-001`).
3. Alternativa em paralelo (sessão/serviço diferente): **`api-gateway feat-006`** (filtro
   `X-Correlation-Id`) — depende só de `feat-001`, já `done`, independente do filtro de PASETO.
   Cuidado: WIP máximo 1 por serviço — não trabalhar em `feat-003` e `feat-006` ao mesmo tempo em
   sessões paralelas, mesmo sendo independentes entre si.
4. Qualquer filtro *bloqueante* novo em `api-gateway` (ex.: `feat-004`, `X-Service-Key`) precisa
   excluir `/actuator/**` desde o início — ver `docs/CONVENTIONS.md`, não redescobrir a regressão
   de `feat-002`.
5. `epic-005` (`telegram-integration`) e `epic-006` (`web`) continuam **não elegíveis** — ambos
   dependem de `epic-008` `done` (não apenas `in-progress`), que só fecha quando `api-gateway`
   fechar `feat-003..006`.
6. `epic-007` (resiliência DLQ/retry) continua **não elegível** — depende de `epic-004` (já
   `done`) **e** `epic-005` (ainda `not-started`).
