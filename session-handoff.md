# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-08

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service), `epic-004` (stats-service) e `epic-008`
  (api-gateway) — todos `done`.
- `epic-005` (telegram-integration) **em andamento** — `feat-001` (bootstrap) e `feat-002`
  (parsing) entregues e mergeados em `develop`. 3 features restam (`feat-003` vínculo de conta,
  `feat-004` integração com `api-gateway`, `feat-005` CI).
- Situação: 6 de 9 epics `done`. `epic-005` é o único `in-progress` no momento. `epic-006`
  (web) segue elegível (dependências satisfeitas) mas não iniciado.

## Concluído nesta sessão (2026-09-08)

- [x] **`telegram-integration feat-001`** (bootstrap uv/FastAPI/i18n/n8n) — ver entrada anterior
      deste log/`progress.md` para o detalhe completo.
- [x] **`telegram-integration feat-002` (Parsing de mensagens não estruturadas) implementado e
      mergeado em `develop`** — 4 subtasks (SV-186..189, story SV-185), 4 PRs de subtask + 1 PR
      de story, todos com CI real e verde. Ver `services/telegram-integration/progress.md` para
      o detalhe completo.
- [x] **Decisão de produto tomada com o usuário via `AskUserQuestion`** (nenhuma nota fixava o
      formato antes): captura de aposta via **foto do bilhete (OCR) ou texto livre**; motor de
      OCR = **Tesseract local**, não API de nuvem. Registrado em `docs/DECISIONS-LOG.md`
      2026-09-08, propagado para `docs/CONVENTIONS.md`, `docs/services/telegram-integration.md`,
      `docs/ARCHITECTURE.md`.
- [x] **2 achados reais MAJOR do Plan Review**, corrigidos antes de codificar: escopo de
      `feat-002` reduzido pra não resolver nomes extraídos contra o catálogo de `bets-service`
      (exige UUID, não nome — fica pra `feat-004`); download de foto movido pro n8n em vez do
      Python (evita segredo novo — `TELEGRAM_BOT_TOKEN` — neste serviço).
- [x] **2 achados reais encontrados durante a implementação/revisão**, corrigidos antes de
      fechar: normalização inconsistente no caminho de resposta direta a uma pergunta; dict de
      campos esparso no fluxo multi-turno (achado do Delivery Review, só exposto por um teste
      novo ponta a ponta pela HTTP real).
- [x] **Impedimento de ambiente resolvido**: Tesseract não estava instalado — `choco` falhou por
      falta de admin, resolvido via `winget` (já instalado, fora do PATH) + `tessdata`
      `por`/`eng` baixados pra `~/.local/tessdata` + `TESSDATA_PREFIX`/`TESSERACT_CMD`.
- [x] (continuação, mesmo dia) `api-gateway feat-005` fechou `epic-008` — ver entrada anterior.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, `epic-005` `in-progress`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| `bets-service` não consome `X-Correlation-Id` real ainda | Sinalizado em `docs/services/bets-service.md`, não é blocker de nada. |
| `n8n/telegram-bot.json` tem 4 pontos não validados contra instância real | Risco residual aceito, documentado em `services/telegram-integration/n8n/README.md`. Validar antes de produção. |
| `POST /bets/capture` sem autenticação própria | Aceitável no estágio atual (rede local/interna, serviço não containerizado/exposto). Revisitar quando containerizado. |
| `web` sem código de aplicação | Só o commit de bootstrap do `epic-009`. Elegível, não iniciado. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`) — em `services/telegram-integration`, exportar
   `TESSDATA_PREFIX`/`TESSERACT_CMD` se o terminal ainda não tiver o PATH persistido (deveria
   pegar sozinho após reiniciar o terminal, ver `docs/CONVENTIONS.md`).
2. **`telegram-integration feat-003`** (vínculo de conta Telegram, `/vincular <codigo>`) é a
   próxima natural — única feature elegível de `epic-005` agora (`feat-004` depende dela). Sem
   ela, `feat-004` não tem como resolver `telegramUserId -> userId/tenantId` de verdade.
3. Alternativa em paralelo (sessão/serviço diferente): **`epic-006` (`web`, Angular)** — todas
   as dependências satisfeitas, ainda não iniciado. WIP máximo 1 por lane de serviço continua
   valendo — não trabalhar em `telegram-integration` e `web` na mesma sessão.
4. `epic-007` (resiliência DLQ/retry) continua **não elegível** até `epic-005` fechar por
   completo (depende de `epic-004` + `epic-005`, não apenas `epic-005` `in-progress`).
