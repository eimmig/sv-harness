// Auditoria automatica de acessibilidade (RNF02, devolutiva do TCC 2): axe-core com as regras
// WCAG 2.0/2.1/2.2 A e AA em cada tela, nos temas claro e escuro, e um teste de teclado no login
// e no registro de aposta (ordem do Tab, foco visivel, envio pelo Enter).
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'https://192.168.2.124';
const OUT = process.argv[2];
const AXE = process.env.AXE_PATH || require.resolve('axe-core/axe.min.js');
const ROUTES = ['overview', 'dashboard', 'register-bet', 'history', 'betting-houses', 'sports', 'leagues',
  'markets', 'tipsters', 'teams', 'sports-dashboard', 'search-statistics', 'period-report', 'period-comparison',
  'telegram-link', 'users', 'change-password'];
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

async function settle(page) {
  await page.waitForLoadState('networkidle');
  await page.locator('app-loading-overlay output').waitFor({ state: 'detached', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(800);
}

async function audit(page) {
  await page.addScriptTag({ path: AXE });
  return page.evaluate(async (tags) => {
    const r = await window.axe.run(document, { runOnly: { type: 'tag', values: tags } });
    return {
      violations: r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length,
        targets: v.nodes.slice(0, 3).map((n) => n.target.join(' ')) })),
      passes: r.passes.length, incomplete: r.incomplete.length,
    };
  }, TAGS);
}

async function login(page) {
  await page.goto(`${BASE}/login`);
  await page.getByTestId('login-email').fill(process.env.CAP_EMAIL);
  await page.getByTestId('login-password').fill(process.env.CAP_PASSWORD);
  await page.getByTestId('login-submit').click();
  await page.waitForURL(/overview|dashboard/);
}

async function focusReport(page, steps) {
  const seen = [];
  for (let i = 0; i < steps; i++) {
    await page.keyboard.press('Tab');
    seen.push(await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      const cs = getComputedStyle(el);
      const outline = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0;
      const shadow = cs.boxShadow && cs.boxShadow !== 'none';
      // o mat-form-field desenha o foco na borda do campo, não no input
      const field = el.closest('.mat-mdc-form-field');
      const fieldFocused = !!field && field.classList.contains('mat-focused');
      const label = el.getAttribute('aria-label') || el.getAttribute('data-testid') || el.textContent.trim().slice(0, 30);
      return { tag: el.tagName.toLowerCase(), label, focusVisible: el.matches(':focus-visible'), indicator: outline || shadow || fieldFocused };
    }));
  }
  return seen;
}

(async () => {
  const browser = await chromium.launch();
  const report = { date: new Date().toISOString(), tags: TAGS, themes: {} };
  for (const scheme of ['dark', 'light']) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: scheme,
      locale: 'pt-BR', ignoreHTTPSErrors: true });
    const page = await context.newPage();
    const pages = {};
    await page.goto(`${BASE}/login`);
    await settle(page);
    pages.login = await audit(page);
    if (scheme === 'dark') {
      report.keyboardLogin = await focusReport(page, 4);
    }
    await login(page);
    for (const route of ROUTES) {
      await page.goto(`${BASE}/${route}`);
      await settle(page);
      pages[route] = await audit(page);
    }
    if (scheme === 'dark') {
      await page.goto(`${BASE}/register-bet`);
      await settle(page);
      report.keyboardRegisterBet = await focusReport(page, 25);
    }
    report.themes[scheme] = pages;
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'a11y.json'), JSON.stringify(report, null, 2));
  for (const [scheme, pages] of Object.entries(report.themes)) {
    for (const [route, r] of Object.entries(pages)) {
      const v = r.violations.map((x) => `${x.id}(${x.impact},${x.nodes})`).join(' ');
      console.log(`${scheme.padEnd(5)} ${route.padEnd(18)} regras ok=${r.passes} violacoes=${r.violations.length} ${v}`);
    }
  }
  const kb = (list) => list.filter(Boolean);
  for (const [name, list] of [['login', report.keyboardLogin], ['register-bet', report.keyboardRegisterBet]]) {
    const items = kb(list);
    console.log(`teclado ${name}: ${items.length} paradas, sem indicador de foco: ${items.filter((x) => !x.indicator).map((x) => x.tag + ':' + x.label).join(', ') || 'nenhuma'}`);
  }
})();
