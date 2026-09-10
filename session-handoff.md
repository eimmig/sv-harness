# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-10

## Objetivo atual

**Todos os 9 epics do backlog raiz estão `done`** (`epic-001..010`, exceto `epic-010` que fechou
nesta sessão junto com `epic-007`). Não há epic `not-started` elegível — o backlog original do
TCC 1, mapeado desde o início do projeto, está completo.

## Concluído nesta sessão (2026-09-10)

- [x] **`epic-007` fechado** (resiliência DLQ/retry) — ver entrada datada em `progress.md` para
      o detalhe completo (cenário DLQ testado contra a stack real, 2 achados reais corrigidos em
      outros serviços, achado de processo de PR/CI corrigido retroativamente).
- [x] **`epic-010` fechado** (migração para Kubernetes) — manifests YAML puros em `infra/k8s/`,
      validados de ponta a ponta contra um cluster `kind` local (tenant/login/aposta via Ingress
      real, evento consumido dentro do cluster). Dockerfile de cada um dos 5 serviços de
      aplicação (4 Java + `telegram-integration`, que entrou no escopo por decisão do usuário)
      feito como feature própria em cada repositório de serviço. Ver entrada datada em
      `progress.md` para o detalhe completo (decisões de escopo via `AskUserQuestion`, achado do
      SonarCloud investigado e marcado Won't Fix em `telegram-integration`).
- [x] **Limpeza de branches** em todos os 6 repositórios de serviço tocados — dezenas de
      branches antigas já mescladas, não só as desta sessão.

## Bloqueios / Riscos

Nenhum.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Nenhum epic `not-started` resta.** Antes de inventar trabalho novo, perguntar ao usuário o
   que vem a seguir — o backlog original do TCC 1 está completo. Candidatos conhecidos, nenhum
   deles bloqueando nada: `apps/web feat-009`/`feat-010` (RF12/RF13, `not-started` naquele
   harness, gap aceito ao fechar `epic-006`); qualquer refinamento/hardening adicional que o
   usuário queira sobre o que já está `done`.
3. Cluster `kind` (`stakevault`) pode continuar no ar de sessões anteriores — checar com
   `kubectl get pods` antes de assumir que precisa recriar.
