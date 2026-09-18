---
tags: [conventions, agent-tooling]
---

# Skills de agente (Caveman + claude-code-skills) — prioritárias em todas as etapas

Decisão de 2026-08-02 (ver [[DECISIONS-LOG]]): duas skills/plugins de Claude Code, aplicadas aos
7 repositórios, **prioritárias** — a ferramenta padrão em cada etapa listada abaixo, não uma
opção entre outras. Não são código de aplicação (não vivem em nenhum dos 7 repositórios) —
configuração do próprio agente (`~/.claude/` ou equivalente).

> **Status: instaladas** em 2026-08-02 (escopo `user` — `claude plugin list` confirma os 8
> plugins `enabled`: `caveman@caveman` + as 7 suítes `@levnikolaevich-skills-marketplace`). Ver
> [[DECISIONS-LOG]] para o caminho de instalação usado (`~/.local/bin/claude.exe`, não estava no
> PATH). Escopo `user` = vale para qualquer projeto nesta máquina, não só estes 7 repositórios.
> Uma sessão que não enxergar as skills disponíveis provavelmente só precisa ser reiniciada
> (plugin instalado depois que a sessão já estava rodando não é carregado até reiniciar).

## Idioma das análises — sempre português

Decisão de 2026-09-03: toda saída dessas skills apresentada ao usuário (Plan Reviewer, Delivery
Reviewer, Test Suite Auditor, Persistence Auditor, Documentation Auditor, Codebase Auditor, e
qualquer outra da claude-code-skills) é escrita em **português**, mesmo quando a skill/template
documenta seu output contract em inglês (ex.: `review-suite:ln-11-plan-reviewer`). Consistente
com a regra já existente em `CLAUDE.md` (raiz) de que toda documentação de projeto — vault,
`CHANGELOG.md`, `progress.md`, `feature_list.json` — é em português, entregável de TCC; a única
exceção documentada é a mensagem de commit (ver `docs/convencoes.md` seção "Git"). Um template
de skill em inglês é um detalhe do marketplace instalado, não uma decisão deste projeto.

Rótulos técnicos estáveis do próprio output contract da skill (ex.: `BLOCKER`/`MAJOR`/`MINOR`,
`READY`/`REVISE`/`BLOCKED`) podem continuar em inglês — são identificadores, mesmo padrão do
`type` em RFC 7807 (ver [[contratos-de-api]]). O texto narrativo (achados, evidência, veredito em
prosa, plano corrigido) é sempre português.

## Caveman — todas as etapas, sempre

[github.com/JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). Comprime as
respostas do agente (~65% menos tokens, mesma precisão técnica) — aplica-se à comunicação em
qualquer etapa do trabalho neste projeto, não a uma fase específica.

## claude-code-skills — mapeamento por etapa

