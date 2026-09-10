---
tags: [statistics, stats-service, web]
---

# Fórmulas e conceitos estatísticos

Nota canônica das métricas calculadas por [[stats-service]] e apresentadas em [[web]] (dashboard,
RF10/RF11, e a tela "Buscar Estatísticas", `epic-011`/`epic-012`). Toda fórmula nova documentada
aqui **antes** de ser implementada — se este arquivo e o código divergirem, é achado de auditoria
(ver `docs/CONVENTIONS.md`).

## Escopo de elegibilidade (RN06)

Todas as métricas abaixo, exceto quando dito o contrário, filtram `FACT_BET` por
`status IN ('won', 'lost', 'void')` — nunca `'pending'` (RN06, ver [[stats-service]]). Uma aposta
pendente não tem `profit`/`isWin` definidos e não deve enviesar nenhum indicador.

## Métricas do dashboard consolidado (RF09, RN04, implementadas desde `stats-service feat-004`)

### ROI agregado (RN04)

```
ROI = lucroLiquidoAcumulado / valorTotalInvestido
    = SUM(profit) / SUM(stake)          (apostas liquidadas do recorte)
```

Fonte teórica: TCC1 cap. 2.5, citando Bodie, Kane e Marcus (2014) — retorno sobre investimento
como indicador nominal de desempenho. RN09 aplica a mesma fórmula por segmento (esporte/mercado/
casa/time) — sempre sobre o subconjunto daquele agrupamento, nunca a base inteira.

### Taxa de acerto (win rate)

```
taxaDeAcerto = apostasGanhas / apostasLiquidadas
```

**`apostasLiquidadas` inclui `void`** (devolvida) — decisão de interpretação registrada em
`stats-service feat-004` (RN06 já inclui `void` na agregação; RN04/RN09 não desambiguam o
denominador da taxa de acerto). Uma aposta devolvida conta no denominador sem contar como vitória
nem derrota.

### Lucro/prejuízo líquido e volume

```
lucroLiquido = SUM(profit)              (apostas liquidadas do recorte)
volumeApostado = SUM(stake)             (apostas liquidadas do recorte)
```

Cálculo de `profit` por aposta individual (RN02/RN03, aplicado por `bets-service` na liquidação,
não recalculado aqui): `profit = stake * odd - stake` se ganha; `profit = -stake` se perdida;
`profit = 0` se devolvida.

## Métricas novas do dashboard consolidado (`epic-013`/`epic-014`/`epic-015`, pedido do usuário 2026-09-10)

Reespecificação do dashboard já entregue em `stats-service feat-006`/`web feat-006` (ambos
`done`) — extensão do bundle consolidado, distinta das métricas de decisão pré-aposta da tela
"Buscar Estatísticas" (seção seguinte). Três delas vêm do `stats-service` (`epic-014`), duas do
`bets-service` (`epic-013`), uma é calculada inteiramente no cliente (`epic-015`) — ver aquelas
notas para o porquê da divisão.

### Vitórias/derrotas (contagens brutas) e odd média

```
apostasVencidas = COUNT(*)                  WHERE isWin = true  (apostas liquidadas do recorte)
apostasPerdidas = COUNT(*)                  WHERE isWin = false (apostas liquidadas do recorte, exclui void)
oddMedia        = AVG(odd)                  (apostas liquidadas do recorte)
```

`apostasVencidas`/`apostasPerdidas` são os números absolutos por trás da taxa de acerto já
existente (`taxaDeAcerto = apostasGanhas / apostasLiquidadas`, seção acima) — apresentados juntos
no card, não substituem a fração. `oddMedia` reaproveita a mesma coluna `odd` de `FACT_BET`
introduzida por `epic-011` (persistência compartilhada entre as duas epics — a que implementar
primeiro grava a coluna, ver `docs/services/stats-service.md`).

### Contagem por tipo (PRÉ/LIVE)

```
apostasPre  = COUNT(*)  WHERE betType = 'PRE'   (apostas liquidadas do recorte)
apostasLive = COUNT(*)  WHERE betType = 'LIVE'  (apostas liquidadas do recorte)
```

`betType` vira enum (`PRE`/`LIVE`) em `bets-service` nesta rodada (`epic-013`) — antes era texto
livre sem valores fixos, o que tornaria este agrupamento uma fragmentação de string em vez de uma
métrica confiável (decisão do usuário, 2026-09-10). Apostas registradas antes da migração ficam
com `betType` nulo e **não entram em nenhum dos dois buckets** — `apostasPre + apostasLive` pode
ser menor que o total de apostas liquidadas do recorte.

