---
tags: [business, bankroll, finance]
---

# Bankroll e movimentações

## Composição do saldo

Para uma casa: `initialBalance + depósitos - retiradas + lucro líquido das apostas liquidadas`.

A banca consolidada é a soma dos saldos de todas as casas do tenant. Liquidação e leitura do saldo respeitam o tenant atual e a atualização é imediata.

## Movimentações

Depósitos e retiradas pertencem a uma casa, têm valor positivo e não podem apontar para casa inexistente. O modelo atual não bloqueia retirada que produza saldo negativo; isso é uma decisão explícita, não uma falha silenciosa.

## Consulta por período

`GET /api/v1/bankroll/balance?at=yyyy-MM-dd` retorna o saldo consolidado naquela data. O dashboard compara saldo inicial e final do período; métricas e fórmulas complementares estão em [[estatisticas]].

## Configuração de unidade

`unitPercent` é lido por todos os usuários para calcular unidades apostadas e alterado apenas por admin. A fórmula de unidades e os casos indeterminados estão em [[estatisticas]] e o uso na interface em [[jornadas-da-aplicacao-web]].

Fontes: [[bets-service]], [[contratos-de-api]], [[ciclo-de-vida-da-aposta]] e [[modelo-de-dados]].
