---
tags: [service, frontend]
---

# web

Angular 21.x + TypeScript ES2025, SPA. Ver [[arquitetura]] para o panorama geral,
[[requisitos]] para RF/RNF completos, [[sistema-de-design]] para tema (claro/escuro), paleta de
cores e inventário de componentes, e [[convencoes]] seção "Internacionalização (i18n)" para a
estratégia de tradução (pt-BR/en-US/es sempre mantidos, biblioteca em runtime) — tudo normativo,
não decidir uma alternativa aqui. Harness de código em `apps/web/CLAUDE.md`.

## Responsabilidade

- RF01/RF02 (UI) — autenticação e gestão de usuários **dentro de um tenant já existente**,
  consumindo [[auth-service]]. **Sem tela de autocadastro** — ver seção "Modelo de tenant (UI)"
  abaixo, reinterpretação de 2026-08-02 sobre o RF01 original do TCC1.
- RF03 (UI) — gestão de casas de apostas, consumindo [[bets-service]].
- RF04 (UI) — registro manual de apostas.
- RF08 (UI) — histórico de operações.
- RF10/RF11 (UI) — dashboards e filtros dinâmicos, consumindo [[stats-service]].
- RNF01 — responsividade (desktop, tablet, mobile).
- RNF02 — usabilidade.

Chama [[api-gateway]] **cross-origin** (`environment.apiGatewayUrl`/`environment.development.ts`
absoluto, ver [[observabilidade-e-configuracao]] seção "Configuração de `apps/web`") — sem proxy `/api`
no `nginx.conf` de produção nem no dev server. Depende do `api-gateway` responder CORS
(`api-gateway feat-012`, achado real de 2026-09-11 — o gap existia desde sempre, só não tinha
sido exercitado por um browser real até então) para o navegador não bloquear a chamada.

## Modelo de tenant (UI)

Decisão de 2026-08-02 (ver [[DECISIONS-LOG]] "Modelo de tenant multiusuário") muda o que a UI
de autenticação precisa cobrir — nenhuma das telas abaixo é autocadastro público:

- **Login**: três campos — identificador/slug da organização (tenant), e-mail, senha. Necessário
  porque e-mail só é único dentro do schema do tenant, não globalmente (ver [[auth-service]]) —
  sem o slug, `auth-service` não sabe em qual schema validar a senha.
- **Sem tela pública de "criar conta"**: criação de **tenant** (e do primeiro usuário, o admin
  daquele tenant) é uma rota administrativa restrita ao operador da plataforma, **fora do
  escopo deste app por completo** — operador chama a API diretamente (`X-Admin-Api-Key`, ver
  [[contratos-de-api]]), sem UI própria em `apps/web` (decisão de 2026-08-02, ver [[DECISIONS-LOG]]
  item 11). Esse é o único passo do fluxo sem equivalente no caso de uso original do TCC1 (UC01
  não previa um segundo ator "operador").
- **Gestão de usuários do tenant** (tela nova, substitui a antiga tela de "cadastro" público):
  visível **apenas** para o usuário logado com `role = admin` do tenant — `role = member` **não
  vê essa tela de forma alguma** (nem em modo somente leitura, decisão de 2026-08-02, ver
  [[DECISIONS-LOG]] item 11). É a implementação de UC01 ("Manter usuário") do diagrama original,
  só que restrita a quem pode acioná-la; continua sendo o próprio usuário (o admin) quem cria os
  demais, não o operador da plataforma. Lista os usuários do tenant e permite criar novos
  (`role = member`) — usa o mesmo layout em painéis (ver [[sistema-de-design]] item 13, "Lista de
  configurações/menu", como base) e a mesma regra semântica de cor (ação de criar usuário é
  neutra/azul, não verde).

## Regras de design do formulário de apostas

O formulário de registro manual (RF04) deve seguir as **oito regras de ouro de Shneiderman**,
citadas explicitamente no escopo do TCC:

1. Buscar consistência.
2. Permitir atalhos para usuários frequentes.
3. Oferecer feedback informativo.
4. Projetar diálogos que indiquem encerramento.
5. Prevenir e tratar erros de forma simples.
6. Permitir reversão fácil de ações.
7. Manter o lócus de controle com o usuário.
8. Reduzir a carga de memória de curto prazo.

## Date picker: mat-datepicker + mat-timepicker (`apps/web feat-022`, `epic-024` da raiz)

Todos os campos de data do app (`period-preset-filter` — compartilhado por dashboard/
period-report/catalog-dashboard —, `history`, `search-statistics`, `register-bet`) usam
`mat-datepicker` (`provideNativeDateAdapter()`, sem `moment`/`date-fns`/`luxon` — mesma filosofia
`Intl` de `core/date-format.ts`). `MAT_DATE_LOCALE` sozinho é um DI token estático; como o app
troca idioma em runtime (`core/language.ts`, `Language.current`), `App` (`app.ts`) registra
`effect(() => dateAdapter.setLocale(language.current()))` no construtor — reaproveita o signal já
existente em vez de escutar `transloco.langChanges$` direto.

**Gotcha real, achado lendo o código-fonte do Material instalado (não só os `.d.ts`)**: o merge
de data/hora entre `mat-datepicker` e `mat-timepicker` é **assimétrico por design do próprio
Material**, não um comportamento configurável — `MatTimepickerInput._assignUserSelection`
preserva a data ao trocar a hora (lê o valor atual antes de aplicar `setTime`), mas
`MatDatepickerInputBase._registerModel` só repassa a seleção do calendário direto, sem merge, e
`NativeDateAdapter._createDateWithOverflow` zera a hora pra meia-noite. Ligar os dois num único
valor compartilhado (`FormControl` único ou variável comum) faria trocar a data resetar
silenciosamente a hora já escolhida. `register-bet` (`betDate`, único campo data+hora do app)
usa **2 `FormControl` independentes** (`betDateOnly`/`betTimeOnly`, nunca compartilham valor) —
combinados via `setHours`/`setMinutes` só no limite do submit (mesmo princípio de conversão no
limite já usado nos filtros abaixo). Reaproveitar este padrão se outro campo data+hora aparecer.

