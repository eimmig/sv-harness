# Session Handoff — Raiz

> Estado atual, não histórico. O diário cronológico é o `progress.md` — este arquivo é reescrito
> a cada sessão para responder "o que a próxima sessão precisa saber agora".

**Última atualização:** 2026-10-04

## Objetivo atual

Gerar a **evidência de produção para o TCC 1** (carga, escalonamento automático, DLQ, cache) e
documentar. Código está pronto e liberado; falta **concluir os testes na máquina Debian com k3s do
usuário** e escrever o capítulo. Roteiro e scripts: `docs/testes-de-producao.md` e `tools/evidence/`.

## Concluído (2026-09-30 a 2026-10-04)

- [x] Auditoria do TCC 1 contra o sistema: `docs/divergencias-tcc1.md` (TCC diz X, foi feito Y).
- [x] `epic-041` fechado e **liberado em `main` nos 7 repositórios** (infra v0.2.0, api-gateway v0.1.2,
      auth-service v1.0.0, bets-service v0.3.0, stats-service v0.2.1, telegram-integration v0.1.2,
      web v2.0.0): HPAs (`infra feat-011`), PostgreSQL 18/Redis 8 (`infra feat-010`), consumo concorrente
      do stats (`stats-service feat-027`), outbox transacional + relay com confirms (`bets-service feat-024`).
- [x] Produção (k3s Debian) atualizada pelo usuário à mão (o deploy do CI nunca alcançou o cluster):
      bancos PG18 recriados vazios, tenant reprovisionado, manifests dos 4 serviços Java e do Redis
      reaplicados (traz `requests.cpu` e remove `replicas`), limite de memória dos 4 Java subido para 1Gi
      com `kubectl set resources` (temporário, o próximo `apply` volta a 512Mi).
- [x] Scripts de evidência em `tools/evidence/` (`01-baseline` a `05-coleta`, `resumo_carga.py`) e roteiro
      com capturas de tela no vault. Testados só localmente (sintaxe e lógica de resumo); **o cluster real
      os validou parcialmente** (01 e 02 rodaram; 03, 04 e 05 ainda não).

## Resultados medidos até agora

**Rodada 1, sem HPA funcionando** (`evidence/20261001-153811`, 1 réplica por serviço): 50.000 apostas,
0 erros, 43,2 apostas/s em 19 min; 96.857 eventos esperados = 96.857 processados (PASS); `fact_bet` =
50.000 (PASS); outbox 0 e DLQ 0 (PASS); nenhum reinício/OOM. A fila nunca acumulou
(`messages_ready` = 0, `unacked` no máximo 216): o gargalo é a API, não o consumo. Nessa rodada o HPA
ficava em `cpu: <unknown>/70%` porque os pods Java ainda não tinham `requests.cpu` (manifests antigos);
**não vale como prova de escalonamento**, vale como linha de base e prova de perda zero.

**Rodada 2, com HPA calculando** (50.000 apostas, 128 threads, depois de reaplicar os manifests):
confirmado antes da carga `cpu: 3%/70%`, `5%`, `16%` (bets-service) e `4%` em repouso. **O usuário
informa que nenhum pod extra subiu.** Os arquivos da rodada (`evidence/com-hpa/02-resumo.txt`,
`02-hpa.txt`, `02-top.txt`, `02-hpa-eventos.txt`) **ainda não foram analisados**.

## Próximo passo imediato: descobrir por que não escalou

Pedir ao usuário `cat evidence/com-hpa/02-resumo.txt` e `tail -30 evidence/com-hpa/02-hpa-eventos.txt`
(e `02-top.txt` se preciso) e decidir pelo que aparecer:

1. **Pico de CPU abaixo de 70% do request (100m)** em todos os serviços: não é bug. A carga não saturou
   (o gerador `tools/load_test_bets.py` limita a vazão a ~43 apostas/s). Opções: mais threads
   (`02-carga.sh 100000 256`), rodar o gerador de outra máquina, ou baixar o alvo do HPA para 50% em
   `k8s/hpa.yaml` (mudança de manifest: nova feature em `infra`, com `Plan Reviewer`). Registrar o
   resultado honestamente no TCC ("sob N apostas/s o pico foi X%, abaixo do limiar").
2. **Pico acima de 70% e `REPLICAS` não subiu**: olhar `02-hpa-eventos.txt` (condições `AbleToScale`,
   `ScalingActive`, eventos `FailedGetResourceMetric`, "unable to get metrics", janela de estabilização)
   e `kubectl describe hpa`. Possível atraso do `metrics-server` (15 a 60 s) ou o HPA considerando só pods
   `Ready`.
3. **Escalou mas o resumo não mostrou**: conferir `resumo_carga.py` contra o formato real de
   `02-hpa.txt` (o parse usa regex para `cpu: 45%/70%`).

Não escrever "escalou" no TCC sem a prova (`REPLICAS` > 1 no `02-hpa.txt` e eventos "New size").

## Falta executar no Debian (depois do HPA)

- `03-dlq.sh` (pausa para capturar a DLQ na UI do RabbitMQ), `04-cache.sh <slug> <email> <senha>`
  (tenant da rodada: `loadtest-40e04b9e`, admin `admin@loadtest-40e04b9e`; a senha está no
  `02-carga.txt` da rodada, não registrada aqui), `05-coleta.sh`.
- Escrever **4.4 Avaliação experimental** no TCC com os números (tabela em `docs/testes-de-producao.md`
  "Números para o texto do TCC").
- Ajustar o texto do TCC pelas divergências de `docs/divergencias-tcc1.md` (Quadro 2 de versões,
  modelo de tenant, rotas em inglês, chaves de cache, método Kanban).

## Bloqueios / Riscos

- **Deploy automático do CI** (`epic-028`) nunca alcançou o k3s: `KUBE_CONFIG` aponta para `127.0.0.1:6443`.
  Aceito pelo usuário; todo deploy é manual (`kubectl apply`/`rollout restart`).
- **Limite de memória 1Gi é temporário** no cluster; um `kubectl apply` dos manifests volta a 512Mi e o
  `stats-service` usa ~485Mi em repouso. Se o teste voltar a rodar depois de um `apply`, reaplicar o
  `kubectl set resources`, ou abrir feature em `infra` para subir o limite nos manifests.
- **Backlog sem `plan_review`:** `stats-service feat-028` (corrida `BetCreated`/`BetSettled` em `fact_bet`,
  curada hoje pelo retry do listener, sem teste) e `feat-029` (cache em `afterCommit`, `existsById` morto).
- **Capacidade do nó** é boa (~8 CPUs, 16 GB, 7% e 6% alocados), mas o `rabbitmq` usa 290 a 620m de CPU
  mesmo parado/depois da carga; olhar se atrapalhar.
- Lição de processo: rodar a **suíte completa** (`mvn verify`), não só testes direcionados, antes de
  abrir PR; o SonarCloud só roda no PR da story e `tools/.sonar.env` permite ler o motivo da falha pela API.

## Próxima sessão — por onde começar

1. Rodar `./init.sh` na raiz (deve sair `0`).
2. Ler `docs/testes-de-producao.md` e `docs/divergencias-tcc1.md`.
3. Pedir ao usuário os arquivos da rodada 2 e seguir "Próximo passo imediato" acima.
4. Fluxo do harness vale para qualquer mudança de código: `Plan Reviewer`, story no Jira, branch pela
   chave, PRs com CI, auditorias na última subtask, `evidence` no fechamento.
