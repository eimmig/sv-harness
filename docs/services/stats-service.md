---
tags: [service, backend]
---

# stats-service

Java 25 + Spring Boot 4.x. Ver [[arquitetura]] para o panorama geral e [[requisitos]] para
RF/RN completos. Harness de código em `services/stats-service/CLAUDE.md`.

## Responsabilidade

RF09 (gerar métricas), RF10 (parte de performance dos dashboards), RF11 (suporte a filtros).

## Consumo de eventos

Consome dois eventos do RabbitMQ, publicados por [[bets-service]] (ver [[contratos-de-api]] para os
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
aposta (ver [[arquitetura]] seção "Fluxos dinâmicos"). Falhas consecutivas vão para a DLQ (ver
[[infra]]).

> **Implementado em `feat-001.9`/`feat-002`/`feat-003`**: o listener (`@RabbitListener` ligado à
> fila real `stats.bet-events`, mesmo nome/argumentos de `infra/rabbitmq/definitions.json`) valida
> cada mensagem contra o JSON Schema do `eventType` correspondente (cópia vendorizada em
> `src/main/resources/contracts/`, lida em runtime — diferente da cópia só-de-teste do lado
> publicador em `bets-service`, ver [[contratos-de-api]] "Cópias vendorizadas do schema") antes de
> processar. Mensagem que não bate com o schema, ou cujo `tenantId` não resolve para um tenant
> provisionado, é rejeitada sem reenfileirar (`AmqpRejectAndDontRequeueException`, não o
> `x-delivery-limit`/retry — ver [[convencoes]]) e cai direto na DLQ — nos dois casos a falha é
> permanente, retentar não ajuda. `BetCreated` faz *insert* em `FACT_BET` (`status: pending`) só
> quando a linha ainda não existe — se `BetSettled` já chegou primeiro (mensagens fora de ordem),
> `BetCreated` é um no-op além de marcar o evento processado, nunca reverte a liquidação já
> aplicada. `BetSettled` sempre faz *upsert* de verdade (carrega a linha existente via `findById`
> e muta a instância rastreada pelo Hibernate — `FactBetJpaEntity.applyFrom`, não reconstrói a
> entidade do zero, que tentaria `INSERT` de novo e falharia por chave duplicada; ver
> [[convencoes]] "Atualizar uma linha já persistida"). As 6 dimensões são resolvidas por
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
métricas (é exatamente o teste de idempotência exigido em [[testes]]). Fiel ao passo "Verificar
EVENTOS_PROCESSADOS" do diagrama de sequência do TCC1 (`docs/diagrams/flows/event-consumption.png`
— nome traduzido para inglês nesta revisão, mesma decisão de "tudo em inglês" — o diagrama
conceitual mais antigo do TCC1 já usava `PROCESSED_EVENT` em inglês para essa mesma tabela, então
esta tradução também é mais fiel ao material original), que não tinha uma tabela equivalente
sobrevivido no ERD final — revivida aqui deliberadamente porque o requisito de idempotência
(testes.md) não tem outro mecanismo definido. Ver [[modelo-de-dados]] seção "Evolução do modelo" para
o histórico completo dessa decisão.

## Multi-tenancy

Schema isolado por tenant (**Schema-per-Tenant**, `tenant_<slug>`) — mesmo padrão de
[[bets-service]] e [[auth-service]] (ver [[DECISIONS-LOG]]). O schema de conexão é resolvido a
partir do header `X-Tenant-Id` (ver [[contratos-de-api]]) tanto no consumo de evento (`tenantId` do
envelope) quanto nas consultas de `GET /api/v1/statistics`, e migrado sob demanda antes de
processar (Flyway lazy, ver [[convencoes]]).

## Modelo de dados (OLAP — esquema estrela, isolado por cliente, banco separado do OLTP)

Ver [[modelo-de-dados]] para o ERD completo (Mermaid + PNG original do TCC1).

- Fato `FACT_BET` (id, dateId FK, bettingHouseId FK, sportId FK, leagueId FK, marketId FK,
  tipsterId FK, stake decimal, profit decimal nullable, isWin boolean nullable, status varchar,
  betCount int). `status` armazena `pending`/`won`/`lost`/`void` (inglês, ver
  [[contratos-de-api]]). `status` e `profit`/`isWin` nullable são uma extensão sobre o ERD original
  do TCC1 (que não tinha `status`) — necessária para RN06 (excluir `pending` das agregações) e
  para o padrão insert-then-upsert descrito acima.