## Dashboards e filtros (RN08)

Filtros por período, casa de apostas, esporte, liga, mercado e tipster devem recalcular as
métricas dinamicamente — não são apenas um filtro client-side sobre dados já carregados; cada
mudança de filtro é uma nova consulta a `GET /api/v1/statistics`, que responde um bundle único
com todas as vistas do dashboard de uma vez (ver [[stats-service]]). Rótulos de filtro na UI são
localizados (ver [[convencoes]]) mesmo os query params enviados sendo sempre em inglês —
**corrigido em `feat-006`**: os nomes reais implementados usam sufixo `Id` (`bettingHouseId`,
`sportId`, `leagueId`, `marketId`, `tipsterId`) mais `from`/`to` (data, `yyyy-MM-dd`), não
`sport`/`league`/`market` como esta nota dizia antes — mesma correção de nomenclatura já feita em
[[contratos-de-api]] para `bets-service`, só não tinha sido propagada até aqui.

## Dashboard consolidado — filtro de período com presets e novos cards (`epic-015` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10) — reespecifica o
dashboard já entregue em `feat-006` (`done`), não cria tela nova.

**Filtro de período**: presets **Hoje** (default — muda o comportamento atual, que hoje carrega
sem filtro nenhum no `ngOnInit`), **Última semana**, **Últimos 15 dias**, **Último mês** (mês
calendário anterior completo) e **Este mês** (dia 1 do mês corrente até hoje), mais um date range
picker (Material) para período customizado. Todos os presets resolvem para `from`/`to`
client-side antes da chamada — mesmo contrato `yyyy-MM-dd` já usado, sem mudança de query param
em `GET /api/v1/statistics`.

**Duas fontes de dados via `forkJoin`** (mesmo padrão já usado para os catálogos em
`feat-004`/`005`/`008`): `GET /api/v1/statistics` ([[stats-service]], `epic-014`) e
`GET /api/v1/bankroll/balance?at=<from|to>` ([[bets-service]], `epic-013`, 2 chamadas — saldo
inicial e final do período).

**Cards novos**, ao lado dos já existentes (lucro/prejuízo = `netProfit`, quantidade de apostas =
`settledCount`, ROI — os 3 já em `feat-006`): unidades apostadas (**calculado no cliente**, não
vem pronto de nenhuma API — `totalStaked / (saldoAtual × unitPercent)`, `unitPercent` de
`GET /api/v1/settings`), apostas PRÉ/LIVE (`preCount`/`liveCount`), vitórias/derrotas ao lado da
taxa de acerto já existente (`wonCount`/`lostCount` + `winRate`), odd média (`avgOdd`), saldo
inicial do período, saldo final do período. Fórmulas completas em [[estatisticas]].

**Configuração de unidade**: campo/tela admin-only para editar `unitPercent`
(`PATCH /api/v1/settings`, `epic-013`) — local exato na UI (aba nova, dentro de casas de
apostas, ou área de usuário) é decisão de plan review daquela feature, não fixada aqui.

> **Implementado em `web feat-014`**. Decisões do plan review: (1) campo de unidade inline no
> próprio painel de filtros do dashboard (não aba/tela nova), gated por `Auth.isAdmin()` — é
> onde o valor é consumido, menor atrito que navegar para outra tela; `GET /api/v1/settings` não
> é restrito (todo usuário precisa de `unitPercent` para `unidadesApostadas`), só o `PATCH` é
> admin-only (403 do backend, gate client-side é só UX). (2) `unidadesApostadas`/`avgOdd`
> indeterminados (saldoAtual ou `unitPercent` = 0) renderizam texto localizado, não lançam
> exceção nem dividem por zero. `shared/period-preset-filter` (presets + range customizado com
> `<input type="date">`, não Material Datepicker — sem precedente no inventário de
> `docs/sistema-de-design.md`, evita dependência nova para 1 par de campos) fica em `shared/` porque
> `epic-017` ("Relatório do período") reusa o mesmo componente. Mudança de comportamento
> intencional: o dashboard agora aplica o preset "Hoje" por padrão no load (antes carregava sem
> filtro nenhum) — mudanças de período aplicam na hora, os 5 filtros de catálogo continuam atrás
> do botão "Aplicar filtro" existente. `StatisticsApi.BetMetrics` (frontend) nunca tinha sido
> atualizado desde `feat-006`, apesar do backend (`stats-service epic-014`) já expor
> `wonCount`/`lostCount`/`voidCount`/`preCount`/`liveCount`/`avgOdd` há várias sessões — gap real
> fechado aqui, escopo restrito só aos 6 campos que os cards desta feature consomem
> (`byLeague`/`byTipster` ficam para quando `epic-019` precisar deles; `byBetType` acabou
> consumido mais tarde por `feat-026`, não por `epic-021` como esta nota previa originalmente —
> ver seção "Paridade betType/byBetType" abaixo).

## Tela "Visão geral" pós-login (`epic-021` da raiz, `apps/web feat-029`, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal). Tela nova, distinta das outras 6 desta rodada — visão de **vida inteira do
tenant**, a única desta rodada **sem filtro de período** (por definição: "todo o período do
tenant"), rota `/overview`. **Login redireciona pra cá em vez de `/dashboard`** (decisão do
usuário, `AskUserQuestion`, 2026-09-15) — `/dashboard` continua existindo, só deixou de ser a
landing page, virou item normal de `app-side-nav` (primeiro da lista, junto com "Visão geral").

