# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-020`/`epic-021`/`epic-023`/`epic-025`/`epic-026`(api-gateway)/`epic-027`/
`epic-028` fechados. `epic-024` (times/jogadores) `in-progress` — `bets-service`
(`feat-016`+`feat-017`) e `apps/web` (`feat-020`+`feat-021`) fechados; ainda cobre `stats-service
feat-018` (`BLOCKED` pelo próprio Plan Reviewer) e `apps/web feat-022..024` (date pickers, ícone
do seletor de idioma, espaçamento de cadastro), nenhum tocado ainda — não fechar o epic sem
revisitar esse escopo mais amplo. **É o único epic aberto no momento.**

**`epic-021` (web — tela "Visão geral" pós-login) fechado por completo nesta sessão**
(`apps/web feat-029`). Decisão de UX real levada ao usuário via `AskUserQuestion`: a tela nova
substitui o redirect pós-login (login agora vai pra `/overview` em vez de `/dashboard`, que virou
item normal de nav). Achado real durante a implementação: `monthly[]` de
`GET /api/v1/statistics` não vem escopado ao ano corrente quando a chamada não tem `from`/`to` —
diferente do que a própria descrição do epic assumia — filtrado client-side, documentado em
`docs/API-CONTRACTS.md`/`docs/services/web.md`. Achado real de teste (só em CI): 2 specs novos
sobrescreviam `navigator.language` sem restaurar no `afterEach`, vazando pro próximo arquivo no
mesmo worker do Vitest — corrigido, documentado em `docs/TESTING.md`.

**`epic-027` também fechado por completo nesta sessão** (`apps/web feat-027` + `feat-026`).
Decisão de design real levada ao usuário via `AskUserQuestion`: `feat-026` (não `feat-029`) é a
dona do campo `byBetType` em `core/statistics-api.ts`.

**`epic-028` (CD automático via CI) fechado no `feature_list.json` — mas o mecanismo real não
funciona ainda**: os 6 repositórios de aplicação ganharam o job `deploy`, e `infra/feat-007`
distribuiu o `KUBE_CONFIG`, mas `kubectl rollout restart` não consegue alcançar o cluster a
partir de um runner hospedado do GitHub Actions — o `KUBE_CONFIG` tem
`server: https://127.0.0.1:6443` (o túnel SSH local do usuário no momento em que a credencial foi
gerada), não um endereço real. Confirmado idêntico nos 6 repositórios. Sem dano a nenhum cluster
(o comando nunca conecta). Ver `docs/services/infra.md` "CD automático via CI" para o achado
completo e as 3 opções de correção. **Perguntado ao usuário explicitamente como prosseguir —
respondeu "deixar como está por agora"**: nenhuma mudança de rede/infraestrutura será tentada até
ele decidir; rollout continua manual (túnel SSH). As 6 imagens `:latest` no GHCR estão
atualizadas (todos os 6 repositórios promovidos `develop -> main` nesta sessão).

## Concluído nesta sessão (2026-09-15)

- [x] `epic-028` fechado no JSON (CD automático, 6 repositórios) — achado real de infraestrutura
      documentado acima, decisão de rede deixada como está a pedido do usuário.
- [x] `api-gateway feat-015` + `apps/web feat-020`+`feat-021` fecharam a pedido explícito do
      usuário — corrigiram a quebra real de `POST /api/v1/bets` antes de qualquer deploy em massa.
- [x] Os 6 repositórios de aplicação promovidos `develop -> main`, confirmando a mesma falha de
      rede em todos e publicando imagem `:latest` fresca em todos.
- [x] `apps/web feat-028` fechada — fecha `epic-020` da raiz (grade mensal de drawdown no
      dashboard). Achados reais corrigidos: bug de design, regressão pré-existente de `feat-021`
      no e2e, bug de responsividade mobile, 2 achados de SonarCloud.
- [x] `apps/web feat-027` + `feat-026` fechadas — fecham `epic-027` da raiz por completo: tela de
      vínculo Telegram, `betType` alinhado a `mat-select` PRE/LIVE e `byBetType` tipado e exibido
      num dashboard novo.
- [x] **`apps/web feat-029` fechada — fecha `epic-021` da raiz por completo**: tela "Visão geral"
      pós-login (`/overview`), curva de lucro acumulado vitalícia, 4 cards, tabela mensal. Login
      redireciona pra cá em vez de `/dashboard`. Ver `apps/web/progress.md` para o detalhe
      completo, inclusive os 2 achados reais (backend `monthly[]` não escopado ao ano; teste
      `navigator.language` vazando entre specs).

## Bloqueios / Riscos

- **Bloqueio de rede conhecido, usuário decidiu deixar como está por agora**: o CD automático de
  `epic-028` não funciona a partir de runners hospedados do GitHub Actions (ver acima). Sem ação
  pendente — não repetir a pergunta nem tentar corrigir sozinho a menos que o usuário peça.

Nenhum outro bloqueio conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Único epic aberto: `epic-024` (`services/bets-service/`, mas o escopo restante vive todo em
   `apps/web`) — `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de popular
   subtasks); `apps/web feat-022..024` ainda `not-started` (`feat-024`, espaçamento dos
   cadastros, é `READY`; `feat-022`, date picker, tem 2 achados MAJOR já corrigidos no plano).
3. Nenhum outro epic `not-started` tem dependências satisfeitas no momento — conferir
   `feature_list.json` (grep por `not-started`) antes de assumir que não há trabalho novo.
4. Se o usuário quiser rodar o rollout manual em produção agora (imagens já atualizadas): mesmo
   padrão de sempre, túnel SSH + `kubectl rollout restart deployment/<serviço>` por repositório.
