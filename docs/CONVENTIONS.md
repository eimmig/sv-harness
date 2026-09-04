---
tags: [conventions, architecture]
---

# Convenções de código e arquitetura

Decisões que valem para **todos** os serviços, para que sessões diferentes (ou serviços
diferentes) não cheguem a soluções distintas para o mesmo problema. Ver [[ARCHITECTURE]] para
a arquitetura de sistema (microsserviços/infra); esta nota é sobre a arquitetura *dentro* de
cada serviço. Ver também [[TESTING]], [[API-CONTRACTS]] e [[OBSERVABILITY-AND-CONFIG]].

> Nada disto foi especificado no TCC 1 (que cobre requisitos, modelagem de dados e arquitetura
> de implantação, não a organização interna do código) — são decisões tomadas para fechar
> lacunas antes da implementação, para reduzir divergência entre serviços e sessões.

> Tema, paleta de cores e inventário de componentes de `apps/web` são tratados em nota separada
> — ver [[DESIGN-SYSTEM]] — para não misturar decisão visual com arquitetura de código nesta
> nota.

## Arquitetura interna dos serviços Java (auth-service, bets-service, stats-service)

**Hexagonal / Ports & Adapters**, igual nos três serviços:

```
src/main/java/com/eduardoimmig/betting/<servico>/
  domain/
    model/            entidades e value objects de domínio (Java puro, sem anotações de framework)
    port/in/           interfaces de caso de uso (o que o serviço faz) — ex.: RegistrarApostaUseCase
    port/out/          interfaces de dependências externas (o que o serviço precisa) — ex.: ApostaRepository, EventPublisher
  application/          implementações dos port/in, orquestram o domínio e chamam port/out
  adapter/
    in/web/             controllers REST (Spring MVC) — traduzem HTTP <-> chamadas ao port/in
    in/messaging/        consumidores RabbitMQ (apenas stats-service) — traduzem evento <-> chamada ao port/in
    out/persistence/     implementações JPA dos port/out (entidades JPA, repositórios Spring Data)
    out/messaging/        publicadores RabbitMQ (apenas bets-service) — implementam port/out de publicação de evento
  config/                configuração Spring (beans, security, RabbitMQ, etc.)
```

Regra prática: `domain/` nunca importa `org.springframework.*` nem `jakarta.persistence.*`. Se
uma classe de domínio precisa de uma anotação de framework, ela pertence a `adapter/`, não a
`domain/`.

- `telegram-integration` (Python) não segue este layout — ver seção Python abaixo.
- `apps/web` (Angular) não segue este layout — ver seção Frontend abaixo.

## Build tool

**Maven** nos três serviços Java (não Gradle) — escolha única para não ter cada serviço com um
sistema de build diferente. `pom.xml` na raiz de cada serviço (não é um monorepo Maven
multi-módulo — cada serviço é buildado e versionado de forma independente, coerente com a
arquitetura de microsserviços).

GroupId: `com.stakevault.betting` (nome do produto, ver [[DESIGN-SYSTEM]] — corrigido em
2026-09-03, era `com.eduardoimmig.betting` até `auth-service feat-001`), artifactId = nome do
serviço (`auth-service`, `bets-service`, `stats-service`).

**Geração inicial do `pom.xml`** (decisão de 2026-08-02, vale também para `api-gateway`): via
**Spring Initializr** (`curl` para a API do `start.spring.io`, não preenchido manualmente) — no
momento desta decisão, `start.spring.io` reporta Spring Boot `4.1.0.RELEASE` como default e Java
25 disponível, batendo com o já decidido acima. Motivo: garante `parent`/versões de dependência
compatíveis entre si, em vez de digitadas de memória com risco de combinação incompatível. O
esqueleto gerado (layout padrão `src/main/java/.../Application.java`) é reestruturado
manualmente logo em seguida para o layout hexagonal descrito acima — o Initializr não conhece
essa convenção, só entrega o `pom.xml` e o ponto de entrada.

## Padrões de código Java