Implementado sem desvio do plano. Curva de lucro acumulado em unidades **contínua, nunca reseta**
(diferente da grade de `epic-020`, que reseta por mês) desde a primeira aposta liquidada do
tenant — `buildLifetimeCurve` (`pages/overview/overview-metrics.ts`), só o último valor
(`lucroTotalUnidades`) é exibido (a curva completa, ponto a ponto num gráfico, não fazia parte do
escopo desta rodada de features, só o card de total). "Início do histórico": sem endpoint
dedicado, usa o primeiro item do array esparso e ordenado por data de
`GET /api/v1/statistics/daily` sem `from`/`to` como proxy (`resolveEarliestDate`) — decisão já
prevista no plan review, confirmada na implementação. Saldo Começo/Final por mês derivado
client-side de uma única chamada a `GET /api/v1/bankroll/balance?at=<data mais antiga>` (pulada
inteiramente para um tenant sem histórico) + o próprio lucro diário já buscado para a curva, sem
1 chamada por mês (`buildMonthlyBalances`) — ver [[estatisticas]].

**Achado real, diverge do que a descrição do epic assumia**: `monthly` de
`GET /api/v1/statistics` **não** vem pré-filtrado pelo ano corrente quando a chamada é feita sem
`from`/`to` — `aggregateByMonth` (`stats-service`) agrupa por `(year, month)` sobre o histórico
inteiro do tenant, sem nenhuma restrição de data. A tabela mensal desta tela (Jan–Dez do ano
corrente) filtra `monthly` pelo ano no cliente (`buildMonthlyTable`) antes de casar cada mês com
seu `BetMetrics` — sem esse filtro, Janeiro de dois anos diferentes se misturariam na mesma linha.
Cards: Lucro Total (U), Pré/Live (U) (`byBetType`, tipado por `feat-026` — ver seção abaixo, esta
tela só reusa o campo), Lucro Médio Mensal (U) = `lucroTotalUnidades / 12` e ROI (`roiMedioDiario`,
extraído de `period-report-metrics.ts` para reuso em vez de duplicar a fórmula).

## Paridade betType/byBetType (`epic-027` da raiz, `apps/web feat-026`, done)

Achado de auditoria (2026-09-12): `register-bet` ainda enviava `betType` como texto livre, embora
`bets-service feat-014.2` já tivesse restringido o campo a um enum `PRE`/`LIVE` (serializado
minúsculo, `pre`/`live`) — requests com outros valores nunca eram rejeitados na tela porque o
`CreateBetRequest` do backend aceita `betType` opcional/nulo (`@JsonProperty` só valida o formato
quando o campo vem preenchido). Trocado por `mat-select` com 3 opções (`pre`/`live`/vazio =
"não classificado"), mesmo padrão de outros selects do formulário.

**Revisado em `apps/web feat-036`** (achado de usuário em uso real, 2026-09-17): a opção
"não classificado" permitia cadastrar apostas sem `betType`, que então não entravam em nenhum dos
2 buckets de `byBetType` (comportamento documentado em `docs/contratos-de-api.md`, ainda válido para
apostas legadas e qualquer outro produtor do contrato, ex. `telegram-integration`) — mas dentro
deste formulário especificamente isso não fazia sentido: toda aposta nova cadastrada por aqui tem
um tipo conhecido no momento do cadastro. Campo `betType` do form agora é `Validators.required`
com default `'pre'`; a opção vazia foi removida do `mat-select` e a chave i18n
`registerBet.betTypeNone` (não usada em nenhum outro lugar do app) foi removida dos 3 locales.
`byBetType`/`bet-type-dashboard` continuam tratando `betType` nulo normalmente para o que já
existe na base ou entra por outro caminho — só este formulário passou a nunca mais produzir esse
estado.

**Decisão de ownership de `byBetType`** (registrada no `plan_review` de `feat-026`, decidida pelo
usuário via pergunta direta, 2026-09-15): `core/statistics-api.ts` (`BetMetrics`) tinha um
comentário explícito e pré-existente reservando `byBetType` para `epic-021` ("Visão geral", ver
seção acima) — implementar a tipagem em `feat-026` sem revisar isso criaria 2 features competindo
pelo mesmo campo. Optou-se por `feat-026` ser a dona: tipa `byBetType: SegmentedBetMetrics[]` em
`StatisticsDashboard` (mesmo formato dos outros 5 segmentos) e expõe uma tela própria — quando
`epic-021`/`feat-029` for implementada, ela só reusa o campo já tipado.

**Sem componente novo**: `shared/catalog-dashboard` (já genérico, lê `data()[segment()]`) ganhou
`'byBetType'` no union `CatalogSegment` e uma 6ª rota (`/bet-type-dashboard`, `catalogDashboard.
betTypeNameLabel`) — mesmo padrão dos outros 5 segmentos (`epic-019`), só que sem par de
"Cadastrar" no menu (não é um catálogo gerenciável, é um agrupamento fixo de 2 buckets). Entrada
de nav ficou junto aos outros links de estatística (`secondaryLinks`), não no grupo de recursos.

## Dashboard — grade de gráficos mensais de drawdown (`epic-020` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal — grade de mini-gráficos de linha, um por mês). Seção/aba nova dentro do
dashboard consolidado (`epic-006`/`epic-015`), não página separada — quarta aba do
`mat-tab-group` já existente (ao lado de Por esporte/mercado/casa de apostas). Filtro de 2
`<input type="month">` (início/fim), **não** o `shared/period-preset-filter` reaproveitado em
outras telas — granularidade de mês, filtro dedicado desta seção. Intervalo trava em fronteira
de mês por construção (`<input type="month">` não tem componente de dia): `from` = dia 01 do mês
inicial, `to` = último dia do mês final. Uma chamada a `GET /api/v1/statistics/daily`
(`epic-016`) cobrindo o intervalo inteiro; cliente agrupa por mês e calcula a curva acumulada em
unidades (ver [[estatisticas]] "Grade de gráficos mensais de drawdown" para a fórmula — usa
`saldoAtual`/`GET /api/v1/bankroll/balance` sem `at`, não `saldoFinal` do período como
`period-report-metrics.ts`; reset só na virada de mês, dia sem aposta carrega o valor anterior).
Zero backend novo. Grade CSS `auto-fit` com N mini-gráficos (`shared/monthly-drawdown-chart`,
`ngx-echarts`, mesmo padrão de `shared/monthly-profit-chart` de `feat-006`) via 1 componente
parametrizado por mês, reaproveitado N vezes — mesmo precedente de `feat-008`/`epic-019` para não
reincidir no achado de duplicação do SonarCloud. Módulo puro de cálculo
(`monthly-drawdown-metrics.ts`) co-localizado em `shared/` (não em `pages/dashboard/`) para não
inverter a dependência — um componente `shared/` nunca deveria depender de um módulo de
`pages/`.

