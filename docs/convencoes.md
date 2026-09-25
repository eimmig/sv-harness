---
tags: [conventions, architecture]
---

# Convenções de código e arquitetura

Navegação: [[technical/referencia-tecnica|Referência técnica]] · [[arquitetura]] · [[contratos-de-api]] ·
[[testes]] · [[observabilidade-e-configuracao]]

Decisões que valem para **todos** os serviços, para que sessões diferentes (ou serviços
diferentes) não cheguem a soluções distintas para o mesmo problema. Ver [[arquitetura]] para
a arquitetura de sistema (microsserviços/infra); esta nota é sobre a arquitetura *dentro* de
cada serviço. Ver também [[testes]], [[contratos-de-api]] e [[observabilidade-e-configuracao]].

> Nada disto foi especificado no TCC 1 (que cobre requisitos, modelagem de dados e arquitetura
> de implantação, não a organização interna do código) — são decisões tomadas para fechar
> lacunas antes da implementação, para reduzir divergência entre serviços e sessões.

> Tema, paleta de cores e inventário de componentes de `apps/web` são tratados em nota separada
> — ver [[sistema-de-design]] — para não misturar decisão visual com arquitetura de código nesta
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

GroupId: `com.stakevault.betting` (nome do produto, ver [[sistema-de-design]] — corrigido em
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
- **1 DTO de resposta por operação** (achado do `Plan Reviewer` em `auth-service feat-009`,
  confirmado contra o próprio código do serviço: `CreateUserResponse`/`CreateTenantResponse`/
  `GenerateTelegramLinkResponse`/`LoginResponse`/`TelegramAccountLookupResponse`, nenhum reusado
  entre 2 operações): mesmo quando dois endpoints devolvem exatamente os mesmos campos (ex.:
  `POST` que cria um recurso e `GET` que lista o mesmo tipo de recurso), cada operação ganha seu
  próprio `record` de resposta em vez de reaproveitar o DTO da outra — evita que o nome do tipo
  (`CreateXResponse` aparecendo no corpo de um `GET`) fique semanticamente errado só para
  economizar um `record` de poucas linhas.
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
  `application/problem+json` (ver [[contratos-de-api]]) com `title`/`detail` localizados (ver seção
  "Internacionalização (i18n)" abaixo) — a exception carrega uma chave de mensagem, não o texto
  final.
- **`LocalizedRuntimeException` como base obrigatória de exceção de domínio nova** (extraída em
  `bets-service feat-022`, achado real de `feat-021`: cada exceção de domínio repetia campo(s) +
  construtor que monta a mensagem + `messageKey()`/`httpStatusCode()`/`messageArgs()`, reprovando
  o gate de duplicação de código novo do SonarCloud a cada exceção nova — resolvido antes com
  `sonar.cpd.exclusions`, workaround removido junto com este refactor). Toda exceção de domínio
  nova (nos 4 serviços Java — `LocalizedDomainException` em `domain.model` de `auth`/`bets`/`stats`;
  no `api-gateway`, que não tem camada de domínio, a interface equivalente é
  `LocalizedFilterException` no pacote `filter`, e a base a implementa em vez da outra) estende
  `LocalizedRuntimeException` em vez de `RuntimeException` diretamente: construtor
  `(String message, Object... args)` (ou `(String message, Throwable cause, Object... args)` para
  quando houver causa) já guarda os args e implementa `messageArgs()` — a subclasse só sobrescreve
  `messageKey()`/`httpStatusCode()`. Regras: (1) o campo `Object[] args` da base é `transient`
  (evita `java:S1948` — `RuntimeException` é `Serializable`, `Object[]` não garante elementos
  serializáveis) e `messageArgs()` devolve `args.clone()` (sem aliasing); (2) `messageKey()`
  **nunca** sobe pra base, mesmo quando parece constante — pelo menos uma exceção real do projeto
  monta a chave dinamicamente a partir de um campo (`CatalogAlreadyRegisteredException`); (3) uma
  exceção que expõe accessor público além dos 3 da interface (ex.: `.slug()`, usado por código que
  precisa do valor tipado, não só localizado) mantém campo próprio — não dá pra só delegar pro
  `Object[]` da base sem cast. (4) Visibilidade da base (`public` vs package-private) segue a
  convenção já estabelecida no próprio serviço, não precisa ser uniforme entre os 4 — em
  `auth-service feat-021` a base ficou package-private porque `SlugRelatedDomainException`
  (abstração pré-existente que resolvia a duplicação só para 2 exceções relacionadas a slug) já
  tinha esse precedente no mesmo pacote; nesse caso a abstração antiga passa a estender a nova
  base em vez de ficar como um segundo mecanismo paralelo fazendo a mesma coisa. (5) Antes de
  aplicar num serviço, auditar de verdade quantas exceções ele tem e se todas implementam
  `LocalizedDomainException` — nem toda exceção do pacote `domain.model` implementa a interface
  (`auth-service` tem 2 que não implementam, `TenantSchemaNotFoundException`/
  `DownstreamProvisioningException`, capturadas internamente antes de chegar ao
  `RestControllerAdvice` — corretamente fora do escopo do refactor). O inverso também existe:
  classe que implementa a interface sem ser exceção (`stats-service`: `InvalidTenantIdHeader`/
  `MissingTenantIdHeader`, singletons aninhados em `TenantSchemaFilter` só para montar o
  `ProblemDetail`) fica fora — não há `RuntimeException` para substituir. Aplicado nos 4 serviços
  (`bets` `feat-022`, `auth` `feat-021`, `stats` `feat-023`, `api-gateway` `feat-018`).
- **Migrations**: Flyway, arquivos em `src/main/resources/db/migration/`, nomeados
  `V{date_now}__descricao_em_snake_case.sql` (ex.: `V2026080119170000__create_user_table.sql`). Nunca editar uma
  migration já commitada — sempre criar uma nova.
- **Migração lazy por schema** (decisão de 2026-08-02, ver [[DECISIONS-LOG]]): em
  `auth-service`, `bets-service` e `stats-service` (schema-per-tenant, ver [[arquitetura]]), o
  Flyway **não** migra uma lista fixa de schemas no boot. Em vez disso, o schema do tenant
  resolvido a partir de `X-Tenant-Id` (ver [[contratos-de-api]]) é verificado/migrado sob demanda,
  antes de a requisição chegar ao controller — mesmo ponto de código que resolve o schema da
  conexão (`SET search_path`/multi-tenant provider) também garante que ele está em dia. Evita
  ter que migrar N schemas de tenant a cada deploy e cobre schemas criados depois que a
  aplicação já subiu.
- **Nomenclatura de schema de tenant**: `tenant_<slug>` (snake_case, derivado deterministicamente
  do slug da organização informado na criação do tenant) — sem tabela de diretório adicional
  para mapear slug → nome de schema; unicidade é garantida pelo próprio Postgres (`CREATE
  SCHEMA` falha se o schema já existir).
- **Migration eager para o schema `public`** (introduzida em `auth-service feat-006`, achado do
  `Plan Reviewer`): tabelas de diretório global (fora de qualquer tenant, ex.: `TELEGRAM_LINK`/
  `PENDING_TELEGRAM_LINK`, ver [[modelo-de-dados]]) não se beneficiam da migração lazy acima — não há
  "schema do tenant resolvido por requisição" para elas, e o schema `public` sempre existe e
  pertence ao próprio serviço, sem a ambiguidade de "quem provisiona" que motivou a lazy
  migration. Solução: uma segunda pasta de migrations (`classpath:db/migration-public/`,
  arquivos com o mesmo padrão de nomenclatura acima), aplicada por um bean dedicado que roda
  `Flyway.configure().schemas("public").createSchemas(false).locations(...).load().migrate()`
  uma única vez no boot — independente do `spring.flyway.enabled: false` global (é uma instância
  própria de `Flyway`, mesmo padrão já usado para a migração lazy por tenant). **Não use
  `ApplicationRunner`/`CommandLineRunner`** para isso (achado do `Persistence Auditor` em
  `feat-006`): o `SpringApplication.run()` já inicia o servidor embutido (`SmartLifecycle`,
  dentro de `refreshContext()`) **antes** de chamar os runners — uma requisição pode chegar e
  ser aceita pela porta HTTP antes da migration rodar, quebrando com "relation does not exist"
  logo após o boot. Use `InitializingBean.afterPropertiesSet()` (roda durante
  `finishBeanFactoryInitialization()`, garantidamente antes do servidor embutido subir — mesmo
  mecanismo que o próprio `FlywayMigrationInitializer` do Spring Boot usa) num bean dedicado.
  Entidades JPA dessas tabelas usam `@Table(schema = "public")` explícito — Hibernate
  sempre qualifica totalmente essas tabelas nas queries geradas, independente do schema corrente
  setado pelo `MultiTenantConnectionProvider` para a sessão (ver bullet acima sobre multi-tenancy
  do Hibernate) — permite que tabelas globais e tabelas por tenant convivam na mesma
  `EntityManagerFactory`/transação, sem precisar de um segundo mecanismo de acesso a dados
  (`JdbcTemplate` cru) nem de coordenar duas transações separadas.
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
  atualizar uma linha já existente. **A partir de `bets-service feat-003`**, esse boilerplate
  (`id`/`isNew`/`@PostLoad`) vive numa única `AbstractJpaEntity` (`@MappedSuperclass`) — extraída
  quando o mesmo mecanismo passou a se repetir em 3+ entidades (`CatalogJpaEntity` refatorada para
  estendê-la, `BettingHouseJpaEntity`/`TransactionJpaEntity` a estendem direto quando não têm
  campo `name` único). Reaproveitar em `stats-service`/`auth-service` se o mesmo padrão de id
  atribuído pelo domínio se repetir por lá.
- **Enum persistido com valor diferente do nome Java** (ex.: `Role.ADMIN`/`MEMBER` gravado como
  `'admin'`/`'member'` para bater com `CHECK` da migration): `AttributeConverter` dedicado com
  `@Converter(autoApply = true)`, nunca `@Enumerated(EnumType.STRING)` puro (grava o nome Java
  literal, maiúsculo). **Valor exposto em JSON é uma decisão separada da persistência** (achado de
  `bets-service feat-003`): `Role` em `auth-service` nunca ganhou tratamento de serialização e
  trafega maiúsculo (`"ADMIN"`) por ser só o default do Jackson, não uma convenção deliberada —
  não seguir esse precedente para enums de estado de domínio (ex.: `TransactionType`, e futuramente
  `BET.status`), que já têm valores minúsculos documentados (`docs/services/bets-service.md`,
  `pending`/`won`/`lost`/`void`). Nesses casos, anotar cada constante do enum com
  `@JsonProperty("valor-minusculo")` (`com.fasterxml.jackson.annotation` — pacote de anotações do
  Jackson não migrou para `tools.jackson` no Jackson 3, confirmado via `mvn dependency:build-
  classpath` contra o classpath real; só `jackson-core`/`jackson-databind` migraram) — cobre
  serialização e desserialização com a mesma anotação, sem precisar de conversor à parte nem de
  customizar o `ObjectMapper` globalmente.
- **`MethodArgumentNotValidException` não cobre corpo malformado**: um `@RestControllerAdvice`
  com handler só para `MethodArgumentNotValidException` (falha de Bean Validation) deixa passar
  JSON malformado ou valor de enum não reconhecido no corpo da requisição — Spring lança
  `HttpMessageNotReadableException` *antes* da validação rodar, então sem handler dedicado a
  resposta cai no formato de erro default do Spring Boot (não `application/problem+json`),
  quebrando o contrato RFC 7807 documentado. Achado real em `bets-service feat-003` (campo
  `TransactionType` no corpo de `POST /api/v1/transactions`) — todo `@RestControllerAdvice` que
  aceita enum ou campo estruturado no corpo precisa do handler de
  `HttpMessageNotReadableException` ao lado do de `MethodArgumentNotValidException`, mapeado para
  o mesmo `validation-failed`.
- **Atualizar uma linha já persistida (não criar)**: até `bets-service feat-004`, todas as
  features dos serviços Java só faziam `INSERT` (`save()` de uma entidade recém-construída,
  `isNew=true`). Para um `UPDATE` de verdade, **não** reconstruir a entidade via
  `new XJpaEntity(id, ...)` e chamar `save()` — a instância nova nasce com `isNew=true` (nenhum
  `@PostLoad` rodou), e o `Persistable` faz Spring Data chamar `entityManager.persist()`,
  tentando inserir uma linha com PK já existente (constraint violation, não um update). O jeito
  certo para um update **incondicional** (sem risco de corrida importar): carregar a entidade via
  `jpaRepository.findById(id)` (isso roda `@PostLoad`, `isNew` vira `false`), mutar o campo
  através de um método da própria entidade (não expor `@Setter` amplo) e salvar a MESMA instância
  carregada — aí sim `Persistable.isNew()==false` faz Spring Data chamar `entityManager.merge()`.
  **Correção em `bets-service feat-005`**: esse padrão (`findById` + mutar + `save`) tem uma
  janela TOCTOU entre a leitura e a escrita — aceitável para um update sem efeito colateral
  sensível, mas **não** para uma transição de estado guardada por uma condição de negócio (ex.:
  `PATCH /api/v1/bets/{id}/status`, só válida a partir de `pending`) onde duas chamadas
  concorrentes podem ambas passar a validação em memória antes de qualquer uma escrever. Nesse
  caso, usar um `UPDATE` atômico condicional direto no banco: `@Modifying @Query("UPDATE
  XJpaEntity x SET x.campo = :novo WHERE x.id = :id AND x.campo = :valorEsperado")` retornando o
  número de linhas afetadas (`int`) — só quem "ganha" a corrida recebe `> 0`; o perdedor trata
  como transição inválida, nunca sobrescreve em silêncio (`JpaBetRepository.transitionStatus`,
  primeira query `@Modifying` do serviço). Reaproveitar em `auth-service`/`stats-service`: o
  padrão simples (`findById`+mutar+`save`) para updates incondicionais, o `@Modifying` atômico
  para qualquer transição de estado com condição de guarda.
  **Reaproveitado em `stats-service feat-003.1`** (`FACT_BET`, upsert de verdade — `BetSettled`
  pode chegar depois de `BetCreated` já ter inserido a linha, sem condição de guarda a proteger):
  `JpaFactBetRepository.save()` faz `findById` primeiro; se a linha existe, chama
  `FactBetJpaEntity.applyFrom(FactBet)` (método da própria entidade, não `@Setter` amplo — a
  primeira tentativa desta feature usou `@Setter` do Lombok na classe inteira antes de reler esta
  nota e corrigir) na instância já rastreada; senão constrói uma nova. Sem risco de corrida a
  proteger aqui — RabbitMQ entrega mensagens da mesma fila sequencialmente a um consumidor, sem
  paralelismo entre eventos do mesmo `betId`.
  **Gotcha real em `auth-service feat-018`**: o método da entidade que muta os campos (`applyFrom`/
  `applyUpdate`) precisa cobrir **todos** os campos que a assinatura de domínio `Repository.update(
  Agregado): Agregado` promete poder alterar, não só os que a primeira feature que criou o método
  precisava. `UserRepository.update(User)` nasceu em `feat-017` (`PATCH /api/v1/users/{id}`, só
  `name`/`role` editáveis) e `UserJpaEntity.applyUpdate(name, role)` foi escrito com só esses 2
  parâmetros; `feat-018` (troca de senha) construiu um `User` atualizado com `passwordHash`/
  `mustChangePassword` novos e chamou o mesmo `update()` esperando persistir — sem erro, sem
  exceção, `204` de sucesso, mas os 2 campos novos eram silenciosamente descartados (`applyUpdate`
  nunca os recebia). Corrigido alargando a assinatura pra `applyUpdate(name, role, passwordHash,
  mustChangePassword)`, sem quebrar o caller original (que já enviava os 2 campos extras
  inalterados do registro lido, só não os repassava adiante). Ao reaproveitar `findById`+mutar+
  `save` para uma nova operação sobre uma entidade que **já tem** um método de mutação, conferir se
  esse método aceita todo campo que o `User`/`Bet`/... novo pode trazer — não assumir que ele já é
  genérico só porque o nome (`applyUpdate`) sugere.
- **Entidade JPA com muitas colunas (`java:S107`, gate `feature -> develop` do SonarCloud)**:
  achado real em `bets-service feat-004` — `BetJpaEntity` (18 colunas) com um construtor
  posicional de 18 parâmetros reprovou o gate (`Constructor has 18 parameters, which is greater
  than 7 authorized`), só descoberto no PR `feature -> develop` (gate completo — PRs de subtask
  pulam SonarCloud, ver `docs/pipeline-ci-cd.md`). Corrigido trocando o construtor posicional por um único
  parâmetro: `BetJpaEntity(Bet bet)`, que lê os campos do record de domínio — direção de
  dependência já é a correta em hexagonal (adapter conhece domínio, nunca o contrário), e
  `TransactionJpaEntity`/`CatalogJpaEntity` já importavam tipos de domínio (`TransactionType`)
  antes disso. Preferir este padrão (construtor recebendo o record de domínio inteiro) em vez de
  builder/Lombok assim que uma entidade JPA nova ultrapassar ~7 colunas, para não repetir o
  mesmo achado reativo em `auth-service`/`stats-service`.
- **Método de `@Query` do Spring Data com muitos filtros opcionais (`java:S107`)**: achado real
  em `bets-service feat-007` — `findFiltered(bettingHouseId, sportId, leagueId, marketId,
  tipsterId, from, to, pageable)` (8 parâmetros) reprovou o mesmo gate. Como o método já é uma
  interface do Spring Data (não dá pra "receber um record no construtor" como em `BetJpaEntity`),
  a correção foi agrupar os filtros num único record de domínio (`BetFilter`, já existente para
  o `port/in`) e referenciá-lo no JPQL via SpEL: `@Query("... :#{#filter.bettingHouseId()} ...")`
  + `findFiltered(@Param("filter") BetFilter filter, Pageable pageable)` (2 parâmetros). SpEL do
  Spring Data JPA chama o método de acesso do record diretamente (`#filter.campo()`, com
  parênteses — não `#filter.campo`, que só funciona para getters JavaBean). Preferir este padrão
  em qualquer método de repositório novo com mais de ~5 filtros opcionais combináveis.
- **JPQL: `FUNCTION('make_date', ...)` no `SELECT` combinado com `GROUP BY` nas colunas cruas
  funciona** (confirmado em `stats-service feat-016`, `aggregateByDay` — Hibernate/Postgres deste
  projeto aceitam expressão determinística das próprias colunas agrupadas sem repeti-la no
  `GROUP BY`, provado por teste de integração real). Combinação nova na época (`findOrderedSettledProfits`
  já usava `FUNCTION('make_date',...)` sem agregação; `aggregateByMonth` já usava `GROUP BY` sem
  `FUNCTION()`) — próxima agregação por data neste ou outro serviço Java schema-per-tenant pode
  reaproveitar o padrão direto, sem precisar redescobrir se funciona.
- **`com.networknt:json-schema-validator` — não pinar a versão mais recente sem checar a API**
  (achado real de `bets-service feat-006`): a versão `3.0.7` (a mais nova no Maven Central no
  momento) é uma reescrita completa da biblioteca — nenhuma das classes clássicas
  (`JsonSchemaFactory`, `JsonSchema`, `SpecVersion`, `ValidationMessage`) existe mais no jar,
  substituídas por uma API nova (`Error`, etc.) nunca documentada/usada neste projeto. Só
  descoberto na compilação do teste (`test-compile` falhou com "package does not exist"), não
  antes. Corrigido: pinado em `1.5.9` (última da linha 1.x, API clássica estável, amplamente
  documentada). Antes de fixar a versão "mais recente" de uma biblioteca nova para o projeto,
  checar o changelog/major version primeiro (ou aceitar o risco e confirmar via `mvn
  test-compile` antes de escrever mais código em cima).
- **`MessageProperties.getDeliveryMode()` só reflete o que VOCÊ setou, não o que a mensagem
  recebida carrega** (achado real de `bets-service feat-006`, `RabbitBetEventPublisherIntegrationTest`):
  `MessageBuilder...setDeliveryMode(MessageDeliveryMode.PERSISTENT)` no lado que publica funciona
  (mensagem sobrevive a restart do broker mesmo em fila durable — sem isso, é não-persistente por
  padrão do protocolo AMQP), mas um teste que consome a mensagem de volta via
  `rabbitTemplate.receive(...)` e chama `getDeliveryMode()` no lado do CONSUMIDOR recebe `null`
  sempre — o valor de fato recebido do broker fica em `getReceivedDeliveryMode()`, um accessor
  separado (mesmo padrão de `getReceivedRoutingKey()`/`getReceivedExchange()` do Spring AMQP,
  que distinguem metadado de entrada de propriedade que você está prestes a setar para uma
  mensagem de saída). Vale para `stats-service` (lado consumidor) e para o publicador de
  `BetSettled` (`feat-008`) reaproveitarem sem redescobrir.
- **Falha de validação de schema num `@RabbitListener` precisa de `AmqpRejectAndDontRequeueException`,
  não uma `RuntimeException` comum** (achado real de `stats-service feat-001.9`, primeiro consumidor
  RabbitMQ do projeto): o mecanismo de "3 tentativas então DLQ" (`x-delivery-limit` da quorum
  queue, ver `docs/contratos-de-api.md` "Topologia RabbitMQ") só funciona quando o container para de
  pedir "requeue" ao broker — o `ConditionalRejectingErrorHandler` padrão do Spring AMQP trata uma
  exceção comum como não-fatal e reenfileira (`requeue=true`) indefinidamente, então o
  `x-delivery-limit` nunca é atingido do jeito esperado (achado em teste real: 128+ redeliveries em
  ~10s sem nunca cair na DLQ, não só um número teórico). Mensagem que falha validação de schema
  nunca vai passar validando de novo — é falha permanente, não transitória — então o correto
  (funcional e não só para destravar o teste) é a exceção de validação estender
  `org.springframework.amqp.AmqpRejectAndDontRequeueException`: o container rejeita sem reenfileirar
  na primeira tentativa, e a mensagem cai direto na fila de dead-letter configurada
  (`x-dead-letter-exchange`). Reservar o `x-delivery-limit`/retry automático só para falha
  genuinamente transitória (ex.: uma futura falha de conexão com o banco ao persistir
  `FACT_BET` em `feat-002`/`feat-003`) — não para erro de payload malformado.
- **`java:S1135` (comentário "TODO") dispara em comentário em português com a palavra "todo"**
  (achado real de `bets-service feat-006`, gate `feature -> develop`): a regra do SonarCloud
  procura a substring "todo" sem diferenciar o marcador de tarefa pendente (inglês) da palavra
  comum do português ("comum a todo evento..."). Não é bug de verdade, mas reprova o gate mesmo
  assim. Evitar a palavra "todo" (preferir "qualquer"/"cada"/"todos os") no início de comentário
  em código Java — vale para os 3 serviços Java, não só este.
- **Filtro opcional `(:param IS NULL OR coluna >= :param)` sobre coluna `timestamp`/`date`/
  numérica quebra no Postgres** (achado real de `bets-service feat-007`, `GET /api/v1/bets` e
  `GET /api/v1/transactions`): `ERROR: could not determine data type of parameter $N`. Diferente
  do mesmo padrão usado para colunas `UUID`/texto (`bettingHouseId`, `sportId` etc., já usado sem
  problema desde `feat-003`/`feat-004`) — o Postgres não consegue inferir o tipo de um parâmetro
  cujo **único** uso na query é um `? IS NULL` isolado, e é mais rígido para isso em tipos
  temporais/numéricos do que em `uuid`/`text`. Corrigido trocando o padrão, só para os filtros de
  intervalo (`from`/`to`), de `(:from IS NULL OR coluna >= :from)` para
  `coluna >= COALESCE(:from, coluna)` — o parâmetro sempre aparece ao lado de uma coluna tipada,
  nunca isolado; `coluna >= COALESCE(:from, coluna)` colapsa para `coluna >= coluna` (sempre
  verdadeiro) quando `:from` é nulo. **Só é seguro quando a coluna é `NOT NULL`** (`betDate`/
  `createdAt` são) — para uma coluna nullable (ex.: `tipsterId`), `COALESCE(:param, coluna) =
  coluna` viraria `NULL = NULL` (nunca verdadeiro em SQL) e excluiria errado as linhas com a
  coluna nula quando nenhum filtro é aplicado; nesses casos manter o padrão `IS NULL OR` original
  (não reproduziu o erro em `tipsterId`/`bettingHouseId`, ambos `UUID`). Só descoberto rodando
  `./init.sh` de verdade contra o Postgres real do Testcontainers, não na compilação — reaproveitar
  para qualquer filtro de intervalo de data/número novo em `auth-service`/`stats-service`.
- **Lombok + Java 25**: `maven-compiler-plugin` precisa de `annotationProcessorPaths` explícito
  apontando pro Lombok — só declarar a dependência (mesmo com escopo `provided`) não basta nesta
  combinação de `javac`/Lombok, o processamento de anotação é pulado em silêncio (sem erro, sem
  aviso) e os métodos gerados (`getX()`, construtor, etc.) simplesmente não existem no `.class`.
- **Filtro de servlet que decide por prefixo de rota** (ex.: `shouldNotFilter`/gate de header
  restrito a `/api/v1/admin/**`, decidido em `auth-service feat-003`): nunca comparar contra
  `request.getRequestURI()` cru — path com percent-encoding (`/api/v1/adm%69n/tenants`) passa
  ileso pela comparação de prefixo enquanto o Spring MVC decodifica e roteia normalmente para o
  endpoint protegido, driblando o filtro por completo. Decodificar primeiro com
  `UriUtils.decode(request.getRequestURI(), StandardCharsets.UTF_8)` antes de comparar o
  prefixo. Achado real via `/code-review`, não do Plan Review original — vale para qualquer
  filtro futuro que gate por prefixo de path nos 4 serviços Java (`api-gateway` incluso, que
  roteia por path).
- **Todo filtro *bloqueante* em `api-gateway` precisa excluir `/actuator/**` via
  `shouldNotFilter`** (achado real, `feat-002`, só percebido rodando `mvn verify` de verdade —
  nem o Plan Review nem `/code-review` do diff isolado do filtro pegaram, porque o efeito só
  aparece ao rodar a suíte inteira do módulo): assim que um `OncePerRequestFilter` que **rejeita**
  requisição sem credencial válida vira `@Component` (ex.: `PasetoAuthenticationFilter`), o Spring
  Boot o registra automaticamente pra **toda** rota do servlet container, inclusive
  `/actuator/health`/`/actuator/health/readiness` — os testes de `feat-001.4`
  (`HealthChecksTest`) passaram a receber `401` em vez de `200`. Diferente do
  `TenantSchemaFilter`/`X-Tenant-Id` de `auth-service`/`bets-service` (que **nunca** rejeita por
  header ausente, só age quando o header existe — não precisa de exclusão), qualquer filtro deste
  serviço que rejeita por padrão (nenhuma credencial = `401`) precisa do mesmo
  `shouldNotFilter` decodificado (`UriUtils.decode` + `startsWith("/actuator/")`) do achado
  acima — health checks precisam continuar acessíveis sem token pro `docker-compose.yml`
  funcionar (ver [[observabilidade-e-configuracao]]). Vale para o filtro de `X-Service-Key` de
  `feat-004` também.
  > **Gate `feature -> develop` do SonarCloud pegou o próprio prefixo hardcoded** (`java:S1075`,
  > "Refactor your code to get this URI from a customizable parameter"): a string literal
  > `/actuator/` usada na comparação de prefixo. Correção real, não supressão de regra — o base
  > path do Actuator já é configurável via `management.endpoints.web.base-path` (default
  > `/actuator`), então o filtro passa a ler esse valor via
  > `@Value("${management.endpoints.web.base-path:/actuator}")` em vez de hardcodar o default —
  > se o base path for reconfigurado, a exclusão continua funcionando (com o literal fixo, ela
  > silenciosamente pararia de funcionar). Vale para o filtro de `feat-004` também.
- **`Paseto.decrypt` (paseto4j-version4) não tem um único tipo de exceção para "token
  inválido"** (achado real de pesquisa em `api-gateway feat-002`, primeiro consumidor de
  `decrypt` no projeto — `auth-service` só chama `encrypt`): confirmado via `javap` contra o jar
  real (`paseto4j-version4-2024.3.jar`/`paseto4j-commons-2024.3.jar`) que token malformado,
  adulterado ou com MAC inválido pode lançar `PasetoException`, `IllegalArgumentException` **ou**
  `IllegalStateException` dependendo de qual verificação falha primeiro — as três `extends
  RuntimeException`, sem uma exception dedicada comum. Um filtro de validação precisa capturar
  `RuntimeException` genérica ao redor de `decrypt`+parse do payload (não uma das três
  isoladamente) para tratar qualquer falha de token como `401` — não é descuido de tratamento de
  exceção amplo demais, é a única forma de cobrir os três caminhos de falha da biblioteca.
  Também não valida `exp` (expiração) sozinho — o payload decifrado é só o JSON puro que
  `auth-service` serializou; checagem de expiração é responsabilidade de quem valida (comparar
  `exp` contra `Instant.now().getEpochSecond()`).

