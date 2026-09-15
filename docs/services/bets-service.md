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
- `BETTING_HOUSE` 1:N `BET`; `SPORT`, `LEAGUE`, `MARKET`, `TIPSTER`, `TEAM` são catálogos 1:N
  `BET` (`TEAM` com FK adicional pra `SPORT` — ver abaixo).
- `BET` (id, bettingHouseId FK, sportId FK, leagueId FK, marketId FK, tipsterId FK,
  **createdByUserId** (uuid, de `X-User-Id` — trilha de auditoria, sem FK real entre bancos,
  ver [[DECISIONS-LOG]] 2026-08-02), ticketNumber, team1Id FK (nullable), team2Id FK (nullable),
  description, betType, playType, stake decimal, odd decimal, status, betDate). `status` armazena
  `pending`/`won`/`lost`/`void` (inglês — ver [[API-CONTRACTS]] — corresponde a
  pendente/ganha/perdida/devolvida em RF12/RN06).
- `TEAM` (id, name, sportId FK, `UNIQUE(name, sportId)`) — catálogo próprio (não a
  `CatalogJpaEntity` genérica de `SPORT`/`LEAGUE`/`MARKET`/`TIPSTER`, que não tem FK pra outro
  catálogo), mesmo desenho de `dim_team` em [[stats-service]]. Rotas `POST`/`GET`
  `/api/v1/teams` (mesmo padrão dos outros 4 catálogos, sem `PUT`/`DELETE`). `team1Id`/`team2Id`
  de `BET` migraram de texto livre (`team1`/`team2` string) pra essa FK em `feat-017` — decisão
  em [[DECISIONS-LOG]] 2026-09-15 (`epic-024`/`feat-016`), implementação fechada no mesmo dia.
  `PLAYER` fica fora desta rodada (mesma decisão).
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
`invalid-status-transition` em qualquer outro caso, incluindo tentar voltar para `pending`).

**`team1`/`team2` viraram `team1Id`/`team2Id` (UUID) em `CreateBetRequest`/`BetResponse` na
`feat-017` (2026-09-15) — mudança incompatível deste contrato síncrono, achado do `Delivery
Reviewer` daquela feature**: diferente do contrato de evento (`BetCreated`/`BetSettled`, mantido
aditivo de propósito — ver `docs/API-CONTRACTS.md` "`TEAM` vira dimensão"), a API REST não tinha
como preservar o campo antigo com o mesmo tipo (não dá pra aceitar tanto `string` livre quanto
`uuid` no mesmo campo sem reintroduzir o texto livre que a decisão de `epic-024` queria eliminar).
**Corrigido em `apps/web feat-021` (2026-09-15, mesmo dia)**: `register-bet.ts` trocou os 2 inputs
de texto livre por selects de `team1Id`/`team2Id`, alimentados por um catálogo de times novo
(`shared/team-manager`, tela dedicada — `TEAM` não é estruturalmente idêntico aos outros 4
catálogos do frontend, tem FK `sportId` obrigatória). `services/telegram-integration` **não** é
afetado — `extraction.py` extrai `team1`/`team2` só para uso conversacional, nunca
encaminha esses campos no payload de `POST /api/v1/bets` (comentário do próprio módulo: "resolving
an extracted name against the tenant's catalog is feat-004's responsibility, not this module's").

## Liquidação de apostas e bankroll consolidado (`feat-005`)

`PATCH /api/v1/bets/{id}/status` passou a exigir `X-User-Id` (401 `missing-caller-context`, mesmo
padrão de `POST /api/v1/bets`) — vira `BET_RESULT.settledByUserId`. A transição de status deixou
de ser "ler status atual, depois escrever" (residual TOCTOU aceito em `feat-004`) e virou um
`UPDATE` atômico condicional (`WHERE status = 'pending'`, via `@Modifying @Query`) — só quem
ganha a corrida muda o status; o perdedor recebe `422 invalid-status-transition` de verdade, nunca
dado corrompido. Dentro da mesma transação (`@Transactional`, primeiro uso real deste mecanismo
no serviço), calcula `profit` (RN02 `stake*odd-stake` para `won`, RN03 `-stake` para `lost`, `0`
para `void`) e persiste `BET_RESULT` (1:1 com `BET` via `UNIQUE(bet_id)`, defesa em profundidade
além da guarda atômica).

`GET /api/v1/betting-houses` (`balance`) passou a somar também o profit líquido das apostas
liquidadas daquela casa (RN01 "atualizado pelo resultado das apostas liquidadas", RN05
"sincronização imediata") — `balance = initialBalance + depósitos - saques + profit líquido`,
numa única query agregada por página (join implícito `BET_RESULT`/`BET`, `bet_result` não tem
`bettingHouseId` direto). RF07 ("gerenciar bankroll") não ganhou endpoint de saldo consolidado
próprio — nenhuma nota do vault documenta um; o total é a soma dos `balance` já retornados,
responsabilidade do consumidor (ex.: `apps/web`).

## Saldo consolidado por data, enum PRE/LIVE, configuração de unidade (`epic-013` da raiz)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, especificação do
dashboard consolidado em [[web]]) — 3 mudanças independentes:

