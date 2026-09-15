---
tags: [service, frontend]
---

# web

Angular 21.x + TypeScript ES2025, SPA. Ver [[ARCHITECTURE]] para o panorama geral,
[[REQUIREMENTS]] para RF/RNF completos, [[DESIGN-SYSTEM]] para tema (claro/escuro), paleta de
cores e inventário de componentes, e [[CONVENTIONS]] seção "Internacionalização (i18n)" para a
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
absoluto, ver [[OBSERVABILITY-AND-CONFIG]] seção "Configuração de `apps/web`") — sem proxy `/api`
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
  [[API-CONTRACTS]]), sem UI própria em `apps/web` (decisão de 2026-08-02, ver [[DECISIONS-LOG]]
  item 11). Esse é o único passo do fluxo sem equivalente no caso de uso original do TCC1 (UC01
  não previa um segundo ator "operador").
- **Gestão de usuários do tenant** (tela nova, substitui a antiga tela de "cadastro" público):
  visível **apenas** para o usuário logado com `role = admin` do tenant — `role = member` **não
  vê essa tela de forma alguma** (nem em modo somente leitura, decisão de 2026-08-02, ver
  [[DECISIONS-LOG]] item 11). É a implementação de UC01 ("Manter usuário") do diagrama original,
  só que restrita a quem pode acioná-la; continua sendo o próprio usuário (o admin) quem cria os
  demais, não o operador da plataforma. Lista os usuários do tenant e permite criar novos
  (`role = member`) — usa o mesmo layout em painéis (ver [[DESIGN-SYSTEM]] item 13, "Lista de
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

## Dashboards e filtros (RN08)

Filtros por período, casa de apostas, esporte, liga, mercado e tipster devem recalcular as
métricas dinamicamente — não são apenas um filtro client-side sobre dados já carregados; cada
mudança de filtro é uma nova consulta a `GET /api/v1/statistics`, que responde um bundle único
com todas as vistas do dashboard de uma vez (ver [[stats-service]]). Rótulos de filtro na UI são
localizados (ver [[CONVENTIONS]]) mesmo os query params enviados sendo sempre em inglês —
**corrigido em `feat-006`**: os nomes reais implementados usam sufixo `Id` (`bettingHouseId`,
`sportId`, `leagueId`, `marketId`, `tipsterId`) mais `from`/`to` (data, `yyyy-MM-dd`), não
`sport`/`league`/`market` como esta nota dizia antes — mesma correção de nomenclatura já feita em
[[API-CONTRACTS]] para `bets-service`, só não tinha sido propagada até aqui.

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
inicial do período, saldo final do período. Fórmulas completas em [[STATISTICS]].

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
> `docs/DESIGN-SYSTEM.md`, evita dependência nova para 1 par de campos) fica em `shared/` porque
> `epic-017` ("Relatório do período") reusa o mesmo componente. Mudança de comportamento
> intencional: o dashboard agora aplica o preset "Hoje" por padrão no load (antes carregava sem
> filtro nenhum) — mudanças de período aplicam na hora, os 5 filtros de catálogo continuam atrás
> do botão "Aplicar filtro" existente. `StatisticsApi.BetMetrics` (frontend) nunca tinha sido
> atualizado desde `feat-006`, apesar do backend (`stats-service epic-014`) já expor
> `wonCount`/`lostCount`/`voidCount`/`preCount`/`liveCount`/`avgOdd` há várias sessões — gap real
> fechado aqui, escopo restrito só aos 6 campos que os cards desta feature consomem
> (`byBetType`/`byLeague`/`byTipster` ficam para quando `epic-019`/`epic-021` precisarem deles).

## Tela "Visão geral" pós-login (`epic-021` da raiz, planejado)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal). Tela nova, distinta das outras 5 desta rodada — visão de **vida inteira do
tenant**, a única desta rodada **sem filtro de período** (por definição: "todo o período do
tenant"). Curva de lucro acumulado em unidades **contínua, nunca reseta** (diferente da grade de
`epic-020`, que reseta por mês) desde a primeira aposta liquidada do tenant. Tabela mensal
(Jan–Dez do ano corrente): saldo Começo/Final (derivado client-side de 1 única chamada a
`GET /api/v1/bankroll/balance` + o próprio lucro diário já buscado para a curva, sem 1 chamada
por mês — ver [[STATISTICS]]), entradas/vitórias/perdas, odd média, taxa de acerto, ROI,
profit em R$/unidades — tudo já vem de `monthly[]` (`feat-006` + campos novos de `epic-014`, já
aninhados lá). Cards: Lucro Total, Pré/Live (`byBetType` novo, `epic-014`), Lucro Médio Mensal
(`lucroTotalUnidades / 12`, fórmula nova) e ROI (reaproveita `roiMedioDiario` de `epic-017`, sem
filtro de período). Decisão de UX **não fechada nesta sessão** (fica pro plan review): se esta
tela substitui o redirect pós-login atual (hoje vai pra `/dashboard`, `feat-002`) ou é só um link
novo na nav.

