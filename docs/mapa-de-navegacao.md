---
tags: [moc, navigation]
---

# Navegação do vault

Use este mapa quando não souber onde procurar.

## Quero entender o produto

[[business/negocio]] → capacidade específica → nota do serviço responsável.

## Quero implementar uma mudança

[[requisitos]] → [[business/negocio]] → nota de serviço → [[contratos-de-api]] / [[modelo-de-dados]] / [[testes]].

## Quero entender uma decisão

[[DECISIONS-LOG]] → fonte normativa indicada no impacto da decisão.

## Quero operar ou validar o sistema

[[technical/referencia-tecnica]] → [[observabilidade-e-configuracao]] / [[pipeline-ci-cd]] / [[testes]] / [[infra]].

## Quero entender a interface

[[business/jornadas-da-aplicacao-web]] → [[sistema-de-design]] → [[web]].

## Organização das pastas

- `business/`: comportamento e regras do domínio, em linguagem de negócio.
- `services/`: peculiaridades de cada serviço e seus limites.
- raiz de `docs/`: fontes normativas cross-service.
- `technical/`: mapas de referência técnica.
- `diagrams/`, `design-references/` e `contracts/`: artefatos de suporte e origem.

Uma nota nova deve ter um assunto único, links para a fonte normativa e entrada em um MOC. Não crie uma segunda versão de uma regra já existente.
