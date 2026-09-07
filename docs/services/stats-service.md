---
tags: [service, backend]
---

# stats-service

Java 25 + Spring Boot 4.x. Ver [[ARCHITECTURE]] para o panorama geral e [[REQUIREMENTS]] para
RF/RN completos. Harness de código em `services/stats-service/CLAUDE.md`.

## Responsabilidade

RF09 (gerar métricas), RF10 (parte de performance dos dashboards), RF11 (suporte a filtros).

## Consumo de eventos

Consome dois eventos do RabbitMQ, publicados por [[bets-service]] (ver [[API-CONTRACTS]] para os
dois schemas — não é um único evento reaproveitado):

- **`BetCreated`** (registro inicial, sempre `status: pending`): faz *insert* em `FACT_BET`
  com os dados dimensionais e `status = 'pending'`, `profit = null`. RN06 já exclui essa linha
  de qualquer agregação (ver seção "Regras de negócio" abaixo) — ela existe só para que a aposta
  apareça em listagens/contagens antes de ser liquidada.
- **`BetSettled`** (liquidação): faz *upsert* na mesma linha de `FACT_BET` por `betId`,
  atualizando `status`, `profit` e `isWin`. Só a partir daqui a aposta entra nas métricas
  (RN06). O payload de `BetSettled` repete os campos dimensionais justamente para este upsert
  não depender de o `BetCreated` correspondente já ter sido processado (mensagens podem chegar
  fora de ordem).

Consumo **assíncrono e idempotente** — consistência eventual, não síncrona com o registro da
aposta (ver [[ARCHITECTURE]] seção "Fluxos dinâmicos"). Falhas consecutivas vão para a DLQ (ver
[[infra]]).

> **Implementado em `feat-001.9`/`feat-002`/`feat-003`**: o listener (`@RabbitListener` ligado à
> fila real `stats.bet-events`, mesmo nome/argumentos de `infra/rabbitmq/definitions.json`) valida
> cada mensagem contra o JSON Schema do `eventType` correspondente (cópia vendorizada em
> `src/main/resources/contracts/`, lida em runtime — diferente da cópia só-de-teste do lado
> publicador em `bets-service`, ver [[API-CONTRACTS]] "Cópias vendorizadas do schema") antes de
> processar. Mensagem que não bate com o schema, ou cujo `tenantId` não resolve para um tenant
> provisionado, é rejeitada sem reenfileirar (`AmqpRejectAndDontRequeueException`, não o
> `x-delivery-limit`/retry — ver [[CONVENTIONS]]) e cai direto na DLQ — nos dois casos a falha é
> permanente, retentar não ajuda. `BetCreated` faz *insert* em `FACT_BET` (`status: pending`) só
> quando a linha ainda não existe — se `BetSettled` já chegou primeiro (mensagens fora de ordem),
> `BetCreated` é um no-op além de marcar o evento processado, nunca reverte a liquidação já
> aplicada. `BetSettled` sempre faz *upsert* de verdade (carrega a linha existente via `findById`
> e muta a instância rastreada pelo Hibernate — `FactBetJpaEntity.applyFrom`, não reconstrói a
> entidade do zero, que tentaria `INSERT` de novo e falharia por chave duplicada; ver
> [[CONVENTIONS]] "Atualizar uma linha já persistida"). As 6 dimensões são resolvidas por
> `DimensionResolver`: as 5 nominais (upsert-if-missing por `existsById`) e `DIM_DATE` (única sem
> id vindo do evento — localizada por chave natural dia/mês/ano, criada sob demanda).

> O envelope de evento carrega `userId` além de `tenantId` desde 2026-08-02 (trilha de
> auditoria, ver [[DECISIONS-LOG]] e [[bets-service]]) — **este serviço não persiste esse campo**
> em `FACT_BET`. RN04/RN08/RN09 agregam por tenant/segmento (esporte/mercado/casa), não por
> usuário; não há requisito hoje para dashboards por usuário dentro do tenant. Se isso mudar,
> adicionar a coluna é direto (o dado já chega no envelope), mas não antecipar sem um RF/RN que
> peça.

### Idempotência: `PROCESSED_EVENT`

Antes de processar qualquer evento, verifica se `eventId` já está em `PROCESSED_EVENT`
(id, eventId, processedAt) — se sim, só confirma o ACK sem reprocessar; se não, processa e então
insere o `eventId` na mesma transação. Sem essa tabela, uma redelivery do RabbitMQ duplicaria
métricas (é exatamente o teste de idempotência exigido em [[TESTING]]). Fiel ao passo "Verificar
EVENTOS_PROCESSADOS" do diagrama de sequência do TCC1 (`docs/diagrams/flows/event-consumption.png`
— nome traduzido para inglês nesta revisão, mesma decisão de "tudo em inglês" — o diagrama
conceitual mais antigo do TCC1 já usava `PROCESSED_EVENT` em inglês para essa mesma tabela, então
esta tradução também é mais fiel ao material original), que não tinha uma tabela equivalente
sobrevivido no ERD final — revivida aqui deliberadamente porque o requisito de idempotência
(TESTING.md) não tem outro mecanismo definido. Ver [[DATA-MODEL]] seção "Evolução do modelo" para
o histórico completo dessa decisão.

