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
      if (url.pathname === '/admin-api/erp/finance-receipt/create' || url.pathname === '/admin-api/erp/finance-payment/create') {
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

    await page.goto(`${origin}/erp/finance/receipt`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    let dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    const form = dialog.locator('form').first()
    await form.locator('.el-form-item').filter({ hasText: '收款时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await form.locator('.el-form-item').filter({ hasText: '客户' }).locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Sales Customer', exact: true }).click()
    await dialog.getByRole('button', { name: /添加销售出库单/ }).click()
    const selector = page.locator('.el-dialog:visible').last()
    await selector.getByText('P2 Sales Customer', { exact: true }).waitFor({ timeout: 20000 })
    await selector.locator('.el-checkbox').first().click()
    await selector.getByRole('button', { name: '确 定' }).click()
    const receiptInput = dialog.locator('.el-table__body-wrapper tbody tr').first().locator('.el-input-number input')
    await receiptInput.fill('3')
    await receiptInput.press('Tab')
    const create = page.waitForResponse(response => new URL(response.url()).pathname === '/admin-api/erp/finance-receipt/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const response = await create
    assert.strictEqual(response.status(), 200)
    const receiptId = (await response.json()).data
    assert(receiptId)
    result.actions.push('receipt-create-from-sale-out')
    await dialog.waitFor({ state: 'hidden' })

    const row = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Sales Customer' }).first()
    await row.waitFor({ timeout: 20000 })
    const status = page.waitForResponse(item => new URL(item.url()).pathname === '/admin-api/erp/finance-receipt/update-status')
    await row.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await status).status(), 200)
    result.actions.push('receipt-approve')

    await page.goto(`${origin}/erp/finance/payment`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible').last()
    await dialog.waitFor()
    const paymentForm = dialog.locator('form').first()
    await paymentForm.locator('.el-form-item').filter({ hasText: '付款时间' }).locator('input').click()
    await page.locator('.el-picker-panel:visible .el-date-table td.today').click()
    await paymentForm.locator('.el-form-item').filter({ hasText: '供应商' }).locator('.el-select').click()
    await page.getByRole('option', { name: 'P2 Purchase Supplier', exact: true }).click()
    await dialog.getByRole('button', { name: /添加采购入库单/ }).click()
    const purchaseSelector = page.locator('.el-dialog:visible').last()
    await purchaseSelector.getByText('P2 Purchase Supplier', { exact: true }).waitFor({ timeout: 20000 })
    await purchaseSelector.locator('.el-checkbox').first().click()
    await purchaseSelector.getByRole('button', { name: '确 定' }).click()
    const paymentInput = dialog.locator('.el-table__body-wrapper tbody tr').first().locator('.el-input-number input')
    await paymentInput.fill('4')
    await paymentInput.press('Tab')
    const createPayment = page.waitForResponse(item => new URL(item.url()).pathname === '/admin-api/erp/finance-payment/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    const paymentResponse = await createPayment
    assert.strictEqual(paymentResponse.status(), 200)
    const paymentId = (await paymentResponse.json()).data
    assert(paymentId)
    result.actions.push('payment-create-from-purchase-in')
    await dialog.waitFor({ state: 'hidden' })
    const paymentRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Purchase Supplier' }).first()
    await paymentRow.waitFor({ timeout: 20000 })
    const paymentStatus = page.waitForResponse(item => new URL(item.url()).pathname === '/admin-api/erp/finance-payment/update-status')
    await paymentRow.getByRole('button', { name: '审批' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await paymentStatus).status(), 200)
    result.actions.push('payment-approve')
    result.receiptId = receiptId
    result.paymentId = paymentId
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
