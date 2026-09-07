---
tags: [service, frontend]
---

# web

Angular 21.x + TypeScript ES2025, SPA. Ver [[ARCHITECTURE]] para o panorama geral,
[[REQUIREMENTS]] para RF/RNF completos, [[DESIGN-SYSTEM]] para tema (claro/escuro), paleta de
cores e inventário de componentes, e [[CONVENTIONS]] seção "Internacionalização (i18n)" para a
estratégia de tradução (pt-BR/en-US/es sempre mantidos, biblioteca em runtime) — tudo normativo,
não decidir uma alternativa aqui. Harness de código em `apps/web/CLAUDE.md`.

## Responsabilidade

- RF01/RF02 (UI) — autenticação e gestão de usuários **dentro de um tenant já existente**,
  consumindo [[auth-service]]. **Sem tela de autocadastro** — ver seção "Modelo de tenant (UI)"
  abaixo, reinterpretação de 2026-08-02 sobre o RF01 original do TCC1.
- RF03 (UI) — gestão de casas de apostas, consumindo [[bets-service]].
- RF04 (UI) — registro manual de apostas.
- RF08 (UI) — histórico de operações.
- RF10/RF11 (UI) — dashboards e filtros dinâmicos, consumindo [[stats-service]].
- RNF01 — responsividade (desktop, tablet, mobile).
- RNF02 — usabilidade.

## Modelo de tenant (UI)

Decisão de 2026-08-02 (ver [[DECISIONS-LOG]] "Modelo de tenant multiusuário") muda o que a UI
de autenticação precisa cobrir — nenhuma das telas abaixo é autocadastro público:

- **Login**: três campos — identificador/slug da organização (tenant), e-mail, senha. Necessário
  porque e-mail só é único dentro do schema do tenant, não globalmente (ver [[auth-service]]) —
  sem o slug, `auth-service` não sabe em qual schema validar a senha.
- **Sem tela pública de "criar conta"**: criação de **tenant** (e do primeiro usuário, o admin
  daquele tenant) é uma rota administrativa restrita ao operador da plataforma, **fora do
  escopo deste app por completo** — operador chama a API diretamente (`X-Admin-Api-Key`, ver
  [[API-CONTRACTS]]), sem UI própria em `apps/web` (decisão de 2026-08-02, ver [[DECISIONS-LOG]]
  item 11). Esse é o único passo do fluxo sem equivalente no caso de uso original do TCC1 (UC01
  não previa um segundo ator "operador").
- **Gestão de usuários do tenant** (tela nova, substitui a antiga tela de "cadastro" público):
  visível **apenas** para o usuário logado com `role = admin` do tenant — `role = member` **não
  vê essa tela de forma alguma** (nem em modo somente leitura, decisão de 2026-08-02, ver
  [[DECISIONS-LOG]] item 11). É a implementação de UC01 ("Manter usuário") do diagrama original,
  só que restrita a quem pode acioná-la; continua sendo o próprio usuário (o admin) quem cria os
  demais, não o operador da plataforma. Lista os usuários do tenant e permite criar novos
  (`role = member`) — usa o mesmo layout em painéis (ver [[DESIGN-SYSTEM]] item 13, "Lista de
  configurações/menu", como base) e a mesma regra semântica de cor (ação de criar usuário é
  neutra/azul, não verde).

## Regras de design do formulário de apostas

O formulário de registro manual (RF04) deve seguir as **oito regras de ouro de Shneiderman**,
citadas explicitamente no escopo do TCC:

1. Buscar consistência.
2. Permitir atalhos para usuários frequentes.
3. Oferecer feedback informativo.
4. Projetar diálogos que indiquem encerramento.
5. Prevenir e tratar erros de forma simples.
6. Permitir reversão fácil de ações.
7. Manter o lócus de controle com o usuário.
8. Reduzir a carga de memória de curto prazo.

## Dashboards e filtros (RN08)

Filtros por período, casa de apostas, esporte, liga, mercado e tipster devem recalcular as
métricas dinamicamente — não são apenas um filtro client-side sobre dados já carregados; cada
mudança de filtro é uma nova consulta a `GET /api/v1/statistics`, que responde um bundle único
com todas as vistas do dashboard de uma vez (ver [[stats-service]]). Rótulos de filtro na UI são
localizados (ver [[CONVENTIONS]]) mesmo os query params enviados sendo sempre em inglês —
**corrigido em `feat-006`**: os nomes reais implementados usam sufixo `Id` (`bettingHouseId`,
`sportId`, `leagueId`, `marketId`, `tipsterId`) mais `from`/`to` (data, `yyyy-MM-dd`), não
`sport`/`league`/`market` como esta nota dizia antes — mesma correção de nomenclatura já feita em
[[API-CONTRACTS]] para `bets-service`, só não tinha sido propagada até aqui.

## Ver também

- [[auth-service]], [[bets-service]], [[stats-service]] — APIs consumidas via API Gateway.
- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário (item 11: operador usa API
  direta, sem UI de provisionamento; `role = member` não vê a tela de gestão de usuários).