## Multi-tenancy

Schema isolado por tenant (**Schema-per-Tenant**, `tenant_<slug>`) — mesmo padrão de
[[bets-service]] e [[auth-service]] (ver [[DECISIONS-LOG]]). O schema de conexão é resolvido a
partir do header `X-Tenant-Id` (ver [[API-CONTRACTS]]) tanto no consumo de evento (`tenantId` do
envelope) quanto nas consultas de `GET /api/v1/statistics`, e migrado sob demanda antes de
processar (Flyway lazy, ver [[CONVENTIONS]]).

## Modelo de dados (OLAP — esquema estrela, isolado por cliente, banco separado do OLTP)

Ver [[DATA-MODEL]] para o ERD completo (Mermaid + PNG original do TCC1).

- Fato `FACT_BET` (id, dateId FK, bettingHouseId FK, sportId FK, leagueId FK, marketId FK,
  tipsterId FK, stake decimal, profit decimal nullable, isWin boolean nullable, status varchar,
  betCount int). `status` armazena `pending`/`won`/`lost`/`void` (inglês, ver
  [[API-CONTRACTS]]). `status` e `profit`/`isWin` nullable são uma extensão sobre o ERD original
  do TCC1 (que não tinha `status`) — necessária para RN06 (excluir `pending` das agregações) e
  para o padrão insert-then-upsert descrito acima.
- Dimensões: `DIM_DATE` (day, month, year, quarter, dayOfWeek), `DIM_BETTING_HOUSE`,
  `DIM_SPORT`, `DIM_LEAGUE`, `DIM_MARKET`, `DIM_TIPSTER` (todas `id`+`name`). `id` é o mesmo uuid
  do catálogo em `bets-service`; `name` vem denormalizado do payload do evento
  (`bettingHouseName`/`sportName`/etc., ver [[API-CONTRACTS]]) — este serviço nunca consulta
  `bets-service` de volta para resolver nome (ver [[DATA-MODEL]]).
- `PROCESSED_EVENT` (id, eventId, processedAt) — controle técnico de idempotência, não é uma
  dimensão nem participa do esquema estrela.

## Cache Redis (Cache-Aside)

O próprio serviço decide quando ler/gravar cache — não é responsabilidade de um proxy externo.
Chaves padronizadas (inglês, mesma decisão de nomenclatura técnica — ver [[API-CONTRACTS]]):

- `tenant:{tenantId}:dashboard:consolidated` — ROI total, taxa de acerto macro, saldo unificado.
- `tenant:{tenantId}:stats:monthly:{year}_{month}` — série histórica para gráficos de linha.
- `tenant:{tenantId}:segment:{sport|market|house}` — ranking de performance por segmento.

> **Corrigido em 2026-08-02** (ver [[DECISIONS-LOG]]): as chaves eram `user:{id}:...`, coerente
> com o modelo antigo (tenant = usuário). Como `FACT_BET` é isolado por schema de **tenant**, não
> tem coluna de usuário, e é compartilhado por todos os usuários daquela organização, a chave
> correta é por `tenantId`, não por `userId` — do contrário dois usuários do mesmo tenant veriam
> caches (e portanto dashboards) diferentes sem motivo.

