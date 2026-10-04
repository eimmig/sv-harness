# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-10-04

## Objetivo atual

Escrever a **4.4 Avaliação experimental** do TCC e ajustar o texto pelas divergências. A evidência de
produção (carga, escalonamento, DLQ, cache) foi **coletada** em 2026-10-04; falta empacotá-la
(`05-coleta.sh` + `scp`) e transformar em texto. Números e leitura honesta: `docs/testes-de-producao.md`
seção "Resultados da rodada de 2026-10-04"; frases do TCC 1 afetadas: `docs/divergencias-tcc1.md` seção 6.

## Concluído

- [x] `epic-041` fechado e liberado em `main` nos 7 repositórios (HPAs, PG18/Redis 8, consumo concorrente do
      stats, outbox transacional com confirms). Produção atualizada à mão (o deploy do CI não alcança o k3s).
- [x] Scripts `tools/evidence/01` a `04` **validados no cluster real** (`05-coleta.sh` ainda sem uso).
      `03-dlq.sh` corrigido para esperar o contador da fila quorum zerar antes de gravar o resultado.
- [x] Rodada real (100.000 apostas, 128 threads, pasta `evidence/final` no Debian, tenant `loadtest-0086b111`)
      com capturas de tela: baseline, HPA escalando, fila RabbitMQ (4 consumidores), reconciliação, redução de
      réplicas, DLQ (mensagem fora do contrato e recuperação), cache.

## Resultados medidos (resumo; completo em `docs/testes-de-producao.md`)

- **HPA:** 4 serviços subiram para 3 ou 4 réplicas em 41 a 62 s (pico de CPU 172% a 501% do request) e
  voltaram a 1 em ~9 min. **Sem ganho de vazão:** 32,4 apostas/s contra 43,2 da rodada 1 (1 réplica); o
  gargalo é o `postgres-bets` (501m de CPU, `pg_isready` estourando 1 s).
- **Eventos:** 193.998 esperados = 193.998 processados, `fact_bet` = 99.998, outbox e DLQ vazios (PASS).
  **Mas 18 apostas ficaram `pending` no stats** (liquidadas no `bets-service`): não escrever "perda zero de
  estado".
- **Cache:** RNF03 PASS (p95 206,2 ms com cache quente, miss de 2.189,5 ms).
- **Probes:** `bets-service` reiniciou 2 vezes na carga por liveness de 1 s com CPU limitada a 500m (26 erros
  no gerador).

## Backlog aberto por esta rodada (nenhum com `plan_review`)

- `stats-service feat-028` (já existia; ganhou a evidência de produção): corrida `BetCreated`/`BetSettled` em
  `fact_bet` **não converge** pelo retry, 18 apostas ficaram `pending`.
- `infra feat-012` (nova): probes tolerantes a carga, `startupProbe` e dimensionamento do `postgres-bets`.
- `stats-service feat-029` (já existia): cache em `afterCommit`, `existsById` morto.

## Falta

- `bash tools/evidence/05-coleta.sh evidence/final` no Debian e `scp` do `.tar.gz` para o PC (a pasta
  `evidence/` nunca foi versionada: guardar fora do repositório e **nunca apagar**).
- Capturas que podem faltar: DLQ com `Ready 2` na mesma rodada, Redis no RedisInsight, tabela do
  `02-resumo.txt` (gerada depois com `resumo_carga.py`).
- Escrever **4.4 Avaliação experimental** (estrutura: ambiente, escalabilidade horizontal, perda de eventos e
  estado, DLQ e recuperação, cache e RNF03, limitações) e ajustar o texto pelas divergências (Quadro 2, modelo de
  tenant, rotas em inglês, chaves de cache, método Kanban).

## Bloqueios / Riscos

- **Deploy automático do CI** (`epic-028`) nunca alcançou o k3s: `KUBE_CONFIG` aponta para `127.0.0.1:6443`.
  Aceito pelo usuário; todo deploy é manual.
- **Limite de memória 1Gi é temporário** no cluster (`kubectl set resources`); um `kubectl apply` volta a 512Mi.
- Depois de um boot do servidor, esperar 10 a 15 min antes de medir: a partida das JVMs sobe réplicas sem tráfego.
- `rabbitmq` usa 200 a 880m de CPU mesmo com pouca carga; olhar se atrapalhar.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Ler `docs/testes-de-producao.md` e `docs/divergencias-tcc1.md`.
3. Se o usuário quiser corrigir os achados (`stats-service feat-028`, `infra feat-012`), seguir o fluxo do harness:
   `Plan Reviewer`, `plan_review`, story no Jira, branch pela chave, PRs com CI, auditorias na última subtask.
4. Se for escrever o capítulo, usar as tabelas "Números para o texto do TCC" e "Resultados da rodada".
