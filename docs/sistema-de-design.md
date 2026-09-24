---
tags: [conventions, design, frontend]
---

# Design System — apps/web

Convenção normativa de tema e componentes visuais para [[web]], no mesmo espírito de
[[convencoes]] (fecha uma lacuna que o TCC 1 não especificava — ele cobre requisitos e
modelagem de dados, não identidade visual). Ver [[convencoes]] seção "Frontend" para a
arquitetura Angular (standalone, Signals, Reactive Forms, Angular Material) que este documento
assume e estende.

> **i18n**: todo texto usado nos componentes deste documento ("Watchlist", "Banca atual",
> "Not set", "Em aberto" etc.) é **referência visual das capturas/mockups, não copy final da
> aplicação** — a implementação real passa cada string por `@jsverse/transloco` nos três locales
> sempre mantidos (`pt-BR`/`en-US`/`es`), ver [[convencoes]] seção "Internacionalização (i18n)".
> Nenhum componente do inventário abaixo tem texto hardcoded — isso vale inclusive para a
> tagline do logo (ver seção "Identidade visual"), que não é fixa apesar de estar num mockup de
> marca.

## Fonte

Duas camadas de referência, nesta ordem de autoridade (a mais recente refina a mais antiga onde
divergem):

1. **Identidade visual final "StakeVault"** (2026-08-01, mesma sessão, mais tarde): mockups HTML
   exatos fornecidos pelo usuário, mais orientação explícita de paleta e regra semântica de cor
   (ver abaixo). Diferente das capturas do Uphold, este material era **texto/código-fonte exato**,
   não uma captura de tela — os valores hex e a geometria SVG citados a partir dele eram citação
   direta, não aproximação visual.
2. **Reformulação de marca "StakeVault" → "Arka"** (`epic-032`, 2026-09-22/23): usuário forneceu
   identidade visual nova completa, substituindo o material do item anterior — refina/supera a
   camada 1 onde divergirem, mesmo critério de ordem de autoridade já usado entre as camadas 1 e
   2 originais. Assets atuais, todos em `docs/design-references/`: `arka-icon.svg`/
   `arka-app-icon-512.png` (favicon/app icon), `arka-mark-dark.svg`/`arka-mark-light.svg`
   (renomeações/relabel dos antigos `logo-mark-dark.svg`/`logo-mark-light.svg` — mesma geometria/
   cor, só o nome do arquivo mudou), `arka-bars-only.svg` (idem, ex-`logo-bars-only.svg`),
   `arka-logo-horizontal-dark.svg`/`arka-logo-horizontal-light.svg` (lockup horizontal novo,
   substitui o wordmark composto manualmente na seção "Wordmark" abaixo), `arka-splash.html`
   (substitui os dois arquivos de splash antigos — ver item 17 do inventário),
   `arka-tokens.css` (paleta/tokens de referência), `arka-bot-avatar.svg`/
   `arka-bot-telegram-512.png` (avatar do bot Telegram — relevante para `telegram-integration`,
   fora do escopo deste documento). **Removidos** (não existe mais equivalente direto):
   `dashboard-mockup.html`, `splash-animation.html`, `splash-animation-artistic.html`,
   `logo-mark-solid.svg`, `logo-concept-source.png` — o app icon/favicon com fundo preenchido
   passa a ser `arka-app-icon-512.png`/`arka-icon.svg` em vez de uma variante `-solid` do mark.
   **Paleta**: valores de `arka-tokens.css` adotados abaixo onde coincidem ou refinam a tabela já
   existente, com duas exceções deliberadas, ambas mantidas (ver notas nas tabelas): o texto
   secundário do modo escuro continua no valor já corrigido por acessibilidade (`feat-011.5`,
   não o valor pré-correção que `arka-tokens.css` traz), e a cor de CTA/ação neutra continua
   **azul** (`--color-action-neutral`), não o verde que `arka-tokens.css` usa em
   `.arka-btn-primary` — decisão do usuário reconfirmada nesta sessão: a regra semântica de cor
   abaixo (verde exclusivo de marca/lucro) continua valendo, `arka-tokens.css` é tratado como
   referência de paleta/marca, não como especificação literal de qual cor vai em qual botão.
2. **Layout em painéis e inventário de componentes de base**: capturas de tela do produto
   [Uphold](https://uphold.com/) (dashboard autenticado, compartilhadas pelo usuário na sessão de
   inicialização do harness, 2026-08-01, mais cedo) — **não** a página de marketing pública (que
   não expõe CSS/tokens reais; checada e não ajudou). As capturas não foram salvas como arquivo
   no repositório; este documento é o registro durável do que foi observado nelas — onde a
   camada 1 não cobre um detalhe (ex.: estrutura de grid em painéis), a descrição aqui continua
   sendo aproximação visual das capturas do Uphold, não citação exata.

