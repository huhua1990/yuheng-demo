const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const output = process.env.YH_BROWSER_OUTPUT;
  const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const results = {};
  try {
    for (const [label, viewport] of Object.entries({ desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } })) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      const errors = [];
      const failed = [];
      const api = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      page.on('requestfailed', request => failed.push({ path: new URL(request.url()).pathname, failure: request.failure()?.errorText }));
      page.on('response', response => {
        const url = new URL(response.url());
        if (url.pathname.startsWith('/admin-api/')) api.push({ path: url.pathname, status: response.status() });
      });
      await page.goto('http://127.0.0.1:5199/login', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2500);
      const loginDebug = await page.evaluate(() => ({
        title: document.title,
        location: location.href,
        viewport: { width: innerWidth, height: innerHeight },
        root: [...document.querySelectorAll('#app, #app > *, #app > * > *')].map(node => ({
          tag: node.tagName, className: node.className,
          rect: (() => { const r = node.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; })(),
          display: getComputedStyle(node).display, visibility: getComputedStyle(node).visibility,
          overflow: getComputedStyle(node).overflow, minHeight: getComputedStyle(node).minHeight
        })),
        inputs: [...document.querySelectorAll('input')].map(node => ({
          placeholder: node.placeholder, display: getComputedStyle(node).display,
          visibility: getComputedStyle(node).visibility,
          rect: (() => { const r = node.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; })()
        })),
        loginText: document.querySelector('#app')?.innerText.slice(0, 500)
      }));
      console.log(`${label} login debug:`, JSON.stringify(loginDebug));
      await fs.promises.writeFile(`${output}-${label}-login-debug.json`, JSON.stringify(loginDebug, null, 2));
      await page.locator('input[placeholder="请输入用户名"]:visible').waitFor({ timeout: 15000 });
      console.log('visible inputs:', await page.locator('input:visible').evaluateAll(nodes => nodes.map(node => ({ placeholder: node.placeholder, type: node.type }))));
      await page.screenshot({ path: `${output}-${label}-login.png` });
      await page.locator('input:visible').nth(1).fill(process.env.YH_BROWSER_USERNAME);
      await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YH_BROWSER_PASSWORD);
      await page.getByRole('button', { name: '登录', exact: true }).click();
      await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 });
      await page.goto('http://127.0.0.1:5199/system/post', { waitUntil: 'domcontentloaded' });
      await page.getByPlaceholder('请输入岗位名称').waitFor({ timeout: 30000 });
      await page.getByText('项目经理', { exact: true }).first().waitFor({ timeout: 30000 });
      await page.mouse.move(viewport.width - 5, viewport.height - 5);
      await page.waitForTimeout(300);

      const initial = await page.evaluate(() => ({
        viewport: { width: innerWidth, height: innerHeight },
        document: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight },
        horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
        rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length,
        contentVisible: !!document.querySelector('.el-table')?.getBoundingClientRect().height,
        layout: (() => {
          const candidates = [...document.querySelectorAll('body *')];
          const rect = node => {
            if (!node) return null;
            const r = node.getBoundingClientRect();
            return { x: r.x, y: r.y, width: r.width, height: r.height };
          };
          const overlay = candidates.find(node => String(node.className).includes('opacity-30'));
          const menu = candidates.find(node => String(node.className).includes('layout-border__right'));
          return {
            menu: menu ? { className: String(menu.className), rect: rect(menu) } : null,
            overlay: overlay ? { className: String(overlay.className), rect: rect(overlay) } : null,
            candidates: candidates.slice(0, 24).map(node => ({ className: String(node.className), rect: rect(node) }))
          };
        })()
      }));
      await page.screenshot({ path: `${output}-${label}-initial.png`, fullPage: true });
      if (label === 'mobile') {
        const hamburger = page.locator('#v-tool-header .v-collapse');
        const hamburgerCount = await hamburger.count();
        let afterHamburger = null;
        let afterOverlay = null;
        if (hamburgerCount === 1) {
          await hamburger.click();
          await page.waitForTimeout(400);
          afterHamburger = await page.evaluate(() => {
            const candidates = [...document.querySelectorAll('body *')];
            const overlay = candidates.find(node => String(node.className).includes('opacity-30'));
            const menu = candidates.find(node => String(node.className).includes('layout-border__right'));
            const rect = node => {
              if (!node) return null;
              const r = node.getBoundingClientRect();
              return { x: r.x, y: r.y, width: r.width, height: r.height };
            };
            return {
              menu: menu ? { className: String(menu.className), rect: rect(menu) } : null,
              overlay: overlay ? { className: String(overlay.className), rect: rect(overlay), display: getComputedStyle(overlay).display } : null,
              rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length
            };
          });
          await page.screenshot({ path: `${output}-mobile-after-hamburger.png`, fullPage: true });
          await page.evaluate(() => {
            const overlay = [...document.querySelectorAll('body *')].find(node =>
              String(node.className).includes('opacity-30'));
            overlay?.click();
          });
          await page.waitForTimeout(400);
          afterOverlay = await page.evaluate(() => ({
            overlayVisible: [...document.querySelectorAll('body *')].some(node =>
              String(node.className).includes('opacity-30')
            ),
            rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length
          }));
          await page.screenshot({ path: `${output}-mobile-after-overlay.png`, fullPage: true });
        }
        results[label] = { initial, hamburgerCount, afterHamburger, afterOverlay, errors, failed, api };
        await context.close();
        continue;
      }
      await page.getByPlaceholder('请输入岗位名称').fill('No such post');
      await page.getByRole('button', { name: '搜索' }).click({ timeout: 15000 });
      await page.getByText('暂无数据', { exact: true }).waitFor({ timeout: 15000 });
      const noMatchRows = await page.locator('.el-table__body-wrapper tbody tr').count();
      await page.getByRole('button', { name: '重置' }).click();
      await page.getByText('项目经理', { exact: true }).first().waitFor({ timeout: 15000 });
      const restoredRows = await page.locator('.el-table__body-wrapper tbody tr').count();
      await page.screenshot({ path: `${output}-${label}-reset.png`, fullPage: true });
      results[label] = { initial, noMatchRows, restoredRows, errors, failed, api };
      await context.close();
    }
  } finally {
    fs.writeFileSync(`${output}.json`, JSON.stringify(results, null, 2) + '\n');
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
