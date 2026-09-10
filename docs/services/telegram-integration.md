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
tela de perfil em [[web]] (chama `POST /api/v1/telegram-links` de [[auth-service]], através do
[[api-gateway]] — rota já roteada) e envia esse código ao bot via `/vincular <codigo>`;
`telegram-integration` repassa `telegramUserId` + código para `POST /api/v1/telegram-accounts`
em [[auth-service]] confirmar e persistir o vínculo. Sem vínculo, o [[api-gateway]] rejeita a
chamada de captura automática (ver abaixo) e o bot deve responder ao usuário pedindo para
vincular a conta primeiro (comportamento de `telegram-integration feat-004`, tratando o `401` do
Gateway na submissão final — ver passo 6 abaixo) — nunca deve tentar adivinhar ou criar um tenant
novo a partir de uma mensagem do Telegram.

> **Decisão de 2026-09-08** (ver [[DECISIONS-LOG]]): a chamada de confirmação
> (`POST /api/v1/telegram-accounts`) vai **direto** em `auth-service`, sem passar pelo
> `api-gateway` — `api-gateway` não roteia `/api/v1/telegram-accounts/**` (só
> `/api/v1/telegram-links/**`), e seu `ServiceKeyAuthenticationFilter` exige um vínculo **já
> confirmado** pra resolver identidade antes de deixar a requisição passar, o que é circular
> pro próprio endpoint que cria o vínculo. Mesmo precedente das rotas admin (`X-Admin-Api-Key`
> fora da tabela de roteamento do Gateway). O código de vínculo em si (aleatório, TTL curto, uso
> único, gerado por `auth-service`) é o mecanismo de segurança desta chamada — sem usuário
> logado e sem `X-Service-Key` aplicável aqui.

## Fluxo de captura de aposta

1. Usuário envia **uma foto do bilhete da aposta** (print do comprovante gerado pela casa de
   apostas) **ou uma mensagem de texto livre** ao bot — decisão de 2026-09-08, ver
   [[DECISIONS-LOG]] (nenhuma nota fixava o formato antes).
2. n8n recebe o webhook do Telegram, normaliza o payload em JSON (texto ou referência da foto).
3. Rotina Python roda OCR (Tesseract, via `pytesseract`) quando for foto, e aplica extração
   heurística genérica (esporte, liga, mercado, odd, stake, casa de apostas, etc.) sobre o texto
   resultante — sem template por casa de apostas, sem garantia de acerto (não há amostra real de
   bilhete disponível pra validar contra o layout de nenhuma casa específica). Campo não
   extraído com confiança faz o bot perguntar ao usuário diretamente, um de cada vez — estado da
   conversa (quais campos já foram resolvidos, qual está pendente) guardado no Redis já
   provisionado em [[infra]], chave por `telegramUserId`, TTL curto.
4. **Resolução de catálogo** (`feat-004`, decisão de 2026-09-08, ver [[DECISIONS-LOG]]):
   `bettingHouseId`/`sportId`/`leagueId`/`marketId` são obrigatórias em `POST /api/v1/bets` (ver
   [[bets-service]]), mas `feat-002` nunca extrai `sport`/`league`/`market` (sempre `None`) e só
   tenta `betting_house` como nome best-effort. Bot busca o catálogo daquele tenant (`GET
   /api/v1/sports`/`/leagues`/`/markets`/`/betting-houses`, mesmos headers do passo 5) e **sempre
   pergunta por lista numerada** para `sport`/`league`/`market`; para `betting_house`, tenta fuzzy
   match contra o nome extraído primeiro, caindo pra lista se não achar. Catálogo vazio para
   algum campo: bot **não cria** a entrada — orienta o usuário a cadastrar em [[web]] primeiro e
   não conclui a captura.
