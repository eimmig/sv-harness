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
feat-018` fechou nesta sessão** — primeiro dos 6 repositórios de aplicação a ganhar o job
`deploy`. Faltam 5: `auth-service feat-016`, `stats-service feat-019`, `api-gateway feat-014`,
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

## Bloqueios / Riscos

Nenhum bloqueio novo. Risco documentado (não bloqueante): a promoção `develop -> main` de
`bets-service` deveria esperar `apps/web feat-021` para não quebrar `POST /api/v1/bets` em
produção — ver acima.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-028`: 5 repositórios de aplicação elegíveis agora, cada um pode virar uma sessão própria
   em paralelo (`auth-service feat-016`, `stats-service feat-019`, `api-gateway feat-014`,
   `telegram-integration feat-010`, `web feat-030`) — mesmo padrão já fechado em `bets-service
   feat-018`, reaproveitar o plano revisado (remover `azure/setup-kubectl`, `permissions: {}`
   explícito) sem repetir o ciclo de descoberta.
3. `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) também elegíveis, sem conflito
   de WIP com `epic-028` (harnesses diferentes).
4. `epic-024` continua aberto — reavaliar se o escopo de `apps/web`/`stats-service` daquele epic
   deveria virar features novas nos respectivos backlogs antes de mais alguém assumir.
5. Cuidado ao promover `bets-service develop -> main`: só depois de `apps/web feat-021` (troca de
   `team1`/`team2` texto livre por `team1Id`/`team2Id` no formulário) para não quebrar
   `POST /api/v1/bets` em produção — essa promoção também é a oportunidade de confirmar o job
   `deploy` de `feat-018` rodando de verdade pela primeira vez.
