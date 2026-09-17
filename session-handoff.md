# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-17

## Objetivo atual

Os 9 epics originais do TCC 1 e todas as rodadas seguintes (`epic-011..028`) estão `done`,
incluindo `epic-024` (evolução do domínio de times/jogadores, fechado em 2026-09-16). Nesta
sessão, dois epics novos surgiram a partir de um achado do usuário em uso real (nunca existiu
troca de senha, nem backend nem frontend): `epic-029` (`auth-service`, endpoint) e `epic-030`
(`apps/web`, tela), `epic-030` dependente de `epic-029`.

**`epic-029` fechado nesta sessão** — `auth-service feat-018` (`POST
/api/v1/auth/change-password`). Ver `progress.md` (entrada "`epic-029` fechado") para o detalhe
completo.

**`epic-030` (`apps/web`, tela de troca de senha) agora é o único epic `not-started` elegível** —
dependia só de `epic-029` (agora `done`) e `epic-006` (`done` há muito tempo).

## Concluído nesta sessão (2026-09-17)

- [x] `auth-service feat-018` fechada — fecha `epic-029` da raiz. Story SV-510, PRs #69-72,
      CI+SonarCloud verdes. Bug real de produção corrigido (`UserJpaEntity.applyUpdate()`
      descartava `passwordHash`/`mustChangePassword` silenciosamente desde `feat-017`).

## Bloqueios / Riscos

Nenhum conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Único epic `not-started` elegível: **`epic-030`** (`apps/web`, tela de troca de senha,
   `services/auth-service/feature_list.json` `feat-018` já fechada expõe o contrato real —
   `POST /api/v1/auth/change-password`, `currentPassword`+`newPassword` → `204`). Entrar em
   `apps/web/`, ler `apps/web/CLAUDE.md` e `docs/services/web.md`, rodar `Plan Reviewer` antes de
   codificar — decisão de UX em aberto (tela dedicada vs. campo dentro de uma tela de
   "conta"/perfil ainda inexistente neste app, ver descrição de `epic-030` em `feature_list.json`
   da raiz) precisa ser resolvida no plan review, possivelmente com `AskUserQuestion`.
3. Nenhum outro epic `not-started` tem dependências satisfeitas no momento — conferir
   `feature_list.json` (grep por `not-started`) antes de assumir que não há trabalho novo.
