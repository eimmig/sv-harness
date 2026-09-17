---
tags: [service, backend]
---

# auth-service

Java 25 + Spring Boot 4.x. Ver [[ARCHITECTURE]] para o panorama geral e [[REQUIREMENTS]] para
RF01/RF02 completos. Harness de código em `services/auth-service/CLAUDE.md`.

## Responsabilidade

- RF01 — manter usuário (cadastro, dados básicos: nome, e-mail, senha). **Reinterpretado em
  2026-08-02** (ver [[DECISIONS-LOG]]): usuário agora existe dentro de um **tenant**
  (organização com múltiplos usuários independentes), não como conta isolada 1:1.
- RF02 — autenticar usuários e controlar sessão. Login exige identificador do tenant além de
  e-mail/senha (ver seção "Modelo de tenant" abaixo).

## Autenticação

Token **PASETO** (Platform-Agnostic Security Tokens) — não JWT. O API Gateway valida o token
antes de rotear para os demais serviços. O token carrega claims de `userId` **e** `tenantId`
(slug do tenant, resolvido no login) — é a partir desses claims que o Gateway injeta
`X-User-Id`/`X-Tenant-Id` (ver [[API-CONTRACTS]]).

> **Contrato implementado em `feat-005`** (`POST /api/v1/auth/login`, biblioteca
> `io.github.nbaars:paseto4j-version4:2024.3` — v4.**local** simétrico, não v4.public/assinado,
> chave `PASETO_LOCAL_KEY` compartilhada com `api-gateway` quando `epic-008` existir, ver
> [[OBSERVABILITY-AND-CONFIG]]): body `{"slug": "acme", "email": "admin@acme", "password":
> "..."}` → `200` `{"token": "v4.local...", "mustChangePassword": true|false, "userId": "uuid",
> "role": "ADMIN"|"MEMBER"}`. `slug` vem do **corpo**, não do header `X-Tenant-Id` — o chamador
> ainda não está autenticado, não há tenant resolvido antes do login. Token carrega
> `userId`/`tenantId`/`iat`/`exp` (TTL 8h, sem token de refresh no backlog atual — sessão de
> duração única, revisitável se/quando refresh for pedido).
> **`userId`/`role` no corpo, contrato implementado em `feat-010`** (2026-09-09, gap encontrado
> ao planejar `apps/web feat-002` — mesmo precedente do gap de `feat-009`): o token é v4.**local**
> (criptografado simetricamente, chave só no backend), então o frontend não tem como decodificar
> claims no cliente. `tenantId` já é conhecido pelo cliente (o próprio slug digitado no login),
> mas `userId`/`role` não têm outra fonte — sem eles a UI não sabe se deve mostrar a tela de
> gestão de usuários do tenant (exclusiva de `role = admin`, ver [[web]] seção "Modelo de tenant
> (UI)") nem tem um id estável do usuário logado.
> `401` **genérico** (`invalid-credentials`, mesma mensagem sempre) para slug malformado, tenant
> inexistente, e-mail inexistente ou senha errada — nunca diferencia o motivo, evita enumeração
> de tenant/usuário; os dois primeiros casos ainda executam um hash BCrypt descartado antes de
> rejeitar, para manter o tempo de resposta equivalente ao de uma comparação de senha real.
> `mustChangePassword = true` (do admin criado em `feat-003`) **não bloqueia** o login — devolvido
> no corpo para o frontend decidir a UX; não há endpoint de troca de senha no backlog ainda,
> bloquear travaria o admin sem via de escape (decisão do usuário, 2026-09-04).

## Modelo de tenant (organização multiusuário)

Decisão de 2026-08-02 — ver [[DECISIONS-LOG]] "Modelo de tenant multiusuário e provisionamento
de banco" para o racional completo. Resumo:

- Um **tenant** é uma organização; pode ter vários usuários (`USER.role`), não é sinônimo de um
  único usuário.
- **Criação de tenant**: rota administrativa, chamável **somente pelo operador da plataforma**
  (sem autocadastro público de organização). Cria o schema `tenant_<slug>` neste serviço e o
  primeiro usuário, `admin@<slug>` (`role = admin`), com senha **aleatória** e
  `mustChangePassword = true`.
  > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] "Modelo de tenant multiusuário", item 3):
  > autenticação via header `X-Admin-Api-Key` (segredo estático dedicado ao operador, ver
  > [[API-CONTRACTS]]). Orquestração: **3 chamadas manuais separadas** do operador — este
  > serviço primeiro, depois `bets-service`, depois `stats-service` — nenhum serviço chama os
  > outros dois em código. Senha padrão previsível sinalizada por `mustChangePassword`.
  > **Resolvido em `feat-005` (2026-09-04, decisão do usuário — não a intenção original desta
  > entrada, que previa bloqueio de verdade)**: o login **não bloqueia** um admin com
  > `mustChangePassword = true` — o valor só é devolvido no corpo da resposta para o frontend
  > decidir a UX. Não há endpoint de troca de senha no backlog ainda; bloquear login deixaria
  > esse admin trancado para sempre, sem via de escape. Ver seção "Autenticação" acima para o
  > contrato completo.
  > **Contrato implementado em `feat-003`** (`POST /api/v1/admin/tenants`, header
  > `X-Admin-Api-Key` obrigatório, checado por `AdminApiKeyFilter` antes do `DispatcherServlet`):
  > body `{"slug": "acme", "tenantName": "Acme Corp"}` (`tenantName` opcional, default
  > `"Administrator"`) → `201` `{"userId": "...", "email": "admin@acme", "temporaryPassword":
  > "...", "downstreamProvisioningFailures": []}` — a senha só aparece nesta resposta, nunca mais
  > recuperável. `409` se o slug já estiver provisionado (`gateway.exists()` checado **antes** de
  > qualquer escrita — idempotência do `CREATE SCHEMA IF NOT EXISTS` faria uma segunda chamada
  > reprovisionar em silêncio sem essa checagem); `422` para slug em formato inválido (validação
  > de domínio, não Bean Validation — ver [[API-CONTRACTS]] seção "Formato de erro" para o corte
  > 400/422); `401` sem tocar o banco se `X-Admin-Api-Key` ausente/incorreto.
  > **`downstreamProvisioningFailures` acrescentado em `feat-015` (2026-09-11, reverte a decisão
  > de "3 chamadas manuais" - ver [[DECISIONS-LOG]] item 3)**: depois de criar schema+admin
  > localmente, este serviço chama a mesma rota `POST /api/v1/admin/tenants` em `bets-service`
  > (primeiro) e `stats-service` (depois) via `RestClientDownstreamTenantProvisioner`
  > (`RestClient` com timeout de conexão 2s/leitura 5s, mesmo padrão de
  > `ServiceKeyAuthenticationFilter` em `api-gateway`), com o mesmo `X-Admin-Api-Key` já
  > configurado neste serviço (reaproveitado, não é um segredo novo). `409` de qualquer downstream
  > é tratado como sucesso (idempotente); qualquer outra falha (rede, 4xx/5xx inesperado) entra no
  > array, sem bloquear a chamada seguinte nem reverter o que já foi criado localmente - a
  > resposta é sempre `201` se a parte deste serviço funcionou. Config nova:
  > `BETS_SERVICE_URL`/`STATS_SERVICE_URL` (env vars, mesmo nome já usado por `api-gateway` pras
  > mesmas URLs).
