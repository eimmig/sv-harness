---
tags: [service, backend]
---

# bets-service

Java 25 + Spring Boot 4.x. Ver [[ARCHITECTURE]] para o panorama geral e [[REQUIREMENTS]] para
RF/RN completos. Harness de código em `services/bets-service/CLAUDE.md`.

## Responsabilidade

RF03 (casas de apostas), RF04 (manter apostas), RF05 (receptor da captura automática, feita
por [[telegram-integration]]), RF06 (processar resultados), RF07 (gerenciar bankroll), RF08
(histórico), RF12 (status da aposta), RF13 (movimentações financeiras).

## Multi-tenancy

Schema isolado por tenant (**Schema-per-Tenant**, `tenant_<slug>`) dentro do Postgres
transacional (OLTP), garantindo ACID e isolamento entre organizações. Não é isolamento por banco
físico (isso é reservado para o isolamento entre *serviços*, não entre *tenants* do mesmo
serviço). Tenant = organização com múltiplos usuários (ver [[auth-service]] e
[[DECISIONS-LOG]]) — o schema de conexão é resolvido a partir do header `X-Tenant-Id` (não mais
`X-User-Id`, ver [[API-CONTRACTS]]), e migrado sob demanda antes de atender a requisição (Flyway
lazy, ver [[CONVENTIONS]] seção "Migrations").

## Provisionamento de tenant (rota admin)

`POST /api/v1/admin/tenants` (`{"slug": "<slug>"}` → 201 `{"schema": "tenant_<slug>"}`), autenticada
por `X-Admin-Api-Key` (ver [[API-CONTRACTS]] e [[DECISIONS-LOG]] item 3 — chamada manual do
operador, direto neste serviço, não roteada pelo `api-gateway`). Idempotente por design (409
`tenant-already-provisioned` se o slug já tem schema), 422 `invalid-tenant-slug` para slug
malformado. Diferente de [[auth-service]] `feat-003`: aqui não há criação de usuário/senha — só o
schema `tenant_<slug>` (`ProvisionTenantSchemaUseCase`, mesmo mecanismo Flyway lazy usado pelo
filtro por requisição, ver [[CONVENTIONS]] seção "Migrations"). Implementado em `feat-001.4`
(bundlado com o setup do serviço, não uma feature separada como em `auth-service` — decisão
aceita no Plan Reviewer daquela feature, já que não há complexidade de criação de admin aqui).

## Modelo de dados (OLTP)

Ver [[DATA-MODEL]] para o ERD (Mermaid + PNG original do TCC1). Confirmado sem divergências em
2026-08-01.

- `BETTING_HOUSE` (id, name, initialBalance, createdAt) 1:N `TRANSACTION` (id, bettingHouseId FK,
  type, amount, createdAt) — depósitos/saques (RF13).
- `BETTING_HOUSE` 1:N `BET`; `SPORT`, `LEAGUE`, `MARKET`, `TIPSTER` são catálogos 1:N `BET`.
- `BET` (id, bettingHouseId FK, sportId FK, leagueId FK, marketId FK, tipsterId FK,
  **createdByUserId** (uuid, de `X-User-Id` — trilha de auditoria, sem FK real entre bancos,
  ver [[DECISIONS-LOG]] 2026-08-02), ticketNumber, team1, team2, description, betType, playType,
  stake decimal, odd decimal, status, betDate). `status` armazena `pending`/`won`/`lost`/`void`
  (inglês — ver [[API-CONTRACTS]] — corresponde a pendente/ganha/perdida/devolvida em RF12/RN06).
- `BET` 1:1 `BET_RESULT` (id, betId FK, **settledByUserId** (uuid, de `X-User-Id` — pode ser
  diferente de `createdByUserId`), profit decimal, settledAt) — só existe quando a aposta é
  liquidada.

## Regras de negócio a codificar (ver [[REQUIREMENTS]] para a tabela completa)

- RN01 — saldo consolidado = soma dos saldos iniciais de todas as casas, ajustado por
  depósitos/retiradas, atualizado pelo resultado das apostas liquidadas.
- RN02 — lucro bruto (vitória) = `stake * odd - stake`.
- RN03 — prejuízo (derrota) = `stake` integral.
- RN05 — sincronização do saldo deve ser **imediata** após liquidação, não em lote.
- RN06 — aposta só entra em métricas quando `status` vira `won`/`lost`/`void` (não `pending`).
- RN07 — `stake` nunca negativo; `odd` estritamente > 1,00; bloquear movimentações inconsistentes.

## Catálogos base (`feat-002`)

`POST`/`GET` (paginado, envelope de [[API-CONTRACTS]]) para os 4 catálogos —
`/api/v1/sports`, `/api/v1/leagues`, `/api/v1/markets`, `/api/v1/tipsters`. Sem seed
compartilhado: cada schema de tenant nasce vazio, cada organização cadastra os próprios
catálogos (decisão explícita do usuário, ver [[DECISIONS-LOG]] item 8) — sem isso, nenhum
tenant conseguiria referenciar `sportId`/`leagueId`/`marketId`/`tipsterId` em `BET` (`feat-004`).
`409 <catalog>-already-registered` para nome duplicado dentro do mesmo schema (`UNIQUE(name)`
por tabela). Primeira introdução de multi-tenancy do Hibernate neste serviço
(`CurrentTenantIdentifierResolver`/`MultiTenantConnectionProvider`, mesmo padrão de
[[auth-service]] `feat-002`, ver [[CONVENTIONS]]) — e primeiro momento em que
`TenantSchemaFilter` passa a exigir `X-Tenant-Id` (`400 missing-tenant-id`) em rotas de negócio,
antecipando o que `feat-001` tinha deixado como residual para `feat-004`.

