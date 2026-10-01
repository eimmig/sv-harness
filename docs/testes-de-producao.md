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

## Capturas de tela a tirar à mão

1. Terminal com `kubectl get hpa -w` durante a carga (REPLICAS subindo de 1 e depois descendo após ~5 min).
2. Terminal com `kubectl get pods` mostrando as réplicas novas.
3. Console do RabbitMQ (`kubectl port-forward svc/rabbitmq 15672:15672`, abrir `http://localhost:15672`):
   página **Queues** com `stats.bet-events` e `stats.bet-events.dlq`, e na DLQ **Get messages** (mensagens
   com o payload visível) depois do `03-dlq.sh`.
4. Terminal com o `04-resumo.txt` e `04-redis-chaves.txt` (ou `redis-cli --scan` e `ttl`).

## Como preencher o TCC

| Afirmação | Onde está a evidência | Reescrita sugerida |
|---|---|---|
| Escalabilidade horizontal (RNF06) | `02-hpa.txt`, `02-pods.txt`, capturas 1 e 2 | "sob carga de N apostas, o HPA elevou X de 1 para Y réplicas e reduziu após a carga" |
| "Nenhuma mensagem é descartada" (3.1.5) | `02-reconciliacao.txt` | "N apostas geraram M eventos; M foram processados, outbox e DLQ vazios" |
| DLQ e reentrega (4.1) | `03-dlq-mensagens.json`, `03-resultado.txt`, captura 3 | "mensagens inválidas ou sem recurso vão à DLQ e, recuperado o recurso, foram reprocessadas" |
| Cache-Aside e RNF03 (3.1.6) | `04-resumo.txt`, `04-redis-chaves.txt` | "p95 de X ms com cache quente (limite 300 ms); primeira requisição Y ms" |

Se algum passo der FAIL, não reescreva a frase do TCC: a causa está nos logs (`kubectl logs deploy/<serviço>`)
e vale abrir uma feature no backlog do serviço correspondente.

Os scripts não foram executados contra o cluster real por quem os escreveu (não havia cluster acessível):
o primeiro uso é também a validação deles; se um comando falhar, o erro aparece no terminal e em `log.txt`.
