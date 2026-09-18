---
tags: [technical, testing]
---

# Estratégia de testes

## Pirâmide

Testes unitários cobrem domínio e aplicação isoladamente. Testes de integração usam Testcontainers para Postgres, RabbitMQ e Redis quando aplicável. Testes E2E usam Playwright no [[web]].

## Casos críticos

Validar isolamento por tenant, regras de liquidação, idempotência de eventos, formato dos contratos, i18n de erros e filtros de dashboard. Fixtures de persistência devem provisionar o schema pelo mesmo caso de uso da produção.

## Gate

A meta é superior a 80% de cobertura. O comando e os critérios por stack estão em [[testes]]; a estratégia de negócio está em [[business/negocio]].
