---
tags: [service, integration]
---

# telegram-integration

Python 3.12+ e n8n. Ver [[ARCHITECTURE]] para o panorama geral e [[REQUIREMENTS]] para RF05.
Harness de código em `services/telegram-integration/CLAUDE.md`.

## Responsabilidade

RF05 — captura automática de apostas via bot do Telegram. É o diferencial competitivo citado no
TCC frente às ferramentas concorrentes (Bet-Analytix, Meu Gestor de Banca, Stakemap, planilhas),
todas 100% manuais.

## Por que Python, isolado dos serviços Java

Isolamento de falhas: instabilidade da API do Telegram ou bugs de parsing não podem afetar
[[bets-service]] nem [[stats-service]]. Esta é uma decisão de arquitetura, não preferência de
linguagem — não reescrever em Java "para unificar a stack" (ver [[ARCHITECTURE]] seção
"Decisões que não devem ser reinterpretadas").

## Vínculo de conta (pré-requisito do RF05)

Antes de capturar apostas de um `telegramUserId`, precisa existir um vínculo com um usuário
cadastrado (`TELEGRAM_ACCOUNT` em [[auth-service]]). Fluxo: usuário gera um código de vínculo na
tela de perfil em [[web]] (chama um endpoint de [[auth-service]]) e envia esse código ao bot;
`telegram-integration` repassa `telegramUserId` + código para [[auth-service]] confirmar e
persistir o vínculo. Sem vínculo, o [[api-gateway]] rejeita a chamada de captura automática (ver
abaixo) e o bot deve responder ao usuário pedindo para vincular a conta primeiro — nunca deve
tentar adivinhar ou criar um tenant novo a partir de uma mensagem do Telegram.

## Fluxo de captura de aposta

1. Usuário envia mensagem de texto não estruturada ao bot.
2. n8n recebe o webhook do Telegram, normaliza o payload em JSON.
3. Rotina Python faz o parsing/higienização da string (esporte, liga, mercado, odd, stake, casa
   de apostas, etc.).
4. Chama `POST /api/v1/bets` através do [[api-gateway]], autenticando com um header `X-Service-Key`
   (credencial de serviço, não token PASETO — não há usuário logado neste fluxo) em vez de
   chamar [[bets-service]] diretamente. O Gateway resolve `telegramUserId -> userId`/`tenantId`
   via o vínculo criado acima e injeta `X-User-Id`/`X-Tenant-Id` antes de rotear — **mesmo
   endpoint** `POST /api/v1/bets` usado pelo formulário web, não um endpoint separado.
   > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): `auth-service` mantém um
   > diretório `TELEGRAM_LINK` no schema `public` (fora de qualquer schema de tenant) que
   > resolve `telegramUserId -> tenantId`/`userId` diretamente — o Gateway não precisa mais
   > varrer schemas nem o bot informar o slug do tenant.
5. Resto do fluxo (evento `BetCreated`, consumo assíncrono por [[stats-service]]) é idêntico
   ao registro manual.

## Internacionalização (i18n)

Mensagens que o bot envia de volta ao usuário (erro de vínculo, confirmação de captura de
aposta, orientação para vincular a conta, etc.) são localizadas — não é só o frontend, ver
[[CONVENTIONS]] seção "Internacionalização (i18n)". Idioma escolhido pelo `language_code` que o
próprio update do Telegram já traz — não é necessário armazenar preferência de idioma em nenhum
serviço para isso. Formato **JSON**, um arquivo por locale em `locales/{pt-BR,en-US,es}.json`
(decisão fechada em 2026-08-02, ver [[DECISIONS-LOG]] — `docs/CONVENTIONS.md` deixava JSON ou
`gettext` em aberto até então). Os três locales sempre em sincronia, mesma regra do resto do
projeto — nenhuma mensagem nova do bot é considerada `done` traduzida para só um ou dois deles.

## Ver também

- [[auth-service]] — `TELEGRAM_ACCOUNT` vincula o `telegramUserId` ao usuário cadastrado; expõe
  o endpoint de confirmação de vínculo e o lookup usado pelo Gateway.
- [[api-gateway]] — autentica a chamada de serviço-a-serviço e resolve o tenant antes de rotear.
- [[bets-service]] — destino final da chamada `POST /api/v1/bets`.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário e do diretório global (item 15)
  que resolve o lookup de `TELEGRAM_ACCOUNT`.
