---
tags: [technical, operations, config]
---

# Operação e configuração

## Observabilidade

Logs estruturados carregam `X-Correlation-Id` e `X-Tenant-Id`. Serviços Java expõem liveness/readiness pelo Actuator; Telegram expõe `GET /health`.

## Ambientes

Cada serviço possui configuração por ambiente e `.env.example`; segredos reais nunca entram no repositório. Portas Java são fixas e URLs de downstream são configuráveis.

## Fontes

Detalhes de logs, health checks, portas, CORS, ambientes, PASETO e configuração do frontend: [[observabilidade-e-configuracao]]. Implantação: [[infra]]. Integrações: [[business/integracao-por-eventos]].
