# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-10

## Objetivo atual

Os 9 epics originais do TCC 1 estão `done`. Segunda rodada de escopo novo (`epic-011..021`,
pedida nesta mesma sessão) sobre estatísticas de decisão pré-aposta, dashboard consolidado e
telas analíticas por cadastro. `epic-011` (`stats-service`) e `epic-012` (`apps/web`, tela
"Buscar Estatísticas") fecharam nesta sessão. Próximos epics elegíveis: `epic-013`
(`bets-service`, saldo consolidado/betType/unidade), `epic-016`/`epic-018` (`stats-service`,
quebra diária/segmentos novos) — todos dependem só de epics já `done`, podem avançar em paralelo
(harnesses diferentes).

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
      `shared/kpi-card.ts#kpiSign`, reaproveitáveis por telas futuras (`epic-015`/`epic-017`/
      `epic-019`/`epic-020`/`epic-021`, que também terão gráficos/cards). Ver
      `apps/web/progress.md` para o detalhe completo, incluindo um achado real de teste (mock de
      e2e com envelope de resposta errado, documentado em `docs/TESTING.md`).
- [x] `epic-012..021` planejados e registrados em `feature_list.json` (raiz), dependências
      mapeadas.

## Bloqueios / Riscos

Nenhum.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Epics elegíveis, todos podendo avançar em paralelo (harnesses diferentes): `epic-013`
   (`bets-service`), `epic-016`/`epic-018` (`stats-service`). `epic-015`/`epic-017`/`epic-019`/
   `epic-020`/`epic-021` (`apps/web`) dependem desses três, ainda não elegíveis.
3. Projeto SonarCloud de `sv-stats-backend` usa janela de "New Code" por tempo (não por diff de
   PR) — sinalizado em `services/stats-service/session-handoff.md`, não investigado se é
   intencional.
4. Padrão reaproveitável desta sessão: extrair lógica de gráfico/sinal de cor compartilhada
   *antes* de duplicar entre telas — o gate do SonarCloud de `sv-frontend`
   (`new_duplicated_lines_density ≤ 3%`) vai pegar duplicação real entre componentes parecidos
   (ex.: dois gráficos ngx-echarts quase idênticos) mesmo que cada arquivo pareça pequeno
   isoladamente.
