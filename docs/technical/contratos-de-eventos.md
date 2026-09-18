---
tags: [technical, events, rabbitmq]
---

# Contratos de eventos

## Fluxo

[[bets-service]] publica `BetCreated` no registro e `BetSettled` na liquidação. [[stats-service]] consome ambos de forma assíncrona. O registro HTTP não espera o processamento estatístico.

## Garantias

Os eventos têm `eventId`, `tenantId`, `userId` e `correlationId`. O consumidor registra eventos processados para impedir duplicação, aceita chegada fora de ordem e faz upsert da aposta liquidada. Falhas permanentes vão para DLQ; falhas transitórias podem ser reenviadas.

## Fontes

Schemas JSON: `contracts/`. Contrato completo e topologia: [[contratos-de-api]]. Regras de negócio: [[business/integracao-por-eventos]] e [[business/estatisticas-e-dashboards]]. Infraestrutura: [[infra]].