**Decisões explícitas do usuário**: identidade visual final é **Arka** (renomeada de "StakeVault"
em 2026-09-22/23, ver item 2 de "Fonte" acima — não mais placeholder, ver seção "Identidade
visual" abaixo); paleta de cores é a da marca (verde `#3EC46D`), não mais uma réplica do verde do
Uphold; layout em painéis continua baseado no Uphold (não fornecido pelos mockups de marca, que
são só a composição interna de um painel).

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

Valores exatos do modo escuro (citação direta dos mockups originais da marca, reconfirmados por
`arka-tokens.css` no rebranding de 2026-09-23 — mesmo verde `#3EC46D`); modo claro derivado pela
mesma regra de construção usada no restante do documento (fundo↔texto invertidos, mesmo verde de
marca), com o verde de modo claro atualizado para `#26A65B` (valor de `arka-tokens.css`) — o
usuário não forneceu um mockup claro original, então o modo claro continua a parte menos
certificada desta tabela, revisitar se um mockup claro real aparecer depois.

### Modo escuro

| Token | Valor | Uso |
|---|---|---|
| `--color-background` | `#0B1622` | Fundo geral do app (navy) |
| `--color-surface` | `#16232F` | Cards/painéis sobre o navy |
| `--color-surface-elevated` | `#1D2A36` | Estados hover/ativo sobre superfície (badge "Em aberto") |
| `--color-border` | `#24323F` | Divisores e bordas sutis (linhas do gráfico, separadores de lista) |
| `--color-text-primary` | `#F2F7F5` | Texto principal (off-white) |
| `--color-text-secondary` | `#8B99A2` | Texto secundário/muted (legendas, rótulos de KPI) — ver nota de contraste abaixo. **`arka-tokens.css` (2026-09-23) traz `#7A8A93` para este papel — não adotado**: é o valor pré-correção de acessibilidade descrito na nota abaixo (`4.47:1`, falha WCAG AA), tratado como desatualizado em vez de reabrir o achado já corrigido |
| `--color-brand` | `#3EC46D` | Verde de marca — **só** logo, ícone ativo da nav, link ativo, e valores positivos (ver regra semântica abaixo) |
| `--color-brand-strong` | `#26A65B` | Estado hover/pressed de elementos com `--color-brand` |
| `--color-positive` | `--color-brand` (mesmo verde) | Lucro, variação percentual positiva, badge de aposta "won" |
| `--color-negative` | `#E24B4A` | Prejuízo, variação percentual negativa, badge de aposta "lost", erro/destrutivo |
| `--color-action-neutral` | `#3E8CC4` | **Cor padrão de CTA/ação neutra** (salvar, filtrar, confirmar, navegação) — ver regra semântica abaixo. Derivada por rotação de matiz do `--color-brand` (mesma saturação/luminosidade, matiz azul) para harmonizar com a marca sem ambiguidade semântica; não veio do mockup do usuário, ajustar se um azul específico for preferido. |
| `--color-action-neutral-strong` | `#2E6FA0` | Estado hover/pressed de `--color-action-neutral` |
| `--color-disabled-bg` | `#1D2A36` | Fundo de botão/elemento desabilitado |
| `--color-disabled-text` | `#4C5A64` | Texto de botão/elemento desabilitado |

> **Achado de QA visual, corrigido (`apps/web feat-002` → `feat-011.5`, 2026-09-09)**: `npx
> impeccable detect` contra a nav real (`--color-text-secondary` sobre `--color-surface` no modo
> escuro, usado nos links inativos da nav) mediu **4.47:1**, `0.03` abaixo do mínimo WCAG AA de
> `4.5:1` pra texto de corpo — primeiro achado concreto de contraste contra o valor `#7A8A93`
> (verbatim do mockup escuro do usuário). Não corrigido no `feat-002` (valor exato citado do
> mockup, não algo que uma feature de UI isolada devesse ajustar por conta própria — mesmo
> racional do bullet de `--color-action-neutral` acima), sinalizado pra "decisão explícita quando
> outra feature tocar este token de novo". `feat-011` tocou o token amplamente (login, badges,
> cards) e o Impeccable achou o mesmo problema de novo (login) — pergunta feita ao usuário nesse
> momento, decisão: **corrigir**. Novo valor `#8B99A2` (mesmo tom cinza-azulado, só um pouco mais
> claro) mede ~5:1 contra `--color-surface` e `--color-surface-elevated`, resolvendo AA nos dois
> fundos escuros usados pelo token. `--color-text-secondary` do modo claro (`#5C6B72`) já passava
> (5.5:1/4.69:1), não precisou de ajuste.

### Modo claro (derivado, sem mockup original correspondente)

