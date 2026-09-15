# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-023`/`epic-025`/`epic-026`/**`epic-028`** fechados; `epic-024`
(times/jogadores) `in-progress` — `bets-service` (`feat-016`+`feat-017`) e `apps/web`
(`feat-020`+`feat-021`) fechados; ainda cobre `stats-service feat-018` (`BLOCKED` pelo próprio
Plan Reviewer) e `apps/web feat-022..024` (date pickers, ícone do seletor de idioma, espaçamento
de cadastro), nenhum tocado ainda — não fechar o epic sem revisitar esse escopo mais amplo.

**`epic-028` (CD automático via CI) fechado no `feature_list.json` — mas o mecanismo real não
funciona ainda**: os 6 repositórios de aplicação ganharam o job `deploy`, e `infra/feat-007`
distribuiu o `KUBE_CONFIG`, mas o primeiro disparo real (`bets-service`, PR #70) **falhou**:
`kubectl rollout restart` não consegue alcançar o cluster a partir de um runner hospedado do
GitHub Actions — o `KUBE_CONFIG` tem `server: https://127.0.0.1:6443` (o túnel SSH local do
usuário no momento em que a credencial foi gerada), não um endereço real. **Confirmado idêntico
nos outros 5 repositórios** depois (usuário perguntou se havia imagem atualizada de todos os
serviços pra `docker pull` manual — não havia, promovidos todos os 6 `develop -> main`):
`build-and-push-image` verde nos 6 (imagens `:latest` atualizadas e prontas), `deploy` falha do
mesmo jeito nos 6. Sem dano a nenhum cluster (o comando nunca conecta em nenhuma tentativa). Ver
`docs/services/infra.md` "CD automático via CI" para o achado completo e as 3 opções de correção.
**Perguntado ao usuário explicitamente como prosseguir — respondeu "deixar como está por agora"**:
nenhuma mudança de rede/infraestrutura será tentada até ele decidir; rollout continua manual (túnel
SSH) como sempre foi antes de `epic-028` existir.

Epics `not-started` elegíveis (dependências satisfeitas): `epic-020`/`epic-027` (`apps/web`, só
um por vez — WIP 1 por harness). `epic-021` (`apps/web`) ainda depende de `epic-027`.

## Concluído nesta sessão (2026-09-15)

- [x] **`epic-028` fechado no JSON** — 6 features em 6 repositórios, cada uma sua própria
      story/subtasks/PRs, CI+SonarCloud reais verdes. Ver `progress.md` da raiz e de cada serviço.
- [x] **A pedido explícito do usuário, depois de `epic-028` fechar** ("corrija a quebra de
      `bets-service`/`apps/web` primeiro, depois dê deploy em tudo"): `api-gateway feat-015`
      (rota `/api/v1/teams`, achado de `bets-service feat-017`) e `apps/web feat-020`+`feat-021`
      fecharam — o segundo corrige de verdade a quebra de `POST /api/v1/bets` (tela nova
      `shared/team-manager` + `register-bet` usando `team1Id`/`team2Id`). `Delivery Reviewer`
      completo (não condensado) rodou nessa feature por ser mudança de negócio real.
- [x] **Os 6 repositórios de aplicação promovidos `develop -> main`** (`bets-service` PR #70 pra
      provar o job `deploy` pela primeira vez; os outros 5 — `stats-service`/`api-gateway`/
      `auth-service`/`telegram-integration`/`web` — a pedido do usuário, que perguntou se havia
      imagem atualizada de todos os serviços pra puxar manualmente no servidor). Achado real de
      infraestrutura confirmado idêntico nos 6, não de código: ver acima e
      `services/bets-service/progress.md` para o log de erro completo e a causa raiz. **As 6
      imagens `:latest` no GHCR estão atualizadas e prontas para `docker pull` no servidor** — só
      a automação do `rollout restart` via CI que não funciona ainda.
- [x] 2 achados de processo (merge local em vez de PR; pular estado `Review` no Jira) cometidos
      nas 2 primeiras features de `epic-028` e corrigidos a partir da terceira — documentados nos
      `progress.md` de `bets-service`/`stats-service`.
- [x] 1 flake de infraestrutura em `telegram-integration` (Docker Hub, resolvido com rerun).

## Bloqueios / Riscos

- **Bloqueio de rede conhecido, usuário decidiu deixar como está por agora**: o CD automático de
  `epic-028` não funciona a partir de runners hospedados do GitHub Actions (ver acima). Sem ação
  pendente — não repetir a pergunta nem tentar corrigir sozinho a menos que o usuário peça.
- As 6 imagens `:latest` estão atualizadas no GHCR (verificado nesta sessão) — o rollout em
  produção é manual (túnel SSH + `kubectl`) até o usuário decidir mudar isso.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) elegíveis agora.
3. `epic-024` continua aberto — `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de
   popular subtasks); `apps/web feat-022..024` ainda `not-started`.
4. Backlog dos 6 repositórios de `epic-028` está esgotado — nenhum tem feature elegível até surgir
   escopo novo.
5. Se o usuário quiser rodar o rollout manual em produção agora (imagens já atualizadas): mesmo
   padrão de sempre, túnel SSH + `kubectl rollout restart deployment/<serviço>` por repositório.