**Implementado em `web feat-028`**: os 2 campos de mês ficam batched atrás de um botão "Aplicar"
explícito (mesmo padrão do `filterForm` de 5 selects do próprio `dashboard.ts`) — achado real de
design encontrado durante os próprios testes: reagir a cada campo independentemente disparava 2
requisições sobrepostas quando os dois mudavam, com risco da resposta desatualizada resolver por
último. QA visual real (screenshots Playwright desktop/mobile × claro/escuro) achou e corrigiu um
bug de responsividade mobile (filtro não quebrava linha, cortando os rótulos). Rodar a suíte e2e
completa (não só o arquivo tocado) revelou e corrigiu uma regressão real pré-existente de
`feat-021` (`e2e/register-bet.spec.ts` nunca ganhou o mock do catálogo de times que aquela
feature acrescentou ao `forkJoin` do formulário) — ver [[testes]] para o padrão de falha geral.

## Menu por cadastro — Cadastrar + Dashboard (`epic-019` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10). Reestrutura a nav
existente: hoje "Catálogos" é um único link com abas internas (Esportes/Ligas/Mercados/Tipsters,
`feat-008`, componente `shared/catalog-manager` parametrizado) e "Casas de Apostas" é outro link
separado (`feat-003`) — os dois só cadastro, sem visão analítica por item. Cada um dos 5
catálogos vira um menu próprio com 2 itens: **Cadastrar `<recurso>`** (reaproveita as telas já
existentes de `feat-003`/`008`, só reorganiza a navegação, sem reescrever o CRUD) e **Dashboard**
(tela nova, filtro de período obrigatório — reusa o componente de `epic-015` — mostrando ranking
mais/menos lucrativo por `roi`, `netProfit` visível ao lado, quantidade de entradas
(`settledCount`) e total ganho/perdido (`netProfit`) daquele catálogo específico). Fonte:
`bySport`/`byLeague`/`byMarket`/`byTipster`/`byBettingHouse` de `GET /api/v1/statistics`
(`byLeague`/`byTipster` novos, `epic-018`). Mesmo precedente de design de `feat-008` (evitar o
achado de duplicação do SonarCloud de `feat-003`): 1 componente parametrizado pelos 5 dashboards,
não 5 telas quase idênticas.

> **Implementado em `web feat-016`** sem divergência do planejado. Decisões técnicas do plan
> review: (1) as 9 rotas ("Cadastrar" ×4 + "Dashboard" ×5) recebem `resourcePath`/`segment` via
> `data` da rota + `withComponentInputBinding()` (novo em `app.config.ts`) em vez de 9
> páginas-wrapper quase idênticas — mesmo precedente anti-duplicação citado acima, aplicado
> também à camada de roteamento, não só aos componentes. (2) `pages/catalogs/` (grupo de abas)
> foi removida por completo — cada catálogo agora é uma rota própria, alcançada pelo menu, sem
> troca de aba em página única. (3) `app-nav` ganhou 5 `mat-menu` (primeiro uso de overlay do CDK
> no app — gotcha de limpeza em teste unitário documentado em [[testes]]) com um helper
> `isResourceActive()` pra destacar o gatilho ativo, já que o botão-gatilho de um `mat-menu` não é
> ele mesmo um `routerLink` (`routerLinkActive` sozinho não o alcança).

**6º catálogo, sem par de Dashboard (`web feat-021`, `epic-024` da raiz, 2026-09-15)**: `TEAM`
(bets-service feat-016/017) quebra o padrão "5 recursos, 1 componente parametrizado" acima —
tem FK `sportId` obrigatória, então não é estruturalmente idêntico a sports/leagues/markets/
tipsters/betting-houses. Em vez de forçar um 5º/6º caso condicional em `shared/catalog-manager`
(risco de regressão nas 4 telas já estáveis por um resource com forma diferente), ganhou um
componente dedicado (`shared/team-manager`) e um link simples no `app-side-nav` (sem o `mat-menu`
Cadastrar/Dashboard dos outros 5 — não existe `byTeam` em `GET /api/v1/statistics`, `stats-service
feat-018` que alinharia `DIM_TEAM` ao catálogo real está `BLOCKED`).

## Tela de vínculo da conta Telegram (`epic-027` da raiz, done)

**Implementado em `web feat-027`** sem divergência do plano. `TelegramLinkApi.create()` (novo,
`core/telegram-link-api.ts`) só faz `POST /api/v1/telegram-links` sem corpo — só envia
`Authorization: Bearer` (`authInterceptor`), o Gateway resolve `X-User-Id`/`X-Tenant-Id` do
token, mesmo padrão de `BettingHousesApi`/`SettingsApi`. Tela nova (`pages/telegram-link`, rota
`/telegram-link`, `authGuard`) reaproveita `submitForm` (`core/api-request.ts`): um botão único
gera/regenera o código de 8 caracteres, mostra `code` + `expiresAt` formatado (`formatDateTime`,
locale ativo) e erro RFC 7807 em caso de falha — sem estado de carregamento dedicado (o botão já
desabilita via `submitting()`, mesmo padrão de `betting-houses`). Entrada nova em
`app-side-nav`'s `secondaryLinks` (ícone `telegram`, sem par de Dashboard — não é um catálogo).

