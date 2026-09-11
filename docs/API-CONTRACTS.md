---
tags: [conventions, api, contracts]
---

# Contratos de API e de eventos

Convenções para que os três serviços Java exponham APIs consistentes entre si, e para o
contrato do único evento assíncrono do sistema. Ver [[ARCHITECTURE]] para o panorama dos fluxos
e [[CONVENTIONS]] para arquitetura/código.

## Convenções REST

> **Tudo em inglês** — decisão explícita do usuário (2026-08-01): rotas, query params, nomes de
> evento e valores de enum na API/eventos são sempre em inglês, sem exceção. Isso fecha uma
> inconsistência que existia até aqui: os nomes de entidade (`BET`, `USER`, `BETTING_HOUSE` etc.)
> e os nomes de campo (`stake`, `odd`, `status`) já eram em inglês desde os ERDs originais do
> TCC1, mas as rotas REST e os nomes de evento tinham sido documentados em português numa
> primeira passada deste harness — corrigido nesta revisão. O texto descritivo do vault
> (nomes de RF/RN, explicações) continua em português — só a **superfície técnica** (o que
> trafega na rede/no código) é inglês.

- **Base path**: `/api/v1/...` em todos os serviços — versionamento explícito desde o início
  evita ter que retrofitar depois.
- **Nomenclatura**: substantivos no plural, kebab-case, sempre em inglês (`/api/v1/betting-houses`,
  `/api/v1/bets`, `/api/v1/transactions`, `/api/v1/statistics`, `/api/v1/users`), nunca verbos na
  URL.
- **Paginação**: query params `page` (0-indexed) e `size` (default 20, máx 100) em toda listagem
  (histórico de apostas, movimentações); resposta envelopada
  `{ "content": [...], "page": 0, "size": 20, "totalElements": N, "totalPages": N }`. **Clampar
  `page`/`size` no controller antes de repassar ao repositório** (`page = max(page, 0)`,
  `size = min(max(size, 1), 100)`) — gotcha real encontrado em `bets-service feat-002`: o
  `PageRequest.of()` do Spring Data lança `IllegalArgumentException` (vira 500 não tratado, não
  400) para `page` negativo ou `size` não positivo; mais barato clampar no controller do que
  tratar a exceção. Mesmo padrão a reaproveitar em qualquer endpoint paginado novo (`bets-service
  feat-007`, `stats-service`).
- **Filtros** (RF11, RN08): query params em inglês, nomeados igual ao campo do domínio (**com**
  sufixo `Id` para referências a catálogo/entidade — `bettingHouseId`, `sportId`, `leagueId`,
  `marketId`, `tipsterId` — não abreviados nem sem o sufixo), mais `from`/`to` para intervalo de
  data: `?bettingHouseId=<uuid>&sportId=<uuid>&from=2026-01-01T00:00:00Z&to=2026-01-31T23:59:59Z`
  — mesmo vocabulário usado em `bets-service` (`GET /api/v1/bets`, `feat-007`) e reaproveitável por
  `stats-service` para os mesmos conceitos. Nomenclatura confirmada contra o código real já
  enviado (`bets-service feat-003`, `TransactionsController.list`, parâmetro `bettingHouseId`) —
  um exemplo anterior desta nota usava nomes sem o sufixo (`?sport=football`), nunca implementado
  e corrigido aqui para não divergir do que o serviço realmente aceita.
