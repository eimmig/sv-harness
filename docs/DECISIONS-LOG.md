---
tags: [decisions, architecture]
---

# Log de decisões — divergências em relação ao TCC 1 original

Registro cronológico de decisões tomadas durante o TCC 2 (este repositório) que **mudam ou
estendem** o que foi especificado/modelado no TCC 1 (`TCC_1_Sistema_de_Apostas.pdf`,
`Proposta_TCC_Eduardo_Mateus_Immig.pdf`, diagramas originais em `docs/diagrams/`). O TCC 1
entregou especificação e modelagem; este log existe porque a implementação real (TCC 2)
inevitavelmente encontra lacunas que o TCC 1 não endereçava, ou decide algo diferente do
desenho original — e isso precisa ficar rastreável para a banca e para sessões futuras, em vez
de se perder espalhado em `progress.md` ou em comentários de commit.

Cada entrada segue o formato: **O que mudou** / **Por quê** / **Impacto**. Decisões ainda em
aberto (não fechadas) ficam marcadas explicitamente como tal — este arquivo não deve fingir que
uma pendência foi resolvida só para parecer completo.

Este log é cumulativo — toda sessão que tomar uma decisão que diverge do TCC1 original deve
adicionar uma entrada aqui, além de atualizar a nota normativa correspondente do vault
(`ARCHITECTURE.md`, `DATA-MODEL.md`, etc.) no mesmo commit. Ver [[ARCHITECTURE]] seção "Decisões
que não devem ser reinterpretadas" para as decisões já consolidadas como definitivas.

## Índice cronológico

