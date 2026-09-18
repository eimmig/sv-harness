---
tags: [requirements]
---

# Requisitos — extraídos do TCC 1 (Quadros 3, 4 e 5)

Navegação: [[business/negocio|Negócio]] · [[mapa-de-navegacao]] · [[technical/referencia-tecnica|Referência técnica]]

Fonte: `TCC_1_Sistema_de_Apostas.pdf`, seção 4.1 (Escopo), cruzado com
`docs/diagrams/process/use-case-diagram.png` (UC01–UC11, mesma cobertura de RF — confirmado em
2026-08-01, sem divergências; movido de `D:\UTFPR\TCC\Graficos` para dentro do vault em
2026-08-02). Ver também [[arquitetura]] para a arquitetura geral.

## Mapeamento por serviço

| Serviço | RF cobertos |
|---|---|
| [[auth-service]] | RF01, RF02 |
| [[bets-service]] | RF03, RF04, RF06, RF07, RF08, RF12, RF13 |
| [[stats-service]] | RF09, RF10 (backend), RF11 |
| [[telegram-integration]] | RF05 |
| [[web]] | RF10 (UI), RF11 (UI), RNF01, RNF02 |

## Requisitos Funcionais (RF)

| ID | Nome | Descrição |
|---|---|---|
| RF01 | Manter usuário | Criação e gerenciamento de contas (nome, e-mail, senha). |
| RF02 | Autenticar usuários | Controle de acesso via autenticação (token PASETO). |

> **RF01/RF02 reinterpretados em 2026-08-02** — o TCC 1 modelava conta como 1:1 com o usuário,
> sem conceito de organização. Este harness estende para um modelo de **tenant multiusuário**
> (organização com vários usuários independentes, um `admin` que cria os demais, login exige
> identificador da organização além de e-mail/senha) — ver [[DECISIONS-LOG]] seção "Modelo de
> tenant multiusuário e provisionamento de banco" para o racional completo e
> [[auth-service]]/[[modelo-de-dados]] para o desenho resultante. A descrição da tabela acima é a
> transcrição fiel do TCC1 original — não editada, para preservar a rastreabilidade com a fonte.
| RF03 | Manter casas de apostas | Cadastro/gerenciamento das casas usadas pelo usuário, com saldo e acompanhamento da banca. |
| RF04 | Manter apostas | Registro manual de apostas pelas interfaces da plataforma. |
| RF05 | Capturar apostas automaticamente | Captura automática via canais externos integrados (bot Telegram). |
| RF06 | Processar resultados | Cálculo automático de lucro/prejuízo das apostas registradas. |
| RF07 | Gerenciar bankroll (banca) | Controle/atualização do saldo consolidado com base nas operações. |
| RF08 | Manter histórico de operações | Histórico completo de apostas e movimentações para análise/auditoria. |
| RF09 | Gerar métricas | ROI, taxa de acerto, lucro acumulado. |
| RF10 | Emitir dashboards | Dashboards e gráficos de desempenho. |
| RF11 | Filtrar e consultar dados | Filtro por período, casa de apostas, esporte, mercado, liga, tipster. |
| RF12 | Atualizar status da aposta | Ganha, perdida, devolvida ou pendente. |
| RF13 | Manter movimentações financeiras | Depósitos e retiradas vinculados às casas de apostas. |

## Requisitos Não Funcionais (RNF)

| ID | Nome | Descrição |
|---|---|---|
| RNF01 | Responsividade | Acesso em computadores, tablets e dispositivos móveis. |
| RNF02 | Usabilidade | Interface baseada em princípios de usabilidade (oito regras de ouro de Shneiderman no formulário de apostas). |
| RNF03 | Desempenho | Tempo de resposta adequado em consultas e registros; meta de < 300 ms nos dashboards via cache Redis. |
| RNF04 | Arquitetura | Microsserviços para separação de responsabilidades. |
| RNF05 | Integração | Comunicação com serviços externos via APIs e mensageria. |
| RNF06 | Escalabilidade | Infraestrutura deve suportar crescimento de volume sem degradação. |

> **Confiabilidade do consumo de eventos (DLQ e retry) não tem ID de RNF** — verificado no PDF do
> TCC 1 em 2026-08-17: a tabela original tem exatamente estes seis RNFs, e nenhum deles é sobre
> tolerância a falha. O mecanismo, no entanto, **está especificado** no TCC 1, em prosa: na
> abertura da seção 4.1 (p. 30), "o sistema foi projetado para processar dados de forma segura e
> consistente, utilizando mecanismos de reentrega automática de mensagens (*retries*) e isolamento
> de falhas por meio de uma fila de mensagens mortas (*Dead Letter Queue* — DLQ) [...] impedindo
> que erros isolados travem o fluxo do sistema"; e no capítulo de arquitetura, "o uso de
> mecanismos como DLQ garante que nenhuma mensagem de aposta seja descartada sem ser processada".
> É a base de `epic-007` — que **não** deve citar RNF06 (escalabilidade é volume, não tolerância a
> falha). Nenhum RNF novo foi criado para isso: decisão do usuário de 2026-08-17, ver
> [[DECISIONS-LOG]].

## Regras de Negócio (RN)

| ID | Nome | Critério de Processamento |
|---|---|---|
| RN01 | Consolidação de saldo | Saldo consolidado = soma dos saldos iniciais de todas as casas, ajustado por depósitos/retiradas líquidos, atualizado pelo resultado das apostas liquidadas. |
| RN02 | Cálculo de lucro bruto | Aposta vencedora: `lucro = stake * odd - stake`. |
| RN03 | Cálculo de prejuízo | Aposta perdida: prejuízo = `stake` integral. |
| RN04 | Cálculo de ROI agregado | `ROI = lucro líquido acumulado / valor total investido`. |
| RN05 | Sincronização imediata | Saldo da casa e da banca consolidada devem atualizar imediatamente após a liquidação. |
| RN06 | Elegibilidade de métricas | Uma aposta só entra nas métricas quando `status` é explicitamente ganha, perdida ou devolvida (não pendente). |
| RN07 | Integridade de dados | `stake` nunca negativo; `odd` estritamente > 1,00; bloquear movimentações inconsistentes. |
| RN08 | Filtragem dinâmica | Dashboards recalculam métricas dinamicamente conforme filtros aplicados (período, plataforma, esporte, mercado). |
| RN09 | Cálculo de ROI segmentado | ROI por mercado/esporte/casa considera exclusivamente as apostas daquele agrupamento. |

## Método de trabalho (adaptado do TCC 1, seção 3.2)

O TCC 1 adotou Kanban individual com fluxo: **Opções → Selecionado → Em Execução (WIP máx 1) →
Verificação (WIP máx 1, cobertura de testes > 80%) → Entregue**. Este harness reflete o mesmo
princípio por **lane de serviço**, não globalmente: `feature_list.json` é o backlog ("Opções"),
e a regra de ouro é **uma feature `in-progress` por vez dentro de cada serviço** — permitindo
múltiplos agentes em paralelo, um por serviço (ver `CLAUDE.md` seção "Regras de trabalho").
Diagramas originais do TCC1 sobre esse método de
trabalho (não normativos para o código, só contexto de processo), movidos para
`docs/diagrams/process/` em 2026-08-02: `kanban-diagram.png` (o fluxo descrito acima) e
`scrum-sprint-diagram.png` (planejamento de sprints do TCC1, não adotado literalmente por este
harness — a unidade de planejamento aqui é a feature/epic, não sprints com data fixa).
