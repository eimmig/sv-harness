---
tags: [technical, frontend, angular]
---

# Diretrizes do frontend

## Arquitetura

[[web]] é uma SPA Angular standalone. O comportamento de negócio das telas está em [[business/jornadas-da-aplicacao-web]]; a identidade visual está em [[sistema-de-design]].

## Regras de implementação

Usar Signals, Reactive Forms, Angular Material e i18n em `pt-BR`, `en-US` e `es`. A URL do gateway é configurada no build. Filtros devem consultar a API novamente e não simular filtragem client-side.

## Responsividade e acesso

As telas devem funcionar em desktop, tablet e mobile. O formulário de apostas segue os oito princípios de Shneiderman. Locators E2E devem usar `data-testid` ou roles estáveis, nunca texto traduzido.

Fonte completa: [[convencoes]], [[sistema-de-design]] e [[testes]].