- Dimensões: `DIM_DATE` (day, month, year, quarter, dayOfWeek), `DIM_BETTING_HOUSE`,
  `DIM_SPORT`, `DIM_LEAGUE`, `DIM_MARKET`, `DIM_TIPSTER` (todas `id`+`name`). `id` é o mesmo uuid
  do catálogo em `bets-service`; `name` vem denormalizado do payload do evento
  (`bettingHouseName`/`sportName`/etc., ver [[contratos-de-api]]) — este serviço nunca consulta
  `bets-service` de volta para resolver nome (ver [[modelo-de-dados]]).
- `PROCESSED_EVENT` (id, eventId, processedAt) — controle técnico de idempotência, não é uma
  dimensão nem participa do esquema estrela.

## Cache Redis (Cache-Aside)

O próprio serviço decide quando ler/gravar cache — não é responsabilidade de um proxy externo.
Chaves padronizadas (inglês, mesma decisão de nomenclatura técnica — ver [[contratos-de-api]]):

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
> uma divergência real entre [[arquitetura]], cujo fluxo já dizia que `stats-service` "atualiza
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
> [[contratos-de-api]]) e responde um bundle único (`StatisticsDashboard`) com as 5 vistas de uma vez
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

## Extensão do dashboard consolidado — PRE/LIVE, odd média, vitórias/derrotas (`epic-014` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, especificação do
dashboard). `overall`/`bySport`/`byMarket`/`byBettingHouse`/`monthly` de
`GET /api/v1/statistics` (`feat-006`) ganham `wonCount`/`lostCount`/`voidCount` (contagens brutas
por trás do `winRate` já existente), `preCount`/`liveCount` e `avgOdd` — fórmulas em
[[estatisticas]], forma da resposta em [[contratos-de-api]].

Duas dependências deste serviço sobre `epic-013` (`bets-service`, mesmo pedido):

- `FACT_BET.betType` (nullable) — só existe se `BET.betType` virar enum `PRE`/`LIVE` primeiro
  (`epic-013`); contar por texto livre fragmentaria o agrupamento. Gravado só no *insert* de
  `BetCreated` (mesmo padrão de `team1Id`/`team2Id`/`odd`, `epic-011`), nunca sobrescrito pelo
  *upsert* de `BetSettled` (payload daquele evento não carrega `betType`).
- `odd` persistida em `FACT_BET` — **coluna compartilhada com `epic-011`**: `epic-011` (`feat-012`)
  implementou primeiro, então `epic-014` só reaproveitou a coluna existente para `avgOdd`, sem
  migração nova.
- **`byBetType` novo** (acrescentado 2026-09-10, pedido da tela "Visão geral" de [[web]]
  `epic-021`): 6º segmento de `GET /api/v1/statistics`, mesmo formato dos outros 5
  (`bySport`/`byMarket`/`byBettingHouse`/`byLeague`/`byTipster`) — só que com 2 buckets fixos
  (`PRE`/`LIVE`) em vez de um por linha de catálogo. `betType` nunca vira query param de filtro,
  só esse agrupamento pronto.

> **Implementado em `stats-service feat-015`** (3 subtasks): `feat-015.1` grava `betType` só no
> *insert* de `BetCreated` e preserva o valor já gravado no *upsert* de `BetSettled` (mesmo padrão
> exato de `dateId`, já que o payload de `BetSettled` não carrega `betType`) — enum `BetType`
> (`PRE`/`LIVE`) com `AttributeConverter` dedicado (`@Converter(autoApply = true)`), mesmo padrão
> de `BetStatusAttributeConverter`. `feat-015.2` estende as 5 queries JPQL existentes com os campos
> novos — achado do plan review: toda comparação de enum (`f.status = ...`/`f.betType = ...`) usa
> `@Param` tipado (`BetStatus`/`BetType`), nunca literal de string solto, para garantir que o
> `AttributeConverter` seja aplicado (o codebase já evitava esse padrão desde `feat-006`, aqui só
> ficou explícito por que). `feat-015.3` adiciona o segmento `byBetType` reaproveitando o mesmo
> `record` `BetMetrics`/`SegmentedBetMetrics` dos outros 5 segmentos (não um tipo apartado) —
> exigiu mudar `dimensionId` de `UUID` para `String` em `SegmentedBetAggregate`/
> `SegmentedBetMetrics` (único segmento sem uuid de catálogo por trás, ver [[contratos-de-api]]), os
> 3 segmentos existentes convertem via `.toString()` na fronteira do adapter
> (`JpaFactBetRepository`). Cache-aside estendido com chave própria (`segment:byBetType`),
> evictada junto das outras 4 chaves — mesma simetria de `bySport`/`byMarket`/`byBettingHouse`, não
> um caso especial como `monthly` (que nunca é cacheado).