> **Implementado em `feat-005`**: `MetricsCacheRepository` (`domain/port/out`) não recebe o
> tenant como parâmetro em nenhum método — o adapter Redis (`RedisMetricsCacheRepository`)
> resolve o slug internamente via `TenantContextHolder.current().slug()`, a mesma simetria que
> `TenantIdentifierResolver` já usa pra rotear o schema do Hibernate. O segmento `house` (casa de
> apostas) foi acrescentado ao padrão de chave original (que só citava `sport|market`) — RN09 já
> exige ROI por mercado/esporte/**casa**, e `feat-004` já implementava `calculateByBettingHouse`,
> então deixar aquele segmento sem cache seria uma assimetria sem motivo. `GetDashboardMetricsService`
> (`application`) orquestra o cache-aside: hit no Redis responde direto, miss chama
> `CalculateMetricsUseCase` e grava antes de retornar (uma consulta a `stats:monthly:{year}_{month}`
> ausente recalcula e cacheia a série inteira de uma vez, aproveitando pra aquecer os outros
> meses). TTL de segurança de 1h em toda gravação — não é regra de negócio (nenhum RNF define
> TTL), é rede de segurança contra uma invalidação esquecida.
>
> **Invalidação no consumo do evento, não só TTL** (decisão do usuário, 2026-09-07, resolvendo
> uma divergência real entre [[ARCHITECTURE]], cujo fluxo já dizia que `stats-service` "atualiza
> o cache Redis" ao processar o evento, e o backlog original desta feature, que só descrevia
> cache-aside puro): sem invalidação, uma aposta liquidada só refletiria no dashboard depois do
> TTL inteiro expirar. **Só `BetSettled` evicta** as 5 chaves do tenant (incluindo o mês
> específico da liquidação) — `BetCreated` nunca evicta: ele só insere `FACT_BET` com
> `status=pending`, e RN06 exclui `pending` de toda agregação, então aquele insert é invisível
> para qualquer métrica cacheada (evictar ali seria desperdício, sem nenhuma mudança de valor).
> Achado real durante a implementação, corrigindo a premissa inicial do plano.

Meta de performance (RNF03): resposta de dashboard < 300 ms (depende do cache estar quente).

## Regras de negócio

- RN04 — `ROI agregado = lucro líquido acumulado / valor total investido`.
- RN06 — toda agregação (RN04, RN09, dashboards) filtra `FACT_BET` por
  `status IN ('won', 'lost', 'void')`, nunca `'pending'`.
- RN08 — dashboards recalculam métricas dinamicamente conforme filtros aplicados.
- RN09 — ROI por mercado/esporte/casa considera exclusivamente as apostas daquele agrupamento.

> **Implementado em `feat-004`**: `FactBetRepository` (`adapter/out/persistence`) expõe 4 métodos
> de agregação bruta (`aggregateOverall`/`aggregateBySport`/`aggregateByMarket`/
> `aggregateByBettingHouse`) via JPQL com `SUM`/`COUNT`, filtrando `status <> PENDING` (equivalente
> a RN06 já que `BetStatus` só tem 4 valores) — `FactBetJpaEntity` não tem `@ManyToOne` para as
> dimensões (colunas UUID simples), então a query segmentada faz join explícito por condição
> (`FROM FactBetJpaEntity f, DimSportJpaEntity s WHERE f.sportId = s.id`) para trazer o nome.
> `CalculateMetricsService` (`application`) transforma o agregado bruto (`BetAggregate`) em
> métricas de negócio (`BetMetrics`): `roi = netProfit / totalStaked`, `taxa de acerto =
> wonCount / settledCount` — **`settledCount` inclui apostas `void`** (RN06 as inclui na
> agregação), então uma aposta devolvida conta no denominador da taxa de acerto sem contar como
> vitória nem derrota (decisão de interpretação, RN04/RN09 não desambiguam o denominador).
> Divisão por zero (nenhuma aposta liquidada ainda) retorna `BigDecimal.ZERO`, não lança exceção.
> Sem endpoint HTTP ainda (`feat-006`) nem cache (`feat-005`) — métricas verificadas por teste
> direto (integração no repositório, unitário no cálculo).

> **Implementado em `feat-006`**: RF11/RN08 completos — `GET /api/v1/statistics` (rota já exigida
> pelo `TenantSchemaFilter` existente, sem middleware novo) aceita 7 filtros opcionais
> (`bettingHouseId`/`sportId`/`leagueId`/`marketId`/`tipsterId`/`from`/`to`, ver
> [[API-CONTRACTS]]) e responde um bundle único (`StatisticsDashboard`) com as 5 vistas de uma vez
> — decisão do usuário (2026-09-07) entre bundle único, resposta mínima com `groupBy` ou
> endpoints separados por segmento. `StatisticsFilter` (todos os campos opcionais,
> `StatisticsFilter.none()` = sem filtro) substituiu as assinaturas sem parâmetro de `feat-004`/
> `feat-005` em vez de manter dois conjuntos paralelos de método. Sem nenhum filtro, a resposta
> vem do cache-aside de `feat-005`; qualquer filtro presente bypassa o cache (as chaves só cobrem
> a vista sem filtro nenhum por tenant) e calcula direto — o campo `monthly` do bundle é sempre
> calculado direto (nunca via o cache por mês de `feat-005`), por ser uma agregação `GROUP BY`
> barata e de baixa cardinalidade. Filtro por `from`/`to` junta `DIM_DATE` e compara
> `FUNCTION('make_date', ...)` (Postgres) contra os limites — **achado real**: o Postgres não
> consegue inferir o tipo de um parâmetro `null` usado só dentro de `CAST`/`FUNCTION`
> (`could not determine data type of parameter`), corrigido substituindo `from`/`to` ausentes por
> limites-sentinela (`1900-01-01`/`2999-12-31`) em vez de outro predicado `IS NULL OR` — ver
> `JpaFactBetRepository`. **Fecha o backlog planejado deste serviço** (`feat-001`..`feat-006`,
> `epic-004` da raiz).

## Ver também

- [[bets-service]] — produtor de `BetCreated` e `BetSettled`.
- [[web]] — consome `GET /api/v1/statistics` para os dashboards.
- [[infra]] — RabbitMQ (consumidor), Redis (cache).
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
