---
tags: [technical, architecture]
---

# Limites da arquitetura

## Serviços

[[auth-service]] é dono de tenants, usuários, autenticação e vínculo Telegram. [[bets-service]] é dono dos catálogos, apostas, liquidação, bankroll e movimentações. [[stats-service]] é dono do modelo analítico, métricas e cache. [[api-gateway]] é a entrada HTTP pública e o ponto de confiança. [[telegram-integration]] é o adaptador de captura remota. [[web]] é a SPA.

## Isolamento

Cada serviço com banco possui seu próprio PostgreSQL. Dentro de auth, bets e stats, os dados são isolados por schema `tenant_<slug>`. Nenhum serviço acessa o banco de outro serviço; comunicação ocorre por HTTP contratado ou eventos.

## Onde aprofundar

Arquitetura completa e fluxos: [[arquitetura]]. Modelo persistido: [[modelo-de-dados]]. Decisões históricas: [[DECISIONS-LOG]]. Capacidades: [[business/negocio]].