## Internacionalização (i18n)

Decisão explícita do usuário (2026-08-01): o sistema é **100% internacionalizável**. Dois
princípios que não se misturam (ver também [[contratos-de-api]] seção "Internacionalização"):

- **Superfície técnica (rotas, query params, nomes/valores de evento, chaves de cache, nomes de
  campo) é sempre em inglês, nunca localizada** — não muda com o idioma do usuário.
- **Todo texto voltado ao usuário final é localizado, nunca hardcoded num idioma só** — título e
  detalhe de erro de API, toda string de UI, e as mensagens que `telegram-integration` envia de
  volta ao usuário no bot.
- **Idiomas suportados, sempre os três em sincronia**: `pt-BR`, `en-US`, `es` — nenhuma feature
  que introduz texto novo é considerada `done` (ver `CLAUDE.md` da raiz) se traduzir para só um
  ou dois dos três. Não há "idioma principal com os outros pendentes".

### Backend Java (auth-service, bets-service, stats-service, api-gateway)

- Mensagens de erro (`title`/`detail` do RFC 7807, ver [[contratos-de-api]]) resolvidas via Spring
  `MessageSource` + `ResourceBundle` (`messages_pt_BR.properties`, `messages_en_US.properties`,
  `messages_es.properties`, uma chave por tipo de erro), escolhidas pelo `LocaleResolver` a
  partir do header `Accept-Language` da requisição. Sem header reconhecido, cai em `pt-BR`
  (idioma padrão). O `type` da resposta (slug em inglês) nunca muda com o locale — só
  `title`/`detail`.
  > **Gotcha crítico, descoberto só em `auth-service feat-003.6`**: sem um `src/main/resources/
  > messages.properties` **sem sufixo de locale** (só `messages_pt_BR.properties`/
  > `messages_en_US.properties`/`messages_es.properties`), o `MessageSourceAutoConfiguration` do
  > Spring Boot **nunca ativa** — a condição de ativação (`ResourceBundleCondition`, confirmado
  > via `javap` contra o jar real `spring-boot-autoconfigure-4.1.1`) checa literalmente
  > `classpath*:messages.properties` (basename + `.properties`, sem locale), não os arquivos com
  > sufixo. Sem a autoconfiguração, `MessageSource` nunca vira bean de verdade — todo
  > `messageSource.getMessage(...)` real da aplicação recebe o `DelegatingMessageSource` interno
  > do Spring (fallback vazio) e lança `NoSuchMessageException` para qualquer chave, mesmo com os
  > 3 arquivos de locale presentes e corretos. **Ficou sem detecção desde `feat-001.5`** porque
  > todo teste até `feat-003.5` (`MessagesTest`, `AdminApiKeyFilterTest`) instanciava seu próprio
  > `new ResourceBundleMessageSource()` manualmente em vez de injetar o bean real da aplicação —
  > só o primeiro teste de integração ponta a ponta de verdade (`@SpringBootTest` +
  > `RANDOM_PORT`, chamando um endpoint que resolve mensagem via o bean autowired) expôs o
  > problema. Correção: criar `messages.properties` (sem sufixo) — não precisa ter as mesmas
  > chaves dos 3 arquivos de locale (eles continuam sendo a fonte real, `.properties` base só
  > existe para satisfazer a condição de ativação); **não** incluir esse arquivo na checagem de
  > paridade de chaves do `validate-i18n-keys.py` (ele não é um 4º locale). Aplicável aos outros 3
  > serviços Java (`bets-service`, `stats-service`, `api-gateway`) assim que criarem seus
  > próprios `messages_*.properties` — criar o arquivo base **junto**, não depois de descobrir o
  > bug de novo.