- **`GET /api/v1/bankroll/balance?at=<yyyy-MM-dd>`** (`feat-014.3`, default hoje): fecha o gap já
  citado acima ("RF07 não ganhou endpoint de saldo consolidado próprio") — soma o `balance` de
  **todas as casas do tenant** (mesma fórmula de `GET /api/v1/betting-houses` por casa —
  `initialBalance` + depósitos - saques + profit líquido) num único número, parametrizável no
  tempo via `at`. 3 métodos de repositório agregados novos, não agrupados por casa
  (`BettingHouseRepository.sumInitialBalance()`, `TransactionRepository.sumNetAmountUpTo(Instant)`,
  `BetResultRepository.sumProfitUpTo(Instant)` — diferentes dos métodos `Map<UUID, ...>` por casa
  já usados por `feat-005`). Corte por **liquidação**, não por `betDate` — o saldo só muda quando o
  resultado é realizado. `at` (`yyyy-MM-dd`) é convertido pro **fim do dia civil brasileiro**
  (`America/Sao_Paulo`, ver `docs/CONVENTIONS.md` "Timezone padrão") como limite superior
  exclusivo antes de comparar com `createdAt`/`settledAt` (`Instant`/UTC) — não UTC ingênuo:
  `2026-09-11T01:00:00Z` ainda é dia civil `2026-09-10` no Brasil (UTC-3) e entra no corte de
  `at=2026-09-10`, mesmo já sendo `2026-09-11` em UTC. Ver [[API-CONTRACTS]] e [[STATISTICS]]
  "Saldo inicial/final do período" para a fórmula completa e o porquê de não replicar isso para
  `stats-service` via evento. `BankrollService.getBalance` é `@Transactional(readOnly = true)`
  (achado real do `Persistence Auditor`, 2026-09-10: sem isso as 3 queries agregadas rodavam em
  3 transações implícitas separadas, podendo misturar dados de instantes diferentes sob escrita
  concorrente) — mesmo padrão de `@Transactional` já usado por `BetService.updateStatus`, sem
  override de isolation level (Postgres `READ COMMITTED`, o padrão deste banco, aceito como
  suficiente na escala deste projeto). `transaction.created_at` e `bet_result.settled_at`
  ganharam índice (`V20260910193000`) já que essas colunas passaram a sustentar um predicado de
  range varrendo a tabela inteira (sem filtro por `betting_house_id`) a cada chamada do endpoint.
