---
tags: [service, backend, infra]
---

# api-gateway

Java 25 + Spring Boot 4.x + **Spring Cloud Gateway Server WebMVC** (bloqueante/servlet, não o
Gateway reativo/WebFlux — decisão de 2026-09-07, ver [[DECISIONS-LOG]], para não introduzir o
único serviço assíncrono do projeto). Ver [[ARCHITECTURE]] para o panorama geral e
[[API-CONTRACTS]] para o modelo de confiança que este serviço implementa. Harness de código em
`services/api-gateway/CLAUDE.md`.

> Nomenclatura nos diagramas originais do TCC1 (`docs/diagrams/architecture/`, ver
> [[ARCHITECTURE]] seção "Diagramas estrutural e de implantação"): o diagrama de implantação
> (`deployment-diagram.png`) mostra dois componentes distintos — um
> `Container: API Gateway (HTTP/REST)`, que é este serviço, e uma `Abstração: Load Balancer
> (Kubernetes Ingress/Service)` na frente dele, um nível de infraestrutura mais baixo (fora de
> escopo do `docker-compose.yml` de desenvolvimento). O diagrama estrutural
> (`structural-diagram.png`) rotula só "Load Balancer" — mesma ideia, nomenclatura menos precisa
> nesse diagrama específico.

## Por que existe

Único ponto de entrada HTTP público da plataforma. [[API-CONTRACTS]] decide que `bets-service` e
`stats-service` confiam cegamente nos headers `X-User-Id`/`X-Tenant-Id` e não revalidam o token
PASETO — este serviço é quem valida o token de fato e injeta esses headers, e é o único
componente que pode. Sem ele, o modelo de confiança descrito na documentação não tem
implementação real. Diferente dos outros serviços Java, não tem RF próprio no TCC 1 nem modelo
de domínio — é infraestrutura de aplicação, sem banco de dados (stateless).

## Responsabilidades

1. **Validação de token PASETO**: toda rota autenticada exige um token PASETO válido (emitido
   por [[auth-service]]), enviado no header `Authorization: Bearer <token>` (ver
   [[API-CONTRACTS]] seção "Confiança entre serviços"). Token ausente/inválido/expirado → `401`,
   `application/problem+json` (`title`/`detail` localizados por `Accept-Language`, ver
   [[API-CONTRACTS]] seção "Internacionalização (i18n)"). **Exceção: `POST /api/v1/auth/login` é
   pública** (achado real de `feat-003`, corrigido antes de existir tráfego real) - exigir token
   para emitir o próprio token impediria qualquer login. Único caminho isento além de
   `/actuator/**`.
2. **Injeção de `X-User-Id`/`X-Tenant-Id`**: após validar o token, injeta o `userId` e o
   `tenantId` (slug do tenant) extraídos dele como headers `X-User-Id`/`X-Tenant-Id` antes de
   rotear. Nunca aceita esses headers vindo do cliente — sempre derivados aqui. **Os dois
   deixaram de ser o mesmo valor em 2026-08-02** (ver [[DECISIONS-LOG]] "Modelo de tenant
   multiusuário") — um usuário não é mais sinônimo de um tenant.
3. **Roteamento**:

   | Prefixo | Destino |
   |---|---|
   | `/api/v1/users/**`, `/api/v1/auth/**`, `/api/v1/telegram-links/**` | [[auth-service]] |
   | `/api/v1/betting-houses/**`, `/api/v1/bets/**`, `/api/v1/transactions/**`, `/api/v1/sports/**`, `/api/v1/leagues/**`, `/api/v1/markets/**`, `/api/v1/tipsters/**` | [[bets-service]] |
   | `/api/v1/statistics/**` | [[stats-service]] |

   `/api/v1/telegram-links/**` acrescentada em `feat-003` (achado real): endpoint já existia em
   `auth-service` (`feat-006`, gera código de vínculo para usuário logado) mas não estava coberto
   por nenhum prefixo desta tabela. **`/api/v1/telegram-accounts/**` nunca ganhou rota aqui**
   (correção 2026-09-08 — esta nota antes previa que `feat-004` a introduziria; achado real do
   `telegram-integration feat-003`: essa chamada é estruturalmente circular para o Gateway, ver
   [[DECISIONS-LOG]] "Confirmação de vínculo Telegram bypassa o api-gateway" — `telegram-integration`
   chama `auth-service` direto). `/api/v1/sports/**`, `/api/v1/leagues/**`, `/api/v1/markets/**`
   acrescentadas em `feat-007` (achado real do Plan Review de `telegram-integration feat-004`):
   os 3 catálogos existiam em [[bets-service]] desde a `feat-002` daquele serviço mas nunca
   tinham rota aqui — `feat-007` deixou `/api/v1/tipsters/**` de fora **de propósito**, porque
   `tipsterId` era opcional em `POST /api/v1/bets` e nenhum consumidor o preenchia ainda.
   **`/api/v1/tipsters/**` acrescentada em `feat-008` (2026-09-09, achado real de `infra/feat-002`,
   teste de resiliência do `epic-007`)**: a decisão de `feat-007` ficou obsoleta sem que nenhuma
   sessão a revisitasse quando `apps/web feat-008` (catálogos) ganhou a aba de tipsters — o
   consumidor que faltava em `feat-007` passou a existir, mas a rota nunca foi atualizada. Só veio
   à tona porque `infra/feat-002` precisou provisionar um tipster de verdade via Gateway para
   registrar uma aposta de teste; `apps/web feat-008` não tem nenhum teste de integração contra
   um Gateway real, só contra `HttpClient` mockado, então não pegou a rota ausente.

4. **Credencial de serviço para [[telegram-integration]]**: o bot não tem um usuário logado com
   token PASETO — só sabe o `telegramUserId` de quem mandou a mensagem. Para esse caminho:
   - `telegram-integration` chama o Gateway com um header `X-Service-Key` (segredo estático por
     ambiente, ver [[OBSERVABILITY-AND-CONFIG]]) em vez de um token PASETO, e informa **qual**
     usuário do Telegram fez a chamada via `X-Telegram-User-Id` (decisão de 2026-09-07, ver
     [[DECISIONS-LOG]] — header dedicado, o corpo da requisição continua idêntico ao do
     formulário web).
   - O Gateway valida a `X-Service-Key` e, se válida, chama internamente
     `GET /api/v1/telegram-accounts/{telegramUserId}` em [[auth-service]] (usando o valor de
     `X-Telegram-User-Id`) para resolver o
     `userId`/`tenantId` vinculados (ver [[auth-service]] seção "Vínculo de conta Telegram").
     > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): `auth-service` resolve esse
     > lookup consultando um diretório `TELEGRAM_LINK` no schema `public` (fora de qualquer
     > schema de tenant) — não precisa mais assumir um `USER` global nem varrer schemas.
   - Se não houver vínculo, o Gateway responde `401`/`404` (RFC 7807) — `telegram-integration`
     deve tratar isso como "usuário precisa vincular a conta antes de registrar apostas pelo
     bot" e informar o usuário via mensagem no Telegram, não tentar adivinhar o tenant.
   - Se houver vínculo, injeta `X-User-Id`/`X-Tenant-Id` resolvidos e roteia normalmente para
     `POST /api/v1/bets` em [[bets-service]] — o mesmo endpoint usado pelo formulário web.