| Token | Valor | Uso |
|---|---|---|
| `--color-background` | `#F2F5F4` | Fundo geral (mesma família do off-white `#F2F7F5` usado como texto no escuro) |
| `--color-surface` | `#FFFFFF` | Cards/painéis |
| `--color-surface-elevated` | `#E7EEEB` | Estados hover/ativo |
| `--color-border` | `#DCE3E0` | Divisores e bordas sutis |
| `--color-text-primary` | `#0B1622` | Texto principal (mesmo navy do fundo escuro) |
| `--color-text-secondary` | `#5A6B75` | Texto secundário/muted (valor de `arka-tokens.css`, 2026-09-23 — próximo do anterior `#5C6B72`, já passava WCAG AA) |
| `--color-brand` | `#26A65B` | Verde de marca, escurecido para contraste em fundo claro (valor de `arka-tokens.css`, 2026-09-23 — antes `#2FA85C`) |
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
  um visual mais próximo do lockup Arka especificamente — trocar exige só atualizar o
  import e esta nota, não é uma decisão de arquitetura.
  - **Wordmark**: desde o rebranding de 2026-09-23, o lockup é o SVG pronto
    `arka-logo-horizontal-{dark,light}.svg` (ver seção "Identidade visual" abaixo), não mais
    construído com duas variações de peso de "Stake"/"Vault" na mesma família — não recriar
    tipograficamente o nome, usar o SVG do lockup.
  - **Números tabulares** (`font-variant-numeric: tabular-nums`) em toda exibição de valores
    monetários/percentuais — obrigatório para preço/saldo não "dançarem" horizontalmente ao
    atualizar. Formatação de número/data respeita o locale ativo — o mockup de referência mostra
    o formato `pt-BR` (`R$ 12.480`, `8,4%`, separador de milhar `.` e decimal `,`); `en-US`/`es`
    usam separadores invertidos (`1,234.56`) — ver [[convencoes]] seção "Internacionalização
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
  - **"Menos cabeçalho" é um valor derivado de layout flex, nunca um pixel fixo chutado por
    página** (achado real, `apps/web` `feat-006`, 2026-09-09, já sinalizado como risco em
    `session-handoff.md` desde `feat-002.2`): toda página (`dashboard`/`history`/
    `betting-houses`/`users`/`catalogs`/`register-bet`) fixava `height: calc(100vh - 64px)` no
    próprio `:host`, chutando a altura da nav. `app-language-selector`/`app-theme-toggle` nunca
    tiveram CSS de posicionamento (nenhum arquivo `.scss` deles existia) e ficavam empilhados em
    fluxo normal *acima* da nav, e a própria nav quebra linha (`flex-wrap: wrap`) conforme mais
    links são adicionados — o "cabeçalho" real sempre foi maior que 64px, só nunca grande o
    suficiente pra estourar visivelmente até o dashboard real (`feat-006`) ter conteúdo alto o
    bastante pra expor via Playwright (`e2e/panel-layout.spec.ts`, que já falhava silenciosamente
    em `develop` antes desta feature - confirmado rodando a suíte contra o HEAD anterior num
    worktree separado). Corrigido na casca compartilhada (`app.html`/`app.scss`, não por página):
    `.app-shell` vira `display:flex;flex-direction:column;height:100%`, o cabeçalho (toolbar de
    idioma/tema + nav + banner) ocupa altura natural (`auto`), e `.app-shell__content` recebe
    `flex:1 1 auto;min-height:0;overflow:hidden` — cada página troca `calc(100vh - 64px)` por
    `height: 100%` e herda o espaço restante, sem precisar saber o pixel exato de nada acima
    dela. Qualquer página nova segue esse padrão (`height: 100%` no `:host`, nunca `calc(100vh -
    Npx)`).
- **Formulário field+botão dentro de painel: nunca `flex-direction: row` sem uma largura mínima
  garantida ao campo** (achado real, `apps/web` `feat-024`, 2026-09-16): `shared/catalog-manager`
  (`.catalog-manager__form`) tinha campo `Nome` (`mat-form-field` em `flex: 1`) e o botão
  "Adicionar" lado a lado na mesma linha — sem `min-width` no campo nem largura mínima garantida
  no painel, o campo era espremido a poucos caracteres em viewports estreitos (320px), chegando a
  cortar o próprio label. Corrigido para `flex-direction: column` (botão em linha própria abaixo
  do campo), mesmo padrão já usado por `shared/team-manager` — agora convenção para qualquer
  formulário campo+botão dentro de um painel estreito: layout em coluna, não em linha. Mesma
  feature também corrigiu `:host` sem padding lateral (`padding: 16px 0` → `24px` +
  `box-sizing: border-box`) em `catalog-manager`/`team-manager` — sem essa padding própria do
  componente, o card colava no menu lateral; testar isso via bounding-box (gap até a nav) é frágil
  porque ancestrais (`app-panel`, chrome do Material) já geram gap suficiente pra mascarar a
  ausência, então a asserção correta é ler `getComputedStyle(host).paddingLeft` diretamente, não
  inferir pela posição do campo (achado do Test Suite Auditor, mesma feature).
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
- **Linha/grid com várias colunas (ex.: "rótulo | valor A | valor B | delta") precisa se
  auto-rotular ao colapsar pra 1 coluna em mobile, não só empilhar os valores nus** (achado real
  de QA visual, `apps/web feat-037.6`, tela de comparativo de períodos): o cabeçalho de coluna
  (que dá contexto aos valores em desktop) normalmente fica `display: none` abaixo de 600px por
  não caber mais — sem substituto, o usuário via 2-3 números soltos empilhados sem saber qual
  período/coluna cada um representava. Mecanismo reaproveitável: o componente da linha recebe os
  rótulos de coluna já traduzidos como inputs (não hardcoda texto na regra CSS), grava cada um
  como `[attr.data-mobile-label]` no elemento de valor correspondente, e o CSS só abaixo do
  breakpoint mobile injeta `content: attr(data-mobile-label) ': '` via `::before` — o rótulo
  correto (no idioma ativo) aparece só na largura onde o cabeçalho compartilhado desaparece, sem
  duplicar informação em desktop. Ver `shared/comparison-metric-row` (`.ts`/`.html`/`.scss`) como
  referência de implementação pra qualquer tabela/linha futura com o mesmo formato.

## Inventário de componentes (mapeados das capturas)

Cada um vira um componente Angular standalone (`app-*`), estilizado com SCSS por componente
(`:host`) usando os tokens acima e as primitivas de Angular Material — ver
[[convencoes]] seção "Frontend".

