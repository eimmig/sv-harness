# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-17

## Objetivo atual

**Todos os 30 epics do `feature_list.json` da raiz estão `done`**. **`apps/web feat-034`
(backlog residual sem epic próprio) também fechada nesta sessão** — nenhum harness tem feature
`not-started` conhecida no momento (conferir cada `feature_list.json` antes de assumir, ver
"Próxima sessão" abaixo).

## Concluído nesta sessão (2026-09-17)

- [x] `auth-service feat-018` fechada — fecha `epic-029`. `POST /api/v1/auth/change-password`.
      Bug real corrigido: `UserJpaEntity.applyUpdate()` descartava `passwordHash`/
      `mustChangePassword` silenciosamente desde `feat-017`.
- [x] `apps/web feat-035` fechada — fecha `epic-030`. Tela `/change-password`. Bug real corrigido:
      `FormGroup.reset()` não limpa a flag `submitted` da `FormGroupDirective` (Angular Material
      `ErrorStateMatcher`).
- [x] `apps/web feat-034` fechada — 4 achados ad-hoc de UX pós-deploy, sem epic próprio. Achado
      crítico: `NativeDateAdapter.parse()` (Angular Material) é `Date.parse()` puro, sempre M/D/Y,
      independente do locale ativo — uma máscara de digitação ordenada pelo locale trocava dia e
      mês em silêncio, só revelado por um teste e2e real (não por unitário). Ver
      `docs/CONVENTIONS.md` e `apps/web/progress.md` para o detalhe completo.
- [x] Decisão do usuário via `AskUserQuestion`: `mustChangePassword` continua sem bloqueio real de
      outras rotas — fecha o item aberto do `DECISIONS-LOG` de 2026-09-04.

## Bloqueios / Riscos

Nenhum conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Nenhum epic `not-started` na raiz, e `apps/web` sem backlog residual conhecido** — antes de
   assumir que não há trabalho, conferir cada harness (`services/*/feature_list.json`,
   `apps/web/feature_list.json`, `infra/feature_list.json`) por `"status": "not-started"`, já que
   features ad-hoc sem epic próprio (mesmo precedente de `feat-032`/`033`/`034`) podem surgir a
   qualquer momento a partir de achados do usuário em uso real.
3. `NativeDateAdapter.parse()` (Angular Material, `apps/web`) é `Date.parse()` puro — nunca
   respeita `MAT_DATE_LOCALE`/`setLocale()`, sempre lê M/D/Y para uma string com `/`. Qualquer
   campo de data futuro em `apps/web` ligado a `matDatepicker` via texto livre deve reaproveitar
   `core/date-mask.directive.ts` (`[appDateMask]`), não reinventar formatação ordenada pelo
   locale.
