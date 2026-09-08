# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-08

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service) e `epic-004` (stats-service) — `done`.
- `epic-008` (api-gateway) **em andamento** — `feat-001`, `feat-002`, `feat-003`, `feat-004` e
  `feat-006` entregues e mergeadas em `develop`. Só `feat-005` (fechamento formal do pipeline de
  CI) resta.
- Situação: 5 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service, `epic-003` bets-service, `epic-004` stats-service). `epic-008` é o único
  `in-progress` no momento, a uma feature de fechar.

## Concluído nesta sessão (2026-09-08)

- [x] **`api-gateway feat-006` implementado e mergeado em `develop`** — filtro global
      `X-Correlation-Id` (`CorrelationIdFilter`, `@Order(Ordered.HIGHEST_PRECEDENCE)`, sem
      `shouldNotFilter` — roda pra toda rota): gera UUID quando ausente/em branco, propaga quando
      presente, injeta no MDC, ecoa na response (decisão além do contrato documentado), repassa
      via `CorrelationIdRequestWrapper` pro roteamento. 2 subtasks (SV-177/178, story SV-176), 2
      PRs de subtask + 1 PR de story, todos com CI verde (SonarCloud incluso no último). Fechava
      uma lacuna real do backlog original (`feat-001..005` nunca cobriam isso, apesar de
      `bets-service` já depender dele para popular `correlationId` no envelope de evento).
- [x] **Achado real de escopo, corrigido pelo Plan Review antes de codificar**: o plano original
      cogitava abrir uma feature nova em `services/bets-service/feature_list.json` sinalizando
      que `BetEventEnvelope` ainda não lê o header real — corrigido para sinalizar só via nota do
      vault (`docs/services/bets-service.md`, nova seção "Correlation id no envelope de evento
      (gap conhecido)"), sem tocar em nenhum arquivo de `services/bets-service/` — `epic-003` já
      está `done` e o gap não bloqueia `feat-006`.
- [x] **Achado real do Delivery Reviewer, corrigido antes de fechar**: os 2 testes de integração
      novos só cobriam a rota pública `/api/v1/auth/login`, sem provar que
      `CorrelationIdRequestWrapper` compõe corretamente quando aninhado com
      `ResolvedIdentityRequestWrapper` (rotas PASETO/`X-Service-Key`) — corrigido estendendo os 2
      testes de integração já existentes dessas rotas.
- [x] `docs/services/api-gateway.md` (item 5) e `docs/services/bets-service.md` (nova seção)
      atualizados no mesmo commit lógico do fechamento da feature.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, falta `epic-005`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| `bets-service` não consome `X-Correlation-Id` real ainda | `BetEventEnvelope` não tem campo `correlationId` apesar do header agora existir de verdade (`api-gateway feat-006`). Sinalizado em `docs/services/bets-service.md`, não é blocker de nada — fica pra uma sessão futura de `bets-service` decidir se/quando fechar. |
| 2 repositórios ainda sem código de aplicação | `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. `api-gateway` está com 5 de 6 features fechadas. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`api-gateway feat-005`** (fechamento formal do pipeline de CI) é a única feature restante de
   `epic-008` — provavelmente uma feature de fechamento sem código novo (o pipeline já roda de
   verdade desde `epic-009`/`feat-001`), mesmo padrão de `auth-service feat-007`. Confirmar que a
   `description` da feature ainda bate com o `ci.yml` real antes de escrever qualquer plano.
   Fechar essa feature fecha `epic-008` inteiro — atualizar `feature_list.json` da raiz na mesma
   sessão.
3. `epic-005` (`telegram-integration`) e `epic-006` (`web`) continuam **não elegíveis** — ambos
   dependem de `epic-008` `done` (não apenas `in-progress`).
4. `epic-007` (resiliência DLQ/retry) continua **não elegível** — depende de `epic-004` (já
   `done`) **e** `epic-005` (ainda `not-started`).
