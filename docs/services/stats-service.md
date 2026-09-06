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

> **Implementado em `feat-001.9`**: o listener técnico (`@RabbitListener` ligado à fila real
> `stats.bet-events`, mesmo nome/argumentos de `infra/rabbitmq/definitions.json`) já valida cada
> mensagem contra o JSON Schema do `eventType` correspondente (cópia vendorizada em
> `src/main/resources/contracts/`, lida em runtime — diferente da cópia só-de-teste do lado
> publicador em `bets-service`, ver [[API-CONTRACTS]] "Cópias vendorizadas do schema") antes de
> processar. Mensagem que não bate com o schema é rejeitada sem reenfileirar
> (`AmqpRejectAndDontRequeueException`, não o `x-delivery-limit`/retry — ver [[CONVENTIONS]]) e
> cai direto na DLQ. **Ainda sem persistência** (insert/upsert em `FACT_BET` descritos acima e a
> tabela `PROCESSED_EVENT` chegam em `feat-002`/`feat-003`) — por enquanto só prova que o
> consumidor recebe, valida e loga corretamente.

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
  `DIM_SPORT`, `DIM_LEAGUE`, `DIM_MARKET`, `DIM_TIPSTER`.
- `PROCESSED_EVENT` (id, eventId, processedAt) — controle técnico de idempotência, não é uma
  dimensão nem participa do esquema estrela.

## Cache Redis (Cache-Aside)

O próprio serviço decide quando ler/gravar cache — não é responsabilidade de um proxy externo.
Chaves padronizadas (inglês, mesma decisão de nomenclatura técnica — ver [[API-CONTRACTS]]):

- `tenant:{tenantId}:dashboard:consolidated` — ROI total, taxa de acerto macro, saldo unificado.
- `tenant:{tenantId}:stats:monthly:{year}_{month}` — série histórica para gráficos de linha.
- `tenant:{tenantId}:segment:{sport|market}` — ranking de performance por segmento.

> **Corrigido em 2026-08-02** (ver [[DECISIONS-LOG]]): as chaves eram `user:{id}:...`, coerente
> com o modelo antigo (tenant = usuário). Como `FACT_BET` é isolado por schema de **tenant**, não
> tem coluna de usuário, e é compartilhado por todos os usuários daquela organização, a chave
> correta é por `tenantId`, não por `userId` — do contrário dois usuários do mesmo tenant veriam
> caches (e portanto dashboards) diferentes sem motivo.

Meta de performance (RNF03): resposta de dashboard < 300 ms (depende do cache estar quente).

## Regras de negócio

- RN04 — `ROI agregado = lucro líquido acumulado / valor total investido`.
- RN06 — toda agregação (RN04, RN09, dashboards) filtra `FACT_BET` por
  `status IN ('won', 'lost', 'void')`, nunca `'pending'`.
- RN08 — dashboards recalculam métricas dinamicamente conforme filtros aplicados.
- RN09 — ROI por mercado/esporte/casa considera exclusivamente as apostas daquele agrupamento.

## Ver também

- [[bets-service]] — produtor de `BetCreated` e `BetSettled`.
- [[web]] — consome `GET /api/v1/statistics` para os dashboards.
- [[infra]] — RabbitMQ (consumidor), Redis (cache).
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
