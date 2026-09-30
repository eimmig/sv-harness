---
tags: [tcc, divergencias]
---

# Divergências em relação ao texto do TCC 1

Lista só o que o **texto do TCC 1** afirma e o sistema entregue **faz diferente**, para saber o
que ajustar ao transformar este material no TCC final. É um recorte enxuto de
[[DECISIONS-LOG]] (que guarda o histórico completo e o porquê de cada decisão); aqui cada linha é
"TCC diz X, foi feito Y, ajuste sugerido". Extensões que só **acrescentam** algo sem contradizer o
texto ficam na seção final.

Seções do TCC citadas conforme o PDF `TCC_1_Sistema_de_Apostas.pdf`.

## 1. Requisitos (seção 4.1)

| TCC 1 diz | Foi feito | Ajustar no texto |
|---|---|---|
| RF01/UC01: criar e gerenciar contas de usuário (nome, e-mail, senha); conta = usuário. | Conta é de uma **organização (tenant)** com vários usuários (`admin`/`member`). **Não há autocadastro**: o operador da plataforma cria o tenant (rota administrativa com `X-Admin-Api-Key`, que também cria o primeiro `admin`); só o admin cria os demais usuários. | RF01, UC01 e a Figura 2. Explicar tenant e papéis. |
| RF02: autenticar usuários. | Login por **e-mail + senha**. O e-mail é `usuario@<slug-do-tenant>` e o tenant é deduzido do domínio (não há campo de organização). Token PASETO leva `userId`, `tenantId` e `role`. Existe troca de senha (`POST /api/v1/auth/change-password`); o login **não** bloqueia por senha provisória. | RF02, seção 4.1 (PASETO). |
| RF09: métricas ROI, taxa de acerto, lucro acumulado. | Muito mais: contagem de vitórias/derrotas, odd média, saldo inicial/final, unidades, ROI sobre banca, profit em unidades, dias green/red, **drawdown máximo**, **Índice de Sharpe simplificado**, quebra diária, grade de drawdown mensal, curva vitalícia. | RF09 e a lista de métricas do resumo. Detalhe em [[estatisticas]]. |
| RF05: captura automática por canais externos (parsing de string). | Captura por **texto livre ou foto do bilhete (OCR Tesseract local)**, com extração heurística e **perguntas do bot** para os campos que faltam. Esporte, liga e mercado sempre vêm de lista numerada; se o catálogo do tenant estiver vazio o bot manda cadastrar no web. A data da aposta não é extraída: usa a data do dia. | RF05, seção 2.6.5 e 4.3.2.2. |
| RNF06 (escalabilidade) e a prosa de DLQ tratados como o mesmo tema. | DLQ/retry **não** é RNF06 (RNF06 fala de volume, não de falha). Não se criou RNF07: o mecanismo é verificado pela prosa da seção 4.1 do TCC. | Não citar RNF06 como justificativa da DLQ. |

## 2. Modelo de dados (seção 4.2)

