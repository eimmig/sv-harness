---
tags: [business, betting, catalog]
---

# Catálogos de apostas

## Objetivo

Fornecer os valores controlados usados para classificar apostas e comparar desempenho.

## Catálogos por tenant

- Casas de apostas: origem do saldo e das apostas.
- Esportes: modalidade da aposta.
- Ligas: competição.
- Mercados: tipo de mercado.
- Tipsters: origem da indicação.
- Times: participantes, únicos por nome dentro do esporte.

Cada tenant cadastra seus próprios catálogos; não existe seed compartilhado. Nomes duplicados são rejeitados dentro do schema. Times exigem `sportId`; jogadores estão fora do escopo desta rodada.

## Relações

Uma aposta referencia uma casa e os catálogos de classificação. [[ciclo-de-vida-da-aposta]] usa esses IDs no registro; [[estatisticas-e-dashboards]] usa as mesmas dimensões para agrupamento; [[modelo-de-dados]] mostra as relações persistidas.

## Fonte técnica

Endpoints e convenções: [[bets-service]] e [[contratos-de-api]]. Regras de isolamento: [[tenant-e-usuarios]].
