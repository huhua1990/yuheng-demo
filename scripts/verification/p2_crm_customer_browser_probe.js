const { chromium } = require('playwright')
const assert = require('assert')
const fs = require('fs')

;(async () => {
  const origin = process.env.P2_CRM_UI_ORIGIN
  const output = process.env.P2_CRM_BROWSER_OUTPUT
  const marker = process.env.P2_CRM_CUSTOMER_MARKER
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.YH_CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()
  const result = { result: 'FAIL', viewport: 'desktop-1440x900', pageErrors: [], consoleErrors: [], failedRequests: [], apiResponses: [] }
  page.on('pageerror', error => result.pageErrors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') result.consoleErrors.push(message.text()) })
  page.on('requestfailed', request => {
    const error = request.failure()?.errorText
    if (error !== 'net::ERR_ABORTED') result.failedRequests.push({ path: new URL(request.url()).pathname, error })
  })
  page.on('response', response => {
    const url = new URL(response.url())
    if (url.pathname === '/admin-api/crm/customer/page') {
      result.apiResponses.push({ method: response.request().method(), status: response.status() })
    }
  })
  try {
    await page.goto(`${origin}/login`, { waitUntil: 'domcontentloaded' })
    await page.locator('input[placeholder="请输入用户名"]:visible').fill(process.env.P2_CRM_USERNAME)
    await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.P2_CRM_PASSWORD)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })
    await page.goto(`${origin}/crm/customer`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('columnheader', { name: '客户名称', exact: true }).waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /新增/ }).first().waitFor({ timeout: 20000 })
    await page.waitForFunction(value => document.body.innerText.includes(value), marker)
    const row = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: marker }).first()
    await row.waitFor({ timeout: 20000 })
    result.listVisible = true
    result.customerRows = await page.locator('.el-table__body-wrapper tbody tr').count()
    result.apiResponses = result.apiResponses.filter(item => item.status === 200)
    assert(result.apiResponses.length > 0, 'customer page API was not successful')
    assert.deepStrictEqual(result.pageErrors, [])
    assert.deepStrictEqual(result.consoleErrors, [])
    assert.deepStrictEqual(result.failedRequests, [])
    result.finalUrl = page.url()
    result.result = 'PASS'
  } catch (error) {
    result.error = error.stack || error.message
    throw error
  } finally {
    fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n')
    await context.close()
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
