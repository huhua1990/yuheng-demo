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
      if (['/admin-api/erp/sale-order/create', '/admin-api/erp/sale-out/create'].includes(url.pathname)) {
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

    await page.goto(`${origin}/erp/sale/order`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    let dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    const orderForm = dialog.locator('form').first()
    await orderForm.locator('.el-form-item').filter({ hasText: '订单时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await orderForm.locator('.el-form-item').filter({ hasText: '客户' }).locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Sales Customer', exact: true }).click()
    const orderRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    const productSelect = orderRow.locator('.el-select').first()
    await productSelect.click()
    await page.getByRole('option', { name: 'P2 Sales Product', exact: true }).click()
    const orderQuantity = orderRow.locator('.el-input-number input').first()
    await orderQuantity.fill('3')
    await orderQuantity.press('Tab')
    const createOrder = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-order/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const orderResponse = await createOrder
    assert.strictEqual(orderResponse.status(), 200)
    const orderId = (await orderResponse.json()).data
    assert(orderId)
    result.actions.push('sales-order-create')
    await dialog.waitFor({ state: 'hidden' })

    let orderTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Sales Customer' }).first()
    await orderTableRow.waitFor({ timeout: 20000 })
    const orderStatusResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-order/update-status')
    await orderTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await orderStatusResponse).status(), 200)
    result.actions.push('sales-order-approve')

    await page.goto(`${origin}/erp/sale/out`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    const outForm = dialog.locator('form').first()
    await outForm.locator('.el-form-item').filter({ hasText: '出库时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await outForm.locator('.el-form-item').filter({ hasText: '关联订单' }).getByRole('button', { name: '选择' }).click()
    const selector = page.locator('.el-dialog:visible').last()
    await selector.getByText('P2 Sales Customer', { exact: true }).waitFor({ timeout: 20000 })
    await selector.locator('.el-radio').first().click()
    await selector.getByRole('button', { name: '确 定' }).click()
    const outRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await outRow.locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Sales Warehouse', exact: true }).click()
    const createOut = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-out/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const outResponse = await createOut
    assert.strictEqual(outResponse.status(), 200)
    const outId = (await outResponse.json()).data
    assert(outId)
    result.actions.push('sales-out-create-from-order')
    await dialog.waitFor({ state: 'hidden' })

    const outTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Sales Customer' }).first()
    await outTableRow.waitFor({ timeout: 20000 })
    const outStatusResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-out/update-status')
    await outTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await outStatusResponse).status(), 200)
    result.actions.push('sales-out-approve')

    await page.goto(`${origin}/erp/sale/return`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    const returnForm = dialog.locator('form').first()
    await returnForm.locator('.el-form-item').filter({ hasText: '退货时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await returnForm.locator('.el-form-item').filter({ hasText: '关联订单' }).getByRole('button', { name: '选择' }).click()
    const returnSelector = page.locator('.el-dialog:visible').last()
    await returnSelector.getByText('P2 Sales Customer', { exact: true }).waitFor({ timeout: 20000 })
    await returnSelector.locator('.el-radio').first().click()
    await returnSelector.getByRole('button', { name: '确 定' }).click()
    const returnRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await returnRow.locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Sales Warehouse', exact: true }).click()
    const createReturn = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-return/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const returnResponse = await createReturn
    assert.strictEqual(returnResponse.status(), 200)
    const returnId = (await returnResponse.json()).data
    assert(returnId)
    result.actions.push('sales-return-create-from-order')
    await dialog.waitFor({ state: 'hidden' })

    const returnTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Sales Customer' }).first()
    await returnTableRow.waitFor({ timeout: 20000 })
    const returnStatusResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/sale-return/update-status')
    await returnTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await returnStatusResponse).status(), 200)
    result.actions.push('sales-return-approve')
    result.orderId = orderId
    result.outId = outId
    result.returnId = returnId
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
