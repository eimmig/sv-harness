# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-24

## Objetivo atual

Nenhum epic em andamento — `epic-001`..`epic-034` todos `done`. O que resta está só no backlog
ad-hoc de `apps/web` (`feat-038`/`040`/`041`/`044`), sem epic próprio.

**Lição de processo** (sessões `auth-service feat-021` e desta): escrever `status:done` +
`evidence` da feature **e** o `progress.md`/`session-handoff.md` do serviço NA branch da story,
dentro do PR da última subtask, ANTES do PR `story->develop`. Depois do merge, qualquer PR só de
harness/docs reprova o gate de `CHANGELOG.md` e força push direto em `develop`.

## Concluído nesta sessão (2026-09-24)

- [x] **`epic-034` fechado** — `stats-service feat-023` (SV-588) e `api-gateway feat-018` (SV-591),
      CI+SonarCloud verdes. Detalhe em `progress.md`. `docs/convencoes.md` corrigido (interface
      do gateway é `LocalizedFilterException`).

## Bloqueios / Riscos

Nenhum bloqueio novo. Risco já conhecido, **não mais um bloqueio pra promoção de `main`**: o job
`deploy` (`epic-028`) segue falhando nos 6 repositórios de aplicação porque o `KUBE_CONFIG` não
alcança o cluster a partir de runners hospedados do GitHub Actions — usuário decidiu nesta sessão
aceitar esse ruído (falha isolada, não bloqueia `release`/demais jobs) em vez de continuar
pausando promoções `develop -> main` por causa disso. Continua sem solução de rede definida (ver
`services/bets-service/session-handoff.md` e `docs/services/infra.md`).

`e2e/search-statistics.spec.ts` (apps/web) segue quebrado desde `feat-036` (não relacionado a
`epic-032`/`epic-033`/`epic-034`) — não resolvido nesta sessão.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `apps/web feat-038`/`040`/`041`/`044` — `038`/`040`/`041` nasceram como "registrar, não
   implementar agora"; `044` tem 4 decisões de UX em aberto na `description`. Confirmar com o
   usuário antes de implementar (ver `apps/web/session-handoff.md`).
