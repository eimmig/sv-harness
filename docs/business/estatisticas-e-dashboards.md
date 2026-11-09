---
tags: [business, statistics, dashboard]
---

# Estatísticas e dashboards

## Elegibilidade

Só `won`, `lost` e `void` entram nas métricas. `pending` pode aparecer em listagens, mas nunca altera ROI, lucro ou taxa de acerto. A atualização é eventual após os eventos chegarem a [[stats-service]].

## Métricas

O bundle de estatísticas entrega visão geral, agrupamentos por esporte, mercado, casa, liga, tipster e tipo de aposta, além da série mensal. Inclui total apostado, lucro líquido, ROI, taxa de acerto, contagens por resultado, PRÉ/LIVE e odd média.

- ROI: lucro líquido / total investido.
- Taxa de acerto: vitórias / (vitórias + derrotas); devolvidas ficam fora do denominador desde `stats-service feat-032`.
- ROI segmentado: calcula somente o agrupamento selecionado.
- Unidades apostadas: total apostado / (saldo inicial do período * `unitPercent`), desde `web feat-072`. Se o divisor for zero, a UI mostra estado indeterminado.
- Vantagem sobre a probabilidade implícita: taxa de acerto menos a média de 1/odd das ganhas e perdidas (`epic-053`, substitui o antigo +EV).
- Intervalos de 95% da taxa de acerto (Wilson) e do ROI (método delta), com aviso no dashboard quando o resultado ainda não se distingue do acaso.
- Relatório: quebra diária, ROI sobre banca, lucro médio, lucro em unidades, vantagem e dias green/red.
- Visão geral: curva vitalícia contínua e resumo mensal, filtrado por ano no cliente.

Fórmulas e exceções: [[estatisticas]]. Regras: [[requisitos]] RN04, RN06, RN08 e RN09.

## Experiência

[[jornadas-da-aplicacao-web]] descreve as telas, presets e filtros. [[contratos-de-api]] descreve o bundle e sua granularidade de datas. [[integracao-por-eventos]] explica por que os números podem aparecer depois do registro.
