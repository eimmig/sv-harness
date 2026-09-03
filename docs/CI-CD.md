---
tags: [conventions, ci-cd]
---

# CI/CD

Convenção de pipeline de integração contínua — evita cada serviço ganhar um workflow diferente
(passos em ordem diferente, gate de cobertura diferente, etc.). Ver [[CONVENTIONS]] (build
tool, i18n), [[TESTING]] (frameworks de teste, meta de cobertura 80%) e [[DECISIONS-LOG]] (data
da decisão).

> **Topologia de repositórios (decisão de 2026-08-02, ver [[DECISIONS-LOG]])**: este projeto não
> é um monorepo — são **7 repositórios GitHub independentes**: 6 por serviço (`api-gateway`,
> `auth-service`, `bets-service`, `stats-service`, `telegram-integration`, `web`) e mais 1,
> `infra`, para os dois epics sem serviço de aplicação próprio (`epic-001`/`epic-007` — Docker
> Compose e o teste de resiliência cross-service). As pastas continuam aninhadas localmente em
> `services/<nome>/`/`apps/web/`/`infra/` dentro desta mesma árvore de trabalho (cada uma com seu
> próprio `.git` interno), só para conveniência de quem trabalha localmente com tudo à vista —
> mas cada uma é hospedada e versionada no GitHub **separadamente**. A **raiz** deste diretório
> (`CLAUDE.md`, `docs/` — este vault —, `feature_list.json`, `progress.md`, `tools/`) é um
> repositório à parte (`sv-harness`, decisão de 2026-08-19 — ver [[DECISIONS-LOG]]) que versiona
> só docs + harness e **não tem pipeline de CI**: não há código de aplicação nem texto de usuário
> ali para build, teste, i18n ou SonarCloud validarem. Consequência prática: cada `.github/workflows/`/`.github/scripts/` vive
> **dentro de cada uma dessas 7 pastas** (`services/<nome>/.github/...`, `apps/web/.github/...`,
> `infra/.github/...`), nunca na raiz — é lá que o GitHub Actions de cada repositório vai
> procurar.

> Estado em 2026-08-02: **scaffolding**. Os 7 repositórios já existem no GitHub (usuário
> `eimmig`), vazios — os workflows abaixo já estão versionados dentro de cada pasta local, mas só
> disparam de verdade quando cada pasta virar de fato aquele repositório (`git init` + `git
> remote add origin` + push) e, para os 6 serviços de aplicação, a organização/projetos do
> SonarCloud forem provisionados (ver seção "Setup pendente" no final — `infra` não usa
> SonarCloud). Nenhum serviço tem código ainda, então nenhum workflow passa hoje — isso é
> esperado, mesma lógica do `init.sh` raiz para sub-harnesses não iniciados.

