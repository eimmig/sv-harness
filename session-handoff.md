# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-07

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service) e `epic-004` (stats-service) — `done`.
- `epic-008` (api-gateway) **iniciado nesta sessão** — `feat-001` (setup do projeto) entregue e
  mergeada em `develop`. Resto do backlog (`feat-002`..`feat-006`) segue `not-started`.
- Situação: 5 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service, `epic-003` bets-service, `epic-004` stats-service). `epic-008` é o único
  `in-progress` no momento.

## Concluído nesta sessão (2026-09-07)

- [x] **`api-gateway feat-001` implementado e mergeado em `develop`** — bootstrap Spring Boot
      4.1.1/Java 25/Maven, Spring Cloud Gateway Server WebMVC (decisão nova, ver
      `docs/DECISIONS-LOG.md`), gate JaCoCo 80%, scaffold de i18n, health checks do Actuator,
      logging estruturado ECS. 6 subtasks (SV-148..153, story SV-147). Evidência completa em
      `services/api-gateway/feature_list.json` e `services/api-gateway/progress.md`.
- [x] **Lacuna de backlog fechada**: `api-gateway feat-006` (filtro `X-Correlation-Id`) criada —
      o backlog original de `feat-001..005` nunca atribuiu essa responsabilidade a nenhuma
      feature, apesar de `docs/OBSERVABILITY-AND-CONFIG.md` já documentá-la como responsabilidade
      do Gateway e `bets-service` já depender dela (`BetEventEnvelope.correlationId`).
- [x] **Achado real corrigido antes de codificar**: `services/api-gateway/CLAUDE.md` ainda citava
      o groupId antigo (`com.eduardoimmig.betting`), nunca atualizado após a correção para
      `com.stakevault.betting` em `auth-service feat-001`.
- [x] **Achado real corrigido durante a codificação**: `docs/CI-CD.md` já alertava explicitamente
      que o `ci.yml` de `api-gateway` ainda tinha as 3 armadilhas de sequenciamento de subtask
      (i18n guardado só por `pom.xml`, goal solto do JaCoCo, atalho do sonar) — o Plan Review
      original buscou por palavra-chave na nota em vez de lê-la inteira e não pegou o aviso.
      Corrigido reativamente (PR de `feat-001.1` quebrou de verdade), portando o `ci.yml` já
      endurecido de `stats-service`. `docs/CI-CD.md` atualizado para fechar a pendência.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, falta `epic-005`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| 3 repositórios ainda sem código de aplicação | `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. `api-gateway` já tem `feat-001`. |
| Dois achados do Test Suite Auditor em `api-gateway feat-001`, deliberadamente em aberto | `MessagesTest`/`LocaleConfigTest` provam o mecanismo isoladamente, não o bean real do Spring numa resposta HTTP localizada — mesmo tradeoff já aceito em `auth-service feat-001.5`. Fecha com cobertura real em `api-gateway feat-002` (primeira resposta 401 RFC 7807 localizada). |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`api-gateway feat-002`** (Validação de token PASETO + injeção de `X-User-Id`/`X-Tenant-Id`)
   é a próxima feature elegível de `epic-008` — primeira a ler `PASETO_LOCAL_KEY` (mesma chave de
   `auth-service`) e a criar o `.env.example` deste serviço. Plan Reviewer antes de codificar —
   **ler `docs/CI-CD.md` inteiro**, não só buscar por palavra-chave (lição desta sessão).
3. Alternativa em paralelo (sessão/serviço diferente): **`api-gateway feat-006`** (filtro
   `X-Correlation-Id`) — depende só de `feat-001`, já `done`, independente do filtro de PASETO.
   Cuidado: WIP máximo 1 por serviço — não trabalhar em `feat-002` e `feat-006` ao mesmo tempo em
   sessões paralelas, mesmo sendo independentes entre si.
4. `epic-005` (`telegram-integration`) e `epic-006` (`web`) continuam **não elegíveis** — ambos
   dependem de `epic-008` `done` (não apenas `in-progress`), que só fecha quando `api-gateway`
   fechar `feat-002..006`.
5. `epic-007` (resiliência DLQ/retry) continua **não elegível** — depende de `epic-004` (já
   `done`) **e** `epic-005` (ainda `not-started`).
