# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-25

## Objetivo atual

Nenhum trabalho em andamento — `epic-001`..`epic-037` todos `done`, e nenhum harness tem feature
`not-started`. Próximo passo depende de pedido novo do usuário.

**Lição de processo** (continua valendo): escrever `status:done` + `evidence` da feature **e** o
`progress.md`/`session-handoff.md` do serviço NA branch da story, dentro do PR da última subtask,
ANTES do PR `story->develop`. Antes de abrir o PR da story, conferir as regras do SonarCloud já
conhecidas em `docs/testes.md` "CI e SonarCloud" — o Sonar só roda nesse gate.

## Concluído nesta sessão (2026-09-25)

- [x] **`epic-037` criado e fechado** — `apps/web feat-058`: escala Y compartilhada entre os
      mini-gráficos do drawdown mensal + grid passa a reaproveitar o filtro geral do dashboard em
      vez do datepicker próprio. Story SV-654, PRs #235-#238. Detalhe em `progress.md`.

## Bloqueios / Riscos

Nenhum bloqueio novo. Risco já conhecido, **não mais um bloqueio pra promoção de `main`**: o job
`deploy` (`epic-028`) segue falhando nos 6 repositórios de aplicação porque o `KUBE_CONFIG` não
alcança o cluster a partir de runners hospedados do GitHub Actions — usuário decidiu aceitar esse
ruído (falha isolada, não bloqueia `release`/demais jobs) em vez de continuar pausando promoções
`develop -> main` por causa disso. Continua sem solução de rede definida (ver
`services/bets-service/session-handoff.md` e `docs/services/infra.md`).

`e2e/search-statistics.spec.ts` (apps/web), anotado como quebrado desde `feat-036` em handoffs
anteriores: rodou verde (suíte completa, 101/101) nesta sessão, sem investigação adicional — não
era o foco desta sessão, então não foi confirmado se o problema original foi corrigido em algum
commit anterior ou se é intermitente. Próxima sessão que mexer em `apps/web`: rodar a suíte
completa de novo antes de reabrir esse item como bloqueio.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Sem backlog pendente em nenhum harness.
