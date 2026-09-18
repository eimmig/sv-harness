---
tags: [business, frontend, workflows]
---

# Jornadas da aplicação web

## Entrada e acesso

Login usa tenant, e-mail e senha. Após autenticar, o usuário entra na visão geral. Admin vê gestão de usuários e configuração de unidade; member não vê essas áreas.

## Operações

- Cadastrar e consultar casas, movimentações e catálogos.
- Registrar aposta com validação, seleção de catálogos e data/hora.
- Consultar histórico e liquidar aposta com estado permitido.
- Usar Telegram como canal remoto para a mesma operação de registro.

## Análise

A visão geral mostra o histórico vitalício. O dashboard operacional usa presets de período e filtros de catálogo; o relatório compara períodos e detalha dias; Buscar Estatísticas expõe filtros e métricas avançadas. Toda mudança de filtro consulta [[stats-service]], não filtra apenas dados antigos no cliente.

## Regras de UX

A SPA deve ser responsiva e manter os oito princípios de Shneiderman no formulário de apostas. Textos são localizados em `pt-BR`, `en-US` e `es`; rotas e query params continuam em inglês.

Fontes: [[web]], [[sistema-de-design]], [[autenticacao-e-acesso]], [[ciclo-de-vida-da-aposta]], [[bankroll-e-movimentacoes]] e [[estatisticas-e-dashboards]].