O residual aceito no plan review (comportamento de gerar um 2º código com um já pendente —
substitui vs. `409`) não exigiu decisão de frontend: a tela sempre substitui o código exibido
pela resposta do último `POST` bem-sucedido e mostra o detail RFC 7807 em caso de `409`/`429` —
comportamento correto nos dois cenários possíveis do backend, sem acoplamento a qual deles é o
real.

## 4 achados de UX ad-hoc pós-deploy (`feat-034`, sem epic próprio — mesmo precedente de `feat-032`/`033`)

Achados do usuário em uso real, investigados contra o dev server (screenshots reais) antes de
codificar — dois deles com hipótese explícita no `feature_list.json` a confirmar/descartar, dois
sem investigação prévia nenhuma.

**(1) `shared/searchable-select` grudado 2-por-linha** (confirmado por medição real):
`getComputedStyle` no `mat-form-field` renderizado por `searchable-select.html` retornava
`display: inline-flex` (default do Material), nunca `block`, mesmo com `register-bet.scss` tendo
`mat-form-field { display: block }` — ViewEncapsulation emulado tageia o elemento com o hash de
`searchable-select` (quem o renderiza), não o do caller, então o seletor compilado do caller nunca
alcança fisicamente o elemento real. Só reproduzia visualmente em janelas largas (~1920px) — em
1280/700/500px o painel já era estreito demais para 2 campos caberem lado a lado mesmo com o
`display` errado, por isso a sessão anterior não tinha conseguido confirmar. Fix: `mat-form-field
{ display: block; width: 100% }` **dentro** de `searchable-select.scss` — a única folha que
realmente alcança o elemento.

**(2) Rótulo cortado em "Mês inicial"/"Mês final"** (`shared/monthly-drawdown-grid`, `<input
type="month">`): dois achados reais empilhados. Primeiro, o campo encolhia bem abaixo do próprio
`flex-basis` em painel estreito (`min-width` ausente — `flex-shrink:1` default não respeita
`flex-basis` como piso sem `min-width` explícito). Corrigir isso sozinho não resolveu o visual —
segunda causa, medida diretamente (`getComputedStyle` comparado contra `register-bet`'s
`ticket-number`, um `matInput` comum): `input[type="month"]` computava `line-height:16px`/
`height:16px` contra os `24px`/`24px` de um input de texto normal — o UA do browser não aplica a
regra `line-height:1.5` do Material a esse tipo de input nativo. Material posiciona o rótulo
flutuante assumindo 24px de altura de conteúdo; só 16px reais deixava o rótulo sem espaço vertical
para limpar o valor. Fix: `min-width` + `input[type='month'] { height: 24px; line-height: 24px }`.

**(3) Logo da sidebar colapsada "quebrando em 2 linhas"**: não reproduzido em nenhuma condição
testada (4 larguras, 2 níveis de zoom, screenshot no meio da transição de 0.25s) — o ícone atual
(só a marca, sem wordmark, que já era condicional) renderiza limpo sempre. A própria descrição já
apontava que o usuário pode ter aberto um worktree desatualizado. Decisão do usuário via
`AskUserQuestion`: aplicar a sugestão original mesmo assim (esconder também o `<img>` do logo
quando colapsada, deixando só o botão de expandir) — mudança preventiva de baixo risco, não uma
correção de bug confirmado.

**(4) Máscara de digitação `__/__/____` ausente** (regressão da `feat-022`, nunca notada):
`core/date-mask.directive.ts` novo — primeira diretiva de máscara do codebase, aplicada nos 4
lugares que usam `matDatepicker` texto livre (`shared/period-preset-filter`, `pages/history` ×2,
`pages/search-statistics`, `pages/register-bet` — decisão do usuário via `AskUserQuestion` de
cobrir os 4, não só o `period-preset-filter` citado literalmente no backlog). **Achado crítico**
que só um teste e2e real revelou (documentado em detalhe em `docs/convencoes.md` seção
"Formulários"): `NativeDateAdapter.parse()` (Angular Material) é `Date.parse()` puro — sempre
M/D/Y para uma string com `/`, **independente** do locale ativo do app. A primeira versão desta
diretiva ordenava a máscara pelo locale (D/M/Y para `pt-BR`/`es`, via `Intl.DateTimeFormat`,
mesma filosofia de `core/date-format.ts`) — isso trocava dia e mês **em silêncio** no parse
sempre que o dia fosse ≤12, um bug de integridade de dado real (aposta salva com data errada, sem
erro nenhum). Corrigido para M/D/Y sempre, independente do idioma — só o texto do placeholder
continua traduzido, a ordem de digitação exigida nunca varia. Testes unitários (`vitest`)
cobrem a formatação da string; JSDOM nunca resolve um `Date` real por esse caminho (confirmado
mesmo setando um valor completo diretamente, sem a diretiva) — a prova do `Date` final correto
fica no e2e (`period-report.spec.ts`), que foi o teste que efetivamente capturou o bug antes do
fix.

Story SV-518 (subtasks SV-519..522), PRs #152-155, CI+SonarCloud verdes. `Delivery Reviewer`/
`Test Suite Auditor` (self-review): `PASS`. `./init.sh` e `npx playwright test` completos verdes
(56→57 arquivos de teste, 81 e2e).

## Tela de troca de senha (`epic-030` da raiz, done)

**Implementado em `web feat-035`**, consumindo `POST /api/v1/auth/change-password`
(`auth-service feat-018`, `epic-029`). Plan Reviewer corrigiu 2 achados MAJOR antes de codificar
(nenhum exigia decisão do usuário): (1) a mensagem de sucesso ia reusar o estilo de
`unitPercentSuccess` (`--color-positive`, verde) — `docs/sistema-de-design.md` reserva essa cor
exclusivamente a ganho financeiro, então a confirmação usa estilo neutro (mesma caixa com borda
de `.telegram-link__result`), não verde; (2) o e2e proposto batia contra o backend real
(login→trocar→logout→login de novo) — contradiz a convenção real da suíte (**todo** Playwright
deste app mocka a API via `page.route()`, nunca bate contra um backend real), corrigido para
`e2e/change-password.spec.ts` mockado, mesmo padrão de `telegram-link.spec.ts`.

