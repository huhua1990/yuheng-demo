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
      if (['/admin-api/erp/purchase-order/create', '/admin-api/erp/purchase-in/create', '/admin-api/erp/purchase-return/create'].includes(url.pathname)) {
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

    await page.goto(`${origin}/erp/purchase/order`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    let dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    let form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '订单时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await form.locator('.el-form-item').filter({ hasText: '供应商' }).locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Purchase Supplier', exact: true }).click()
    let orderRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await orderRow.locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Purchase Product', exact: true }).click()
    let quantity = orderRow.locator('.el-input-number input').first()
    await quantity.fill('10')
    await quantity.press('Tab')
    const createOrder = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-order/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const orderResponse = await createOrder
    assert.strictEqual(orderResponse.status(), 200)
    const orderId = (await orderResponse.json()).data
    assert(orderId)
    result.actions.push('purchase-order-create')
    await dialog.waitFor({ state: 'hidden' })
    let orderTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Purchase Supplier' }).first()
    await orderTableRow.waitFor({ timeout: 20000 })
    const orderStatus = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-order/update-status')
    await orderTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await orderStatus).status(), 200)
    result.actions.push('purchase-order-approve')

    await page.goto(`${origin}/erp/purchase/in`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '入库时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await form.locator('.el-form-item').filter({ hasText: '关联订单' }).getByRole('button', { name: '选择' }).click()
    let selector = page.locator('.el-dialog:visible').last()
    await selector.getByText('P2 Purchase Supplier', { exact: true }).waitFor({ timeout: 20000 })
    await selector.locator('.el-radio').first().click()
    await selector.getByRole('button', { name: '确 定' }).click()
    let inRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await inRow.locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Purch Wh', exact: true }).click()
    const createIn = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-in/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const inResponse = await createIn
    assert.strictEqual(inResponse.status(), 200)
    const inId = (await inResponse.json()).data
    assert(inId)
    result.actions.push('purchase-in-create-from-order')
    await dialog.waitFor({ state: 'hidden' })
    const inTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Purchase Supplier' }).first()
    await inTableRow.waitFor({ timeout: 20000 })
    const inStatus = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-in/update-status')
    await inTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await inStatus).status(), 200)
    result.actions.push('purchase-in-approve')

    await page.goto(`${origin}/erp/purchase/return`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '退货时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await form.locator('.el-form-item').filter({ hasText: '关联订单' }).getByRole('button', { name: '选择' }).click()
    selector = page.locator('.el-dialog:visible').last()
    await selector.getByText('P2 Purchase Supplier', { exact: true }).waitFor({ timeout: 20000 })
    await selector.locator('.el-radio').first().click()
    await selector.getByRole('button', { name: '确 定' }).click()
    const returnRow = dialog.locator('.el-table__body-wrapper tbody tr').first()
    await returnRow.locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Purch Wh', exact: true }).click()
    const returnQuantity = returnRow.locator('.el-input-number input').first()
    await returnQuantity.fill('2')
    await returnQuantity.press('Tab')
    const createReturn = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-return/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const returnResponse = await createReturn
    assert.strictEqual(returnResponse.status(), 200)
    const returnId = (await returnResponse.json()).data
    assert(returnId)
    result.actions.push('purchase-return-create-from-order')
    await dialog.waitFor({ state: 'hidden' })
    const returnTableRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Purchase Supplier' }).first()
    await returnTableRow.waitFor({ timeout: 20000 })
    const returnStatus = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/purchase-return/update-status')
    await returnTableRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await returnStatus).status(), 200)
    result.actions.push('purchase-return-approve')
    result.orderId = orderId
    result.inId = inId
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
