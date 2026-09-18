---
tags: [technical, api]
---

# API REST

## Padrão

As rotas usam `/api/v1`, substantivos plurais em inglês, paginação `page`/`size` e erros `application/problem+json`. Query params e valores técnicos também são em inglês; mensagens são localizadas.

## Identidade

Chamadas autenticadas carregam `X-User-Id` e `X-Tenant-Id`, injetados pelo [[api-gateway]]. Operações administrativas usam `X-Admin-Api-Key`; a integração Telegram usa a credencial de serviço definida no contrato.

## Capacidades

Apostas e catálogos: [[business/catalogos-de-apostas]] e [[business/ciclo-de-vida-da-aposta]]. Saldo: [[business/bankroll-e-movimentacoes]]. Login e acesso: [[business/autenticacao-e-acesso]].

## Fonte completa

Payloads, filtros, erros, CORS e regras de confiança estão em [[contratos-de-api]].
