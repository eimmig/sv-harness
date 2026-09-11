# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-11

## Objetivo atual

Os 9 epics originais do TCC 1 estão `done`. Segunda rodada de escopo novo (`epic-011..021`)
sobre estatísticas de decisão pré-aposta, dashboard consolidado e telas analíticas por cadastro.
`epic-011..014` fechados. Próximos epics elegíveis: `epic-016`/`epic-018` (`stats-service`, ambos
só dependem de `epic-004`, `done` — respeitar WIP máximo 1 por harness, não iniciar os dois ao
mesmo tempo). `epic-015`/`epic-017`/`epic-019`/`epic-020`/`epic-021` (`apps/web`) ainda dependem
de epics não fechados (`epic-013` já done, mas `epic-015` também depende de `epic-014` — agora
liberado).

## Concluído nesta sessão (2026-09-11)

- [x] **`epic-014` fechado** (`stats-service feat-015`, 4 subtasks, story SV-343) — `GET
      /api/v1/statistics` ganha `wonCount`/`lostCount`/`voidCount`/`preCount`/`liveCount`/
      `avgOdd` em todos os agregados existentes, mais 6º segmento `byBetType` (2 buckets fixos
      PRE/LIVE). `FACT_BET.betType` persistido (insert-only em `BetCreated`, preservado no
      upsert de `BetSettled`). Plan Reviewer (READY WITH CONCERNS, 3 MAJOR corrigidos: parâmetro
      tipado em comparação de enum JPQL, getter no tipo real do enum na projeção de `byBetType`,
      mudança de tipo `dimensionId` UUID→String com escopo de teste explícito) +
      `Delivery Reviewer`/`Test Suite Auditor`/`Persistence Auditor` (todos PASS, 1 achado real
      de doc drift corrigido — `docs/API-CONTRACTS.md` não mostrava `preCount`/`liveCount` no
      exemplo de `byBetType`). Ver `services/stats-service/progress.md` para o detalhe completo.

## Bloqueios / Riscos

Nenhum bloqueio novo. **Atenção, herdado de sessão anterior**: `services/bets-service` pode ainda
ter um `git stash` pendente (`feat-015` daquele serviço, build/push de imagem Docker pro GHCR) —
checar `git stash list` antes de iniciar qualquer feature nova ali.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Epics elegíveis: `epic-016`/`epic-018` (`stats-service`, respeitar WIP máximo 1 — só um
   `in-progress` por harness) e `epic-015` (`apps/web`, agora com `epic-013`+`epic-014` satisfeitas
   — falta só decidir se `apps/web` tem WIP livre). `epic-017`/`epic-019`/`epic-020`/`epic-021`
   (`apps/web`) ainda não elegíveis (dependem de epics acima).
3. Em `services/bets-service`, checar `git stash list` antes de iniciar qualquer feature nova.
4. Padrão reaproveitável desta sessão: quando uma comparação de enum aparece numa query JPQL,
   sempre via `@Param` tipado (`BetStatus`/`BetType`), nunca literal de string solto
   (`f.status = 'LOST'`) — literal arrisca o `AttributeConverter` (`@Converter(autoApply=true)`)
   não ser aplicado de forma garantida pelo Hibernate. Ver `docs/services/stats-service.md`.
5. Padrão reaproveitável (sessão anterior, continua valendo): extrair lógica de gráfico/sinal de
   cor compartilhada *antes* de duplicar entre telas — o gate do SonarCloud de `sv-frontend`
   (`new_duplicated_lines_density ≤ 3%`) pega duplicação real entre componentes parecidos.
6. Outro padrão reaproveitável (sessão anterior): quando uma feature precisa de autorização por
   role num serviço sem tabela `USER`, o modelo é claim no PASETO + header injetado pelo
   `api-gateway` (`X-User-Role`, lowercase `admin`/`member`) — ver `docs/DECISIONS-LOG.md` "Claim
   role no PASETO".
