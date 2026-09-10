---
tags: [moc]
---

# Índice — Plataforma de Gestão de Bankroll

Vault Obsidian deste projeto. Abra a pasta `docs/` como vault (não a raiz do repositório —
código e arquivos de harness ficam fora do vault, ver [[ARCHITECTURE#Harness multinível]]).

## Visão geral

- [[ARCHITECTURE]] — arquitetura geral, infraestrutura, fluxos de eventos, decisões que não
  devem ser reinterpretadas.
- [[REQUIREMENTS]] — requisitos funcionais, não funcionais e regras de negócio do TCC 1.
- [[DATA-MODEL]] — ERDs consolidados (Mermaid) de `auth-service`, `bets-service` e
  `stats-service`, com histórico de evolução do modelo.
- [[DECISIONS-LOG]] — log cronológico de decisões que divergem/estendem o TCC 1 original (ex.:
  modelo de tenant multiusuário, provisionamento de schema, idioma da API). Atualizado a cada
  sessão que tomar uma decisão desse tipo — não confundir com `progress.md` (diário de sessão).
- **Diagramas originais do TCC1**, movidos de `D:\UTFPR\TCC\Graficos` para dentro do vault em
  2026-08-02 — agora em `docs/diagrams/` (`database/`, `flows/`, `architecture/`, `process/`) e
  `docs/design-references/` (mockups de marca). Cruzados com este vault em 2026-08-01; onde havia
  divergência, a nota correspondente registra a decisão tomada. Os fluxos dinâmicos e os ERDs já
  têm uma transcrição Mermaid autoritativa em [[ARCHITECTURE]] e [[DATA-MODEL]] — os PNGs
  originais em `docs/diagrams/` ficam como prova de origem, não precisam ser reabertos para
  consulta do dia a dia.

## Convenções (decisões que fecham lacunas não especificadas no TCC 1)

- [[CONVENTIONS]] — arquitetura hexagonal dos serviços Java, build tool (Maven), padrões de
  código, Angular (Signals), Python, fluxo de git.
- [[TESTING]] — frameworks de teste por stack, Testcontainers, meta de cobertura 80%.
- [[API-CONTRACTS]] — convenções REST (sempre em inglês), formato de erro (localizado),
  contratos dos eventos `BetCreated` e `BetSettled` (schemas em `docs/contracts/`), confiança
  serviço-a-serviço.
- [[OBSERVABILITY-AND-CONFIG]] — logs estruturados, correlation id, health checks, segredos.
- [[DESIGN-SYSTEM]] — marca StakeVault, tema (claro/escuro), paleta de cores, tipografia e
  inventário de componentes de `apps/web` (layout em painéis baseado no Uphold, identidade
  visual própria) — assets em `docs/design-references/`.
- [[CI-CD]] — pipeline GitHub Actions por repositório (changelog, i18n, build, testes,
  SonarCloud — `infra/` só changelog + validação do compose), `CHANGELOG.md` por repositório,
  setup pendente do SonarCloud.
- [[AGENT-SKILLS]] — Caveman + claude-code-skills (18 skills/7 suítes), prioritárias em
  arquitetura/desenvolvimento/testes/validação — mapeamento por etapa, instaladas (escopo
  `user`) em 2026-08-02.
- [[STATISTICS]] — fórmulas e conceitos estatísticos usados no dashboard e na tela "Buscar
  Estatísticas" (ROI, taxa de acerto, odd média, drawdown máximo, Índice de Sharpe
  simplificado), com a fundamentação teórica do TCC1 citada por métrica.

## Serviços

- [[api-gateway]] — ponto único de entrada HTTP, validação de token PASETO, injeção de
  `X-User-Id`, credencial de serviço para `telegram-integration`. Sem RF próprio.
- [[auth-service]] — cadastro e autenticação (RF01, RF02).
- [[bets-service]] — casas de apostas, apostas, bankroll, movimentações (RF03, RF04, RF06,
  RF07, RF08, RF12, RF13).
- [[stats-service]] — consumidor de eventos, OLAP, cache (RF09, RF10, RF11).
- [[telegram-integration]] — captura automática via bot (RF05).
- [[web]] — SPA Angular (dashboards, formulários).
- [[infra]] — Docker Compose, PostgreSQL, RabbitMQ, Redis; teste de resiliência cross-service
  (`epic-007`). Sem serviço de aplicação, mas com harness e repositório Git próprios, igual aos
  demais (ver [[DECISIONS-LOG]] "Topologia").

## Onde fica o harness de cada nível

| Nível | Instruções | Backlog | Verificação |
|---|---|---|---|
| Raiz (cross-service, não é repositório) | `../CLAUDE.md` | `../feature_list.json` (epics) | `../init.sh` |
| Cada serviço (repositório próprio) | `../../services/<nome>/CLAUDE.md` | `.../feature_list.json` (granular) | `.../init.sh` |
| Frontend (repositório próprio) | `../../apps/web/CLAUDE.md` | `.../feature_list.json` | `.../init.sh` |
| Infra (repositório próprio) | `../../infra/CLAUDE.md` | `.../feature_list.json` | `.../init.sh` |

O vault documenta o *quê* e o *porquê*; os arquivos de harness (fora do vault, dentro de cada
pasta de código) documentam o *como trabalhar* e o *estado atual* daquele nível.