- Exceptions de domínio (ver seção "Padrões de código Java" acima) carregam uma chave de
  mensagem (ex.: `error.invalid-odd`), não o texto final — o `@RestControllerAdvice` resolve o
  texto no locale da requisição, nunca a camada de domínio.
- **Dois gotchas de encoding descobertos juntos em `auth-service feat-003`** (só apareceram
  quando uma mensagem de erro com acento — `es`/`pt-BR` — foi testada pela primeira vez; as
  mensagens hardcoded anteriores, `TenantSchemaFilter` de `feat-001.3`, não tinham acento, então
  os dois bugs ficaram latentes sem nenhum teste pegar):
  1. **Filtro de servlet escrevendo corpo RFC 7807 direto no `HttpServletResponse`** (necessário
     quando o erro acontece fora do `DispatcherServlet` — ex.: `AdminApiKeyFilter`, que roda
     antes do `@RestControllerAdvice` e não pode contar com ele):
     `response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE)` sozinho **não** basta —
     sem `charset` explícito no content-type, `HttpServletResponse` (e `MockHttpServletResponse`
     em teste) assume **ISO-8859-1** por padrão (default do Servlet spec), então texto UTF-8
     escrito pelo `ObjectMapper` é relido errado por qualquer client/teste que decodifique a
     resposta. Correção: `response.setCharacterEncoding("UTF-8")` explícito antes de escrever o
     corpo, sempre que um filtro (não um `@RestControllerAdvice` — esse já usa
     `HttpMessageConverter` com UTF-8 correto) monta a resposta na mão. **Quase regredido em
     `bets-service feat-001.9`**: ao extrair um `FilterProblemWriter` compartilhado entre dois
     filtros (`/code-review` da própria feature, achado de duplicação), o `setCharacterEncoding`
     ficou de fora da extração - só pego na revisão final porque as mensagens deste serviço já
     nasceram acentuadas (diferente de `auth-service`, que nunca teve acento no texto hardcoded do
     `TenantSchemaFilter` e por isso nunca expôs o bug). Qualquer extração futura de um helper de
     escrita de problema RFC 7807 num filtro precisa levar essa linha junto, não só content-type
     e status.
  2. **`ResourceBundleMessageSource` construído manualmente em teste** (mesmo padrão usado desde
     `feat-001.5` para testar `MessageSource` sem subir o contexto Spring inteiro) **não** herda
     o default `spring.messages.encoding=UTF-8` do autoconfigure do Spring Boot — sem
     `setDefaultEncoding("UTF-8")` explícito, ele lê o `.properties` (já em UTF-8 real no disco)
     como ISO-8859-1, produzindo um *double-encoding* (`á` vira dois caracteres errados, que ao
     serem re-serializados como UTF-8 geram 4 bytes em vez de 2). O bean real da aplicação (via
     `MessageSourceAutoConfiguration`) não tem esse problema — é uma armadilha exclusiva de quem
     instancia `new ResourceBundleMessageSource()` manualmente em teste. Correção: sempre chamar
     `messageSource.setDefaultEncoding("UTF-8")` junto com `setBasename`/
     `setFallbackToSystemLocale(false)` nesse padrão de teste.
     > **Pegadinha extra, só apareceu no CI (Linux), não localmente (Windows)**: corrigir
     > `setDefaultEncoding("UTF-8")` numa única classe de teste não basta se **outra** classe do
     > mesmo módulo também instancia `new ResourceBundleMessageSource()` para o mesmo
     > `basename`/`locale` **sem** esse ajuste — `ResourceBundle.getBundle(...)` (usado por baixo
     > dos panos pelo Spring) mantém um **cache estático por JVM**, sem levar o `Control`/encoding
     > em conta na chave. Se a classe "errada" (sem `setDefaultEncoding`) rodar primeiro na mesma
     > JVM (Surefire por padrão reusa uma única JVM fork para todas as classes de teste), ela
     > popula o cache com a versão mal-decodificada, e a classe "certa" (com
     > `setDefaultEncoding`) reaproveita esse cache errado silenciosamente — o resultado depende
     > da **ordem de execução das classes**, que difere entre Windows e Linux (`surefire.runOrder`
     > default não é garantidamente igual nos dois SOs). Sintoma: teste passa isolado
     > (`-Dtest=UmaClasse`) ou na máquina local, falha só na suíte completa ou só no CI.
     > Correção real: aplicar `setDefaultEncoding("UTF-8")` em **toda** instância manual de
     > `ResourceBundleMessageSource` no módulo, não só na classe nova — um site esquecido
     > contamina os outros. Achado em `auth-service feat-003.5` (`MessagesTest` de `feat-001.5`
     > não tinha o ajuste; `AdminApiKeyFilterTest` tinha, e mesmo assim CI falhou até corrigir as
     > duas juntas — confirmado forçando `-Dsurefire.runOrder=alphabetical` e
     > `reversealphabetical` localmente, os dois passam só com as duas classes corrigidas).