### Saldo inicial/final do período

```
saldoEm(data) = SUM(BETTING_HOUSE.initialBalance)                              [todas as casas]
              + SUM(TRANSACTION.amount, assinado por type, createdAt <= data)  [todas as casas]
              + SUM(BET_RESULT.profit, settledAt <= data)                      [todas as casas]

saldoInicial = saldoEm(from)
saldoFinal   = saldoEm(to)
```

Calculado inteiramente em `bets-service` (`GET /api/v1/bankroll/balance?at=<data>`, `epic-013`),
**não** replicado para o esquema estrela de `stats-service` — é dado transacional (saldo é
domínio de `bets-service`, que já mantém `initialBalance`/`TRANSACTION`/`BET_RESULT`), trazer uma
cópia pro OLAP via evento novo (`BettingHouseCreated`/`TransactionCreated`) foi avaliado e
descartado por esta sessão (complexidade desproporcional ao ganho — `bets-service` já calcula
`balance` corrente do mesmo jeito desde `feat-005`, só faltava o parâmetro `at` pra ponto no
tempo). **Corte por `settledAt` (liquidação), não por `betDate` (data do jogo)** — o saldo só se
move quando o resultado é realizado, não quando a partida acontece; uma aposta cujo jogo foi em
`from` mas que só liquidou depois de `to` não deve mexer no saldo do período. Soma **todas as
casas de apostas do tenant** (decisão do usuário, 2026-09-10) — sem filtro por `bettingHouseId`
nesta métrica especificamente, mesmo que o dashboard tenha outros filtros aplicados.

### Unidades apostadas

```
unidadesApostadas = totalStaked(período) / (saldoAtual × unitPercent)
```

**Calculado no cliente** (`apps/web`, `epic-015`), não em nenhum backend — combina `totalStaked`
já devolvido por `GET /api/v1/statistics` (`stats-service`) com `saldoAtual` (`GET
/api/v1/bankroll/balance` sem `at`, ou seja "agora") e `unitPercent` (`GET /api/v1/settings`,
ambos `bets-service`). "Unidade" aqui é um **percentual configurável da banca** (decisão do
usuário, 2026-09-10: não é um valor fixo em R$ nem digitado por aposta), default 1%, editável em
`PATCH /api/v1/settings` (admin-only). **Simplificação deliberada**: usa o `unitPercent` e o
`saldoAtual` **vigentes agora**, aplicados retroativamente ao `totalStaked` do período inteiro —
não versiona o percentual nem recalcula unidade por aposta com o saldo que existia naquele
momento específico (exigiria uma tabela de histórico de configuração e o mesmo cálculo
`saldoEm(betDate)` por aposta, não só duas datas de corte). Se o usuário mudar `unitPercent` no
meio do período filtrado, `unidadesApostadas` recalcula tudo com o valor novo — aceito por
simplicidade, revisitar se o usuário achar o resultado confuso na prática.

## Métricas da página "Relatório do período" (`epic-016`/`epic-017`, pedido do usuário 2026-09-10)

Página nova, fora do backlog original do TCC1 — pedido a partir de um print de planilha pessoal
do usuário (layout livre, só o conteúdo é normativo). Quase tudo é calculado no cliente
(`apps/web`) combinando campos que já existem (`GET /api/v1/statistics`, `GET
/api/v1/statistics/daily` de `epic-016`, `GET /api/v1/bankroll/balance`/`GET /api/v1/settings` de
`epic-013`) — só a quebra diária (`epic-016`) é backend novo.

### Quebra diária

`GET /api/v1/statistics/daily` devolve `{date, totalStaked, netProfit, roi, betCount}` por dia
**com pelo menos 1 aposta liquidada** dentro do período — dias sem aposta não vêm na resposta
(array esparso); o cliente preenche com zero os dias faltantes do intervalo `from`..`to` antes de
montar a tabela. `roi` por dia usa a mesma fórmula já existente (`netProfit/totalStaked` daquele
dia).

### ROI sobre banca ("ROI Bankroll") — distinto do ROI existente

```
roiBankroll = lucroLiquido(período) / saldoInicial(período)
            = netProfit / saldoEm(from)
```

