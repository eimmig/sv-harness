# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-023`/`epic-025`/`epic-026` fechados; `epic-024` (times/jogadores)
`in-progress` — `bets-service` (`feat-016`+`feat-017`) fechado, mas a description do epic também
cobre `stats-service feat-018` e `apps/web feat-020..024` (label "Data do evento", date pickers,
ícone do seletor de idioma, espaçamento de cadastro), nenhum tocado ainda — não fechar o epic sem
revisitar esse escopo mais amplo.

`epic-028` (CD automático via CI, `infra/`) segue `in-progress`: o lado de `infra/` já fechou
(ServiceAccount `ci-deployer` + `KUBE_CONFIG` reais, aplicado pelo usuário) e **`bets-service
feat-018` e `stats-service feat-019` fecharam nesta sessão** — 2 dos 6 repositórios de aplicação
já com o job `deploy`. Faltam 4: `auth-service feat-016`, `api-gateway feat-014`,
`telegram-integration feat-010`, `web feat-030` — todos elegíveis agora, cada um em seu próprio
repositório/sessão, sem conflito de WIP entre si.

Epics `not-started` elegíveis (dependências satisfeitas): `epic-020`/`epic-027` (`apps/web`, só
um por vez — WIP 1 por harness). `epic-021` (`apps/web`) ainda depende de `epic-027`.

## Concluído nesta sessão (2026-09-15)

- [x] **`bets-service feat-018` fechada** (job `deploy` automático em `ci.yml`, `kubectl rollout
      restart` contra `KUBE_CONFIG`/`ci-deployer` de `infra/feat-007`). `Plan Reviewer` corrigiu 2
      MINOR antes de codificar (remover `azure/setup-kubectl` — redundante, `kubectl` já vem
      preinstalado no runner `ubuntu-latest`; adicionar `permissions: {}` explícito). `Delivery
      Reviewer` PASS, `Test Suite Auditor` PASS/N/A. Story SV-423, PRs #67/#68/#69, CI+SonarCloud
      verdes, merge `feature/SV-423 -> develop` concluído.
- [x] **Decisão real, não só ferramental**: o primeiro disparo de verdade do job `deploy` (contra
      produção) foi deliberadamente **adiado**. `main` de `bets-service` estava 35 commits atrás
      de `develop`, incluindo `feat-017` (quebra conhecida do contrato REST síncrono de
      `POST /api/v1/bets` para quem ainda envia `team1`/`team2` texto livre — só `apps/web
      feat-021`, ainda `not-started`, corrige). Promover `develop -> main` agora só para provar o
      job forçaria essa quebra em produção sem necessidade real — decisão de não fazer,
      documentada em `services/bets-service/progress.md`/`session-handoff.md`. **Quando essa
      promoção acontecer** (depois de `apps/web feat-021`), registrar a confirmação real (log do
      Actions) em `docs/services/infra.md`.
- [x] `docs/services/infra.md` corrigido — seção "CD automático via CI" ainda dizia "em
      andamento" e "`KUBE_CONFIG` ainda não existe em nenhum repositório", desatualizado desde que
      `infra/feat-007` fechou numa sessão anterior no mesmo dia.
- [x] **`stats-service feat-019` fechada** — reaproveitou byte a byte o padrão de `bets-service
      feat-018` (mesma sessão), única diferença o nome do `Deployment`. `Delivery Reviewer`: PASS
      (revisão condensada). Story SV-426, PRs #59/#60/#61, CI+SonarCloud verdes. Mesma decisão de
      adiar o disparo real (main ~20 commits atrás de develop, decisão de release mais ampla).
- [x] **2 achados de processo nesta sessão, ambos documentados em `services/stats-service/
      progress.md` para não se repetir nos 4 repositórios restantes de `epic-028`**: (1) tentei
      mesclar `story -> develop` com `git merge --no-ff` local em vez de PR real — revertido antes
      de empurrar (`git reset --hard origin/develop`) e refeito via `gh pr create`/`gh pr merge`;
      o gate pesado sempre passa por PR real com CI+SonarCloud, nunca merge local direto. (2) em
      **ambos** `bets-service feat-018` e `stats-service feat-019`, marquei a última subtask e a
      feature inteira `done` na mesma edição do `feature_list.json` antes de rodar
      `--sync-status` uma única vez — pula o estado `Review` no board do Jira (vai direto
      `In Progress -> Done`), exatamente o erro que `CLAUDE.md` da raiz já documenta (seção "O
      board é vivo") ter acontecido antes em `auth-service feat-002`. Não refeito retroativamente
      (estado final `Done` correto, só a rastreabilidade intermediária ficou incompleta) — mas os
      próximos 4 fechamentos de `epic-028` devem separar em 2 disparos de `--sync-status`.

## Bloqueios / Riscos

Nenhum bloqueio novo. Risco documentado (não bloqueante, mesmo padrão nos 2 repositórios
fechados): a promoção `develop -> main` de `bets-service` deveria esperar `apps/web feat-021`
para não quebrar `POST /api/v1/bets` em produção; a de `stats-service` não tem quebra conhecida
mas acumula ~20 commits sem promoção — ambas as decisões de release ficam para quando fizer
sentido, não são bloqueio desta feature.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-028`: 4 repositórios de aplicação elegíveis agora, cada um pode virar uma sessão própria
   em paralelo (`auth-service feat-016`, `api-gateway feat-014`, `telegram-integration feat-010`,
   `web feat-030`) — mesmo padrão já fechado em `bets-service feat-018`/`stats-service feat-019`,
   reaproveitar o plano revisado (remover `azure/setup-kubectl`, `permissions: {}` explícito) sem
   repetir o ciclo de descoberta. **Ao fechar**: (a) merge `story -> develop` sempre via PR real
   no GitHub, nunca `git merge` local; (b) separar em 2 disparos de `--sync-status` — um depois de
   marcar a última subtask `done` (feature ainda `in-progress`, story cai em `Review`), outro
   depois de marcar a feature `done` numa edição separada.
3. `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) também elegíveis, sem conflito
   de WIP com `epic-028` (harnesses diferentes).
4. `epic-024` continua aberto — reavaliar se o escopo de `apps/web`/`stats-service` daquele epic
   deveria virar features novas nos respectivos backlogs antes de mais alguém assumir. Nota:
   `stats-service feat-018` (parte desse epic) está `BLOCKED` pelo próprio Plan Reviewer — não
   confundir com `feat-019` (fechada nesta sessão, epic-028, sem relação).
5. Cuidado ao promover `bets-service develop -> main`: só depois de `apps/web feat-021` (troca de
   `team1`/`team2` texto livre por `team1Id`/`team2Id` no formulário) para não quebrar
   `POST /api/v1/bets` em produção — essa promoção também é a oportunidade de confirmar o job
   `deploy` de `feat-018` rodando de verdade pela primeira vez. `stats-service` não tem essa
   restrição de contrato, pode promover quando fizer sentido como release.
