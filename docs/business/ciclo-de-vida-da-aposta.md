---
tags: [business, betting, lifecycle]
---

# Ciclo de vida da aposta

## Estados

`pending` é o estado inicial. A única transição válida é `pending` para `won`, `lost` ou `void`. Aposta liquidada não volta a pendente nem pode ser liquidada duas vezes.

## Registro

A aposta pertence a uma casa e pode ser classificada por esporte, liga, mercado, tipster e times. `stake` deve ser positivo e `odd` deve ser maior que 1,00. O autor é registrado por `createdByUserId`. `Idempotency-Key` permite repetir uma criação sem duplicar a aposta.

A entrada pode vir do formulário web ou de [[captura-via-telegram]]; ambos terminam no contrato de criação de [[bets-service]].

## Liquidação

A liquidação registra `settledByUserId`, calcula o resultado e atualiza o saldo na mesma transação. Lucro de vitória: `stake * odd - stake`; derrota: `-stake`; devolução: `0`. A mudança de estado usa guarda atômica para resolver concorrência.

## Consequências

[[bankroll-e-movimentacoes]] reflete o resultado imediatamente. [[integracao-por-eventos]] propaga `BetCreated` e `BetSettled` para [[estatisticas-e-dashboards]], que só agrega estados liquidados. [[requisitos]] contém RN02, RN03, RN05, RN06 e RN07.