- **`@Order` num `@Bean` que retorna um `Filter` de biblioteca (não `@Component` seu) não ordena
  o registro do Filter no Spring Boot** (achado real, `api-gateway feat-012`, 2026-09-11): um
  `@Component` com `@Order` na própria classe (ex.: `CorrelationIdFilter`, `api-gateway feat-006`)
  funciona — o Boot registra `Filter` beans via `ServletContextInitializerBeans`, que só respeita
  ordem via `Ordered`/`@Order` lido da **classe da instância**, não da metadata do método `@Bean`
  que a criou. Um `CorsFilter` (classe do próprio Spring, sem `@Order` nela) anotado
  `@Order(Ordered.HIGHEST_PRECEDENCE)` no método `@Bean` continuou rodando **depois** de filtros
  sem ordem explícita (default `LOWEST_PRECEDENCE`) — só descoberto porque o teste de integração
  (preflight `OPTIONS` real, contexto Spring inteiro) voltou `401` em vez de `200`. Correção:
  envolver em `FilterRegistrationBean<T>` e chamar `.setOrder(...)` explícito — esse é o mecanismo
  que o Boot realmente honra para ordenar um `Filter` que não é uma classe sua. Aplicável a
  qualquer serviço Java deste projeto que precise ordenar um `Filter` de biblioteca (não um
  `OncePerRequestFilter` próprio, que já é `@Component` normal).

