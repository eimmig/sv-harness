# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-08

## Objetivo atual

- `epic-002` (auth-service), `epic-003` (bets-service), `epic-004` (stats-service) e `epic-008`
  (api-gateway) — todos `done`.
- Situação: 6 de 9 epics `done` (`epic-001` infra, `epic-009` bootstrap+SonarCloud, `epic-002`
  auth-service, `epic-003` bets-service, `epic-004` stats-service, `epic-008` api-gateway).
  Nenhum epic `in-progress` no momento — `epic-005` (telegram-integration) e `epic-006` (web)
  ambos ficaram elegíveis agora que `epic-008` fechou.

## Concluído nesta sessão (2026-09-08)

- [x] **`api-gateway feat-005` (fechamento formal do pipeline de CI) implementado e mergeado em
      `develop`** — feature de fechamento sem código/workflow novo, mesmo padrão de
      `auth-service feat-007`/`stats-service feat-007`: `description` corrigida de "5 passos com
      atalho `mvn sonar:sonar`" pra "6 passos reais" (changelog, i18n, build, testes+cobertura,
      SonarCloud com coordenadas completas, gate de zero issue) — o pipeline já rodava assim de
      verdade desde `feat-001.1` e já tinha passado verde, com SonarCloud, em todas as 8 PRs desta
      sessão (SV-148 até SV-178). 1 subtask (SV-180, story SV-179).
- [x] **`epic-008` (api-gateway) fechado** — todas as 6 features (`feat-001..006`) `done`.
      `feature_list.json` da raiz atualizado (evidência completa, `harness` → `status: done`).
- [x] (continuação de sessão anterior, mesmo dia) `api-gateway feat-006` — filtro global
      `X-Correlation-Id`, ver entrada anterior deste log/`progress.md` para o detalhe.

## Bloqueios / Riscos

| Item | Estado |
|---|---|
| DLQ local usa `at-most-once` | Aberto **por desenho**. Só reavaliável quando `infra/feat-002` rodar, que depende de `epic-004`/`epic-005` (`epic-004` já `done`, `epic-005` agora elegível). Ver `docs/DECISIONS-LOG.md` (2026-08-03). |
| Topologia RabbitMQ é contrato | `bets-service` e `stats-service` publicam/consomem **sem redeclarar** exchange ou fila. Ver `docs/API-CONTRACTS.md`. |
| `bets-service` não consome `X-Correlation-Id` real ainda | `BetEventEnvelope` não tem campo `correlationId` apesar do header agora existir de verdade (`api-gateway feat-006`). Sinalizado em `docs/services/bets-service.md`, não é blocker de nada — fica pra uma sessão futura de `bets-service` decidir se/quando fechar. |
| 2 repositórios ainda sem código de aplicação | `telegram-integration`, `web` — só o commit de bootstrap do `epic-009`. Ambos elegíveis agora. |

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **`epic-005` (`telegram-integration`)** e **`epic-006` (`web`)** são os dois epics elegíveis
   agora — dependências (`epic-002`/`epic-003`/`epic-004`/`epic-008`) todas `done`. Diferentes
   serviços, podem avançar em paralelo (WIP máximo 1 por lane de serviço, não globalmente) — mas
   numa sessão só, escolher um. `epic-005` é o mais natural de priorizar: também libera `epic-007`
   (resiliência DLQ/retry, que depende de `epic-004` + `epic-005`).
3. `telegram-integration` é Python (primeiro serviço não-Java do backlog) — ler
   `services/telegram-integration/CLAUDE.md` com atenção especial antes de começar (convenções
   `uv`/`ruff`/`mypy`, formato de i18n JSON já decidido em `docs/DECISIONS-LOG.md`, `python3` vs
   `python` no PATH desta máquina — ver `docs/DECISIONS-LOG.md` 2026-08-02).
4. `epic-007` (resiliência DLQ/retry) continua **não elegível** até `epic-005` fechar também
   (depende de `epic-004` + `epic-005`).