- **Criação de usuário dentro de um tenant**: só o usuário `role = admin` daquele tenant pode
  criar outros usuários (`role = member`). Precisa de checagem de autorização por role no
  endpoint correspondente — não é feature transparente pelo simples fato de existir a coluna
  `role`.
  > **Contrato implementado em `feat-004`** (`POST /api/v1/users`, requer `X-Tenant-Id` — já
  > resolvido pelo `TenantSchemaFilter` de `feat-001.3` — e `X-User-Id`, o id do usuário
  > chamador): body `{"name": "...", "email": "...", "password": "..."}` → `201`
  > `{"id": "...", "name": "...", "email": "...", "role": "MEMBER", "mustChangePassword": false,
  > "createdAt": "..."}` — nunca `passwordHash` nem a senha em texto puro (diferente da resposta
  > de `feat-003`, aqui quem escolhe a senha é o próprio requester). `role` é sempre `MEMBER`;
  > este endpoint não cria outro `admin`. `401` se `X-User-Id` estiver ausente ou não for um
  > UUID válido (mesma família de status que `X-Admin-Api-Key` ausente/inválido em `feat-003` —
  > é identidade do chamador, não um campo de payload). `400` se `X-Tenant-Id` estiver ausente
  > (ainda não existe `api-gateway`/`epic-008` para injetar os dois headers de verdade — por ora
  > quem chama informa direto, mesmo modelo de confiança que `bets-service`/`stats-service` vão
  > usar, ver [[API-CONTRACTS]]) ou se o payload falhar Bean Validation (`name`/`email`/`password`
  > em branco, `email` com formato inválido). `403` se o chamador não existir no tenant resolvido
  > ou não for `admin` (os dois casos retornam o mesmo erro, para não vazar enumeração de
  > usuário). `409` se o e-mail já estiver cadastrado nesse tenant.
  > **Contrato implementado em `feat-009`** (`GET /api/v1/users`, motivado por um gap real
  > encontrado ao planejar `apps/web feat-002` — a tela de gestão de usuários do tenant precisa
  > de listagem, que não existia até aqui): mesmos headers `X-User-Id`/`X-Tenant-Id` e mesma
  > checagem de `role = admin` de `feat-004` (401/400/403 idênticos), sem payload de entrada.
  > `200` com array `[{"id": "...", "name": "...", "email": "...", "role": "ADMIN"|"MEMBER",
  > "mustChangePassword": true|false, "createdAt": "..."}]` ordenado por `name` ascendente
  > (nenhum requisito fixava ordenação; escolhido por usabilidade de tela de admin), incluindo o
  > próprio chamador. Sem paginação (lista de tenant provisionado manualmente é pequena por
  > natureza) e sem filtro/busca no backlog atual. DTO de resposta é `UserSummaryResponse`, novo e
  > distinto de `CreateUserResponse` (mesmos 5 campos, nunca `passwordHash`) — mantém a convenção
  > de 1 DTO por operação já usada pelos demais endpoints deste serviço.
  > **Contrato implementado em `feat-017`** (`PATCH /api/v1/users/{id}`, fecha o gap de "só
  > create/list, sem update" no CRUD de usuários do tenant): mesmos headers/checagem de
  > `role = admin` de `feat-004`/`feat-009` (401/400/403 idênticos). Body `{"name": "...", "role":
  > "ADMIN"|"MEMBER"}` → `200` com `UpdateUserResponse` (mesmos 5 campos, DTO dedicado, nunca
  > `passwordHash`). Só `name`/`role` são editáveis — `email` fica de fora (é a chave de
  > unicidade/identidade dentro do tenant) e senha/`mustChangePassword` continuam fora do backlog
  > (troca de senha nunca teve endpoint, decisão já registrada em `feat-005`). `404` se o `{id}`
  > não existir no tenant resolvido (isolamento cross-tenant automático via
  > `search_path`/multi-tenancy do Hibernate, mesmo mecanismo que já isola `findById`). `409` se a
  > operação rebaixaria o único `admin` restante do tenant para `member` — sem rota de
  > autocadastro nem de promoção `member`→`admin` no backlog, esse caminho deixaria o tenant sem
  > nenhum admin e sem forma de se recuperar via API (achado do `Plan Reviewer`, ver
  > `feature_list.json` de `auth-service`).
  > **Contrato implementado em `feat-018`** (`POST /api/v1/auth/change-password`, fecha o gap
  > registrado em `feat-005`/`feat-017`: nunca existiu endpoint para trocar a própria senha).
  > Requer `X-User-Id`/`X-Tenant-Id` (usuário já autenticado — não está na lista de exceção do
  > `PasetoAuthenticationFilter`, que só isenta `POST /api/v1/auth/login`). Body
  > `{"currentPassword": "...", "newPassword": "..."}` → `204` sem corpo (token não é reemitido —
  > as claims do PASETO não carregam `mustChangePassword`, então o token atual continua válido).
  > Valida `currentPassword` contra o hash atual antes de trocar; erro `401` **genérico**
  > (`current-password-mismatch`, exceção dedicada — não reaproveita `invalid-credentials` do
  > login, cujo texto localizado menciona tenant/e-mail e seria enganoso aqui) sem diferenciar de
  > "usuário não encontrado" (`caller-not-found`, reaproveitado de `feat-006`). Zera
  > `mustChangePassword` ao trocar com sucesso. **Decisão do usuário nesta sessão**: a troca em si
  > não passou a bloquear outras rotas enquanto `mustChangePassword = true` — mitigação por senha
  > aleatória de alta entropia (nunca logada) continua sendo considerada suficiente; ver
  > [[DECISIONS-LOG]]. Fluxo "esqueci minha senha" (sem sessão ativa) fica fora de escopo.
  > **Achado real durante a implementação**: `UserRepository.update()` (adicionado em `feat-017`
  > só para `name`/`role`) tinha `UserJpaEntity.applyUpdate(name, role)` que silenciosamente
  > ignorava `passwordHash`/`mustChangePassword` — trocar a senha "funcionava" (204, sem erro) mas
  > não persistia nada. Corrigido alargando `applyUpdate` para os 4 campos mutáveis do agregado
  > `User` (`name`, `role`, `passwordHash`, `mustChangePassword`), já que o contrato de domínio
  > `UserRepository.update(User): User` sempre recebeu o agregado inteiro — `feat-017` não muda de
  > comportamento (já enviava `passwordHash`/`mustChangePassword` inalterados do alvo). Qualquer
  > serviço Java que reaproveitar esse mecanismo de `findById+applyUpdate+save` (ver
  > [[CONVENTIONS]]) deve conferir se o método `applyUpdate` da entidade cobre **todos** os campos
  > que o `update()` de domínio promete alterar, não só os que a primeira feature que o criou
  > precisava.
- **Login (RF02)**: e-mail é único apenas dentro do schema do tenant, não globalmente — a tela
  de login precisa de um terceiro campo (slug/identificador da organização) para que este
  serviço saiba em qual schema procurar antes de validar a senha.

## Modelo de dados (banco `auth`, isolado — Database per Service, schema-per-tenant)

Ver [[DATA-MODEL]] para o ERD (Mermaid + PNG original do TCC1). ERD original confirmado sem
divergências em 2026-08-01; `role` e o isolamento por schema (`tenant_<slug>`) são extensões de
2026-08-02 sobre esse ERD, ver [[DECISIONS-LOG]].

- `USER`: `id` (uuid, PK), `name`, `email` (UK **dentro do schema do tenant**, não globalmente),
  `passwordHash`, `role` (`admin`/`member`), `mustChangePassword` (boolean, `true` para o admin
  recém-criado por provisionamento de tenant — ver [[DECISIONS-LOG]] item 3), `createdAt`. Sem
  coluna `tenantId` — o schema em que a linha vive já é o tenant.
- `TELEGRAM_ACCOUNT`: `id` (uuid, PK), `userId` (FK → USER, relação 1:1), `telegramUserId`,
  `linkedAt`. Vínculo entre a conta web e a conta do Telegram usada por
  [[telegram-integration]] para identificar quem enviou a mensagem. Vive **dentro do schema do
  tenant**, como qualquer outro dado de negócio.

**Mapeamento JPA/persistência implementado em `feat-002`** (tabelas físicas `users`/
`telegram_accounts`, não `user`/`telegram_account` — ver [[DATA-MODEL]] nota sobre palavra
reservada do Postgres): roteamento por schema via multi-tenancy do Hibernate (mecanismo
reaproveitável pelos outros serviços Java, documentado em [[CONVENTIONS]] seção "Padrões de
código Java"). `UserRepository.save()`/`TelegramAccountRepository.save()` são **só de criação**
por enquanto (`Persistable<UUID>` sempre trata o id como novo) — nenhuma feature do backlog atual
precisa atualizar uma linha já existente; quando `mustChangePassword` precisar ser zerado após
troca de senha (ou qualquer outro update futuro), o mecanismo de `isNew()` precisa ser revisitado
antes de reusar `save()` para isso.

### Diretório global (schema `public`, fora de qualquer tenant)

Duas tabelas pequenas, só para resolver identidade — não são dado de negócio de nenhum tenant
(ver [[DECISIONS-LOG]] item 15):

- `TELEGRAM_LINK`: `telegramUserId` (PK), `tenantId` (slug), `userId` — diretório definitivo
  `telegramUserId -> tenantId`/`userId`, consultado por `GET /api/v1/telegram-accounts/{telegramUserId}`
  (lookup O(1), sem varrer schemas). `tenantId`/`userId` não são FK reais — apontam para uma
  linha que vive num schema de tenant diferente, não no `public`.
- `PENDING_TELEGRAM_LINK`: `code` (PK), `tenantId`, `userId`, `expiresAt` — códigos de vínculo de
  curta duração, gravados aqui **além de** dentro do schema do tenant no momento da geração, para
  que a confirmação (que só recebe `telegramUserId` + código, sem saber o tenant) consiga achar
  o tenant certo.

Como schema-per-tenant aqui vive dentro do **mesmo banco Postgres** (schemas são namespaces do
mesmo banco, não bancos físicos separados), gravar em `public` e num schema de tenant na mesma
operação é uma transação local comum — não um problema de transação distribuída.

## Vínculo de conta Telegram (suporte a RF05)

`auth-service` é dono do vínculo `TELEGRAM_ACCOUNT`, mesmo não sendo o serviço que recebe as
mensagens do bot:

- `POST /api/v1/telegram-links` — usuário logado gera um código de vínculo de curta duração.
  Grava o código em `PENDING_TELEGRAM_LINK` (schema `public`, ver seção "Diretório global"
  acima) — só ali, sem cópia no schema do tenant: a própria linha em `public` já carrega
  `tenantId`/`userId`, suficiente para o passo de confirmação abaixo achar o tenant certo sem o
  bot precisar informar o slug.
- `POST /api/v1/telegram-accounts` — endpoint interno (via [[api-gateway]] quando esse existir;
  hoje sem `api-gateway`, sem header de credencial de serviço — mesmo risco residual aceito em
  `feat-003` para a rota admin, desproporcional de mitigar antes do Gateway existir de fato) que
  confirma o vínculo: `telegramUserId` + código → busca `PENDING_TELEGRAM_LINK` (`404` se
  ausente, `422` se expirado — código expirado é consumido/apagado mesmo assim), e **numa única
  transação** cria `TELEGRAM_ACCOUNT` dentro do schema do tenant resolvido, faz upsert em
  `TELEGRAM_LINK` e apaga o `PENDING_TELEGRAM_LINK` consumido. Se `telegramUserId` já estava
  vinculado a outro tenant/usuário, a nova confirmação **sobrescreve** o vínculo antigo
  (decisão do usuário, `feat-006`; `TELEGRAM_LINK.telegramUserId` já é PK única — só um vínculo
  ativo por vez — a linha de `TELEGRAM_ACCOUNT` do tenant anterior fica órfã, sem endpoint de
  desvínculo ainda). `409` se o usuário chamador ou o `telegramUserId` já tiver um vínculo ativo
  dentro do MESMO tenant (não é o caso de sobrescrita entre tenants acima).
- `GET /api/v1/telegram-accounts/{telegramUserId}` — lookup interno usado pelo [[api-gateway]]
  para resolver `telegramUserId -> userId`/`tenantId` antes de rotear a captura automática de
  aposta para [[bets-service]]. Mesmo estado sem header de credencial de serviço do endpoint
  acima, até o Gateway existir. Retorna `404` se não houver vínculo, para o Gateway rejeitar a
  chamada em vez de adivinhar o tenant.
  > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): o lookup consulta a tabela
  > `TELEGRAM_LINK` no schema `public` (seção "Diretório global" acima) — não busca mais um
  > `USER` numa tabela global, e não precisa varrer schemas de tenant.
  > **Contrato implementado em `feat-006`**: `POST /api/v1/telegram-links` requer `X-User-Id`
  > (`401` se ausente/inválido ou se o usuário não existir no tenant corrente) e `X-Tenant-Id`
  > (já resolvido pelo `TenantSchemaFilter`, mesmo modelo de confiança de `feat-004`) → `201`
  > `{"code": "...", "expiresAt": "..."}` (código de 8 caracteres alfanuméricos maiúsculos sem
  > ambíguos, TTL configurável via `telegram.link-code-ttl-minutes`, default 15 minutos).
  > `TELEGRAM_LINK`/`PENDING_TELEGRAM_LINK` são entidades JPA normais com `@Table(schema =
  > "public")` explícito — não um adapter JDBC separado — convivendo com a multi-tenancy do
  > Hibernate na mesma `EntityManagerFactory` (ver [[CONVENTIONS]] seção "Migrations"); a
  > transação de confirmação abre o `TenantContextScope` do tenant resolvido **antes** de entrar
  > no método `@Transactional` (não durante), porque a sessão Hibernate resolve o schema da
  > conexão uma única vez, na primeira aquisição, não a cada query — abrir o escopo depois não
  > re-roteia a conexão já aberta.

## Ver também

- [[api-gateway]] — valida os tokens PASETO emitidos aqui e consome o lookup de conta Telegram.
- [[bets-service]] — consome `userId`/`tenantId` emitidos aqui para isolar dados por tenant.
- [[telegram-integration]] — inicia o fluxo de confirmação de vínculo a partir do bot.
- [[web]] — telas de login, gestão de usuários do tenant e geração de código de vínculo
  consomem este serviço (sem tela de autocadastro — ver [[DECISIONS-LOG]]).
- [[DECISIONS-LOG]] — racional completo do modelo de tenant multiusuário (itens 1–14) e do
  diretório global que resolve o lookup de Telegram (item 15).