- **Nunca usar `@Autowired`** (decisão de 2026-09-04): injeção sempre via construtor, campo
  `final`, sem a anotação — Spring injeta sozinho quando só existe um construtor. Vale também
  para classe de teste: `spring.test.constructor.autowire.mode=all` em
  `src/test/resources/junit-platform.properties` (um arquivo por serviço) habilita injeção por
  construtor nos testes `@SpringBootTest`, sem precisar de `@TestConstructor` em cada classe.
- **DTOs e value objects imutáveis**: `record` do Java (25 tem suporte pleno), não classes com
  getters/setters manuais.
- **Entidades JPA**: usar Lombok (`@Getter`, `@Setter`, `@NoArgsConstructor`,
  `@AllArgsConstructor`) apenas em `adapter/out/persistence/` — JPA exige construtor sem
  argumentos e mutabilidade, incompatível com `record`. Fora de `adapter/out/persistence/`,
  não usar Lombok.
- **Validação de entrada**: Bean Validation (`jakarta.validation`, ex.: `@NotNull`, `@Positive`)
  nos DTOs de `adapter/in/web/`. O domínio valida suas próprias invariantes (RN02, RN03, RN07
  etc.) via exceptions de domínio, independente do framework de validação.
- **Tratamento de erro**: exceptions de domínio customizadas (ex.: `OddInvalidaException`,
  `StakeNegativoException`) lançadas em `domain/`/`application/`, capturadas por um
  `@RestControllerAdvice` em `adapter/in/web/` que as traduz para respostas
  `application/problem+json` (ver [[API-CONTRACTS]]) com `title`/`detail` localizados (ver seção
  "Internacionalização (i18n)" abaixo) — a exception carrega uma chave de mensagem, não o texto
  final.
- **Migrations**: Flyway, arquivos em `src/main/resources/db/migration/`, nomeados
  `V{date_now}__descricao_em_snake_case.sql` (ex.: `V2026080119170000__create_user_table.sql`). Nunca editar uma
  migration já commitada — sempre criar uma nova.
- **Migração lazy por schema** (decisão de 2026-08-02, ver [[DECISIONS-LOG]]): em
  `auth-service`, `bets-service` e `stats-service` (schema-per-tenant, ver [[ARCHITECTURE]]), o
  Flyway **não** migra uma lista fixa de schemas no boot. Em vez disso, o schema do tenant
  resolvido a partir de `X-Tenant-Id` (ver [[API-CONTRACTS]]) é verificado/migrado sob demanda,
  antes de a requisição chegar ao controller — mesmo ponto de código que resolve o schema da
  conexão (`SET search_path`/multi-tenant provider) também garante que ele está em dia. Evita
  ter que migrar N schemas de tenant a cada deploy e cobre schemas criados depois que a
  aplicação já subiu.
- **Nomenclatura de schema de tenant**: `tenant_<slug>` (snake_case, derivado deterministicamente
  do slug da organização informado na criação do tenant) — sem tabela de diretório adicional
  para mapear slug → nome de schema; unicidade é garantida pelo próprio Postgres (`CREATE
  SCHEMA` falha se o schema já existir).
- **Multi-tenancy do Hibernate por schema** (decidido em `auth-service feat-002`, vale para os 3
  serviços Java schema-per-tenant): `CurrentTenantIdentifierResolver<String>` (lê o contexto de
  tenant já resolvido pelo filtro HTTP; sem tenant resolvido, usa `public`) +
  `MultiTenantConnectionProvider<String>` (`Connection.setSchema(...)` no checkout da conexão —
  o driver do Postgres já traduz isso para `SET SEARCH_PATH` internamente —, reset para `public`
  no release, tratando falha de `setSchema()` sem vazar a conexão do pool), registrados via
  `HibernatePropertiesCustomizer`. Chaves de propriedade confirmadas por `javap` contra o jar
  real instalado (Hibernate ORM 7.x): `org.hibernate.cfg.MultiTenancySettings.
  MULTI_TENANT_CONNECTION_PROVIDER` (`hibernate.multi_tenant_connection_provider`) e
  `MULTI_TENANT_IDENTIFIER_RESOLVER` (`hibernate.tenant_identifier_resolver`) — não existe mais
  `hibernate.multiTenancy=SCHEMA` (isso era Hibernate 5). Confirmar de novo contra o jar
  instalado antes de reaproveitar, versão pode ter mudado. O contexto de tenant resolvido pelo
  filtro HTTP (`X-Tenant-Id`) fica num `ThreadLocal`, exposto também via MDC para log — só é
  seguro em requisição síncrona (Spring MVC bloqueante, sem `@Async`/WebFlux); se algum serviço
  passar a usar dispatch assíncrono, esse mecanismo de propagação precisa ser revisto.