1. **Shell/nav lateral de ícones** — coluna fixa estreita, logo Arka no topo (ver seção
   "Identidade visual" abaixo), botões de ícone empilhados (ícone ativo = cor `--color-brand`),
   ícone "mais" no rodapé.

   > **Implementado em `web feat-018`** (2026-09-11) — divergência real corrigida: da `feat-002`
   > até aqui a implementação era uma nav horizontal no topo, nunca a nav lateral que este item
   > sempre especificou. `app-side-nav` (substitui `app-nav`): colapsável (ícone+texto expandido
   > / só ícone retraído, alternado manualmente, estado persistido como `Theme`/`Language`),
   > logo+wordmark no topo (`logo-mark-{tema}.svg`, só o mark quando retraído), ícone ativo em
   > `--color-brand` conforme especificado. Sem o ícone "mais" no rodapé do mockup original — o
   > rodapé tem conteúdo real (idioma/tema/sair) em vez de um menu "more" genérico, decisão
   > tomada no plan review por já ter conteúdo suficiente sem precisar de overflow. **Achado
   > real de QA** (screenshots reais, não só leitura de código): a coluna expandida (232px) comia
   > quase a tela inteira abaixo de ~600px, quebrando a regra "mobile = coluna única" (RNF01)
   > que o resto do app já seguia — corrigido com default retraído abaixo desse breakpoint quando
   > o usuário não escolheu explicitamente (mesmo padrão de `Theme` seguir `prefers-color-scheme`
   > até uma escolha explícita). O seletor de idioma some do rodapé quando retraído (não cabe nos
   > 72px da coluna) — usuário expande a nav pra trocar de idioma.
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
   deste documento, que descrevia o gráfico do Uphold como sem grid; o mockup original da marca (mais
   recente e mais específico deste produto) mostra grade sutil, adotada aqui como padrão.
   Biblioteca: **`ngx-echarts`** (wrapper Angular do Apache ECharts) — decisão de 2026-08-02,
   escolhida sobre `ng2-charts`/Chart.js e `ngx-charts` (Swimlane) por dar controle fino
   suficiente para reproduzir o gradiente customizado e o grid sutil acima sem CSS/SVG
   manual. Usado por todos os gráficos de RF10/RF11 (UI), não só o de linha — inclusive
   eventuais breakdowns em barra/pizza dos painéis de dashboard.
   **Todo gráfico tem título, legenda e botão "?"** (`apps/web feat-040`, pedido do usuário
   2026-09-24): o canvas fica dentro de `shared/chart-frame` — `h3` com o título, legenda HTML
   (swatch por token CSS, segue o tema; nunca a legenda nativa do ECharts, para haver um só
   mecanismo) e um botão `?` (`aria-expanded`/`aria-controls`) que mostra a explicação inline, em
   vez de tooltip (funciona em toque e teclado). Textos em `charts.<gráfico>.{title,help,legend}`
   nos 3 locales, derivados de [[estatisticas]]. Grade de mini-gráficos (drawdown mensal) usa um
   frame só em volta da grade; cada mini mantém o título do mês. Gráfico novo entra já dentro do
   frame.
   **Rótulo de eixo em `--color-text-secondary`, grade em `--color-border`** (`apps/web feat-045`,
   2026-09-24): os builders de `core/chart-theme.ts` recebem as duas cores separadas. Rótulo na cor
   da grade dava 1,30:1 (claro) / 1,22:1 (escuro), abaixo do mínimo WCAG de 4,5:1;
   `--color-text-secondary` dá 5,52:1 / 5,45:1. A grade continua sutil de propósito — só texto
   precisa de contraste de leitura.
   **Data diária com ano quando a série passa de 1 ano** (`apps/web feat-048`, 2026-09-24):
   `formatDay(value, locale, withYear)` + `spansMoreThanOneYear(primeiro, último)` em
   `core/date-format.ts`. Até 1 ano o rótulo fica compacto (dia + mês); acima disso eixo e
   tooltip mostram o ano — o tooltip `trigger: 'axis'` reaproveita a categoria do eixo, separar
   os dois exigiria `tooltip.formatter` próprio. O tooltip do ECharts é HTML (não canvas), então
   dá para verificá-lo em E2E com `hover()` no gráfico.
   **Tooltip no tema ativo** (`apps/web feat-052`, 2026-09-24): `themedTooltip()` em
   `core/chart-theme.ts`, espalhado nos 2 builders — fundo `--color-surface-elevated`, borda
   `--color-border`, texto `--color-text-primary` (15,47:1 claro / 13,50:1 escuro). Sem isso o
   ECharts usa caixa branca fixa, fora da paleta no tema escuro. Em E2E, a caixa raiz do tooltip é
   a `div[style*="z-index: 9999999"]` dentro do gráfico (as `div` internas são transparentes).
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
    mockup original da marca, canto superior direito). Primeira implementação real: `feat-011.4`,
    coluna Nome da tela de usuários do tenant (`users.ts`/`.html`, método `initials()` — primeiro
    + último nome, maiúsculo, no máximo 2 letras).