## Dashboard — grade de gráficos mensais de drawdown (`epic-020` da raiz, planejado)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-10, referência: print
de planilha pessoal — grade de mini-gráficos de linha, um por mês). Seção/aba nova dentro do
dashboard consolidado (`epic-006`/`epic-015`), não página separada. **Revisado 2026-09-10, mesma
sessão**: filtro de 2 date pickers (início/fim), não mais navegação por ano fixo com setas —
quantidade de mini-gráficos **dinâmica** (1 por mês do intervalo). Intervalo trava em fronteira
de mês: `from` = dia 01 do mês do picker inicial, `to` = último dia do mês do picker final
(30/31 conforme o mês) — independente do filtro de período com presets de `epic-015`. Uma
chamada a `GET /api/v1/statistics/daily` (`epic-016`) cobrindo o intervalo inteiro; cliente
agrupa por mês e calcula a curva acumulada em unidades (ver [[STATISTICS]] "Grade de gráficos
mensais de drawdown" para a fórmula — reset só na virada de mês, dia sem aposta carrega o valor
anterior). Zero backend novo. Grade com N mini-gráficos (`ngx-echarts`, mesmo padrão de
`shared/monthly-profit-chart` de `feat-006`, layout acomodando contagem variável) via 1
componente parametrizado por mês, reaproveitado N vezes — mesmo precedente de `feat-008`/
`epic-019` para não reincidir no achado de duplicação do SonarCloud.

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
> no app — gotcha de limpeza em teste unitário documentado em [[TESTING]]) com um helper
> `isResourceActive()` pra destacar o gatilho ativo, já que o botão-gatilho de um `mat-menu` não é
> ele mesmo um `routerLink` (`routerLinkActive` sozinho não o alcança).

## Navegação lateral (sidebar), animações no shell e no login (`epic-022` da raiz, done)

Escopo novo, fora do backlog original do TCC1 (pedido do usuário, 2026-09-11). Fecha uma
divergência real: `docs/DESIGN-SYSTEM.md` item 1 do inventário sempre especificou nav lateral,
mas a implementação real (desde `feat-002`) ficou como nav horizontal no topo — nunca corrigido
até esta feature. `app-side-nav` substitui `app-nav`: colapsável (ícone+texto expandido / só
ícone retraído, alternado manualmente, estado persistido como `Theme`/`Language`), submenus de
catálogo continuam `mat-menu` popup (mesmo comportamento de `epic-019`, só a barra host muda de
orientação). Tela de login perdeu o header duplo (barra de idioma/tema sempre visível + nav
horizontal quando autenticado) — idioma/tema viram controles flutuantes no canto inferior
esquerdo, sem barra, só na tela de login (não autenticado); nos demais estados, idioma/tema vivem
no rodapé do `app-side-nav`.

Motion pass (pedido do usuário, "bastante animações, bem fluido", orientado pela skill
`impeccable` — `.claude/skills/impeccable`, `docs/DESIGN-SYSTEM.md`/`docs/AGENT-SKILLS.md`
continuam a fonte normativa de paleta/layout, a skill só orienta motion/polish):
`withViewTransitions()` no router, transição de collapse/expand do sidebar, e uma animação
autoral no card de login (`app-login-border-trace`) — um traço verde sai do ponto central
superior em 2 direções, percorre cada lado, se encontra no ponto central inferior, e retrai de
volta, em loop enquanto a tela de login está visível. Implementado com 2 paths SVG
espelho-simétricos (garante comprimento igual sem medir) dimensionados via `ResizeObserver`, não
um tamanho fixo. Toda animação nova respeita `prefers-reduced-motion` (mesmo padrão já usado no
splash: pula direto pro estado final em vez de pausar uma animação em andamento).

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
esse bug latente, corrigido globalmente (ver `docs/CONVENTIONS.md`).

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
`roiBankroll` (**distinto** do `roi` já existente — ver [[STATISTICS]]), ROI médio diário ("Average
Profit"), stake médio (`totalStaked/settledCount`, já existe desde `feat-006`), dias
green/red, taxa de acerto das entradas sem `void` e `+EV`. Fórmulas completas e a decisão de
deixar "Cashout Favor/Contra" (do print de referência) fora do escopo em [[STATISTICS]] seção
"Métricas da página \"Relatório do período\"".

> **Implementado em `web feat-015`** sem divergência do planejado. Decisão do plan review (única
> não coberta explicitamente pelo escopo do epic): "saldoAtual" nas fórmulas desta página (usado
> por `roiUnidades`/`profitUnidades`) resolve para `saldoFinal` (`saldoEm(to)`) — esta página faz
> só 2 chamadas de bankroll (`at=from`/`at=to`, sem uma 3ª "agora" separada), diferente do
> dashboard consolidado. Módulo de cálculo puro (`period-report-metrics.ts`) testado contra os
> valores do print de referência do usuário como oráculo independente — achado real: a própria
> nota do vault tinha um erro de aritmética no exemplo de `+EV` (`37,00% − 31,06% = 5,98%` estava
> escrito, o correto é `5,94%`), corrigido em [[STATISTICS]] no mesmo commit deste fechamento.

## Tela "Buscar Estatísticas" (`epic-012` da raiz, planejado)

Tela nova, distinta do dashboard consolidado (feat-006) — fonte de verdade para decisão
pré-aposta, não visão geral de desempenho já ocorrido. Formulário de busca: esporte e liga
obrigatórios (validação client-side, reforçada pelo backend — ver [[API-CONTRACTS]]
`GET /api/v1/statistics/search`), time/casa de apostas/mercado/tipster/período opcionais.
Resultado em cards (ROI, taxa de acerto, odd média, volume/lucro líquido, drawdown máximo,
Índice de Sharpe simplificado — fórmulas em [[STATISTICS]]) mais um gráfico de linha da série
`timeline` (equity curve/lucro acumulado da combinação buscada, mesma série usada pro cálculo de
drawdown, sem chamada extra). Estado vazio (nenhuma busca feita ainda, ou combinação sem apostas
liquidadas) precisa de tratamento explícito — não é o mesmo caso de "carregando".

## Ver também

- [[auth-service]], [[bets-service]], [[stats-service]] — APIs consumidas via API Gateway.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (item 11: operador usa API
  direta, sem UI de provisionamento; `role = member` não vê a tela de gestão de usuários).
