# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-08

## Objetivo atual

- `epic-001`/`epic-002`/`epic-003`/`epic-004`/`epic-008`/`epic-009` — todos `done`.
- `epic-005` (telegram-integration) **em andamento** — `feat-001`..`feat-004` entregues e
  mergeados em `develop`. Restam `feat-005` (CI, fechamento formal) e `feat-006` (checklist de
  validação pré-deploy, criada nesta sessão).
- Situação: 6 de 9 epics `done`. `epic-005` é o único `in-progress`. `epic-006` (web) segue
  elegível (dependências satisfeitas) mas não iniciado. `epic-007` (resiliência DLQ) continua
  não elegível até `epic-005` fechar por completo.

## Concluído nesta sessão (2026-09-08)

- [x] **Decisão de produto tomada com o usuário via `AskUserQuestion`** (nenhuma nota fixava
      isso antes): resolução de catálogo no fluxo Telegram — `sport`/`league`/`market` sempre
      perguntados por lista numerada; `betting_house` por fuzzy match; catálogo vazio bloqueia a
      captura orientando cadastro em `apps/web`. Registrado em `docs/DECISIONS-LOG.md`.
- [x] **`api-gateway feat-007` fechada** (repositório separado, reaberto — `epic-008` já era
      `done`): bloqueador real achado no Plan Review de `telegram-integration feat-004` —
      `/api/v1/sports`/`leagues`/`markets` nunca tinham rota no Gateway apesar de existirem em
      `bets-service` desde a `feat-002` daquele serviço. PRs #24/#25, CI/SonarCloud verdes.
- [x] **`telegram-integration feat-004` fechada** (RF05 — integração com `POST /api/v1/bets`
      via `api-gateway`): `catalog_client.py` (busca paginada de catálogo) + `bets_client.py`
      (submissão final, `Idempotency-Key` via `update_id` nativo do Telegram, `bet_date`
      convertido pra `Instant` completo) + extensão de `orchestration.py`/`conversation.py`
      (fase de pergunta numerada com snapshot de opções). 4 subtasks (SV-198..201), CI/SonarCloud
      verdes, 85 testes, cobertura 100%. Ver `services/telegram-integration/progress.md` para o
      detalhe completo (achados do Plan Review, Delivery Reviewer, Test Suite Auditor).
- [x] **2 achados reais corrigidos durante a própria revisão de entrega** (não previstos no Plan
      Review original): estado da conversa era limpo incondicionalmente ao chegar em
      `"complete"` — corrigido pra só limpar após confirmar o outcome real da submissão, e
      limpar também em `CATALOG_ENTRY_NOT_FOUND`/`VALIDATION_FAILED` (retry cego nesses 2 casos
      reenviaria dado já comprovadamente inválido pra sempre). Fuzzy match de casa de apostas e
      uso do snapshot de catálogo ganharam teste pro caso realmente perigoso (match ambíguo,
      catálogo mudando entre pergunta e resposta) — nenhum teste anterior provava isso.
- [x] **`telegram-integration feat-006` criada no backlog** (`not-started`): reúne riscos
      residuais que só um ambiente real resolve — `n8n/telegram-bot.json` nunca importado numa
      instância n8n de verdade (7 pontos documentados em `n8n/README.md`), endpoints internos
      sem autenticação/limite de corpo enquanto não containerizados, rate limiting em
      `auth-service`, timezone de `bet_date` (UTC vs Brasília).
- [x] `docs/DECISIONS-LOG.md`, `docs/API-CONTRACTS.md`, `docs/services/{api-gateway,
      telegram-integration}.md` atualizados no mesmo commit lógico — inclusive uma correção de
      claim desatualizada (`docs/services/api-gateway.md` previa que `telegram-accounts` seria
      roteada pelo Gateway em sua `feat-004`; nunca foi — `telegram-integration feat-003` decidiu
      bypassar).
- [x] Corrigido um erro de documentação de ambiente de sessões anteriores: `TESSDATA_PREFIX`
      real desta máquina é `C:\Users\eduar\AppData\Local\tessdata`, não `~/.local/tessdata`
      como o handoff de `telegram-integration` registrava — `TESSERACT_CMD` também não estava
      persistido como variável de ambiente de usuário (só `TESSDATA_PREFIX` estava); ambos
      corrigidos via `setx`.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar (`epic-007`), que depende de `epic-004`+`epic-005` completos. Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| `bets-service` não consome `X-Correlation-Id` real ainda | Sinalizado em `docs/services/bets-service.md`, não é blocker de nada. |
| `n8n/telegram-bot.json` tem 7 pontos não validados contra instância real | Reunidos no checklist de `telegram-integration feat-006` (criada nesta sessão) — nenhuma instância n8n existe no projeto ainda; decidir com o usuário onde provisionar uma (`infra/`? deploy?) antes de codificar aquela feature. |
| `POST /bets/capture`/`POST /telegram/link` sem autenticação própria | Aceitável no estágio atual (rede local/interna, serviço não containerizado/exposto). Reunido em `telegram-integration feat-006`. |
| `web` sem código de aplicação | Só o commit de bootstrap do `epic-009`. Elegível, não iniciado. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`) — em `services/telegram-integration`, exportar
   `TESSDATA_PREFIX=/c/Users/eduar/AppData/Local/tessdata` e
   `TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"` se a sessão Bash não herdar o
   valor persistido (confirmar com `echo $TESSDATA_PREFIX` antes).
2. **`telegram-integration feat-005`** (fechamento formal do CI, sem código novo — mesmo padrão
   já usado em `auth-service feat-007`/`stats-service feat-007`/`api-gateway feat-005`) é a
   entrega mais rápida, sem dependência externa.
3. **`telegram-integration feat-006`** (checklist de validação pré-deploy) precisa de uma
   decisão prévia com o usuário: como/quando provisionar uma instância n8n real — nada em
   `infra/` provisiona n8n hoje.
4. Alternativa em paralelo (sessão/serviço diferente): **`epic-006` (`web`, Angular)** — todas as
   dependências satisfeitas, ainda não iniciado. WIP máximo 1 por lane de serviço continua
   valendo — não trabalhar em `telegram-integration` e `web` na mesma sessão.
5. `epic-007` (resiliência DLQ/retry) continua **não elegível** até `epic-005` fechar por
   completo.
