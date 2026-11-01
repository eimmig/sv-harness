---
tags: [testes, producao, tcc]
---

# Testes de produção: carga, escalonamento, DLQ e cache

Roteiro para gerar, no servidor Debian com k3s, a evidência que o TCC precisa: escalonamento
automático (HPA), eventos sem perda, fila de mensagens mortas (DLQ), cache Redis e tempo de resposta
do dashboard (RNF03). Os scripts ficam em `tools/evidence/` do repositório `sv-harness` e gravam tudo
em `evidence/<data-hora>/`. Contexto das correções que tornam estes testes válidos: [[divergencias-tcc1]]
seção 6, [[bets-service]] "Mecanismo de publicação" e [[infra]] "Autoscaling horizontal".

## Pré-requisitos (na máquina Debian)

- `kubectl` apontando para o k3s, `curl`, `python3` e `python3-requests` (`sudo apt install python3-requests`).
- Clone do `sv-harness` (`git clone https://github.com/eimmig/sv-harness`), na pasta raiz dele.
- Serviços, HPAs e Postgres 18 no ar (`kubectl get pods`, `kubectl get hpa` com percentual).
- Secret `stakevault-secrets` no namespace (os scripts leem `ADMIN_API_KEY`, `RABBITMQ_*` e o Redis dele, nunca imprimem).
- `BASE_URL` do Ingress se não for `http://localhost` (`export BASE_URL=http://<host>`); `NS=<namespace>` se não for `default`.

## Ordem

| Passo | Comando | O que prova |
|---|---|---|
| 1 | `bash tools/evidence/01-baseline.sh` | estado inicial, versões (PG 18, Redis 8), capacidade do nó |
| 2 | `bash tools/evidence/02-carga.sh 50000 64` | HPA escalando, eventos publicados = processados |
| 3 | `bash tools/evidence/03-dlq.sh` | retry, DLQ com mensagens e recuperação |
| 4 | `bash tools/evidence/04-cache.sh <slug> <email> <senha>` | cache hit/miss, TTL, RNF03 |
| 5 | `bash tools/evidence/05-coleta.sh evidence/<pasta>` | empacota tudo em `.tar.gz` |

Use `OUT=evidence/meu-teste` para juntar os passos na mesma pasta. O `slug`, o `email` e a senha do
passo 4 vêm do final da saída do passo 2 (`tenant slug`, `admin email`, `admin password`).

### 2. Carga e escalonamento

`02-carga.sh` cria um tenant limpo, registra e liquida N apostas pela API real (`tools/load_test_bets.py`)
e, em paralelo, amostra a cada 10 s `kubectl get hpa`, `get pods`, `top pods` e as filas do RabbitMQ
(`02-hpa.txt`, `02-pods.txt`, `02-top.txt`, `02-filas.txt`). Ao terminar espera o outbox e a fila
esvaziarem e grava `02-reconciliacao.txt` com PASS/FAIL para:

- eventos processados no stats = apostas criadas + liquidadas (perda zero);
- `fact_bet` = apostas em `bets-service`;
- outbox vazio e DLQ vazia.

