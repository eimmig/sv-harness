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
  > outros dois em código. Senha padrão previsível mitigada por `mustChangePassword`: o backend
  > bloqueia qualquer ação do admin recém-criado além de trocar a senha, até esse campo virar
  > `false`.
- **Criação de usuário dentro de um tenant**: só o usuário `role = admin` daquele tenant pode
  criar outros usuários (`role = member`). Precisa de checagem de autorização por role no
  endpoint correspondente — não é feature transparente pelo simples fato de existir a coluna
  `role`.
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

- Endpoint autenticado (token PASETO, usuário logado em [[web]]) para gerar um código de
  vínculo de curta duração. Grava o código em `PENDING_TELEGRAM_LINK` (schema `public`, ver
  seção "Diretório global" acima) **além de** no schema do próprio tenant — é o que permite ao
  passo de confirmação abaixo achar o tenant certo sem o bot precisar informar o slug.
- Endpoint interno (via [[api-gateway]], sem exigir token PASETO — é chamado por
  [[telegram-integration]] repassando o código enviado pelo usuário ao bot) para confirmar o
  vínculo: `telegramUserId` + código → busca `PENDING_TELEGRAM_LINK`, e **numa única transação**
  cria/atualiza `TELEGRAM_ACCOUNT` dentro do schema do tenant resolvido e faz upsert em
  `TELEGRAM_LINK`.
- `GET /api/v1/telegram-accounts/{telegramUserId}` — lookup interno usado pelo [[api-gateway]]
  para resolver `telegramUserId -> userId`/`tenantId` antes de rotear a captura automática de
  aposta para [[bets-service]]. Não exige token PASETO (não há usuário logado nesse caminho) —
  só é alcançável pelo Gateway, autenticado por credencial de serviço, nunca exposto
  publicamente. Retorna `404` se não houver vínculo, para o Gateway rejeitar a chamada em vez de
  adivinhar o tenant.
  > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): o lookup consulta a tabela
  > `TELEGRAM_LINK` no schema `public` (seção "Diretório global" acima) — não busca mais um
  > `USER` numa tabela global, e não precisa varrer schemas de tenant.

## Ver também

- [[api-gateway]] — valida os tokens PASETO emitidos aqui e consome o lookup de conta Telegram.
- [[bets-service]] — consome `userId`/`tenantId` emitidos aqui para isolar dados por tenant.
- [[telegram-integration]] — inicia o fluxo de confirmação de vínculo a partir do bot.
- [[web]] — telas de login, gestão de usuários do tenant e geração de código de vínculo
  consomem este serviço (sem tela de autocadastro — ver [[DECISIONS-LOG]]).
- [[DECISIONS-LOG]] — racional completo do modelo de tenant multiusuário (itens 1–14) e do
  diretório global que resolve o lookup de Telegram (item 15).