- **`BET.betType` vira enum `PRE`/`LIVE`** (`feat-014.2`, `BetType` + `BetTypeAttributeConverter`,
  mesmo padrão de `BetStatus`/`BetStatusAttributeConverter`) — antes era `varchar` livre, sem
  valores fixos (usuário digitava qualquer coisa). Migração normaliza pra lowercase e zera
  (`NULL`) qualquer valor fora de `('pre','live')` antes de aplicar o `CHECK` — linhas existentes
  não têm remapeamento seguro (texto arbitrário → 2 valores fixos), apostas antigas saem das
  contagens PRÉ/LIVE do dashboard (ver [[STATISTICS]]). Publicado no evento `BetCreated`
  (`docs/contracts/bet-created.schema.json` ganhou `enum: [pre, live, null]`) — serializado
  minúsculo como qualquer outro enum de domínio deste serviço (`status`), não revalidado por
  `stats-service`, que só grava o valor recebido.
- **`TENANT_SETTINGS` nova** (schema-per-tenant, linha única, `feat-014.1`): `unitPercent`
  (`decimal`, default `0.01`), seed automático via Flyway na criação do schema do tenant (mesmo
  mecanismo já usado pra provisionar o schema — sem SQL cru montado na mão, `UUID` constante
  literal na linha única já que este codebase não usa `pgcrypto`/`gen_random_uuid()`).
  `GET`/`PATCH /api/v1/settings` — `PATCH` restrito a `X-User-Role: admin` (header novo injetado
  por `api-gateway`/`auth-service`, ver [[DECISIONS-LOG]] "Claim role no PASETO" — este serviço
  não tem tabela `USER` pra resolver role localmente como `auth-service` faz, confia no header já
  validado pelo Gateway), `403` (`AdminRoleRequiredException`) caso ausente ou `member`.
  "Unidade" de banca é percentual configurável, não valor fixo em R$ nem campo por aposta
  (decisão do usuário).

## Histórico (RF08, `feat-007`)

`GET /api/v1/bets` (listagem, além do `GET /api/v1/bets/{id}` de `feat-004`) e
`GET /api/v1/transactions` são endpoints de leitura paginados com filtros opcionais e
combináveis (ver [[API-CONTRACTS]] seção "Convenções REST" para o envelope e os query params —
mesmo vocabulário usado por [[stats-service]] para os filtros de dashboard, RF11/RN08):
`bettingHouseId`/`sportId`/`leagueId`/`marketId`/`tipsterId` (só `/bets`) e `from`/`to` (ambos os
endpoints, sobre `betDate`/`createdAt` respectivamente). Alimentam a tela de histórico em [[web]]
e servem como trilha de auditoria. Uma única query JPQL por endpoint, com predicado condicional
por filtro — **achado real**: `(:param IS NULL OR coluna >= :param)` quebra no Postgres para
coluna `timestamp` (`could not determine data type of parameter`, mesmo padrão seguro para
`UUID`) — corrigido com `coluna >= COALESCE(:param, coluna)`, ver `docs/CONVENTIONS.md`.

## Eventos publicados

Dois eventos distintos no RabbitMQ (ver [[API-CONTRACTS]] para os schemas completos e o motivo
da separação — fiel aos diagramas de fluxo do TCC1, que não reaproveitam um único evento):

- **`BetCreated`** (`feat-006`, implementado): publicado uma vez, logo após o `INSERT` de `BET`
  suceder (sempre `status: pending`). Envelope carrega `userId` = `BET.createdByUserId`.
- **`BetSettled`** (`feat-008`, implementado): publicado quando `BET_RESULT` é criado/`BET.status`
  muda para `won`/`lost`/`void` (RN06) — carrega `profit`/`settledAt`, que `BetCreated` nunca tem,
  e **não** carrega os campos descritivos de `BET` (`ticketNumber`/`team1`/`team2`/`description`/
  `betType`/`playType` — confirmado contra o schema real, diferente de `BetCreated`). Envelope
  carrega `userId` = `BET_RESULT.settledByUserId` (pode ser diferente do `userId` do `BetCreated`
  correspondente). Publicado só quando a transição atômica (`feat-005`) e o `BET_RESULT` são
  salvos com sucesso — nunca no ramo de transição inválida (`422`).