[github.com/levnikolaevich/claude-code-skills](https://github.com/levnikolaevich/claude-code-skills),
18 skills em 7 suítes. As 7 estão instaladas (decisão do usuário — instalar tudo, não uma
seleção), mas nem todas têm papel definido no fluxo deste projeto — mapeamento abaixo.

### Arquitetura

- **Architecture Diagram Builder** / **Current Architecture Documenter**: usar para **conferir**
  se a implementação bate com [[arquitetura]]/[[modelo-de-dados]] — nunca para gerar diagrama
  paralelo como fonte nova (mesma ressalva do Impeccable/taste-skill sobre [[sistema-de-design]]:
  este projeto já tem fonte de verdade única de arquitetura).
- **Architecture Decision Recorder**: idem — apoio de estruturação ao redigir uma decisão, mas o
  registro definitivo continua sendo uma entrada em [[DECISIONS-LOG]], não um artefato paralelo
  da skill.
- **System Design Baseline Builder**: apoio ao esclarecer requisitos/restrições mensuráveis
  quando uma feature ambígua aparecer — complementa [[requisitos]], não substitui.
- **System Design Proposal Builder**: apoio ao desenhar uma mudança arquitetural antes de
  implementar (ex.: uma feature que caia na regra "pare e peça confirmação" de
  `CLAUDE.md` raiz sobre desviar de convenção).
- **Architecture Migration Planner**: se uma feature exigir mudança estrutural relevante (trocar
  padrão de cache, biblioteca de mensageria, etc.) — plano reversível antes de mexer.

### Desenvolvimento

- **Plan Reviewer** (Review Suite): antes de começar a implementar uma feature `in-progress`,
  validar o plano contra evidência do repositório — prioritário sobre simplesmente começar a
  escrever código a partir da leitura do `feature_list.json`.
- **`/code-review` (ou `/simplify`)** — não é do pacote `claude-code-skills`, é a skill builtin
  do Claude Code: decisão de 2026-09-03, roda contra o diff **de cada subtask antes de abrir o
  PR dela** (ver [[convencoes]] seção "Git"), não só no gate completo de `feature/` → `develop`.
  Motivo: pega comentário ruidoso e prosa redundante no código cedo, antes de virar histórico do
  Git — as skills de revisão de `claude-code-skills` abaixo (`Delivery Reviewer`,
  `Test Suite Auditor` etc.) só rodam no merge final, tarde demais para esse tipo de ajuste.
- **Codebase Auditor**: saúde geral de código/segurança/manutenibilidade — rodar
  periodicamente, não só no fim.
- **Dependency Upgrader** / **Code Modernizer** / **Performance Optimizer** / **Benchmark
  Comparator** (Optimization Suite): usar quando a situação pedir (dependência desatualizada,
  otimização mensurável necessária) — não é gate obrigatório de toda feature, esses precisam de
  código real existente para fazer sentido.

### Testes

- **Test Strategy Planner**: antes de escrever os testes de uma feature, definir estratégia
  baseada em risco — complementa [[testes]] (que já define frameworks/meta de cobertura por
  stack), não redefine de novo.
- **Acceptance Test Builder**: apoio a testes de aceitação/E2E — alinha com Playwright em
  `apps/web` e com o teste de resiliência cross-service (`infra` `feat-002`).
- **Test Suite Auditor** (Codebase Audit Suite): audita cobertura/qualidade de teste antes de
  marcar uma feature `done` — parte da Definição de Pronto de cada repositório.

### Validação (Definição de Pronto)

- **Delivery Reviewer** (Review Suite): revisão do código implementado através de perspectivas
  selecionadas por risco, antes de marcar `done` — parte da Definição de Pronto de cada
  repositório.
- **Documentation Auditor**: audita se `CLAUDE.md`/`docs/services/*` ainda batem com o que foi
  implementado — roda bem no fim de uma feature que mudou comportamento documentado.
- **Persistence Auditor**: nos 3 serviços Java com banco próprio (`auth-service`, `bets-service`,
  `stats-service`) — audita queries/transações/ciclo de vida de schema-per-tenant.

### Fora do fluxo deste projeto (instaladas, mas sem papel definido)

- **Product Discovery Suite** (Opportunity Evaluator): requisitos já vêm fechados do TCC1 — sem
  necessidade de descoberta/priorização de oportunidade de produto.
- **Maintainer Suite** (Skill Reviewer, Repository Publisher, Release Publisher, Community
  Announcer): voltada a manter/publicar o próprio marketplace de skills, não ao ciclo de vida
  deste projeto. Mantida instalada (decisão do usuário), mas sem gate associado — reavaliar se
  surgir um uso concreto (ex.: `Release Publisher` para as releases reais do projeto, não do
  marketplace de skills).

## Ver também

- [[DECISIONS-LOG]] — decisão original (2026-08-02), racional e status de instalação bloqueado.
- [[convencoes]], [[testes]], [[arquitetura]] — fontes de verdade que as skills auditam, mas
  não substituem.
- [[sistema-de-design]] — mesma ressalva de "auditoria, não fonte nova" aplicada a Impeccable/
  taste-skill (QA visual de `apps/web`).