- [2026-08-01 — Idioma da superfície técnica e i18n completo](#2026-08-01-idioma-da-superficie-tecnica-e-i18n-completo)
- [2026-08-01 — API Gateway como serviço próprio](#2026-08-01-api-gateway-como-servico-proprio)
- [2026-08-01 — Caminho de confiança do telegram-integration](#2026-08-01-caminho-de-confianca-do-telegram-integration)
- [2026-08-01 — Eventos BetCreated/BetSettled traduzidos e PROCESSED_EVENT revivida](#2026-08-01-eventos-betcreatedbetsettled-traduzidos-e-processed_event-revivida)
- [2026-08-02 — Modelo de tenant multiusuário e provisionamento de banco](#2026-08-02-modelo-de-tenant-multiusuario-e-provisionamento-de-banco)
- [2026-08-02 — Pipeline de CI (SonarCloud) e formato JSON para i18n do Python](#2026-08-02-pipeline-de-ci-sonarcloud-e-formato-json-para-i18n-do-python)
- [2026-08-02 — Topologia: 7 repositórios independentes, não monorepo](#2026-08-02-topologia-7-repositorios-independentes-nao-monorepo)
- [2026-08-02 — Nomes reais dos repositórios (usuário GitHub eimmig)](#2026-08-02-nomes-reais-dos-repositorios-usuario-github-eimmig)
- [2026-08-02 — Modelo de branch: main/develop/feature-bugfix-spike](#2026-08-02-modelo-de-branch-maindevelopfeature-bugfix-spike)
- [2026-08-02 — QA visual em apps/web: Impeccable e taste-skill](#2026-08-02-qa-visual-em-appsweb-impeccable-e-taste-skill-playwright-ja-estava-decidido)
- [2026-08-02 — Plugins de agente para todos os repositórios: Caveman + claude-code-skills](#2026-08-02-plugins-de-agente-para-todos-os-repositorios-caveman--claude-code-skills)
- [2026-08-03 — Postgres por instância, topologia RabbitMQ e DLQ do ambiente local](#2026-08-03-postgres-por-instancia-topologia-rabbitmq-e-dlq-do-ambiente-local)
- [2026-08-03 — Jira como espelho do backlog (reverte "este projeto não usa Jira")](#2026-08-03-jira-como-espelho-do-backlog-reverte-este-projeto-nao-usa-jira)
- [2026-08-17 — Conventional Commits 1.0.0, sempre em inglês](#2026-08-17-conventional-commits-100-sempre-em-ingles)
- [2026-08-17 — DLQ/retry não é RNF06: requisito de prosa, sem ID](#2026-08-17-dlqretry-nao-e-rnf06-requisito-de-prosa-sem-id)
- [2026-08-17 — SonarCloud adiado até o primeiro repositório ter código](#2026-08-17-sonarcloud-adiado-ate-o-primeiro-repositorio-ter-codigo)
- [2026-08-17 — Templates de issue do Jira, separados do script](#2026-08-17-templates-de-issue-do-jira-separados-do-script)
- [2026-09-03 — huashu-design adicionado; correção sobre `/impeccable init`](#2026-09-03-huashu-design-adicionado-correcao-sobre-impeccable-init)
- [2026-09-03 — Templates do Jira alinhados ao padrão de `oficina/tools`](#2026-09-03-templates-do-jira-alinhados-ao-padrao-de-oficinatools)
- [2026-08-19 — Raiz vira o 8º repositório (`sv-harness`), reverte "a raiz nunca vai para o GitHub"](#2026-08-19-raiz-vira-o-8-repositorio-sv-harness-reverte-a-raiz-nunca-vai-para-o-github)
- [2026-09-04 — `mustChangePassword` não bloqueia login, reverte a intenção original da entrada de 2026-08-02](#2026-09-04-mustchangepassword-nao-bloqueia-login-reverte-a-intencao-original-da-entrada-de-2026-08-02)

---

## 2026-08-01 — Idioma da superfície técnica e i18n completo

**O que mudou**: os diagramas originais do TCC1 usam português para rotas e nomes de evento
(`/apostas`, `ApostaCriada`, `ApostaLiquidada`). Decidido traduzir toda a superfície técnica
(rotas REST, query params, nomes/valores de evento, chaves de cache) para inglês, mantendo
apenas UI e mensagens de erro localizadas — e localizadas nos **três** idiomas (`pt-BR`/`en-US`/
`es`), não só português como o TCC1 assumia implicitamente.

**Por quê**: consistência com os nomes de entidade/campo, que já eram em inglês desde os ERDs
originais (`BET`, `stake`, `odd`); decisão do usuário de que o sistema deveria ser
internacionalizável desde o início, não como melhoria futura.

**Impacto**: `docs/API-CONTRACTS.md`, `docs/CONVENTIONS.md` seção "Internacionalização (i18n)".
Detalhe completo já documentado nessas notas — não duplicado aqui.

## 2026-08-01 — API Gateway como serviço próprio

**O que mudou**: os diagramas originais do TCC1 (estrutural e de implantação) já mencionavam um
"API Gateway"/"Load Balancer", mas nenhum RF, epic ou harness cobria construí-lo — os outros
serviços simplesmente assumiam que ele existia. Criado `epic-008` e `services/api-gateway/`
como serviço de aplicação de pleno direito (não infraestrutura genérica), único validador de
token PASETO e único injetor de identidade nas chamadas entre serviços.

**Por quê**: sem ele, o modelo de confiança descrito em `docs/API-CONTRACTS.md` (bets-service e
stats-service confiando cegamente em headers injetados) não tinha implementação real —
lacuna crítica encontrada em auditoria do harness antes do início da codificação.

**Impacto**: `docs/services/api-gateway.md`, `docs/ARCHITECTURE.md`, `feature_list.json` raiz
(epic-008). Detalhe completo em `progress.md` da raiz, entrada "Auditoria do harness" (2026-08-01).

## 2026-08-01 — Caminho de confiança do telegram-integration

**O que mudou**: os diagramas originais mostram `telegram-integration` chamando `bets-service`
diretamente, sem Gateway e sem nenhum mecanismo de autenticação visível. Decidido: o bot
autentica no `api-gateway` via credencial de serviço estática (`X-Service-Key`), que resolve
`telegramUserId -> userId` chamando um novo endpoint em `auth-service`
(`GET /api/v1/telegram-accounts/{telegramUserId}`) antes de rotear para `bets-service`.

**Por quê**: o bot não tem usuário logado nem token PASETO — os diagramas do TCC1 simplesmente
não endereçavam essa questão, apenas assumiam a chamada direta.

**Impacto**: `docs/services/auth-service.md` (endpoint de lookup + fluxo de vínculo de conta),
`docs/services/api-gateway.md`, `docs/API-CONTRACTS.md` seção "Confiança entre serviços".

## 2026-08-01 — Eventos BetCreated/BetSettled traduzidos e PROCESSED_EVENT revivida

**O que mudou**: (a) os diagramas de fluxo do TCC1 já usavam dois eventos distintos
(`ApostaCriada`/`ApostaLiquidada`, traduzidos aqui para `BetCreated`/`BetSettled`) — confirmado,
não é uma divergência, só tradução. (b) a tabela `PROCESSED_EVENT`, presente no rascunho
conceitual mais antigo do TCC1, não sobreviveu ao ERD OLAP final — foi revivida deliberadamente
neste harness porque o requisito de idempotência do consumo de evento (ver `docs/TESTING.md`)
não tinha nenhum outro mecanismo definido nos diagramas mais recentes. (c) `FACT_BET` ganhou
campo `status` e tornou `profit`/`isWin` nullable — extensão sobre o ERD original, necessária
para RN06 (excluir `pending` das agregações) coexistir com o padrão insert-then-upsert
(`BetCreated` insere, `BetSettled` faz upsert na mesma linha).

**Por quê**: fechar lacunas técnicas que o ERD final do TCC1 deixava sem solução (idempotência,
convivência de dois eventos na mesma linha de fato).

**Impacto**: `docs/DATA-MODEL.md` seção "Evolução do modelo" (histórico completo já documentado
lá, não duplicado aqui), `docs/services/stats-service.md` seção "Idempotência".

---

## 2026-08-02 — Modelo de tenant multiusuário e provisionamento de banco

Discussão completa sobre como a camada de dados provisiona e isola tenants — o TCC1 modelava
`USER` como uma conta individual simples (RF01: "criação e gerenciamento de contas, nome/e-mail/
senha") e não tinha nenhum conceito de organização, hierarquia de usuários ou provisionamento de
schema. As decisões abaixo são todas **extensões novas**, não estavam no TCC1 original.

### 1. Tenant = organização com múltiplos usuários independentes

**O que mudou**: um tenant deixou de ser sinônimo de "um usuário" (modelo 1:1 implícito no RF01
original) e passou a representar uma organização que pode ter vários usuários independentes
compartilhando o mesmo schema/dados.

**Por quê**: decisão explícita do usuário nesta sessão, para suportar múltiplas pessoas
gerenciando a mesma banca/organização.

**Impacto**: `USER` ganha campo `role` (`admin`/`member`); RF01 é reinterpretado (ver
`docs/REQUIREMENTS.md`); todo o modelo de confiança do Gateway precisa distinguir "quem" (usuário)
de "qual organização" (tenant) — ver decisão 6 abaixo.

### 2. Isolamento por schema estendido também ao `auth-service`

**O que mudou**: schema-per-tenant, que já valia para `bets-service`/`stats-service`, passa a
valer também para `auth-service` — `USER` vive dentro do schema do próprio tenant, não numa
tabela global única com uma coluna de discriminação.

**Por quê**: elimina uma classe inteira de bug (esquecer o `WHERE tenant_id = ?` em alguma query)
porque a query fisicamente não enxerga outros tenants; consistente com o mesmo padrão já usado
nos outros dois serviços Java.

**Impacto**: `USER` **não** tem coluna `tenantId` — o próprio schema é o limite. `email` passa a
ser único **por schema de tenant**, não globalmente (dois tenants podem ter cada um seu
`joao@gmail.com`). Ver `docs/DATA-MODEL.md`.

### 3. Provisionamento de tenant via rota admin, restrita ao operador da plataforma

**O que mudou**: criação de um tenant novo (schema + primeiro usuário admin daquele tenant) é
feita por uma rota administrativa, chamável **apenas pelo operador da plataforma** — não há
autocadastro público de organização.

**Por quê**: decisão explícita do usuário; evita lidar com fraude/spam de autocadastro de
organizações, aceitável para o escopo do TCC (não é um SaaS de autoatendimento).

**Impacto**: `auth-service` ganha uma rota administrativa fora do fluxo normal de usuário. O
primeiro usuário do tenant nasce como `admin@<nome-do-tenant>` com uma senha padrão.

**Resolvido em 2026-08-02** (mesmo dia, decidido depois desta entrada original — ver item 15
abaixo para o racional completo do lookup de Telegram, que dependia de dois destes três pontos):

- **Autenticação da rota admin**: header `X-Admin-Api-Key` — um segredo estático dedicado,
  análogo a `X-Service-Key` mas de uso exclusivo do operador da plataforma, nunca do
  `telegram-integration`. Ver [[API-CONTRACTS]] seção "Confiança entre serviços".
- **Orquestração cross-service**: **três chamadas manuais separadas** do operador, uma por
  serviço (`auth-service`, depois `bets-service`, depois `stats-service`), todas com o mesmo
  `X-Admin-Api-Key` — nenhum serviço chama os outros dois em código. Escolhida sobre a
  alternativa de `auth-service` orquestrar tudo numa única chamada porque: (a) criar tenant é
  operação rara (onboarding manual de organização, não um fluxo self-service de alto volume) —
  o custo de 3 passos manuais em vez de 1 é aceitável; (b) evita lógica de compensação para
  falha parcial (schema criado em `auth-service` mas a chamada a `bets-service` falha); (c)
  **resolve sozinho o risco de dependência circular** sinalizado abaixo — como nenhum serviço
  chama outro em código, a ordem de dependência declarada em `feature_list.json` da raiz
  (`epic-003`/`epic-004` dependem de `epic-002`) continua válida sem precisar reordenar nada.
- **Senha padrão previsível**: **troca obrigatória no primeiro login**. `USER` ganha coluna
  `mustChangePassword` (boolean, `true` para o admin recém-criado por provisionamento de
  tenant); o backend bloqueia qualquer outra ação até a senha ser trocada. Ver [[DATA-MODEL]].
- ~~Risco de dependência circular entre epics~~ — não se materializa: a escolha de "três
  chamadas manuais" acima elimina a necessidade de `auth-service` chamar `bets-service`/
  `stats-service` em código, então a ordem de dependência atual (`epic-002` antes de
  `epic-003`/`epic-004`) permanece correta.

### 4. Apenas o admin do tenant cria novos usuários

**O que mudou**: dentro de um tenant já existente, só o usuário com `role = admin` pode criar
outros usuários (`role = member`).

**Por quê**: decisão explícita do usuário, consistente com a decisão 3 (controle de acesso
centralizado).

**Impacto**: `auth-service` precisa de checagem de autorização por `role` no endpoint de criação
de usuário — lógica de negócio nova, não apenas um campo a mais. Detalhe de enforcement ainda não
especificado (fica para o design de `epic-002`).

> **Precisão importante (esclarecida em 2026-08-02, depois da entrada original acima)**: UC01
> ("Manter usuário") do diagrama de casos de uso original
> (`docs/diagrams/process/use-case-diagram.png`) continua sendo acionado pelo ator **Usuário** —
> não muda de ator, só ganha uma restrição de `role`. É o próprio admin do tenant (um `Usuário`,
> como no diagrama original) quem cria os demais usuários, via UC01 normalmente. A única peça
> **sem equivalente em nenhum UC do TCC1** é o bootstrap do primeiro admin de cada tenant
> (decisão 3), que nasce automaticamente quando o operador da plataforma provisiona o tenant —
> isso sim é um mecanismo novo, fora do diagrama original. Não confundir os dois: UC01
> continua existindo essencialmente como estava, só restrito a quem pode acioná-lo.

### 5. Login exige identificador da organização (slug), além de e-mail e senha

**O que mudou**: como `email` só é único dentro do schema do tenant (decisão 2), a tela de login
precisa de um terceiro campo — o identificador/slug da organização — para que `auth-service`
saiba em qual schema procurar antes de validar a senha.

**Por quê**: alternativa considerada e descartada nesta sessão: manter um diretório global leve
(tabela `email -> schema` fora dos schemas de tenant). Rejeitada por contradizer parcialmente o
isolamento total que motivou a decisão 2 — o usuário preferiu manter o isolamento estrito e pagar
o custo de UX de um campo a mais no login.

**Impacto**: RF02 ganha um campo de entrada novo (slug/organização). Nome do schema é derivado
deterministicamente do slug (ex.: `tenant_<slug>`), então `CREATE SCHEMA` falhando em caso de
slug duplicado já garante unicidade — não é necessário nenhum diretório global adicional para
isso. Ver `docs/CONVENTIONS.md` para a convenção de nomenclatura de schema.

### 6. Migrações Flyway rodam de forma preguiçosa (lazy), por schema, antes de atender a chamada

**O que mudou**: em vez de o Flyway migrar uma lista fixa de schemas no boot da aplicação
(padrão usual), cada serviço Java verifica/roda migrações pendentes do schema do tenant
resolvido **antes** de processar a requisição que chegou — mesmo padrão já usado pelo usuário
profissionalmente em produção.

**Por quê**: decisão explícita do usuário; resolve o problema de "startup precisaria migrar N
schemas de tenant" (lento, e não cobre schemas criados depois que a aplicação já subiu) sem
precisar de um job de migração em lote a cada deploy.

**Impacto**: o mesmo ponto de resolução de tenant (schema por requisição, ver decisão 7 abaixo)
passa a também garantir que o schema está migrado, antes de delegar ao controller. Ver
`docs/CONVENTIONS.md` seção "Migrations".

### 7. Cabeçalho de tenant separado de `X-User-Id`

**O que mudou**: até esta sessão, `docs/API-CONTRACTS.md` tratava `X-User-Id` como sinônimo do
tenant (modelo 1:1 usuário-tenant). Com a decisão 1 (tenant = organização com múltiplos
usuários), isso deixou de ser verdade — o Gateway agora precisa injetar **dois** headers
distintos: `X-User-Id` (quem fez a chamada) e um novo `X-Tenant-Id` (qual organização/schema).

**Por quê**: consequência direta da decisão 1 — sem essa separação, `bets-service`/
`stats-service` não teriam como saber em qual schema rotear uma chamada feita por um usuário
`member` que não é o próprio identificador do tenant.

**Impacto**: `docs/API-CONTRACTS.md` seção "Confiança entre serviços" e envelope de evento
(`BetCreated`/`BetSettled`) — campo `tenantId` do payload deixa de ser `= X-User-Id`. Nome do
header (`X-Tenant-Id`) e convenção de nomenclatura de schema (`tenant_<slug>`) são convenções
técnicas fechadas nesta sessão, análogas a `X-Service-Key`/`X-User-Id` já existentes.

**Resolvido em 2026-08-02** (mesmo dia, decidido depois desta entrada original — ver item 14
abaixo): `BET`/`BET_RESULT` ganharam `createdByUserId`/`settledByUserId`, e o envelope de evento
ganhou `userId` além de `tenantId`.

### 8. Catálogos continuam por tenant, sem seed compartilhado

**O que mudou**: nada, na verdade — confirma a suposição já documentada, agora explicitamente:
`SPORT`/`LEAGUE`/`MARKET`/`TIPSTER` nascem vazios em cada schema de tenant nada é
pré-populado/compartilhado entre tenants.

**Por quê**: decisão explícita do usuário — cada organização cadastra seus próprios catálogos.

**Impacto**: nenhuma mudança de modelo, só remove a ambiguidade que motivou a pergunta.

### 9. Chaves de cache Redis migradas de `user:{id}:...` para `tenant:{tenantId}:...`

**O que mudou**: `docs/services/stats-service.md` documentava chaves `user:{id}:dashboard:...`.
Corrigido para `tenant:{tenantId}:dashboard:...`.

**Por quê**: consequência direta da decisão 1 — `FACT_BET` é isolado por schema de **tenant**,
sem coluna de usuário, e compartilhado por todos os usuários da mesma organização. Chave por
`userId` faria dois usuários do mesmo tenant enxergarem caches (logo dashboards) diferentes sem
nenhum motivo de negócio para isso.

**Impacto**: `docs/services/stats-service.md` seção "Cache Redis (Cache-Aside)".

### 10. Propagação para `telegram-integration` e observabilidade

**O que mudou**: `docs/services/telegram-integration.md` e seu `feature_list.json` ainda citavam
só `X-User-Id` e não tinham o aviso de bloqueio já presente em `auth-service.md`/`api-gateway.md`
sobre o lookup de `TELEGRAM_ACCOUNT` sem schema conhecido (item 7 acima). Logs estruturados
(`docs/OBSERVABILITY-AND-CONFIG.md`) também só carregavam `X-Correlation-Id`, sem `X-Tenant-Id`.

**Por quê**: lacuna de propagação da própria sessão anterior — atualizar um serviço sem
atualizar todos os que dependem do mesmo header/modelo deixa a documentação inconsistente entre
si, o mesmo tipo de problema que motivou este log existir.

**Impacto**: `docs/services/telegram-integration.md`, `services/telegram-integration/feature_list.json`,
`docs/OBSERVABILITY-AND-CONFIG.md` seção "Logs" (agora `tenantId` também vai para o MDC/log
estruturado, junto do correlation id — útil para depurar incidentes específicos de uma
organização).

### 11. `apps/web` redesenhado para o modelo sem autocadastro

**O que mudou**: `docs/services/web.md` e `apps/web/feature_list.json` (`feat-002`) descreviam
uma tela de "cadastro" pública, incompatível com a decisão 3 (só o operador da plataforma cria
tenant) e a decisão 4 (só o admin do tenant cria usuário). Substituído por: login com 3 campos
(slug do tenant, e-mail, senha) e uma tela nova de "gestão de usuários do tenant", visível só
para `role = admin`, que lista e cria usuários (`role = member`) dentro do próprio tenant.

**Por quê**: consequência direta das decisões 1/3/4 — a UI precisa refletir que não existe
autocadastro em nenhum nível.

**Impacto**: `docs/services/web.md` seção "Modelo de tenant (UI)", `apps/web/feature_list.json`
`feat-002`.

**Resolvido em 2026-08-02**: operador da plataforma cria tenant chamando a API diretamente
(`X-Admin-Api-Key`, ver decisão 3/item 3 e [[API-CONTRACTS]]) — **sem UI própria** em `apps/web`
para isso, não faz parte do escopo deste app. `role = member` **não vê** a tela de gestão de
usuários do tenant de forma alguma (nem somente leitura) — visível só para `role = admin`.

### 12. Estratégia de teste de integração para schema-per-tenant

**O que mudou**: `docs/TESTING.md` não descrevia como um teste de `adapter/out/persistence/`
teria um schema de tenant disponível no Postgres efêmero do Testcontainers (schema-per-tenant +
migração lazy, decisões 2 e 6, não têm schema pronto por padrão). Decidido: uma classe base de
teste de integração por serviço provisiona um schema de teste chamando o **mesmo caso de uso de
provisionamento usado em produção** (camada `application/`, não a rota HTTP admin), com slug
único por classe de teste (evita colisão se o container Testcontainers for reaproveitado) e
`DROP SCHEMA` ao final.

**Por quê**: reaproveitar o caminho de código de produção evita duas implementações divergentes
de "como criar um schema" (uma em produção, outra em SQL bruto no teste) — e chamar o caso de
uso diretamente, não a rota HTTP, desacopla a fixture do mecanismo de autenticação daquela rota,
que ainda está em aberto (item 3) — quando for decidido, só o teste da própria rota muda, não a
fixture usada por todos os outros testes de persistência.

**Impacto**: `docs/TESTING.md` seção "Java" (novo item "Schema-per-tenant nos testes de
integração").

### 13. Auditoria pós-tenant: `CLAUDE.md` de serviço e contratos de evento estavam desatualizados

**O que mudou**: os 6 `CLAUDE.md` de serviço (`auth-service`, `bets-service`, `stats-service`,
`api-gateway`, `telegram-integration`, `web`) — o arquivo que cada sessão carrega automaticamente
ao entrar naquela pasta, antes até de ler o vault — não tinham sido atualizados com o modelo de
tenant multiusuário. Em `bets-service/CLAUDE.md`, uma linha estava **factualmente errada**:
*"Só confia no header `X-User-Id`... como identidade do tenant"*. Além disso, os JSON Schemas
reais dos eventos (`docs/contracts/bet-created.schema.json`, `bet-settled.schema.json`) ainda
descreviam `tenantId` como *"userId do dono da aposta"* — o contrato máquina-a-máquina usado
pelos testes (ver [[TESTING]]), não só prosa.

**Por quê**: as sessões anteriores desta série de decisões atualizaram o vault (`docs/`) e os
`feature_list.json`, mas não os `CLAUDE.md` de serviço nem os schemas JSON — uma lacuna de
propagação encontrada só numa auditoria dedicada, pedida explicitamente pelo usuário.

**Impacto**: todos os 6 `CLAUDE.md` de serviço ganharam os bullets correspondentes (headers
`X-User-Id`/`X-Tenant-Id` distintos, schema-per-tenant também em `auth-service`, migração lazy,
avisos de bloqueio onde aplicável). `bet-created.schema.json`/`bet-settled.schema.json`: campo
`tenantId` perdeu `"format": "uuid"` (agora é o slug do tenant, não necessariamente um UUID) e a
descrição foi corrigida.

**Lição para sessões futuras**: ao mudar uma convenção cross-service, checklist de propagação
completo é: nota(s) de serviço no vault → `docs/API-CONTRACTS.md`/outras notas cross-service →
`feature_list.json` (raiz e de cada serviço afetado) → **`CLAUDE.md` de cada serviço afetado** →
schemas JSON em `docs/contracts/` se o contrato de evento mudar. Os dois últimos itens foram os
que passaram batido nesta série de decisões.

### 14. Trilha de auditoria por usuário: `createdByUserId`/`settledByUserId` + `userId` no envelope

**O que mudou**: fecha a pendência do item 7 acima. `BET` ganha `createdByUserId`, `BET_RESULT`
ganha `settledByUserId` (ambos `uuid`, valor de `X-User-Id` no momento da chamada, sem FK real —
`USER` vive em `auth-service`, outro banco). O envelope de `BetCreated`/`BetSettled` ganha
`userId` (campo obrigatório) além de `tenantId` — `BetCreated.userId = BET.createdByUserId`,
`BetSettled.userId = BET_RESULT.settledByUserId` (podem ser pessoas diferentes: quem registrou a
aposta não precisa ser quem depois a liquida).

**Por quê**: decisão explícita do usuário — saber qual organização isola os dados (`tenantId`)
não é suficiente, também é preciso saber qual usuário dentro dela fez cada ação.

**Impacto**: `docs/DATA-MODEL.md` (ERD de `bets-service`), `docs/services/bets-service.md`,
`docs/API-CONTRACTS.md` (envelope + nota sobre `X-User-Id`), `docs/contracts/bet-created.schema.json`
e `bet-settled.schema.json` (`userId` agora obrigatório no envelope),
`services/bets-service/feature_list.json` (`feat-004`, `feat-005`, `feat-006`, `feat-008`),
`services/bets-service/CLAUDE.md`.

**Escopo deliberadamente não estendido**: `stats-service`/`FACT_BET` **não** persiste `userId` —
RN04/RN08/RN09 agregam por tenant/segmento (esporte/mercado/casa), não por usuário, e não há
nenhum RF/RN pedindo dashboard por usuário dentro do tenant. O dado já chega no envelope se um
requisito futuro precisar disso — ver `docs/services/stats-service.md`.

### 15. Lookup `telegramUserId -> tenant` resolvido via diretório no schema `public`

**O que mudou**: fecha o bloqueio sinalizado nos itens 3/7/10 (e em `docs/API-CONTRACTS.md`,
`docs/services/{auth-service,api-gateway,telegram-integration}.md`): como não há como saber em
qual schema de tenant procurar um `telegramUserId` sem algum índice fora dos schemas,
`auth-service` ganha duas tabelas no schema **`public`** do seu próprio banco (fora de qualquer
schema de tenant):

- `TELEGRAM_LINK` (`telegramUserId` PK, `tenantId`, `userId`) — diretório definitivo, consultado
  por `GET /api/v1/telegram-accounts/{telegramUserId}` (usado pelo `api-gateway` em toda captura
  automática de aposta). Lookup O(1), sem varrer schemas.
- `PENDING_TELEGRAM_LINK` (`code` PK, `tenantId`, `userId`, `expiresAt`) — códigos de vínculo de
  curta duração. Gerados pelo endpoint autenticado (usuário logado em `apps/web`, já dentro do
  seu tenant) e gravados aqui **além de** dentro do schema do tenant, exatamente para que o passo
  de confirmação (que só recebe `telegramUserId` + código, sem saber o tenant) consiga achar o
  tenant certo.

O passo de confirmação (`telegramUserId` + código → `auth-service`, via `api-gateway`, sem
PASETO) faz, numa única transação: busca o código em `PENDING_TELEGRAM_LINK`, cria/atualiza
`TELEGRAM_ACCOUNT` dentro do schema do tenant resolvido, e faz upsert em `TELEGRAM_LINK`.

**Por quê**: schema-per-tenant aqui vive **dentro do mesmo banco Postgres** de `auth-service`
(schemas são só namespaces do mesmo banco, não bancos físicos separados) — então uma operação
que grava no schema `public` e num schema de tenant ao mesmo tempo é uma transação local comum,
não um problema de transação distribuída. Duas tabelas pequenas de diretório resolvem o lookup
sem quebrar a regra "dado de tenant vive isolado no schema do tenant" (`TELEGRAM_LINK`/
`PENDING_TELEGRAM_LINK` não são dado de negócio de nenhum tenant — são só um índice de
identidade, análogo a um catálogo/diretório cross-tenant). Alternativa descartada: pedir o slug
do tenant ao usuário toda vez que captura uma aposta pelo bot — pior UX e desnecessário, já que
o vínculo só precisa do tenant uma vez (no momento da confirmação).

**Impacto**: `docs/DATA-MODEL.md` (ERD de `auth-service`, novo bloco "diretório global");
`docs/services/auth-service.md` seção "Vínculo de conta Telegram"; `docs/services/api-gateway.md`
e `docs/services/telegram-integration.md` (removido o aviso de bloqueio);
`docs/API-CONTRACTS.md` seção "Confiança entre serviços"; `services/auth-service/feature_list.json`
(`feat-006`), `services/api-gateway/feature_list.json` (`feat-004`),
`services/telegram-integration/feature_list.json` (`feat-004`); `feature_list.json` da raiz
(`epic-005`, `epic-008`); `CLAUDE.md` de `auth-service`, `api-gateway` e `telegram-integration`.

## 2026-08-02 — Pipeline de CI (SonarCloud) e formato JSON para i18n do Python

**O que mudou**: adotada uma pipeline de CI no GitHub Actions, um workflow por serviço (não um
workflow único do monorepo), com 5 passos sempre na mesma ordem: validação de
`CHANGELOG.md` atualizado, validação de que as 3 chaves de tradução (`pt-BR`/`en-US`/`es`) estão
em sincronia, build, testes unitários com cobertura, e análise de qualidade/cobertura no
**SonarCloud** (não SonarQube self-hosted) — um projeto por serviço, chave = nome do repositório
GitHub daquele serviço (ex.: `sv-bets-backend` — ver entrada "Nomes reais dos repositórios"
abaixo; `stakevault-<nome>` foi o placeholder original desta decisão, substituído no mesmo dia
em que os nomes reais foram definidos).
Registrado como uma feature nova em cada `feature_list.json` de serviço (dependente de
`feat-001`), não como um epic cross-service na raiz, já que o design em si (workflow, scripts)
é compartilhado mas a execução é isolada por serviço, igual ao resto do harness. Como
consequência prática, o formato de i18n de `telegram-integration`, deixado em aberto em
`docs/CONVENTIONS.md` ("JSON ou gettext"), foi fechado como **JSON**
(`locales/{pt-BR,en-US,es}.json`) — o validador de chaves precisa de um formato concreto, e JSON
evita introduzir `gettext` como dependência nova (mesmo raciocínio que o texto original já
dava) além de reusar o mesmo parser do validador usado por `apps/web`.

**Por quê**: decisão explícita do usuário — quer agentes/sessões trabalhando em paralelo em
serviços diferentes (ver `CLAUDE.md` raiz seção "Regras de trabalho"), e quer um gate
automatizado de qualidade/cobertura por serviço antes de qualquer merge, não só a verificação
local via `init.sh`.

**Impacto**: `docs/CI-CD.md` (nota nova, descreve os 5 passos e o setup pendente do
SonarCloud), `docs/Index.md` (link), `docs/CONVENTIONS.md` (formato JSON do Python fechado,
referência a `[[CI-CD]]` no fluxo de git), `docs/TESTING.md` (relatórios de cobertura já
definidos — JaCoCo XML, LCOV, `coverage.xml` — agora também consumidos pelo Sonar),
`.github/workflows/*.yml` (6 arquivos, um por serviço), `.github/scripts/validate-changelog.sh`
e `validate-i18n-keys.py`, `CHANGELOG.md` novo em cada serviço/app, `sonar-project.properties`
em `apps/web` e `services/telegram-integration`, `CLAUDE.md` (raiz e de cada serviço) e
`feature_list.json` de cada serviço (nova feature de CI).

**Em aberto**: o repositório ainda não existe no GitHub — os workflows são scaffolding até (1)
`git init` + push para um repo real, (2) criação da organização e dos 6 projetos no SonarCloud,
(3) secret `SONAR_TOKEN` e variable `SONAR_ORGANIZATION` configurados no repositório GitHub. Ver
`docs/CI-CD.md` seção "Setup pendente".

**Emenda (2026-08-02, mesmo dia)**: a topologia acima ("o repositório") assumia um monorepo —
revisto no mesmo dia, ver entrada seguinte "Topologia: 7 repositórios independentes, não
monorepo". `.github/workflows/`/`.github/scripts/` foram movidos da raiz para dentro de cada
pasta de serviço; os 5 passos, o formato do changelog e o gate de cobertura em si não mudam.

## 2026-08-02 — Topologia: 7 repositórios independentes, não monorepo

**O que mudou**: decisão explícita do usuário — o projeto não será um monorepo. Seriam criados
inicialmente **6 repositórios GitHub independentes**, um por serviço (`api-gateway`,
`auth-service`, `bets-service`, `stats-service`, `telegram-integration`, `web`) — número que
sobe para **7** ainda no mesmo dia com a adição de `infra/` (ver "Resolvido em 2026-08-02"
abaixo). As pastas continuam aninhadas
localmente dentro desta mesma árvore de trabalho (`services/<nome>/`, `apps/web/`), cada uma
ganhando seu próprio `.git` interno — só por conveniência de trabalhar com todos os serviços à
vista numa única sessão local. **A raiz deste diretório (`CLAUDE.md`, este vault `docs/`,
`feature_list.json`, `progress.md`) não é um repositório Git e nunca vai para o GitHub** — é só
uma pasta de trabalho/vault local.

> **Revisto em 2026-08-19**: esta última frase (raiz não versionada) foi revertida — ver a
> entrada [2026-08-19](#2026-08-19-raiz-vira-o-8-repositorio-sv-harness-reverte-a-raiz-nunca-vai-para-o-github).
> O resto desta entrada (não-monorepo, 7 repositórios de código independentes) continua valendo.

**Por quê**: decisão explícita do usuário sobre como quer distribuir/hospedar o código —
não foi motivada por uma limitação técnica descoberta nesta sessão.

**Impacto**:
- `.github/workflows/`/`.github/scripts/` deixam de existir na raiz e passam a existir **dentro
  de cada pasta de serviço** (`services/<nome>/.github/...`, `apps/web/.github/...`) — cada
  workflow perde o `paths:` de filtro de monorepo (não faz mais sentido: o próprio repositório já
  é o limite do serviço) e o `defaults.run.working-directory` (a raiz do serviço já é a raiz do
  repositório). `docs/CI-CD.md` reescrita para refletir isso.
- Scripts de validação (`validate-changelog.sh`, `validate-i18n-keys.py`) duplicados nos 6
  repositórios em vez de compartilhados a partir de um único `.github/scripts/` na raiz — ver
  `docs/CI-CD.md` seção "Scripts de CI duplicados em cada repositório, não compartilhados" para o
  racional (evita um 7º repositório só de tooling de CI).
- `CLAUDE.md` da raiz: seção "Harness multinível" e "Artefatos obrigatórios" atualizadas para
  deixar explícito que a raiz não é um repositório e cada serviço é o seu próprio.
  `docs/CONVENTIONS.md` seção "Git": nome de branch não precisa mais de prefixo de serviço
  (`feat/<id-da-feature>`, não `feat/<serviço>/<id-da-feature>`) já que cada repositório só
  contém um serviço.
- `feature_list.json` de cada serviço: descrição da feature de CI atualizada com o novo caminho
  (`.github/workflows/ci.yml`, não `.github/workflows/<serviço>.yml` na raiz).

**Resolvido em 2026-08-02** (mesmo dia, decidido depois desta entrada original): `epic-001`
(infraestrutura `docker-compose.yml`) e `epic-007` (teste de resiliência cross-service) ganham
um **7º repositório, `infra/`** — decisão do usuário entre duas opções (repositório próprio vs.
viver dentro de `api-gateway`, o único serviço sem domínio de negócio próprio). `infra/` passa a
ter harness completo (`CLAUDE.md`, `feature_list.json` com `feat-001`/`feat-002`, `init.sh`,
`progress.md`, `CHANGELOG.md`, `.github/`) igual aos 6 serviços de aplicação, só que sem
arquitetura hexagonal/i18n (não se aplica) e com uma pipeline de CI mais simples (changelog +
`docker compose config`, sem i18n nem SonarCloud). `epic-001`/`epic-007` na raiz passam a ter
`harness: "infra/"` em vez de `harness: null`. Este `infra/` é um repositório **diferente** do 7º
repositório hipotético de tooling de CI compartilhado mencionado acima (aquele foi rejeitado;
este, de infraestrutura, foi aceito). Ver `docs/CI-CD.md` (seções atualizadas) e
`infra/CLAUDE.md`.

## 2026-08-02 — Nomes reais dos repositórios (usuário GitHub `eimmig`)

**O que mudou**: usuário forneceu os 7 repositórios GitHub reais (já criados, vazios),
substituindo o placeholder `stakevault-<serviço>` usado nas entradas anteriores:

| Pasta local | Repositório |
|---|---|
| `services/api-gateway/` | `eimmig/sv-api-gateway` |
| `services/auth-service/` | `eimmig/sv-auth-backend` |
| `services/bets-service/` | `eimmig/sv-bets-backend` |
| `services/stats-service/` | `eimmig/sv-stats-backend` |
| `services/telegram-integration/` | `eimmig/sv-telegram-integration-backend` |
| `apps/web/` | `eimmig/sv-frontend` |
| `infra/` | `eimmig/sv-infra-backend` |

Prefixo `sv-` = StakeVault, nome de marca já decidido em `docs/DESIGN-SYSTEM.md` — não é uma
convenção nova.

**Por quê**: os repositórios existiam apenas como conceito ("vou criar 5/6 repositórios") até
esta sessão; agora são reais e a documentação/CI podem referenciá-los concretamente.

**Impacto**: chave de projeto SonarCloud passou de `stakevault-<serviço>` para o próprio nome do
repositório (ex.: `sv-bets-backend`) — atualizado nos 6 workflows/`sonar-project.properties` de
serviço. `docs/CI-CD.md` ganhou a tabela de mapeamento pasta→repositório. `feature_list.json` de
cada um dos 7 harnesses ganhou a URL do repositório correspondente na descrição da feature de
CI (ou de `feat-001`, no caso de `infra/`).

**Resolvido em 2026-08-02** (mesmo dia): usuário optou por `git init` + `git remote add origin`
nas 7 pastas, sem commit nem push. Feito — as 7 pastas têm `.git` local, branch `main`, remote
`origin` correto, zero commits. Push fica para quando o usuário pedir explicitamente (ação que
publica conteúdo no GitHub).

## 2026-08-02 — Modelo de branch: `main`/`develop`/`feature`-`bugfix`-`spike`

**O que mudou**: decisão explícita do usuário — 3 níveis de branch, iguais nos 7 repositórios:
`main` (estável, só recebe merge de `develop`), `develop` (integração, base de tudo), e branches
de trabalho a partir de `develop` com prefixo por tipo — `feature/<id>`, `bugfix/<id>`,
`spike/<slug>`. Substitui a convenção anterior (`feat/<id-da-feature>`, sem branch de
integração).

**Por quê**: decisão explícita do usuário, modelo Git Flow simplificado (sem branches de
release/hotfix — não pedidas). Como o projeto não usa Jira, o `<id>` de `feature`/`bugfix` é o
id da feature/epic em `feature_list.json` daquele repositório (ex.: `feature/feat-004`) em vez
de um código de ticket externo; `spike/<slug>` não tem id associado (investigação sem feature
formal).

**Impacto**: `docs/CONVENTIONS.md` seção "Git" (reescrita), `CLAUDE.md` raiz (bullet "Git"),
`docs/CI-CD.md` seção "Setup pendente" (passo 1 menciona criar `develop` a partir de `main` no
primeiro commit), e os 7 `.github/workflows/ci.yml` (`push: branches:` passou de `[main]` para
`[main, develop]`, já que push direto em `develop` também deve rodar CI).

**Em aberto**: nenhum dos 7 repositórios tem commit ainda, então `develop` ainda não existe de
fato em nenhum — só documentado como convenção para quando o primeiro commit acontecer.

## 2026-08-02 — QA visual em apps/web: Impeccable e taste-skill (Playwright já estava decidido)

**O que mudou**: usuário pediu 3 ferramentas para `apps/web`: [Playwright](https://github.com/microsoft/playwright)
(já decidido, sem mudança — E2E funcional), [Impeccable](https://github.com/pbakaus/impeccable) e
[taste-skill](https://github.com/leonxlnx/taste-skill) (novas — ambas são *design guidance para
agentes de IA*, não bibliotecas de app: comandos/skills que auditam UI implementada contra
padrões de "cara de IA genérica"). As duas novas normalmente geram seu próprio `DESIGN.md`/
referências visuais — decidido **não deixar isso acontecer**: `docs/DESIGN-SYSTEM.md` já é a
única fonte de verdade de design deste projeto (marca StakeVault, paleta, layout em painéis,
fechados antes desta sessão). Uso restrito a auditoria/polish de componentes já implementados
contra `docs/DESIGN-SYSTEM.md`, nunca como fonte de novas decisões visuais.

**Por quê**: decisão explícita do usuário sobre quais ferramentas usar; a restrição de uso
(QA-only, sem gerar design language próprio) foi proposta por mim e confirmada pelo usuário, para
evitar duas fontes de verdade de design divergentes.

**Impacto**: `docs/DESIGN-SYSTEM.md` (nova seção "QA visual"), `docs/CONVENTIONS.md` seção
Frontend, `apps/web/CLAUDE.md` (bullet novo + item na Definição de Pronto),
`apps/web/feature_list.json` (`feat-001` ganhou a instalação: `npx impeccable install`, `npx
skills add https://github.com/leonxlnx/taste-skill`).

**Em aberto**: não instalado ainda — `apps/web` não tem `package.json` (`feat-001` não
iniciado). Instalação prevista para quando `feat-001` for de fato implementado, não nesta sessão
(usuário optou por só documentar por enquanto).

**Emenda (2026-08-02, mesmo dia)**: usuário pediu que Impeccable/taste-skill sejam
**prioritárias** também, mesmo tratamento do Caveman/claude-code-skills — ferramenta padrão de
QA visual em `apps/web`, não uma opção entre outras. Reafirmado no mesmo pedido: o design já
definido (`docs/DESIGN-SYSTEM.md`) continua sendo a fonte de verdade — a prioridade é de *uso da
ferramenta como auditoria*, não de deixá-la substituir decisões de design já tomadas. Sem
mudança na regra QA-only já registrada acima. `docs/DESIGN-SYSTEM.md` e `apps/web/CLAUDE.md`
atualizados para deixar a prioridade explícita. Instalação continua pendente de `feat-001` (sem
mudança nesta emenda).

## 2026-08-17 — Conventional Commits 1.0.0, sempre em inglês

**O que mudou**: decisão explícita do usuário — toda mensagem de commit dos 7 repositórios segue
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) **em inglês**
(descrição, corpo e footers). A convenção em si já valia desde a entrada de 2026-08-02 ("Modelo
de branch"), mas sem idioma definido e sem o formato completo — o exemplo registrado ali
(`feat: RF04 registro manual de apostas (SV-12 / feat-004)`) era em português e colocava a
rastreabilidade entre parênteses na descrição, não em footer. Fechado agora:

- Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`, `revert`.
- Descrição no imperativo, minúscula, sem ponto final.
- Rastreabilidade em **footers**, um por linha: `Refs: <chave-jira>` e `Feature: <id>` — os dois,
  mantendo o motivo já registrado em 2026-08-02 (chave liga à story, id liga ao
  `feature_list.json`, que é a fonte da verdade).
- Breaking change: `!` antes dos dois-pontos **e** footer `BREAKING CHANGE:`, obrigatório quando
  um contrato entre serviços muda (ver [[API-CONTRACTS]]).

**Por quê**: pedido direto do usuário. O inglês é coerente com a decisão de 2026-08-01 ("Idioma
da superfície técnica"), que já colocou rotas, nomes/valores de evento e chaves de cache em
inglês — commit é a mesma superfície técnica, cita esses identificadores o tempo todo, e
misturar prosa em português com `feat(bets): POST /api/v1/bets` era a inconsistência remanescente.
Footer em vez de parênteses é o que a spec 1.0.0 define (convenção de trailer do git), então
ferramenta que lê Conventional Commits consegue extrair a chave sem parsing ad-hoc.

**Escopo — o que *não* muda**: `CHANGELOG.md`, `progress.md`, `session-handoff.md`,
`feature_list.json` e todo o vault seguem em português. São entregável de TCC e leitura da banca,
não superfície técnica. A regra de i18n de produto (três locales sempre, ver [[CONVENTIONS]])
também não é afetada.

**Impacto**: [[CONVENTIONS]] seção "Git" (bullet "Commits" reescrito com o formato completo),
`CLAUDE.md` raiz (bullet "Git" e passo 4 do Fim de Sessão). Os 7 `CLAUDE.md` de harness não
citavam convenção de commit — apontam para [[CONVENTIONS]], sem edição necessária.

**Nota sobre commits já existentes**: os 3 commits de `infra/` (único repositório com histórico)
já estavam em inglês e em Conventional Commits, mas sem os footers `Refs:`/`Feature:` — a chave
do Jira nem existia ainda. Não reescritos: `main` e `develop` já foram publicados, e um
`filter-branch` para acrescentar footer retroativo troca rastreabilidade real por cosmética.

## 2026-08-17 — DLQ/retry não é RNF06: requisito de prosa, sem ID

**O que mudou**: `epic-007` (e `infra/feat-002`) citava **RNF06 (Escalabilidade)** como
justificativa do teste de resiliência DLQ/retry, com uma ressalva registrada desde 2026-08-01 de
que a citação parecia errada e só o PDF do TCC 1 poderia confirmar. **Conferido no PDF em
2026-08-17** (`TCC_1_Sistema_de_Apostas.pdf`, Quadro 4, p. 31): a tabela original tem exatamente
seis RNFs, RNF06 é *"garantir a capacidade de expansão da infraestrutura da aplicação para
suportar o crescimento do volume de dados e requisições sem degradação do desempenho"* — volume,
não tolerância a falha — e **nenhum dos seis é sobre confiabilidade**. A citação estava de fato
errada e foi removida dos dois lugares.

O mecanismo, porém, **não é invenção do TCC 2**: está especificado no TCC 1 em prosa, em dois
pontos. Abertura da seção 4.1 (p. 30): *"o sistema foi projetado para processar dados de forma
segura e consistente, utilizando mecanismos de reentrega automática de mensagens (retries) e
isolamento de falhas por meio de uma fila de mensagens mortas (Dead Letter Queue — DLQ) [...]
impedindo que erros isolados travem o fluxo do sistema e permitindo uma análise posterior das
falhas"*. E no capítulo de arquitetura: *"o uso de mecanismos como DLQ garante que nenhuma
mensagem de aposta seja descartada sem ser processada, permitindo que o sistema recupere o estado
consistente assim que os recursos forem restabelecidos"*. É essa passagem que `epic-007` verifica.

**Por quê não criar um RNF07 (Confiabilidade)**: decisão do usuário entre as três opções
oferecidas (citar a prosa / criar RNF07 / manter RNF06 com ressalva). Criar um ID novo tornaria a
tabela de requisitos do TCC 2 divergente da do TCC 1 — algo que a banca veria e que precisaria ser
justificado — em troca de conveniência de rastreabilidade. Citar a passagem resolve a
rastreabilidade sem mexer na tabela.

**Impacto**: [[REQUIREMENTS]] (nota após a tabela de RNF, com as duas citações e a instrução
explícita de que `epic-007` não deve citar RNF06), `feature_list.json` da raiz (`epic-007`),
`infra/feature_list.json` (`feat-002`), `progress.md` da raiz e `session-handoff.md` (risco em
aberto desde 2026-08-01, agora fechado).

**Fecha** a pendência registrada em 2026-08-01 ("nenhum diagrama cita números de RNF/RN
diretamente, então a dúvida sobre a citação de RNF06 continua em aberto — só o texto do PDF do
TCC1 pode confirmar isso").

## 2026-08-17 — SonarCloud adiado até o primeiro repositório ter código

**O que mudou**: o setup do SonarCloud (criar organização, os 6 projetos, o secret `SONAR_TOKEN` e
a variable `SONAR_ORGANIZATION` em cada repositório GitHub) fica **deliberadamente adiado** até o
primeiro repositório de aplicação ter código — na prática, `services/auth-service/feat-001`. Não é
mais listado como pendência de setup em aberto, e sim como um passo agendado.

**Por quê**: decisão do usuário. Nenhum dos 6 repositórios de aplicação tem commit, então o passo
5 da CI não roda de verdade em lugar nenhum hoje — a "falha" seria em um workflow que nunca é
disparado. `infra/` (único repo com código) não usa SonarCloud por design (sem código de
aplicação para analisar), então nada está sem cobertura de análise agora. Descartada a opção de
tornar o passo não-bloqueante (`continue-on-error`): enfraqueceria o gate acordado em
[[CONVENTIONS]]/[[TESTING]] de forma permanente para resolver um problema temporário.

**Impacto**: [[CI-CD]] seção "Setup pendente" (passos 2–4 reetiquetados como agendados para
`auth-service/feat-001`, não pendência aberta). Nenhuma mudança nos 6 `ci.yml` — a configuração
(`projectKey` = nome do repositório, org via `vars`, token via `secrets`) já está correta e foi
reconferida nesta sessão.

**Corrigido junto, achado da mesma conferência**: `apps/web/sonar-project.properties` e
`services/telegram-integration/sonar-project.properties` apontavam para
`.github/workflows/web.yml` e `.github/workflows/telegram-integration.yml` num comentário —
caminhos da época do monorepo, que deixaram de existir na reestruturação de 2026-08-02 (hoje é
`.github/workflows/ci.yml` dentro de cada repositório).

## 2026-08-17 — Templates de issue do Jira, separados do script

**O que mudou**: as primeiras issues geradas pelo `tools/jira_story.py` (story `SV-1` e
sub-tasks `SV-2`…`SV-8`) saíram ilegíveis para uma pessoa: título igual ao texto inteiro do passo
(um deles com 140 caracteres), descrição em parágrafos corridos, e o `plan_review` cru — um bloco
técnico de ~2 mil caracteres — despejado no meio da story. O usuário pediu issues curtas,
detalhadas e "que pareçam escritas por humanos", sugerindo templates. Feito:

- **`tools/jira_templates.py`** (novo): monta o Atlassian Document Format com painéis, listas
  ordenadas, `rule` e blocos recolhíveis (`expand`). Separado de `jira_story.py`, que continua
  cuidando só de ler o harness e falar com a API — mudar o visual da issue não deve exigir tocar
  na lógica de rede.
- **Campos de apresentação no `feature_list.json`**, todos opcionais: na feature, `goal` e
  `scope`; na subtask, `detail`, `checklist`, `validation` e `owner`. `name` passa a ser título
  curto — o texto longo vai nos campos novos. `owner: usuario` pinta um aviso na issue de que
  aquele passo é manual (UI web) e não pode ser executado pelo agente.
- **`--update`** no script: reescreve `summary`/`description` de issues já criadas, e **só**
  esses dois campos — status, sprint, responsável e estimativa são decididos fora do template e
  não podem ser sobrescritos por um re-render.
- Estrutura da story: objetivo em painel no topo → o que entra → passos numerados (com a chave de
  cada sub-task) → dependências → veredito do plan review + achados resumidos, com o texto
  completo recolhido → definição de pronto → rastreabilidade e diagrama de branches recolhidos.

**Por quê**: o Jira é o artefato que a banca e qualquer pessoa de fora abrem primeiro; um board
onde o título da tarefa não cabe na coluna não serve para essa finalidade. A informação técnica
não foi removida — foi movida para dentro de `expand`, que é o que o ADF oferece para separar
"o que preciso ler agora" de "o que preciso poder consultar".

**Impacto**: `tools/jira_templates.py` (novo), `tools/jira_story.py` (usa os templates, ganha
`--update` e força UTF-8 no stdout — o console do Windows abre em cp1252 e quebrava ao imprimir
acento), `CLAUDE.md` da raiz (regra de trabalho nova), `infra/feature_list.json` (`feat-003`
reescrita nos campos novos, 7 sub-tasks com título curto). `SV-1`…`SV-8` reescritas no Jira com
`--update` e conferidas via `GET /rest/api/3/issue`.

**Nota**: os campos novos são de apresentação, não de decisão. A fonte da verdade continua sendo
o `feature_list.json`, e a direção continua sendo harness → Jira.

**Emenda (2026-08-17, mesmo dia) — `--sync-status` e o ciclo de vida do board**: o espelho estava
incompleto — as issues ficavam em `Backlog` mesmo com a feature `in-progress` e duas subtasks já
`done`. Adicionado `--sync-status`, que transiciona story e sub-tasks via
`POST /rest/api/3/issue/{key}/transitions`, resolvendo a transição pelo *nome* do status de
destino (ids variam por projeto).

O board do projeto `SV` tem cinco status que reproduzem exatamente o Kanban do TCC 1 (`Backlog`,
`To Do`, `In Progress`, `Review`, `Done` ↔ Opções, Selecionado, Em Execução, Verificação,
Entregue — ver [[REQUIREMENTS]] "Método de trabalho"). A primeira versão mapeava só os três
estados do harness e tratava `To Do`/`Review` como território humano. **O usuário definiu o ciclo
completo**, e os cinco status passaram a ser **derivados** da combinação feature + subtasks, sem
nenhum campo novo:

| Estado no harness | Story | Sub-tasks |
|---|---|---|
| feature `not-started` | `Backlog` | `Backlog` |
| feature `in-progress`, nenhuma subtask iniciada | `To Do` | `To Do` |
| feature `in-progress`, alguma subtask iniciada | `In Progress` | por status da subtask |
| feature `in-progress`, todas as subtasks `done` | `Review` | `Done` |
| feature `done` | `Done` | `Done` |

**`Review` é o estado "código pronto, falta provar"**: a story permanece lá até a suíte planejada
ter rodado — unitários, integração e E2E, os aplicáveis àquele harness (ver [[TESTING]]) — e a
Definição de Pronto estar satisfeita com `evidence` preenchida. Isso é o que autoriza a feature a
virar `done` no JSON, e só então a story sai de `Review`. Consequência: `Review` não é decorativo,
é o ponto onde o gate de teste do TCC 1 (coluna "Verificação", WIP máx 1, cobertura > 80%) fica
visível no board.

Com o ciclo derivado, a exceção anterior de "preservar o que foi movido à mão" foi **removida**:
todos os cinco status têm agora origem no JSON, e preservar movimento manual criaria uma segunda
fonte de verdade — exatamente o que a decisão de 2026-08-03 (harness → Jira) proíbe. Lógica
verificada com uma tabela dos sete cenários do ciclo antes de tocar o board.

**Emenda 2 (2026-08-17, mesmo dia) — `evidence` vira comentário na story**: o `--sync-status`
publica o campo `evidence` da feature como comentário na issue, assim que ele estiver preenchido.
Fecha o último pedaço do espelho que só existia no JSON: a issue passa a carregar, nela mesma, o
registro de que a Definição de Pronto foi cumprida — que é o que a banca abre junto da story.

O comentário leva um marcador no rodapé (`harness-evidence:<harness>:<feature>:<hash8>`) com hash
do próprio texto. Isso dá duas propriedades: rodar o sync repetidamente **não duplica** o
comentário, e uma `evidence` editada no harness gera um **comentário novo** em vez de sobrescrever
o anterior — o histórico da issue preserva as duas versões, que é o comportamento correto para um
registro de rastreabilidade. Testado ponta a ponta em `SV-1` (publicação, idempotência e
versionamento após edição), com os comentários de teste removidos ao final via
`DELETE /rest/api/3/issue/{key}/comment/{id}`.

## 2026-09-03 — huashu-design adicionado; correção sobre `/impeccable init`

**O que mudou**: usuário pediu que Impeccable, taste-skill e **huashu-design** (terceira
ferramenta, nova neste projeto — protótipos/slides/animação HTML com "20 filosofias de design"
e review em 5 dimensões próprios) sejam usadas sempre que houver tarefa de frontend, e pediu
para rodar `/impeccable init`.

huashu-design entrou sob a **mesma restrição** já valendo para as outras duas desde 2026-08-02:
prototipagem/QA permitida, decisão de design não — a paleta/tema do prompt vem de
`docs/DESIGN-SYSTEM.md`, nunca da filosofia default da ferramenta, e o resultado nunca é
especificação, só rascunho descartável.

**Correção real, não extensão**: a regra de 2026-08-02 dizia *"não rodar `/impeccable init` (gera
`DESIGN.md` próprio)"* — presunção nunca verificada contra a ferramenta. Consultado o `SKILL.md`
oficial do Impeccable (`pbakaus/impeccable`, `.claude/skills/impeccable/SKILL.md` e
`reference/init.md`) via `gh api`: **`init` não escreve `DESIGN.md`**, nunca escreveu — grava só
`PRODUCT.md` (contexto de produto: público, propósito, restrições, voz). Citação literal do
skill: *"init captures durable product truth in PRODUCT.md. It does not invent a visual world and
does not write DESIGN.md"*, e *"Never silently overwrite an existing file or offer DESIGN.md
during init."* Quem escreve `DESIGN.md` é `/impeccable document` (extrai do código) ou o fluxo
`new-work` (workshop interativo) — comandos distintos, nunca acionados por `init`.

Isso significa que o risco real nunca esteve em `init` — estava em deixar `document`/`new-work`
rodarem **sem** um `DESIGN.md` nosso já existindo. O próprio skill resolve isso sozinho, desde
que o arquivo já exista: *"If a DESIGN.md already exists, do not silently overwrite it. Show the
user the existing file first. STOP and call AskUserQuestion. The choice is refresh, overwrite, or
merge."* — nunca sobrescreve em silêncio.

**Decisão nova, substituindo a proibição de `init`**: `apps/web/DESIGN.md` é **pré-escrito** a
partir de `docs/DESIGN-SYSTEM.md`, no [formato oficial `DESIGN.md`](https://github.com/google-labs-code/design.md)
— front-matter YAML (`colors`, `typography`, `rounded`, `spacing`, `components`) seguido das 8
seções canônicas na ordem fixa (`Overview`, `Colors`, `Typography`, `Layout`,
`Elevation & Depth`, `Shapes`, `Components`, `Do's and Don'ts`; seções não aplicáveis podem ser
omitidas). Com o arquivo já existindo, qualquer tentativa futura de `document`/`new-work` gerar
um `DESIGN.md` cai no fluxo `refresh/overwrite/merge` — a sessão recusa `overwrite`. `init` passa
a ser seguro de rodar sem ressalva.

**Por quê**: honestidade de fonte prevalece sobre manter uma regra já escrita — a proibição de
`init` estava resolvendo um problema que `init` não causa, e não resolvia o problema real (que é
`document`/`new-work` sem `DESIGN.md` prévio). Verificado contra o `SKILL.md` primário do
repositório, não memória/suposição.

**Impacto**: [[DESIGN-SYSTEM]] seção "QA visual e prototipagem" (reescrita — 3 ferramentas, regra
de `init` corrigida, mecanismo do `DESIGN.md` pré-escrito documentado), `apps/web/CLAUDE.md`
(mesmo bullet), `apps/web/feature_list.json` (`feat-001` — instalação das 3 + pré-escrita do
`DESIGN.md` como passo explícito, logo após `npx impeccable install`).

**Em aberto**: a pré-escrita de fato (converter o conteúdo de `DESIGN-SYSTEM.md` para o formato
`DESIGN.md`) só acontece quando `feat-001` de `apps/web` for implementado — `.impeccable/` e
`DESIGN.md` vivem dentro daquele projeto Angular, que ainda não existe.

## 2026-09-03 — Templates do Jira alinhados ao padrão de `oficina/tools`

**O que mudou**: usuário apontou `D:\UTFPR\oficina\tools` — outro projeto (roadify) com uma
versão mais madura dos mesmos dois scripts (`jira_story.py`/`jira_templates.py`, mesmo desenho de
2026-08-17) — e pediu que a criação de tarefas e o comentário de evidência seguissem o mesmo
leiaute, por legibilidade. Comparado os dois arquivos linha a linha e portados os ganhos que
fazem sentido no nosso schema (não portados: `_ficha`/`design_link`/`track`/`sprint`/`estimate_h`
— campos daquele projeto sem equivalente aqui):

1. **`rich()`**: trecho entre `crases` em qualquer parágrafo vira nó de código automaticamente.
   Antes, `` `./init.sh` `` saía como texto plano — o comando não se destacava da prosa ao redor.
2. **`evidence` aceita objeto estruturado** — `{"resumo": ..., "secoes": [{"titulo": ...,
   "itens": [...]}]}` — além da string simples já suportada (mantida para não quebrar evidência
   já registrada). O comentário sai com um subtítulo por seção em vez de um parágrafo único
   concatenado. `evidence_marker()` passa a fazer hash de JSON canônico quando o campo é objeto.
3. **`_review_section` simplificado**: a story deixa de repetir veredito + achados do
   `plan_review` quando ele está preenchido — não mostra nada nessa seção. Motivo (comentário no
   próprio `oficina/tools`, adotado aqui): os achados do Plan Reviewer já viraram subtask (é
   assim que este harness já trabalha desde 2026-08-03), então repeti-los na story duplicaria a
   mesma decisão. O aviso "Plan Review pendente" continua aparecendo quando o campo está vazio.
   Texto integral do `plan_review` continua no `feature_list.json` — não perdido, só não
   duplicado na issue.
4. **`_texto()`/`_lista()`**: helpers que evitam título órfão quando o campo está vazio,
   substituindo blocos `if scope: nodes += [...]` repetidos por chamada única.

**Não portado, por não ter equivalente no nosso schema**: `_ficha()` (sprint/trilha/estimativa —
este harness não tem conceito de sprint), `design`/`design_link` (canvas de design do roadify —
nós já temos `docs/DESIGN-SYSTEM.md` como fonte única), `REPO_TAG`/`short_title()` (o
equivalente aqui já existe via `--harness` + label, um `feature_list.json` por repositório em vez
de um só cross-repo), `snippet`/`language` (bloco de código longo em subtask — nenhuma subtask
deste harness precisou disso até agora; adicionar o campo fica para quando surgir necessidade
real).

**Por quê**: usuário apontou a implementação de referência explicitamente — não é escolha
estética minha, é alinhar com um padrão já em uso em outro projeto dele.

**Impacto**: `tools/jira_templates.py` (`rich()`, `_texto`/`_lista`/`_passos_section` novos,
`_split_review` removido — ficou morto), `tools/jira_story.py` (`post_evidence` corrigido para
aceitar `evidence` como objeto, não só string), `CLAUDE.md` da raiz (bullet reescrito).
`infra/feature_list.json` (`feat-003.evidence` convertida de string para o formato estruturado,
como demonstração real — não é obrigatório converter evidência antiga, só feito aqui para
validar o comentário no Jira de verdade). Aplicado em produção: `SV-1`…`SV-9` reescritas com
`--update`, evidência republicada com `--sync-status` (nova versão do comentário, já que o
conteúdo mudou de string para objeto — comportamento correto de versionamento, não bug).
Verificado via `GET /rest/api/3/issue` que os blocos ADF (`panel`/`heading`/`bulletList`) saíram
como esperado antes de considerar a tarefa concluída.

## Ver também

- [[ARCHITECTURE]] — decisões consolidadas como definitivas (não reinterpretar sem nova
  confirmação do usuário).
- [[DATA-MODEL]] — ERDs atualizados refletindo as decisões acima.
- [[API-CONTRACTS]] — modelo de confiança e headers atualizados.
- `progress.md` (raiz) — log de sessão, cronológico mas não organizado por decisão; este arquivo
  é o índice normativo, `progress.md` é o diário.

## 2026-08-02 — Plugins de agente para todos os repositórios: Caveman + claude-code-skills

**O que mudou**: usuário pediu dois plugins de Claude Code aplicados a todos os 7 repositórios
(não código de aplicação — configuração do próprio agente):

- **[Caveman](https://github.com/JuliusBrussee/caveman)**: comprime as respostas do agente
  (~65% menos tokens, mesma precisão técnica). Instalado via caminho nativo de plugin do Claude
  Code (não o script `curl|bash`, que exigiria confiar em código não revisado):
  `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`.
- **[claude-code-skills](https://github.com/levnikolaevich/claude-code-skills)**: marketplace
  com 18 skills em 7 suítes (Review, Codebase Audit, Optimization, Testing, Product Discovery,
  Maintainer, Architecture). Usuário optou por instalar as 7 suítes inteiras, não uma seleção.
  `claude plugin marketplace add levnikolaevich/claude-code-skills` + um `claude plugin install
  <suíte>@levnikolaevich-skills-marketplace` por suíte.

**Ressalva registrada** (mesmo padrão do Impeccable/taste-skill, ver entrada de QA visual
acima): a **Architecture Suite** deste marketplace (Architecture Decision Recorder, Current
Architecture Documenter, etc.) não deve gerar decisão/diagrama paralelo ao que já existe em
`docs/DECISIONS-LOG.md`/`docs/ARCHITECTURE.md`/`docs/DATA-MODEL.md` — usar só para conferir
consistência do que já está escrito, nunca como fonte nova, pelo mesmo motivo de duas fontes de
verdade divergentes.

**Por quê**: decisão explícita do usuário; instalação completa das 7 suítes (em vez de uma
seleção) também foi escolha explícita do usuário, depois de eu sinalizar quais pareciam mais
aplicáveis desde já (Review + Testing) e quais menos (Product Discovery, Maintainer).

**Impacto**: nenhum arquivo de código alterado — mudança é de configuração do agente
(`~/.claude/` ou equivalente), fora do escopo de qualquer um dos 7 repositórios.

**Em aberto — bloqueado por limitação de ambiente** *(resolvido, ver emenda abaixo)*: eu (sessão
rodando como extensão nativa do VSCode) não tenho acesso ao binário `claude` (CLI) neste
ambiente — `command -v claude` falha tanto em Bash quanto PowerShell, e `~/.claude/plugins/`
local só contém `blocklist.json` (sem registro de marketplace/plugin instalado). Não é seguro
replicar a instalação editando esses arquivos manualmente (o comando real busca e registra o
conteúdo do plugin a partir do GitHub).

**Emenda 1 (2026-08-02, mesmo dia)**: usuário pediu que as duas skills sejam **prioritárias em
todas as etapas do desenvolvimento** (arquitetura, desenvolvimento, testes, validação), não só
instaladas passivamente. Criada `docs/AGENT-SKILLS.md` com o mapeamento completo de qual skill
usar em qual etapa (mantendo a ressalva acima sobre a Architecture Suite). Propagado para
`CLAUDE.md` da raiz (novo passo no "Fluxo de início de sessão" — `Plan Reviewer` antes de
codificar; novo bullet em "Regras de trabalho"; novo item na "Definição de pronto" —
`Delivery Reviewer`/`Test Suite Auditor`) e para o `CLAUDE.md` dos 7 harnesses (bullet + item de
Definição de Pronto específico, incluindo `Persistence Auditor` nos 3 serviços Java com banco
próprio).

**Emenda 2 (2026-08-02, mesmo dia, resolve o bloqueio de ambiente)**: encontrado
`claude.exe` em `C:\Users\eduar\.local\bin\claude.exe` (versão 2.1.195) — instalado, mas
**não estava no PATH** (por isso `command -v claude` falhava). Rodado com caminho completo:

```
claude plugin marketplace add JuliusBrussee/caveman
claude plugin install caveman@caveman
claude plugin marketplace add levnikolaevich/claude-code-skills
claude plugin install review-suite@levnikolaevich-skills-marketplace
claude plugin install codebase-audit-suite@levnikolaevich-skills-marketplace
claude plugin install optimization-suite@levnikolaevich-skills-marketplace
claude plugin install testing-suite@levnikolaevich-skills-marketplace
claude plugin install product-discovery-suite@levnikolaevich-skills-marketplace
claude plugin install maintainer-suite@levnikolaevich-skills-marketplace
claude plugin install architecture-suite@levnikolaevich-skills-marketplace
```

**Resultado**: os 8 plugins instalados com sucesso, `claude plugin list` confirma todos
`enabled`, escopo `user` (vale para qualquer projeto nesta máquina, não só estes 7
repositórios — mais amplo do que "todos os repositórios" pedido originalmente, mas é o
comportamento padrão do escopo `user` do Claude Code). Os itens de skill nas Definições de
Pronto (antes condicionados a "se as skills já estiverem instaladas") passaram a incondicionais
em `CLAUDE.md` da raiz e dos 7 harnesses. Sessões já abertas antes da instalação (como esta)
podem precisar reiniciar para enxergar os plugins carregados.

**Para o usuário usar `claude` no terminal normalmente**: adicionar `C:\Users\eduar\.local\bin`
ao PATH do usuário no Windows (Configurações → Sobre → Configurações avançadas do sistema →
Variáveis de Ambiente → `Path` do usuário → adicionar a entrada), depois reabrir o terminal.

## 2026-08-03 — Postgres por instância, topologia RabbitMQ e DLQ do ambiente local

Quatro decisões tomadas ao implementar `infra` `feat-001` (`epic-001` da raiz) — o
`docker-compose.yml` obrigou a fechar lacunas que nem o TCC1 nem este vault endereçavam.

**1. Postgres: uma instância (container) por serviço, não três bancos no mesmo servidor.**

*O que mudou*: [[ARCHITECTURE]] e [[infra]] diziam "uma **instância lógica** por serviço", o que
admitia ler como um único Postgres com três bancos; [[DATA-MODEL]] já dizia "instâncias Postgres
distintas". Ambiguidade fechada pelo usuário nesta sessão: três containers —
`postgres-auth` (5432), `postgres-bets` (5433), `postgres-stats` (5434), volume próprio cada um.
As duas notas foram corrigidas no mesmo commit.

*Por quê*: escolha do usuário. Isolamento real (nenhum serviço tem sequer conectividade com o
banco do outro, não só falta de permissão) e fidelidade ao diagrama de implantação do TCC1 —
relevante para a banca, que avalia justamente a arquitetura de microsserviços. Custo aceito:
~3x memória local em relação a um container só.

**2. Topologia RabbitMQ nomeada e versionada como contrato.**

*O que mudou*: nenhuma nota nomeava exchange/fila. Definidos `bets.events` (topic),
`stats.bet-events` (quorum), `bets.events.dlx` (fanout), `stats.bet-events.dlq` (quorum), routing
keys `bet.created`/`bet.settled` — tabela completa em [[API-CONTRACTS]], criada por
`infra/rabbitmq/definitions.json`.

*Por quê*: é contrato compartilhado entre [[bets-service]] e [[stats-service]], não detalhe de
infraestrutura. `x-delivery-limit` (o mecanismo que implementa o "limite de tentativas" dos
diagramas do TCC1) **só existe em quorum queue** — classic queue reentrega indefinidamente e
nunca chegaria à DLQ sozinha. Como a topologia nasce pronta no broker, os dois serviços precisam
consumir/publicar **sem redeclarar**: uma redeclaração com argumentos diferentes derruba o canal
com `PRECONDITION_FAILED` em loop. Por isso a tabela está em [[API-CONTRACTS]] e não só no
compose.

*Impacto*: [[API-CONTRACTS]] nova seção "Topologia RabbitMQ", [[infra]], `epic-003`/`epic-004`.

**3. Definições aplicadas pós-boot, não por `load_definitions`.**

*O que mudou*: a topologia é aplicada por um container one-shot `rabbitmq-init`
(`infra/rabbitmq/apply-definitions.sh`, `POST /api/definitions`) depois do broker ficar
`healthy`, em vez de `load_definitions` no `rabbitmq.conf`.

*Por quê*: a documentação oficial do RabbitMQ é explícita — *"if a blank (uninitialised) node
imports a definition file, it will not create the default virtual host and user"*. Com
`load_definitions`, o broker subiria sem vhost `/` e sem usuário, e o healthcheck
`rabbitmq-diagnostics check_running` **ainda passaria** (o nó está rodando): falha silenciosa que
só apareceria no `epic-003`, ao primeiro serviço tentar conectar. Aplicando pós-boot, o usuário
default continua vindo de `RABBITMQ_DEFAULT_USER/PASS` e nenhum segredo precisa ser versionado
dentro do `definitions.json`. Encontrado pelo `Plan Reviewer` antes de qualquer código ser
escrito.

**4. DLQ com estratégia `at-most-once` (default) no ambiente local — tradeoff explícito.**

*O que mudou*: [[infra]] descrevia a DLQ como garantia de que a mensagem "não é descartada". A
estratégia default do RabbitMQ para dead-lettering é `at-most-once`, que **pode** perder a
mensagem no trajeto até a DLQ em falha de broker.

*Por quê*: `at-least-once` exige `overflow: reject-publish`, que muda comportamento visível do
produtor ([[bets-service]] passa a ter publicação rejeitada quando a fila enche) — complexidade
desproporcional para ambiente de desenvolvimento. Tradeoff aceito e registrado em vez de
silencioso. Reavaliar se `feat-002` (`epic-007`) mostrar perda real de mensagem.

## 2026-08-03 — Jira como espelho do backlog (reverte "este projeto não usa Jira")

**O que mudou**: o TCC1 não mencionava ferramenta de gestão, e este harness tinha decidido
explicitamente **não** usar Jira — o id da feature no `feature_list.json` fazia o papel de
chave de tarefa (ver entrada de 2026-08-02 sobre o modelo de branch, e [[CONVENTIONS]] seção
"Git"). Decisão do usuário nesta sessão: toda feature passa a ter uma **story no Jira**,
criada a partir do harness, contendo a análise do `Plan Reviewer` como descrição da tarefa.

**Direção do fluxo, que é o ponto que evita o problema clássico de dois backlogs**: harness →
Jira, nunca o contrário. O `feature_list.json` de cada repositório continua sendo a fonte da
verdade de status, dependências, WIP, `plan_review` e `evidence`; o Jira é espelho. Nenhuma
sessão consulta o Jira para decidir o que fazer, e divergência entre os dois não é bug do
harness — o JSON está certo por definição.

**Branch e commit passam a usar a chave do Jira** (decisão do usuário, corrigindo a proposta
inicial desta mesma sessão, que mantinha o id do `feature_list.json`): branch é
`feature/SV-12`/`bugfix/SV-31-<slug>`, e a mensagem de commit cita **os dois** identificadores
(`(SV-12 / feat-004)`) — a chave liga o commit à story, o id liga à fonte da verdade. Isso impõe
uma ordem no fluxo: a story tem de existir antes da branch, então `Plan Reviewer` →
`plan_review` preenchido → `jira_story.py` → `git checkout -b`. A objeção de "sessão sem rede
não saberia nomear a branch" não se aplica, porque o script grava a chave no campo `jira` da
feature — depois de criada, a chave vive no JSON e não exige consultar o Jira. `spike/<slug>`
continua sem chave: não tem feature nem story associada.

**Por quê**: o valor pedido é rastreabilidade e evidência de processo ágil para a banca — não
substituir o mecanismo que efetivamente dirige o trabalho, que já é verificável localmente
(`init.sh`, campos do `feature_list.json`) e não depende de serviço externo.

**Como**: `tools/jira_story.py` (stdlib apenas, sem dependência nova) lê o `feature_list.json`
do harness, monta a story em Atlassian Document Format — contexto, dependências, análise do plan
review, ponteiro para a Definição de Pronto daquele harness — cria via `POST /rest/api/3/issue`
e grava a chave de volta no campo `jira` da feature. `--dry-run` imprime o payload sem chamar a
API. O script vive na **raiz**, que não é repositório Git, junto das credenciais
(`tools/.jira.env`, modelo em `tools/.jira.env.example`) — nenhum dos 7 repositórios versiona
token ou sabe da existência do Jira.

**Subtasks (mesma sessão, refinamento)**: cada feature ganhou um array `subtasks` no
`feature_list.json`, espelhado como sub-tasks da story no Jira. Os itens saem do veredito do
`Plan Reviewer`, que já entrega os menores passos ordenados por dependência — não é uma
decomposição inventada à parte.

**O modelo de branch passou de 3 para 4 níveis** (decisão do usuário, corrigindo a proposta
inicial desta sessão, que mantinha uma branch só por story): `main` ← `develop` ←
`feature/<chave-da-story>` ← `subtask/<chave-da-subtask>`. Cada branch leva a chave da sua
própria issue; a branch da subtask sai da branch da story, não de `develop`; o merge sobe um
nível por vez, sempre `--no-ff`.

O aninhamento por barra (`feature/SV-12/SV-13`) foi descartado por **restrição do Git**, não por
gosto: refs são arquivos em `.git/refs/heads/`, então `feature/SV-12` (arquivo) e
`feature/SV-12/` (diretório) não coexistem — o segundo `checkout -b` falha com `cannot lock
ref`. Daí o prefixo `subtask/`; o vínculo pai/filho fica no `feature_list.json` e na própria
sub-task do Jira, que já aponta para o parent.

**Dois gates de peso diferente** (decisão do usuário): merge `subtask/` → branch da story exige a
**pipeline de CI do GitHub passando** naquele PR — changelog, i18n, build, testes — mas não o
`./init.sh` local nem as skills de revisão, porque estado intermediário raramente passa no gate de
cobertura (um `docker-compose.yml` sem o RabbitMQ ainda não sobe; `mvn verify` num serviço pela
metade também não). O gate completo (`init.sh`, `Delivery Reviewer`, `Test Suite Auditor`,
`evidence`, CI inteira) roda uma vez, na story, antes de `develop`.

**Duas correções que isso obrigou no `ci.yml` dos 7 repositórios**, porque a pipeline dispara em
`pull_request` sem filtro de branch e portanto passou a rodar também nos PRs de subtask:

1. **SonarCloud pulado em PR de subtask** (condição sobre `github.base_ref`). O quality gate mede
   *código novo*: uma feature pela metade — código escrito, testes ainda na subtask seguinte —
   reprovaria sem indicar defeito real, bloqueando o merge por um motivo que não é qualidade. A
   análise acontece na story, com a feature completa.
2. **Changelog validado em todo PR, inclusive de subtask** — decisão do usuário de que cada
   subtask carrega a própria linha em `[Unreleased]`, acumulando na branch da story até o merge
   em `develop` (a proposta inicial era uma entrada só, por feature).

**Impacto**: `CLAUDE.md` da raiz (nova regra em "Regras de trabalho" + seção Git reescrita),
[[CONVENTIONS]] seção "Git" (nome de branch e formato de commit), `feature_list.json` dos 7
harnesses (campos `jira` e `subtasks`, irmãos de `plan_review`), `tools/jira_story.py`,
`tools/.jira.env.example`. `infra` `feat-001` teve as 8 subtasks preenchidas retroativamente, a
partir do que foi de fato entregue, para servir de modelo de granularidade. **Exceção histórica**: `infra` `feat-001` foi implementada e mergeada
antes desta decisão, na branch `feature/feat-001` e sem story — não renomear retroativamente.

**Pendente**: credenciais ainda não configuradas — nenhuma story foi criada até agora. O primeiro
uso real será na primeira feature de `epic-002` (`auth-service`).

## 2026-08-19 — Raiz vira o 8º repositório (`sv-harness`), reverte "a raiz nunca vai para o GitHub"

**O que mudou**: a raiz deste diretório passa a ser um repositório Git próprio, hospedado em
`https://github.com/eimmig/sv-harness.git`. Reverte a última frase da entrada
[2026-08-02 — Topologia](#2026-08-02-topologia-7-repositorios-independentes-nao-monorepo), que
dizia que a raiz "não é um repositório Git e nunca vai para o GitHub". O resto daquela decisão
não muda: continua **não sendo monorepo**, e continuam existindo 7 repositórios de código
independentes (6 serviços + `infra/`), cada um com seu próprio remote e sua própria CI.

O `sv-harness` versiona **só docs + harness**: `CLAUDE.md`, `docs/` (este vault), `feature_list.json`
(epics), `progress.md`, `session-handoff.md`, `init.sh` e `tools/` (scripts de Jira/Sonar). O
`.gitignore` da raiz exclui `/services/`, `/infra/` e `/apps/`, então nenhum código de aplicação
entra aqui — o repositório da raiz **não** é pai dos outros e não os enxerga.

**Por quê**: o vault e o harness são o artefato de método do TCC — as decisões, os requisitos, o
backlog de epics e o próprio processo de trabalho. Deixá-los só em disco local significava
nenhum histórico de como as decisões evoluíram (justamente o que `DECISIONS-LOG.md` existe para
rastrear) e nenhum backup fora da máquina. Não foi motivado por limitação técnica.

**Impacto**:
- `.gitignore` da raiz é obrigatório e normativo. Além de `/services/`, `/infra/` e `/apps/`,
  ignora `__pycache__/` (recursivo — os `.pyc` de `tools/` ficam em `tools/__pycache__`, não na
  raiz), `*.env`/`.env.*` com exceção de `*.env.example` (os segredos reais de `tools/.jira.env`
  e `tools/.sonar.env` **nunca** podem ser commitados), o estado de janela do Obsidian
  (`**/.obsidian/workspace.json`, `workspace-mobile.json`, `cache`) mantendo a config
  compartilhável do vault versionada (`app.json`, `appearance.json`, `core-plugins.json`,
  `graph.json`), e `**/.claude/settings.local.json`.
- **Gotcha do `.gitignore` que custou uma rodada**: padrão com barra no meio é ancorado na raiz
  do repositório, não recursivo. `.obsidian/workspace.json` **não** pega
  `docs/.obsidian/workspace.json`; precisa de `**/.obsidian/workspace.json`. Mesma armadilha em
  `/__pycache__`, que não pegava `tools/__pycache__`.
- **Por que `/apps/` precisa estar ignorado**: `apps/web/` tem `.git` próprio, igual a
  `services/*`. Sem a regra, `git add .` na raiz grava um **gitlink de submódulo órfão**
  (mode 160000) apontando para um SHA que nenhum clone consegue resolver, porque não há
  `.gitmodules` nem remote registrado. Falha silenciosa: `git status` não reclama depois do
  commit.
- Nenhuma pipeline de CI na raiz — não há código de aplicação nem texto de usuário para build,
  testes, i18n ou SonarCloud validarem. `docs/CI-CD.md` atualizada.
- `CLAUDE.md` da raiz (seção "Harness multinível", passo 8 do Startup Workflow) e
  `docs/ARCHITECTURE.md` atualizados no mesmo commit.

**Modelo de branch do `sv-harness`** (decidido pelo usuário na mesma sessão): **uma única
branch `master`, com commits diretos**. Não segue o `main` ← `develop` ← `feature/<chave-jira>`
← `subtask/<chave-jira>` dos 7 repositórios de código (ver `docs/CONVENTIONS.md` seção "Git"),
e isso é intencional, não uma pendência: aquele fluxo existe para separar código estável de
código em integração e para pendurar gates de CI e stories do Jira em cada nível — nada disso se
aplica a um repositório de docs + harness, que não tem build, não tem pipeline e cujas mudanças
não têm um estado "instável" a isolar de um estado "entregável". A branch é `master` (não `main`)
porque foi assim que o repositório foi inicializado; nenhuma feature ou story do Jira aponta para
ela, então não há valor em renomear.

## 2026-09-04 — `mustChangePassword` não bloqueia login, reverte a intenção original da entrada de 2026-08-02

**O que mudou**: a entrada [2026-08-02 — Modelo de tenant multiusuário](#2026-08-02-modelo-de-tenant-multiusuario-e-provisionamento-de-banco),
item 3, previa que "o backend bloqueia qualquer outra ação até a senha ser trocada" para o admin
recém-criado por provisionamento de tenant (`mustChangePassword = true`). `feat-005` (login,
`services/auth-service`) implementou o oposto: login **sempre autentica** se a senha bater,
independente de `mustChangePassword` — o campo só é devolvido no corpo da resposta
(`{"token": "...", "mustChangePassword": true|false}`) para o frontend decidir a UX (ex.: forçar
tela de troca de senha). Nenhum bloqueio real no backend.

**Por quê**: não existe endpoint de troca de senha em nenhum `feature_list.json` do backlog atual
(nem `auth-service`, nem planejado em `apps/web`). Implementar o bloqueio como a entrada original
previa deixaria o admin recém-criado por `feat-003` permanentemente trancado — autenticado o
suficiente para saber que precisa trocar a senha, mas sem nenhuma rota que aceite a troca.
Decisão tomada com o usuário (`AskUserQuestion`) durante o Plan Review de `feat-005`: preferir a
opção que não bloqueia, adiando o bloqueio real para quando uma feature de troca de senha existir
no backlog.

**Impacto**:
- `docs/services/auth-service.md` seção "Modelo de tenant" atualizada no mesmo commit — o
  blockquote que citava a intenção de bloqueio agora aponta para este item, e a seção
  "Autenticação" documenta o contrato real de `POST /api/v1/auth/login`.
- Esta entrada não reescreve o texto de 2026-08-02 (histórico, fica como registro fiel da
  intenção original) — só reverte o resultado, mesmo padrão das demais entradas "reverte X"
  deste log.
- Item aberto: quando uma feature de troca de senha for criada (nenhuma reserva de id ainda em
  `services/auth-service/feature_list.json`), decidir se o bloqueio real volta a ser implementado
  ali, ou se a mitigação por si só (senha aleatória de alta entropia, nunca logada, só na resposta
  de `feat-003`) é considerada suficiente.
