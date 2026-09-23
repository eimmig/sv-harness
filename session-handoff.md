# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-23

## Objetivo atual

32 dos 33 epics `done`. `epic-032` (reformulação de marca StakeVault -> Arka) `in-progress`,
multi-harness — ordem sugerida: vault raiz (done) -> `apps/web feat-042` (done) ->
`telegram-integration feat-011` (done) -> 4 serviços Java (`auth-service`/`bets-service`/
`stats-service`/`api-gateway`, ainda não auditados) -> `infra/` (ainda não auditado). `epic-033`
(novo, `not-started`) — CI: gerar versão automática ao merge para master, nos 7 repositórios;
escopo ainda por decidir por harness (mecanismo de versionamento difere por stack: Maven/npm/
pyproject/tag solta em `infra/`), nenhuma feature granular aberta ainda.

## Concluído nesta sessão (2026-09-23)

- [x] `telegram-integration feat-011` fechada — 3º harness de `epic-032`. Escopo bem mais estreito
      que `apps/web` (só `n8n/telegram-bot.json` + `n8n/README.md`, 4 arquivos batidos no total
      pelo grep, 2 deles corretamente fora de escopo). Aplicado o gotcha aprendido em
      `apps/web feat-042` (wordmark partido em substring): `grep -rniE "stake|vault"` além do
      `grep -i stakevault` simples — nenhum achado novo, escopo mecânico. Plan Reviewer (READY) +
      Delivery Reviewer (PASS) passe próprio. Story SV-545, PRs #42-45, CI+SonarCloud verdes.
      `./init.sh` do serviço e da raiz verdes. Detalhe completo em
      `services/telegram-integration/progress.md`.
- [x] `epic-033` adicionado ao backlog da raiz (pedido do usuário) — `not-started`, sem feature
      granular ainda em nenhum harness.

## Bloqueios / Riscos

Nenhum bloqueio novo. Ver `services/telegram-integration/session-handoff.md` — nada pendente
lá (backlog daquele serviço esgotado de novo).

`e2e/search-statistics.spec.ts` (apps/web) segue quebrado desde `feat-036` (não relacionado a
`epic-032`/`epic-033`) — ver `apps/web/session-handoff.md`/`progress.md` pro detalhe, não
resolvido nesta sessão.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`epic-032` in-progress** — próximo harness na ordem sugerida: auditar
   `services/auth-service/`, `services/bets-service/`, `services/stats-service/`,
   `services/api-gateway/` (grep `-ril "stakevault"` case-insensitive **e** `grep -rniE
   "stake|vault"` pra descartar substring partida, mesmo cuidado usado em `telegram-integration`)
   antes de abrir feature granular em cada um; por último `infra/`.
3. **`epic-033` not-started** — se o usuário pedir pra avançar, plan review por harness primeiro
   (mecanismo de versionamento não está decidido, ver `description` do epic na raiz).
4. `develop` de `sv-frontend` segue à frente de `main` desde `epic-031` (decisão de promoção fica
   com o usuário, não assumir).