### Frontend (apps/web)

- Biblioteca de tradução em **runtime** (decisão do usuário — não `@angular/localize`
  build-time): **`@jsverse/transloco`** — suporte nativo a Signals (consistente com o
  gerenciamento de estado já decidido abaixo), arquivos de tradução JSON por locale
  (`pt-BR.json`, `en-US.json`, `es.json`), troca de idioma instantânea sem reload nem rebuild,
  um único build para os três idiomas. Mesma filosofia do toggle de tema claro/escuro (ver
  [[sistema-de-design]]) — troca em runtime, preferência persistida em `localStorage`, com fallback
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
  strings por locale, um arquivo **JSON** por idioma em
  `src/telegram_integration/locales/{pt-BR,en-US,es}.json` (decisão fechada em 2026-08-02, ver
  [[DECISIONS-LOG]] — evita introduzir `gettext` como dependência só para isso, e usa o mesmo
  formato de [[web]]; caminho dentro do pacote, não na raiz do repositório, desde 2026-09-10 —
  um caminho relativo fora do pacote só resolvia certo em install editable, quebrando em
  qualquer imagem de produção), selecionado pelo campo `language_code` que o
  próprio Telegram Bot API já envia em todo update — não é necessário armazenar preferência de
  idioma em nenhum serviço para isso. Formato validado automaticamente pelo passo de i18n da
  pipeline de CI — ver [[pipeline-ci-cd]].

## Timezone padrão

Primeira convenção de timezone do projeto (decisão de `telegram-integration feat-006`,
2026-09-08 — nenhuma nota fixava isso antes). Todo usuário do sistema é brasileiro (apostas
esportivas no Brasil); onde uma data "de hoje" é inferida sem o usuário informar explicitamente
(ex.: `bet_date` default quando não extraído do texto/foto da aposta, ver
[[telegram-integration]]), usar **`America/Sao_Paulo`**, não UTC — UTC produzia off-by-one perto
da meia-noite local (uma aposta feita às 23h de Brasília virava o dia seguinte). Em Python,
`zoneinfo.ZoneInfo("America/Sao_Paulo")` (stdlib desde 3.9, precisa do pacote `tzdata` como
dependência explícita em runtime Windows — a imagem base do CI/Docker em Linux normalmente já
tem a IANA tzdb do sistema, mas depender disso silenciosamente quebraria em qualquer máquina de
desenvolvimento Windows sem o pacote, como aconteceu ao implementar esta decisão). Não confundir
com o timestamp em si (`Instant`/UTC continua correto para armazenamento — só o cálculo de qual
*dia civil* é "hoje" precisa do fuso correto).

## Frontend (apps/web — Angular 22.x + TypeScript ES2025)

> Corrigido de "21.x" pra "22.x" em `feat-001` (2026-09-09) — mesmo padrão já usado em outros
> serviços (Spring Boot/Java, uv/PyPI): a versão real resolvida pela ferramenta no momento do
> bootstrap é a fonte de verdade, não o número anotado quando esta nota foi escrita. Angular CLI
> 22.1.7 exige Node `^22.22.3 || ^24.15.0 || >=26.0.0` — a máquina de desenvolvimento tinha
> Node 24.9.0 (não satisfaz), corrigido via `nvm install 24.21.0` (LTS).

- **Componentes standalone** (padrão do Angular moderno), sem `NgModule` desnecessário.
- **Gerenciamento de estado: Signals nativos** do Angular, não NgRx. `signal()`/`computed()`
  para estado de componente e de serviços compartilhados (ex.: usuário autenticado, filtros do
  dashboard); evitar `BehaviorSubject`/RxJS para estado simples — reservar RxJS para streams
  assíncronos reais (requisições HTTP, websockets, se vierem a existir).