- **`GET /api/v1/statistics` (`stats-service`, RF11/RN08, `feat-006`)**: os mesmos 7 filtros
  acima, mas `from`/`to` usam **data sem hora** (`yyyy-MM-dd`, ex. `from=2026-01-01&to=2026-01-31`)
  — diferente do `GET /api/v1/bets` de `bets-service` (timestamp completo, granularidade real de
  aposta), porque `FACT_BET` é OLAP e a dimensão de data (`DIM_DATE`) só guarda dia/mês/ano, sem
  hora; um `from`/`to` com timestamp completo sugeriria uma precisão que o modelo não tem.
  Resposta é um **bundle único** (decisão do usuário, 2026-09-07, escolhida entre bundle
  único/resposta mínima com `groupBy`/endpoints separados por segmento — a segunda e a terceira
  opção exigiriam múltiplas chamadas por atualização de dashboard, contra a premissa de
  `docs/services/web.md` de que cada mudança de filtro é uma única consulta a esta rota):
  ```json
  {
    "overall": { "totalStaked": 1000.00, "netProfit": 150.00, "roi": 0.15, "winRate": 0.55, "settledCount": 42 },
    "bySport": [ { "dimensionId": "...", "dimensionName": "Soccer", "metrics": { "totalStaked": 600.00, "netProfit": 90.00, "roi": 0.15, "winRate": 0.55, "settledCount": 25 } } ],
    "byMarket": [ { "dimensionId": "...", "dimensionName": "Over/Under", "metrics": { "totalStaked": 400.00, "netProfit": 60.00, "roi": 0.15, "winRate": 0.55, "settledCount": 17 } } ],
    "byBettingHouse": [ { "dimensionId": "...", "dimensionName": "Bet365", "metrics": { "totalStaked": 1000.00, "netProfit": 150.00, "roi": 0.15, "winRate": 0.55, "settledCount": 42 } } ],
    "monthly": [ { "year": 2026, "month": 1, "metrics": { "totalStaked": 200.00, "netProfit": 30.00, "roi": 0.15, "winRate": 0.5, "settledCount": 8 } } ]
  }
  ```
  Cada item de `bySport`/`byMarket`/`byBettingHouse`/`monthly` aninha as métricas sob `metrics`
  (em vez de achatadas ao lado de `dimensionId`/`dimensionName`/`year`/`month`) — reaproveita os
  mesmos `record`s de domínio já usados internamente desde `feat-004`/`feat-005`
  (`SegmentedBetMetrics`, `MonthlyBetMetrics`), sem duplicar um DTO HTTP só para achatar o
  formato. Achado do self-review de `feat-006.3`: o exemplo apresentado ao usuário na decisão do
  formato (`AskUserQuestion`, acima) mostrava os campos achatados só para ilustrar a escolha
  *bundle único vs. endpoints separados* — a resposta real, aninhada, não muda essa decisão.
  Sem nenhum dos 7 filtros, a resposta vem do cache-aside de `feat-005` (RNF03, meta < 300 ms com
  cache quente); qualquer filtro presente bypassa o cache (as chaves só cobrem a vista sem filtro
  nenhum por tenant) e calcula direto contra `FACT_BET` — ver [[stats-service]].
- **`overall` de `GET /api/v1/statistics` ganha campos novos** (`stats-service`, `epic-014` da
  raiz, extensão do dashboard consolidado, 2026-09-10): `wonCount`/`lostCount`/`voidCount`
  (contagens brutas — `winRate` já existente continua sendo a fração), `preCount`/`liveCount`
  (a partir de `BET.betType`, que vira enum `PRE`/`LIVE` em `bets-service feat-013` — apostas com
  `betType` nulo não entram em nenhum dos dois), `avgOdd` (`AVG(odd)` do recorte liquidado, reusa
  a coluna `odd` de `FACT_BET` já introduzida por `epic-011`):
  ```json
  {
    "overall": {
      "totalStaked": 1000.00, "netProfit": 150.00, "roi": 0.15, "winRate": 0.55, "settledCount": 42,
      "wonCount": 23, "lostCount": 18, "voidCount": 1,
      "preCount": 30, "liveCount": 10,
      "avgOdd": 1.92
    }
  }
  ```
  Os mesmos campos novos aninham em `bySport`/`byMarket`/`byBettingHouse`/`byLeague`/`byTipster`/
  `monthly` também (RN09 já aplica as métricas existentes por segmento — os campos novos seguem
  a mesma regra, sem exceção documentada). Ver [[STATISTICS]] para as fórmulas.
- **`byBetType` novo em `GET /api/v1/statistics` (`stats-service`, `epic-014` da raiz, pedido da
  tela "Visão geral" de `epic-021`, 2026-09-10)**: 6º segmento, mesmo formato dos outros 5 — só
  que com exatamente 2 itens fixos (`PRE`/`LIVE`, apostas sem `betType` classificado não entram
  em nenhum dos dois):
  ```json
  { "byBetType": [
    { "dimensionId": "PRE", "dimensionName": "PRE", "metrics": { "totalStaked": 700.00, "netProfit": 100.00, "roi": 0.14, "winRate": 0.55, "settledCount": 30, "wonCount": 17, "lostCount": 13, "voidCount": 0, "preCount": 30, "liveCount": 0, "avgOdd": 1.90 } },
    { "dimensionId": "LIVE", "dimensionName": "LIVE", "metrics": { "totalStaked": 300.00, "netProfit": 50.00, "roi": 0.17, "winRate": 0.58, "settledCount": 12, "wonCount": 7, "lostCount": 5, "voidCount": 0, "preCount": 0, "liveCount": 12, "avgOdd": 2.10 } }
  ] }
  ```
  Implementado (`stats-service feat-015.3`) reaproveitando o mesmo `record` `BetMetrics` dos
  outros 5 segmentos (`SegmentedBetMetrics`) em vez de um tipo apartado — `preCount`/`liveCount`
  aparecem também aqui, ainda que triviais dentro do próprio bucket (`PRE` sempre tem
  `preCount == settledCount` e `liveCount == 0`, e vice-versa): evita duplicar
  `SegmentedBetMetrics` só para omitir 2 campos redundantes-mas-inofensivos, mesma decisão
  registrada no `plan_review` daquela feature.
  `betType` nunca é query param de filtro — só um agrupamento pronto, `dimensionId`/
  `dimensionName` carregam o próprio valor do enum em vez de um `uuid` (único segmento sem FK de
  catálogo por trás).
