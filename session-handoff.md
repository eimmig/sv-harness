# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-020`/`epic-023`/`epic-025`/`epic-026`(api-gateway)/`epic-027`/`epic-028`
fechados. `epic-024` (times/jogadores) `in-progress` — `bets-service` (`feat-016`+`feat-017`) e
`apps/web` (`feat-020`+`feat-021`) fechados; ainda cobre `stats-service feat-018` (`BLOCKED` pelo
próprio Plan Reviewer) e `apps/web feat-022..024` (date pickers, ícone do seletor de idioma,
espaçamento de cadastro), nenhum tocado ainda — não fechar o epic sem revisitar esse escopo mais
amplo.

**`epic-027` fechado por completo nesta sessão** (`apps/web feat-027` + `feat-026`, ambas `done`).
Decisão de design real levada ao usuário via `AskUserQuestion` antes de codificar `feat-026`:
`core/statistics-api.ts` tinha um comentário reservando `byBetType` para `epic-021`, mas
`feat-026` também precisava dele — usuário decidiu que `feat-026` é a dona (opção recomendada).

**`epic-021` (web — tela "Visão geral" pós-login) marcado `in-progress`**: suas 6 dependências
(`epic-016`/`014`/`013`/`006`/`026`-api-gateway/`027`) estão todas `done`. Decisão de UX (substitui
redirect pós-login vs. link novo na nav) levada ao usuário via `AskUserQuestion` — **escolheu
substituir o redirect pós-login**: login passa a levar direto pra esta tela nova em vez de
`/dashboard`, que vira só mais um item de nav. Decisão registrada no `plan_review` de `feat-029`
(agora `READY`) e no `detail`/`checklist` de `feat-029.3`. Próximo passo: implementar `feat-029`
em `apps/web` (4 subtasks já planejadas pelo Plan Reviewer).

**`epic-028` (CD automático via CI) fechado no `feature_list.json` — mas o mecanismo real não
funciona ainda**: os 6 repositórios de aplicação ganharam o job `deploy`, e `infra/feat-007`
distribuiu o `KUBE_CONFIG`, mas `kubectl rollout restart` não consegue alcançar o cluster a
partir de um runner hospedado do GitHub Actions — o `KUBE_CONFIG` tem
`server: https://127.0.0.1:6443` (o túnel SSH local do usuário no momento em que a credencial foi
gerada), não um endereço real. Confirmado idêntico nos 6 repositórios. Sem dano a nenhum cluster
(o comando nunca conecta). Ver `docs/services/infra.md` "CD automático via CI" para o achado
completo e as 3 opções de correção. **Perguntado ao usuário explicitamente como prosseguir —
respondeu "deixar como está por agora"**: nenhuma mudança de rede/infraestrutura será tentada até
ele decidir; rollout continua manual (túnel SSH). As 6 imagens `:latest` no GHCR estão
atualizadas (todos os 6 repositórios promovidos `develop -> main` nesta sessão).

## Concluído nesta sessão (2026-09-15)

- [x] `epic-028` fechado no JSON (CD automático, 6 repositórios) — achado real de infraestrutura
      documentado acima, decisão de rede deixada como está a pedido do usuário.
- [x] `api-gateway feat-015` + `apps/web feat-020`+`feat-021` fecharam a pedido explícito do
      usuário — corrigiram a quebra real de `POST /api/v1/bets` antes de qualquer deploy em massa.
- [x] Os 6 repositórios de aplicação promovidos `develop -> main`, confirmando a mesma falha de
      rede em todos e publicando imagem `:latest` fresca em todos.
- [x] `apps/web feat-028` fechada — fecha `epic-020` da raiz (grade mensal de drawdown no
      dashboard). Achados reais corrigidos: bug de design, regressão pré-existente de `feat-021`
      no e2e, bug de responsividade mobile, 2 achados de SonarCloud.
- [x] **`apps/web feat-027` + `feat-026` fechadas — fecham `epic-027` da raiz por completo**:
      tela de vínculo Telegram, `betType` alinhado a `mat-select` PRE/LIVE e `byBetType` tipado
      e exibido num dashboard novo. Ver `progress.md` para o detalhe completo, inclusive a
      decisão de ownership levada ao usuário.

## Bloqueios / Riscos

- **Bloqueio de rede conhecido, usuário decidiu deixar como está por agora**: o CD automático de
  `epic-028` não funciona a partir de runners hospedados do GitHub Actions (ver acima). Sem ação
  pendente — não repetir a pergunta nem tentar corrigir sozinho a menos que o usuário peça.
Nenhum bloqueio conhecido no momento.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-021` (`apps/web`) está `in-progress` — implementar `feat-029` (`plan_review` `READY`, 4
   subtasks já planejadas: `feat-029.1` data mais antiga/saldo inicial, `feat-029.2` cards
   vitalícios, `feat-029.3` tabela mensal + troca do redirect pós-login pra esta tela nova (decisão
   já tomada, ver acima), `feat-029.4` testes/QA/vault). `epic-024` continua `in-progress` em
   harness diferente (`services/bets-service/`) — sem conflito de WIP, mas ainda assim só 1
   feature `in-progress` por vez dentro do `feature_list.json` de `apps/web`.
3. `epic-024` continua aberto — `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de
   popular subtasks); `apps/web feat-022..024` ainda `not-started`.
4. Backlog dos 6 repositórios de `epic-028` está esgotado — nenhum tem feature elegível até surgir
   escopo novo.
5. Se o usuário quiser rodar o rollout manual em produção agora (imagens já atualizadas): mesmo
   padrão de sempre, túnel SSH + `kubectl rollout restart deployment/<serviço>` por repositório.
