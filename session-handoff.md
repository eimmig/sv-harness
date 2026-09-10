# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-10

## Objetivo atual

Os 9 epics originais do TCC 1 estão `done`. Usuário abriu uma segunda rodada de escopo novo
(`epic-011..021`, pedida nesta mesma sessão) sobre estatísticas de decisão pré-aposta, dashboard
consolidado e telas analíticas por cadastro. `epic-011` (busca de estatísticas por combinação,
`stats-service`) fechou primeiro; durante o planejamento de `epic-012` (tela "Buscar
Estatísticas" em `apps/web`) surgiu um addendum (`feat-013`, `DIM_TEAM` escopado por esporte) que
também fechou nesta sessão. Próximo epic elegível: `epic-012` (`apps/web`, depende só de
`epic-011`, já `done`).

## Concluído nesta sessão (2026-09-10)

- [x] **`epic-011` fechado** (`stats-service feat-012`, `GET /api/v1/statistics/search`) — motor
      de decisão pré-aposta, `DIM_TEAM`+`odd` novos em `FACT_BET`.
- [x] **Addendum `feat-013` fechado** (`stats-service`, sobre `epic-011`) — `DIM_TEAM` ganha
      `sportId` (chave natural composta `(name, sportId)`), `GET /api/v1/statistics/teams` novo.
      Achado real de Test Suite Auditor corrigido (constraint UNIQUE sem teste DB-level) e achado
      de gate corrigido (Reliability finding do SonarCloud em código de `feat-012`, capturado pela
      janela de "New Code" por tempo do projeto, não por diff do PR) antes de fechar. Ver entrada
      datada em `services/stats-service/progress.md` para o detalhe completo.
- [x] `epic-012..021` planejados e registrados em `feature_list.json` (raiz), todos
      `not-started`, dependências mapeadas.

## Bloqueios / Riscos

Nenhum.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Epic elegível: `epic-012` (`apps/web` — tela "Buscar Estatísticas", consome `stats-service
   feat-012`+`feat-013`, ambos `done`). `epic-013` (`bets-service`) também elegível em paralelo
   (WIP por harness, serviços diferentes).
3. Projeto SonarCloud de `sv-stats-backend` usa janela de "New Code" por tempo (não por diff de
   PR) — um PR sem nenhuma linha tocada num arquivo ainda pode falhar o gate por código de
   horas/dias atrás entrando na janela (aconteceu nesta sessão, `feat-013`). Não investigado se é
   intencional; sinalizado em `services/stats-service/session-handoff.md`.