## Casas de apostas e movimentações (`feat-003`)

`POST`/`GET` (paginado) para `/api/v1/betting-houses` e `/api/v1/transactions` (RF03/RF13).
`GET /api/v1/betting-houses` inclui `balance` calculado (`initialBalance` + depósitos - saques,
parcela de RN01 anterior à liquidação de apostas — o restante, resultado das apostas liquidadas,
entra em `feat-005`), numa única query agregada por página (não uma soma por casa). `409
betting-house-already-registered` para nome duplicado (`UNIQUE(name)`); `404
betting-house-not-found` ao criar movimentação para `bettingHouseId` inexistente; `400
validation-failed` para `amount` não positivo (RN07, "bloquear movimentações inconsistentes") —
saque que deixaria o saldo negativo **não** é bloqueado (RN01 trata saldo como total corrente, não
piso rígido; revisitar se o usuário quiser proteção contra saldo negativo). `type` de
`TRANSACTION` (`deposit`/`withdrawal`) trafega minúsculo no JSON via `@JsonProperty` por
constante — ver [[CONVENTIONS]] seção "Padrões de código Java" para o porquê de não seguir o
precedente maiúsculo de `Role` em [[auth-service]].

## Registro e ciclo de vida da aposta (`feat-004`)

`POST /api/v1/bets` (RF04/RF05, compartilhado com [[telegram-integration]] via [[api-gateway]]):
`createdByUserId` = `X-User-Id` (401 `missing-caller-context` se ausente/inválido, mesmo padrão
de [[auth-service]] `feat-004`), valida as 4 FKs (`bettingHouseId`/`sportId`/`leagueId`/
`marketId` obrigatórias, `tipsterId` opcional — nullable, ver `docs/contracts/bet-created.schema.json`
já existente antes desta feature), 404 `<recurso>-not-found` para FK inexistente. RN07 (`odd`
estritamente > 1,00, `stake` > 0) validado como regra de domínio (422 `invalid-odd`/
`invalid-stake`, mensagem citando "(RN07)" — segue o exemplo literal de [[API-CONTRACTS]], não
Bean Validation). Header `Idempotency-Key` opcional: reenvio da mesma chave retorna a aposta já
criada (200, não 201), sem checar se o corpo bate com o original (simplificação aceita, sem TTL).
`GET /api/v1/bets/{id}` (recurso único, 404 `bet-not-found`) e `PATCH /api/v1/bets/{id}/status`
(RF12) completam o ciclo mínimo — só `pending -> won|lost|void` é transição válida (422
`invalid-status-transition` em qualquer outro caso, incluindo tentar voltar para `pending`). Esta
feature não cria `BET_RESULT` nem calcula `profit`/atualiza saldo (RN02/RN03/RN05) — isso é
`feat-005`, que reage à mesma transição de status.

**Risco residual aceito**: `BetService.updateStatus` lê o status atual e só depois escreve (sem
`WHERE status = 'pending'` atômico nem `@Version`) — duas chamadas `PATCH` concorrentes para a
mesma aposta `pending` poderiam ambas passar a validação e a segunda sobrescrever a primeira
(last-write-wins), sem nunca retornar `422`. Sem consequência hoje (não há `BET_RESULT`/`profit`
associado ainda); revisitar quando `feat-005` passar a depender desta transição ser exatamente-uma-vez.

## Histórico (RF08)

`GET /api/v1/bets` e `GET /api/v1/transactions` são endpoints de leitura paginados (ver
[[API-CONTRACTS]] seção "Convenções REST" para o envelope e os query params de filtro — mesmo
vocabulário usado por [[stats-service]] para os filtros de dashboard, RF11/RN08). Alimentam a
tela de histórico em [[web]] e servem como trilha de auditoria.

## Eventos publicados

Dois eventos distintos no RabbitMQ (ver [[API-CONTRACTS]] para os schemas completos e o motivo
da separação — fiel aos diagramas de fluxo do TCC1, que não reaproveitam um único evento):

- **`BetCreated`**: publicado uma vez, no registro inicial de `BET` (sempre `status: pending`).
  Envelope carrega `userId` = `BET.createdByUserId`.
- **`BetSettled`**: publicado quando `BET_RESULT` é criado/`BET.status` muda para
  `won`/`lost`/`void` (RN06) — carrega `profit`/`settledAt`, que `BetCreated` nunca tem.
  Envelope carrega `userId` = `BET_RESULT.settledByUserId` (pode ser diferente do `userId` do
  `BetCreated` correspondente).

Contrato compartilhado com [[stats-service]] — não alterar nenhum dos dois payloads sem
atualizar a nota daquele serviço e os JSON Schemas correspondentes no mesmo commit.

## Ver também

- [[auth-service]] — fornece `userId`/`tenantId` (schema) usados no isolamento por schema.
- [[stats-service]] — consumidor dos eventos `BetCreated`/`BetSettled`.
- [[telegram-integration]] — chama `POST /api/v1/bets` através do [[api-gateway]], mesmo
  endpoint do formulário web.
- [[infra]] — RabbitMQ com DLQ, Postgres.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