5. **Filtro global de `X-Correlation-Id`** (`feat-006`, implementado em 2026-09-08):
   `CorrelationIdFilter` gera o header (`UUID.randomUUID()`) se a requisição chegar sem ele
   (ausente ou em branco), propaga se já existir, injeta no MDC (`correlationId`, mesma
   convenção camelCase de `TenantSchemaFilter` em `bets-service`) e repassa no request roteado
   para `auth-service`/`bets-service`/`stats-service` via `CorrelationIdRequestWrapper` (ver
   [[OBSERVABILITY-AND-CONFIG]]). Roda para **toda** rota — `@Order(Ordered.HIGHEST_PRECEDENCE)`,
   sem `shouldNotFilter`, inclusive `/actuator/**` — independente de validação PASETO (item 1) ou
   credencial de serviço (item 4); a composição dos dois wrappers (`ResolvedIdentityRequestWrapper`
   + `CorrelationIdRequestWrapper`) foi provada ponta a ponta nos dois caminhos de autenticação.
   Também ecoa o header na response (decisão além do contrato original, para o chamador
   correlacionar do lado dele). **Ainda não fecha o ciclo**: `bets-service` não lê esse header
   real no `BetEventEnvelope` — ver [[bets-service]] seção "Correlation id no envelope de evento
   (gap conhecido)".

6. **Filtro global de CORS** (`feat-012`, achado real de 2026-09-11 — nenhuma nota do vault
   cobria CORS antes, gap real desde que [[web]] existe, não só do ambiente local): `CorsConfig`
   registra um `CorsFilter` (biblioteca do Spring) para **toda** rota, origem(ns) configurável(is)
   via `CORS_ALLOWED_ORIGINS` (default `http://localhost:4200`, ver
   [[OBSERVABILITY-AND-CONFIG]]), sem `allowCredentials` (token vai em `Authorization`, nunca
   cookie — ver [[API-CONTRACTS]] seção "CORS"). Precisa rodar **antes** de `PasetoAuthenticationFilter`/
   `ServiceKeyAuthenticationFilter` (item 1/4) — o preflight `OPTIONS` do navegador não carrega
   `Authorization`/`X-Service-Key`, então se qualquer um dos dois rodar primeiro rejeita o
   preflight com `401` antes do `CorsFilter` responder. **Gotcha real**: `@Order` direto no método
   `@Bean` que retorna o `CorsFilter` **não** é suficiente para isso — só funciona registrando via
   `FilterRegistrationBean<CorsFilter>` com `.setOrder(...)` explícito (ver [[CONVENTIONS]] seção
   "Java" para o detalhe, evitar redescobrir em outro serviço que precise ordenar um `Filter` de
   biblioteca).

## O que este serviço não faz

- **Não roteia a criação de tenant**: o operador da plataforma chama a rota administrativa de
  cada serviço (`auth-service`, `bets-service`, `stats-service`) diretamente, autenticado por
  `X-Admin-Api-Key` — 3 chamadas manuais separadas, fora da tabela de roteamento acima. Ver
  [[API-CONTRACTS]] e [[DECISIONS-LOG]] item 3.
- Não implementa regra de negócio de nenhum outro serviço (RN01–RN09 continuam em
  `bets-service`/`stats-service`).
- Não persiste dados — sem banco próprio, sem exceção à regra Database per Service (ele
  simplesmente não tem estado para guardar).
- Não emite nem gera tokens PASETO — isso é exclusivo de [[auth-service]]; o Gateway só valida.

## Ver também

- [[auth-service]] — emite os tokens PASETO validados aqui e expõe o lookup de conta Telegram.
- [[bets-service]], [[stats-service]] — destino do roteamento, confiam em
  `X-User-Id`/`X-Tenant-Id`.
- [[telegram-integration]] — único consumidor do caminho de credencial de serviço.
- [[API-CONTRACTS]] — modelo de confiança completo entre serviços.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (2026-08-02).