- **Entidade JPA com id atribuído pelo domínio**: implementar `Persistable<UUID>` (campo
  `@Transient boolean isNew = true`, `@PostLoad` vira `false`) — sem isso, todo `save()` de uma
  linha nova é tratado como possível update (`merge()` + `SELECT` extra a cada inserção, porque
  o id já vem preenchido e não é `null`). `save()` assim construído só serve para criar, não para
  atualizar uma linha já existente.
- **Enum persistido com valor diferente do nome Java** (ex.: `Role.ADMIN`/`MEMBER` gravado como
  `'admin'`/`'member'` para bater com `CHECK` da migration): `AttributeConverter` dedicado com
  `@Converter(autoApply = true)`, nunca `@Enumerated(EnumType.STRING)` puro (grava o nome Java
  literal, maiúsculo).
- **Lombok + Java 25**: `maven-compiler-plugin` precisa de `annotationProcessorPaths` explícito
  apontando pro Lombok — só declarar a dependência (mesmo com escopo `provided`) não basta nesta
  combinação de `javac`/Lombok, o processamento de anotação é pulado em silêncio (sem erro, sem
  aviso) e os métodos gerados (`getX()`, construtor, etc.) simplesmente não existem no `.class`.

## Internacionalização (i18n)

Decisão explícita do usuário (2026-08-01): o sistema é **100% internacionalizável**. Dois
princípios que não se misturam (ver também [[API-CONTRACTS]] seção "Internacionalização"):

- **Superfície técnica (rotas, query params, nomes/valores de evento, chaves de cache, nomes de
  campo) é sempre em inglês, nunca localizada** — não muda com o idioma do usuário.
- **Todo texto voltado ao usuário final é localizado, nunca hardcoded num idioma só** — título e
  detalhe de erro de API, toda string de UI, e as mensagens que `telegram-integration` envia de
  volta ao usuário no bot.
- **Idiomas suportados, sempre os três em sincronia**: `pt-BR`, `en-US`, `es` — nenhuma feature
  que introduz texto novo é considerada `done` (ver `CLAUDE.md` da raiz) se traduzir para só um
  ou dois dos três. Não há "idioma principal com os outros pendentes".

### Backend Java (auth-service, bets-service, stats-service, api-gateway)

- Mensagens de erro (`title`/`detail` do RFC 7807, ver [[API-CONTRACTS]]) resolvidas via Spring
  `MessageSource` + `ResourceBundle` (`messages_pt_BR.properties`, `messages_en_US.properties`,
  `messages_es.properties`, uma chave por tipo de erro), escolhidas pelo `LocaleResolver` a
  partir do header `Accept-Language` da requisição. Sem header reconhecido, cai em `pt-BR`
  (idioma padrão). O `type` da resposta (slug em inglês) nunca muda com o locale — só
  `title`/`detail`.
- Exceptions de domínio (ver seção "Padrões de código Java" acima) carregam uma chave de
  mensagem (ex.: `error.invalid-odd`), não o texto final — o `@RestControllerAdvice` resolve o
  texto no locale da requisição, nunca a camada de domínio.

### Frontend (apps/web)

