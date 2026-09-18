---
tags: [technical, ci-cd]
---

# Pipeline de CI/CD

## Organização

Cada serviço e `infra/` possui seu próprio workflow. A raiz contém somente o harness e o vault; não há pipeline agregada de aplicação.

## Gates

Nos serviços de aplicação, a pipeline valida changelog, i18n, build, testes, cobertura e SonarCloud. `infra/` valida changelog e configuração do Compose.

## Fontes

Procedimento completo: [[pipeline-ci-cd]]. Testes: [[technical/estrategia-de-testes]] e [[testes]]. Topologia: [[technical/limites-da-arquitetura]] e [[infra]].
