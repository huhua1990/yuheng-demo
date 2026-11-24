const { chromium } = require('playwright')
const assert = require('assert')
const fs = require('fs')

;(async () => {
  const browser = await chromium.launch({ headless: true,
    executablePath: process.env.P2_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
  const errors = [], failed = [], canceled = [], requests = [], actions = []
  const result = { result: 'FAIL', viewport: { width: 1440, height: 900 }, errors, failed, canceled, requests, actions }
  const base = process.env.P2_MEMBER_PAY_ORIGIN
  const memberId = Number(process.env.P2_MEMBER_PAY_ID)
  const page = await browser.newPage({ viewport: result.viewport })
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('requestfailed', request => {
    const item = { path: new URL(request.url()).pathname, error: request.failure()?.errorText }
    ;(item.error === 'net::ERR_ABORTED' ? canceled : failed).push(item)
  })
  page.on('request', request => {
    const path = new URL(request.url()).pathname
    if (path.startsWith('/admin-api/')) requests.push({ method: request.method(), path })
  })
  async function login(username, password) {
    await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' })
    await page.locator('.login-form:visible input[type="text"]:visible').last().fill(username)
    await page.locator('.login-form:visible input[type="password"]:visible').last().fill(password)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })
    await page.waitForLoadState('networkidle')
  }
  function response(path) {
    return page.waitForResponse(r => new URL(r.url()).pathname === `/admin-api${path}`)
  }
  async function memberList() {
    await page.goto(`${base}/member/user`, { waitUntil: 'domcontentloaded' })
    const filter = page.getByPlaceholder('请输入用户昵称', { exact: true })
    try {
      await filter.waitFor({ state: 'visible', timeout: 10000 })
    } catch (error) {
      result.member_list_diagnostic = {
        url: page.url(), title: await page.title(),
        body: (await page.locator('body').innerText()).slice(0, 3000),
        inputs: await page.locator('input:visible').evaluateAll(nodes => nodes.map(node => ({
          placeholder: node.getAttribute('placeholder'), type: node.getAttribute('type')
        })))
      }
      await page.screenshot({ path: process.env.P2_MEMBER_PAY_BROWSER_OUTPUT.replace('.json', '-failure.png'), fullPage: true })
      throw error
    }
    await filter.fill('P2 Pay Member')
    const refreshed = response('/member/user/page')
    await page.getByRole('button', { name: '搜索', exact: true }).click()
    assert.strictEqual((await (await refreshed).json()).code, 0)
    const row = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 Pay Member' })
    await row.waitFor()
    return row
  }
  try {
    await login(process.env.P2_MEMBER_PAY_USER, process.env.P2_MEMBER_PAY_PASSWORD)
    const walletResponse = response('/pay/wallet/get')
    await page.goto(`${base}/member/user/detail/${memberId}`, { waitUntil: 'domcontentloaded' })
    const wallet = (await (await walletResponse).json()).data
    assert.strictEqual(wallet.userId, memberId)
    assert.strictEqual(wallet.balance, 125)
    await page.getByText('账户明细', { exact: true }).waitFor()
    const transactions = response('/pay/wallet-transaction/page')
    await page.getByRole('tab', { name: '余额', exact: true }).click()
    const initial = (await (await transactions).json()).data
    assert.strictEqual(initial.total, 1)
    assert.strictEqual(initial.list[0].price, 125)
    await page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: '1.25 元' }).waitFor()
    actions.push('member-wallet-detail', 'member-wallet-transactions')
    for (const [kind, amount, expected] of [['增加', '2.50', 375], ['减少', '0.75', 300]]) {
      const row = await memberList()
      await row.getByRole('button', { name: '更多', exact: true }).click()
      const walletLoading = response('/pay/wallet/get')
      await page.getByRole('menuitem', { name: '修改余额', exact: true }).click()
      assert.strictEqual((await (await walletLoading).json()).code, 0)
      const dialog = page.locator('.el-dialog:visible')
      await dialog.waitFor()
      await dialog.locator('.el-radio').filter({ hasText: kind }).click()
      await dialog.locator('.el-input-number input').fill(amount)
      await dialog.locator('.el-input-number input').press('Tab')
      const update = response('/pay/wallet/update-balance')
      await dialog.getByRole('button', { name: '确 定', exact: true }).click()
      assert.strictEqual((await (await update).json()).code, 0)
      await dialog.waitFor({ state: 'hidden' })
      await page.waitForLoadState('networkidle')
      actions.push(`member-wallet-${kind}`)
      const reread = response('/pay/wallet/get')
      await page.goto(`${base}/member/user/detail/${memberId}`, { waitUntil: 'domcontentloaded' })
      assert.strictEqual((await (await reread).json()).data.balance, expected)
      await page.waitForLoadState('networkidle')
    }
    const finalTransactions = response('/pay/wallet-transaction/page')
    await page.getByRole('tab', { name: '余额', exact: true }).click()
    const final = (await (await finalTransactions).json()).data
    assert.deepStrictEqual(final.list.map(row => [row.price, row.balance]), [[-75, 300], [250, 375], [125, 125]])
    await page.waitForLoadState('networkidle')
    actions.push('member-wallet-ledger-after-adjustments')
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
    await login(process.env.P2_MEMBER_PAY_READER, process.env.P2_MEMBER_PAY_READER_PASSWORD)
    const readerRow = await memberList()
    assert.strictEqual(await readerRow.getByRole('button', { name: '更多', exact: true }).count(), 0)
    actions.push('readonly-wallet-action-hidden')
    assert(!requests.some(({ path }) => /^\/admin-api\/(product|trade|promotion)\//.test(path)))
    assert.deepStrictEqual(errors, [])
    assert.deepStrictEqual(failed, [])
    result.result = 'PASS'
  } finally {
    fs.writeFileSync(process.env.P2_MEMBER_PAY_BROWSER_OUTPUT, JSON.stringify(result, null, 2) + '\n')
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
