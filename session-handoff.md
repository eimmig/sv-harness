# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-22

## Objetivo atual

**Todos os 31 epics do `feature_list.json` da raiz estão `done`** (`epic-031` fechado nesta
sessão). Nenhum harness tem feature `not-started` conhecida no momento (conferir cada
`feature_list.json` antes de assumir, ver "Próxima sessão" abaixo).

## Concluído nesta sessão (2026-09-22)

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
- **Sobra não commitada do rename do vault** (`docs: reorganize vault with Portuguese
  navigation`, commit `f39582a`, sessão anterior a esta): `docs/API-CONTRACTS.md`,
  `ARCHITECTURE.md`, `CONVENTIONS.md`, `DATA-MODEL.md`, `Index.md`, `REQUIREMENTS.md`,
  `STATISTICS.md` existem como cópias em **inglês, não rastreadas** (`git status` mostra `??`),
  idênticas às versões em português já commitadas (`contratos-de-api.md` etc.) exceto por
  wikilinks internos (`[[ARCHITECTURE]]` vs `[[arquitetura]]`). Não foram tocadas nesta sessão
  (fora de escopo do trabalho pedido) — próxima sessão que mexer em docs deve perguntar ao
  usuário se apaga essas 7 cópias órfãs ou se há algum motivo pra mantê-las.

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
