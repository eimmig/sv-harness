# Gaps de integração backend/frontend

## O que foi identificado

Auditoria comparando os endpoints implementados nos backends com os clientes, rotas e
telas do Angular:

- O `bets-service` já expõe bankroll, settings e transações.
- O `stats-service` já produz o agrupamento `byBetType`.
- O `auth-service` já suporta a geração do código de vínculo Telegram.
- O frontend já possui clientes para bankroll e transações, mas ainda precisa fechar a
  integração visual e ponta a ponta desses fluxos.
- O `api-gateway` não roteava `/api/v1/bankroll/**` nem `/api/v1/settings/**`.
- O formulário web de aposta tratava `betType` como texto livre, enquanto o backend
  aceita somente `pre` e `live`.
- O frontend não tipava nem apresentava `byBetType`.
- O frontend não possuía tela para iniciar o vínculo da conta Telegram.

## Onde foi registrado

- `services/api-gateway/feature_list.json`: `feat-013`, rotas de bankroll e settings.
- `apps/web/feature_list.json`: `feat-025`, gestão financeira; `feat-026`, `betType` e
  `byBetType`; `feat-027`, vínculo Telegram.
- `feature_list.json` da raiz: `epic-026` e `epic-027`, espelhos cross-service.

Todas as entradas novas começam como `not-started`. A implementação deve seguir o fluxo
normal do harness: Plan Review, criação da story/subtasks no Jira, branch pela chave Jira,
testes, revisão, evidência e atualização de status.

## Critério de conclusão

Não basta o backend responder diretamente. O fluxo deve funcionar pela URL pública do
Gateway e pela interface Angular, com contratos tipados, autenticação, isolamento de
tenant, traduções, testes e `./init.sh` verde no repositório tocado.