15. **Grade de KPIs/estatísticas** — grid responsivo (`auto-fit`, `minmax(120px, 1fr)`) de
    tiles pequenos dentro de um painel, cada um com rótulo muted (12px) em cima e valor grande
    (20–24px, peso 500) embaixo; valores que são inerentemente positivos/negativos (lucro, ROI)
    usam `--color-positive`/`--color-negative`, valores neutros (banca atual, tamanho de
    unidade) usam `--color-text-primary`. Visto no mockup original da marca: "Banca atual", "Lucro",
    "ROI", "Unidade".
16. **Badge de resultado de aposta** — pequeno rótulo com fundo tonal e texto na mesma cor
    (ex.: fundo verde escuro + texto verde, não fundo verde sólido + texto branco — mesma
    técnica do badge "+R$ 212" no mockup), mapeado 1:1 ao `status` do domínio (ver
    [[contratos-de-api]]): `won` → tom `--color-positive`; `lost` → tom `--color-negative`;
    `pending`/`void` → tom `--color-text-secondary` sobre `--color-surface-elevated` (neutro,
    "Em aberto" no mockup). Usado nas linhas de histórico (RF08) e em qualquer lista de apostas.
17. **Splash/loading animado** — referência única `docs/design-references/arka-splash.html`
    (2026-09-23, substitui as duas referências antigas `splash-animation.html`/
    `splash-animation-artistic.html`, unificadas num só arquivo com a técnica mais elaborada da
    versão artística e ciclo mais curto — `2.1s`, não mais `5.4s`, já resolvendo a ressalva que a
    versão anterior deste documento registrava sobre o ciclo artístico ser mais longo que o
    carregamento típico do app):
      - Anel de guia pontilhado (`--color-border`-ish, bem sutil) que gira continuamente em
        segundo plano (`14s`, independente do ciclo principal de `2.1s`) — funciona sozinho como o
        "loop discreto" exigido pela regra de produção abaixo para carregamentos acima de ~3s,
        sem precisar de nenhuma animação extra.
      - Um "cometa" (ponto de luz) percorre o mesmo caminho do anel em sincronia com o
        `stroke-dashoffset`, dando a sensação de que é ele quem desenha o anel.
      - Os raios giram até a posição final enquanto se desenham (`spin`/`dialin`) — leitura de
        "girar o dial do cofre até destravar", não só raios aparecendo.
      - Barras/raios crescem com easing overshoot (`cubic-bezier(.2,1.3,.4,1)`, ultrapassa e
        volta) em vez de easing linear — mais "vivo".
      - Ao final da montagem, um efeito de pulso/ondulação (`ripple`) se expande e desaparece
        (confirmação/"encaixou") — linguagem visual de microinteração de sucesso.
      - Nome revelado por **varredura via `<mask>` SVG** (`#arka-mask`), não um fade simples —
        texto "desliza para dentro" enquanto é revelado.
      - **Já implementa `@media (prefers-reduced-motion: reduce)` corretamente** — desliga todas
        as animações e define os valores de estado final diretamente (`stroke-dashoffset: 0`,
        opacidades/posições finais) em vez de tentar pausar uma animação em andamento. Usar este
        arquivo como referência de implementação do requisito de acessibilidade abaixo, não só
        descrição em prosa.
    - Três regras de produção (recomendação explícita do usuário, seguidas por `arka-splash.html`):
      - **Não usar loop infinito em produção** — rodar a sequência uma vez e travar no logo
        formado enquanto o app carrega de verdade; se o carregamento terminar antes da animação,
        deixá-la concluir e só então dar fade — animação cortada no meio lê como bug. Se o
        carregamento passar de ~3s, entra um loop discreto (o giro lento do anel de guia já cobre
        isso de graça — único elemento com `animation-iteration-count: infinite` no arquivo).
      - **Respeitar `prefers-reduced-motion`** — ver o bloco `@media` já pronto em
        `arka-splash.html`.
      - **CSS/SVG puro é suficiente** — poucos KB, anima na GPU; não introduzir Lottie ou outra
        biblioteca de animação só para isto (só compensaria para morphing complexo entre formas,
        que não é o caso aqui).
    - **Uso em produção (`apps/web feat-044`, 2026-09-24, decisão do usuário)**: não existe
      mais splash de boot — o login abre instantâneo. A montagem do logo é o **indicador de
      carregamento do app inteiro** (`core/loading-overlay`, o app não tem spinner em lugar
      nenhum): aparece sobre o app todo (sidebar incluída), com fundo translúcido
      (`color-mix` de `--color-background`) + `backdrop-filter: blur`, sempre que uma chamada a
      `/api/` passa de 250ms (chamada rápida não pisca; `/i18n/*.json` não conta). Uma vez
      visível, a sequência de 2.1s termina antes do fade de 400ms (regra acima). Cores por
      token (`--color-brand`/`--color-text-primary`/`--color-border`), não os hex fixos da
      referência, para funcionar nos 2 temas. `z-index: 1100` (acima do `.cdk-overlay-container`
      do Material, 1000) e `inert` no `.app-shell` enquanto visível — bloqueia ponteiro e teclado.
      Estado/tempo em `core/loading.ts` (`Loading`), contagem via `core/loading-interceptor.ts`.
      **Quem decide mostrar o overlay é o template do `App`** (`@if (loading.visible())` em
      `app.html`, `apps/web feat-054`), não o próprio `LoadingOverlay`: o Angular atualiza o
      template do `App` (onde também fica o `[inert]`), depois as views das rotas, e só por
      último os componentes filhos. Com o `@if` dentro do componente filho, um erro de render em
      qualquer tela abortava o ciclo antes de o overlay sumir e o app ficava preso atrás dele.
      Não mover o `@if` de volta para dentro do componente (`app.spec.ts` cobre o caso).
    - **Tela já carregada não repete o loading (`apps/web feat-049`, 2026-09-24)**: GET a
      `/api/` fica em cache em memória (`core/http-cache.ts` + `core/http-cache-interceptor.ts`,
      antes do interceptor de loading na cadeia) — voltar a uma tela cujos dados já vieram não
      faz requisição, então não há overlay. Chave: URL com query params + `Accept-Language`
      (filtro novo = chave nova = requisição nova, RN08 preservada). Só resposta 2xx entra.
      Qualquer requisição não-GET a `/api/` (inclui login) e `Auth.logout` limpam tudo — limpa
      ao enviar e de novo na resposta/erro via `tap`, antes de o componente receber (não
      `finalize`, que roda depois do `next`); GET que estava em voo durante a limpeza não grava
      (contador de geração). TTL 5 min; nos 10s seguintes a uma limpeza nada é gravado, para não
      fixar estatística ainda atrasada pela consistência eventual (`stats-service` via
      RabbitMQ). Corpo servido via `structuredClone` (mutação no componente não altera o cache).
      Limite aceito: aposta registrada pelo Telegram ou em outra aba só aparece no web depois do
      TTL ou de uma mutação feita no próprio web.

