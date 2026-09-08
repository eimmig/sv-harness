---
tags: [conventions, observability, config]
---

# Observabilidade e configuração

Convenções operacionais que evitam cada serviço logar/configurar de um jeito diferente. Ver
[[CONVENTIONS]] e [[API-CONTRACTS]].

## Logs

- **Logs estruturados em JSON** (não texto livre) nos três serviços Java — facilita correlação
  entre serviços e é pré-requisito para qualquer ferramenta de agregação de log no futuro.
- **Correlation ID**: todo request HTTP que entra pelo API Gateway recebe (ou propaga, se já
  existir) um header `X-Correlation-Id`. Esse id:
  - é repassado em qualquer chamada HTTP entre serviços (ex.: `telegram-integration` →
    `bets-service`);
  - vai como propriedade no **envelope do evento** RabbitMQ (`correlationId`, adicional ao
    `eventId` — ver [[API-CONTRACTS]]) para que `stats-service` consiga correlacionar o
    processamento assíncrono de volta à requisição original;
  - aparece em toda linha de log relevante (MDC no Java / equivalente no Python).
- Sem isso, depurar "por que essa aposta enviada pelo Telegram não apareceu no dashboard" exige
  procurar manualmente em três serviços sem nenhum fio condutor.
- **`X-Tenant-Id` também vai para o MDC/log estruturado** (adicional ao `X-Correlation-Id`,
  decisão de 2026-08-02 — ver [[DECISIONS-LOG]]): com schema-per-tenant em `auth-service`,
  `bets-service` e `stats-service`, incidentes tendem a ser específicos de uma organização (ex.:
  "schema do tenant X não migrou", "queries lentas só para o tenant Y"). Sem `tenantId` em toda
  linha de log, essa investigação exigiria correlacionar manualmente pelo `X-User-Id` de cada
  requisição isolada. Mesmo mecanismo de propagação do correlation id (MDC no Java, injetado
  pelo mesmo filtro que resolve o schema da conexão).

## Health checks

- Serviços Java: Spring Boot Actuator, `/actuator/health` (liveness) e `/actuator/health/readiness`
  (readiness — inclui checagem de conexão com Postgres/RabbitMQ/Redis conforme o serviço).
- `telegram-integration`: endpoint simples `GET /health` (FastAPI, ver
  [[telegram-integration]]) retornando 200 se o processo está de pé. **Correção de 2026-09-08**:
  esta nota chegou a dizer que o endpoint verificava conectividade com "RabbitMQ/n8n configurados"
  — nenhuma outra nota sustenta este serviço falando com RabbitMQ diretamente (ele nunca publica
  nem consome evento; só `bets-service`/`stats-service` fazem isso) nem com n8n (é n8n quem chama
  este serviço, não o contrário) — era erro de cópia, achado ao planejar `feat-001`. Se o design
  evoluir para checar alguma dependência real (ex.: alcançar `api-gateway`), atualizar aqui.
- `infra/docker-compose.yml` deve usar esses endpoints em `healthcheck:` para que serviços
  dependentes (ex.: `stats-service` esperando o RabbitMQ) só subam depois que a dependência
  estiver de fato pronta, não apenas com a porta aberta.

## Portas HTTP

