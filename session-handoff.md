# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-09

## Objetivo atual

- `epic-001`/`epic-002`/`epic-003`/`epic-004`/`epic-005`/`epic-008`/`epic-009` — todos `done`.
- `epic-006` (`apps/web`) **em andamento** — `feat-001`/`feat-002`/`feat-003`/`feat-007` entregues
  e mergeados em `develop`. Restam `feat-004` (RF04 UI, registro manual de apostas), `feat-005`
  (RF08 UI, histórico) e `feat-006` (RF10/RF11 UI, dashboards).
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

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| Bundle inicial de `apps/web` acima do budget (601KB vs 500KB, warning não-bloqueante) | Pré-existente desde `feat-001` (confirmado via `git stash` comparando baseline em 570KB antes de `feat-002`) — não é regressão desta sessão. Revisitar lazy-loading do Angular Material quando `feat-006` (dashboard real) ou outra feature grande justificar. |
| `dashboard.scss` usa `height: calc(100vh - 64px)` fixo pra descontar a altura da nav | Funciona hoje (nav real de `feat-002.2` cabe nos 64px por coincidência), mas é frágil — sinalizado em `apps/web/progress.md` (`feat-002.2`) pra trocar por layout flex quando `feat-006` mexer no dashboard real. |
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar (`epic-007`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`apps/web feat-004`** (RF04 UI — registro manual de apostas, oito regras de ouro de
   Shneiderman, ver `docs/services/web.md`) é a próxima feature elegível — depende só de
   `feat-003`, já `done`. Consome `bets-service` (`POST /api/v1/bets`, catálogos
   `sports`/`leagues`/`markets`/`tipsters` já existentes desde `bets-service feat-002`) e
   `betting-houses` (já existe, `feat-003`) via `api-gateway`.
3. Alternativa em paralelo (sessão/serviço diferente): **`epic-007`** (resiliência DLQ/retry,
   `infra/feat-002`) — elegível, ainda não iniciado. WIP máximo 1 por lane continua valendo — não
   trabalhar em `apps/web` e `infra` na mesma sessão.
4. Antes de começar `feat-004`, revisar `apps/web/CLAUDE.md` seção sobre o formulário de aposta
   (regras de Shneiderman) — mais complexo que `feat-002`/`feat-003` (validação de 4 FKs
   obrigatórias + 1 opcional, `Idempotency-Key`, mensagens RN07).
