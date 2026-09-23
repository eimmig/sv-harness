# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-09-23

## Objetivo atual

32 dos 33 epics `done`. `epic-032` (reformulação de marca StakeVault -> Arka) `in-progress`,
multi-harness — ordem sugerida: vault raiz (done) -> `apps/web feat-042` (done) ->
`telegram-integration feat-011` (done) -> 4 serviços Java (`auth-service feat-019`/`bets-service
feat-020`/`stats-service feat-021`/`api-gateway feat-016`, todos done) -> `infra/` (único harness
restante, ainda não auditado). `epic-033` (novo, `not-started`) — CI: gerar versão automática ao
merge para master, nos 7 repositórios; escopo ainda por decidir por harness (mecanismo de
versionamento difere por stack: Maven/npm/pyproject/tag solta em `infra/`), nenhuma feature
granular aberta ainda.

## Concluído nesta sessão (2026-09-23)

- [x] `telegram-integration feat-011` fechada — 3º harness de `epic-032`. Detalhe em
      `services/telegram-integration/progress.md`.
- [x] **Os 4 serviços Java fechados** (4º/5º/6º/7º harness de `epic-032`, mesma sessão): escopo
      real bem menor que os anteriores — em cada um, só a linha `<description>` do `pom.xml`
      (metadado de prosa Maven); o GroupId `com.stakevault.betting` (pacote Java raiz) é
      identificador técnico real, já deferido por decisão de 2026-09-23. Plan Reviewer rodado uma
      vez (`auth-service feat-019`, READY) e reaproveitado condensado nos outros 3 (mesma
      estrutura confirmada idêntica). `auth-service feat-019` (story SV-549), `bets-service
      feat-020` (SV-552), `stats-service feat-021` (SV-555), `api-gateway feat-016` (SV-558) -
      todos com CI+SonarCloud verdes. Detalhe completo em `progress.md` (raiz) e no
      `progress.md` de cada serviço.
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
2. **`epic-032` in-progress** — único harness restante na ordem sugerida: auditar `infra/`
   (`grep -ril "stakevault"` case-insensitive **e** `grep -rniE "stake|vault"` pra descartar
   substring partida, mesmo cuidado usado nos harnesses anteriores) antes de abrir feature
   granular lá. Atenção: `docs/DECISIONS-LOG.md` (2026-09-23) já lista `infra/k8s/` (secret
   `stakevault-secrets`, imagens `stakevault/<serviço>:local`) como identificadores técnicos reais
   fora de escopo — confirmar se sobra algo de prosa/metadado real antes de planejar.
3. **`epic-033` not-started** — se o usuário pedir pra avançar, plan review por harness primeiro
   (mecanismo de versionamento não está decidido, ver `description` do epic na raiz).
4. `develop` de `sv-frontend` segue à frente de `main` desde `epic-031` (decisão de promoção fica
   com o usuário, não assumir). Mesma pausa vale pros 4 serviços Java + `telegram-integration`
   (ver "Bloqueios" acima).