- Biblioteca de tradução em **runtime** (decisão do usuário — não `@angular/localize`
  build-time): **`@jsverse/transloco`** — suporte nativo a Signals (consistente com o
  gerenciamento de estado já decidido abaixo), arquivos de tradução JSON por locale
  (`pt-BR.json`, `en-US.json`, `es.json`), troca de idioma instantânea sem reload nem rebuild,
  um único build para os três idiomas. Mesma filosofia do toggle de tema claro/escuro (ver
  [[DESIGN-SYSTEM]]) — troca em runtime, preferência persistida em `localStorage`, com fallback
  inicial para o idioma do navegador.
- Nenhum componente tem string de UI hardcoded — toda label/mensagem passa pela chave de
  tradução (`transloco()`/pipe `| transloco`), mesmo em componentes pequenos.
- Formatação de número/moeda/data respeita o locale ativo (`Intl.NumberFormat`/
  `Intl.DateTimeFormat` do próprio TypeScript, ou os pipes do Angular com o locale do
  `LOCALE_ID` sincronizado ao locale do Transloco) — importante para valores de aposta/saldo
  (RN01–RN04), já que `1.234,56` (pt-BR) e `1,234.56` (en-US) usam separadores invertidos.

### Python (telegram-integration)

- Mensagens que o bot envia de volta ao usuário (ex.: "conta ainda não vinculada", confirmações
  de captura de aposta) também são localizadas — não é só o frontend. Mecanismo: dicionário de
  strings por locale, um arquivo **JSON** por idioma em `locales/{pt-BR,en-US,es}.json` (decisão
  fechada em 2026-08-02, ver [[DECISIONS-LOG]] — evita introduzir `gettext` como dependência só
  para isso, e usa o mesmo formato de [[web]]), selecionado pelo campo `language_code` que o
  próprio Telegram Bot API já envia em todo update — não é necessário armazenar preferência de
  idioma em nenhum serviço para isso. Formato validado automaticamente pelo passo de i18n da
  pipeline de CI — ver [[CI-CD]].

## Frontend (apps/web — Angular 21.x + TypeScript ES2025)

- **Componentes standalone** (padrão do Angular moderno), sem `NgModule` desnecessário.
- **Gerenciamento de estado: Signals nativos** do Angular, não NgRx. `signal()`/`computed()`
  para estado de componente e de serviços compartilhados (ex.: usuário autenticado, filtros do
  dashboard); evitar `BehaviorSubject`/RxJS para estado simples — reservar RxJS para streams
  assíncronos reais (requisições HTTP, websockets, se vierem a existir).
- **Formulários**: Reactive Forms (`FormGroup`/`FormControl`) no formulário de registro de
  apostas, não Template-Driven Forms — necessário para validação estruturada e feedback claro
  (regras de Shneiderman, ver [[web]]).
- **Estilo**: SCSS por componente (`:host`), utilizando Angular Material. Tema (claro/escuro),
  paleta de cores e inventário de componentes visuais já decididos em [[DESIGN-SYSTEM]] — não
  escolher uma paleta alternativa por conta própria.
- **i18n**: `@jsverse/transloco`, três locales sempre em sincronia (`pt-BR`/`en-US`/`es`) — ver
  seção "Internacionalização (i18n)" acima, não hardcodar strings de UI.
- **Cliente HTTP**: serviços Angular tipados por domínio (`AuthService`, `BetsService`,
  `StatsService`), um por serviço backend consumido, usando os tipos documentados em
  [[API-CONTRACTS]]. Não gerar cliente automaticamente a partir de OpenAPI neste projeto (escopo
  pequeno o suficiente para não justificar a ferramenta extra) — mas manter os tipos TypeScript
  sincronizados manualmente com os DTOs Java é responsabilidade de quem mexe na feature.
- **Nunca usar `any`** (decisão de 2026-09-04): todo tipo é explícito — `unknown` + type guard
  quando o tipo de fato não é conhecido em tempo de compilação, nunca `any` como atalho. Vale
  para parâmetro, retorno, variável e genérico.