**Não é o mesmo `roi` já existente** (`netProfit/totalStaked`, seção "Métricas do dashboard
consolidado") — este divide pelo **saldo no início do período**, não pelo volume apostado.
Confirmado contra o print de referência do usuário: `264,20 / 1195,05 = 22,11%`. Nomear
diferente na UI (`roiBankroll` vs `roi`) para não confundir as duas.

### ROI médio diário ("Average Profit")

```
roiMedioDiario = média(roi_dia)     para cada dia com pelo menos 1 aposta liquidada
```

Média simples, **não ponderada** por volume apostado — cada dia conta igual, diferente de
`roiBankroll`/`roi` (que são uma razão de somas). Decisão do usuário (2026-09-10, `AskUserQuestion`):
esta é a leitura de "Average Profit" do print de referência, distinta de "ROI Bankroll" ao lado.

### Profit em unidades

```
profitUnidades = lucroLiquido(período) / (saldoAtual × unitPercent)
```

Mesma conversão de `unidadesApostadas` (seção "Métricas novas do dashboard consolidado" acima),
aplicada ao `netProfit` em vez de ao `totalStaked` — mesma simplificação deliberada (usa
`saldoAtual`/`unitPercent` vigentes, não históricos).

### Taxa de acerto das entradas (excluindo devolvidas) e +EV

```
taxaDeAcertoEntradas = apostasGanhas / (apostasGanhas + apostasPerdidas)   [void EXCLUÍDO do denominador]
```

**Diferente da taxa de acerto já existente** (`taxaDeAcerto = apostasGanhas / apostasLiquidadas`,
que inclui `void` no denominador) — esta é só "vitórias contra derrotas", sem contar devolvidas
de nenhum dos lados. Confirmado contra o print de referência: `74 / (74 + 126) = 37,00%`.

```
EV = taxaDeAcertoEntradas − (1 / oddMedia)
```

Fórmula confirmada pelo usuário (2026-09-10) contra os números do print de referência:
`37,00% − (1 / 3,22) = 37,00% − 31,06% = 5,98%` — bate com o `+EV` mostrado. `1 / oddMedia` é a
probabilidade implícita da odd média (sem descontar a margem da casa) — `EV` positivo indica que
a taxa de acerto real do usuário superou o que a odd média "precificava" como necessário para
empatar. Casos-limite: sem apostas liquidadas no período (denominador zero) → `EV` indefinido
(`null`), mesmo tratamento de outras razões com denominador zero neste documento.

### Dias e entradas "green"/"red"

```
diasVerdes = COUNT(dia)  WHERE netProfit(dia) > 0   [só dias com pelo menos 1 aposta]
diasVermelhos = COUNT(dia)  WHERE netProfit(dia) < 0
diasTrabalhados = diasVerdes + diasVermelhos          (dias com netProfit = 0 não somam nenhum dos dois)
```

`apostasVencidas`/`apostasPerdidas` (rótulo "Entradas Green/Red" no print de referência) são os
mesmos `wonCount`/`lostCount` já descritos na seção "Vitórias/derrotas" acima — sem cálculo novo,
só outro rótulo/apresentação nesta página.

### Fora de escopo: cashout antecipado

O print de referência do usuário tinha um card "Cashout Favor/Contra" — **não implementado**
(decisão do usuário, 2026-09-10, `AskUserQuestion`): cashout antecipado (encerrar uma aposta
antes do fim do jogo por valor parcial) não existe no domínio de `bets-service` hoje (só
`pending`/`won`/`lost`/`void`) e exigiria um mecanismo novo inteiro (status adicional, valor de
cashout). Fora do escopo de `epic-016`/`epic-017`.

## Grade de gráficos mensais de drawdown (`epic-020`, pedido do usuário 2026-09-10)

Seção nova dentro do dashboard consolidado (`epic-006`/`epic-015`) — grade de 12 mini-gráficos
(Janeiro..Dezembro do ano selecionado), cada um a curva de lucro/prejuízo **acumulado em
unidades**, resetando a cada mês:

```
diasDoMes = todo dia de 1..N do mês (calendário, N = 28/29/30/31)
profitUnidadesDia = netProfit(dia) / (saldoAtual × unitPercent)     (0 se não houve aposta liquidada naquele dia)
acumulado[1] = profitUnidadesDia(dia 1)
acumulado[i] = acumulado[i-1] + profitUnidadesDia(dia i)            para i > 1
```

**Reseta só na virada de mês** (dia 1 de cada mês recomeça em 0) — dentro do mês, um dia sem
aposta **carrega o acumulado igual ao dia anterior** (linha reta), não zera no meio da curva.
Mesma conversão de unidades de `profitUnidades` (seção "Métricas novas do dashboard consolidado"
acima) — mesma simplificação deliberada (`saldoAtual`/`unitPercent` vigentes, não históricos).
Fonte: `GET /api/v1/statistics/daily` (`epic-016`) com `from`/`to` cobrindo o intervalo
selecionado, agrupado por mês no cliente — nenhum endpoint novo, nenhum campo novo de backend.

**Revisado 2026-09-10, mesma sessão**: navegação por 2 date pickers (início/fim), não mais por
ano fixo com setas — a quantidade de mini-gráficos é **dinâmica** (1 por mês coberto pelo
intervalo, não fixo em 12). O intervalo trava em fronteira de mês, não no dia exato clicado:

```
from = dia 01 do mês do date picker inicial
to   = último dia do mês do date picker final (30/31 conforme o mês)
```

Continua distinto dos presets de período de `epic-015` (Hoje/semana/mês etc.) — filtro de *range
de meses* dedicado desta seção, não reaproveitado.

Apesar do rótulo popular "gráfico de drawdown" (nome dado pelo usuário, mantido na UI), esta
curva **não é o `drawdownMaximo`** já definido na seção "Métricas novas da tela 'Buscar
Estatísticas'" abaixo (aquele é um único número, pico-a-vale sobre uma combinação de filtro
específica) — é a curva de patrimônio acumulado bruta, mês a mês, sem nenhum cálculo de
pico/vale sobre ela nesta feature.

