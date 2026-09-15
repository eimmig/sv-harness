# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-15

## Objetivo atual

Os 9 epics originais do TCC 1 e a segunda rodada (`epic-011..022`) estão `done`. Terceira rodada
em andamento: `epic-023`/`epic-025` fechados (fora deste arquivo, ver `progress.md` "Lacuna de
registro"); `epic-024` (times/jogadores) `in-progress` — `bets-service` (`feat-016`+`feat-017`)
fechado, mas a description do epic também cobre `stats-service feat-018` e `apps/web
feat-020..024` (label "Data do evento", date pickers, ícone do seletor de idioma, espaçamento de
cadastro), nenhum tocado ainda — não fechar o epic sem revisitar esse escopo mais amplo.

Epics elegíveis agora (dependências satisfeitas, `not-started`): `epic-020`/`epic-027`
(`apps/web`, só um por vez — WIP 1 por harness) e `epic-028` (`infra/`, ServiceAccount de CI +
kubeconfig pra deploy automático — desbloqueia `feat-018` em todos os 6 repositórios de
aplicação, incluindo `bets-service`). `epic-021` (`apps/web`) ainda depende de `epic-027`.

## Concluído nesta sessão (2026-09-15)

- [x] **`bets-service feat-017` fechado** (catálogo `TEAM` + migração de `Bet.team1`/`team2`
      pra `team1Id`/`team2Id`) — continuação de `epic-024`. `Plan Reviewer` corrigiu um BLOCKER
      real antes de codificar (plano original quebraria consumo já em produção de
      `stats-service`); `Delivery Reviewer` achou um segundo risco real (contrato REST síncrono
      não pôde ficar aditivo, `apps/web` vai quebrar até `feat-021` de lá corrigir — documentado,
      não bloqueante). Ver `services/bets-service/progress.md` para o detalhe completo.
- [x] Limpeza de estado: uma sessão anterior tinha deixado trabalho de `epic-028` (mirror do
      backlog `feat-018`/`feat-019`/`feat-016`/`feat-014`/`feat-010`/`feat-030`/`feat-007` nos 7
      repositórios) não commitado — commitado no início desta sessão antes de continuar.

## Bloqueios / Riscos

Nenhum bloqueio novo. `services/bets-service` sem feature elegível até `infra/feat-007`
(`epic-028`) fechar.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Epics elegíveis: `epic-020`/`epic-027` (`apps/web`, só um `in-progress` por vez) e `epic-028`
   (`infra/`) — nenhum epic `in-progress` nesses dois harnesses agora, os dois podem começar em
   paralelo (sessões diferentes) sem conflito de WIP.
3. `epic-024` continua aberto — reavaliar se o escopo de `apps/web`/`stats-service` daquele epic
   deveria virar features novas nos respectivos backlogs antes de mais alguém assumir.
4. Padrão reaproveitável desta sessão: ao trocar um campo de texto livre por FK num contrato de
   evento já em produção (`BetCreated`/`BetSettled`), checar se o consumidor real já lê esse campo
   (não assumir "ainda não conectado" sem checar o código) — mudança aditiva (manter o campo
   antigo, acrescentar o novo) é sempre mais segura que renomear quando há dúvida.