## Integração com Angular Material (M3)

`apps/web` já decidiu Angular Material em [[convencoes]]. Angular Material 22.x usa o sistema
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
  o navy/off-white específicos do Arka, não o cinza neutro padrão do M3.
- `--color-positive`/`--color-negative` são tokens **próprios da aplicação**, não papéis nativos
  do M3 (o papel `error` do M3 significa "algo deu errado", não "você perdeu dinheiro" — mesmo
  que a cor seja parecida, o significado é diferente; não reaproveitar `error` para prejuízo,
  ainda que `--color-negative` possa compartilhar o mesmo valor hex que o `error` do tema).
- Tema claro/escuro via `color-scheme` + os dois blocos de tokens acima, trocados no elemento
  raiz — primeira sessão de `feat-001` de `apps/web` implementa e registra em
  `apps/web/progress.md` a abordagem exata usada (media query vs. classe manual vs. as duas).

**Implementação real (`feat-001.2`, 2026-09-09)**: `mat.theme()` só aceita mapas de paleta M3
completos (tons 0–100 + `neutral`/`neutral-variant`/`secondary`/`error`) em `primary`/`tertiary`,
não uma cor hex solta — não existe função Sass pública pra gerar isso a partir de uma cor
qualquer. Gerado via o schematic real do CLI:
`ng generate @angular/material:m3-theme --primary-color "#3E8CC4" --tertiary-color "#3EC46D"`
(grava `src/theme-colors.scss`, tons reais derivados do algoritmo M3 a partir das duas cores
Arka — não uma das paletas nomeadas embutidas do Material, que divergiriam da marca).
Overrides de `surface`/`background`/`on-surface`/`on-surface-variant` (`src/styles/_tokens.scss`)
apontam pros custom properties `--color-*`, não valores fixos — os dois blocos de tokens (claro
em `:root`, escuro em `:root[data-theme='dark']`) cobrem tanto o app quanto o Material ao mesmo
tempo. Troca de tema: **media query + classe manual, as duas** — `@media
(prefers-color-scheme: dark)` decide o default enquanto o usuário não escolher explicitamente;
uma escolha explícita (serviço `Theme`, `signal` + `localStorage`) grava `data-theme="dark"`/
`"light"` em `<html>`, que tem prioridade sobre a media query (`:root:not([data-theme='light'])`
na regra da media query evita que ela vença depois de uma escolha explícita pra "light").

