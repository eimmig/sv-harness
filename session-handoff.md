# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-10

## Objetivo atual

Os 9 epics originais do TCC 1 estão `done`. Segunda rodada de escopo novo (`epic-011..021`,
pedida nesta mesma sessão) sobre estatísticas de decisão pré-aposta, dashboard consolidado e
telas analíticas por cadastro. `epic-011`/`epic-012`/`epic-013` fecharam nesta sessão. Próximos
epics elegíveis: `epic-014` (`stats-service`, `byBetType`, depende de `epic-004`+`epic-013`,
ambos `done`), `epic-016`/`epic-018` (`stats-service`) — todos podem avançar em paralelo
(harnesses diferentes, respeitando WIP máximo 1 por serviço). `epic-015`/`epic-017`/`epic-019`/
`epic-020`/`epic-021` (`apps/web`) ainda dependem de epics não fechados.

## Concluído nesta sessão (2026-09-10)

- [x] **`epic-011` fechado** (`stats-service feat-012`, `GET /api/v1/statistics/search`) — motor
      de decisão pré-aposta, `DIM_TEAM`+`odd` novos em `FACT_BET`.
- [x] **Addendum `feat-013` fechado** (`stats-service`, sobre `epic-011`) — `DIM_TEAM` ganha
      `sportId` (chave natural composta `(name, sportId)`), `GET /api/v1/statistics/teams` novo.
      Ver `services/stats-service/progress.md`.
- [x] **`epic-012` fechado** (`apps/web feat-012`, tela "Buscar Estatísticas") — 7 subtasks,
      consome os dois endpoints de `stats-service` acima. Dois achados reais de gate corrigidos
      na raiz do problema (não contornados): a11y de inputs de data sem `id`, e duplicação de
      código real entre os dois gráficos ngx-echarts do app e entre as duas telas com cards de
      KPI — resolvido extraindo `core/chart-theme.ts#buildLineChartOption` e
      `shared/kpi-card.ts#kpiSign`, reaproveitáveis por telas futuras. Ver `apps/web/progress.md`
      para o detalhe completo, incluindo um achado real de teste (mock de e2e com envelope de
      resposta errado, documentado em `docs/TESTING.md`).
- [x] **`epic-013` fechado** (`bets-service feat-014`, 4 subtasks, story SV-317) — `GET`/
      `PATCH /api/v1/settings` (admin-only via `X-User-Role`), `BET.betType` enum `PRE`/`LIVE`,
      `GET /api/v1/bankroll/balance?at=` (corte de fuso `America/Sao_Paulo`, não UTC ingênuo).
      Decisão via `AskUserQuestion` ao usuário (única pergunta genuína desta sessão): claim
      `role` no PASETO + header `X-User-Role` injetado pelo `api-gateway`, já que este serviço
      não tem tabela `USER`. Achado cross-service real corrigido antes de qualquer consumidor
      depender do valor errado: `auth-service` emitia a claim em uppercase, corrigido em
      `auth-service feat-013`. `Delivery Reviewer`+`Test Suite Auditor`+`Persistence Auditor`
      rodados em paralelo contra o diff inteiro — achados reais corrigidos (transaction boundary
      em `BankrollService`, índices faltando, testes de isolamento/HTTP faltando). Ver
      `services/bets-service/progress.md` para o detalhe completo.
- [x] `epic-012..021` planejados e registrados em `feature_list.json` (raiz), dependências
      mapeadas.

## Bloqueios / Riscos

Nenhum bloqueio no trabalho fechado. **Atenção**: `services/bets-service` tem um `git stash`
pendente (`feat-015`, build/push de imagem Docker pro GHCR — `plan_review` já escrito, nunca
commitado, encontrado como estado órfão ao retomar esta sessão). Não é escopo desta sessão, não
foi descartado — só posto de lado pra não violar WIP máximo 1 enquanto `feat-014` estava
`in-progress`. Próxima sessão em `bets-service`: `git stash list` primeiro, decidir se retoma
esse plano ou substitui.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Epics elegíveis: `epic-014` (`stats-service`), `epic-016`/`epic-018` (`stats-service`, mas
   respeitar WIP máximo 1 — só um `in-progress` por harness). `epic-015`/`epic-017`/`epic-019`/
   `epic-020`/`epic-021` (`apps/web`) ainda não elegíveis (dependem de epics acima).
3. Em `services/bets-service`, checar `git stash list` antes de iniciar qualquer feature nova —
   ver "Bloqueios / Riscos" acima.
4. Projeto SonarCloud de `sv-stats-backend` usa janela de "New Code" por tempo (não por diff de
   PR) — sinalizado em `services/stats-service/session-handoff.md`, não investigado se é
   intencional.
5. Padrão reaproveitável desta sessão: extrair lógica de gráfico/sinal de cor compartilhada
   *antes* de duplicar entre telas — o gate do SonarCloud de `sv-frontend`
   (`new_duplicated_lines_density ≤ 3%`) vai pegar duplicação real entre componentes parecidos
   mesmo que cada arquivo pareça pequeno isoladamente.
6. Outro padrão reaproveitável: quando uma feature precisa de autorização por role num serviço
   sem tabela `USER`, o modelo é claim no PASETO + header injetado pelo `api-gateway`
   (`X-User-Role`, lowercase `admin`/`member`) — não reinventar por serviço, ver
   `docs/DECISIONS-LOG.md` "Claim role no PASETO".