- **Formulários**: Reactive Forms (`FormGroup`/`FormControl`) no formulário de registro de
  apostas, não Template-Driven Forms — necessário para validação estruturada e feedback claro
  (regras de Shneiderman, ver [[web]]).
  - **Gotcha real recorrente (SonarCloud, `apps/web feat-002`/`feat-004`, 2026-09-09)**: todo
    `<input matInput>`/`<textarea matInput>` sem `id`/`aria-label` explícitos dispara
    `Web:InputWithoutLabelCheck` no gate de qualidade — o Angular Material associa o `<mat-label>`
    ao input via `id` gerado em runtime, mas o scanner estático do SonarCloud lê o HTML da
    template antes da compilação e não enxerga essa associação. Só aparece no PR
    `feature->develop` (gate completo), nunca num PR de subtask (que não roda SonarCloud) —
    reincidiu 2 vezes na mesma sessão por isso. Padrão a aplicar de saída em todo input novo:
    `id="<contexto>-<campo>-input"` + `[attr.aria-label]="'chave.i18n' | transloco"` (mesma string
    do `<mat-label>` correspondente). Banner de confirmação/erro com `role="status"`/`role="alert"`
    também é sinalizado (`Web:S6819`) — usar `<output>` no lugar de `role="status"` (mantém
    `role="alert"` pra erro, que não tem substituto semântico equivalente).
  - **Duplicação (`new_duplicated_lines_density`, gate `feature -> develop`) também pega
    literais de configuração repetidos, não só componentes** (achado real, `apps/web feat-016`,
    gate `feature->develop`, PR #75): 9 blocos de rota quase idênticos em `app.routes.ts` (4
    "Cadastrar" + 5 "Dashboard", só variando `path`/`resourcePath`/`segment`/`labelKey`) foram
    detectados como 100% duplicados (11,1% de densidade no PR, limite é 3%) mesmo sem nenhum
    componente duplicado — o mesmo precedente de "1 componente parametrizado em vez de N
    quase-cópias" (`feat-003`/`008`) se aplica também a um array de configuração de rotas: extrair
    uma tabela de dados (`{path, resourcePath}[]`) e gerar os objetos `Route` via `.map()` em vez
    de repetir o literal.
  - **`mat-select`/`mat-form-field` (appearance `outline`) mantêm o label flutuante clicável,
    interceptando cliques em campos estreitos** (achado real, `apps/web feat-018`, sidebar
    lateral estreitou a grade de 3 colunas de `register-bet`): o rótulo visualmente flutuado
    (`label.mdc-floating-label`, posicionado via `transform`, não por layout) mantém
    `pointer-events: all` nesta versão do Material em vez do `none` que a especificação MDC
    normalmente daria a ele — o mesmo vale pro `<mat-label>` cru projetado e pro espelho do
    rótulo dentro de `.mdc-notched-outline` (usado só pra dimensionar o recorte do contorno). Os
    três se sobrepõem geometricamente ao campo **independente da largura do layout** — só vira
    problema quando o campo fica estreito o bastante pro centro do clique (onde `page.click()`
    do Playwright mira por padrão) cair sobre um deles em vez de além. Bug latente, não novo:
    qualquer usuário clicando nesse mesmo intervalo de pixels já falhava em abrir o dropdown
    antes desta feature estreitar o campo o bastante pra tornar isso provável. Corrigido
    globalmente em `src/styles.scss`: `mat-label`, `.mdc-notched-outline` (`pointer-events: none`
    simples resolve) e `.mdc-floating-label` (precisa de `!important` — o Material injeta uma
    declaração concorrente em empate de especificidade, depois desta folha de estilo global, e
    vence o empate por ordem). `mat-select` já encaminha o clique do rótulo via `aria-owns`, não
    por `<label for>` nativo — nenhum dos três elementos tem papel interativo legítimo próprio.
  - **Diretiva de atributo do Material sem o módulo importado falha em silêncio, não em erro**
    (achado real, `apps/web feat-019.2`): um standalone component que usa `mat-icon-button`/
    `mat-button`/etc. no template sem importar `MatButtonModule` (ou o standalone directive
    equivalente) no array `imports` do `@Component` **não gera erro de compilação nem de
    runtime** — Angular trata `mat-icon-button` como um atributo estático comum, já que nenhuma
    diretiva reivindica aquele seletor. O elemento (`<button mat-icon-button>`) continua
    renderizando, só que como `<button>` HTML puro, com o chrome padrão do browser (fundo cinza,
    borda `outset`) em vez do botão circular sem borda do Material — e como o chrome nativo segue
    o `color-scheme` do sistema operacional/browser, não os tokens de tema do app, o sintoma
    visível pode ser "a cor não respeita o tema", levando a investigar CSS que nunca foi a causa.
    Só aparece ao inspecionar o elemento renderizado (classes `mat-mdc-*` ausentes) ou via
    `getComputedStyle` — nenhum teste unitário (`jsdom`, sem CSS real do Material) pega. Checar
    sempre que um botão/ícone do Material "não está estilizado direito": conferir primeiro se o
    módulo está no array `imports` do componente, antes de investigar SCSS.
  - **"Grid blowout": item de grid/flex com filho `overflow-x: auto` ainda estoura a página se o
    próprio item não tiver `min-width: 0`** (achado real, `apps/web feat-025`, tabela de
    `betting-houses` com uma coluna nova): `app-panel-layout` já tem `grid-template-columns: 1fr`
    abaixo de 600px (mobile) e a tabela larga já estava dentro de um `.table-wrap { overflow-x:
    auto }` (mesmo padrão de `history.scss`) — mesmo assim a página inteira estourava a largura
    da viewport em mobile. Causa: itens de grid/flex usam `min-width: auto` por padrão, que
    equivale ao tamanho de conteúdo mínimo dos descendentes — isso **ignora** `overflow` de
    qualquer filho, porque o cálculo de tamanho do track do grid acontece antes/independente de
    como o overflow vai ser renderizado visualmente. Sintoma: o `overflow-x: auto` "não funciona"
    mesmo estando no lugar certo, porque o problema não é ali, é no ancestral (o item de grid)
    que nunca encolhe abaixo do conteúdo. Corrigido com `min-width: 0` no `:host` de `app-panel`
    (o item de grid real de `app-panel-layout`) — vale pra qualquer página que use `app-panel`
    com conteúdo largo (tabela, código, etc.), não só `betting-houses`. Verificar sempre que um
    `overflow-x: auto` num filho não parece surtir efeito dentro de um layout de grid/flex.
  - **`display: block` envolvendo um filho com `width: 100%`, sem largura definida em nenhum
    ancestral, mede errado** (achado real, `apps/web feat-023.1`, seletor de idioma sobreposto ao
    botão de tema no login): `core/language-selector/language-selector.scss` tinha
    `.language-selector-host { display: block }` envolvendo `.language-selector { width: 100% }`
    — funciona quando ALGUM ancestral tem largura definida (a sidebar, que sempre deu certo), mas
    quebra quando o componente fica dentro de um container que também se auto-dimensiona pelo
    conteúdo (a tela de login, `.app-shell__floating-controls`, um `flex` sem largura própria).
    Bloco (`display: block`) não tem regra de spec garantindo medição correta de um filho
    percentual nesse cenário de shrink-to-fit encadeado — medido contra o dev server real
    (`getBoundingClientRect()`), o filho renderizava 13–26px mais largo que a própria caixa que
    deveria contê-lo, vazando sobre o elemento vizinho. Trocar o ancestral pra `display: flex`
    (mesmo modo de layout do filho) resolve: Flexbox tem regra explícita pra isso (item flex com
    largura percentual é tratado como `auto` pro dimensionamento intrínseco do próprio container,
    CSS Flexbox §9.9). Verificar sempre que um componente com filho `width: 100%`/`height: 100%`
    for reusado num container novo sem largura/altura própria — não basta funcionar no lugar
    onde foi criado originalmente.
  - **`FormGroup.reset()` não limpa a flag `submitted` da `FormGroupDirective`** (achado real,
    `apps/web feat-035`, pego só por QA visual real — nenhum teste unitário/e2e mockado pega,
    porque nenhum dos dois renderiza o `ErrorStateMatcher` do Material com CSS real): o
    `ErrorStateMatcher` padrão do Angular Material considera um campo inválido quando
    `control.invalid && (control.touched || form.submitted)` — `form` aqui é a
    `FormGroupDirective` associada ao `<form [formGroup]>`, cujo `submitted` vira `true` no
    primeiro `(ngSubmit)` e **fica** `true` depois, porque `FormGroup.reset()` só reseta o
    `FormGroup` em si (valor/`touched`/`dirty`), não a diretiva. Sintoma: um formulário que se
    limpa a si mesmo após um submit bem-sucedido (em vez de navegar pra outra tela) mostra todos
    os campos `required` com borda vermelha de erro assim que ficam vazios de novo — ao lado da
    própria mensagem de sucesso. Corrigido com `@ViewChild(FormGroupDirective) formDirective` no
    componente e `this.formDirective.resetForm()` no lugar de `this.form.reset()` — reseta o
    `FormGroup` E a flag `submitted` junto. Aplicar em qualquer formulário novo deste app que
    permaneça na mesma tela e se limpe após sucesso.
  - **`NativeDateAdapter.parse()` (Angular Material) é `new Date(Date.parse(value))` — sempre
    M/D/Y para uma string com `/`, INDEPENDENTE do locale ativo do app** (achado real e crítico,
    `apps/web feat-034.3`, confirmado contra um browser real, não só leitura de código): lido
    `node_modules/@angular/material/fesm2022/core.mjs` — `format()` usa `Intl.DateTimeFormat(
    this.locale, ...)` (reage a `setLocale()`), mas `parse()` **não** — é só `Date.parse()` puro,
    e `Date.parse()` para uma string não-ISO separada por `/` segue a convenção americana (M/D/Y)
    em todo motor JS relevante, sempre, não importa `MAT_DATE_LOCALE`/`setLocale()`. O primeiro
    `appDateMask` (diretiva de máscara de digitação `__/__/____`, `core/date-mask.directive.ts`)
    formatava dia/mês/ano na ordem do locale ativo (`pt-BR`/`es` = D/M/Y, via
    `Intl.DateTimeFormat(locale).formatToParts()`, mesmo racional Intl-based de
    `core/date-format.ts`) — parecia correto e passava em unitário (JSDOM nunca resolve o Date
    de verdade nesse caminho, só prova a formatação da string em si, ver abaixo). Só um teste
    e2e real (`e2e/period-report.spec.ts`, digitando "05092026" esperando 5 de setembro em
    pt-BR) expôs o defeito: `Date.parse("05/09/2026")` sempre lê mês=05/dia=09, então uma
    aposta com dia≤12 e mês diferente do dia seria salva com dia e mês **trocados, em
    silêncio** — sem erro, sem validação, só um dado errado no banco. Corrigido removendo o
    Intl/locale da ordem da máscara — `appDateMask` agora usa M/D/Y **sempre**, independente do
    idioma ativo (só o texto do placeholder continua traduzido — a ORDEM de digitação exigida
    para o parse funcionar nunca varia, só a legenda visual). O clique no calendário do próprio
    `mat-datepicker` nunca teve esse problema (constrói um `Date` direto a partir de ano/mês/dia,
    nunca passa por `Date.parse()` de string) — só o caminho de digitação de texto livre é
    afetado. Qualquer máscara/parsing de data futura neste app **não pode** assumir que o locale
    ativo controla a ordem esperada por `matDatepicker`; controla só a exibição.
  - **JSDOM nunca resolve um `Date` real através de `input+matDatepicker+ngModel`, mesmo para um
    valor completo e corretamente formatado setado diretamente (sem digitação)** (achado real,
    mesma feature): um harness mínimo (`date-mask.directive.spec.ts`) que seta `input.value =
    '17/09/2026'` e dispara `input.dispatchEvent(new Event('input'))` nunca preenche o `ngModel`
    vinculado, mesmo com `provideNativeDateAdapter()` e `DateAdapter.setLocale()` configurados —
    causa raiz não identificada (não vale o custo de investigar mais a fundo só para viabilizar
    unitário). Confirma o padrão já usado por `period-preset-filter.spec.ts` (testar o
    componente via chamada direta de método, não pela digitação real no DOM) e desloca a prova
    de que o texto digitado realmente vira um `Date` correto para o e2e (Playwright, browser
    real) — unitário prova só a formatação da string (`input.value`), não o parse.
  - **Vitest/JSDOM neste projeto resolve `navigator.language` como `en-US`, não `pt-BR`** (achado
    real, mesma feature, `register-bet.spec.ts`): qualquer `describe` que nunca precisou de
    `Language` antes (nenhum componente da árvore o injetava) e ganha uma dependência nova que o
    injeta (aqui, `DateMaskDirective` em `betDateOnly`) corre o risco de `Language.current()`
    resolver via `browserLocale()` (fallback quando `localStorage['stakevault.language']` está
    vazio) para `en-US` em vez do `pt-BR` que o `langs`/`availableLangs` do teste presume — toda
    chamada `.translate()`/pipe do componente (não só da diretiva nova) passa a resolver contra
    um lang não registrado no mock, retornando a chave crua/formato de fallback do Transloco em
    vez do texto esperado. Sintoma enganoso: o teste que quebra é o que afirma uma STRING
    traduzida literal (`expect(...).toBe('Aposta registrada com sucesso.')`), não o que só
    verifica presença/estrutura — os demais testes do mesmo arquivo continuam verdes. Corrigido
    com `localStorage.setItem('stakevault.language', 'pt-BR')` explícito no `beforeEach` (não
    `removeItem` — o fallback do browser não é `pt-BR` neste ambiente), mesmo padrão que
    `auth.spec.ts`/`app-side-nav.spec.ts` já usam. Ao adicionar a QUALQUER componente uma
    dependência nova que injeta `Language` (direta ou via uma diretiva/serviço), conferir se o
    spec daquele componente já fixa o locale explicitamente antes de confiar em asserções de
    texto traduzido.