**Correção real (`feat-011.1`, 2026-09-09)**: o paragrafo acima ("os dois blocos de tokens cobrem
tanto o app quanto o Material ao mesmo tempo") estava **errado** — só os 4 aliases genéricos
`--mat-sys-surface`/`background`/`on-surface`/`on-surface-variant` são de fato sobrescritos por
`tokens.scss`. `mat.theme()` gera centenas de outros tokens `--mat-*`/`--mdc-*` **específicos por
componente** (ex.: o painel de overlay de um `mat-select`, `--mat-select-panel-background-color`
e equivalentes) a partir da paleta M3 real, calculados **uma única vez**, na chamada de
`mat.theme()` em `html { ... }` com `theme-type: light` — nunca existiu uma segunda chamada pro
modo escuro, então qualquer token que o Material lê diretamente (não via os 4 aliases) ficava
preso no valor claro mesmo com `data-theme="dark"` ativo. Sintoma real reportado pelo usuário:
seletor de idioma (`mat-select`) com painel de opções branco e texto quase branco no tema escuro
- ilegível. Corrigido chamando `mat.theme()` **de novo**, com `theme-type: dark`, sob os mesmos
dois seletores que `tokens.dark-tokens` já usa (`:root[data-theme='dark']` e `@media
(prefers-color-scheme: dark) { :root:not([data-theme='light']) }`) — é o padrão oficial do
Angular Material pra múltiplos temas (escopar `mat.theme()` a um seletor re-gera todos os tokens
M3 pra esse escopo). Resultado: cada `mat-select`/`mat-menu`/`mat-dialog`/etc. do app inteiro
passou a ter overlay corretamente escuro no tema escuro, não só o componente que expôs o bug -
`src/styles.scss` tem o código real, comentado com o racional. Ao adicionar qualquer override de
tema novo no futuro, não assumir que os 4 aliases de `tokens.scss` bastam - overlays/paineis do
Material especificamente merecem teste visual real no tema escuro, não só leitura do código.

**Fonte de ícone (`feat-032`, 2026-09-16)**: `mat-icon` usa **Material Icons** clássico como
padrão do app (`<link>` em `index.html`), mas o `app-side-nav` usa `fontSet` seletivo em cada
`<mat-icon>` para renderizar via **Material Symbols Outlined** (`<link>` adicional, mais a classe
global `.material-symbols-outlined` em `styles.scss` com `font-variation-settings`) — o Symbols
tem centralização óptica melhor pra glifos diagonais (`trending_up`/`trending_down`,
`sports_score`) que apareciam desalinhados na nav colapsada com a fonte clássica. Não é uma troca
global: o ícone `telegram` (link do nav) **não existe** no Material Symbols (Google não inclui
ícones de marca/social nesse conjunto, só no Material Icons clássico) — confirmado contra o
`codepoints` oficial do `google/material-design-icons` no GitHub — então esse item específico
mantém o `fontSet` padrão (`app-side-nav.html`, binding condicional por `link.icon === 'telegram'`).
Outras telas (KPI cards de `overview`/`dashboard`/`period-report`/`search-statistics`, página
`telegram-link`) continuam no Material Icons clássico sem mudança. Ao adicionar um ícone novo na
sidebar, confirmar que o nome existe no Symbols Outlined antes de aplicar o `fontSet` — ícones de
marca/social normalmente não existem lá. O inverso também vale (`apps/web feat-050`): fora da
sidebar o nome tem que existir no Material Icons **clássico** — `target` (só Symbols) quebrou o
card de odd média do dashboard, virou `local_offer`, o mesmo de Buscar Estatísticas. Os E2E de
dashboard e de Buscar Estatísticas afirmam que todo `mat-icon` de `app-kpi-card` renderiza como
glifo (`scrollWidth <= clientWidth` depois de `document.fonts.ready`; ligadura não resolvida
vira texto mais largo que os 24px do ícone).

## Seletor de mês/ano (MatDatepicker `startView="year"`, `feat-039`, 2026-09-22)

`shared/monthly-drawdown-chart`/`pages/dashboard/monthly-drawdown-grid` precisam de um filtro que
seleciona só mês+ano (sem dia), travado em fronteira de mês inteiro — não o range de dias de
`shared/period-preset-filter`. Padrão: `<input matInput readonly [matDatepicker]="picker">` +
`<mat-datepicker #picker startView="year" (monthSelected)="...">`, fechando o picker manualmente
no handler (`picker.close()`) em vez de deixá-lo descer pra visão de dia. `startView="year"` abre
direto na grade de 12 meses do ano corrente; a barra de período no topo do calendário (`.mat-
calendar-period-button`) navega pra visão multi-ano quando o usuário precisa de outro ano.
Reaproveitável em qualquer filtro futuro que precise de granularidade mês/ano.

## Identidade visual — Arka

Nome e marca **definidos** (2026-08-01, como "StakeVault") — não é mais placeholder, substitui a
seção anterior deste documento. "Bankroll" (nome genérico usado antes) não é mais referenciado em
lugar nenhum. **Renomeada para "Arka" em 2026-09-22/23** (`epic-032`) — mesma geometria de marca,
assets relabelados (ver item 2 de "Fonte" no início deste documento).

### Logo

Anel (o "cofre") com quatro raios diagonais nos cantos, e três barras verticais ascendentes
dentro (o elemento de gráfico/crescimento — é o que carrega o significado da marca). Geometria
inalterada pelo rebranding — só os nomes de arquivo mudaram. Variantes em
`docs/design-references/`:

- `arka-mark-dark.svg` (ex-`logo-mark-dark.svg`) — anel/raios em `--color-brand` (verde), barras
  em `--color-text-primary` (off-white) com opacidade ascendente `0.45 / 0.75 / 1` (a barra mais
  alta é a mais opaca) — uso padrão sobre fundo escuro.
- `arka-mark-light.svg` (ex-`logo-mark-light.svg`) — anel/raios em navy, barras em tons
  ascendentes de verde — uso sobre fundo claro. Cores aproximadas (o usuário não deu os hex
  exatos desta variante, só a imagem composta) — revisitar com color picker se precisão importar.
- `arka-icon.svg` / `arka-app-icon-512.png` — mark sobre fundo preenchido, para app icon/favicon
  em contexto que precisa de um quadrado com fundo (PWA, thumbnail) — substitui a antiga
  `logo-mark-solid.svg` (removida, sem equivalente `-solid` direto neste conjunto).
- `arka-bars-only.svg` (ex-`logo-bars-only.svg`) — **só as três barras**, sem o anel, cor única
  (`--color-brand`). Uso explícito recomendado pelo usuário: favicon em tamanho pequeno, loaders,
  estados vazios — o anel completo não lê bem abaixo de ~32px, as barras sozinhas continuam
  reconhecíveis e servem como padrão gráfico reutilizável (ex.: marca d'água sutil num painel sem
  dados ainda).
- `arka-logo-horizontal-dark.svg` / `arka-logo-horizontal-light.svg` — lockup horizontal pronto
  (mark + wordmark), novo em 2026-09-23 — ver seção "Wordmark" abaixo.

**Achado real (`feat-011.1`, 2026-09-09, sobre os arquivos `logo-mark-*` originais)**: os 4 SVGs
tinham um comentário XML/HTML (`<!-- ... -->`) antes do elemento raiz `<svg>` (documentação de
proveniência). Isso nunca deu problema até agora porque os únicos dois consumidores existentes
eram `<link rel="icon">` (favicon, não depende de tamanho intrínseco) e o SVG inline reconstruído
à mão em `Splash` (não é um `<img>`, não passa pelo decoder de imagem do navegador). A primeira
vez que um SVG desses foi usado via `<img src="...">` (logo na tela de login) o Chromium reportou
`naturalWidth`/`naturalHeight` `0` mesmo com a requisição retornando 200 e `Content-Type:
image/svg+xml` corretos — o `<img>` renderizava como ícone de imagem quebrada. Causa raiz
confirmada isoladamente (arquivo de teste com/sem o comentário antes de `<svg>`): um comentário
antes do elemento raiz impede o Chromium de calcular o tamanho intrínseco de um SVG carregado via
`<img>`, mesmo o `<svg>` tendo `width`/`height` explícitos. Corrigido removendo o comentário
inicial dos 4 arquivos — geometria/cores dos SVGs não mudaram. Ao adicionar um SVG novo neste
projeto para uso via `<img>` (não só `<link>`/inline), não colocar comentário antes do elemento
`<svg>` raiz — confirmar que `arka-mark-*.svg`/`arka-bars-only.svg` (relabels diretos) preservam
essa correção; `arka-icon.svg` (novo) não tem comentário antes da raiz.

### Wordmark

Desde 2026-09-23, o lockup é o SVG pronto `arka-logo-horizontal-{dark,light}.svg` — mark + nome
"Arka" compostos horizontalmente, geometria/tipografia definidas no próprio arquivo, não mais
reconstruído com duas variações de peso tipográfico do nome em CSS (abordagem antiga, usada para
"Stake"+"Vault"). Funciona em monocromático (ex.: impressão, ícone de app sem cor).

Tagline "GESTÃO DE BANCA" (maiúsculas, tracking largo, `--color-text-secondary`, 11px) é
**string de UI comum, não parte fixa do lockup** — passa pelo mecanismo de i18n como qualquer
outro texto (`en-US`: "BANKROLL MANAGEMENT"; `es`: "GESTIÓN DE BANCA"). O nome "Arka" em si
**não é traduzido** — nome de marca, mesma convenção usada por produtos reais (nomes próprios não
mudam com o idioma da interface).

### Onde usar cada variante

- Nav lateral (item 1 do inventário): `arka-mark-dark.svg` (ou `light`, conforme o tema ativo) +
  wordmark ao lado (ou `arka-logo-horizontal-{dark,light}.svg` direto, se o espaço permitir o
  lockup completo em vez de mark+texto separados), tamanho pequeno (~30px, ver mockup de
  referência).
- Splash/loading (item 17 do inventário): geometria do `arka-mark-dark.svg`, animada — usar
  `docs/design-references/arka-splash.html` como alvo.
- Favicon/app icon: `arka-icon.svg`/`arka-app-icon-512.png` (contextos que precisam de fundo
  preenchido) ou `arka-bars-only.svg` (contextos que precisam só do símbolo em tamanho pequeno).
- Estados vazios/loaders inline: `arka-bars-only.svg`.

## QA visual e prototipagem: Impeccable, taste-skill e huashu-design — prioritárias (decisão de 2026-08-02, estendida em 2026-09-03)

Três ferramentas de *design guidance para agentes de IA* — [Impeccable](https://github.com/pbakaus/impeccable),
[taste-skill](https://github.com/leonxlnx/taste-skill) e [huashu-design](https://github.com/alchaincyf/huashu-design)
— **prioritárias** em `apps/web`, igual ao Caveman/claude-code-skills (ver [[habilidades-do-agente]]) —
não uma opção entre outras, o conjunto padrão para qualquer tarefa de frontend. Usadas **só como
auditoria/polish/prototipagem** do que for implementado, nunca como fonte de novas decisões de
design:

- **Este documento (`sistema-de-design.md`) continua sendo a única fonte de verdade de design** —
  marca Arka, paleta, layout em painéis, tema, tipografia, já fechados. O taste-skill não
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
  não tem nada a ver com a identidade Arka). O taste-skill entra pelo mesmo motivo:
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
  Já estava planejado antes desta decisão (ver [[testes]]).

## Ver também

- [[convencoes]] — arquitetura Angular que este documento estende.
- [[web]] — RF/RNF cobertos, regras de Shneiderman para o formulário de apostas.
- [[testes]] — Playwright deve cobrir os fluxos críticos nos dois temas (claro/escuro), não só
  no padrão.
- [[DECISIONS-LOG]] — decisão de 2026-08-02 sobre Impeccable/taste-skill como QA visual, não
  fonte de design, estendida em 2026-09-03 para incluir huashu-design sob a mesma restrição.
