---
tags: [conventions, design, frontend]
---

# Design System — apps/web

Convenção normativa de tema e componentes visuais para [[web]], no mesmo espírito de
[[CONVENTIONS]] (fecha uma lacuna que o TCC 1 não especificava — ele cobre requisitos e
modelagem de dados, não identidade visual). Ver [[CONVENTIONS]] seção "Frontend" para a
arquitetura Angular (standalone, Signals, Reactive Forms, Angular Material) que este documento
assume e estende.

> **i18n**: todo texto usado nos componentes deste documento ("Watchlist", "Banca atual",
> "Not set", "Em aberto" etc.) é **referência visual das capturas/mockups, não copy final da
> aplicação** — a implementação real passa cada string por `@jsverse/transloco` nos três locales
> sempre mantidos (`pt-BR`/`en-US`/`es`), ver [[CONVENTIONS]] seção "Internacionalização (i18n)".
> Nenhum componente do inventário abaixo tem texto hardcoded — isso vale inclusive para a
> tagline do logo (ver seção "Identidade visual"), que não é fixa apesar de estar num mockup de
> marca.

## Fonte

Duas camadas de referência, nesta ordem de autoridade (a mais recente refina a mais antiga onde
divergem):

1. **Identidade visual final "StakeVault"** (2026-08-01, mesma sessão, mais tarde): mockups HTML
   exatos fornecidos pelo usuário — preservados verbatim em
   `docs/design-references/dashboard-mockup.html`, `docs/design-references/splash-animation.html`
   e `docs/design-references/splash-animation-artistic.html` (esta última adicionada depois pelo
   usuário como uma versão mais elaborada, recomendada como alvo de implementação — ver item 17
   do inventário) — mais orientação explícita de paleta e regra semântica de cor (ver abaixo).
   Diferente das capturas do Uphold, este material é **texto/código-fonte exato**, não uma
   captura de tela — os valores hex e a geometria SVG neste documento são citação direta, não
   aproximação visual. Logo extraído desses mockups em quatro variantes SVG standalone:
   `docs/design-references/logo-mark-{dark,light,solid}.svg` e `logo-bars-only.svg` (marca
   simplificada, só as barras, para favicon/loaders/estados vazios — ver seção "Identidade
   visual" abaixo). A imagem raster original de onde essas variantes foram extraídas/aproximadas
   (ver ressalvas de precisão de cor abaixo) está preservada em
   `docs/design-references/logo-concept-source.png` (movida de `D:\UTFPR\TCC\Graficos` em
   2026-08-02) — só para provenance, não usar como asset de produção (as versões vetoriais acima
   são o artefato final).
2. **Layout em painéis e inventário de componentes de base**: capturas de tela do produto
   [Uphold](https://uphold.com/) (dashboard autenticado, compartilhadas pelo usuário na sessão de
   inicialização do harness, 2026-08-01, mais cedo) — **não** a página de marketing pública (que
   não expõe CSS/tokens reais; checada e não ajudou). As capturas não foram salvas como arquivo
   no repositório; este documento é o registro durável do que foi observado nelas — onde a
   camada 1 não cobre um detalhe (ex.: estrutura de grid em painéis), a descrição aqui continua
   sendo aproximação visual das capturas do Uphold, não citação exata.

**Decisões explícitas do usuário**: identidade visual final é **StakeVault** (não mais
placeholder — ver seção "Identidade visual" abaixo); paleta de cores é a do StakeVault (verde
`#3EC46D`), não mais uma réplica do verde do Uphold; layout em painéis continua baseado no
Uphold (não fornecido pelo mockup StakeVault, que é só a composição interna de um painel).

## Modos claro e escuro (RNF02)

O app suporta **os dois modos com toggle** (decisão do usuário) — não é dark-mode-only nem
light-mode-only. As capturas mostram os dois modos completos, com o mesmo verde de destaque
funcionando em ambos (só o fundo/superfície/texto invertem). Implementação: Angular Material
22.x tema M3 (ver seção "Integração com Angular Material" abaixo) com os tokens de cor
definidos como CSS custom properties, alternados por `[data-theme="dark"]`/`[data-theme="light"]`
no elemento raiz (mesmo padrão usado pelos Artifacts desta ferramenta, não coincidência — é o
jeito correto de fazer isso sem duplicar folhas de estilo). Padrão inicial: seguir
`prefers-color-scheme` do sistema operacional, com toggle manual persistido (`localStorage`)
sobrepondo a preferência do SO quando o usuário escolher explicitamente.

## Paleta de cores

Valores exatos do modo escuro (citação direta dos mockups StakeVault); modo claro derivado pela
mesma regra de construção usada no restante do documento (fundo↔texto invertidos, mesmo verde de
marca) — o usuário não forneceu um mockup claro do StakeVault, então o modo claro é a parte
menos certificada desta tabela, revisitar se um mockup claro real aparecer depois.

### Modo escuro

| Token | Valor | Uso |
|---|---|---|
| `--color-background` | `#0B1622` | Fundo geral do app (navy) |
| `--color-surface` | `#16232F` | Cards/painéis sobre o navy |
| `--color-surface-elevated` | `#1D2A36` | Estados hover/ativo sobre superfície (badge "Em aberto") |
| `--color-border` | `#24323F` | Divisores e bordas sutis (linhas do gráfico, separadores de lista) |
| `--color-text-primary` | `#F2F7F5` | Texto principal (off-white) |
| `--color-text-secondary` | `#7A8A93` | Texto secundário/muted (legendas, rótulos de KPI) |
| `--color-brand` | `#3EC46D` | Verde de marca — **só** logo, ícone ativo da nav, link ativo, e valores positivos (ver regra semântica abaixo) |
| `--color-brand-strong` | `#26A65B` | Estado hover/pressed de elementos com `--color-brand` |
| `--color-positive` | `--color-brand` (mesmo verde) | Lucro, variação percentual positiva, badge de aposta "won" |
| `--color-negative` | `#E24B4A` | Prejuízo, variação percentual negativa, badge de aposta "lost", erro/destrutivo |
| `--color-action-neutral` | `#3E8CC4` | **Cor padrão de CTA/ação neutra** (salvar, filtrar, confirmar, navegação) — ver regra semântica abaixo. Derivada por rotação de matiz do `--color-brand` (mesma saturação/luminosidade, matiz azul) para harmonizar com a marca sem ambiguidade semântica; não veio do mockup do usuário, ajustar se um azul específico for preferido. |
| `--color-action-neutral-strong` | `#2E6FA0` | Estado hover/pressed de `--color-action-neutral` |
| `--color-disabled-bg` | `#1D2A36` | Fundo de botão/elemento desabilitado |
| `--color-disabled-text` | `#4C5A64` | Texto de botão/elemento desabilitado |

### Modo claro (derivado, sem mockup StakeVault correspondente)

| Token | Valor | Uso |
|---|---|---|
| `--color-background` | `#F2F5F4` | Fundo geral (mesma família do off-white `#F2F7F5` usado como texto no escuro) |
| `--color-surface` | `#FFFFFF` | Cards/painéis |
| `--color-surface-elevated` | `#E7EEEB` | Estados hover/ativo |
| `--color-border` | `#DCE3E0` | Divisores e bordas sutis |
| `--color-text-primary` | `#0B1622` | Texto principal (mesmo navy do fundo escuro) |
| `--color-text-secondary` | `#5C6B72` | Texto secundário/muted |
| `--color-brand` | `#2FA85C` | Verde de marca, escurecido para contraste em fundo claro |
| `--color-brand-strong` | `#22803F` | Estado hover/pressed |
| `--color-positive` | `--color-brand` | Lucro, variação positiva, badge "won" |
| `--color-negative` | `#C73E3D` | Prejuízo, variação negativa, badge "lost", erro |
| `--color-action-neutral` | `#2E70A0` | CTA/ação neutra, escurecido para contraste em fundo claro |
| `--color-action-neutral-strong` | `#215680` | Estado hover/pressed |
| `--color-disabled-bg` | `#E7EEEB` | Fundo de elemento desabilitado |
| `--color-disabled-text` | `#9AA6A2` | Texto de elemento desabilitado |

### Regra semântica de cor (importante — recomendação explícita do usuário)

Num app de bankroll, verde carrega peso semântico de "lucro" automaticamente aos olhos do
usuário — reaproveitar a mesma cor para ações neutras faz o usuário ler "botão verde = resultado
positivo" por engano. Por isso, a partir desta revisão, as três cores de significado são
**estritamente segregadas**, correção sobre a versão anterior deste documento (que usava
`--color-accent`/verde também para CTAs genéricas):

- **Verde (`--color-brand`/`--color-positive`)**: exclusivamente marca (logo, ícone ativo da
  nav, link ativo) e sinalização de **ganho** (lucro, aposta `won`, variação percentual
  positiva). Nunca usar em um botão de ação neutra.
- **Azul (`--color-action-neutral`)**: cor padrão de **toda CTA/ação que não é inerentemente um
  resultado financeiro** — salvar, filtrar, confirmar cadastro, navegar, editar. É a cor do
  botão primário (item 12 do inventário) por padrão.
- **Vermelho (`--color-negative`)**: exclusivamente **prejuízo** (perda, aposta `lost`, variação
  percentual negativa), erro de validação, e ação destrutiva (excluir, cancelar vínculo).

Consequência prática: o botão de submeter o formulário de registro de aposta (RF04) é **azul**,
não verde — registrar uma aposta não é, em si, um resultado positivo ou negativo.

## Tipografia

- Família: **Inter** — confirmada pelo usuário como uma das opções que combinam com o desenho da
  marca (junto com Satoshi e General Sans, também gratuitas); mantida como escolha desta revisão
  por já estar integrada (`@fontsource/inter` ou Google Fonts) e ser a mais amplamente suportada
  das três. Satoshi/General Sans ficam como alternativas documentadas se uma sessão futura quiser
  um visual mais próximo do lockup StakeVault especificamente — trocar exige só atualizar o
  import e esta nota, não é uma decisão de arquitetura.
  - **Wordmark é exceção**: o lockup "StakeVault" (ver seção "Identidade visual" abaixo) usa peso
    leve (400) em "Stake" e médio (500) em "Vault" dentro da mesma família — não recriar isso com
    duas fontes diferentes, é só variação de peso.
  - **Números tabulares** (`font-variant-numeric: tabular-nums`) em toda exibição de valores
    monetários/percentuais — obrigatório para preço/saldo não "dançarem" horizontalmente ao
    atualizar. Formatação de número/data respeita o locale ativo — o mockup de referência mostra
    o formato `pt-BR` (`R$ 12.480`, `8,4%`, separador de milhar `.` e decimal `,`); `en-US`/`es`
    usam separadores invertidos (`1,234.56`) — ver [[CONVENTIONS]] seção "Internacionalização
    (i18n)". O símbolo de moeda também segue o locale/moeda do usuário, não é sempre `R$`.
- Escala (usar como base, ajustar durante implementação):
  - Display (saldo total, valor grande de input): 40–48px, peso 700. KPI de painel (ex.: "Banca
    atual", ver inventário item 15): 20–24px, peso 500.
  - Título de card/seção ("Watchlist", "Total balance", "Evolução da banca"): 16–18px, peso 600.
  - Corpo (nomes de ativos, linhas de lista, título de aposta no histórico): 14–15px, peso
    500–600.
  - Legenda/muted ("Not set", ticker, rótulo de KPI, descrição de aposta): 12–13px, peso
    400–500.

## Espaçamento, raio e elevação

- **Raio de borda**: cards/painéis grandes `16–20px`; campos de input tipo "card" (Select
  source/destination) `12–14px`; botões e seletores de segmento **totalmente arredondados**
  (pill, `999px`); badges/avatares de ícone **circulares**.
- **Espaçamento interno**: padding generoso dentro de cards (`~24px`); gap entre cards no layout
  de colunas (`~24px`); ritmo vertical entre itens de lista (`~16–20px`).
- **Elevação**: modo escuro não usa sombra — profundidade vem só do contraste entre
  `--color-background` e `--color-surface`. Modo claro usa sombra difusa e sutil sob os cards
  (`0 4px 24px rgba(20, 20, 30, 0.06)`), nunca bordas duras.

## Layout em painéis

Traço estrutural do Uphold que vale a pena nomear separadamente do componente "card" em si
(item 2 do inventário abaixo): as três capturas mostram páginas compostas por **painéis
independentes lado a lado**, não uma página de rolagem única. É a decisão de layout mais visível
do produto — replicar isto é tão importante quanto a paleta de cores.

- **Grid de painéis**: CSS Grid no desktop, colunas de largura definida por página (ex.: painel
  lateral mais estreito, painel central mais largo — mesmas proporções vistas nas capturas, não
  colunas uniformes). Gap entre painéis = `24px` (mesmo token de espaçamento já definido).
- **Rolagem independente por painel**: cada painel rola dentro de si mesmo
  (`overflow-y: auto`, altura máxima = viewport menos o cabeçalho/nav), a página como um todo
  **não** rola. Visível na primeira captura: a barra de rolagem aparece só dentro do painel da
  esquerda (Watchlist/Most Bought/Recently Added), não na janela inteira.
  - **Regra: cada painel tem no máximo a altura da viewport visível (menos cabeçalho) e nunca
    dita a altura de outro painel adjacente** — trate cada `app-panel` como uma região de rolagem
    própria (`overflow-y: auto`), não como um bloco de altura variável que empurra o layout.
- **Painel = unidade de composição de página**, não só decoração dentro de uma página — todo
  fluxo de tela (dashboard, histórico, formulário de aposta, gestão de casas de apostas) é
  montado como um ou mais painéis lado a lado, nunca como formulário solto em página cheia ou
  modal (o próprio "Anything to Anything" do Uphold, formulário de transação, vive dentro de um
  painel — mesmo tratamento que o formulário de registro de aposta (RF04) deve ter aqui).
- **Responsivo (RNF01)** — o grid de painéis não pode simplesmente encolher; a estratégia é
  colapsar colunas:
  - **Desktop** (`≥1024px`): grid multi-coluna completo, conforme decidido por página.
  - **Tablet** (`~600–1024px`): cai para 2 colunas — painel menos crítico da página reflui para
    abaixo dos outros dois.
  - **Mobile** (`<600px`): empilha em coluna única, um painel por seção de largura total. Se uma
    página tiver mais de 2 painéis, considerar um controle segmentado no topo para alternar
    entre eles em vez de forçar rolagem vertical longa (regra de Shneiderman "reduzir a carga de
    memória de curto prazo", ver [[web]]) — decisão final de qual abordagem cabe a cada feature
    de UI, não fixada aqui.
- **Composição sugerida por página** (default razoável, cada feature RF03/04/08/10/11 UI decide
  o número exato de painéis quando for implementada — isto aqui não é obrigatório, é ponto de
  partida):
  - Dashboard (RF10/RF11 UI): 2–3 painéis — análogo direto à tela de trade do Uphold (ex.: filtros/
    navegação de métricas, gráfico + saldo consolidado, breakdown segmentado por esporte/mercado/
    casa). Painéis podem atualizar de forma independente conforme filtros mudam (RN08).
  - Histórico (RF08 UI): 1–2 painéis (filtros + tabela paginada).
  - Casas de apostas (RF03 UI): 1 painel (lista/gestão).
  - Registro manual de aposta (RF04 UI): 1 painel contendo o formulário completo.
- Componente: um container de grid reutilizável (`app-panel-layout`, define colunas/breakpoints
  por página) + o componente de painel em si (`app-panel`, ver item 2 do inventário) — ambos
  standalone, ambos usando os tokens de espaçamento/raio já definidos acima.

## Inventário de componentes (mapeados das capturas)

Cada um vira um componente Angular standalone (`app-*`), estilizado com SCSS por componente
(`:host`) usando os tokens acima e as primitivas de Angular Material — ver
[[CONVENTIONS]] seção "Frontend".

1. **Shell/nav lateral de ícones** — coluna fixa estreita, logo StakeVault no topo (ver seção
   "Identidade visual" abaixo), botões de ícone empilhados (ícone ativo = cor `--color-brand`),
   ícone "mais" no rodapé.
2. **Card/painel base** (`app-panel`) — container `--color-surface`, raio grande, cabeçalho
   opcional (título + botões de ícone circulares no canto), rolagem interna própria. É a unidade
   básica do "Layout em painéis" descrito acima, não só um card decorativo.
3. **Card de banner dispensável** — imagem à direita, título+texto+botão pill à esquerda,
   indicadores de carrossel (dots), ícone de fechar (X) no canto superior direito.
4. **Linha de lista (ativo/menu)** — ícone/avatar circular à esquerda, rótulo primário + legenda
   empilhados, valor + variação percentual coloridos (`--color-positive`/`--color-negative`) OU
   chevron `>` à direita.
5. **Texto de valor + variação** — número em negrito, percentual colorido com seta
   pequena (↑/↓).
6. **Gráfico de linha** — traço na cor `--color-brand`, gradiente suave preenchendo a área abaixo
   até transparente (opacidade baixa, ~0.12), ponto de destaque no último valor. Três linhas de
   grade horizontais finas e sutis (`--color-border`, ~1px) — correção sobre a versão anterior
   deste documento, que descrevia o gráfico do Uphold como sem grid; o mockup StakeVault (mais
   recente e mais específico deste produto) mostra grade sutil, adotada aqui como padrão.
   Biblioteca: **`ngx-echarts`** (wrapper Angular do Apache ECharts) — decisão de 2026-08-02,
   escolhida sobre `ng2-charts`/Chart.js e `ngx-charts` (Swimlane) por dar controle fino
   suficiente para reproduzir o gradiente customizado e o grid sutil acima sem CSS/SVG
   manual. Usado por todos os gráficos de RF10/RF11 (UI), não só o de linha — inclusive
   eventuais breakdowns em barra/pizza dos painéis de dashboard.
7. **Seletor de período (chips)** — linha horizontal de pílulas (1H/1D/1W/1M/1Y); ativa =
   `--color-surface-elevated` + texto de contraste médio; inativa = transparente + texto muted.
8. **Controle segmentado (tabs tipo "Transact/Limit")** — switcher de duas opções em formato
   pílula; segmento ativo ganha fundo `--color-surface-elevated`.
9. **Campo de input tipo card** ("Select source/destination") — caixa arredondada com borda
   sutil, rótulo muted, pequeno traço colorido de destaque acima do campo, área de toque grande.
10. **Display numérico grande** (valor de transação) — número enorme em negrito, rótulo muted
    abaixo ("Enter amount"), ícone auxiliar à direita (ex.: swap/inverter).
11. **Linha de ação com ícone + rótulo + status** ("Repeat transaction", "Take Profit",
    "Trailing Stop") — ícone à esquerda, rótulo + valor muted ("Not set") abaixo, linha/card
    inteiro clicável.
12. **Botão CTA primário (pill full-width)** — preenchido com `--color-action-neutral` por
    padrão (ver "Regra semântica de cor" acima — **não** `--color-brand`/verde, correção sobre a
    versão anterior deste documento) quando habilitado; estado desabilitado =
    `--color-disabled-bg`/`--color-disabled-text`, permanece visível (nunca escondido), só com
    contraste reduzido — ver captura do botão "Preview". Um botão cuja ação é inerentemente
    positiva (ex.: confirmar que uma aposta pendente foi ganha) pode usar `--color-brand`
    conscientemente — é a exceção, não o padrão.
13. **Lista de configurações/menu** ("More") — linhas rótulo + chevron, divisor sutil entre
    linhas, fundo `--color-surface-elevated` sutil no hover/pressed (visto na linha "Security"),
    linha de perfil com avatar circular de iniciais + nome/e-mail, rodapé com links legais e
    versão em texto muted.
14. **Avatar/badge de iniciais** — círculo, fundo muted, iniciais em negrito (ex.: "RM" no
    mockup StakeVault, canto superior direito).
15. **Grade de KPIs/estatísticas** — grid responsivo (`auto-fit`, `minmax(120px, 1fr)`) de
    tiles pequenos dentro de um painel, cada um com rótulo muted (12px) em cima e valor grande
    (20–24px, peso 500) embaixo; valores que são inerentemente positivos/negativos (lucro, ROI)
    usam `--color-positive`/`--color-negative`, valores neutros (banca atual, tamanho de
    unidade) usam `--color-text-primary`. Visto no mockup StakeVault: "Banca atual", "Lucro",
    "ROI", "Unidade".
16. **Badge de resultado de aposta** — pequeno rótulo com fundo tonal e texto na mesma cor
    (ex.: fundo verde escuro + texto verde, não fundo verde sólido + texto branco — mesma
    técnica do badge "+R$ 212" no mockup), mapeado 1:1 ao `status` do domínio (ver
    [[API-CONTRACTS]]): `won` → tom `--color-positive`; `lost` → tom `--color-negative`;
    `pending`/`void` → tom `--color-text-secondary` sobre `--color-surface-elevated` (neutro,
    "Em aberto" no mockup). Usado nas linhas de histórico (RF08) e em qualquer lista de apostas.
17. **Splash/loading animado** — duas referências em `docs/design-references/`, a segunda é a
    recomendada como alvo de implementação:
    - `splash-animation.html` (versão simples): anel via `stroke-dasharray`/`stroke-dashoffset`
      animando até `0` (comprimento do círculo = `2πr`; raio `36` do mark ≈`227` — para formas
      irregulares no futuro, calcular com `path.getTotalLength()` em JS em vez de à mão), raios
      surgindo com a mesma técnica, barras crescendo com `transform: scaleY(0 → 1)` +
      `transform-box: fill-box` + `transform-origin: bottom` (crescimento parte da base, não do
      centro do SVG), nome aparecendo por fade simples.
    - `splash-animation-artistic.html` (versão recomendada, adicionada depois pelo usuário —
      "mais artística... ficaria mais legal para o carregamento", concordo): mesma base técnica,
      mais refinada:
      - Anel de guia pontilhado (`--color-border`-ish, bem sutil) que gira continuamente em
        segundo plano (14s, independente do ciclo principal de 5.4s) — funciona sozinho como o
        "loop discreto" exigido pela regra de produção abaixo para carregamentos acima de ~3s,
        sem precisar de nenhuma animação extra.
      - Um "cometa" (ponto de luz) percorre o mesmo caminho do anel em sincronia com o
        `stroke-dashoffset`, dando a sensação de que é ele quem desenha o anel.
      - Os raios começam girados (`rotate(-40deg)`) e giram até a posição final enquanto se
        desenham — leitura de "girar o dial do cofre até destravar", não só raios aparecendo.
      - Barras crescem com easing overshoot (`cubic-bezier(.2,1.3,.4,1)`, ultrapassa e volta) em
        vez de easing linear — mais "vivo".
      - Ao final da montagem, o ícone dá um pequeno "pop" (`scale` 1→1.05→1) e dois anéis de
        pulso se expandem e desaparecem (efeito de confirmação/"encaixou") — linguagem visual de
        microinteração de sucesso.
      - Nome revelado por **varredura via `<mask>` SVG** (retângulo animado em `translateX`) +
        leve `translateY`/fade, não um fade simples — texto "desliza para dentro" enquanto é
        revelado da esquerda para a direita.
      - **Já implementa `@media (prefers-reduced-motion: reduce)` corretamente** — desliga todas
        as animações e define os valores de estado final diretamente (`stroke-dashoffset: 0`,
        `scaleY(1)`, opacidades finais, `translateX(0)`) em vez de tentar pausar uma animação em
        andamento. Usar este arquivo como referência de implementação do requisito de
        acessibilidade abaixo, não só descrição em prosa.
    - Três regras de produção (recomendação explícita do usuário, valem para qualquer uma das
      duas referências):
      - **Não usar loop infinito em produção** — rodar a sequência uma vez e travar no logo
        formado enquanto o app carrega de verdade; se o carregamento terminar antes da animação,
        deixá-la concluir e só então dar fade — animação cortada no meio lê como bug. Se o
        carregamento passar de ~3s, entra um loop discreto (na versão artística, o giro lento do
        anel de guia já cobre isso de graça).
      - **Respeitar `prefers-reduced-motion`** — ver o bloco `@media` já pronto em
        `splash-animation-artistic.html`.
      - **CSS/SVG puro é suficiente** — poucos KB, anima na GPU; não introduzir Lottie ou outra
        biblioteca de animação só para isto (só compensaria para morphing complexo entre formas,
        que não é o caso aqui).
    - **Atenção na implementação**: o ciclo completo da versão artística dura `5.4s` no arquivo
      de referência — se isso for mais longo que o carregamento real típico do app, considerar
      encurtar a sequência (não é obrigatório rodar os 5.4s inteiros; a regra de produção acima
      já cobre terminar mais cedo se o carregamento acabar antes).

## Integração com Angular Material (M3)

`apps/web` já decidiu Angular Material em [[CONVENTIONS]]. Angular Material 22.x usa o sistema
de tema M3 (`mat.theme()`, Sass), que gera um conjunto completo de tokens (`--mat-sys-*`) a
partir de uma cor semente. Não duplicar um sistema de cor paralelo do zero:

- Gerar o tema M3 a partir de `--color-action-neutral` (`#3E8CC4`/`#2E70A0`) como cor **primária**
  semente — não `--color-brand`/verde. O papel `primary` do M3 é o que o Material usa por padrão
  em botões/controles interativos, e por causa da regra semântica de cor acima, esse papel deve
  mapear para a cor neutra, não para a marca. `--color-brand` (verde) é injetado como cor
  **secondary** ou **tertiary** do tema (usado explicitamente onde a marca/positividade é
  intencional: logo, nav ativa, valores positivos), não como `primary`.
- Mapear `--color-surface`, `--color-background`, `--color-text-primary`/`secondary` para os
  papéis M3 equivalentes (`surface`, `background`, `on-surface`, `on-surface-variant`) via
  overrides do tema, em vez de deixar o Material gerar neutros genéricos — isso é o que garante
  o navy/off-white específicos do StakeVault, não o cinza neutro padrão do M3.
- `--color-positive`/`--color-negative` são tokens **próprios da aplicação**, não papéis nativos
  do M3 (o papel `error` do M3 significa "algo deu errado", não "você perdeu dinheiro" — mesmo
  que a cor seja parecida, o significado é diferente; não reaproveitar `error` para prejuízo,
  ainda que `--color-negative` possa compartilhar o mesmo valor hex que o `error` do tema).
- Tema claro/escuro via `color-scheme` + os dois blocos de tokens acima, trocados no elemento
  raiz — primeira sessão de `feat-001` de `apps/web` implementa e registra em
  `apps/web/progress.md` a abordagem exata usada (media query vs. classe manual vs. as duas).

## Identidade visual — StakeVault

Nome e marca **definidos** (2026-08-01) — não é mais placeholder, substitui a seção anterior
deste documento. "Bankroll" (nome genérico usado antes) não é mais referenciado em lugar nenhum.

### Logo

Anel (o "cofre") com quatro raios diagonais nos cantos, e três barras verticais ascendentes
dentro (o elemento de gráfico/crescimento — é o que carrega o significado da marca). Geometria
exata e as três variantes de cor em `docs/design-references/`:

- `logo-mark-dark.svg` — anel/raios em `--color-brand` (verde), barras em `--color-text-primary`
  (off-white) com opacidade ascendente `0.45 / 0.75 / 1` (a barra mais alta é a mais opaca) — uso
  padrão sobre fundo escuro.
- `logo-mark-light.svg` — anel/raios em navy, barras em tons ascendentes de verde — uso sobre
  fundo claro. Cores aproximadas (o usuário não deu os hex exatos desta variante, só a imagem
  composta) — revisitar com color picker se precisão importar.
- `logo-mark-solid.svg` — fundo verde sólido com raio de borda, anel/raios/barras em navy — para
  app icon/favicon em contexto que precisa de um quadrado preenchido (ex.: ícone de PWA,
  thumbnail). Cores também aproximadas da imagem composta.
- `logo-bars-only.svg` — **só as três barras**, sem o anel, cor única (`--color-brand`). Uso
  explícito recomendado pelo usuário: favicon em tamanho pequeno, loaders, estados vazios — o
  anel completo não lê bem abaixo de ~32px, as barras sozinhas continuam reconhecíveis e servem
  como padrão gráfico reutilizável (ex.: marca d'água sutil num painel sem dados ainda).

### Wordmark

"Stake" + "Vault" na mesma família tipográfica (ver seção Tipografia), duas variações de peso
para criar hierarquia sem depender de cor: "Stake" em peso leve (400), "Vault" em peso médio
(500) e cor `--color-brand`. Funciona em monocromático (ex.: impressão, ícone de app sem cor) —
não recriar a hierarquia com duas fontes diferentes.

Tagline "GESTÃO DE BANCA" (maiúsculas, tracking largo, `--color-text-secondary`, 11px) é
**string de UI comum, não parte fixa do lockup** — passa pelo mecanismo de i18n como qualquer
outro texto (`en-US`: "BANKROLL MANAGEMENT"; `es`: "GESTIÓN DE BANCA"). O nome "StakeVault" em si
**não é traduzido** — nome de marca, mesma convenção usada por produtos reais (nomes próprios não
mudam com o idioma da interface).

### Onde usar cada variante

- Nav lateral (item 1 do inventário): `logo-mark-dark.svg` (ou `light`, conforme o tema ativo) +
  wordmark ao lado, tamanho pequeno (~30px, ver mockup de referência).
- Splash/loading (item 17 do inventário): geometria do `logo-mark-dark.svg`, animada — usar
  `docs/design-references/splash-animation-artistic.html` como alvo (`splash-animation.html` é a
  versão simples, mantida como referência secundária) — ver a descrição técnica no inventário.
- Favicon/app icon: `logo-mark-solid.svg` (contextos que precisam de fundo preenchido) ou
  `logo-bars-only.svg` (contextos que precisam só do símbolo em tamanho pequeno).
- Estados vazios/loaders inline: `logo-bars-only.svg`.

## QA visual e prototipagem: Impeccable, taste-skill e huashu-design — prioritárias (decisão de 2026-08-02, estendida em 2026-09-03)

Três ferramentas de *design guidance para agentes de IA* — [Impeccable](https://github.com/pbakaus/impeccable),
[taste-skill](https://github.com/leonxlnx/taste-skill) e [huashu-design](https://github.com/alchaincyf/huashu-design)
— **prioritárias** em `apps/web`, igual ao Caveman/claude-code-skills (ver [[AGENT-SKILLS]]) —
não uma opção entre outras, o conjunto padrão para qualquer tarefa de frontend. Usadas **só como
auditoria/polish/prototipagem** do que for implementado, nunca como fonte de novas decisões de
design:

- **Este documento (`DESIGN-SYSTEM.md`) continua sendo a única fonte de verdade de design** —
  marca StakeVault, paleta, layout em painéis, tema, tipografia, já fechados. O taste-skill não
  pode gerar um design language paralelo, e o huashu-design não pode usar sua própria "filosofia
  de design"/review em 5 dimensões para *decidir* aparência — ambos duplicariam a fonte de
  verdade. Gerar prototipagem/mockup/slide com o huashu-design é permitido (é o ponto forte da
  ferramenta), desde que a paleta/tipografia/layout do prompt venham deste documento, não do
  default da ferramenta — o resultado nunca é aceito como especificação, só como rascunho
  descartável.
- **`/impeccable init` é seguro e não é a mesma coisa que gerar `DESIGN.md`** — correção de
  2026-09-03 a uma leitura errada da ferramenta em 2026-08-02: `init` só escreve `PRODUCT.md`
  (público, propósito, restrições, voz) e, segundo o próprio `SKILL.md` do Impeccable, *"does
  not invent a visual world and does not write DESIGN.md"* nem oferece criar um durante `init`.
  Quem escreve `DESIGN.md` é `/impeccable document` (extrai do código) ou o fluxo `new-work`
  (workshop interativo) — comandos distintos, nunca acionados por `init`.
  **Mecanismo real para não duplicar a fonte de verdade**: `apps/web/DESIGN.md` é **pré-escrito
  a partir deste documento**, no [formato oficial `DESIGN.md`](https://github.com/google-labs-code/design.md)
  — front-matter YAML com os tokens (`colors`, `typography`, `rounded`, `spacing`, `components`)
  seguido das 8 seções canônicas na ordem (`Overview`, `Colors`, `Typography`, `Layout`,
  `Elevation & Depth`, `Shapes`, `Components`, `Do's and Don'ts`; seções não aplicáveis podem ser
  omitidas). Feito isso, `document`/`new-work` **não sobrescrevem sozinhos**: o próprio skill diz
  *"If a DESIGN.md already exists, do not silently overwrite it. STOP and call AskUserQuestion.
  The choice is refresh, overwrite, or merge"* — a sessão futura escolhe `merge`/recusa
  `overwrite`. `context.mjs` carrega `PRODUCT.md` + `DESIGN.md` uma vez por sessão antes de
  qualquer comando de auditoria, então audit/polish passam a avaliar contra os nossos tokens.
- Uso pretendido: comandos de auditoria (ex.: `/impeccable audit`, `/impeccable polish`) rodados
  contra componentes já implementados, comparando o resultado com o que este documento descreve
  (detectar "cara de IA genérica" — gradiente roxo-azul, cards aninhados, fontes padrão — que
  não tem nada a ver com a identidade StakeVault). O taste-skill entra pelo mesmo motivo:
  refinar layout/tipografia/animação de componentes já implementados, não desenhar do zero.
  huashu-design entra numa etapa diferente das outras duas — **antes** da implementação, não
  depois: gerar um protótipo HTML clicável ou mockup de uma tela nova a partir da paleta/tema
  deste documento, para servir de referência visual rápida ao implementar o componente Angular
  de verdade — nunca é o artefato final, nunca é commitado em `apps/web/src`.
  Instalação: `npx impeccable install` / `npx skills add https://github.com/leonxlnx/taste-skill`
  / `npx skills add https://github.com/alchaincyf/huashu-design`.
- **Ainda não instaladas** — `apps/web` não tem `package.json` ainda (`feat-001` não iniciado).
  Instalação das três prevista para `feat-001`, junto com Angular/Playwright — ver
  `apps/web/CLAUDE.md` e `apps/web/feature_list.json`.
- **Playwright** (Microsoft) é diferente das três acima — teste E2E **funcional**, não QA visual.
  Já estava planejado antes desta decisão (ver [[TESTING]]).

## Ver também

- [[CONVENTIONS]] — arquitetura Angular que este documento estende.
- [[web]] — RF/RNF cobertos, regras de Shneiderman para o formulário de apostas.
- [[TESTING]] — Playwright deve cobrir os fluxos críticos nos dois temas (claro/escuro), não só
  no padrão.
- [[DECISIONS-LOG]] — decisão de 2026-08-02 sobre Impeccable/taste-skill como QA visual, não
  fonte de design, estendida em 2026-09-03 para incluir huashu-design sob a mesma restrição.
