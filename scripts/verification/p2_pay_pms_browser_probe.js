const { chromium } = require('playwright')
const assert = require('assert')
const fs = require('fs')

const output = process.env.P2_BROWSER_OUTPUT
const user = process.env.P2_BROWSER_USER
const password = process.env.P2_BROWSER_PASSWORD
const shareToken = process.env.P2_SHARE_TOKEN
const sanitizeUrl = value => shareToken ? String(value).split(shareToken).join('[redacted]') : String(value)
const base = process.env.P2_BROWSER_ORIGIN || 'http://127.0.0.1:5219'
const loginForm = '.login-form:visible'

;(async () => {
  const browser = await chromium.launch({ headless: true,
    executablePath: '/Users/huhua/Library/Caches/ms-playwright/chromium-1248/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const errors = [], failed = [], canceled = [], requests = [], actions = []
  page.on('pageerror', error => errors.push(sanitizeUrl(error.stack || error.message)))
  page.on('console', message => { if (message.type() === 'error') errors.push(sanitizeUrl(message.text())) })
  page.on('requestfailed', request => {
    const error = request.failure()?.errorText
    const entry = { url: sanitizeUrl(request.url()), error: sanitizeUrl(error) }
    if (error === 'net::ERR_ABORTED') canceled.push(entry)
    else failed.push(entry)
  })
  page.on('request', request => {
    const url = new URL(request.url())
    if (url.pathname.startsWith('/admin-api/')) requests.push({ method: request.method(), path: url.pathname })
  })
  const result = { result: 'FAIL', viewport: { width: 1440, height: 900 }, errors, failed, canceled, requests, actions }
  try {
    await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByPlaceholder('请输入用户名', { exact: true }).waitFor()
    await page.locator(`${loginForm} input[type="text"]:visible`).last().fill(user)
    await page.locator(`${loginForm} input[type="password"]:visible`).last().fill(password)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })
    await page.waitForLoadState('networkidle')
    await page.goto(`${base}/pay/app`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('columnheader', { name: '应用标识', exact: true }).first().waitFor({ timeout: 30000 })
    actions.push('pay-app-route')
    await page.getByRole('button', { name: /新增/ }).click()
    const appDialog = page.locator('.el-dialog:visible')
    await appDialog.waitFor({ timeout: 15000 })
    await appDialog.locator('input[placeholder="请输入应用名"]').fill(`Browser Pay ${Date.now()}`)
    await appDialog.locator('input[placeholder="请输入应用标识"]').fill(`browser-${Date.now()}`)
    await appDialog.locator('input[placeholder="请输入支付结果的回调地址"]').fill('https://example.invalid/order')
    await appDialog.locator('input[placeholder="请输入退款结果的回调地址"]').fill('https://example.invalid/refund')
    const createResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/pay/app/create')
    await appDialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await (await createResponse).json()).code, 0)
    const refreshedApps = page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/pay/app/page')
    await refreshedApps
    await page.waitForLoadState('networkidle')
    actions.push('pay-app-create')

    await page.goto(`${base}/pms/pm/project/list`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('button', { name: '新建项目', exact: true }).waitFor({ timeout: 30000 })
    actions.push('pms-project-route')
    const create = page.getByRole('button', { name: /新建项目|新增项目|新增/ }).first()
    await create.click()
    const projectDialog = page.locator('.el-dialog:visible')
    await projectDialog.waitFor({ timeout: 15000 })
    await projectDialog.locator('input[placeholder="请输入项目名称"]').fill(`Browser Project ${Date.now()}`)
    const projectResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/pms/pm/project/create')
    await projectDialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await (await projectResponse).json()).code, 0)
    actions.push('pms-project-create')
    assert(shareToken, 'share token is required')
    const anonymous = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    try {
      const sharePage = await anonymous.newPage()
      const anonymousRequests = []
      sharePage.on('request', request => {
        const path = new URL(request.url()).pathname
        if (path.startsWith('/admin-api/')) anonymousRequests.push(path)
      })
      sharePage.on('pageerror', error => errors.push(sanitizeUrl(error.stack || error.message)))
      sharePage.on('console', message => { if (message.type() === 'error') errors.push(sanitizeUrl(message.text())) })
      sharePage.on('requestfailed', request => {
        const error = request.failure()?.errorText
        const entry = { url: sanitizeUrl(request.url()), error: sanitizeUrl(error) }
        if (error === 'net::ERR_ABORTED') canceled.push(entry)
        else failed.push(entry)
      })
      await sharePage.goto(`${base}/pms/kb/document/share/${encodeURIComponent(shareToken)}`, { waitUntil: 'domcontentloaded' })
      await sharePage.getByText('P2 content', { exact: true }).waitFor({ timeout: 30000 })
      await sharePage.reload({ waitUntil: 'domcontentloaded' })
      await sharePage.getByText('P2 content', { exact: true }).waitFor({ timeout: 30000 })
      assert(!anonymousRequests.some(path => path.startsWith('/admin-api/system/notify-message/')),
        'anonymous share must not request authenticated notifications')
      actions.push('anonymous-share-visible')
    } finally {
      await anonymous.close()
    }
    assert.deepStrictEqual(errors, [])
    assert.deepStrictEqual(failed, [])
    result.result = 'PASS'
  } finally {
    result.errors = errors
    result.failed = failed
    result.canceled = canceled
    fs.writeFileSync(output, JSON.stringify(result, null, 2))
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
