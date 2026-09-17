# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-17

## Objetivo atual

**Todos os 30 epics do `feature_list.json` da raiz estão `done`** — os 9 originais do TCC 1 e
todas as rodadas seguintes (`epic-011..030`), incluindo `epic-029`/`epic-030` (endpoint + tela de
troca de senha, achado do usuário em uso real, fechados nesta sessão). Não há epic `not-started`
elegível no momento.

Isso **não** significa que não há mais trabalho: cada harness pode ter backlog residual próprio,
sem epic correspondente na raiz (mesmo precedente de `apps/web feat-032`/`033`). Verificado nesta
sessão: `apps/web feat-034` (4 achados ad-hoc de UX pós-deploy: campos `searchable-select`
grudados, rótulo cortado no drawdown mensal, logo quebrando em 2 linhas na sidebar colapsada,
máscara de data ausente) é `not-started`, sem `plan_review` ainda — ver
`apps/web/session-handoff.md`.

## Concluído nesta sessão (2026-09-17)

- [x] `auth-service feat-018` fechada — fecha `epic-029`. `POST /api/v1/auth/change-password`.
      Bug real corrigido: `UserJpaEntity.applyUpdate()` descartava `passwordHash`/
      `mustChangePassword` silenciosamente desde `feat-017`.
- [x] `apps/web feat-035` fechada — fecha `epic-030`. Tela `/change-password`. Bug real corrigido:
      `FormGroup.reset()` não limpa a flag `submitted` da `FormGroupDirective` (Angular Material
      `ErrorStateMatcher`).
- [x] Decisão do usuário via `AskUserQuestion`: `mustChangePassword` continua sem bloqueio real de
      outras rotas — fecha o item aberto do `DECISIONS-LOG` de 2026-09-04.

## Bloqueios / Riscos

Nenhum conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Nenhum epic `not-started` na raiz** — não escolher trabalho aqui sem antes verificar se o
   usuário tem um pedido novo, ou entrar em `apps/web/` pra `feat-034` (backlog residual daquele
   harness, sem epic próprio, ver `apps/web/session-handoff.md`).
3. Antes de assumir que não há trabalho: `grep -c '"status": "not-started"' feature_list.json`
   (raiz) confirma 0; mas cada harness (`services/*/feature_list.json`, `apps/web/feature_list.json`,
   `infra/feature_list.json`) pode ter feature própria pendente sem epic correspondente aqui —
   conferir cada um antes de reportar "nada a fazer".