- **QA visual (Impeccable/taste-skill)**: ferramentas de design guidance para agentes de IA,
  usadas só como auditoria/polish de componentes já implementados contra [[DESIGN-SYSTEM]] —
  nunca como fonte de novas decisões de design (esse documento já é a fonte de verdade). Ver
  [[DESIGN-SYSTEM]] seção "QA visual" para o racional completo e status de instalação.

## Python (telegram-integration)

- Gerenciador de dependências: **uv** (mais rápido, `pyproject.toml` único, sem `requirements.txt`
  espalhado) — se um agente sessão futura preferir Poetry/pip puro, deve primeiro atualizar esta
  nota, não decidir isoladamente dentro da pasta do serviço.
- Formatação/lint: `ruff` (format + lint em uma ferramenta só).
- Tipagem: usar type hints (`from __future__ import annotations` se necessário) e `mypy` no CI
  local, mesmo em um serviço pequeno — facilita retomar o código entre sessões.
- **i18n**: mensagens do bot para o usuário são localizadas (`pt-BR`/`en-US`/`es`) via o
  `language_code` do update do Telegram — ver seção "Internacionalização (i18n)" acima.

## Git — fluxo de trabalho

Modelo de **4 níveis** de branch (3 níveis decididos em 2026-08-02; o nível de subtask entrou em
2026-08-03 junto com o espelhamento no Jira — ver [[DECISIONS-LOG]]), igual nos 7 repositórios
**de código** (cada serviço e `infra/` — ver [[CI-CD]]). O repositório `sv-harness` da raiz é a
exceção deliberada: docs + harness, sem build nem CI, vive numa única branch `master` com commits
diretos — ver [[DECISIONS-LOG]] 2026-08-19. O fluxo de branch/merge/gate descrito abaixo vale
para os 7, não para ele. O formato de **mensagem de commit** (Conventional Commits 1.0.0, em
inglês) vale para todos, mas nos commits do `sv-harness` os rodapés `Refs:`/`Feature:` são
omitidos: não há story do Jira nem feature de harness por trás de uma mudança de docs. Escopo
sugerido ali: `docs`, `harness`, `tools`.

```
main
 └── develop
      └── feature/SV-12          (story — base a partir de develop)
           ├── subtask/SV-13     (subtask — base a partir da branch da story)
           ├── subtask/SV-14
           └── subtask/SV-15
```

O merge sobe um nível por vez, sempre `--no-ff`: `subtask/SV-13` → `feature/SV-12` → `develop`.

- **`main`**: branch estável/entregável. Nunca recebe commit direto — só merge vindo de
  `develop`.
- **`develop`**: branch de integração. Base de toda `feature/`/`bugfix/`/`spike/`, e destino do
  PR delas. Criada a partir de `main` no primeiro commit de cada repositório (`git checkout -b
  develop` logo após o commit inicial em `main`, depois `git push -u origin develop`).
