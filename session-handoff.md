# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-11-04

## Objetivo atual

Desenvolvimento encerrado: 52 de 52 epics `done`. O que falta é levar a produção (k3s) até o código
que já está em `main`/`develop`.

## Backlog

- 52 de 52 epics `done`: `epic-049` (telegram-integration `feat-014`) fechado em 2026-11-04, story
  SV-806. Está em `develop`, ainda não em `main` nem em produção.
- telegram-integration `feat-016`: odd/stake vazia chega ao envio e gera `400`.
- `apps/web feat-077`: specs de página estouram o timeout de 5 s só com a suíte inteira.

Os 7 repositórios estão em `develop`, com working tree limpo.

## Pendente de produção

O deploy do CI falha sempre (`connection refused` em `127.0.0.1:6443`), então todo rollout é manual.
Script: `tools/rollout-producao.sh` (kubectl por SSH no servidor; `HOST=<ip>` se o IP mudar).

1. `bash tools/rollout-producao.sh backend`: `auth-service` e `stats-service`. As imagens de `main`
   já estão no GHCR (`build-and-push-image` verde nos runs 41523758410 e 41523746988).
2. Só depois, `bash tools/rollout-producao.sh web`: abre o PR de release `develop -> main` do
   `sv-frontend` (leva `feat-078` e `feat-072`), espera a CI, faz o merge, espera o
   `build-and-push-image` **daquele merge** e reinicia o `web`. Inverter a ordem quebra a tela
   Vincular Telegram, que depende de `GET /api/v1/telegram-links/me`.
3. telegram-integration: release `develop -> main` (leva `feat-014`) e `kubectl rollout restart`
   dele. Independe da ordem dos passos 1 e 2.

Em 2026-11-02 o classificador do auto mode bloqueou esses passos ("Production Deploy"): o usuário
roda o script ou autoriza explicitamente.

## Bloqueios / Riscos

- IP do servidor não é fixo (`docs/services/infra.md`, "Acesso ao servidor"). Servidor nem sempre
  ligado: perguntar antes de depender dele.
- Depois de um boot do servidor, esperar 10 a 15 min antes de medir qualquer coisa.

## Próxima sessão — por onde começar

1. `./init.sh` na raiz.
2. Se o servidor estiver ligado, seguir "Pendente de produção" e registrar o resultado no
   `progress.md`.