**Saldo inicial/final do período e "unidades apostadas" NÃO entram neste serviço** — decisão de
arquitetura desta sessão: saldo é dado transacional (domínio de `bets-service`, que já mantém
`initialBalance`/`TRANSACTION`/`BET_RESULT`); replicar isso pro esquema estrela via eventos novos
(`BettingHouseCreated`/`TransactionCreated`) foi avaliado e descartado por complexidade
desproporcional — `bets-service` ganha um endpoint parametrizado no tempo em vez disso
(`GET /api/v1/bankroll/balance?at=`, `epic-013`). "Unidades apostadas" é calculado inteiramente
no cliente (`web`, `epic-015`), combinando `totalStaked` (daqui) com saldo e `unitPercent`
(`bets-service`). Ver [[estatisticas]] para o racional completo.

## Segmentos byLeague/byTipster (`epic-018` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, menu por cadastro
em [[web]]). `GET /api/v1/statistics` ganha `byLeague`/`byTipster`, mesmo formato de
`bySport`/`byMarket`/`byBettingHouse` (`feat-006`) — até aqui `leagueId`/`tipsterId` só
estreitavam os outros segmentos como filtro (decisão original, ver plan review de `web feat-006`),
nunca tiveram o próprio agrupamento. Mesma mecânica de agregação já usada pelos 3 segmentos
existentes (`SegmentedBetMetrics`), sem schema novo (`DIM_LEAGUE`/`DIM_TIPSTER` já existem desde
`epic-004`).

> **Implementado em `stats-service feat-017`** sem divergência do planejado. `aggregateByLeague`
> é mirror exato de `aggregateBySport`/`aggregateByMarket`; `aggregateByTipster` exclui
> `f.tipsterId IS NULL` (campo opcional em `FACT_BET`, diferente de `leagueId`, sempre presente),
> mesmo padrão de `aggregateByBetType.betType IS NOT NULL`. Cache-aside estendido com 2 chaves
> novas (`segment:league`/`segment:tipster`) — `evict()` passou a incluir as 2 junto das
> existentes, ponto sinalizado no plan review e coberto por teste de integração dedicado
> (`RedisMetricsCacheRepositoryIntegrationTest`) para não regredir silenciosamente no futuro.

