# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-09

## Objetivo atual

- `epic-001`/`epic-002`/`epic-003`/`epic-004`/`epic-005`/`epic-008`/`epic-009` — todos `done`.
- `epic-006` (`apps/web`) **em andamento** — `feat-001`/`feat-002`/`feat-003`/`feat-004`/
  `feat-005`/`feat-007`/`feat-008` entregues e mergeados em `develop`. Resta só `feat-006`
  (RF10/RF11 UI, dashboards) pra fechar o epic inteiro. `feat-009` (RF12, status da aposta) e
  `feat-010` (RF13, movimentações financeiras) registradas no backlog daquele mesmo app,
  `not-started` — gap real encontrado planejando `feat-005`, decisão do usuário: ficam pra depois
  de `feat-006`, não bloqueiam o epic.
- `epic-007` (resiliência DLQ) segue elegível (dependências `epic-004`+`epic-005` satisfeitas)
  mas não iniciado — nenhuma sessão trabalhou nele ainda.

## Concluído nesta sessão (2026-09-09)

- [x] **`auth-service feat-010` fechada** (repositório `sv-auth-backend`, reaberto — `epic-002`
      já era `done`): gap real encontrado planejando `apps/web feat-002` — o token PASETO v4.local
      é criptografado simetricamente, o frontend não tinha como saber `userId`/`role` do usuário
      logado. `POST /api/v1/auth/login` passou a devolver esses 2 campos além de
      `token`/`mustChangePassword`. PR #47 (subtask->story) + PR #48 (story->develop), CI/Sonar
      verdes.
- [x] **`apps/web feat-002` fechada** (RF01/RF02 UI — autenticação e gestão de usuários do
      tenant): `AuthService`(Signals, sessão em `localStorage`)+interceptor de `Authorization`,
      login real, `authGuard`/`adminGuard`, nav mínima do app shell, banner não-bloqueante de
      `mustChangePassword`, tela de gestão de usuários do tenant (lista+criar, admin-only). 4
      subtasks, PRs #13-#17, CI/Sonar verdes (1 retrofit de achados reais do SonarCloud no PR
      final — `Web:InputWithoutLabelCheck`, `S6819`, `S7059`).
- [x] **`apps/web feat-003` fechada** (RF03 UI — casas de apostas): `BettingHousesApi`+tela real
      (lista+criar), `PagedResponse<T>` genérico. 3 subtasks, PRs #18-#21, CI/Sonar verdes.
- [x] **Achado real levantado pelo usuário durante `feat-003`, não pelo Plan Reviewer**:
      `docs/CONVENTIONS.md` já normatizava "nomes de rota, evento e código, todos já em inglês",
      mas `apps/web` tinha 3 páginas em português desde `feat-001` (`historico`,
      `registro-de-aposta`, `usuarios`) sem nenhuma sessão anterior ter cruzado a convenção contra
      o nome real dos arquivos. Usuário decidiu renomear tudo agora (não deixar a dívida crescer)
      — `history`/`register-bet`/`users`/`betting-houses` (a última nasceu direto em inglês, sem
      passar pelo nome antigo). Ver `apps/web/progress.md` (`feat-003.1`) pro detalhe completo.
- [x] **Achado real do gate de SonarCloud no PR `feature->develop`** de `feat-003` (não pego em
      nenhum PR de subtask, que não roda SonarCloud): `BettingHouses`/`Users` duplicavam ~16 linhas
      cada (padrão `reload()`/`submit()` com tratamento de erro RFC 7807), estourando o gate de 3%
      de duplicação nova. Corrigido extraindo `core/api-request.ts`
      (`loadInto`/`submitForm`, genérico) e reaproveitado também em `Login` — elimina a duplicação
      na raiz, não só nos 2 arquivos que o Sonar apontou.
- [x] **`apps/web feat-008` fechada** (catálogos base — esportes/ligas/mercados/tipsters): gap
      real encontrado planejando `feat-004` (formulário de aposta precisa dos dropdowns, bot
      Telegram já orienta "cadastrar em `apps/web`" quando o catálogo está vazio, mas nenhuma
      feature cobria essa tela). Decisão do usuário via `AskUserQuestion`: tela dedicada, inserida
      antes de `feat-004` (que passou a depender dela). 1 componente reaproveitável
      (`shared/catalog-manager`) instanciado 4x com `mat-tab-group`, em vez de 4 páginas quase
      idênticas — decisão de design explícita para não repetir o achado de duplicação do
      SonarCloud de `feat-003`. 2 subtasks, PRs #22-#24, CI/Sonar verdes (sem achado de
      duplicação desta vez).
