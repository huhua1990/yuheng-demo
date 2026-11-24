const { chromium } = require('playwright')
const assert = require('assert')

;(async () => {
  const origin = process.env.YH_ERP_UI_ORIGIN
  const output = process.env.YH_ERP_BROWSER_OUTPUT
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.YH_CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()
  const result = { viewport: 'desktop-1440x900', actions: [], pageErrors: [], consoleErrors: [], failedRequests: [], apiResponses: [] }
  page.on('pageerror', error => result.pageErrors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') result.consoleErrors.push(message.text()) })
  page.on('requestfailed', request => {
    const error = request.failure()?.errorText
    if (error !== 'net::ERR_ABORTED') result.failedRequests.push({ path: new URL(request.url()).pathname, error })
  })
  page.on('response', async response => {
    const url = new URL(response.url())
    if (url.pathname.startsWith('/admin-api/erp/')) {
      const event = { method: response.request().method(), path: url.pathname, status: response.status() }
      if (['/admin-api/erp/stock-check/create', '/admin-api/erp/stock-move/create'].includes(url.pathname)) {
        try { event.body = (await response.json()).data } catch {}
      }
      result.apiResponses.push(event)
    }
  })

  try {
    await page.goto(`${origin}/login`, { waitUntil: 'domcontentloaded' })
    await page.locator('input[placeholder="请输入用户名"]:visible').fill(process.env.YUHENG_PROBE_USERNAME)
    await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YUHENG_PROBE_PASSWORD)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })

    await page.goto(`${origin}/erp/stock/check`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    let dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    let form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '盘点时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    let row = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await row.locator('.el-select').nth(0).click()
    await page.getByRole('option', { name: 'P2 Stock Warehouse A', exact: true }).click()
    const stockRead = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/stock/get')
    await row.locator('.el-select').nth(1).click()
    await page.getByRole('option', { name: 'P2 Stock Product', exact: true }).click()
    await stockRead
    const actualCount = row.locator('.el-input-number input').nth(0)
    await actualCount.fill('7')
    assert.strictEqual(await actualCount.inputValue(), '7')
    await actualCount.press('Tab')
    const createCheck = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/stock-check/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const checkResponse = await createCheck
    assert.strictEqual(checkResponse.status(), 200)
    const checkId = (await checkResponse.json()).data
    assert(checkId)
    result.actions.push('stock-check-create-with-positive-adjustment')
    await dialog.waitFor({ state: 'hidden' })
    let checkTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Stock Product' }).first()
    await checkTableRow.waitFor({ timeout: 20000 })
    const checkStatus = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/stock-check/update-status')
    await checkTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await checkStatus).status(), 200)
    result.actions.push('stock-check-approve')

    await page.goto(`${origin}/erp/stock/move`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '调度时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    row = dialog.locator('.el-table__body-wrapper tbody tr').first()
    const choose = async (index, value) => {
      const select = row.locator('.el-select').nth(index)
      await select.click()
      await page.getByRole('option', { name: value, exact: true }).last().evaluate(element => element.click())
    }
    await choose(0, 'P2 Stock Warehouse A')
    await choose(1, 'P2 Stock Warehouse B')
    await choose(2, 'P2 Stock Product')
    const moveQuantity = row.locator('.el-input-number input').nth(0)
    await moveQuantity.fill('3')
    await moveQuantity.press('Tab')
    assert.deepStrictEqual(await row.locator('.el-select').evaluateAll(selects => selects.map(select => select.innerText.trim())),
      ['P2 Stock Warehouse A', 'P2 Stock Warehouse B', 'P2 Stock Product'])
    assert.strictEqual(await moveQuantity.inputValue(), '3.000')
    const createMove = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/stock-move/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const moveResponse = await createMove
    assert.strictEqual(moveResponse.status(), 200)
    const moveId = (await moveResponse.json()).data
    assert(moveId)
    result.actions.push('stock-move-create-two-warehouses')
    await dialog.waitFor({ state: 'hidden' })
    const moveTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Stock Product' }).first()
    await moveTableRow.waitFor({ timeout: 20000 })
    const moveStatus = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/stock-move/update-status')
    await moveTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await moveStatus).status(), 200)
    result.actions.push('stock-move-approve')
    result.checkId = checkId
    result.moveId = moveId
    result.finalUrl = page.url()
    assert.deepStrictEqual(result.pageErrors, [])
    assert.deepStrictEqual(result.consoleErrors, [])
    assert.deepStrictEqual(result.failedRequests, [])
    result.result = 'PASS'
  } catch (error) {
    result.result = 'FAIL'
    result.error = error.stack || error.message
    throw error
  } finally {
    require('fs').writeFileSync(output, JSON.stringify(result, null, 2) + '\n')
    await context.close()
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
