---
tags: [conventions, testing]
---

# Estratégia de testes

Ver [[CONVENTIONS]] para arquitetura/código. O TCC 1 já define a meta de cobertura (seção
"Método", fase "Verificação" do fluxo Kanban): **cobertura de testes unitários superior a 80%**
antes de uma feature ser considerada `done` — isso vale para todos os serviços, não só os Java.

## Nomenclatura de testes (todos os serviços)

Nome de método/caso de teste sempre em **inglês**, padrão `should<ComportamentoEsperado>` (ex.:
`shouldRejectDuplicateEmail`, `shouldReturnEmptyWhenUserIdNotFound`) — nunca descrição em
português (`salvaEBuscaPorId`, `emailDuplicado_rejeitado`). Motivo: mesmo racional de
`docs/CONVENTIONS.md` para mensagem de commit — superfície técnica compartilhada com nomes de
classe/método, que já são em inglês; só documentação de projeto (`CHANGELOG.md`, `progress.md`,
vault) segue em português. Decisão de 2026-09-04, corrigindo os testes de `auth-service feat-001`
e o início de `feat-002`, escritos em português antes desta regra existir — não reescritos
retroativamente sem confirmação do usuário (fora do escopo desta nota; não é divergência do TCC1,
por isso não entra em `docs/DECISIONS-LOG.md` — mesmo padrão de "Título do PR"/"Comentário em
código" em `docs/CONVENTIONS.md`).

## Java (auth-service, bets-service, stats-service)

- **Unitários**: JUnit 5 + Mockito + AssertJ. Testam `domain/` e `application/` isoladamente,
  mockando os `port/out/` (ver [[CONVENTIONS]] para a estrutura hexagonal). Nenhum teste
  unitário deve subir contexto Spring (`@SpringBootTest`) nem tocar banco/RabbitMQ real.
- **Integração**: **Testcontainers** para Postgres, RabbitMQ e Redis (quando aplicável) — testam
  os `adapter/out/persistence/` e `adapter/in/messaging/` contra instâncias reais e efêmeras,
  não contra os mocks usados nos unitários. Não reusar o `infra/docker-compose.yml` de
  desenvolvimento para testes automatizados — Testcontainers sobe/derruba os containers por
  execução de teste, isolado do ambiente de dev.
- **Schema-per-tenant nos testes de integração** (decisão de 2026-08-02, ver [[DECISIONS-LOG]]):
  `auth-service`, `bets-service` e `stats-service` são schema-per-tenant com migração lazy (ver
  [[CONVENTIONS]] seção "Migrations") — um teste de `adapter/out/persistence/` não tem schema
  nenhum pronto no Postgres efêmero do Testcontainers até que algo o crie.
  - Uma classe base de teste de integração por serviço (`src/test/java/.../support/`, não
    compartilhada entre serviços — cada um é buildado independentemente, ver [[CONVENTIONS]])
    provisiona um schema de teste **chamando o mesmo caso de uso de provisionamento usado em
    produção** (o port/in de `application/` que cria o schema + roda o Flyway, ex.:
    `ProvisionTenantSchemaUseCase`), não uma cópia do SQL de criação de schema escrita à mão no
    teste. Isso garante que produção e teste exercitam exatamente o mesmo caminho de código, e
    que testes já passam a validar o provisionamento como efeito colateral.
  - Chamar o caso de uso diretamente (camada `application/`), **não** a rota HTTP administrativa
    — desacopla a fixture de teste do mecanismo de autenticação daquela rota, que ainda está em
    aberto (ver [[DECISIONS-LOG]] item 3). Quando esse mecanismo for decidido, só o teste da
    própria rota HTTP (um teste a mais, não a fixture inteira) precisa mudar.
  - Slug do tenant de teste é único por classe de teste (ex.: `test_<uuid>`), não um valor fixo
    — evita colisão de schema se o container do Testcontainers for reaproveitado entre classes
    (padrão comum para acelerar a suíte). Schema derrubado (`DROP SCHEMA ... CASCADE`) ao final
    da classe.
  - Consequência prática: **não existe teste de persistência sem tenant** neste projeto — todo
    teste de `adapter/out/persistence/` roda dentro de algum schema de tenant de teste, nunca
    contra o schema `public`/default do Postgres.
- **Idempotência (stats-service)**: teste explícito de que processar o mesmo evento
  (`BetCreated` ou `BetSettled`) duas vezes — mesmo `eventId`, redelivery do RabbitMQ — não
  duplica linhas nem métricas em `FACT_BET`. Mecanismo: tabela `PROCESSED_EVENT` (ver
  [[stats-service]]), consultada antes de processar e escrita na mesma transação. É a regra mais
  fácil de quebrar sem perceber.
- **Cobertura**: JaCoCo, gate de 80% de cobertura de linha vinculado à fase `verify` do Maven
  (`mvn verify` falha se a cobertura cair abaixo do limite). Cada `init.sh` de serviço Java roda
  `mvn verify`, não apenas `mvn test`, exatamente para aplicar esse gate automaticamente.
- **i18n**: pelo menos um teste de integração por serviço confirma que uma resposta de erro
  muda de `title`/`detail` conforme o header `Accept-Language` (`pt-BR` vs `en-US` vs `es`) —
  não é suficiente testar só o idioma padrão (ver [[CONVENTIONS]] seção "Internacionalização").
- **`BigDecimal` e coluna `NUMERIC` — não comparar por `equals()`/`record` cru** (achado real de
  `bets-service feat-003`): uma coluna `NUMERIC(19,2)` sempre devolve o valor já normalizado pra
  escala 2 (`100` vira `100.00`) depois do round-trip pelo banco. `BigDecimal.equals()` (usado
  implicitamente pelo `equals()` gerado de um `record` de domínio, ex.: `BettingHouse`) considera
  escala diferente como valor diferente — um teste que insere `BigDecimal.valueOf(100)` (escala 0)
  e depois faz `assertThat(lista).contains(objetoOriginal)` falha mesmo com o valor "certo"
  persistido. Comparar campos monetários com `isEqualByComparingTo(...)` (AssertJ) em vez de
  `contains`/`isEqualTo` sobre o objeto inteiro, ou extrair o campo e comparar à parte — vale para
  qualquer entidade futura com campo `BigDecimal` (`BET.stake`/`odd` em `feat-004`).

## Frontend (apps/web)

- **Unitários/componente**: o test runner padrão do Angular CLI no momento em que `feat-001`
  daquele app rodar `ng test` (Angular 21 pode já ter migrado de Karma para outro runner — a
  primeira sessão que rodar `ng new`/`ng test` registra em
  `apps/web/progress.md` qual runner foi de fato usado).
- **E2E**: Playwright, cobrindo todos os fluxos cadastro de aposta manual,
  atualização de status de aposta, e filtro de dashboard recalculando métricas (RN08).
- **Cobertura**: `ng test --code-coverage`, mesma meta de 80% do restante do projeto.
- **i18n**: pelo menos um fluxo Playwright roda com o idioma trocado para `en-US` (ou `es`) via
  o seletor de idioma, confirmando que o texto renderizado muda — não é suficiente testar só
  `pt-BR` (ver [[CONVENTIONS]] seção "Internacionalização"). Não é necessário duplicar todos os
  fluxos em todos os idiomas, só confirmar que a troca funciona de ponta a ponta.

## Python (telegram-integration)

- **pytest** + **pytest-cov** (meta de 80%, mesma regra do projeto).
- Mockar chamadas HTTP externas (API do Telegram, webhook do n8n) — nenhum teste automatizado
  deve depender de credenciais reais ou de rede externa disponível.
- Testar especificamente o parser com mensagens malformadas/incompletas (não só o caminho feliz)
  — é a superfície mais sujeita a bugs deste serviço, por lidar com texto livre do usuário.

## Testes de contrato entre serviços

O par `bets-service` (produtor) / `stats-service` (consumidor) dos eventos `BetCreated`/
`BetSettled` não tem um broker de contrato automatizado (Pact ou similar) neste projeto — escopo
pequeno demais para justificar a ferramenta. Em vez disso:

- O schema de cada evento é a fonte da verdade (ver [[API-CONTRACTS]] e os dois arquivos em
  `docs/contracts/`: `bet-created.schema.json` e `bet-settled.schema.json`).
- `bets-service` deve ter um teste que valida cada mensagem publicada contra o JSON Schema
  correspondente.
- `stats-service` deve ter um teste que valida uma mensagem de exemplo (fixture) de cada tipo
  contra o JSON Schema correspondente antes de testar a lógica de consumo.
- Se algum schema mudar, os dois testes (em repositórios/pastas diferentes) devem ser
  atualizados no mesmo commit/feature — não é aceitável só um lado saber da mudança.

## CI e SonarCloud

Os relatórios de cobertura definidos acima (JaCoCo XML, LCOV do `ng test --code-coverage`,
`coverage.xml` do `pytest-cov`) são gerados localmente pelo `init.sh`/gate de cada serviço e
também consumidos pela pipeline de CI para a análise de qualidade/cobertura no SonarCloud — ver
[[CI-CD]] para os 6 passos da pipeline e o setup pendente. O gate de 80% em si continua sendo
aplicado localmente (`mvn verify`/`ng test`/`pytest-cov`), o Sonar não duplica esse gate, só
reporta a métrica.

## Ver também

- [[DECISIONS-LOG]] — racional do modelo de tenant multiusuário e por que a fixture de teste de
  integração provisiona schema chamando o caso de uso de produção, não a rota admin HTTP.
- [[CI-CD]] — pipeline de CI por serviço (changelog, i18n, build, testes, SonarCloud).