| TCC 1 diz | Foi feito | Ajustar no texto |
|---|---|---|
| 4.2.1: o microsserviço de identidade usa banco global; só o núcleo transacional é schema-por-tenant. | **`auth-service` também é schema-por-tenant** (`USER` dentro do schema do tenant, sem coluna `tenantId`). Fora dos schemas há só um diretório no schema `public` (`TELEGRAM_LINK`, `PENDING_TELEGRAM_LINK`) para achar o tenant de um usuário do Telegram. E-mail é único **por tenant**. | Texto de 4.2.1 e a Figura 3. |
| Figura 3 (ER OLTP): `USER` com `name`, `email`, `passwordHash`; `TELEGRAM_ACCOUNT.userId`. | `USER` ganhou `role` e `mustChangePassword`. `BET.betType` virou enum (PRÉ/LIVE). Novas tabelas: `TEAM`, `TENANT_SETTINGS` (uma linha por tenant), `TELEGRAM_LINK`, `PENDING_TELEGRAM_LINK`. `BET` ganhou `createdByUserId`; `BET_RESULT` ganhou `settledByUserId` (trilha de auditoria, sem FK entre bancos). `team1`/`team2` viraram FK para `TEAM`, escopado por esporte. | Redesenhar a Figura 3; conferir o ERD atual em [[modelo-de-dados]]. |
| Figura 4 (OLAP): `FACT_BET` com `isWin`, `betCount`; 6 dimensões. | `FACT_BET` ganhou `status`; `profit`/`isWin` passaram a aceitar nulo (aposta pendente não entra nas métricas, RN06). Dimensão nova `DIM_TEAM` (chave `nome+esporte`). Tabela `PROCESSED_EVENT` para idempotência do consumo. | Figura 4 e a lista de dimensões em 4.2.2. |
| 4.2.3: chaves `usuario:{id}:dashboard:consolidado`, `usuario:{id}:estatistica:mensal:{ano}_{mes}`, `usuario:{id}:segmento:...` (em português, por usuário). | Chaves em inglês e **por tenant**: `tenant:{slug}:dashboard:consolidated` e derivadas. O `FACT_BET` é do tenant, não do usuário, então cache por usuário mostraria dashboards diferentes sem motivo de negócio. | Seção 4.2.3. |

## 3. Arquitetura e fluxos (seções 3.1 e 4.3)

| TCC 1 diz | Foi feito | Ajustar no texto |
|---|---|---|
| Rotas `/apostas`, `/estatisticas`; evento `ApostaCriada` (Figuras 6, 7, 8). | Superfície técnica **toda em inglês**: `/api/v1/bets`, `/api/v1/statistics`; eventos `BetCreated` e `BetSettled` (dois eventos distintos, com envelope `tenantId` + `userId`). UI e mensagens de erro em três idiomas (`pt-BR`, `en-US`, `es`). | Figuras 6, 7, 8 e o texto que cita rotas e evento. |
| Serviço de Integração chama o Serviço de Apostas direto (Figura 7). | O bot passa pelo **API Gateway** com credencial de serviço (`X-Service-Key` + `X-Telegram-User-Id`); o gateway consulta o `auth-service` para achar usuário e tenant. **Exceção**: a confirmação do vínculo (`/vincular <código>`) vai direto ao `auth-service`, sem gateway. | Figura 7. |
| API Gateway aparece só como caixa na Figura 5. | É um **serviço próprio** (Spring Cloud Gateway Server WebMVC): único validador do token PASETO e único que injeta `X-User-Id`, `X-Tenant-Id` e `X-User-Role`. Os outros serviços confiam nesses headers. | Descrever o gateway na seção 4.3.1. |
| 3.1.5 / 4.1: reentrega automática pelo RabbitMQ e DLQ; "nenhuma mensagem de aposta é descartada". | O RabbitMQ 4.3+ **não conta** `nack(requeue=true)` no `x-delivery-limit`, então a contagem de tentativas foi para a **aplicação** (`spring-retry`, 3 tentativas, 1 s); esgotadas, a mensagem é rejeitada e vai à DLQ por DLX. O `x-delivery-limit: 3` ficou só como defesa adicional. Filas são *quorum queues*; dead-lettering no modo padrão `at-most-once`. | Seção 3.1.5: descrever o retry como de aplicação. A frase "nenhuma mensagem é descartada" está **em revisão**, ver seção 6. |
| Figura 5: contêineres Docker orquestrados por Kubernetes. | Confirmado: manifests YAML puros em `infra/k8s/`, executando em **k3s** (servidor Debian) com imagens no **GHCR** e Ingress só para o gateway. Docker Compose continua como ambiente de desenvolvimento. | Citar k3s e GHCR na 4.3.1. |
| Serviço de Estatísticas monta o cache no Redis com Cache-Aside (Figura 8). | Igual. Diferença só nas chaves (seção 2) e no escopo por tenant. | Nada além das chaves. |
| Topologia: microsserviços com "bancos PostgreSQL isolados". | Um **container Postgres por serviço** (auth, bets, stats), cada um com volume próprio; dentro de cada instância há um schema por tenant. | Opcional: deixar explícito na 3.1.7. |
| Provisionar tenant novo: passo manual não descrito. | `POST /api/v1/admin/tenants` no `auth-service` cria schema e admin e **orquestra** a criação nos outros dois serviços. Falha parcial não é desfeita: a resposta traz `downstreamProvisioningFailures` e o operador repete a chamada do serviço que falhou (idempotente, 409 se já existe). | Se o texto descrever onboarding. |