## Tela "Visão geral" — curva vitalícia e resumo mensal (`epic-021`, pedido do usuário 2026-09-10)

Tela pós-login, sem filtro de período (escopo = todo o histórico do tenant) — referência: print de
planilha pessoal do usuário.

### Curva de lucro acumulado vitalícia

```
diasComAposta = todo dia com pelo menos 1 aposta liquidada, do primeiro dia do tenant até hoje
acumulado[1] = profitUnidadesDia(dia 1)
acumulado[i] = acumulado[i-1] + profitUnidadesDia(dia i)     para i > 1, NUNCA reseta
```

**Diferente da grade de `epic-020`** (12 curvas que resetam a cada mês) — aqui é uma curva
**única e contínua**, desde a primeira aposta liquidada do tenant. Mesma fonte
(`GET /api/v1/statistics/daily`, `epic-016`) e mesma conversão de unidades (`profitUnidades`),
só sem `from`/`to` (histórico completo) e sem reset mensal.

### Saldo Começo/Final por mês, sem N chamadas

```
saldoInicioHistorico = GET /api/v1/bankroll/balance?at=<primeiro dia com aposta>   (1 única chamada)
saldoComeco(mês N) = saldoInicioHistorico + SUM(netProfit de todo dia antes do mês N)
saldoFinal(mês N)  = saldoComeco(mês N) + SUM(netProfit dos dias do mês N)
```

As somas usam o mesmo `GET /api/v1/statistics/daily` já buscado para a curva — evita chamar
`GET /api/v1/bankroll/balance` uma vez por mês (13 chamadas pro ano); só a mais antiga é
necessária, o resto deriva do próprio lucro diário já em mãos.

### Lucro médio mensal

```
lucroMedioMensal = lucroTotalUnidades / 12
```

**Divide sempre por 12** (meses do ano corrente), não pelo número de meses com atividade —
confirmado contra o print de referência do usuário: `22,11u / 12 = 1,84u`. Diferente de
`roiMedioDiario` (seção "Métricas da página 'Relatório do período'" acima), que só entra dias com
aposta no denominador.

### Lucro por tipo (Pré/Live)

```
lucroPreUnidades  = byBetType[PRE].netProfit  / (saldoAtual × unitPercent)
lucroLiveUnidades = byBetType[LIVE].netProfit / (saldoAtual × unitPercent)
```

`byBetType` é o 6º segmento de `GET /api/v1/statistics` (`epic-014`, mesmo formato de
`bySport`/`byMarket`/`byBettingHouse`/`byLeague`/`byTipster`) — 2 buckets fixos, apostas sem
`betType` classificado não entram em nenhum dos dois.

## Métricas novas da tela "Buscar Estatísticas" (`epic-011`, RF09 estendido)

Fundamentação teórica: TCC1 cap. 2.4/2.5 — gestão de bankroll como ativo financeiro estruturado
(Galekwa et al., 2025), onde métricas nominais (ROI, taxa de acerto) são insuficientes para
avaliar sustentabilidade do capital sem indicadores de variabilidade/risco (Sharpe, 1994;
drawdown). Diferente do dashboard consolidado (bundle único, todos os filtros opcionais,
`stats-service feat-006`), esta tela exige esporte+liga como filtro mínimo e responde uma
combinação específica — os indicadores abaixo dependem de iterar a série de apostas liquidadas
daquele recorte, não só um agregado SQL simples.