Contrato compartilhado com [[stats-service]] — não alterar nenhum dos dois payloads sem
atualizar a nota daquele serviço e os JSON Schemas correspondentes no mesmo commit.

Ambos os eventos carregam também `bettingHouseName`/`sportName`/`leagueName`/`marketName`
(obrigatórios) e `tipsterName` (opcional, acompanha `tipsterId`) — denormalizados a partir do
catálogo deste serviço (`feat-010`, implementado) para `stats-service` popular `name` das
dimensões OLAP sem chamada síncrona de volta a este serviço (ver [[API-CONTRACTS]] "Nomes das
dimensões denormalizados no payload" e [[DATA-MODEL]]). `BetService.resolveDimensionNames`
busca as 5 entidades de catálogo por id (`findById`, não só `existsById`) no momento de publicar,
tanto em `create()` quanto em `updateStatus()`.

**Mecanismo de publicação (`feat-006`/`feat-008`)**: `RabbitBetEventPublisher`
(`adapter/out/messaging/`) publica ambos os eventos no exchange `bets.events` (routing keys
`bet.created`/`bet.settled`) já provisionado por `infra/rabbitmq/definitions.json` — nunca
redeclarado em código; os dois compartilham o mesmo envelope genérico (`BetEventEnvelope<T>`) e
o mesmo método privado de publish/log de erro. Mensagem marcada `PERSISTENT` (sobrevive a
restart do broker, já que a fila de produção é durable) — ver `docs/CONVENTIONS.md` para o
gotcha de `getDeliveryMode()` vs `getReceivedDeliveryMode()` descoberto testando isso. Falha ao
publicar é logada (nível ERROR) e nunca propagada como erro HTTP — a durabilidade do registro da
aposta/liquidação pesa mais que o sinal assíncrono nesta fase do projeto; **risco residual
aceito**: sem outbox/retry, uma falha de publish nesse instante perde o evento permanentemente —
replay de `Idempotency-Key` (`BetCreated`) e nova tentativa de liquidação já resolvida
(`BetSettled`, bloqueada por `422`) não tentam republicar. Revisitar se o volume/criticidade
justificar um mecanismo de outbox. Teste de contrato valida cada mensagem publicada contra a
cópia vendorizada do schema correspondente (`src/test/resources/contracts/*.schema.json` — ver
`docs/API-CONTRACTS.md` seção "Cópias vendorizadas do schema").

## Correlation id no envelope de evento (gap conhecido, 2026-09-08)

`api-gateway feat-006` implementou o filtro global de `X-Correlation-Id` (gera/propaga, injeta no
MDC, repassa no roteamento — ver [[api-gateway]] item 5 de "Responsabilidades") — o header agora
chega de verdade em toda chamada `POST /api/v1/bets` roteada pelo Gateway. **Este serviço ainda
não lê esse header**: `BetEventEnvelope.java` não tem campo `correlationId` (só
`eventId`/`eventType`/`schemaVersion`/`occurredAt`/`tenantId`/`userId`/`payload`), apesar de
`docs/contracts/bet-created.schema.json`/`bet-settled.schema.json` já declararem `correlationId`
como propriedade opcional (não em `required`, então nada quebra sem ele). Fechar esse gap é
trabalho deste serviço (ler `X-Correlation-Id` da requisição, popular o envelope, MDC próprio) —
não implementado por `api-gateway feat-006` (fora de escopo daquele serviço, `epic-003` já
`done`). Ver `services/bets-service/src/main/java/.../adapter/out/messaging/BetEventEnvelope.java`
(comentário desatualizado — ainda cita "epic-008" como bloqueio, mas o filtro já existe).

## Ver também

- [[auth-service]] — fornece `userId`/`tenantId` (schema) usados no isolamento por schema.
- [[stats-service]] — consumidor dos eventos `BetCreated`/`BetSettled`.
- [[telegram-integration]] — chama `POST /api/v1/bets` através do [[api-gateway]], mesmo
  endpoint do formulário web.
- [[infra]] — RabbitMQ com DLQ, Postgres.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