No fim, `02-resumo.txt` traz a tabela pronta: **máximo de réplicas** por serviço, **pico de CPU** (% do
`requests.cpu`, o valor que o HPA compara com 70%), **tempo até o primeiro escalonamento**, pico de CPU e
memória por pod e a vazão da carga (apostas por segundo, erros). O **motivo** de cada escalonamento está em
`02-hpa-eventos.txt` (`kubectl describe hpa`: linhas "New size: N; reason: cpu resource utilization
above target"). Limites: amostragem a cada 10 s e o `metrics-server` atrasa 15 a 60 s, então o pico real
pode ser um pouco maior que o registrado; não há gráfico nem latência por requisição sob carga (a latência
só é medida no passo 4, em repouso).

Comece com 50 mil apostas para ver o HPA reagir; suba para 200 mil ou 1 milhão se o nó aguentar.
Se réplicas ficarem `Pending`, o nó está pequeno (`kubectl describe pod`): anote isso, é resultado.

### 3. DLQ

`03-dlq.sh` esvazia as filas, publica (pela API de gerenciamento) duas mensagens e mostra:

- **Cenário A**, fora do contrato (não passa no JSON Schema): rejeitada sem reentregar e vai para a DLQ.
- **Cenário B**, evento válido de um tenant que ainda não existe: o consumidor tenta e, sem sucesso, a
  mensagem vai para a DLQ. Depois o script cria o tenant, reenvia a mensagem e confirma que a linha
  aparece em `fact_bet`: é a "recuperação do estado consistente" descrita no TCC (3.1.5).

Saídas: `03-dlq-mensagens.json` (corpo das mensagens na DLQ), `03-logs-stats.txt` (tentativas nos logs
do stats), `03-resultado.txt`. O dead-lettering do broker segue no modo `at-most-once`
([[DECISIONS-LOG]] 2026-08-03 item 4).

### 4. Cache e RNF03

`04-cache.sh` apaga as chaves do tenant no Redis, mede uma requisição a frio (miss), depois N
requisições a quente (hit) em `GET /api/v1/statistics`, e grava: chaves e TTL (segurança de 1 h),
o JSON do dashboard consolidado, hits/misses do Redis antes e depois e `04-resumo.txt` com p50/p95 e
o veredito de RNF03 (p95 abaixo de 300 ms com cache quente). A medida inclui a rede até o Ingress.

## Passo a passo com as capturas (o que fazer, quando, onde)

Use 3 janelas SSH na máquina Debian e o navegador do seu computador.

**Preparação (uma vez)**

- Janela **B**: `watch -n 3 kubectl get hpa`
- Janela **C**: `watch -n 3 'kubectl get pods | grep -E "auth|bets|stats|gateway"'`
- Janela **A**: onde roda os scripts (`cd ~/sv-harness`).
- Console do RabbitMQ no seu navegador: no seu computador `ssh -L 15672:localhost:15672 eduardo@<ip-do-servidor>`;
  no servidor (janela extra) `kubectl port-forward svc/rabbitmq 15672:15672`; abra `http://localhost:15672`.
  Usuário e senha: `kubectl get secret stakevault-secrets -o jsonpath='{.data.RABBITMQ_USER}' | base64 -d`
  (idem `RABBITMQ_PASSWORD`).

| # | Momento | O que fazer | Captura (janela) | Figura no TCC |
|---|---|---|---|---|
| 1 | Antes de tudo | janela A: `bash tools/evidence/01-baseline.sh` | **B** e **C** com 1 réplica por serviço; **A** com a saída do baseline (versões PG 18/Redis 8, capacidade do nó) | "Ambiente e estado inicial" |
| 2 | Começo da carga | janela A: `bash tools/evidence/02-carga.sh 50000 64` | espere 1 a 3 min; quando a **B** mostrar `REPLICAS` maior que 1 e `TARGETS` acima de 70%, capture **B** e **C** juntas | "HPA elevando réplicas sob carga" |
| 3 | No meio da carga | navegador: RabbitMQ, aba **Queues** | capture a tabela com `stats.bet-events` (Ready, Incoming, Deliver/Get) | "Fila de eventos durante a carga" |
| 4 | Fim da carga | a janela A imprime `02-reconciliacao.txt` e `02-resumo.txt` | capture o final da janela **A** (PASS/FAIL e a tabela de réplicas/pico) | "Reconciliação de eventos" e tabela de pico |
| 5 | ~6 min depois do fim | olhe a janela **B** | capture quando `REPLICAS` voltar a 1 (o HPA espera 300 s para reduzir) | "Redução automática de réplicas" |
| 6 | DLQ | janela A: `bash tools/evidence/03-dlq.sh`; quando pedir **Enter**, vá ao navegador | **Queues**: `stats.bet-events.dlq` com 2 mensagens (Ready 2); clique na fila, **Get messages**, ack mode "Nack message requeue true", **Get Message(s)** e capture o payload; depois volte à janela A e aperte Enter | "Mensagens na DLQ" |
| 7 | DLQ, recuperação | fim do `03-dlq.sh` | capture a janela **A** com `03-resultado.txt` (PASS) e a **Queues** com a DLQ zerada | "Reprocessamento após recuperação" |
| 8 | Cache | janela A: `bash tools/evidence/04-cache.sh <slug> <email> <senha>` (os 3 valores saem no fim do passo 2) | capture o final da janela **A** (`04-resumo.txt`); depois `cat evidence/<pasta>/04-redis-chaves.txt` e capture | "Cache hit/miss e tempo de resposta" |
| 9 | Guardar | `bash tools/evidence/05-coleta.sh evidence/<pasta>`; no seu computador `scp eduardo@<ip>:~/sv-harness/evidence/<pasta>.tar.gz .` | n/a | n/a |

Dica: para capturas de terminal use a tela inteira da janela; para o RabbitMQ, a captura da página inteira.

## Números para o texto do TCC (de onde copiar)

| Número | Arquivo | Linha |
|---|---|---|
| máximo de réplicas e pico de CPU | `02-resumo.txt` | tabela "HPA" |
| tempo até escalar | `02-resumo.txt` | coluna "1o escalonamento" |
| vazão (apostas/s) e erros | `02-resumo.txt` | seção "Carga" |
| eventos publicados = processados | `02-reconciliacao.txt` | linhas com PASS |
| causa do escalonamento | `02-hpa-eventos.txt` | "reason: cpu resource utilization" |
| mensagens na DLQ e recuperação | `03-resultado.txt` | todas |
| p50/p95 do dashboard e RNF03 | `04-resumo.txt` | todas |
| TTL e chaves do cache | `04-redis-chaves.txt` | todas |

Estrutura sugerida no Capítulo 4: **4.4 Avaliação experimental**, com: ambiente (passo 1), escalabilidade
horizontal (passos 2 a 5), resiliência e DLQ (6 e 7), cache e desempenho (8) e limitações (amostragem de 10 s,
um único nó, carga sintética gerada por `tools/load_test_bets.py`).

## Como preencher o TCC

| Afirmação | Onde está a evidência | Reescrita sugerida |
|---|---|---|
| Escalabilidade horizontal (RNF06) | `02-hpa.txt`, `02-pods.txt`, capturas 1 e 2 | "sob carga de N apostas, o HPA elevou X de 1 para Y réplicas e reduziu após a carga" |
| "Nenhuma mensagem é descartada" (3.1.5) | `02-reconciliacao.txt` | "N apostas geraram M eventos; M foram processados, outbox e DLQ vazios" |
| DLQ e reentrega (4.1) | `03-dlq-mensagens.json`, `03-resultado.txt`, captura 3 | "mensagens inválidas ou sem recurso vão à DLQ e, recuperado o recurso, foram reprocessadas" |
| Cache-Aside e RNF03 (3.1.6) | `04-resumo.txt`, `04-redis-chaves.txt` | "p95 de X ms com cache quente (limite 300 ms); primeira requisição Y ms" |

Se algum passo der FAIL, não reescreva a frase do TCC: a causa está nos logs (`kubectl logs deploy/<serviço>`)
e vale abrir uma feature no backlog do serviço correspondente.

## Resultados da rodada de 2026-10-04 (100.000 apostas, 128 threads)

Rodada real no k3s (nó de ~8 CPUs, 16 GB), pasta `evidence/final` na máquina Debian. Tenant `loadtest-0086b111`.

| Medida | Resultado |
|---|---|
| Vazão do gerador | 32,4 apostas/s em 3.089 s (51 min), 26 erros de 100.000 |
| HPA, réplicas máximas | `api-gateway` 4, `auth-service` 3, `bets-service` 4, `stats-service` 4 |
| Pico de CPU (% do `requests.cpu` de 100m) | 290%, 172%, 501% e 495% |
| Tempo até o primeiro escalonamento | 41 s (gateway, auth, bets) e 62 s (stats) |
| Redução | todos voltaram a 1 réplica cerca de 9 min depois do fim da carga |
| Eventos esperados x processados | 193.998 = 193.998 (PASS); `fact_bet` 99.998 = apostas do `bets-service` (PASS); outbox e DLQ em 0 (PASS) |
| Estado final | **18 apostas ficaram `pending` em `fact_bet`** e liquidadas no `bets-service` (0,019% das 94.000 liquidações); `stats-service` `feat-028` |
| Cache (`04-cache.sh`) | miss 2.189,5 ms; hit p50 173,4 ms, p95 206,2 ms, máx. 292,0 ms (RNF03 PASS); 392 hits e 8 misses; 8 chaves por tenant com TTL de ~1 h |
| DLQ | mensagem fora do contrato rejeitada direto para a DLQ; evento válido de tenant inexistente foi para a DLQ depois das tentativas e, criado o tenant, foi reprocessado e gravado em `fact_bet` (PASS) |

Como ler esses números sem afirmar demais:

- **Escalabilidade:** o HPA subiu e desceu os 4 serviços, mas a vazão com réplicas (32,4/s) ficou **abaixo** da
  linha de base de 1 réplica (43,2/s, 50.000 apostas, 64 threads). O gargalo é o PostgreSQL único do `bets-service`:
  `postgres-bets` chegou a 501m de CPU e o `pg_isready` dele estourou o timeout de 1 s. Escrever "elevou réplicas
  sob carga e manteve a consistência dos eventos", nunca "aumentou a vazão".
- **Eventos:** "eventos processados = esperados" vale para a **contagem**. O estado final divergiu em 18 apostas,
  então não escrever "perda zero de estado" (`stats-service` `feat-028`, com a hipótese de corrida em `fact_bet`).
- **Erros do gerador (26):** coincidem com restarts do `bets-service` por falha de liveness (probe de 1 s com limite
  de CPU de 500m) durante a carga; `infra` `feat-012`. Os 26 não são perda de evento, são requisições que falharam na API.
- **Dashboard:** `settledCount` 93.982 contra 94.000 é a mesma divergência das 18 apostas, não erro de cálculo do cache.
- **Limitações:** nó único, um PostgreSQL por serviço, carga sintética de um único processo, amostragem de 10 s do
  `metrics-server` (que atrasa 15 a 60 s), eventos do Kubernetes duram ~1 h.

## Resultados da rodada de 2026-11-01 (100.000 apostas, 128 threads) — a que o TCC usa

Rodada definitiva, depois de `infra` `feat-012` (sondas só da aplicação, `postgres-bets` com 2000m/2Gi) e de
`stats-service` `feat-028` (corrida entre `BetCreated` e `BetSettled`). Mesmo nó: i5-1145G7 (4 núcleos, 8 threads),
16 GB, Debian 13, k3s v1.36.4. Evidência em `evidence/20261101-152144` no Debian (cópia `.tar.gz` com o autor).
Tenant `loadtest-8a365bf8`. O TCC apresenta só esta rodada; a de 04/10 fica aqui como histórico.

| Medida | Resultado |
|---|---|
| Vazão do gerador | **90,1 apostas/s** em 1.109,9 s, **0 erros**, 100.000 de 100.000 (04/10: 32,4/s e 26 erros) |
| HPA, réplicas máximas | `api-gateway` 4, `auth-service` 2, `bets-service` 4, `stats-service` 4 |
| Pico de CPU (% do `requests.cpu` de 100m) | 303%, 127%, 501% e 498% |
| Tempo até o primeiro escalonamento | 40 s (auth) e 61 s (gateway, bets, stats) |
| Pico por pod | `postgres-bets` **1.916m** (limite 2000m); `postgres-stats` 501m e réplicas do stats em 501m (no limite) |
| Redução | auth voltou a 1 durante a carga; gateway e bets ~6 min depois do fim; stats ficou em 4 até a fila esvaziar e a coleta terminou antes da redução dele |
| Fila | **96.822 eventos** em `stats.bet-events` no fim do registro, drenados em ~11 min (consumo, não registro, virou o limite) |
| Eventos esperados x processados | 194.055 = 194.055 (PASS); `fact_bet` 100.000 (PASS); outbox e DLQ em 0 (PASS) |
| Estado final (`02-estado.txt`) | contagens por status **iguais** nos dois bancos (won 44.199, lost 47.112, void 2.744, pending 5.945); a divergência de 18 de 04/10 não se repetiu |
| Cache (`04-cache.sh`, 2ª execução) | miss 1.930,9 ms; hit p50 156,8 ms, p95 193,6 ms, máx. 229,5 ms (RNF03 PASS); 392 hits e 8 misses |
| Reinícios | 0 nos pods de aplicação durante a carga |

Como ler sem afirmar demais:

- **Vazão:** o ganho sobre 04/10 vem dos ajustes do banco e das sondas. Não houve rodada com 1 réplica depois deles,
  então a parcela do ganho devida ao HPA não foi medida.
- **Estado:** `02-estado.txt` compara totais por status, não aposta por aposta.
- **Cache:** o `04-cache.sh` rodou duas vezes (16:00:25 e 16:00:50) e a segunda sobrescreveu os arquivos. A primeira
  teve máx. de 431,7 ms (p95 207,1 ms), registrada só em captura de tela e no `log.txt`. O TCC usa a segunda.
- **DLQ e figuras da fila:** não refeitas nesta rodada; o TCC reaproveita as capturas de 04/10.

## Lições para repetir os testes

- **Atualizar o clone antes de tudo** (`git pull` na pasta `sv-harness` do Debian): um clone antigo roda o
  `02-carga.sh` sem `02-resumo.txt` nem `02-hpa-eventos.txt`, e os eventos do Kubernetes que explicam o
  escalonamento expiram em ~1 h. Se faltar o resumo, `python3 tools/evidence/resumo_carga.py <pasta>` o gera depois
  a partir de `02-hpa.txt`, `02-top.txt` e `02-carga.txt`.
- **Esperar o cluster assentar depois de um boot** (10 a 15 min): a partida simultânea das JVMs estoura os 100m
  de request e faz o HPA subir réplicas sem tráfego, e o `metrics-server` ainda responde com erro. Esses eventos não
  são evidência de carga. Conferir `kubectl get hpa` (todos em 1 réplica) e `kubectl top pods` antes de começar.
- **Uma pasta por rodada** (`export OUT=evidence/<nome>`) e nunca apagar `evidence/`; a pasta de uma rodada perdida
  não se reconstrói.
- **Cache no RedisInsight:** a figura fica melhor com a interface do que com o `cat`. Túnel
  `ssh -L 6379:localhost:6379 <usuario>@<ip>`, no servidor `kubectl port-forward svc/redis 6379:6379`, senha em
  `kubectl get secret stakevault-secrets -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d`. As chaves expiram em 1 h:
  rodar o `04-cache.sh` logo antes da captura.
- **Contadores de fila quorum atrasam** alguns segundos: `03-dlq.sh` espera o contador da DLQ zerar antes de gravar o
  resultado; olhar `rabbitmqctl list_queues` isolado logo depois de um drain pode mostrar o valor antigo.
- O IP do servidor na rede local pode mudar entre boots; `hostname -I` no Debian dá o atual.
- **Túnel antigo na porta 18081:** um `kubectl port-forward` esquecido de rodada anterior aponta para o pod que o
  rollout derrubou e o script falha com `Connection refused` em `localhost:18081`. O `port_forward` do `lib.sh` agora
  aborta com mensagem se o túnel novo não sobe; para limpar: `pkill -f "port-forward svc/auth-service"`.

- **`export OUT` na mesma janela que roda os scripts** (achado de 2026-11-01): exportado em outra aba, o `02-carga.sh`
  cria `evidence/<data-hora>` e o baseline vai para outra pasta. Confira a primeira linha (`saida em ...`).
- **Rodar `04-cache.sh` uma vez só**: cada execução sobrescreve os `04-*.txt`, e a captura de tela precisa ser da
  mesma execução que fica nos arquivos.
- **Senha nas capturas**: o fim do `02-carga.sh` e o comando do `04-cache.sh` mostram a senha do admin do tenant.
  Corte essas linhas antes de usar a captura no TCC.
- **Depois de `rollout restart`, esperar o HPA voltar a 1**: as JVMs subindo juntas levam os 4 serviços a 4 réplicas
  sem tráfego; o baseline só vale com todos em 1.
- **Estado final por status**: o `02-carga.sh` não compara as situações das apostas. Rode o `group by status` em `bet`
  e `fact_bet` e grave em `$OUT/02-estado.txt`.

Os scripts `01` a `04` foram validados contra o cluster real nesta rodada; `05-coleta.sh` é o único ainda sem uso
registrado. Se um comando falhar, o erro aparece no terminal e em `log.txt`.
