---
tags: [business, telegram, integration]
---

# Captura via Telegram

## Objetivo

Permitir o registro remoto de apostas sem exigir que o usuário esteja navegando na SPA. É uma entrada alternativa; a regra de negócio continua pertencendo a [[bets-service]].

## Vínculo

O usuário autenticado gera um código de curta duração. A confirmação associa `telegramUserId` ao tenant e ao usuário no diretório global de [[auth-service]]. O endpoint de confirmação é público controlado e não passa pelo gateway; o lookup usado no fluxo autenticado é protegido por credencial de serviço.

## Captura

O bot recebe texto ou foto do bilhete. OCR e parsing extraem dados; quando a confiança é baixa, o bot conduz uma confirmação conversacional. O módulo não resolve catálogos nem inventa IDs: a resolução usa os catálogos do tenant antes de enviar a criação para o gateway.

## Segurança e rastreabilidade

[[api-gateway]] autentica o bot com `X-Service-Key` e `X-Telegram-User-Id`, resolve o tenant/usuário e encaminha a chamada. `X-Correlation-Id` acompanha a jornada. Falhas de parsing não criam aposta parcialmente.

Fontes: [[telegram-integration]], [[auth-service]], [[api-gateway]], [[contratos-de-api]] e [[observabilidade-e-configuracao]].