- **Estilo**: SCSS por componente (`:host`), utilizando Angular Material. Tema (claro/escuro),
  paleta de cores e inventário de componentes visuais já decididos em [[sistema-de-design]] — não
  escolher uma paleta alternativa por conta própria.
  - **Gotcha real (`apps/web` `feat-001.7`, 2026-09-09)**: um elemento customizado Angular
    (`<app-x>`) é `display: inline` por padrão, igual qualquer tag desconhecida do browser —
    componente algum recebe `block`/`flex`/`grid` de graça. Se o componente participa de um
    layout que depende de altura definida (item de CSS Grid, `height: 100%` encadeado, etc.),
    `:host` **precisa** declarar `display` explicitamente (`block`, na maioria dos casos) e a
    própria altura (`height: 100%`/`max-height: 100%`) — sem isso a cadeia de dimensionamento
    nunca se aplica de verdade, e o problema não aparece em teste unitário (`jsdom` não roda
    layout real, só o Playwright/browser real pega). Achado real:
    `app-panel`/`app-panel-layout` (`feat-001.4`) sem esse `:host` fez um painel com conteúdo
    maior que a viewport crescer a página inteira em vez de rolar internamente — só descoberto
    quando o Playwright de `feat-001.7` deu o primeiro browser real da sessão pra tirar
    screenshot. Verificar todo componente novo que participa de layout (não decorativo/inline)
    contra isso antes de assumir que `height: 100%`/`overflow: auto` no CSS "deveriam" funcionar.
  - **Um pai forçando `width: 100%` no host de um componente não centraliza o conteúdo do
    componente** (achado real, `apps/web feat-019.1`, `theme-toggle` no rodapé colapsado da
    sidebar): `.side-nav__footer` (flex column) forçava `app-theme-toggle { width: 100%; }` pra
    dar largura total ao componente quando expandido, mas o `:host { display: block }` do
    próprio componente não tem nenhuma regra de centralização — um filho de tamanho fixo (o
    `mat-icon-button`, ~40px) dentro de um bloco 100% de largura fica encostado na borda inicial
    (esquerda), não centralizado, porque `width: 100%` só define o tamanho da caixa do host, não
    como o conteúdo dele se posiciona dentro dela. Corrigido no componente, não no pai: `:host`
    (ou um wrapper interno) precisa do próprio `display: flex; justify-content: center` sempre
    que o componente for usado num contexto onde a largura do host pode exceder a do conteúdo.
- **i18n**: `@jsverse/transloco`, três locales sempre em sincronia (`pt-BR`/`en-US`/`es`) — ver
  seção "Internacionalização (i18n)" acima, não hardcodar strings de UI.
- **Cliente HTTP**: serviços Angular tipados por domínio (`AuthService`, `BetsService`,
  `StatsService`), um por serviço backend consumido, usando os tipos documentados em
  [[contratos-de-api]]. Não gerar cliente automaticamente a partir de OpenAPI neste projeto (escopo
  pequeno o suficiente para não justificar a ferramenta extra) — mas manter os tipos TypeScript
  sincronizados manualmente com os DTOs Java é responsabilidade de quem mexe na feature.
- **Nunca usar `any`** (decisão de 2026-09-04): todo tipo é explícito — `unknown` + type guard
  quando o tipo de fato não é conhecido em tempo de compilação, nunca `any` como atalho. Vale
  para parâmetro, retorno, variável e genérico.
- **Bibliotecas pesadas usadas só numa rota — escopar no componente, não em `app.config.ts`**
  (achado real, `apps/web` `feat-001.6`, 2026-09-09): registrar `echarts.use([...])` +
  `provideEchartsCore({echarts})` (~500KB) globalmente estourou o budget de erro do
  `angular.json` (1MB). Corrigido movendo o registro pros `providers` do próprio componente que
  usa o gráfico — como Angular só resolve esses providers quando o componente é de fato
  instanciado, e o componente só existe numa rota lazy (`loadComponent`), a biblioteca inteira
  fica dentro do chunk daquela rota em vez do bundle principal (confirmado no tamanho real dos
  chunks pós-build, não só na teoria). `ngx-echarts` é usado por todos os gráficos de RF10/RF11
  (ver [[sistema-de-design]] item 6) — qualquer novo gráfico de `feat-006` (dashboard real) deve
  seguir o mesmo padrão de escopo por componente, não reintroduzir o registro global.
- **Teste unitário de componente com `ngx-echarts` real precisa de um stub de contexto 2D de
  canvas** (achado real, `apps/web` `feat-006`, 2026-09-09): `jsdom` não implementa
  `HTMLCanvasElement.getContext('2d')` de verdade sem o pacote nativo `canvas` (não instalado
  neste projeto - build nativo, sem necessidade fora de teste) - `getContext` devolve `null`, e
  o `zrender` (renderer do Apache ECharts) desreferencia esse contexto sem checar null tanto na
  inicialização (`Layer.initContext`, ex.: `ctx.dpr = ...`) quanto no `dispose()`
  (`Layer.clear` → `ctx.clearRect`), lançando `TypeError` real (não só warning) - o erro
  geralmente aparece no `afterEach`/cleanup do `TestBed`, não na asserção do teste em si, o que
  o torna fácil de confundir com um problema de outra causa. Corrigido com um stub local por
  arquivo de teste (mesmo padrão de duplicação já usado pro `ResizeObserverStub` de
  `feat-001.6`, não um helper compartilhado novo): `HTMLCanvasElement.prototype.getContext`
  substituído por uma função que devolve um `Proxy` permissivo (todo método é no-op, toda
  propriedade é gravável, `createLinearGradient`/`createRadialGradient` devolvem um objeto com
  `addColorStop` no-op) - não valida pixel nenhum, só permite que o ciclo de vida completo do
  ECharts (init → setOption → dispose) rode sem lançar. Ver
  `apps/web/src/app/shared/monthly-profit-chart/monthly-profit-chart.spec.ts` (`stubCanvasContext`)
  para a implementação de referência - qualquer novo teste que renderize um componente com
  `NgxEchartsDirective` real (não só os gráficos de `feat-006`, qualquer futuro RF10/RF11) precisa
  do mesmo stub.
