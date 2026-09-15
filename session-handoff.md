# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-020`/`epic-023`/`epic-025`/`epic-026`/`epic-028` fechados. `epic-024`
(times/jogadores) `in-progress` — `bets-service` (`feat-016`+`feat-017`) e `apps/web`
(`feat-020`+`feat-021`) fechados; ainda cobre `stats-service feat-018` (`BLOCKED` pelo próprio
Plan Reviewer) e `apps/web feat-022..024` (date pickers, ícone do seletor de idioma, espaçamento
de cadastro), nenhum tocado ainda — não fechar o epic sem revisitar esse escopo mais amplo.
`epic-027` `in-progress` — `apps/web feat-027` (tela de vínculo Telegram) fechada; falta
`feat-026` (mesmo epic) para completá-lo, hoje `REVISE` (ver abaixo).

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

Epics `not-started` elegíveis (dependências satisfeitas): nenhum novo além do que já está
`in-progress` (`epic-024`/`epic-027`) — WIP 1 por harness já ocupado em `apps/web` por
`epic-027`.

## Concluído nesta sessão (2026-09-15)

- [x] `epic-028` fechado no JSON (CD automático, 6 repositórios) — achado real de infraestrutura
      documentado acima, decisão de rede deixada como está a pedido do usuário.
- [x] `api-gateway feat-015` + `apps/web feat-020`+`feat-021` fecharam a pedido explícito do
      usuário — corrigiram a quebra real de `POST /api/v1/bets` antes de qualquer deploy em massa.
- [x] Os 6 repositórios de aplicação promovidos `develop -> main`, confirmando a mesma falha de
      rede em todos e publicando imagem `:latest` fresca em todos.
- [x] `apps/web feat-028` fechada — fecha `epic-020` da raiz (grade mensal de drawdown no
      dashboard). Achados reais corrigidos: bug de design (2 campos de mês batched atrás de
      Aplicar), regressão pré-existente de `feat-021` no e2e (só apareceu rodando a suíte
      completa), bug de responsividade mobile, 2 achados de SonarCloud.
- [x] **`apps/web feat-027` fechada** — tela de vínculo da conta Telegram (`TelegramLinkApi` +
      `pages/telegram-link`, rota `/telegram-link`, entrada em `app-side-nav`). Sem desvio do
      plano. `epic-027` **não** fecha ainda — falta `feat-026` (mesmo epic), ver abaixo.

## Bloqueios / Riscos

- **Bloqueio de rede conhecido, usuário decidiu deixar como está por agora**: o CD automático de
  `epic-028` não funciona a partir de runners hospedados do GitHub Actions (ver acima). Sem ação
  pendente — não repetir a pergunta nem tentar corrigir sozinho a menos que o usuário peça.
- **`apps/web feat-026` é `REVISE`, decisão de dono pendente**: `plan_review` daquela feature
  aponta que `core/statistics-api.ts` (`BetMetrics`) tem um comentário explícito dizendo
  "byBetType stays out of scope (epic-021 consumes it)" — implementar a parte 2 de `feat-026`
  sem revisar isso cria 2 features competindo pelo mesmo campo. Decidir antes de codificar se
  `feat-026` passa a ser dona de `byBetType` ou se essa parte deve sair de `feat-026` (ficando só
  para `feat-029`/`epic-021`). Se for uma decisão de design real (não só "quem primeiro"),
  perguntar ao usuário em vez de decidir sozinho.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. `epic-027` (`apps/web`) segue elegível para continuar — falta só `feat-026`, mas primeiro
   resolver a decisão de ownership de `byBetType` acima (reler o `plan_review` completo).
3. `epic-024` continua aberto — `stats-service feat-018` `BLOCKED` (reler `plan_review` antes de
   popular subtasks); `apps/web feat-022..024` ainda `not-started`.
4. Backlog dos 6 repositórios de `epic-028` está esgotado — nenhum tem feature elegível até surgir
   escopo novo.
5. Se o usuário quiser rodar o rollout manual em produção agora (imagens já atualizadas): mesmo
   padrão de sempre, túnel SSH + `kubectl rollout restart deployment/<serviço>` por repositório.
