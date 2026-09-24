# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-24

## Objetivo atual

Nenhum trabalho em andamento — `epic-001`..`epic-035` todos `done`, e nenhum harness tem feature
`not-started`. Próximo passo depende de pedido novo do usuário.

**Lição de processo** (continua valendo): escrever `status:done` + `evidence` da feature **e** o
`progress.md`/`session-handoff.md` do serviço NA branch da story, dentro do PR da última subtask,
ANTES do PR `story->develop`. Antes de abrir o PR da story, conferir as regras do SonarCloud já
conhecidas em `docs/testes.md` "CI e SonarCloud" — o Sonar só roda nesse gate.

## Concluído nesta sessão (2026-09-24)

- [x] **`epic-034` fechado** — `stats-service feat-023` e `api-gateway feat-018`.
- [x] **Backlog ad-hoc do web**: `feat-044` (overlay de carregamento), `feat-041` (lucro por dia),
      `feat-040` (título/legenda/ajuda nos gráficos).
- [x] **`epic-035` criado e fechado** — filtro PRE/LIVE na busca (`stats-service feat-024` +
      `web feat-038`), `/bet-type-dashboard` removida.
- Detalhe em `progress.md`.

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
2. Sem backlog pendente. Pendência observada e fora de escopo: rótulos de eixo dos gráficos usam
   `--color-border` e ficam com pouco contraste (`docs/sistema-de-design.md` item 6).