5. Chama `POST /api/v1/bets` através do [[api-gateway]], autenticando com um header `X-Service-Key`
   (credencial de serviço, não token PASETO — não há usuário logado neste fluxo) e informando o
   autor da mensagem via `X-Telegram-User-Id` (decisão de 2026-09-07, ver [[DECISIONS-LOG]] —
   header dedicado, corpo da requisição idêntico ao do formulário web) em vez de chamar
   [[bets-service]] diretamente. O Gateway resolve `telegramUserId -> userId`/`tenantId` via o
   vínculo criado acima e injeta `X-User-Id`/`X-Tenant-Id` antes de rotear — **mesmo endpoint**
   `POST /api/v1/bets` usado pelo formulário web, não um endpoint separado.
   > **Resolvido em 2026-08-02** (ver [[DECISIONS-LOG]] item 15): `auth-service` mantém um
   > diretório `TELEGRAM_LINK` no schema `public` (fora de qualquer schema de tenant) que
   > resolve `telegramUserId -> tenantId`/`userId` diretamente — o Gateway não precisa mais
   > varrer schemas nem o bot informar o slug do tenant.
6. **Envio da aposta resolvida** (`feat-004`): a chamada leva `Idempotency-Key` derivada do
   `update_id` nativo do Telegram (repassado pelo n8n como `telegramUpdateId` — protege contra o
   Telegram reentregar o mesmo webhook; um hash do conteúdo da aposta foi cogitado e descartado
   por colidir entre duas apostas legítimas com odd/stake/casa iguais, ver [[API-CONTRACTS]]).
   `bettingHouseId`/`sportId`/`leagueId`/`marketId` resolvidos no passo 4; `betDate` convertido de
   data pura (`aaaa-mm-dd`) para instante completo (`aaaa-mm-ddT00:00:00Z`) — `CreateBetRequest`
   exige `Instant`, não data pura. Resposta do Gateway vira uma de seis mensagens localizadas:
   sucesso (`201` ou reenvio idempotente `200`), sem vínculo (`401` — orienta `/vincular`), FK não
   encontrada (`404`, raro — a resolução do passo 4 já validou os IDs momentos antes), validação
   de negócio falhou (`422`, RN07) ou erro genérico (indisponibilidade). **Limpeza do estado da
   conversa depende de qual parte falhou, não só de sucesso/falha genérico**: sem vínculo (`401`)
   e erro genérico (indisponibilidade) preservam os campos/IDs já resolvidos no Redis — o dado da
   aposta está correto, só uma condição externa precisa mudar (vincular a conta; a infra voltar),
   então a próxima mensagem do usuário repete a tentativa de envio imediatamente, sem pedir os
   dados de novo. FK não encontrada (`404`) e validação de negócio (`422`) **limpam o estado**
   como sucesso — insistir com o mesmo `catalogId` obsoleto ou a mesma `odd`/`stake` inválida só
   repetiria a falha para sempre; a próxima mensagem do usuário começa uma conversa nova (achado
   real corrigido durante a implementação, não previsto no Plan Review original).
7. Resto do fluxo (evento `BetCreated`, consumo assíncrono por [[stats-service]]) é idêntico
   ao registro manual.

## Internacionalização (i18n)

Mensagens que o bot envia de volta ao usuário (erro de vínculo, confirmação de captura de
aposta, orientação para vincular a conta, etc.) são localizadas — não é só o frontend, ver
[[CONVENTIONS]] seção "Internacionalização (i18n)". Idioma escolhido pelo `language_code` que o
próprio update do Telegram já traz — não é necessário armazenar preferência de idioma em nenhum
serviço para isso. Formato **JSON**, um arquivo por locale em
`src/telegram_integration/locales/{pt-BR,en-US,es}.json` (decisão fechada em 2026-08-02, ver
[[DECISIONS-LOG]] — `docs/CONVENTIONS.md` deixava JSON ou `gettext` em aberto até então; caminho
movido pra dentro do pacote em `feat-008`, 2026-09-10 — só funcionava fora dele em install
editable). Os três locales sempre em sincronia, mesma regra do resto do
projeto — nenhuma mensagem nova do bot é considerada `done` traduzida para só um ou dois deles.

## Ver também

- [[auth-service]] — `TELEGRAM_ACCOUNT` vincula o `telegramUserId` ao usuário cadastrado; expõe
  o endpoint de confirmação de vínculo e o lookup usado pelo Gateway.
- [[api-gateway]] — autentica a chamada de serviço-a-serviço e resolve o tenant antes de rotear.
- [[bets-service]] — destino final da chamada `POST /api/v1/bets`.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário e do diretório global (item 15)
  que resolve o lookup de `TELEGRAM_ACCOUNT`.
