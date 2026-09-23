# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-22

## Objetivo atual

**Todos os 31 epics do `feature_list.json` da raiz estão `done`**. Nenhum harness tem feature
`not-started` conhecida no momento (conferir cada `feature_list.json` antes de assumir, ver
"Próxima sessão" abaixo). `bets-service feat-019` (`PUT /api/v1/bets/{id}`, ad-hoc, sem epic
próprio) e seu companion `stats-service feat-020` fechados mais tarde no mesmo dia — ver
`services/bets-service/progress.md`. `apps/web feat-039` (drawdown mensal + filtro de mês, ad-hoc)
também fechada no mesmo dia — ver `apps/web/progress.md`.

## Concluído nesta sessão (2026-09-22)

- [x] `bets-service feat-019` — `PUT /api/v1/bets/{id}`, edição de aposta pendente ou já
      liquidada sem excluir/recriar. Plan Reviewer (`REVISE`, 2 BLOCKER corrigidos: gotcha
      `Persistable`/`isNew` do JPA já documentado em `docs/convencoes.md` fazia `.save()` tentar
      `INSERT` numa linha já existente; corrida real entre `PUT` e `PATCH /status` concorrentes
      podia gravar `profit` inconsistente com stake/odd, corrigido com `UPDATE` atômico
      condicional). Companion cross-service `stats-service feat-020` (`processCreated` aceita
      reprocessar `FACT_BET` ainda `pending`). Ambos os `./init.sh` verdes. Sem story/branch/PR
      formal (fluxo direto de pareamento).

- [x] `apps/web feat-039` — drawdown mensal "só subia e saturava": 2 causas reais (padding de
      dias futuros no mês corrente + smoothing/grid grosseiro do `chart-theme.ts`), validadas
      rodando a stack real localmente contra o tenant de demonstração `demo-b583c3`. Filtro de
      mês trocado de `<input type="month">` nativo para `MatDatepicker` mês/ano. `./init.sh`
      verde (291 testes) + e2e completo (84/84). Sem story/branch/PR formal.

- [x] `epic-031` fechado — `apps/web feat-037`, tela "Comparativo de períodos"
      (`/period-comparison`). Pedido do usuário, zero backend novo (client-side). 7 subtasks,
      cada uma com PR próprio e CI verde (SV-529..536, PRs #157-164 em `sv-frontend`), `develop`
      atualizada, `main` **não** tocado — promoção fica a critério do usuário. Detalhe completo
      em `progress.md` (raiz) e `apps/web/progress.md`.
- [x] 2 achados reais corrigidos no caminho, fora do escopo de `feat-037` mas bloqueando o
      próprio fluxo de PRs dessa feature:
      - Flake de CI intermitente (`period-report.spec.ts`/`register-bet.spec.ts`, vazamento de
        `navigator.language`/`localStorage` entre specs no mesmo worker do Vitest) — achado já
        previsto em `docs/testes.md` (`feat-029.3`), confirmado na prática e corrigido.
      - 4 apontamentos reais do SonarCloud (2x função com mais de 7 parâmetros, 1x complexidade
        cognitiva 23>15, 1x asserção genérica) — só aparecem no gate `story→develop`, não nos PRs
        de subtask (SonarCloud não roda lá por desenho).
- [x] Achado real de QA visual corrigido: linhas de comparação de `feat-037` sem rótulo abaixo de
      600px — mecanismo reaproveitável (`data-mobile-label`/`::before`) documentado em
      `docs/sistema-de-design.md`.

## Bloqueios / Riscos

- **`e2e/search-statistics.spec.ts` (apps/web) quebrado desde `feat-036`** (2026-09-17, não
  `feat-037`): aquela feature substituiu o componente `language-selector` standalone pelo menu de
  configurações do side-nav em páginas autenticadas, sem atualizar esse spec — ainda procura
  `getByTestId('language-selector')`, que só existe na tela de login agora. Não bloqueia CI
  (Playwright não roda no pipeline do GitHub, só localmente via `npx playwright test`), mas
  qualquer sessão que rode a suíte e2e completa vai ver essa falha isolada. Fix provável: apontar
  o teste pro fluxo real (`nav-settings-language-*`), não reintroduzir o componente antigo. Ver
  `apps/web/progress.md` pro detalhe.

**Resolvido nesta sessão**: as 7 cópias órfãs em inglês do rename do vault (`docs/API-CONTRACTS.md`,
`ARCHITECTURE.md`, `CONVENTIONS.md`, `DATA-MODEL.md`, `Index.md`, `REQUIREMENTS.md`,
`STATISTICS.md`, nunca rastreadas, idênticas às versões em português já commitadas) foram apagadas
a pedido do usuário — não é mais um risco a monitorar. Também revertido nesta sessão:
`infra/.env.example` tinha lixo colado por engano (JSON com senha temporária real vazada,
`git checkout -- .env.example` resolveu, nada commitado).

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Nenhum epic `not-started` na raiz** — antes de assumir que não há trabalho, conferir cada
   harness (`services/*/feature_list.json`, `apps/web/feature_list.json`,
   `infra/feature_list.json`) por `"status": "not-started"`, já que features ad-hoc sem epic
   próprio (mesmo precedente de `feat-032`/`033`/`034`/`036`) podem surgir a qualquer momento a
   partir de achados do usuário em uso real.
3. `develop` de `sv-frontend` está à frente de `main` (feat-037 mesclada, main não). Se o usuário
   pedir uma promoção/release, é decisão dele — não promover `develop→main` por conta própria.
4. Ver "Bloqueios / Riscos" acima antes de tocar em `apps/web` e2e ou em qualquer arquivo
   `docs/*.md` de nome em inglês.