| Pasta local | Repositório GitHub |
|---|---|
| `services/api-gateway/` | [eimmig/sv-api-gateway](https://github.com/eimmig/sv-api-gateway.git) |
| `services/auth-service/` | [eimmig/sv-auth-backend](https://github.com/eimmig/sv-auth-backend.git) |
| `services/bets-service/` | [eimmig/sv-bets-backend](https://github.com/eimmig/sv-bets-backend.git) |
| `services/stats-service/` | [eimmig/sv-stats-backend](https://github.com/eimmig/sv-stats-backend.git) |
| `services/telegram-integration/` | [eimmig/sv-telegram-integration-backend](https://github.com/eimmig/sv-telegram-integration-backend.git) |
| `apps/web/` | [eimmig/sv-frontend](https://github.com/eimmig/sv-frontend.git) |
| `infra/` | [eimmig/sv-infra-backend](https://github.com/eimmig/sv-infra-backend.git) |

Prefixo `sv-` = **StakeVault**, nome da marca já decidido em [[DESIGN-SYSTEM]] — não é um
prefixo novo/arbitrário.

**Chave de projeto no SonarCloud = `eimmig_<nome-do-repositório>`** (ex.:
`eimmig_sv-bets-backend`), não o nome do repositório sozinho. É o formato que o próprio
SonarCloud gera ao importar um repositório do GitHub — `<org-key>_<repo>` — e adotá-lo evita seis
renomeações manuais na UI só para divergir do padrão da ferramenta. Corrigido em 2026-08-17
(`feat-003.8`): os workflows nasceram com a forma sem prefixo, que produziria erro de projeto
inexistente na primeira análise. A org key `eimmig` chega ao scanner pela variable
`SONAR_ORGANIZATION`; a chave do projeto é literal no `ci.yml` (Java) ou no
`sonar-project.properties` (Python/Angular), porque esse arquivo não interpola variável de
ambiente.

## Um workflow por repositório, sem filtro de path

Como cada serviço (e `infra/`) é seu próprio repositório, `.github/workflows/ci.yml` dentro de
cada pasta dispara em **todo** push/PR daquele repositório — não precisa de `paths:` filtrando
subpastas (não existe outra coisa no mesmo repositório para disparar à toa). Isso é diferente de
um workflow de monorepo com path filter: aqui o próprio limite do repositório já é o limite do
serviço.

Não existe um workflow agregado equivalente ao `init.sh` raiz. O repositório `sv-harness` da
raiz existe, mas ignora `/services/`, `/infra/` e `/apps/` — um workflow rodando lá não teria
acesso a nenhum código de serviço para verificar, e o `init.sh` raiz só agrega o estado local dos
sub-harnesses. Cada repositório de serviço continua sendo o único lugar onde CI roda.

`infra/` segue uma pipeline mais simples (só 2 passos: changelog + `docker compose config`), não
os 5 passos abaixo — não tem texto de usuário (sem passo de i18n), não tem código de aplicação
para o SonarCloud analisar, e "testes unitários" não se aplica a um `docker-compose.yml`. Ver
`infra/CLAUDE.md` e `infra/.github/workflows/ci.yml`.

## Os 5 passos dos serviços de aplicação, sempre nesta ordem

Aplicam-se aos 6 repositórios de serviço (`api-gateway`, `auth-service`, `bets-service`,
`stats-service`, `telegram-integration`, `web`) — não a `infra/`, ver seção anterior.

1. **Changelog**: falha o PR se `CHANGELOG.md` (na raiz do repositório) não foi tocado no diff
   contra a branch base. Script: `.github/scripts/validate-changelog.sh` (dentro do próprio
   repositório). Só roda em `pull_request`, e só quando a base é `develop`/`main` (ver seção
   "Changelog por serviço" abaixo — a linha de cada subtask já existe antes da branch dela
   nascer, então cobrar o toque também no PR de subtask quebraria por sequenciamento).
2. **Validador de chaves de tradução**: confere que os 3 arquivos de locale (`pt-BR`/`en-US`/
   `es`) do serviço têm exatamente o mesmo conjunto de chaves — nenhum idioma "para trás" (ver
   [[CONVENTIONS]] seção "Internacionalização (i18n)": os três sempre em sincronia é requisito
   de `done`, não sugestão). Script: `.github/scripts/validate-i18n-keys.py` (dentro do próprio
   repositório). Caminhos por tipo de serviço, relativos à raiz do repositório:
   - Java (`api-gateway`, `auth-service`, `bets-service`, `stats-service`):
     `src/main/resources/messages_{pt_BR,en_US,es}.properties` (`--format properties`).
   - `web` (Transloco): `src/assets/i18n/{pt-BR,en-US,es}.json` (`--format json`).
   - `telegram-integration`: `locales/{pt-BR,en-US,es}.json` (`--format json`) — formato
     fechado como JSON nesta mesma decisão (ver [[DECISIONS-LOG]]; [[CONVENTIONS]] deixava
     JSON/gettext em aberto).
3. **Build**: compila/instala dependências sem rodar teste ainda (serve para falhar rápido em
   erro de compilação antes de pagar o custo de subir Testcontainers). Java: `mvn -B -DskipTests
   package`. `web`: `npm ci && npm run build`. `telegram-integration`: `uv sync` + `ruff check`
   (Python não compila, mas lint/instalação de deps é o equivalente prático de "build" — ver
   [[CONVENTIONS]] seção Python).
4. **Testes unitários + cobertura**: Java: `mvn -B test jacoco:report` (gera
   `target/site/jacoco/jacoco.xml`, ver [[TESTING]] — o gate de 80% em si já é aplicado pelo
   `mvn verify` do `init.sh` local; aqui o objetivo é gerar o relatório que o Sonar consome, não
   duplicar o gate). `web`: `npm run test -- --code-coverage` (gera `coverage/lcov.info`).
   `telegram-integration`: `uv run pytest --cov=. --cov-report=xml` (gera `coverage.xml`).
5. **Qualidade de código e cobertura (SonarCloud)**: lê o relatório de cobertura gerado no passo
   anterior.
   - Java: `mvn -B sonar:sonar` com o goal totalmente qualificado do
     `sonar-maven-plugin` — não precisa declarar o plugin no `pom.xml`.
   - `web` e `telegram-integration`: `SonarSource/sonarqube-scan-action@v4`, configurado por
     `sonar-project.properties` na raiz do repositório (`sonar.organization`/`sonar.host.url`
     passados via `-D` no workflow, não no arquivo — não interpola variável de ambiente).
   - Projeto SonarCloud por serviço, chave = nome do repositório GitHub (ex.:
     `sv-bets-backend`) — um projeto por repositório, mesma lógica de isolamento por serviço do
     resto do harness. Ver tabela de repositórios no início desta nota.

## Scripts de CI duplicados em cada repositório, não compartilhados

`.github/scripts/validate-changelog.sh` existe **em cada um dos 7 repositórios**, e
`validate-i18n-keys.py` nos 6 de aplicação (`infra/` não tem i18n) — mesmo conteúdo em todos —
decisão de 2026-08-02 (ver [[DECISIONS-LOG]]): como não há um repositório-raiz compartilhado
para os outros referenciarem, a alternativa a duplicar seria mais um repositório só para tooling
de CI, referenciado via `uses: org/ci-shared@ref` — descartada por adicionar complexidade de
versionamento entre repositórios desproporcional ao tamanho do projeto. Custo aceito: uma
mudança nesses scripts precisa ser replicada manualmente em cada lugar (baixa frequência
esperada).

## Changelog por serviço

`CHANGELOG.md` na **raiz de cada repositório** (`services/<nome>/CHANGELOG.md`,
`apps/web/CHANGELOG.md`, `infra/CHANGELOG.md` — na cópia de trabalho local, vira a raiz de
verdade quando cada pasta virar seu próprio repositório). **Não** é Keep a Changelog com prosa
categorizada em `Added`/`Changed`/`Fixed` (decisão revista em 2026-09-03) — cada linha de
`## [Unreleased]` é só um link para a issue do Jira que a gerou, sem descrição:

```
- [SV-10](https://stakevault.atlassian.net/browse/SV-10) - Setup do projeto
- [SV-11](https://stakevault.atlassian.net/browse/SV-11) - Bootstrap do pom.xml e esqueleto hexagonal
```

Uma linha por issue (story **e** cada subtask), `[chave](url) - título`, nada além disso — sem
data, sem categoria, sem corpo. **Escrita automaticamente por `tools/jira_story.py`**, no exato
momento em que cada issue é criada (chamada simples cria a story + todas as subtasks já
planejadas pelo `Plan Reviewer` de uma vez; `--update` acrescenta a linha de uma subtask
descoberta depois). A sessão nunca escreve essa linha à mão — o formato vem sempre do script,
idempotente (rodar de novo não duplica). O texto que explicava a mudança agora vive só na issue
do Jira (`description` da story/subtask) e na mensagem de commit — o `CHANGELOG.md` é apenas o
índice rastreável, o Jira é onde o "porquê" mora.

Consequência de sequenciamento: como a linha de cada subtask nasce **antes** da branch daquela
subtask existir (a chave só existe depois que `jira_story.py` roda, e a branch só nasce depois de
ter a chave — ver [[CONVENTIONS]] seção "Git"), o próprio diff de uma PR `subtask/` → branch da
story **nunca** toca `CHANGELOG.md` — a linha já estava lá quando a branch foi criada. Por isso o
passo 1 (changelog) só roda de fato na PR story → `develop` (guarda por `github.base_ref`, mesmo
mecanismo já usado no passo 5/Sonar) — exigir o toque também no PR de subtask quebraria por
sequenciamento, não por esquecimento real.

### Quais passos rodam em qual PR

O modelo de branch tem 4 níveis (ver [[CONVENTIONS]] seção "Git"), então nem todo passo faz
sentido em todo PR:

| Passo | `subtask/` → story | story → `develop` | push em `main`/`develop` |
|---|---|---|---|
| Changelog | **não** | sim | não (só em PR) |
| i18n / build / testes | sim | sim | sim |
| SonarCloud | **não** | sim | sim |

O SonarCloud é pulado no PR de subtask (condição sobre `github.base_ref` no `ci.yml`) porque o
quality gate mede **código novo**: uma feature pela metade — código já escrito, testes ainda na
subtask seguinte — reprovaria sem indicar defeito real, e bloquearia o merge por um motivo que
não é qualidade. A análise acontece na story, onde a feature está completa. `infra/` não usa
SonarCloud, então a coluna não se aplica lá. O Changelog é pulado no PR de subtask pelo motivo
oposto (não é sobre qualidade, é sequenciamento): a linha daquela subtask já existe desde antes
da branch nascer — ver seção anterior.

## Setup pendente (uma vez por repositório, quando cada um for criado)

Repetir para cada um dos 6 serviços de aplicação (`infra/` só precisa do passo 1 — não usa
SonarCloud):

1. Dentro da pasta (`services/<nome>/`, `apps/web/` ou `infra/`): `git init -b main`, `git
   remote add origin <url da tabela acima>` (já feito em 2026-08-02 — ver [[DECISIONS-LOG]]),
   primeiro commit + push em `main`, depois `git checkout -b develop` + `git push -u origin
   develop` — ver [[CONVENTIONS]] seção "Git" para o modelo de 3 branches
   (`main`/`develop`/`feature`-`bugfix`-`spike`).
2. Criar o projeto correspondente no SonarCloud (mesma organização para os 6 serviços de
   aplicação, chave = nome do repositório, ex. `sv-bets-backend`).
3. Gerar um token do SonarCloud e configurar como secret `SONAR_TOKEN` **naquele** repositório
   GitHub (segredo por repositório, não compartilhado).
4. Configurar a variable (não secret — não é sensível) `SONAR_ORGANIZATION` **naquele**
   repositório GitHub com o org key do SonarCloud (a mesma organização vale para os 6, mas a
   variable é configurada em cada repo individualmente — GitHub não compartilha variables entre
   repositórios distintos automaticamente).

Sem os passos 2–4 (por repositório de aplicação), o workflow daquele serviço existe mas falha no
passo 5 (Sonar) por falta de credencial — comportamento esperado, não um bug do workflow.

> **Concluído em 2026-08-17** (`infra/feat-003`, `epic-009` — antecipado para antes de qualquer
> implementação, a pedido do usuário, em vez de ficar agendado para `auth-service/feat-001` como
> se decidiu mais cedo no mesmo dia). Os 7 repositórios têm `main` e `develop` publicados; os 6 de
> aplicação têm o secret `SONAR_TOKEN` e a variable `SONAR_ORGANIZATION` configurados, e os 6
> projetos existem no SonarCloud sob a organização `eimmig`. Distribuição feita por
> `tools/sonar_setup.py` (lê `tools/.sonar.env`, valida token/organização/projetos contra a API do
> SonarCloud e grava via `gh`, sem imprimir o token). Rode `python tools/sonar_setup.py --check`
> para reconferir o estado a qualquer momento.
>
> Foi descartada a alternativa de tornar o passo do Sonar não-bloqueante (`continue-on-error`):
> enfraqueceria o gate de qualidade de forma permanente para contornar uma situação temporária. Em
> vez disso, os passos 2–5 são pulados por **guarda de arquivo-marcador** enquanto o repositório
> não tem projeto — ver a seção seguinte.

## Guarda por arquivo-marcador: CI verde em repositório sem código

Cada passo dos workflows dos 6 repositórios de aplicação roda apenas quando o projeto daquele
repositório existe:

| Repositório | Marcador (`if: hashFiles(...) != ''`) |
|---|---|
| `sv-api-gateway`, `sv-auth-backend`, `sv-bets-backend`, `sv-stats-backend` | `pom.xml` |
| `sv-telegram-integration-backend` | `pyproject.toml` |
| `sv-frontend` | `package-lock.json` |

Vale para os passos 2–5 **e para os steps de setup de toolchain** — não é detalhe: `actions/setup-node`
com `cache: npm` **falha o job** quando não há lockfile, em vez de apenas não fazer nada
([actions/setup-node#282](https://github.com/actions/setup-node/issues/282)). Por isso o marcador do
frontend é `package-lock.json` e não `package.json`: tanto o cache quanto o `npm ci` precisam do
lockfile, não do manifesto.

Efeito: um repositório só com harness reporta **success** com todos esses passos `skipped`, e o
gate liga sozinho no `feat-001` de cada serviço, quando o marcador passar a existir — sem editar
workflow nenhum. Isso é diferente de `continue-on-error`, que esconderia falha real depois que o
projeto existir.

**Gotcha encontrado em `sv-auth-backend` (2026-09-03, durante `feat-001.1`)**: o desenho acima
assume `feat-001` como unidade atômica — pom.xml e os arquivos de mensagem de i18n nascendo no
mesmo commit. Mas o `Plan Reviewer` (ver `plan_review` de `services/auth-service/feature_list.json`
`feat-001`) dividiu a feature em 8 subtasks incrementais, cada uma com PR/gate de CI próprio
(`subtask/SV-* → feature/SV-10`) — e `pom.xml` nasce na primeira subtask (esqueleto), enquanto
`messages_pt_BR.properties` só nasce numa subtask bem mais à frente (scaffold de i18n). Com o
passo 2 guardado só por `pom.xml`, os PRs das subtasks intermediárias quebrariam na validação de
i18n por **sequenciamento**, não por defeito real. Corrigido em `sv-auth-backend/.github/workflows/ci.yml`:
o passo 2 ganhou marcador **próprio** (`messages_pt_BR.properties`), independente do `pom.xml`
que guarda os passos 3–5. **Mesma armadilha latente ainda não corrigida nos outros 3 repositórios
Java** (`sv-api-gateway`, `sv-bets-backend`, `sv-stats-backend`) e potencialmente em
`sv-frontend`/`sv-telegram-integration-backend` se o `feat-001` deles também for dividido em
subtasks incrementais — cada um deve aplicar a mesma correção (marcador do passo de i18n = o
primeiro arquivo de tradução daquele stack, não o marcador geral do repositório) quando chegar a
vez de bootstrapar seu próprio `feat-001`, não só copiar o `ci.yml` atual do `auth-service` sem
essa correção.

**Segunda armadilha do mesmo dia**: o passo 4 chamava `mvn test jacoco:report` — um goal solto
que exige o plugin JaCoCo já declarado no `pom.xml`. Como o plugin só entra numa subtask
posterior (gate de cobertura), o mesmo desalinhamento pom.xml-nasce-antes se repetiu, agora
quebrando o passo 4 em vez do passo 2. Corrigido trocando para `mvn -B verify`: os testes rodam
normalmente desde a primeira subtask com `pom.xml`, e quando o plugin JaCoCo for configurado
(vinculado às fases do lifecycle via `<executions>`, não invocado como goal solto), `mvn verify`
passa a gerar e checar a cobertura sozinho — sem precisar tocar no workflow de novo. Lição geral
para os outros repositórios: qualquer passo de CI que dependa de uma ferramenta/plugin
configurada numa subtask posterior à que introduz o `pom.xml`/`pyproject.toml`/`package-lock.json`
precisa do mesmo tratamento — goal solto ou verificação de conteúdo específico quebra por
sequenciamento, não por defeito.

**Terceira armadilha, esta pré-existente desde `epic-009`, não causada pela divisão em
subtasks**: o passo 5 chamava `mvn sonar:sonar` (atalho de prefixo). Esse atalho só resolve se
`org.sonarsource.scanner.maven` estiver em `<pluginGroups>` do `settings.xml` do runner ou já
referenciado em algum `<plugin>` do `pom.xml` — nenhum dos dois é o caso em nenhum dos 6
repositórios, então o erro é sempre `No plugin found for prefix 'sonar'`, nunca uma falha real de
análise. Passou despercebido em `epic-009` porque o passo nunca chegou a rodar de fato (nenhum
repositório tinha `pom.xml`/testes reais ainda). Corrigido em `sv-auth-backend` para as
coordenadas completas do plugin (`org.sonarsource.scanner.maven:sonar-maven-plugin:5.7.0.6970:sonar`,
versão pinada) em vez do atalho — não depende de nada estar declarado no `pom.xml`. **Mesma
correção pendente nos outros 5 `ci.yml`** quando cada repositório chegar ao próprio `feat-001`.

Os scripts em `.github/scripts/` são versionados como `100755`. O Windows reporta
`core.fileMode=false`, então o bit precisa ser posto no índice (`git update-index --chmod=+x`); sem
isso o `run:` que os invoca direto quebra com *Permission denied* no primeiro PR. `init.sh` tem o
mesmo tratamento — a CI não o chama, mas o `CLAUDE.md` manda rodá-lo, e um clone Linux não
conseguiria.

## Consultar o resultado da CI a partir de uma sessão

`gh` (GitHub CLI) está instalado desde 2026-08-17 em
`C:\Program Files\GitHub CLI\gh.exe` — **fora do `PATH` de sessões já abertas** (um terminal novo
o enxerga; uma sessão antiga precisa do caminho completo).

**`gh auth login --with-token` não funciona com a credencial que o Git já usa neste ambiente**: o
Windows Credential Manager guarda um PAT clássico de 40 caracteres, e o `login` exige o escopo
`read:org`, que ele não tem — falha com `error validating token: missing required scope
'read:org'`. Isso **não** impede o uso: `GH_TOKEN` pula a validação de login e o escopo `repo`
basta para ler Actions. Padrão que funciona:

```bash
export GH_TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill \
  | sed -n 's/^password=//p')
gh run list --limit 5
gh run view <id> --json jobs --jq '.jobs[] | .steps[] | "\(.conclusion)\t\(.name)"'
```

O segundo comando é o que prova a **guarda por arquivo-marcador**: num repositório só com
harness o esperado é `checkout` em `success` e todos os passos seguintes em `skipped`, com o job
verde. Job verde com passos *executados* num repositório sem código significaria que a guarda
não está fazendo efeito.

Sem `GH_TOKEN`, a API pública responde `403 rate limit exceeded` rápido (60 requisições/hora por
IP) — não confunda isso com repositório privado ou com falha de pipeline.

## Ver também

- [[CONVENTIONS]] — build tool por stack, i18n (formato dos arquivos de tradução validados no
  passo 2).
- [[TESTING]] — frameworks de teste e meta de cobertura 80% (o gate em si roda local via
  `init.sh`/`mvn verify`; o CI consome o relatório, não reimplementa o gate).
- [[DECISIONS-LOG]] — data e racional da decisão de SonarCloud, formato JSON para i18n do
  Python, e da topologia de 7 repositórios independentes (em vez de monorepo), incluindo por que
  `infra/` existe como repositório próprio.