Decisão de 2026-09-07 (ver [[DECISIONS-LOG]] "Porta HTTP fixa por serviço Java + URL de
roteamento configurável no Gateway"), fechada ao planejar `api-gateway feat-003`: nenhum dos
quatro serviços Java tinha porta HTTP explícita antes disso (todos no default `8080` do Spring
Boot, colidindo em desenvolvimento local — nenhum ainda é containerizado, `infra/docker-compose.yml`
só cobre Postgres/RabbitMQ/Redis). Alocação fixa via `server.port` no `application.yml` de cada
serviço:

| Serviço | Porta |
|---|---|
| `api-gateway` | `8080` (default — único ponto de entrada público) |
| `auth-service` | `8081` |
| `bets-service` | `8082` |
| `stats-service` | `8083` |

`api-gateway` resolve a URL de cada destino por variável de ambiente (`AUTH_SERVICE_URL`,
`BETS_SERVICE_URL`, `STATS_SERVICE_URL`, ver `.env.example` daquele serviço), default
`http://localhost:808x` correspondente — nunca hardcoded, para sobreviver à containerização
futura dos quatro serviços sem mudar o mecanismo (só o default deixa de ser `localhost`).

## Configuração e segredos

- Cada serviço tem um `.env.example` versionado (nunca `.env` real) listando as variáveis
  necessárias (credenciais de banco, RabbitMQ, Redis, chave PASETO, token do bot Telegram,
  `X-Service-Key` compartilhada entre `api-gateway` e `telegram-integration`, `X-Admin-Api-Key`
  de uso exclusivo do operador da plataforma para criar tenants em `auth-service`/`bets-service`/
  `stats-service` (decisão de 2026-08-02, ver [[DECISIONS-LOG]] item 3) — ver [[API-CONTRACTS]]
  seção "Confiança entre serviços"). `.env` real fica em `.gitignore` desde o `feat-001` de cada
  serviço. Em `auth-service`, a env var é `ADMIN_API_KEY` (`feat-003`), lida em
  `application.yml` como `admin.api-key` — perfil `test` usa um valor fixo, nunca `${ADMIN_API_KEY}`
  sem default.
- Serviços Java: `application.yml` com profiles `dev`/`test`/`prod` — `dev` lê de `.env`
  (via `spring-dotenv` ou variáveis de ambiente do `docker-compose.yml`), `test` usa valores
  fixos consumidos pelos containers do Testcontainers (ver [[TESTING]]), nunca aponta para
  infraestrutura real.
- **Nunca** commitar segredo real (chave PASETO, token do bot, senha de banco) em nenhum
  arquivo versionado — inclusive em exemplos de request/response na documentação.
- Chave PASETO: gerada uma vez por ambiente (dev/test/prod), armazenada como variável de
  ambiente, nunca hardcoded no código-fonte de `auth-service` nem de nenhum outro serviço.
  > **Contrato implementado em `feat-005`**: env var `PASETO_LOCAL_KEY` (32 bytes em hex, 64
  > chars, `openssl rand -hex 32`), lida em `application.yml` de `auth-service` como
  > `paseto.local-key` — v4.**local** (simétrica), não v4.public. **É a MESMA chave** que
  > `services/api-gateway` vai precisar quando `epic-008` existir (quem valida o token) — não
  > gerar uma independente lá, ou os tokens emitidos por `auth-service` ficam indecifráveis.
  > Perfil `test` de `auth-service` usa um valor hex fixo de 64 chars, mesmo padrão de
  > `ADMIN_API_KEY`.

### Configuração de `apps/web` (frontend)

`apps/web` é uma SPA estática (sem processo Node em produção lendo `.env`) — o mecanismo acima
não se aplica diretamente. Decisão de 2026-08-02: **`environment.ts` (build-time)**, padrão do
Angular CLI — `src/environments/environment.ts` (dev) e `environment.prod.ts` (prod), cada um
com a URL base do `api-gateway` daquele ambiente, trocado no build via `fileReplacements` do
`angular.json`. Um bundle por ambiente (não "build once, deploy many") — trade-off aceito pela
simplicidade; se isso mudar para config runtime (`config.json` buscado no boot), esta nota e
`apps/web/CLAUDE.md` precisam ser atualizados juntos. Nenhum segredo real vive em
`environment.ts` (só a URL do Gateway, que é pública) — segue a mesma regra de nunca commitar
segredo, mas por um motivo diferente: não há segredo de frontend, o token PASETO do usuário
fica em runtime (storage do navegador), nunca em arquivo versionado.
