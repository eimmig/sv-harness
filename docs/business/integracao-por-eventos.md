---
tags: [business, integration, events]
---

# Integração por eventos

## Contrato

[[bets-service]] publica `BetCreated` ao registrar e `BetSettled` ao liquidar. [[stats-service]] consome ambos pela fila RabbitMQ. Os payloads repetem dimensões no evento de liquidação para suportar chegada fora de ordem.

## Garantias

- Registro da aposta não espera o processamento estatístico.
- `eventId` é controlado em `PROCESSED_EVENT`; redelivery não duplica fatos.
- `BetSettled` faz upsert e pode chegar antes de `BetCreated`.
- Validação de schema e tenant inválido são falhas permanentes e vão para DLQ.
- Retry cobre falhas transitórias; DLQ isola falhas que não devem travar a fila.
- `BetSettled` invalida o cache de métricas; `BetCreated` não invalida porque `pending` é inelegível.

## Navegação técnica

Payloads e topologia: [[contratos-de-api]]. Persistência analítica: [[modelo-de-dados]]. Infraestrutura e operação: [[infra]] e [[observabilidade-e-configuracao]]. Regras de consistência: [[estatisticas-e-dashboards]].