- [x] **`apps/web feat-004` fechada** (RF04 UI — registro manual de apostas): primeiro
      formulário do app com regras de UX explícitas do TCC1 (8 regras de ouro de Shneiderman,
      mapeamento regra-a-regra no `plan_review`). `Idempotency-Key` client-side contra duplo-
      submit; dropdowns alimentados por `betting-houses`/catálogos em vez de UUIDs digitados.
      Achado real pego pelo próprio teste unitário antes do commit: banner de sucesso era zerado
      pela própria chamada de `reset()` logo em seguida — corrigido invertendo a ordem. 2
      subtasks, PRs #25-#27, CI/Sonar verdes (1 retrofit de achados reais do SonarCloud no PR
      final — mesmos `Web:InputWithoutLabelCheck`/`S6819` de `feat-002`, mais `typescript:S2699`,
      teste sem assertion real).
- [x] **`apps/web feat-005` fechada** (RF08 UI — histórico de operações): tela somente leitura
      (2 abas: Apostas/Movimentações), primeira com paginação de verdade. Gap real encontrado
      planejando esta feature: RF12 (status da aposta) e RF13 (depósitos/saques) também não
      tinham UI — decisão do usuário via `AskUserQuestion`: ficam fora, viram `feat-009`/
      `feat-010` (backlog, `not-started`, não bloqueiam nada). Padrão de `id`+`aria-label`/
      `<output>` (documentado em `docs/CONVENTIONS.md` após os achados de `feat-002`/`feat-004`)
      aplicado de saída — 1ª feature da sessão sem retrofit de SonarCloud no PR final. 2
      subtasks, PRs #28-#30, CI/Sonar verdes.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| Bundle inicial de `apps/web` acima do budget (601KB vs 500KB, warning não-bloqueante) | Pré-existente desde `feat-001` (confirmado via `git stash` comparando baseline em 570KB antes de `feat-002`) — não é regressão desta sessão. Revisitar lazy-loading do Angular Material quando `feat-006` (dashboard real) ou outra feature grande justificar. |
| `dashboard.scss` usa `height: calc(100vh - 64px)` fixo pra descontar a altura da nav | Funciona hoje (nav real de `feat-002.2` cabe nos 64px por coincidência), mas é frágil — sinalizado em `apps/web/progress.md` (`feat-002.2`) pra trocar por layout flex quando `feat-006` mexer no dashboard real. |
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar (`epic-007`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`apps/web feat-006`** (RF10/RF11 UI — dashboards e filtros dinâmicos) é a última feature
   elegível de `epic-006` — depende de `feat-005`, já `done`. Consome `GET /api/v1/statistics`
   (`stats-service feat-006`) via `api-gateway`; fechar esta feature fecha `epic-006` por
   completo (raiz). `ngx-echarts` já instalado desde `feat-001.6`.
3. **`apps/web feat-009`/`feat-010`** (RF12 status da aposta / RF13 depósitos-saques) — elegíveis
   depois de `feat-006` (dependência registrada), ainda sem `plan_review`. Gap real encontrado
   nesta sessão planejando `feat-005`, decisão do usuário de deixar pra depois.
4. Alternativa em paralelo (sessão/serviço diferente): **`epic-007`** (resiliência DLQ/retry,
   `infra/feat-002`) — elegível, ainda não iniciado. WIP máximo 1 por lane continua valendo — não
   trabalhar em `apps/web` e `infra` na mesma sessão.
5. **Padrão recorrente desta sessão, já resolvido em `feat-005` (aplicado de saída, sem retrofit
   necessário)**: todo PR `feature->develop` de `apps/web` pode pegar achados reais do
   SonarCloud (`Web:InputWithoutLabelCheck`, `Web:S6819`) que PRs de subtask não pegam (SonarCloud
   só roda no gate completo) — documentado em `docs/CONVENTIONS.md` seção Frontend. Ao criar
   formulário/input novo em `feat-006`, já aplicar de saída: `id` + `[attr.aria-label]` em todo
   `<input matInput>`/`<textarea matInput>`, e `<output>` em vez de `role="status"` pra qualquer
   banner de confirmação.