## Quebra diária (`epic-016` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal do usuário — layout livre, só o conteúdo importa). `GET
/api/v1/statistics/daily` — mesmos filtros de `GET /api/v1/statistics`, `groupBy` por dia em vez
de mês (`DIM_DATE.day`/`month`/`year` já existe, mesma agregação já usada para `MonthlyBetMetrics`
desde `feat-004`, só troca a chave de agrupamento). Array esparso — só dias com pelo menos 1
aposta liquidada, sem preencher os dias vazios (isso fica pro cliente, ver [[web]] "Relatório do
período"). Sem nenhuma dependência nova sobre `epic-013`/`epic-014` (não usa `betType`/`odd`/
saldo) — só `epic-004` (`done`). Ver [[estatisticas]] para o formato da resposta e
[[contratos-de-api]] para o contrato completo.

> **Implementado em `stats-service feat-016`** sem divergência do planejado.
> `FactBetRepository.aggregateByDay` usa `FUNCTION('make_date', d.year, d.month, d.day)` no
> `SELECT` combinado com `GROUP BY` nas colunas cruas — combinação nova neste codebase
> (`aggregateByMonth` já usava `GROUP BY`, `findOrderedSettledProfits` já usava `FUNCTION()`, nunca
> os dois juntos), confirmada funcional pelo teste de integração real na primeira tentativa
> (fallback client-side previsto no plan review não foi necessário) — ver
> [[convencoes]] "JPQL". `calculateDaily` reaproveita a regra RN04 de `roi=ZERO` via helper
> privado `roiOf`, extraído de `toMetrics` (elimina duplicação entre os dois cálculos).

## Busca de estatísticas por combinação (`epic-011` da raiz, done)

`GET /api/v1/statistics/search` (ver [[contratos-de-api]]) — motor de decisão pré-aposta: usuário
escolhe esporte+liga (obrigatórios) e opcionalmente time/casa/mercado/tipster/período, recebe
ROI, taxa de acerto, odd média, drawdown máximo e Índice de Sharpe simplificado daquela
combinação exata, mais uma série temporal de lucro acumulado. Fórmulas e fundamentação teórica
em [[estatisticas]] — não duplicadas aqui.

Duas mudanças de schema que este endpoint pressupõe, sobre o modelo de `feat-002`/`feat-004`:

- **`DIM_TEAM` nova** (ver [[modelo-de-dados]]): resolvida por nome (chave natural), não por id vindo
  do evento — `team1`/`team2` não têm catálogo em `bets-service` (texto livre por aposta). `
  FACT_BET` ganha `team1Id`/`team2Id` (nullable); filtro por `teamId` casa contra qualquer um dos
  dois. **Atualizado no dia seguinte (`feat-013`)**: a chave natural passou de `name` sozinho
  para `(name, sportId)` composta — ver seção "Times escopados por esporte" abaixo.
  **Atualizado de novo (`feat-018`, 2026-09-16, `epic-024`)**: desde que `bets-service feat-017`
  introduziu um catálogo `TEAM` real, `BetCreated` ganhou `team1Id`/`team2Id` (aditivo, nullable)
  e `BetSettled` ganhou `team1Id`/`team1Name`/`team2Id`/`team2Name` (novo, nunca existiu antes).
  `DimensionResolver.resolveTeam(UUID id, String name, UUID sportId)` passou a considerar o id do
  evento, mas com **precedência da chave natural**: `(name, sportId)` é buscada primeiro — se já
  existir, o id já gravado vence (mesmo que diferente do id do evento), só criando linha nova com
  o id do evento quando o time é visto pela primeira vez aqui. Isso evita violar
  `uq_dim_team_name_sport` quando um time resolvido localmente antes desta mudança (id gerado por
  este serviço, `epic-011`) reaparece com o id real do catálogo — sem essa precedência, a segunda
  tentativa de `INSERT` colidiria com a linha antiga (mensagem "envenenada" permanente, esgotando
  as 3 tentativas do `spring-retry` de `feat-010` e morta-letrando sem se recuperar sozinha,
  diferente do residual P2 abaixo que se auto-recupera). **Assimetria resultante, aceita e
  documentada, não corrigida por backfill** (mesmo precedente de `V20260910130000` — catálogo
  nunca usado em tenant real): `DIM_TEAM.id` só passa a coincidir com o catálogo real de
  `bets-service` para times vistos pela primeira vez depois desta feature; times antigos mantêm o
  id local para sempre. `BetSettledEvent.team1()`/`team2()` (`String`, nunca populados por nenhum
  publicador real — `BetSettled` nunca carregou `team1`/`team2` antes desta mudança) foram
  substituídos pelos campos reais `team1Id`/`team1Name`/`team2Id`/`team2Name`; `processSettled`
  resolve/grava a dimensão quando o evento os traz (cobre `BetSettled` chegando antes do
  `BetCreated` correspondente) e **preserva** o `team1Id`/`team2Id` já gravado quando o evento não
  traz (mesmo padrão de `dateId`/`betType` acima) — liquidar uma aposta nunca apaga o time já
  resolvido no *insert*.
- **`odd` persistida em `FACT_BET`** (nullable): já trafegava em `BetCreated`/`BetSettled`
  (`odd`, campo obrigatório do evento) mas nunca era gravada — sem requisito anterior que
  precisasse. `DimensionResolver` e os *listeners* de evento (`feat-001.9`/`feat-002`/`feat-003`)
  precisam gravar `team1Id`/`team2Id`/`odd` no mesmo *insert*/*upsert* que já fazem para as
  outras 5 dimensões — não é uma tabela nova de consumo, é campo a mais na mesma linha.

**Achado do `Persistence Auditor` (P2, aceito como risco residual)**: `DimensionResolver.resolveTeam`
tem a mesma corrida check-then-act (`findByName` → `save`, não atômico) já presente nas outras 5
dimensões (`existsById` → `save`) — mas com exposição maior na prática: as outras 5 têm `id`
determinístico vindo de `bets-service` (colisão só se dois eventos citarem o MESMO catálogo pela
primeira vez ao mesmo tempo), enquanto `DIM_TEAM` não tem catálogo — o mesmo nome de time aparece
em várias apostas diferentes desde o início. Falha (violação de `uq_dim_team_name`) derruba o
processamento daquela mensagem, mas o mecanismo de retry/DLQ já validado em `epic-007` a
reprocessa com sucesso (na segunda tentativa, `findByName` já encontra a linha commitada pela
transação concorrente) — auto-recuperável, sem perda de dado. Não corrigido agora: uma correção de
verdade (`INSERT ... ON CONFLICT`) mudaria as 6 dimensões de uma vez, fora do escopo pontual desta
feature.

`maxDrawdown`/`sharpeRatio` não são agregados SQL simples (`SUM`/`AVG`/`COUNT`) como o resto do
serviço — exigem a série de `profit` ordenada por `betDate` (data do jogo — ver [[estatisticas]])
das apostas liquidadas do recorte, iterada em memória (`domain`, calculador puro sem I/O, ver
"Cálculo de decisão" abaixo) depois de uma única consulta ordenada ao repositório. Sem
cache-aside (ver [[contratos-de-api]] — espaço de combinações grande demais).

**Achado real do plan review de `epic-011`, corrigido antes do código**: `processSettled`
(upsert de `BetSettled`) recalculava `dateId` a partir de `event.settledAt()` — sobrescrevendo o
`dateId` correto (resolvido de `betDate` no *insert* de `processCreated`) com a data de
liquidação, toda vez que uma aposta liquidava. Como `betDate` é a data do jogo (não de registro
nem de liquidação, decisão do usuário), isso corrompia silenciosamente a granularidade mensal já
usada pelo dashboard consolidado (`monthly`, `feat-006`) para qualquer aposta liquidada em mês
diferente do jogo — não só a série nova desta feature. Corrigido: `processSettled` preserva o
`dateId` já existente na linha (não recalcula) quando `BetCreated` já processou antes. Residual
aceito: se `BetSettled` chegar antes do `BetCreated` correspondente (mensagens fora de ordem), a
linha ainda nasce com `dateId` derivado de `settledAt` (sem `betDate` no payload de `BetSettled`)
até `BetCreated` processar depois — `BetCreated` nunca sobrescreve uma liquidação já aplicada
(comportamento existente desde `feat-003`), então esse `dateId` de estimativa nunca é corrigido
retroativamente nesse caso raro. Corrigir isso de verdade exigiria propagar `betDate` também no
evento `BetSettled` (mudança de contrato cross-service com `bets-service`) — fora do escopo de
`epic-011`.

### Times escopados por esporte (`feat-013`, addendum do dia seguinte)

Planejando a tela "Buscar Estatísticas" em [[web]] (`epic-012`), achado real: `DIM_TEAM` não
tinha nenhum endpoint de listagem — sem catálogo em `bets-service`, o frontend não tinha como
saber quais `teamId` existiam pra montar o autocomplete de time. Decisão do usuário: em vez de só
adicionar a listagem, `DIM_TEAM` ganha `sportId` (FK `DIM_SPORT`) — a chave natural vira
**`(name, sportId)`** composta, porque o mesmo nome de time pode existir em esportes diferentes
(ex. clubes com time de futebol e de basquete). `DimensionResolver.resolveTeam(name, sportId)`
resolve pela chave composta; o achado do `Persistence Auditor` acima (corrida check-then-act)
continua valendo, sem mudança de severidade — mesmo mecanismo, só com um campo a mais na chave.

`GET /api/v1/statistics/teams?sportId=<uuid>` (ver [[contratos-de-api]]) lista `[{id, name}]`
escopado por esporte, `sportId` obrigatório (mesma `MissingRequiredStatisticsFilterException` de
`GET /api/v1/statistics/search`) — troca de esporte na tela refiltra a lista, nunca mistura times
de esportes diferentes. `ListTeamsUseCase`/`ListTeamsService` mantêm o limite hexagonal (
`adapter/in` nunca chama `port/out` direto), mesmo padrão de `SearchStatisticsUseCase`.

## Ver também

- [[bets-service]] — produtor de `BetCreated` e `BetSettled`.
- [[web]] — consome `GET /api/v1/statistics` para os dashboards.
- [[infra]] — RabbitMQ (consumidor), Redis (cache).
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
