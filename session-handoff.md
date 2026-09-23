# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-23

## Objetivo atual

33 dos 33 epics `done` — `epic-032` (reformulação de marca StakeVault -> Arka) fechou nesta sessão,
último dos originais. `epic-033` (novo, `not-started`) — CI: gerar versão automática ao merge para
master, nos 7 repositórios; escopo ainda por decidir por harness (mecanismo de versionamento
difere por stack: Maven/npm/pyproject/tag solta em `infra/`), nenhuma feature granular aberta
ainda.

## Concluído nesta sessão (2026-09-23)

- [x] **`epic-032` fechado** — todos os 7 repositórios avaliados na ordem sugerida: vault raiz,
      `apps/web feat-042`, `telegram-integration feat-011` (mudança real de UI/i18n/nome de bot),
      4 serviços Java `auth-service feat-019`/`bets-service feat-020`/`stats-service feat-021`/
      `api-gateway feat-016` (mudança real, `pom.xml <description>`), `infra/` (auditado, **sem**
      mudança necessária - tudo lá é identificador técnico já deferido: nome de rede/projeto do
      compose, usuário RabbitMQ, `Secret`/`Ingress` k8s, tags de imagem). Marca StakeVault -> Arka
      completa em toda superfície visível a usuário/operador real; identificadores técnicos reais
      (GroupId Maven, chave de `localStorage`, nomes de imagem/secret Docker/k8s, domínio Jira)
      permanecem StakeVault por decisão explícita, registrada em `docs/DECISIONS-LOG.md` como
      pendência conhecida pra uma rodada futura separada.
- [x] **Impedimento real resolvido com o usuário**: 8 processos `java.exe` órfãos de outro teste
      do usuário travavam o `repackage` do `mvn verify` local (Windows) nos 4 serviços Java.
      Usuário confirmou via `AskUserQuestion` que eram processos de outro teste dele e autorizou
      pular o build local em vez de derrubar-los — `mvn test` local (EXIT=0 nos 4) + o gate real
      de CI (Linux, sem esse lock) rodando `mvn verify` completo fecharam a verificação.
- [x] **Achado de processo corrigido**: `bets-service` e `stats-service` tinham 1 commit local
      cada, de sessão anterior, nunca publicado em `origin/develop` — sincronizados antes de
      ramificar, pra não vazar aqueles commits alheios no diff das features de rebranding.
- [x] `epic-033` adicionado ao backlog da raiz (pedido do usuário) — `not-started`, sem feature
      granular ainda em nenhum harness.

## Bloqueios / Riscos

Nenhum bloqueio novo dos itens fechados nesta sessão. Risco já documentado (não desta sessão,
não relacionado a `epic-032`/`epic-033`): o `KUBE_CONFIG` de `epic-028` não alcança o cluster a
partir de runners hospedados do GitHub Actions — promoções `develop -> main` dos 6 repositórios
de aplicação continuam pausadas até o usuário decidir o caminho de rede (ver
`services/bets-service/session-handoff.md` e `docs/services/infra.md`).

`e2e/search-statistics.spec.ts` (apps/web) segue quebrado desde `feat-036` (não relacionado a
`epic-032`/`epic-033`) — ver `apps/web/session-handoff.md`/`progress.md` pro detalhe, não
resolvido nesta sessão.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. **Nenhum epic `not-started` na raiz exceto `epic-033`** — conferir cada harness por features
   ad-hoc sem epic próprio antes de assumir que não há trabalho (mesmo padrão já visto).
3. **`epic-033` not-started** — se o usuário pedir pra avançar, plan review por harness primeiro
   (mecanismo de versionamento não está decidido, ver `description` do epic na raiz): provável
   ordem natural é `infra/` primeiro (decide o padrão geral, sem app própria) ou o serviço mais
   simples primeiro, a critério de quem planejar.
4. `develop` de `sv-frontend` segue à frente de `main` desde `epic-031` (decisão de promoção fica
   com o usuário, não assumir). Mesma pausa vale pros 4 serviços Java + `telegram-integration`
   (ver "Bloqueios" acima).
