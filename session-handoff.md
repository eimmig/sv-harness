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
usuário no momento em que a credencial foi gerada), não um endereço real. Sem dano ao cluster
(o comando nunca conectou). Ver `docs/services/infra.md` "CD automático via CI" para o achado
completo e as 3 opções de correção — nenhuma decidida, é decisão de topologia de rede do usuário.
**As promoções `develop -> main` dos outros 5 repositórios de `epic-028` foram pausadas de
propósito** — mesma falha esperada, mesmo secret.

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
- [x] **`bets-service develop -> main` promovido (PR #70) para provar o job `deploy` — achado real
      de infraestrutura, não de código**: ver acima e `services/bets-service/progress.md` para o
      log de erro completo e a causa raiz.
- [x] 2 achados de processo (merge local em vez de PR; pular estado `Review` no Jira) cometidos
      nas 2 primeiras features de `epic-028` e corrigidos a partir da terceira — documentados nos
      `progress.md` de `bets-service`/`stats-service`.
- [x] 1 flake de infraestrutura em `telegram-integration` (Docker Hub, resolvido com rerun).

## Bloqueios / Riscos

- **Bloqueio real, aguardando decisão do usuário**: o CD automático de `epic-028` não funciona a
  partir de runners hospedados do GitHub Actions (ver acima). Precisa de uma decisão de rede antes
  de qualquer outro repositório promover `develop -> main` esperando que o `deploy` funcione de
  verdade — do contrário, os outros 5 vão repetir a mesma falha sem necessidade.
- Rollout manual (túnel SSH + `kubectl`, mesmo padrão de antes de `epic-028` existir) continua
  funcionando normalmente enquanto isso não for resolvido.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Não promover `develop -> main` dos outros 5 repositórios de `epic-028`
   (`stats-service`/`api-gateway`/`auth-service`/`telegram-integration`/`web`) esperando que o
   `deploy` funcione** até o usuário decidir o caminho de rede (`docs/services/infra.md` lista 3
   opções). Promover por outro motivo (release normal) continua seguro — só o `kubectl rollout
   restart` vai falhar do mesmo jeito, sem dano ao cluster.
3. `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) elegíveis agora.
4. `epic-024` continua aberto — `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de
   popular subtasks); `apps/web feat-022..024` ainda `not-started`.
5. Backlog dos 6 repositórios de `epic-028` está esgotado — nenhum tem feature elegível até surgir
   escopo novo (ou até a correção de rede virar uma feature própria em `infra/`).
