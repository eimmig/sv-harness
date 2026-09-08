# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-08

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service), `epic-004` (stats-service) e `epic-008`
  (api-gateway) — todos `done`.
- `epic-005` (telegram-integration) **em andamento** — `feat-001` (bootstrap) entregue e
  mergeado em `develop`. 4 features restam (`feat-002` parsing, `feat-003` vínculo de conta,
  `feat-004` integração com `api-gateway`, `feat-005` CI).
- Situação: 6 de 9 epics `done`. `epic-005` é o único `in-progress` no momento. `epic-006`
  (web) segue elegível (dependências satisfeitas) mas não iniciado nesta sessão.

## Concluído nesta sessão (2026-09-08)

- [x] **`telegram-integration feat-001` (Setup do projeto Python + webhook n8n) implementado e
      mergeado em `develop`** — primeiro serviço Python do backlog, nenhum código existia antes.
      Bootstrap real via `uv init`/`uv add` (não escrito à mão), FastAPI+Uvicorn como framework
      HTTP (decisão registrada em `docs/CONVENTIONS.md`), i18n (`locales/{pt-BR,en-US,es}.json`
      + loader com fallback), `n8n/telegram-bot.json` (Telegram Trigger + normalização, parando
      antes do `HTTP Request` — isso é `feat-002`). 3 subtasks (SV-182..184, story SV-181), 4 PRs
      com CI real e verde (incluindo SonarCloud no PR de story). Ver
      `services/telegram-integration/progress.md` para o detalhe completo (achados reais: 2
      armadilhas de sequenciamento de CI, 1 achado de documentação, 1 achado do Delivery Review,
      1 achado real do SonarCloud).
- [x] **Impedimento de ambiente resolvido**: `uv` não estava instalado nesta máquina — corrigido
      via `pip install --user uv` + cópia do executável para `~/.local/bin` (mesmo mecanismo do
      gotcha anterior do `claude.exe`), PATH persistido via PowerShell para sessões futuras.
- [x] (continuação, mesmo dia) `api-gateway feat-005` fechou `epic-008` — ver entrada anterior
      deste log/`progress.md`.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, `epic-005` `in-progress`). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| `bets-service` não consome `X-Correlation-Id` real ainda | Sinalizado em `docs/services/bets-service.md`, não é blocker de nada. |
| `n8n/telegram-bot.json` não testado contra instância real | Risco residual aceito, documentado em `services/telegram-integration/n8n/README.md`. Validar antes de considerar o fluxo pronto pra produção. |
| `web` sem código de aplicação | Só o commit de bootstrap do `epic-009`. Elegível, não iniciado. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`telegram-integration feat-002`** (Parsing de mensagens não estruturadas) é a próxima
   natural — única feature elegível de `epic-005` agora (`feat-003`/`feat-004` dependem dela).
   É o que de fato liga o nó `HTTP Request` no workflow n8n ao endpoint Python.
3. Alternativa em paralelo (sessão/serviço diferente): **`epic-006` (`web`, Angular)** — todas
   as dependências satisfeitas, ainda não iniciado. WIP máximo 1 por lane de serviço continua
   valendo — não trabalhar em `telegram-integration` e `web` na mesma sessão.
4. `epic-007` (resiliência DLQ/retry) continua **não elegível** até `epic-005` fechar por
   completo (depende de `epic-004` + `epic-005`, não apenas `epic-005` `in-progress`).