- **Escala Y compartilhada entre instâncias irmãs de `ngx-echarts`** (mecanismo introduzido em
  `apps/web feat-058.1`, 2026-09-25, corrigindo a grade de mini-gráficos de `monthly-drawdown-grid`
  onde cada instância auto-escalava o próprio eixo Y, fazendo o mês com lucro acumulado menor
  parecer maior/mais inclinado que os demais): `buildLineChartOption`/`LineChartStyleOptions`
  (`core/chart-theme.ts`) aceitam `yMin`/`yMax` opcionais, setados em `yAxis.min`/`max` só quando
  fornecidos — sem eles o comportamento auto-scale de sempre continua (nenhum outro consumidor
  precisa mudar). O min/max compartilhado é calculado uma vez (ver `computeSharedYRange` em
  `shared/monthly-drawdown-chart/monthly-drawdown-metrics.ts`, arredondado pra fora em 1 casa
  decimal pra não gerar rótulo de eixo com dízima) e passado como `input()` pra cada instância do
  gráfico. Reaproveitar este padrão em qualquer grade futura de gráficos comparáveis lado a lado
  (RF10/RF11) em vez de deixar cada instância auto-escalar.
- **Componente `@Input`-driven: separar o `effect()` que dispara a busca do `computed()` que
  deriva o que é exibido** (mesma feature, `feat-058.2`): quando um componente recebe filtro +
  outros dados já carregados pelo pai via `input.required<...>()`, só os campos que realmente
  mudam a query HTTP devem estar dentro do `effect()` de fetch — campos usados só pra converter a
  resposta já carregada (ex.: saldo/percentual de unidade convertendo `netProfit` em unidades)
  pertencem a um `computed()` separado a partir do dado bruto já em signal. Bug real evitado por
  essa separação: colocar todos os inputs no mesmo `effect()` de fetch dispara uma requisição HTTP
  nova toda vez que QUALQUER um deles muda, mesmo quando só o dado já carregado precisava ser
  recalculado (ex.: usuário salva um novo `unitPercent` — não deveria refazer a chamada de
  `/statistics/daily`, só reconverter o resultado já em memória).
- **QA visual (Impeccable/taste-skill)**: ferramentas de design guidance para agentes de IA,
  usadas só como auditoria/polish de componentes já implementados contra [[sistema-de-design]] —
  nunca como fonte de novas decisões de design (esse documento já é a fonte de verdade). Ver
  [[sistema-de-design]] seção "QA visual" para o racional completo e status de instalação.

## Python (telegram-integration)

- Gerenciador de dependências: **uv** (mais rápido, `pyproject.toml` único, sem `requirements.txt`
  espalhado) — se um agente sessão futura preferir Poetry/pip puro, deve primeiro atualizar esta
  nota, não decidir isoladamente dentro da pasta do serviço.
- Formatação/lint: `ruff` (format + lint em uma ferramenta só).
- Tipagem: usar type hints (`from __future__ import annotations` se necessário) e `mypy` no CI
  local, mesmo em um serviço pequeno — facilita retomar o código entre sessões.
- **i18n**: mensagens do bot para o usuário são localizadas (`pt-BR`/`en-US`/`es`) via o
  `language_code` do update do Telegram — ver seção "Internacionalização (i18n)" acima.
- **Framework HTTP: FastAPI + Uvicorn** (decisão de `feat-001`, 2026-09-08 — nenhuma nota fixava
  isso antes). Motivo: type hints nativos (já convenção deste serviço, mypy-friendly), validação
  automática via Pydantic para o JSON normalizado que chega do n8n (reduz parsing defensivo
  manual), `TestClient` síncrono embutido facilita `pytest` sem depender de `pytest-asyncio`.
  n8n chama este serviço via HTTP depois de normalizar o payload do webhook do Telegram (ver
  [[telegram-integration]]) — o endpoint real de parsing só existe a partir de `feat-002`, mas o
  framework já fica fixado aqui para não ser redecidido por sessão.
- **OCR: Tesseract local via `pytesseract`** (decisão de `feat-002`, 2026-09-08, ver
  [[DECISIONS-LOG]]) — não API de nuvem, para não introduzir a primeira dependência paga/externa
  do projeto. Precisa do binário `tesseract-ocr` instalado no sistema (não é só pacote `pip`) —
  trivial via `apt-get` no CI/Docker, precisa de instalação manual (`choco` no Windows) em
  máquina de desenvolvimento.
- **Cliente Redis: `redis` (redis-py)**, síncrono — mesma instância já provisionada em
  `infra/docker-compose.yml` para `stats-service`, reaproveitada aqui só para guardar o estado
  do fallback conversacional de captura de aposta (ver [[DECISIONS-LOG]] 2026-09-08), não para
  cache de leitura como em `stats-service`. Mesmas variáveis de ambiente
  (`REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`, ver `.env.example` de `stats-service`).

## Git — fluxo de trabalho

Modelo de **4 níveis** de branch (3 níveis decididos em 2026-08-02; o nível de subtask entrou em
2026-08-03 junto com o espelhamento no Jira — ver [[DECISIONS-LOG]]), igual nos 7 repositórios
**de código** (cada serviço e `infra/` — ver [[pipeline-ci-cd]]). O repositório `sv-harness` da raiz é a
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
    > seção "Changelog por serviço" de [[pipeline-ci-cd]]), e a PR final `feature/` → `develop` mostra
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
  documentação e definição de negócio, nunca o código-fonte. `package-info.java` **não** é
  exceção — removidos de todos os pacotes em `auth-service feat-002` por duplicarem o diagrama de
  estrutura já documentado na seção "Arquitetura interna dos serviços Java" acima; não recriar em
  nenhum dos 4 serviços Java.
- **Merge `subtask/` → branch da story**: `--no-ff`, via PR, com a **pipeline de CI daquele PR
  passando** (i18n, build, testes — não changelog, ver [[pipeline-ci-cd]] seção "Changelog por serviço")
  e a subtask marcada `done` no `feature_list.json`. **Não** exige `./init.sh` local nem as
  skills de revisão de `claude-code-skills`: um estado intermediário raramente passa no gate de
  cobertura (um `docker-compose.yml` sem o RabbitMQ ainda não sobe; `mvn verify` num serviço pela
  metade também não). O **SonarCloud é pulado** nesses PRs — cobertura parcial de uma feature em
  andamento reprovaria o quality gate de código novo sem indicar defeito real (condição
  `github.base_ref` no `ci.yml`, ver [[pipeline-ci-cd]]).
- **Merge de `feature/`/`bugfix`/`spike/` → `develop`**: gate completo — `./init.sh` daquele
  repositório passando, `feature_list.json` atualizado (todas as `subtasks` `done`, `evidence`
  preenchida), skills de revisão rodadas (ver [[habilidades-do-agente]]) e a pipeline de CI inteira,
  **incluindo SonarCloud** (changelog, i18n, build, testes, Sonar nos 6 de aplicação; changelog +
  validação do compose em `infra/`) — ver [[pipeline-ci-cd]]. **Branch protection real nos 7 repositórios
  do GitHub** (`develop` e `main`, `required_status_checks` no check `pipeline`, configurado via
  API em 2026-09-04 depois de uma PR mergear com 27 apontamentos do SonarCloud nunca revisados —
  até então nenhuma falha de CI de fato impedia o botão de merge, só ficava um X vermelho
  cosmético). Sem essa proteção, todo o resto desta lista é convenção seguida por disciplina, não
  um gate de verdade.
- **`CHANGELOG.md`**: uma linha por issue do Jira (story e cada subtask), formato
  `- [chave](url) - título`, nada além disso — sem prosa, sem categoria Added/Fixed. Escrita
  automaticamente por `tools/jira_story.py` no momento em que cada issue é criada, nunca à mão
  pela sessão (ver [[pipeline-ci-cd]] seção "Changelog por serviço" para o racional completo e o motivo
  de a validação de changelog só rodar na PR story → `develop`, não nas de subtask).
- **Merge de `develop` → `main`**: quando o conjunto de features acumuladas em `develop` estiver
  estável o suficiente para ser considerado uma entrega (não há cadência fixa definida — critério
  é estabilidade, não calendário).
- **Deletar branch de trabalho depois do merge** (decisão de 2026-09-04): toda `feature/`/
  `subtask/`/`bugfix/` — local e remota (`git branch -d`/`git push origin --delete`) — assim que
  o merge que a fecha for concluído (subtask → branch da story, ou story → `develop`). A chave
  do Jira já preserva o nome/histórico via `feature_list.json`; a branch em si não carrega
  informação que não esteja nos commits mergeados. Não deletar antes de confirmar o merge (`git
  branch -d` já recusa branch não mergeada, proteção suficiente).
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
    rota pública, header de confiança). Ver [[contratos-de-api]].

  **O idioma inglês vale só para a mensagem de commit.** Não muda `CHANGELOG.md`, `progress.md`,
  `session-handoff.md`, `feature_list.json` nem o vault, que seguem em português — e não muda a
  regra de i18n de conteúdo de produto (ver seção "Internacionalização (i18n)"). Motivo: commit
  é superfície técnica compartilhada com nomes de rota, evento e código, todos já em inglês;
  documentação de projeto é entregável de TCC, em português.
