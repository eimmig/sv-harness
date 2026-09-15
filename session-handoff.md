# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-023`/`epic-025`/`epic-026`/**`epic-028`** fechados; `epic-024`
(times/jogadores) `in-progress` — `bets-service` (`feat-016`+`feat-017`) fechado, mas a
description do epic também cobre `stats-service feat-018` (esse, à parte, está `BLOCKED` pelo
próprio Plan Reviewer — não confundir com `stats-service feat-019`, fechada por `epic-028`) e
`apps/web feat-020..024` (label "Data do evento", date pickers, ícone do seletor de idioma,
espaçamento de cadastro), nenhum tocado ainda — não fechar o epic sem revisitar esse escopo mais
amplo.

**`epic-028` (CD automático via CI) fechado por completo nesta sessão** — os 6 repositórios de
aplicação (`bets-service feat-018`, `stats-service feat-019`, `api-gateway feat-014`,
`auth-service feat-016`, `telegram-integration feat-010`, `web feat-030`) ganharam o job `deploy`
no `ci.yml`, todos reaproveitando o mesmo plano revisado uma única vez. `infra/feat-007` (lado do
servidor) já tinha fechado mais cedo no mesmo dia. Ver `docs/services/infra.md` "CD automático via
CI" para o estado consolidado.

Epics `not-started` elegíveis (dependências satisfeitas): `epic-020`/`epic-027` (`apps/web`, só
um por vez — WIP 1 por harness). `epic-021` (`apps/web`) ainda depende de `epic-027`.

## Concluído nesta sessão (2026-09-15)

- [x] **`epic-028` fechado por completo** — 6 features em 6 repositórios diferentes, cada uma sua
      própria story/subtasks/PRs, todas com CI+SonarCloud reais verdes. Ver `progress.md` da raiz
      e o `progress.md` de cada serviço tocado para o detalhe completo por feature.
- [x] **Decisão real repetida nos 6 repositórios**: o primeiro disparo de verdade do job `deploy`
      contra produção foi **deliberadamente adiado** em todos — nenhuma promoção
      `develop -> main` aconteceu nesta sessão. `bets-service` tem razão concreta (`feat-017`
      quebra `POST /api/v1/bets` até `apps/web feat-021` corrigir); os outros 5 porque promover
      `main` é decisão de release mais ampla, não desta feature. **Pendência real para a próxima
      vez que cada repositório promover `develop -> main`**: registrar a confirmação do rollout
      real (log do GitHub Actions) em `docs/services/infra.md`.
- [x] **2 achados de processo cometidos nas 2 primeiras features (`bets-service`/`stats-service`)
      e corrigidos a partir da terceira (`api-gateway`) em diante**: (1) merge `story -> develop`
      tentado como `git merge --no-ff` local em vez de PR real no GitHub — sempre usar PR real com
      CI+SonarCloud daqui pra frente. (2) marcar a última subtask e a feature inteira `done` na
      mesma edição do `feature_list.json` antes de um único `--sync-status` pula o estado `Review`
      no board do Jira — sempre separar em 2 disparos (subtask done sozinha → `Review`; feature
      done depois, edição separada → `Done`). Ambos documentados nos `progress.md` de
      `bets-service`/`stats-service` para não se repetirem.
- [x] Achado de infraestrutura (não de código): 1 rerun de CI necessário em
      `telegram-integration` (falha transitória de rede puxando a imagem `redis` do Docker Hub via
      testcontainers) — `gh run rerun --failed` resolveu.

## Bloqueios / Riscos

Nenhum bloqueio novo. Risco documentado (não bloqueante): a promoção `develop -> main` de
`bets-service` deveria esperar `apps/web feat-021` para não quebrar `POST /api/v1/bets` em
produção.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) elegíveis agora.
3. `epic-024` continua aberto — reavaliar se o escopo de `apps/web`/`stats-service` daquele epic
   deveria virar features novas nos respectivos backlogs antes de mais alguém assumir. Nota:
   `stats-service feat-018` (parte desse epic) está `BLOCKED` pelo próprio Plan Reviewer — reler
   aquele `plan_review` antes de popular subtasks.
4. Backlog dos 6 repositórios de `epic-028` está esgotado em todos — nenhum tem feature elegível
   até surgir escopo novo.
5. Quando qualquer um dos 6 repositórios de `epic-028` promover `develop -> main` pela primeira
   vez desde esta sessão: confirmar o job `deploy` rodando de verdade (log do Actions) e registrar
   em `docs/services/infra.md`. Prioridade natural: `bets-service`, assim que `apps/web feat-021`
   fechar.