- **Branch de trabalho**, prefixo conforme o tipo. Cada branch leva **a chave da sua própria
  issue no Jira** (decisão de 2026-08-03, ver [[DECISIONS-LOG]] — reverte o uso do id do
  `feature_list.json` que valia antes):
  - `feature/<chave-da-story>` — feature nova, a partir de `develop` (ex.: `feature/SV-12`).
    Consequência de ordem: a story precisa existir **antes** da branch, então o fluxo é
    `Plan Reviewer` → `plan_review` e `subtasks` preenchidos → `tools/jira_story.py` cria story e
    sub-tasks → só então `git checkout -b feature/SV-12`. As chaves ficam gravadas em `jira`
    (feature e cada subtask), então sessão sem acesso à rede continua sabendo os nomes de branch
    sem consultar o Jira.
    > **Não commitar a saída do `jira_story.py` em `develop` antes de criar a branch** (achado
    > real de `auth-service feat-002`/SV-22, 2026-09-04): `jira_story.py` grava as linhas de
    > `CHANGELOG.md` de toda a story no exato momento em que cria as issues — se esse commit for
    > feito em `develop` e só depois vier o `git checkout -b feature/SV-12`, a branch da feature
    > nasce já com as linhas, `CHANGELOG.md` nunca mais é tocado nela (nenhuma subtask toca, ver
    > seção "Changelog por serviço" de [[CI-CD]]), e a PR final `feature/` → `develop` mostra
    > diff vazio no arquivo — o passo 1 do gate falha achando que a mudança não documentou nada,
    > mesmo a issue e o codigo existindo de verdade. Pior: como o `base.sha` que o GitHub Actions
    > usa é o **merge-base** entre as branches (o ponto onde divergiram), empurrar um commit novo
    > em `develop` depois não resolve sozinho — é preciso `git merge develop` dentro da branch da
    > feature para o merge-base andar, e mesmo assim o merge reaplica a remoção (lado da feature
    > "não mudou" aquele trecho, então herda a exclusão do outro lado) e as linhas precisam ser
    > re-adicionadas manualmente depois do merge. **Fluxo correto**: deixe a saída do
    > `jira_story.py` sem commitar (`feature_list.json`/`CHANGELOG.md` no working tree), rode
    > `git checkout -b feature/SV-12` — as mudanças não commitadas seguem para a branch nova
    > automaticamente —, e só então faça o commit, já dentro da branch da feature. `develop`
    > nunca vê essas linhas antes da PR final.
  - `subtask/<chave-da-subtask>` — um passo da feature, **a partir da branch da story**, não de
    `develop` (ex.: `subtask/SV-13`).
    > Por que prefixo próprio em vez de `feature/SV-12/SV-13`: o Git guarda ref como arquivo em
    > `.git/refs/heads/`, então `feature/SV-12` (arquivo) e `feature/SV-12/` (diretório) não
    > coexistem — o segundo `checkout -b` falha com `cannot lock ref`. O vínculo pai/filho vive
    > no `feature_list.json` e na própria sub-task do Jira, que já aponta para o parent.
  - `bugfix/<chave-jira>` — correção de bug, a partir de `develop` (ex.:
    `bugfix/SV-31-odd-negativa`, chave da issue + descrição curta).
  - `spike/<slug>` — investigação/prova de conceito sem issue associada (ex.:
    `spike/avaliar-testcontainers-rabbitmq`), kebab-case, sem chave.
- **Antes de abrir o PR da subtask, rode a skill `code-review` (ou `simplify`) contra o diff**
  (decisão de 2026-09-03) — pega comentário ruidoso, prosa redundante no código e más práticas
  antes de virarem histórico do Git, sem depender só das skills de revisão de `claude-code-skills`
  (essas só rodam no gate completo, `feature/` → `develop`, tarde demais para um ajuste pequeno de
  estilo). Corrija os achados e só então abra o PR.
- **Título do PR**: `[chave] título`, mesma chave e título da linha correspondente em
  `CHANGELOG.md` (ex.: `[SV-11] Bootstrap do pom.xml e esqueleto hexagonal`) — não a mensagem do
  commit.
- **Zero comentário de documentação/racional/regra de negócio no código** (decisão de 2026-09-04,
  endurece a regra anterior de "no máximo uma linha" da mesma sessão — o usuário considerou até o
  comentário de uma linha ruído). Nenhum bloco `/** ... */`/`//` explicando o quê, o porquê ou uma
  regra de negócio — nem em classe, nem em método, nem em campo. Código autoexplicativo por
  nome/estrutura; o resto (por que uma decisão foi tomada, o que um code review pegou, gotcha de
  biblioteca, contrato de um campo) vai para a mensagem de commit, a descrição da issue do Jira,
  ou a nota do vault correspondente ao assunto — o Obsidian é a centralização única de
  documentação e definição de negócio, nunca o código-fonte. Javadoc de `package-info.java`
  continua permitido (é rótulo estrutural de pacote, já espelhado no diagrama de
  `docs/CONVENTIONS.md` "Arquitetura interna dos serviços Java" — não é racional/regra de
  negócio).
