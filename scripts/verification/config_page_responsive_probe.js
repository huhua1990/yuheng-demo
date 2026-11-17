const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('assert');

const base = process.env.YH_BROWSER_BASE;
const output = process.env.YH_BROWSER_OUTPUT;
const result = { base, viewports: {}, consoleErrors: [], pageErrors: [], requestFailed: [], responses: [] };

async function inspectViewport(browser, width, height, label) {
  const context = await browser.newContext({ viewport: { width, height } });
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.__yhPointerEvents = [];
    document.addEventListener('mouseover', event => {
      const node = event.target;
      if (node instanceof Element && (node.closest('.v-menu') || node.closest('[id^="el-popper-container"]'))) {
        window.__yhPointerEvents.push({ type: event.type, tag: node.tagName,
          className: String(node.className), text: node.textContent?.trim().slice(0, 100),
          x: event.clientX, y: event.clientY });
      }
    }, true);
  });
  page.on('pageerror', error => result.pageErrors.push({ label, message: error.message }));
  page.on('console', message => {
    if (message.type() === 'error') result.consoleErrors.push({ label, message: message.text() });
  });
  page.on('requestfailed', request => result.requestFailed.push({
    label, path: new URL(request.url()).pathname, failure: request.failure()?.errorText
  }));
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.pathname.startsWith('/admin-api/infra/config/')) {
      result.responses.push({ label, method: response.request().method(), path: url.pathname, status: response.status() });
    }
  });

  try {
    await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' });
    const user = page.locator('input[placeholder="请输入用户名"]');
    const loginButton = page.getByRole('button', { name: '登录', exact: true });
    try {
      await user.waitFor({ state: 'visible', timeout: 15000 });
    } catch (error) {
      if (new URL(page.url()).pathname.includes('/login')) {
        throw new Error(`login form did not become visible at ${page.url()}: ${(await page.locator('body').innerText()).slice(0, 300)}`);
      }
    }
    if (await user.isVisible().catch(() => false)) {
      await user.fill(process.env.YH_BROWSER_USERNAME);
      await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YH_BROWSER_PASSWORD);
      await loginButton.click();
      await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 });
    }

    await page.goto(`${base}/infra/config`, { waitUntil: 'domcontentloaded' });
    await page.getByPlaceholder('请输入参数名称').waitFor({ timeout: 30000 });
    const rows = page.locator('.el-table__body-wrapper tbody tr');
    await rows.first().waitFor({ timeout: 30000 });
    // Moving the pointer away from the collapsed sidebar dismisses hover submenus.
    await page.mouse.move(width - 5, height - 5);
    await page.waitForTimeout(500);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(100);
    const measurements = await page.evaluate(() => {
      const visible = element => {
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
      };
      const content = document.querySelector('.app-main, .app-container, #app');
      const table = document.querySelector('.el-table');
      const filter = document.querySelector('.el-form');
      const bodyRows = [...document.querySelectorAll('.el-table__body-wrapper tbody tr')];
      const rect = element => {
        if (!element) return null;
        const r = element.getBoundingClientRect();
        return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height };
      };
      return {
        document: { clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth,
          clientHeight: document.documentElement.clientHeight, scrollHeight: document.documentElement.scrollHeight },
        content: rect(content), table: rect(table), filter: rect(filter),
        visibleMenuItems: [...document.querySelectorAll('.el-menu-item, .el-sub-menu__title')].filter(visible).length,
        visibleRows: bodyRows.length,
        rowHeights: bodyRows.slice(0, 3).map(row => row.getBoundingClientRect().height),
        searchButton: rect([...document.querySelectorAll('button')].find(button => button.innerText.includes('搜索') && visible(button))),
        sidebar: rect(document.querySelector('.layout-border__right')),
        overlayCount: document.querySelectorAll('.v-layout > .opacity-30').length,
        visiblePoppers: [...document.querySelectorAll('[id^="el-popper-container"] [role="menu"]')]
          .filter(visible).map(node => ({ text: node.innerText.slice(0, 200), rect: rect(node) }))
      };
    });
    result.viewports[label] = { list: measurements, rowTexts: await rows.allInnerTexts() };
    await page.screenshot({ path: `${output}-${label}-list.png`, fullPage: true });

    const nameFilter = page.getByPlaceholder('请输入参数名称');
    const captureHit = () => page.getByRole('button', { name: /搜索/ }).evaluate(button => {
      const r = button.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      const ancestors = [];
      for (let node = hit; node && ancestors.length < 8; node = node.parentElement) {
        const s = getComputedStyle(node), rect = node.getBoundingClientRect();
        ancestors.push({ tag: node.tagName, id: node.id, className: String(node.className),
          text: node.textContent?.trim().slice(0, 120), display: s.display, visibility: s.visibility,
          opacity: s.opacity, left: rect.left, top: rect.top, width: rect.width, height: rect.height });
      }
      return { withinButton: !!hit && button.contains(hit), ancestors, events: window.__yhPointerEvents.slice(-30) };
    });
    result.viewports[label].hitBeforeFill = await captureHit();
    if (width < 600 && !result.viewports[label].hitBeforeFill.withinButton) {
      await page.locator('#v-tool-header .v-collapse').click();
      const overlay = page.locator('.v-layout > .opacity-30');
      await overlay.waitFor({ state: 'visible' });
      await overlay.click({ position: { x: width - 10, y: height - 10 } });
      await overlay.waitFor({ state: 'detached' });
      await page.waitForTimeout(500);
      result.viewports[label].hitAfterDrawerCycle = await captureHit();
    }
    await nameFilter.fill('YH responsive no match');
    result.viewports[label].searchHitTarget = await captureHit();
    await page.getByRole('button', { name: /搜索/ }).click();
    await page.getByText('暂无数据', { exact: true }).waitFor({ timeout: 15000 });
    result.viewports[label].noMatchRows = await rows.count();
    await page.getByRole('button', { name: /重置/ }).click();
    await rows.first().waitFor({ timeout: 15000 });
    result.viewports[label].resetRows = await rows.count();

    const detail = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/get' && response.status() === 200);
    await rows.first().getByRole('button', { name: '编辑' }).click();
    await detail;
    const dialog = page.locator('.el-dialog:visible');
    await dialog.waitFor({ timeout: 15000 });
    await page.waitForFunction(() => !document.querySelector('.el-dialog')?.closest('.dialog-fade-enter-active'));
    await page.waitForTimeout(350);
    result.viewports[label].dialog = await dialog.evaluate(element => {
      const r = element.getBoundingClientRect();
      const footer = element.querySelector('.el-dialog__footer')?.getBoundingClientRect();
      return { left: r.left, right: r.right, width: r.width, scrollWidth: element.scrollWidth,
        footerRight: footer?.right ?? null, viewportWidth: document.documentElement.clientWidth };
    });
    const value = dialog.getByPlaceholder('请输入参数键值');
    const original = await value.inputValue();
    result.viewports[label].fieldGeometry = await value.evaluate(input => {
      const nodes = [input, input.parentElement, input.closest('.el-form-item__content'), input.closest('.el-form-item'), input.closest('.el-dialog')];
      return nodes.filter(Boolean).map(node => {
        const r = node.getBoundingClientRect(), s = getComputedStyle(node);
        return { tag: node.tagName, className: node.className, width: r.width, height: r.height,
          left: r.left, right: r.right, display: s.display, visibility: s.visibility,
          minWidth: s.minWidth, overflow: s.overflow, scrollWidth: node.scrollWidth };
      });
    });
    result.viewports[label].defaultFieldUsable = result.viewports[label].fieldGeometry[0].width >= 100;
    await page.screenshot({ path: `${output}-${label}-dialog.png`, fullPage: true });
    if (width < 600 && !(await value.isVisible())) {
      await dialog.locator('.el-dialog__header .is-hover').first().click();
      await value.waitFor({ state: 'visible', timeout: 10000 });
      result.viewports[label].fieldVisibleAfterFullscreen = true;
    }
    await value.fill(original + ' responsive cancel probe');
    await dialog.getByRole('button', { name: '取 消' }).click();
    await dialog.waitFor({ state: 'hidden', timeout: 15000 });
    result.viewports[label].cancelChangedFormOnly = true;
    await page.screenshot({ path: `${output}-${label}-after-cancel.png`, fullPage: true });
  } finally {
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  try {
    result.errors = {};
    for (const [width, height, label] of [[1440, 900, 'desktop-1440x900'], [390, 844, 'mobile-390x844'], [320, 844, 'mobile-320x844']]) {
      try { await inspectViewport(browser, width, height, label); }
      catch (error) { result.errors[label] = error.stack; }
    }
    assert.deepStrictEqual(result.errors, {});
    assert.strictEqual(result.viewports['mobile-390x844'].noMatchRows, 0);
    assert(result.viewports['mobile-390x844'].resetRows > 0);
    assert.strictEqual(result.viewports['mobile-390x844'].list.document.scrollWidth, 390);
    assert(result.viewports['mobile-390x844'].dialog.right <= 390);
    assert(result.viewports['mobile-390x844'].dialog.footerRight <= 390);
    if (process.env.YH_REQUIRE_USABLE_DEFAULT === 'true') {
      for (const viewport of Object.values(result.viewports)) {
        assert(viewport.defaultFieldUsable, 'default config value input must be at least 100px wide');
        assert(viewport.dialog.scrollWidth <= viewport.dialog.width + 1, 'dialog content must fit');
        assert(!viewport.fieldVisibleAfterFullscreen, 'default config form must work without fullscreen');
      }
    }
    result.completed = true;
  } finally {
    fs.writeFileSync(`${output}.json`, JSON.stringify(result, null, 2) + '\n');
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