### Odd média

```
oddMedia = AVG(odd)                     (apostas liquidadas do recorte)
```

Indicador direto de "quão favorável, em média, o apostador está entrando" naquela combinação —
não citado literalmente no TCC1, mas decorre diretamente do pedido do usuário ("odd média") e do
campo `odd` já capturado em toda aposta (RN07: odd > 1.00).

### Drawdown máximo

Maior queda pico-a-vale no lucro acumulado, em valor absoluto (mesma unidade de `stake`/`profit`
— não percentual, pois o recorte filtrado não tem um capital-base próprio isolado do resto da
banca):

```
apostas ordenadas por betDate crescente (data do JOGO, nao de quando a aposta foi
registrada nem de quando foi liquidada), liquidadas do recorte
acumulado[i] = SUM(profit[0..i])
pico[i] = MAX(acumulado[0..i])
drawdown[i] = pico[i] - acumulado[i]
drawdownMaximo = MAX(drawdown[i])       para todo i
```

> **`betDate` = data do jogo** (decisão do usuário, 2026-09-10) — não a data de registro da
> aposta nem a de liquidação. `stats-service` guarda essa data em `DIM_DATE`/`dateId`,
> resolvida a partir de `BetCreated.betDate` no *insert* inicial. Achado real durante o plan
> review de `epic-011`: `processSettled` (upsert de `BetSettled`) recalculava `dateId` a partir
> de `settledAt`, sobrescrevendo o `dateId` correto do jogo com a data de liquidação — corrigido
> para preservar o `dateId` já gravado (ver [[stats-service]]). Residual aceito: no caso raro de
> `BetSettled` chegar antes do `BetCreated` correspondente (mensagens fora de ordem), não há
> `betDate` disponível no payload de `BetSettled` — cai em `settledAt` como estimativa até o
> `BetCreated` (que nunca sobrescreve uma liquidação já aplicada, ver [[stats-service]]) processar
> depois. Corrigir isso de verdade exigiria propagar `betDate` também no evento `BetSettled`
> (mudança de contrato cross-service) — não feito agora, fora do escopo de `epic-011`.

Fonte teórica: TCC1 cap. 2.4/2.5, citando Galekwa et al. (2025) — "dinâmica de portfólio
dependente do caminho e drawdown máximo... revelam a resiliência da banca diante de sequências de
variabilidade negativa". Requer a série ordenada (não um agregado), diferente de ROI/taxa de
acerto/odd média.

### Índice de Sharpe simplificado

Adaptação do Índice de Sharpe (Sharpe, 1994, TCC1 cap. 2.4/2.5) ao contexto de apostas: em vez de
retornos por período de tempo uniforme (ação/fundo), trata **cada aposta liquidada como uma
observação**, taxa livre de risco = 0 (não há ativo livre de risco equivalente no domínio de
apostas esportivas):

```
sharpeSimplificado = media(profit_i) / desvioPadrao(profit_i)     (apostas liquidadas do recorte)
```

Desvio-padrão amostral (`n-1`), não populacional — o recorte é sempre uma amostra das apostas do
usuário, não a população completa de resultados possíveis. **Limitação documentada
deliberadamente**: o Índice de Sharpe clássico usa retornos *percentuais* por período *uniforme*
(ex. mensal); aqui `profit` é valor absoluto por aposta e apostas não ocorrem em intervalos
regulares — este índice serve para comparar a consistência (retorno/risco) **entre combinações de
filtro dentro da própria plataforma**, não é comparável a um Sharpe de mercado financeiro
tradicional. Casos-limite: menos de 2 apostas liquidadas no recorte, ou desvio-padrão zero (todas
as apostas com o mesmo `profit`) → retorna `null` (indeterminado), nunca divisão por zero.

## Ver também

- [[stats-service]] — implementação (`FactBetRepository`, `CalculateMetricsService`,
  `GET /api/v1/statistics` e `GET /api/v1/statistics/search`).
- [[bets-service]] — `GET /api/v1/bankroll/balance` (saldo inicial/final) e
  `GET /api/v1/settings` (`unitPercent`), ambos consumidos pelo dashboard.
- [[web]] — apresentação em cards/gráficos (dashboard e tela "Buscar Estatísticas").
- [[REQUIREMENTS]] — RN04, RN06, RN08, RN09 (regras normativas de que estas fórmulas derivam).