`ChangePasswordApi` (novo, `core/change-password-api.ts`) só faz `POST
/api/v1/auth/change-password` — mesmo padrão de `TelegramLinkApi`/`SettingsApi`, só
`Authorization: Bearer`. Tela nova (`pages/change-password`, rota `/change-password`,
`authGuard`, sem `adminGuard` — qualquer usuário troca a própria senha) com Reactive Form
`currentPassword`/`newPassword`/`confirmPassword` e um validator de **grupo** customizado
comparando `newPassword`/`confirmPassword` — primeiro validator desse tipo no codebase (grep
confirmou nenhum `ValidatorFn`/`AbstractControl` customizado antes desta feature). `Auth`
(`core/auth.ts`) ganhou `clearMustChangePassword()`: zera `session.mustChangePassword` no signal
e no `localStorage` sem exigir novo login — necessário porque o token PASETO não é reemitido
(suas claims nunca carregaram `mustChangePassword`) e a sessão é só client-side.

**Gotcha real de Angular Reactive Forms encontrado via QA visual** (não pego por nenhum teste
unitário/e2e, só pela captura de tela real): `FormGroup.reset()` sozinho **não** limpa a flag
`submitted` da `FormGroupDirective` associada ao `<form [formGroup]>` — e o
`ErrorStateMatcher` padrão do Angular Material considera um campo inválido quando
`control.invalid && (control.touched || form.submitted)`. Resultado: depois de um submit
bem-sucedido que limpava o form com `this.form.reset()`, os 3 campos de senha (agora vazios,
`required` os torna inválidos de novo) apareciam com borda vermelha de erro bem ao lado da
mensagem de sucesso — nada quebrado funcionalmente, mas visualmente contraditório (parece erro
junto de "senha trocada com sucesso"). Corrigido trocando para
`@ViewChild(FormGroupDirective) formDirective` + `this.formDirective.resetForm()`, que reseta a
flag `submitted` junto com o valor/touched/dirty do `FormGroup`. Qualquer formulário novo deste
app que limpe a si mesmo após um submit bem-sucedido (em vez de navegar pra outra tela) deve usar
esse padrão, não `form.reset()` puro.

`app-side-nav`: link novo no rodapé (`side-nav__footer`, entre `app-theme-toggle` e o botão de
logout, ícone `lock_reset`) — não em `secondaryLinks` (grupo de analytics/relatórios), porque
troca de senha é configuração de conta; disponível pra **todo** usuário (sem checagem de role,
diferente do link `/users`). `MustChangePasswordBanner` ganhou um `routerLink` real pro botão de
ação (antes só tinha o botão de dispensar, porque o endpoint não existia).

## Navegação lateral (sidebar), animações no shell e no login (`epic-022` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-11). Fecha uma
divergência real: `docs/sistema-de-design.md` item 1 do inventário sempre especificou nav lateral,
mas a implementação real (desde `feat-002`) ficou como nav horizontal no topo — nunca corrigido
até esta feature. `app-side-nav` substitui `app-nav`: colapsável (ícone+texto expandido / só
ícone retraído, alternado manualmente, estado persistido como `Theme`/`Language`), submenus de
catálogo continuam `mat-menu` popup (mesmo comportamento de `epic-019`, só a barra host muda de
orientação). Tela de login perdeu o header duplo (barra de idioma/tema sempre visível + nav
horizontal quando autenticado) — idioma/tema viram controles flutuantes no canto inferior
esquerdo, sem barra, só na tela de login (não autenticado); nos demais estados, idioma/tema vivem
no rodapé do `app-side-nav`.

**Estilizar o painel de um overlay do CDK (`mat-menu`/`mat-select`) pelo tamanho de outro
elemento** (`web feat-033`): o painel renderiza fora do `:host` do componente, então CSS scoped
não alcança — precisa de `panelClass` (`[class]` no `<mat-menu>`) + `::ng-deep` no SCSS do
componente que o abre, não um arquivo global. Usado 2x: `language-selector.scss` (raio da borda)
e `app-side-nav.scss` (menu Cadastrar/Dashboard de cada recurso acompanha a largura da nav
quando expandida, `min-width: $width-expanded`, volta ao padrão do Material quando colapsada).

Motion pass (pedido do usuário, "bastante animações, bem fluido", orientado pela skill
`impeccable` — `.claude/skills/impeccable`, `docs/sistema-de-design.md`/`docs/habilidades-do-agente.md`
continuam a fonte normativa de paleta/layout, a skill só orienta motion/polish):
`withViewTransitions()` no router, transição de collapse/expand do sidebar, e uma animação
autoral no card de login (`app-login-border-trace`) — um traço verde sai do ponto central
superior em 2 direções, percorre cada lado, se encontra no ponto central inferior, e retrai de
volta, em loop enquanto a tela de login está visível. Implementado com 2 paths SVG
espelho-simétricos (garante comprimento igual sem medir) dimensionados via `ResizeObserver`, não
um tamanho fixo. Toda animação nova respeita `prefers-reduced-motion` (mesmo padrão já usado no
overlay de carregamento, ver [[sistema-de-design]] item 17: pula direto pro estado final em vez de pausar uma animação em andamento).

**Achados reais de QA visual** (screenshots reais contra o dev server, não só leitura de código):
(1) o painel de opções do seletor de idioma (`mat-select`) herdava a largura do *trigger* atual,
que encolhe pro idioma selecionado no momento — um idioma curto ("English") selecionado deixava o
painel estreito demais pro idioma mais longo ("Português"), cortando o texto; corrigido com
`min-width` no trigger, mantendo `mat-select`/`mat-option` intactos (evita quebrar os e2e que
localizam opções por `role="option"`). (2) a coluna expandida do sidebar (232px) comia quase a
tela inteira abaixo de ~600px, quebrando a regra "mobile = coluna única" (RNF01) que o resto do
app já seguia — corrigido com default retraído abaixo desse breakpoint quando o usuário não
escolheu explicitamente. (3) achado durante a implementação, não da QA visual: o rótulo flutuado
de um `mat-select`/`mat-form-field` (`label.mdc-floating-label`) mantinha `pointer-events: all`
nesta versão do Material em vez do `none` que o MDC normalmente daria — a coluna mais estreita do
formulário de registro de aposta (efeito colateral do sidebar reduzir o espaço disponível) expôs
esse bug latente, corrigido globalmente (ver `docs/convencoes.md`).