- **`GET /api/v1/bankroll/balance` (`bets-service`, `epic-013` da raiz, 2026-09-10)**: saldo
  consolidado — soma de **todas as casas de apostas do tenant**, sem filtro por
  `bettingHouseId` (decisão do usuário: a métrica é sempre agregada, nunca por casa individual).
  Query param opcional `at` (`yyyy-MM-dd`, default hoje) — saldo naquele instante, não só o
  corrente: `initialBalance` de todas as casas + transações (`createdAt <= at`) + `profit` das
  apostas liquidadas (`settledAt <= at`, **não** `betDate` — ver [[STATISTICS]] "Saldo
  inicial/final do período"). Fecha o gap já sinalizado em [[bets-service]] `feat-005` ("RF07 não
  ganhou endpoint de saldo consolidado próprio") — reaproveita a mesma fórmula que
  `GET /api/v1/betting-houses` já usa por casa (`balance = initialBalance + depósitos - saques +
  profit líquido`), só que somada entre casas e parametrizável no tempo:
  `?at=2026-09-01`
  ```json
  { "at": "2026-09-01", "balance": 4820.50 }
  ```
  Consumido pelo dashboard (`web`, `epic-015`) 2x por consulta (`from`/`to` do filtro de período)
  para os cards de saldo inicial/final, e 1x sem `at` (saldo atual) para o cálculo client-side de
  "unidades apostadas".
- **`GET`/`PATCH /api/v1/settings` (`bets-service`, `epic-013` da raiz, 2026-09-10)**:
  configuração por tenant, linha única (`TENANT_SETTINGS`, ver [[DATA-MODEL]]). Só `unitPercent`
  por enquanto (`decimal`, default `0.01`) — "unidade" de banca como percentual configurável
  (decisão do usuário: não é valor fixo em R$ nem campo por aposta). `PATCH` restrito a
  `X-User-Role: admin` (header novo do Gateway, ver seção de headers acima — `bets-service` não
  tem tabela `USER` pra resolver role localmente como `auth-service` faz), `403` caso contrário:
  ```json
  { "unitPercent": 0.01 }
  ```
  Consumido pelo dashboard (`web`, `epic-015`) para calcular "unidades apostadas" e por uma tela
  de configuração (admin-only) para editar o percentual.
- **`byLeague`/`byTipster` novos em `GET /api/v1/statistics` (`stats-service`, `epic-018` da
  raiz, 2026-09-10)**: mesmo formato de `bySport`/`byMarket`/`byBettingHouse` já existentes
  (array de `{dimensionId, dimensionName, metrics: SegmentedBetMetrics}`), fechando a lacuna
  documentada desde `feat-006` ("nenhum endpoint separado por `byLeague`/`byTipster` —
  `leagueId`/`tipsterId` só estreitavam os outros segmentos como filtro"). Motivado pelo menu por
  cadastro de [[web]] (`epic-019`) — cada um dos 5 catálogos precisa do próprio ranking. Sem
  campo novo em `SegmentedBetMetrics`, só mais 2 arrays no bundle.
- **`GET /api/v1/statistics/daily` (`stats-service`, `epic-016` da raiz, página "Relatório do
  período" de [[web]], 2026-09-10)**: mesmos 7 filtros de `GET /api/v1/statistics`, granularidade
  diária em vez de mensal (mesma mecânica de agregação de `monthly`, `DIM_DATE` já tem
  `day`/`month`/`year`). Resposta é **array esparso** — só dias com pelo menos 1 aposta liquidada
  no recorte, ordenado por data:
  ```json
  [
    { "date": "2026-07-01", "totalStaked": 34.94, "netProfit": 34.94, "roi": 1.00, "betCount": 22 },
    { "date": "2026-07-03", "totalStaked": 34.94, "netProfit": -0.57, "roi": -0.0162, "betCount": 28 }
  ]
  ```
  Dias sem aposta dentro de `from`..`to` **não aparecem** na resposta — o cliente preenche com
  zero antes de montar a tabela (ver [[STATISTICS]] "Quebra diária"). Sem cache-aside, mesmo
  padrão de qualquer consulta filtrada deste serviço.
- **`GET /api/v1/statistics/search` (`stats-service`, `epic-011` da raiz, tela "Buscar
  Estatísticas" de [[web]])**: rota nova, distinta de `GET /api/v1/statistics` — existe pra
  responder uma combinação específica de filtro com métricas de decisão (RN04/RN09 + as 3 novas
  de [[STATISTICS]]: odd média, drawdown máximo, Índice de Sharpe simplificado), não o bundle
  consolidado do dashboard. **`sportId` e `leagueId` são obrigatórios** (`400`, RFC 7807, se
  ausentes) — único ponto do contrato onde um filtro de estatística deixa de ser opcional,
  decisão de produto da tela (não RN08, que continua regendo o dashboard). Demais filtros
  opcionais, mesmo vocabulário de `GET /api/v1/statistics` mais `teamId` (novo — casa contra
  `team1Id` **ou** `team2Id` em `FACT_BET`, ver [[DATA-MODEL]] "`DIM_TEAM`"), `from`/`to` também
  `yyyy-MM-dd`:
  `?sportId=<uuid>&leagueId=<uuid>&teamId=<uuid>&bettingHouseId=<uuid>&marketId=<uuid>&tipsterId=<uuid>&from=2026-01-01&to=2026-01-31`
  ```json
  {
    "filters": { "sportId": "...", "leagueId": "...", "teamId": null, "bettingHouseId": null, "marketId": null, "tipsterId": null, "from": null, "to": null },
    "summary": {
      "betCount": 42, "totalStaked": 1000.00, "netProfit": 150.00,
      "roi": 0.15, "winRate": 0.55, "avgOdd": 1.87,
      "maxDrawdown": 80.00, "sharpeRatio": 0.42
    },
    "timeline": [ { "date": "2026-01-03", "cumulativeProfit": 30.00 }, { "date": "2026-01-07", "cumulativeProfit": -10.00 } ]
  }
  ```
  `sharpeRatio` é `null` quando o recorte tem menos de 2 apostas liquidadas ou desvio-padrão zero
  (ver [[STATISTICS]] "casos-limite") — nunca divisão por zero. `timeline` é a série ordenada por
  `betDate` de lucro acumulado das apostas liquidadas do recorte (mesma série usada para calcular
  `maxDrawdown`), reaproveitada pelo frontend para o gráfico de equity curve sem uma segunda
  chamada. Sempre calculado direto (sem cache-aside) — o espaço de combinações possíveis
  (esporte × liga × time × mercado × tipster × período) é grande demais para caber no padrão de
  chave fixa por tenant de `feat-005`.
- **`GET /api/v1/statistics/teams` (`stats-service`, `feat-013`, addendum do dia seguinte à
  entrega de `GET /api/v1/statistics/search`)**: lista `[{id, name}]` de `DIM_TEAM` para
  popular o autocomplete de time da tela "Buscar Estatísticas" — `DIM_TEAM` não tem catálogo em
  `bets-service` (texto livre por aposta), sem esse endpoint não haveria como o frontend saber
  quais `teamId` existem. **`sportId` obrigatório** (`400` RFC 7807 localizado, mesma
  `MissingRequiredStatisticsFilterException` de `GET /api/v1/statistics/search`) — decisão do
  usuário: `DIM_TEAM` tem chave natural composta `(name, sportId)` (ver [[DATA-MODEL]]), então a
  listagem é sempre escopada por esporte; trocar de esporte na tela refiltra a lista, nunca
  mistura times de esportes diferentes. Sem paginação (volume baixo por tenant, mesmo raciocínio
  já aceito para as outras dimensões de `FACT_BET` sem índice):
  `?sportId=<uuid>`
  ```json
  [ { "id": "...", "name": "Flamengo" }, { "id": "...", "name": "Vasco" } ]
  ```
- **Idempotência do `POST /api/v1/bets`**: aceita um header opcional `Idempotency-Key`.
  Necessário porque `telegram-integration` pode reenviar a mesma mensagem em caso de retry do
  webhook — sem isso, uma falha de rede no bot pode duplicar uma aposta. `bets-service` apenas
  verifica se a chave já foi vista (reenvio devolve a aposta já criada, `200` em vez de `201`,
  sem comparar o corpo contra o original — simplificação aceita, sem TTL, ver
  [[bets-service]]); é `telegram-integration` (`feat-004`) quem decide o valor da chave — usa o
  `update_id` nativo do Telegram (identifica de forma estável um reenvio real do mesmo webhook
  pelo próprio Telegram; um hash do conteúdo da aposta foi cogitado e descartado por colidir
  entre duas apostas legítimas com odd/stake/casa iguais) — ver [[telegram-integration]] seção
  "Envio da aposta resolvida".
- **Valores de status de aposta** (campo `status`, em `BET` e nos eventos): sempre em inglês —
  `pending`, `won`, `lost`, `void`. Correspondem a `pendente`/`ganha`/`perdida`/`devolvida` na
  especificação original do TCC1 (RF12/RN06, ver [[REQUIREMENTS]] — a tabela de RF/RN em si
  **não** é traduzida, é transcrição fiel do TCC1; só a codificação técnica do campo é inglês).

## Formato de erro

Todos os serviços Java respondem erros como **RFC 7807** (`application/problem+json`):

```json
{
  "type": "https://docs/errors/invalid-odd",
  "title": "Invalid odd",
  "status": 422,
  "detail": "The provided odd (0.95) must be strictly greater than 1.00 (RN07).",
  "instance": "/api/v1/bets"
}
```

- `type` é um slug estável **em inglês**, referenciando a regra de negócio violada quando
  aplicável (RN01–RN09) — para que o front-end e os logs consigam correlacionar o erro à regra
  documentada em [[REQUIREMENTS]]. `type` nunca muda com o idioma da requisição (é identificador
  técnico, não texto para humano).
- `title`/`detail` são **localizados** conforme o header `Accept-Language` da requisição (`pt-BR`,
  `en-US` ou `es`, ver [[CONVENTIONS]] seção "Internacionalização (i18n)") — o exemplo acima está
  em inglês só ilustrativamente; o mesmo erro em `pt-BR` teria `"title": "Odd inválida"`,
  `"detail": "A odd informada (0.95) deve ser estritamente maior que 1.00 (RN07)."`.
- Erros de validação de campo (`jakarta.validation`) usam `status: 400`; violações de regra de
  negócio de domínio usam `status: 422`.
- **Header obrigatório ausente/inválido**: dois status distintos, conforme o papel do header —
  `401` quando o header carrega **identidade do chamador** (ex.: `X-Admin-Api-Key`, `X-User-Id`
  em [[auth-service]] `feat-004`), `400` quando carrega **contexto de negócio** necessário pra
  resolver a operação mas não é identidade (ex.: `X-Tenant-Id` ausente — presente mas malformado
  já é `400` desde `feat-001.3`, ausente é a mesma família de falha de contrato). Convenção
  fixada em `feat-004` (auth-service) pra `bets-service`/`stats-service` reaproveitarem sem
  redecidir status code header a header.

## Documentação de API

Cada serviço Java expõe **springdoc-openapi** (`/v3/api-docs`, UI em `/swagger-ui.html`) — não é
opcional: é como o front-end e o `telegram-integration` descobrem os DTOs reais sem precisar ler
o código-fonte do outro serviço.

## Confiança entre serviços (service-to-service)

> **`X-User-Id` deixou de ser sinônimo de tenant em 2026-08-02** (ver [[DECISIONS-LOG]] "Modelo
> de tenant multiusuário"): um tenant agora pode ter vários usuários independentes. O Gateway
> injeta **três** headers distintos (o terceiro, `X-User-Role`, desde 2026-09-10) — não
> confundir nenhum dos três nem tratá-los como intercambiáveis.

- O **[[api-gateway]]** (`epic-008`, `services/api-gateway/`) é o único ponto que valida o token
  PASETO. O cliente (web ou qualquer chamador autenticado por usuário) envia o token no header
  padrão **`Authorization: Bearer <token>`** — convenção HTTP usual para credencial de usuário,
  reservada para esse caso; os headers `X-Admin-Api-Key`/`X-Service-Key` abaixo continuam
  dedicados aos dois caminhos que não são "usuário logado com token PASETO" (decisão implícita
  ao criar `api-gateway feat-002`, nunca antes escrita nesta nota — nenhum outro documento do
  vault fixava o transporte do token até este ponto). Ao validar, injeta três headers na
  requisição antes de rotear para `bets-service`/`stats-service`:
  - `X-User-Id`: qual usuário fez a chamada. **Persistido como trilha de auditoria** (decisão de
    2026-08-02, ver [[DECISIONS-LOG]]): `BET.createdByUserId` e `BET_RESULT.settledByUserId` em
    [[bets-service]] gravam esse valor (ver [[DATA-MODEL]]), e o envelope de evento (seção
    abaixo) carrega `userId` além de `tenantId`.
  - `X-Tenant-Id`: qual organização/schema a chamada pertence — extraído do token PASETO
    (resolvido no login a partir do slug informado, ver [[auth-service]]). O valor é o slug do
    tenant; cada serviço deriva o nome físico do schema deterministicamente a partir dele
    (`tenant_<slug>`, ver [[CONVENTIONS]] seção "Migrations").
  - `X-User-Role` (desde 2026-09-10, ver [[DECISIONS-LOG]] "Claim `role` no PASETO"): `admin` ou
    `member`, extraído do claim `role` do token (embutido por [[auth-service]] na emissão). Existe
    porque serviços além de `auth-service` passaram a precisar de uma checagem `role = admin`
    (`bets-service epic-013`, `PATCH /api/v1/settings`) sem ter acesso à tabela `USER` — mesmo
    princípio de confiança dos outros dois headers: o Gateway já validou o token, o serviço
    downstream não revalida nada, só confia no valor injetado.
- `bets-service` e `stats-service` **não revalidam o token PASETO** — apenas exigem que
  `X-User-Id` e `X-Tenant-Id` estejam presentes nas rotas autenticadas; `X-Tenant-Id` é a
  identidade confiável usada para resolver o schema da conexão. Isso evita reimplementar a
  lógica de validação de token em três lugares diferentes (a própria motivação desta nota).
- Consequência direta: `bets-service` e `stats-service` **não podem ser expostos diretamente à
  internet** em produção — só o `api-gateway`. No `docker-compose.yml` de desenvolvimento, isso
  é só uma convenção a respeitar (todos estão na mesma rede local), mas o código não deve
  assumir que pode confiar em qualquer requisição que chegue sem passar pelo Gateway.
- **Chamadas sem usuário logado** (hoje só `telegram-integration`, que não tem token PASETO):
  autenticam no `api-gateway` com um header `X-Service-Key` (segredo estático por ambiente, ver
  [[OBSERVABILITY-AND-CONFIG]]) em vez de um token PASETO, e informam **qual** usuário do
  Telegram fez a chamada via um segundo header, `X-Telegram-User-Id` (decisão de 2026-09-07, ver
  [[DECISIONS-LOG]] — nenhuma nota fixava isso antes de `api-gateway feat-004`; o corpo da
  requisição continua idêntico ao do formulário web, sem esse campo). O `api-gateway` resolve o
  usuário/tenant chamando `auth-service` (lookup de `TELEGRAM_ACCOUNT`, ver [[auth-service]]) e
  injeta `X-User-Id`/`X-Tenant-Id` resolvidos antes de rotear — o chamador nunca informa esses
  dois headers diretamente (só `X-Telegram-User-Id`), o mesmo invariante do caminho autenticado
  por PASETO.
  > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): `auth-service` mantém um
  > diretório `TELEGRAM_LINK` (`telegramUserId -> tenantId`/`userId`) no schema `public` do seu
  > próprio banco, fora de qualquer schema de tenant — o lookup é uma consulta direta a essa
  > tabela, sem precisar varrer schemas nem o bot informar o slug do tenant. Ver [[auth-service]]
  > e [[DATA-MODEL]].
- **Chamadas administrativas do operador da plataforma** (criação de tenant — ver
  [[DECISIONS-LOG]] item 3): autenticam com um header **`X-Admin-Api-Key`** (segredo estático,
  ver [[OBSERVABILITY-AND-CONFIG]]), direto em cada serviço (`auth-service`, `bets-service`,
  `stats-service`) — **não passam pelo `api-gateway`**, que só roteia tráfego de usuário/bot. O
  operador faz **3 chamadas manuais separadas**, uma por serviço (`auth-service` primeiro, depois
  `bets-service`, depois `stats-service`) — nenhum serviço chama os outros dois em código, decisão
  que evita tanto lógica de compensação para falha parcial quanto o risco de dependência circular
  entre os epics desses serviços (ver [[DECISIONS-LOG]] item 3). `auth-service` cria o primeiro
  usuário admin do tenant com senha aleatória e `mustChangePassword = true` (ver [[DATA-MODEL]]).
  Contrato de `auth-service` implementado em `feat-003`: `POST /api/v1/admin/tenants` — ver
  [[auth-service]] seção "Modelo de tenant" para o payload/resposta exatos. `bets-service`
  implementa a mesma rota (`feat-001.4`) só criando o schema, sem usuário/senha — ver
  [[bets-service]] seção "Provisionamento de tenant (rota admin)".
- **Confirmação de vínculo de conta Telegram** (`telegram-integration feat-003`, decisão de
  2026-09-08): `POST /api/v1/telegram-accounts` em `auth-service` também **não passa pelo
  `api-gateway`**, mesmo precedente das chamadas administrativas acima. Motivo diferente das
  chamadas admin: não é por convenção de operador, é porque o mecanismo de identidade do
  Gateway pra chamadas sem usuário logado (`X-Service-Key` + `X-Telegram-User-Id`, bullet acima)
  **resolve identidade fazendo lookup no próprio vínculo já confirmado** — circular pro endpoint
  que existe justamente pra criar esse vínculo, e `RouteConfig` do Gateway nem roteia
  `/api/v1/telegram-accounts/**` (só `/api/v1/telegram-links/**`, usado por [[web]] pra *gerar*
  o código). Segurança desta chamada específica não vem de header nenhum: vem do próprio código
  de vínculo (aleatório, TTL curto, uso único, ver [[auth-service]]) — sem usuário logado e sem
  credencial de serviço aplicável a este endpoint. Ver [[telegram-integration]] seção "Vínculo
  de conta" e [[DECISIONS-LOG]].

## Contratos de evento: `BetCreated` e `BetSettled`

Dois eventos distintos, ambos produzidos por `bets-service` e consumidos por `stats-service`
(ver [[bets-service]] e [[stats-service]]) — fiéis aos diagramas de fluxo do TCC1
(`docs/diagrams/flows/manual-bet-registration.png` e `bet-settlement.png`, transcritos como
Mermaid em [[ARCHITECTURE]] seção "Fluxos dinâmicos", que chamavam os eventos de `ApostaCriada`/
`ApostaLiquidada` — nomes traduzidos para inglês nesta revisão, mesma decisão de "tudo em
inglês" do topo desta nota; o diagrama estrutural do TCC1 já usava `BetCreated` em inglês,
então esta tradução também corrige uma inconsistência entre os próprios diagramas originais),
que mostram dois eventos separados, não um único evento reaproveitado:

- **`BetCreated`**: publicado no registro inicial (RF04/RF05), sempre com `status: "pending"`.
  Schema em `docs/contracts/bet-created.schema.json`.
- **`BetSettled`**: publicado quando a aposta é liquidada (RF06/RF12 — status vira `won`, `lost`
  ou `void`). Carrega `profit`/`settledAt` (que não existem em `BetCreated`) e repete os campos
  dimensionais (`bettingHouseId`, `sportId` etc.) para que `stats-service` consiga fazer o
  upsert em `FACT_BET` por `betId` sem depender de já ter processado o `BetCreated`
  correspondente. Schema em `docs/contracts/bet-settled.schema.json`.

**Nomes das dimensões denormalizados no payload** (achado real de `stats-service feat-002`,
antes de qualquer código, implementado em `bets-service feat-010`):
`DIM_BETTING_HOUSE`/`DIM_SPORT`/`DIM_LEAGUE`/`DIM_MARKET`/`DIM_TIPSTER` (ver [[DATA-MODEL]]) têm
coluna `name`, mas os IDs sozinhos (`bettingHouseId`, `sportId`, `leagueId`, `marketId`,
`tipsterId`) não bastam para `stats-service` populá-la — `stats-service` só lê o evento, nunca
chama `bets-service` de volta (consistência eventual é intencional, ver `CLAUDE.md` raiz). Por
isso o payload de ambos os eventos ganhou os campos irmãos
`bettingHouseName`/`sportName`/`leagueName`/`marketName` (obrigatórios, mesma obrigatoriedade dos
IDs correspondentes) e `tipsterName` (opcional, acompanha `tipsterId`). Consulta adicional, não
gratuita: a validação de existência antes de gravar a aposta (`BetService.validateReferences`)
usava só `existsById` (boolean) — não trazia o nome. `feat-010` acrescentou `findById` aos 5
repositórios de catálogo (ports + adapters) e um `resolveDimensionNames` que busca as 5 entidades
por PK no momento de publicar (`create()` e `updateStatus()`) — uma consulta a mais por PK em
tabela pequena (catálogo), não um I/O caro nem síncrono cross-service, só mais específico do que
o achado original sugeria. Mudança de contrato: `docs/contracts/*.schema.json` (`schemaVersion`
continua `1` — ver nota abaixo) e os dois serviços atualizados no mesmo ciclo de trabalho (não no
mesmo commit — repositórios diferentes): `bets-service feat-010` popula os campos no publicador;
`stats-service feat-002`/`feat-003` consomem o schema já estendido (a cópia vendorizada de
`feat-001.9` foi resincronizada com os campos novos antes de `feat-002` começar).

> **Nota sobre `schemaVersion`**: mesmo os dois campos sendo `required` no schema (não
> opcionais), a mudança é tratada como aditiva e sem bump de `schemaVersion` porque nenhuma
> versão do payload jamais foi publicada em produção sem eles — `bets-service` e `stats-service`
> saem do zero e chegam à primeira versão real do evento já com os nomes inclusos. Um bump de
> `schemaVersion` seria necessário se um payload já publicado precisasse mudar de formato depois
> de já estar em uso.

Mudanças de payload em qualquer um dos dois atualizam o schema correspondente, os testes de
contrato (ver [[TESTING]]) e este parágrafo no mesmo commit.

**Cópias vendorizadas do schema em cada repositório de serviço**: os arquivos `docs/contracts/
*.schema.json` vivem no repositório `sv-harness` (raiz) — `bets-service` e `stats-service` são
repositórios Git separados, e a pipeline de CI de cada um só faz checkout do próprio repositório
(sem acesso aos `docs/` da raiz). Por isso, o teste que valida a mensagem publicada/consumida
contra o schema real (exigido pela Definição de Pronto de ambos os serviços) precisa de uma cópia
do `.schema.json` dentro do próprio repositório — mesmo padrão de duplicação já aceito para
`.github/scripts` (ver [[CI-CD]]). O diretório da cópia depende de **quem lê o schema e quando**:
- `bets-service` (produtor): só o **teste** valida a mensagem já publicada contra o schema —
  produção nunca lê o arquivo. Cópia em `src/test/resources/contracts/` (achado real de
  `feat-006`).
- `stats-service` (consumidor): a **produção** precisa validar cada mensagem recebida contra o
  schema correspondente ao `eventType` antes de decidir processar ou deixar ir para a DLQ — não é
  só uma verificação de teste. Cópia em `src/main/resources/contracts/` (achado real de
  `feat-001.9`), lida em runtime pelo listener; os testes reaproveitam a mesma cópia sem
  duplicá-la de novo em `src/test/resources/`, já que o Maven inclui `src/main/resources` no
  classpath de teste automaticamente.

**Qualquer mudança num schema em `docs/contracts/` atualiza também as cópias vendorizadas nos
repositórios que os leem/testam**, no mesmo commit/PR daquele repositório (não simultâneo ao
commit da raiz, já que são repositórios diferentes — mas a próxima sessão que tocar aquele schema
não pode esquecer a cópia, em nenhum dos dois repositórios).

Envelope (idêntico para os dois — todo evento do sistema, presente ou futuro, usa este
envelope, só `eventType` e `payload` mudam):

```json
{
  "eventId": "uuid",
  "eventType": "BetCreated",
  "schemaVersion": 1,
  "occurredAt": "2026-07-30T12:00:00Z",
  "tenantId": "slug do tenant (X-Tenant-Id) - NAO mais igual a userId, ver DECISIONS-LOG",
  "userId": "uuid do usuario que fez a chamada (X-User-Id) - quem criou/liquidou, distinto do tenant",
  "payload": { "...": "campos da aposta, ver o JSON Schema correspondente" }
}
```

### Topologia RabbitMQ (contrato entre `bets-service` e `stats-service`)

Criada por `infra/rabbitmq/definitions.json` (ver [[infra]]), **não** declarada pelos serviços no
boot. Faz parte do contrato de evento, não é detalhe interno da infraestrutura: se
`bets-service` publicar em outro exchange, ou se `stats-service` declarar a fila com argumentos
diferentes dos abaixo, o canal quebra com `PRECONDITION_FAILED` em loop — por isso os dois
serviços devem **consumir/publicar sem redeclarar** (Spring AMQP: nada de `Queue`/`Exchange`
bean com argumentos próprios; o broker já tem a topologia quando o serviço sobe).

| Recurso | Nome | Tipo | Argumentos |
|---|---|---|---|
| Exchange principal | `bets.events` | topic, durable | — |
| Fila do consumidor | `stats.bet-events` | **quorum**, durable | `x-dead-letter-exchange: bets.events.dlx`, `x-delivery-limit: 3` |
| Exchange de dead-letter | `bets.events.dlx` | fanout, durable | — |
| Fila de dead-letter | `stats.bet-events.dlq` | **quorum**, durable | — |

Routing keys: `bet.created` para `BetCreated`, `bet.settled` para `BetSettled` — ambas ligadas a
`stats.bet-events`. Nomes em inglês, mesma regra do topo desta nota.

`x-delivery-limit` só existe em quorum queue (classic queue reentrega indefinidamente e nunca
chegaria à DLQ sozinha) — continua configurado como defesa em profundidade, mas **desde
2026-09-09 não é mais o mecanismo primário de "limite de tentativas"**: RabbitMQ 4.3+ (versão
real deste projeto) não conta `nack(requeue=true)` — o que qualquer falha de consumo produz por
padrão no Spring AMQP — para esse limite; quem hoje aciona a DLQ de verdade é o retry de
aplicação de `stats-service` (`spring.rabbitmq.listener.simple.retry`, 3 tentativas, ver
[[infra]] seção "Dead Letter Queue (DLQ)" para o achado completo). Mudança em qualquer linha
desta tabela é mudança de contrato: atualiza `infra/rabbitmq/definitions.json`, [[bets-service]],
[[stats-service]] e [[infra]] no mesmo commit.

- `schemaVersion` incrementa em qualquer mudança incompatível do `payload`; o consumidor deve
  ignorar (ou tratar explicitamente) versões que não reconhece, nunca falhar silenciosamente.
- Mensagens que falham consecutivamente no consumo vão para a DLQ (ver [[infra]]) — não são
  descartadas nem travam a fila principal.
- Idempotência do consumo (mesmo evento reentregue não duplica efeito) é garantida por
  `stats-service` via a tabela `PROCESSED_EVENT` — ver [[stats-service]].

## Internacionalização (i18n)

Decisão explícita do usuário (2026-08-01): o sistema é **100% internacionalizável** — nenhum
texto voltado ao usuário final (mensagens de erro de API, UI do front-end) é hardcoded num único
idioma. Ver [[CONVENTIONS]] seção "Internacionalização (i18n)" para a implementação completa
(backend Java e frontend Angular). Nesta nota, o que importa para o contrato de API:

- `type` (RFC 7807) é sempre um slug estável em inglês — **não** é localizado, é identificador
  técnico.
- `title`/`detail` (RFC 7807) são resolvidos a partir do header `Accept-Language` da requisição
  (`pt-BR`, `en-US`, `es` — os três sempre mantidos em sincronia, nunca só um atualizado).
  Requisição sem `Accept-Language` reconhecido cai no idioma padrão (`pt-BR`).
- Rotas, query params, nomes de campo e nomes/valores de evento **nunca** são localizados — são
  parte da superfície técnica da API, sempre em inglês, independente do idioma do usuário final.
