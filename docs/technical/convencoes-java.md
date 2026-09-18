---
tags: [technical, java]
---

# Convenções Java

## Estrutura

Os serviços Java usam arquitetura hexagonal: domínio sem dependências de Spring/JPA; aplicação orquestra casos de uso; adapters traduzem HTTP, mensageria e persistência.

## Padrões

Injeção por construtor, DTOs como `record`, validação de entrada nos adapters, exceções de domínio traduzidas para RFC 7807 e migrations Flyway imutáveis após commit.

## Persistência

Multi-tenancy usa schema por tenant. Atualizações carregam a entidade existente; transições condicionais usam operação atômica. Detalhes de Hibernate, JPA e Sonar ficam na fonte completa.

Fonte normativa: [[convencoes]]. Testes: [[testes]]. Dados e negócio: [[modelo-de-dados]] e [[business/negocio]].
