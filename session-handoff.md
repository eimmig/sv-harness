# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-16

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-020`/`epic-021`/`epic-023`/`epic-025`/`epic-026`(api-gateway)/`epic-027`/
`epic-028` fechados. `epic-024` (times/jogadores) `in-progress` — `bets-service`
(`feat-016`+`feat-017`), `api-gateway feat-015` e `apps/web` (`feat-020`/`feat-021`/`feat-023`)
fechados; ainda cobre `stats-service feat-018` (`BLOCKED` pelo próprio Plan Reviewer) e `apps/web
feat-022` (`REVISE`, date picker)/`feat-024` (`READY`, espaçamento de cadastro). **É o único epic
aberto no momento.**

**`epic-021` e `epic-027` fechados por completo nesta sessão** (`apps/web feat-029` e
`feat-027`+`feat-026`). 2 decisões de design/UX reais levadas ao usuário via `AskUserQuestion`
antes de codificar: `feat-026` (não `feat-029`) é a dona de `byBetType`; a tela "Visão geral"
substitui o redirect pós-login (`/overview` em vez de `/dashboard`). Achados reais documentados
em `docs/API-CONTRACTS.md`/`docs/TESTING.md` (ver `apps/web/progress.md` para o detalhe).

**`apps/web feat-023` também fechada** (backlog residual de `epic-024`): achado de usuário real
(sobreposição do seletor de idioma no login) investigado e corrigido de verdade — causa raiz
medida contra o dev server (`display: block` envolvendo filho `width: 100%` sem largura de
ancestral). Gotcha reutilizável documentado em `docs/CONVENTIONS.md`.

**`epic-028` (CD automático via CI) fechado no `feature_list.json` — mas o mecanismo real não
funciona ainda**: `kubectl rollout restart` não alcança o cluster a partir de um runner hospedado
do GitHub Actions (`KUBE_CONFIG` aponta pro túnel SSH local do usuário). Ver
`docs/services/infra.md` "CD automático via CI". **Perguntado ao usuário — respondeu "deixar
como está por agora"**: nenhuma mudança de rede será tentada até ele decidir; rollout continua
manual. As 6 imagens `:latest` no GHCR estão atualizadas.

## Concluído nesta sessão (2026-09-15/16)

- [x] `epic-028` fechado no JSON (CD automático, 6 repositórios) — decisão de rede deixada como
      está a pedido do usuário.
- [x] `api-gateway feat-015` + `apps/web feat-020`+`feat-021` fecharam a pedido explícito do
      usuário — corrigiram a quebra real de `POST /api/v1/bets`.
- [x] Os 6 repositórios de aplicação promovidos `develop -> main`.
- [x] `apps/web feat-028` fechada — fecha `epic-020` da raiz (grade mensal de drawdown).
- [x] `apps/web feat-027` + `feat-026` fechadas — fecham `epic-027` da raiz por completo.
- [x] `apps/web feat-029` fechada — fecha `epic-021` da raiz por completo (tela "Visão geral").
- [x] **`apps/web feat-023` fechada** — corrige a sobreposição real do seletor de idioma no
      login. Ver `apps/web/progress.md` para o detalhe completo.

## Bloqueios / Riscos

- **Bloqueio de rede conhecido, usuário decidiu deixar como está por agora**: o CD automático de
  `epic-028` não funciona a partir de runners hospedados do GitHub Actions (ver acima). Sem ação
  pendente — não repetir a pergunta nem tentar corrigir sozinho a menos que o usuário peça.

- **`services/telegram-integration` E a raiz (`init.sh`) têm mudanças não commitadas, não feitas
  nesta sessão**: `git status` mostra scripts modificados (SHA-pinning de GitHub Actions em
  `telegram-integration`, `[` → `[[` bash em ambos, flags `uv --no-build --locked`) — não
  investigado nem tocado (fora do escopo do trabalho desta sessão, e não foi este agente quem
  editou; confirmado que os outros 5 repositórios de serviço não têm a mesma mudança). Investigar
  a origem antes de commitar ou descartar — deixado como está.

Nenhum outro bloqueio conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Único epic aberto: `epic-024` (`services/bets-service/`, escopo restante todo em `apps/web`) —
   `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de popular subtasks); `apps/web
   feat-024` (espaçamento dos cadastros) é `READY`, próximo candidato natural; `feat-022` (date
   picker) é `REVISE` — falta decidir/confirmar o `DateAdapter` reativo ao idioma e o tratamento
   de `betDate` (datetime-local) antes de codificar, ver `plan_review` completo.
3. Nenhum outro epic `not-started` tem dependências satisfeitas no momento — conferir
   `feature_list.json` (grep por `not-started`) antes de assumir que não há trabalho novo.
4. Se o usuário quiser rodar o rollout manual em produção agora (imagens já atualizadas): mesmo
   padrão de sempre, túnel SSH + `kubectl rollout restart deployment/<serviço>` por repositório.
5. **Encerrar qualquer `ng serve` (ou dev server equivalente) usado pra QA visual assim que
   terminar aquele passo** — um processo esquecido rodando em background segurou um lock em
   `node_modules/@esbuild/.../esbuild.exe`, quebrando `npm ci`/`./init.sh` mais tarde na mesma
   sessão (achado real, `feat-023.3`, ver `docs/TESTING.md`).