## 3.1. Versões (Quadro 2)

| TCC 1 diz | Foi feito | Ajustar |
|---|---|---|
| Angular 21.x | Angular **22.x** (`^22.1`) | Atualizar o número no Quadro 2. |
| n8n "Online" | n8n **1.100.0 self-hosted** em contêiner | Atualizar o Quadro 2 e a seção 3.1.4. |
| Spring Boot 4.x, Java 25, Python 3.12+, RabbitMQ 4.x | Iguais (Spring Boot 4.1.1). | Nenhum. |

PostgreSQL 18.x e Redis 8.x (Quadro 2) passaram a ser as versões usadas: as imagens foram
atualizadas, não é mais uma divergência.

## 4. Método (seção 3.2)

| TCC 1 diz | Foi feito | Ajustar no texto |
|---|---|---|
| Kanban individual com **WIP máximo 1** no quadro todo. | WIP máximo 1 **por serviço** (permite trabalho paralelo entre serviços). Colunas do quadro Jira reproduzem as 5 do TCC (Backlog, To Do, In Progress, Review, Done), derivadas do `feature_list.json`. Cobertura mínima de 80% verificada em CI e no SonarCloud. | Seção 3.2 e a Figura 1. |
| Trabalho individual; sem menção a ferramentas de apoio. | Desenvolvimento com **agentes de IA** (Claude Code) seguindo um harness (arquivos `CLAUDE.md`, `feature_list.json`, skills de revisão) e **8 repositórios Git** independentes (6 serviços, `infra/` e o `sv-harness` de documentação), cada um com CI própria. | Mencionar em 3.2, se a banca esperar rastreabilidade do processo. |

## 5. Extensões que não contradizem o texto (citar como "além do proposto")

- Internacionalização completa (`pt-BR`, `en-US`, `es`).
- Papéis `admin`/`member` e trilha de auditoria por usuário.
- OCR de bilhete e conversa guiada no bot do Telegram.
- Métricas avançadas (drawdown, Sharpe, unidades, ROI sobre banca).
- Catálogo de times escopado por esporte (`TEAM`); jogadores ficaram fora.
- Marca **Arka** e identidade visual.
- Pipeline de CI/CD com versionamento semântico, imagens no GHCR e deploy no k3s.

## 6. Afirmações do TCC ainda sem evidência (atualizar após os testes de produção)

Estas frases do texto **ainda não foram provadas** pelo sistema e devem ser reescritas conforme
o resultado dos testes de carga e resiliência:

| Frase do TCC 1 | Situação |
|---|---|
| "O uso de DLQ garante que nenhuma mensagem de aposta seja descartada" (3.1.5). | Achado em teste local com 1 milhão de apostas: só ~40% dos eventos chegaram ao stats; filas e DLQ vazias. O publicador do `bets-service` não usava confirmação de publicação nem outbox. Em correção. |
| Escalabilidade horizontal, RNF06 e o objetivo específico "arquitetura visando escalabilidade horizontal". | Os manifests tinham 1 réplica fixa e nenhum autoscaler. Em correção (HPA). |
| Resposta de dashboard **abaixo de 300 ms** (3.1.6). | Ainda não medido com volume. |
