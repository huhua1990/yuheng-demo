const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('assert');

(async () => {
  const output = process.env.YH_BROWSER_OUTPUT;
  const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const api = [], errors = [], failed = [], writes = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('requestfailed', request => failed.push({ path: new URL(request.url()).pathname, failure: request.failure()?.errorText }));
  page.on('request', request => {
    const path = new URL(request.url()).pathname;
    if (path.startsWith('/admin-api/infra/config/') && !['GET', 'HEAD'].includes(request.method())) {
      writes.push({ method: request.method(), path });
    }
  });
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.pathname.startsWith('/admin-api/infra/config/')) api.push({
      method: response.request().method(), path: url.pathname, status: response.status()
    });
  });
  const result = { api, errors, failed, writes, actions: [] };
  try {
    await page.goto('http://127.0.0.1:5300/login', { waitUntil: 'domcontentloaded' });
    await page.locator('input[placeholder="请输入用户名"]:visible').waitFor({ timeout: 30000 });
    await page.locator('input[placeholder="请输入用户名"]:visible').fill(process.env.YH_BROWSER_USERNAME);
    await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YH_BROWSER_PASSWORD);
    await page.getByRole('button', { name: '登录', exact: true }).click();
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 });
    await page.goto('http://127.0.0.1:5300/infra/config', { waitUntil: 'domcontentloaded' });
    const nameFilter = page.getByPlaceholder('请输入参数名称');
    await nameFilter.waitFor({ timeout: 30000 });
    const rows = page.locator('.el-table__body-wrapper tbody tr');
    await rows.first().waitFor({ timeout: 30000 });
    result.initialRows = await rows.count();
    result.firstRow = await rows.first().innerText();
    await page.screenshot({ path: `${output}-initial.png`, fullPage: true });
    await nameFilter.fill('YH probe no matching config');
    await page.getByRole('button', { name: '搜索' }).click();
    await page.getByText('暂无数据', { exact: true }).waitFor({ timeout: 15000 });
    result.noMatchRows = await rows.count();
    assert.strictEqual(result.noMatchRows, 0);
    await page.getByRole('button', { name: '重置' }).click();
    await rows.first().waitFor({ timeout: 15000 });
    result.restoredRows = await rows.count();
    assert.strictEqual(result.restoredRows, result.initialRows);
    assert.strictEqual(await nameFilter.inputValue(), '');
    await page.getByRole('button', { name: '新增' }).click();
    const dialog = page.locator('.el-dialog:visible');
    await dialog.waitFor({ timeout: 15000 });
    await dialog.getByPlaceholder('请输入参数分类').fill('browser-probe');
    await dialog.getByPlaceholder('请输入参数名称').fill('Browser CRUD probe');
    await dialog.getByPlaceholder('请输入参数键名').fill('yh.browser.crud.probe');
    await dialog.getByPlaceholder('请输入参数键值').fill('initial-value');
    const createResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/create', { timeout: 20000 });
    await dialog.getByRole('button', { name: '确 定' }).click();
    const created = await createResponse;
    assert.strictEqual(created.status(), 200);
    assert.strictEqual((await created.json()).code, 0);
    result.actions.push({ action: 'create', status: created.status(), code: 0 });
    await dialog.waitFor({ state: 'hidden', timeout: 15000 });
    await nameFilter.fill('Browser CRUD probe');
    await page.getByRole('button', { name: '搜索' }).click();
    const createdRow = rows.filter({ hasText: 'yh.browser.crud.probe' });
    await createdRow.waitFor({ timeout: 15000 });
    const getResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/get', { timeout: 15000 });
    await createdRow.getByRole('button', { name: '编辑' }).click();
    const detail = await getResponse;
    assert.strictEqual(detail.status(), 200);
    assert.strictEqual((await detail.json()).code, 0);
    const editDialog = page.locator('.el-dialog:visible');
    const editValue = editDialog.getByPlaceholder('请输入参数键值');
    await editValue.fill('updated-value');
    const updateResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/update', { timeout: 20000 });
    await editDialog.getByRole('button', { name: '确 定' }).click();
    const updated = await updateResponse;
    assert.strictEqual(updated.status(), 200);
    assert.strictEqual((await updated.json()).code, 0);
    result.actions.push({ action: 'update', status: updated.status(), code: 0 });
    await createdRow.getByText('updated-value', { exact: true }).waitFor({ timeout: 15000 });
    const deleteResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/delete' && response.request().method() === 'DELETE', { timeout: 20000 });
    await createdRow.getByRole('button', { name: '删除' }).click();
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click();
    const deleted = await deleteResponse;
    assert.strictEqual(deleted.status(), 200);
    assert.strictEqual((await deleted.json()).code, 0);
    result.actions.push({ action: 'delete', status: deleted.status(), code: 0 });
    await rows.filter({ hasText: 'yh.browser.crud.probe' }).waitFor({ state: 'detached', timeout: 15000 });
    await page.getByRole('button', { name: '重置' }).click();
    await rows.first().waitFor({ timeout: 15000 });
    result.rowsAfterDeleteAndReset = await rows.count();
    assert.strictEqual(result.rowsAfterDeleteAndReset, result.initialRows);
    await page.screenshot({ path: `${output}-after-crud.png`, fullPage: true });
    const configGet = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/infra/config/get' && response.status() === 200, { timeout: 15000 });
    await rows.first().getByRole('button', { name: '编辑' }).click();
    const configResponse = await configGet;
    assert.strictEqual((await configResponse.json()).code, 0);
    const cancelDialog = page.locator('.el-dialog:visible');
    const value = cancelDialog.getByPlaceholder('请输入参数键值');
    const previous = await value.inputValue();
    await value.fill(previous + ' browser-cancel-probe');
    result.editChanged = (await value.inputValue()) !== previous;
    await cancelDialog.getByRole('button', { name: '取 消' }).click();
    await cancelDialog.waitFor({ state: 'hidden', timeout: 15000 });
    await page.waitForTimeout(500);
    result.afterCancelRows = await rows.count();
    assert.strictEqual(result.afterCancelRows, result.initialRows);
    assert.deepStrictEqual(writes.map(write => write.path), [
      '/admin-api/infra/config/create', '/admin-api/infra/config/update', '/admin-api/infra/config/delete'
    ]);
    await page.screenshot({ path: `${output}-after-cancel.png`, fullPage: true });
    result.completed = true;
  } finally {
    fs.writeFileSync(`${output}.json`, JSON.stringify(result, null, 2) + '\n');
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
