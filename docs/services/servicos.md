---
tags: [moc, services]
---

# Serviços

Índice das responsabilidades técnicas. Para entender o comportamento do produto, comece em [[business/negocio]].

| Serviço | Papel | Entrada de negócio |
|---|---|---|
| [[auth-service]] | Tenants, usuários, login e vínculo Telegram | [[business/tenant-e-usuarios]], [[business/autenticacao-e-acesso]] |
| [[api-gateway]] | Entrada HTTP, autenticação e roteamento | [[business/autenticacao-e-acesso]], [[business/captura-via-telegram]] |
| [[bets-service]] | Catálogos, apostas, liquidação, saldo e movimentações | [[business/catalogos-de-apostas]], [[business/ciclo-de-vida-da-aposta]], [[business/bankroll-e-movimentacoes]] |
| [[stats-service]] | Consumo de eventos, métricas e cache | [[business/estatisticas-e-dashboards]], [[business/integracao-por-eventos]] |
| [[telegram-integration]] | Captura remota e parsing | [[business/captura-via-telegram]] |
| [[web]] | Jornadas e telas da SPA | [[business/jornadas-da-aplicacao-web]] |
| [[infra]] | Execução local, mensageria, bancos e Kubernetes | [[business/integracao-por-eventos]] |

Cada nota de serviço responde a: responsabilidade, limites, dados próprios, interfaces e peculiaridades da implementação. Regras de negócio continuam nas notas em `business/`; contratos compartilhados em [[contratos-de-api]].