- **Merge `subtask/` → branch da story**: `--no-ff`, via PR, com a **pipeline de CI daquele PR
  passando** (i18n, build, testes — não changelog, ver [[CI-CD]] seção "Changelog por serviço")
  e a subtask marcada `done` no `feature_list.json`. **Não** exige `./init.sh` local nem as
  skills de revisão de `claude-code-skills`: um estado intermediário raramente passa no gate de
  cobertura (um `docker-compose.yml` sem o RabbitMQ ainda não sobe; `mvn verify` num serviço pela
  metade também não). O **SonarCloud é pulado** nesses PRs — cobertura parcial de uma feature em
  andamento reprovaria o quality gate de código novo sem indicar defeito real (condição
  `github.base_ref` no `ci.yml`, ver [[CI-CD]]).
- **Merge de `feature/`/`bugfix`/`spike/` → `develop`**: gate completo — `./init.sh` daquele
  repositório passando, `feature_list.json` atualizado (todas as `subtasks` `done`, `evidence`
  preenchida), skills de revisão rodadas (ver [[AGENT-SKILLS]]) e a pipeline de CI inteira,
  **incluindo SonarCloud** (changelog, i18n, build, testes, Sonar nos 6 de aplicação; changelog +
  validação do compose em `infra/`) — ver [[CI-CD]].
- **`CHANGELOG.md`**: uma linha por issue do Jira (story e cada subtask), formato
  `- [chave](url) - título`, nada além disso — sem prosa, sem categoria Added/Fixed. Escrita
  automaticamente por `tools/jira_story.py` no momento em que cada issue é criada, nunca à mão
  pela sessão (ver [[CI-CD]] seção "Changelog por serviço" para o racional completo e o motivo
  de a validação de changelog só rodar na PR story → `develop`, não nas de subtask).
- **Merge de `develop` → `main`**: quando o conjunto de features acumuladas em `develop` estiver
  estável o suficiente para ser considerado uma entrega (não há cadência fixa definida — critério
  é estabilidade, não calendário).
- **Commits**: [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/),
  **sempre em inglês** — descrição, corpo e footers (decisão de 2026-08-17, ver
  [[DECISIONS-LOG]]). Formato:

  ```
  <type>[optional scope]: <description>

  [optional body]

  [optional footer(s)]
  ```

  - **`type`**: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`,
    `revert`. `feat` e `fix` têm o significado da spec (nova capacidade / correção de bug), não
    "arquivo novo" / "arquivo alterado".
  - **`scope`** (opcional): módulo tocado dentro do repositório, em kebab-case
    (`feat(bets): ...`, `ci(sonar): ...`). Não repita o nome do serviço — o repositório já é o
    serviço.
  - **`description`**: imperativo, minúscula inicial, sem ponto final
    (`add manual bet registration`, não `Added manual bet registration.`).
  - **Rastreabilidade — a chave do Jira *e* o id da feature, no rodapé**, um por linha:

    ```
    feat(bets): add manual bet registration

    Refs: SV-12
    Feature: feat-004
    ```

    Os dois, não um só: a chave liga o commit à story, o id liga o commit à fonte da verdade
    (`feature_list.json`), que é onde a evidência e o `plan_review` daquele trabalho realmente
    vivem. Commits de subtask citam a chave da própria sub-task (`Refs: SV-13`) e o id dela
    (`Feature: feat-004.3`).
  - **Breaking change**: `!` antes dos dois-pontos **e** footer `BREAKING CHANGE: <descrição>`
    — obrigatório quando um contrato entre serviços muda (payload de `BetCreated`/`BetSettled`,
    rota pública, header de confiança). Ver [[API-CONTRACTS]].

  **O idioma inglês vale só para a mensagem de commit.** Não muda `CHANGELOG.md`, `progress.md`,
  `session-handoff.md`, `feature_list.json` nem o vault, que seguem em português — e não muda a
  regra de i18n de conteúdo de produto (ver seção "Internacionalização (i18n)"). Motivo: commit
  é superfície técnica compartilhada com nomes de rota, evento e código, todos já em inglês;
  documentação de projeto é entregável de TCC, em português.