## Sobreposição do seletor de idioma no login (`epic-024` da raiz, `apps/web feat-023`, done)

Achado de usuário (2026-09-15, screenshot real): o pill do seletor de idioma (canto inferior
esquerdo da tela de login, ver seção anterior) aparecia sobreposto ao botão de tema ao lado,
cortando parte do ícone. Investigação real (medição de `getBoundingClientRect()` contra o dev
server, não só leitura de CSS) achou a causa exata: `.language-selector-host`
(`core/language-selector/language-selector.scss`) usava `display: block` envolvendo um filho
(`.language-selector`) com `width: 100%`. Enquanto o `app-side-nav` (sidebar) sempre dá a esse
componente uma largura definida (a própria coluna da sidebar), a tela de login o usa dentro de
`app.scss`'s `.app-shell__floating-controls` — um container `flex` **sem largura própria**
(shrink-to-fit, dimensionado pelos próprios filhos). Layout em bloco (`display: block`) não tem
regra bem definida de spec pra medir corretamente um filho com largura percentual nesse cenário
de auto-dimensionamento; o resultado medido: o `mat-select` renderizava 13–26px mais largo que o
próprio pill que deveria contê-lo, vazando sobre o botão de tema adjacente. Trocado pra `display:
flex` (mesmo modo de layout do filho) — Flexbox tem regra explícita pra esse caso (item flex com
largura percentual é tratado como `auto` pro dimensionamento intrínseco do próprio container,
CSS Flexbox §9.9) — sem efeito na sidebar, que nunca foi afetada.

**Achado secundário, mesma investigação**: a tela de login usava `min-height: 100dvh` num `:host`
com `align-items: center` — se o conteúdo (marca + card) excedesse a altura real disponível
(`.app-shell__content` clipa com `overflow:hidden`, ver seção "Navegação lateral" acima), o texto
crescia além da área visível sem nenhuma forma de rolar até ele, e a coluna de controles
flutuantes acabava sobre os próprios campos do formulário. Trocado pra `height: 100%` (o padrão
já usado por toda página roteada, ver `pages/period-report/period-report.scss`) +
`overflow-y: auto`, com `padding-bottom` reservando o espaço dos controles flutuantes e
`margin: auto 0` no lugar de `align-items: center` sozinho (técnica "flexbug #3": mantém o topo
do conteúdo alcançável por rolagem em vez de cortar os dois lados simetricamente). Residual aceito
(viewport extremamente curto, ex. celular em paisagem <450px de altura): o conteúdo ainda aparece
parcialmente atrás do pill na primeira renderização até o usuário rolar — cenário raro pra uma
tela de login, e a alternativa (reduzir o padding do `shared/panel` compartilhado por toda a
tela de login) arriscaria regressão em todas as outras páginas que o usam.

## Página "Relatório do período" (`epic-017` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal — layout livre, conteúdo normativo). Página nova, distinta do dashboard
consolidado (`epic-006`/`epic-015`) e da tela "Buscar Estatísticas" (`epic-012`) — visão fechada
do desempenho num período, **sempre com filtro de data** (reusa o mesmo componente de
presets/date-range de `epic-015`, sem período "sem filtro nenhum").

Combina 4 chamadas via `forkJoin` (mesmo padrão de `feat-004`/`005`/`008`/`epic-015`):
`GET /api/v1/statistics` (overall), `GET /api/v1/statistics/daily` (`epic-016`),
`GET /api/v1/bankroll/balance?at=<from|to>` (2x, `epic-013` — mesmas chamadas já usadas pelo
dashboard de `epic-015`, reaproveitadas aqui) e `GET /api/v1/settings` (`unitPercent`,
`epic-013`).

