---
tags: [business, statistics, dashboard]
---

# Estatísticas e dashboards

## Elegibilidade

Só `won`, `lost` e `void` entram nas métricas. `pending` pode aparecer em listagens, mas nunca altera ROI, lucro ou taxa de acerto. A atualização é eventual após os eventos chegarem a [[stats-service]].

## Métricas

O bundle de estatísticas entrega visão geral, agrupamentos por esporte, mercado, casa, liga, tipster e tipo de aposta, além da série mensal. Inclui total apostado, lucro líquido, ROI, taxa de acerto, contagens por resultado, PRÉ/LIVE e odd média.

- ROI: lucro líquido / total investido.
- Taxa de acerto: vitórias / apostas liquidadas; devolvidas permanecem no denominador do dashboard atual.
- ROI segmentado: calcula somente o agrupamento selecionado.
- Unidades apostadas: total apostado / (saldo atual * `unitPercent`). Se o divisor for zero, a UI mostra estado indeterminado.
- Relatório: quebra diária, ROI sobre banca, lucro médio, lucro em unidades, +EV e dias green/red.
- Visão geral: curva vitalícia contínua e resumo mensal, filtrado por ano no cliente.

Fórmulas e exceções: [[estatisticas]]. Regras: [[requisitos]] RN04, RN06, RN08 e RN09.

## Experiência

[[jornadas-da-aplicacao-web]] descreve as telas, presets e filtros. [[contratos-de-api]] descreve o bundle e sua granularidade de datas. [[integracao-por-eventos]] explica por que os números podem aparecer depois do registro.