Tudo o resto é calculado no cliente, sem campo novo de backend além de `epic-016`: tabela de dias
(preenchendo com zero os dias sem aposta que não vêm no array esparso), profit em unidades e R$,
`roiBankroll` (**distinto** do `roi` já existente — ver [[estatisticas]]), ROI médio diário ("Average
Profit"), stake médio (`totalStaked/settledCount`, já existe desde `feat-006`), dias
green/red, taxa de acerto das entradas sem `void` e `+EV`. Fórmulas completas e a decisão de
deixar "Cashout Favor/Contra" (do print de referência) fora do escopo em [[estatisticas]] seção
"Métricas da página \"Relatório do período\"".

> **Implementado em `web feat-015`** sem divergência do planejado. Decisão do plan review (única
> não coberta explicitamente pelo escopo do epic): "saldoAtual" nas fórmulas desta página (usado
> por `roiUnidades`/`profitUnidades`) resolve para `saldoFinal` (`saldoEm(to)`) — esta página faz
> só 2 chamadas de bankroll (`at=from`/`at=to`, sem uma 3ª "agora" separada), diferente do
> dashboard consolidado. Módulo de cálculo puro (`period-report-metrics.ts`) testado contra os
> valores do print de referência do usuário como oráculo independente — achado real: a própria
> nota do vault tinha um erro de aritmética no exemplo de `+EV` (`37,00% − 31,06% = 5,98%` estava
> escrito, o correto é `5,94%`), corrigido em [[estatisticas]] no mesmo commit deste fechamento.

## Tela "Buscar Estatísticas" (`epic-012` da raiz, planejado)

Tela nova, distinta do dashboard consolidado (feat-006) — fonte de verdade para decisão
pré-aposta, não visão geral de desempenho já ocorrido. Formulário de busca: esporte e liga
obrigatórios (validação client-side, reforçada pelo backend — ver [[contratos-de-api]]
`GET /api/v1/statistics/search`), time/casa de apostas/mercado/tipster/período opcionais.
Resultado em cards (ROI, taxa de acerto, odd média, volume/lucro líquido, drawdown máximo,
Índice de Sharpe simplificado — fórmulas em [[estatisticas]]) mais um gráfico de linha da série
`timeline` (equity curve/lucro acumulado da combinação buscada, mesma série usada pro cálculo de
drawdown, sem chamada extra). Estado vazio (nenhuma busca feita ainda, ou combinação sem apostas
liquidadas) precisa de tratamento explícito — não é o mesmo caso de "carregando".

## Selects de filtro pesquisáveis (`apps/web feat-031`, done)

Achado do usuário a partir do painel "Filtros" de `search-statistics` (feat-012): campos de
catálogo (esporte/liga/time/casa de apostas/mercado/tipster) eram `mat-select` fechado —
inviável de rolar manualmente conforme o catálogo do tenant cresce. `shared/searchable-select`
novo: wrapper sobre `mat-autocomplete` implementando `ControlValueAccessor` — mesmo uso via
`formControlName` que o `mat-select` anterior, filtro por nome case+acento-insensível
(`normalizeForSearch`, sem dependência nova), opção sentinela (`allOptionLabel`, ex. "Todos"/
"Nenhum") e suporte a `disabled` (cobre `register-bet` team1Id/team2Id, desabilitados até um
esporte ser escolhido). Substituiu `mat-select` em ~20 campos de 5 telas (`register-bet`,
`team-manager`, `search-statistics`, `dashboard`, `history`) — `catalog-manager` e
`period-preset-filter` confirmados sem mudança (nenhum tem select de catálogo).

**Zero e2e por página precisou de edição** — todo teste já interagia via
`getByTestId(...).click()` + `getByRole('option', {name}).click()`, e `mat-autocomplete` também
renderiza `mat-option` com `role="option"`, só o alvo do `testId` mudou (de `<mat-select>` pro
`<input>` interno). Única exceção: `betting-houses-move-balance.spec.ts` usava `toContainText`
pro valor pré-selecionado — corrigido pra `toHaveValue` (ver [[testes]] "Frontend (apps/web)"
para o porquê). 3 gotchas reais de implementação também documentados lá: `mat-error` nunca ativa
sem `ngControl` (resolvido com `<p role="alert">` próprio em vez de brigar com o mecanismo do
Material), `:host { display: contents }` necessário pro host do componente não virar item extra
de flex/grid nas telas com filtro em `flex-wrap`, e duplo de teste precisa de `signal()` real
(não propriedade mutável simples) pra repropagar num segundo `detectChanges()` sob CD zoneless.

`errorMessage` (opcional) plugado em `search-statistics` (sportId/leagueId, `Validators.required`)
— renderiza a mesma mensagem de antes, só que fora do `mat-form-field`.

## Página "Comparativo de períodos" (`epic-031` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-22). Tela nova
(`/period-comparison`), distinta do dashboard consolidado, de "Relatório do período" e de
"Buscar Estatísticas" — compara 2 períodos escolhidos livremente pelo usuário (ex.: 1º semestre
de 2026 vs 1º semestre de 2025), lado a lado. Zero endpoint novo — client-side, reaproveitando
`GET /api/v1/statistics(/daily)`, `GET /api/v1/bankroll/balance`, `GET /api/v1/settings` (já
existentes desde `epic-013/014/016/018`), cada um disparado 2x por `applyFilter()` (uma vez por
período). 2 instâncias de `shared/period-preset-filter` (Período A/B, seeds já resolvidos em vez
de vazios — ver [[testes]] para o achado real de flake corrigido no caminho) + o mesmo bloco de
filtros comuns do dashboard (esporte/liga/mercado/casa de apostas/tipster), aplicado igualmente
aos 2 lados.

3 peças novas, todas dedicadas a esta tela (nenhuma reaproveita/adapta um componente existente
que já tinha 5+ consumidores — decisão do Plan Reviewer, ver `plan_review` em
`apps/web/feature_list.json` feature `feat-037`):

- `shared/comparison-metric-row` — 14 linhas de KPI (rótulo | valor A | valor B | delta),
  padrão "linha de lista"/"valor + variação" já documentado em [[sistema-de-design]], não 3
  `kpi-card` por métrica. Só `netProfit`/`roi` recebem cor no delta (mesma discrição do
  `kpi-card` em outras telas — um número indo pra cima/baixo não é inerentemente bom/ruim).
- `shared/comparison-equity-chart` — 2 séries sobrepostas (Período A em `--color-brand`, Período
  B em `--color-action-neutral`), eixo por índice de dia dentro de cada período (não data
  calendário), sem reset — `core/chart-theme.ts:buildComparisonLineChartOption` estende o
  builder de série única já existente. Curva do período mais curto some (não achata) além do
  próprio tamanho.
- `pages/period-comparison/segment-comparison-table` — ROI/lucro líquido comparados por item de
  cada segmento (esporte/liga/mercado/tipster/casa de apostas/tipo de aposta), 6 instâncias.
  União dos itens presentes em A OU B (não interseção); lado ausente mostra "Indeterminado", não
  0 — um item pode só ter tido aposta liquidada em um dos 2 períodos.

Achado real de QA visual corrigido no caminho: abaixo de 600px o cabeçalho de coluna
(Período A/B/Diferença) some e uma linha de 4 colunas não cabe — `comparison-metric-row` ganhou
auto-rotulação via `data-mobile-label`/`::before` só nessa largura (mecanismo reaproveitável,
ver [[sistema-de-design]] seção "Layout em painéis").

## Ver também

- [[auth-service]], [[bets-service]], [[stats-service]] — APIs consumidas via API Gateway.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (item 11: operador usa API
  direta, sem UI de provisionamento; `role = member` não vê a tela de gestão de usuários).
