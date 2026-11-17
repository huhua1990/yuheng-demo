const { chromium } = require('playwright')
const assert = require('assert')
const fs = require('fs')

;(async () => {
  const output = process.env.YH_MEMBER_BROWSER_OUTPUT
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()
  const errors = []
  const failed = []
  const events = []
  const requests = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('requestfailed', request => failed.push({ url: request.url(), error: request.failure()?.errorText }))
  page.on('request', request => {
    const url = new URL(request.url())
    if (url.pathname.startsWith('/admin-api/member/')) requests.push({ method: request.method(), path: url.pathname })
  })
  page.on('response', response => {
    const url = new URL(response.url())
    if (url.pathname.startsWith('/admin-api/member/')) {
      events.push({ method: response.request().method(), path: url.pathname, status: response.status() })
    }
  })
  const result = { errors, failed, events, requests, actions: [] }
  try {
    await page.goto('http://127.0.0.1:5203/login', { waitUntil: 'domcontentloaded' })
    await page.locator('input[placeholder="请输入用户名"]:visible').waitFor({ timeout: 30000 })
    await page.locator('input[placeholder="请输入用户名"]:visible').fill(process.env.YH_MEMBER_USERNAME)
    await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YH_MEMBER_PASSWORD)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })
    await page.goto('http://127.0.0.1:5203/member/tag', { waitUntil: 'domcontentloaded' })
    const filter = page.locator('input[placeholder="请输入标签名称"]:visible').first()
    await filter.waitFor({ timeout: 30000 })
    const rows = page.locator('.el-table__body-wrapper tbody tr')
    await page.waitForFunction(() => !document.querySelector('.el-loading-mask:not([style*="display: none"])'), null,
      { timeout: 30000 }).catch(() => {})
    const marker = 'P2 UI tag ' + Date.now()
    await filter.fill(marker)
    await page.getByRole('button', { name: '搜索' }).click()
    const createButton = page.getByRole('button', { name: /新增/ }).first()
    await createButton.click()
    let dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    const field = dialog.locator('input[placeholder="请输入标签名称"]')
    await field.fill(marker)
    const createResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/member/tag/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await createResponse).status(), 200)
    result.actions.push('create')
    let row = rows.filter({ hasText: marker })
    await row.waitFor({ timeout: 15000 })
    await row.getByRole('button', { name: '编辑' }).click()
    dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    const editField = dialog.locator('input[placeholder="请输入标签名称"]')
    await page.waitForFunction(({ selector, value }) => document.querySelector(selector)?.value === value,
      { selector: '.el-dialog input[placeholder="请输入标签名称"]', value: marker }, { timeout: 15000 })
    const confirm = dialog.getByRole('button', { name: '确 定' })
    await confirm.waitFor({ state: 'visible', timeout: 15000 })
    await page.waitForFunction(() => {
      const button = [...document.querySelectorAll('.el-dialog button')]
        .find(element => element.textContent.trim() === '确 定')
      return button && !button.disabled
    }, null, { timeout: 15000 })
    await editField.fill(marker + ' edited')
    await confirm.click()
    await page.waitForFunction(() => !document.querySelector('.el-dialog'), null, { timeout: 15000 })
    assert(requests.some(event => event.path === '/admin-api/member/tag/update'), requests)
    result.actions.push('update')
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    await page.reload({ waitUntil: 'domcontentloaded' })
    await filter.waitFor({ timeout: 15000 })
    row = rows.filter({ hasText: marker + ' edited' })
    await row.waitFor({ timeout: 15000 })
    const deleteResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/member/tag/delete')
    await row.getByRole('button', { name: '删除' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await deleteResponse).status(), 200)
    result.actions.push('delete')
    await row.waitFor({ state: 'detached', timeout: 15000 })

    await page.goto('http://127.0.0.1:5203/member/user', { waitUntil: 'domcontentloaded' })
    const nickname = page.locator('input[placeholder="请输入用户昵称"]:visible')
    await nickname.waitFor({ timeout: 30000 })
    await nickname.fill('P2 member updated')
    await page.getByRole('button', { name: '搜索' }).click()
    let memberRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 member updated' })
    await memberRow.waitFor({ timeout: 15000 })
    assert((await memberRow.innerText()).includes('990951'), 'isolated member fixture not found')
    result.actions.push('member-search')

    await memberRow.getByRole('button', { name: '更多' }).click()
    await page.getByRole('menuitem', { name: '修改积分' }).click()
    dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    await page.waitForFunction(() => {
      const dialog = [...document.querySelectorAll('.el-dialog')].find(element => element.offsetHeight)
      return dialog?.querySelector('.el-input-number input')?.value === '15'
    }, null, { timeout: 15000 })
    await dialog.locator('.el-radio').filter({ hasText: '减少' }).click()
    const pointInput = dialog.locator('.el-input-number input').nth(1)
    await pointInput.fill('2')
    await pointInput.press('Tab')
    assert((await dialog.locator('.el-input-number input').nth(2).inputValue()) === '13',
      'calculated member point should be 13')
    const pointResponse = page.waitForResponse(response =>
      new URL(response.url()).pathname === '/admin-api/member/user/update-point')
    await dialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await pointResponse).status(), 200)
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    memberRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 member updated' })
    await page.waitForFunction(() => {
      const row = [...document.querySelectorAll('.el-table__body-wrapper tbody tr')]
        .find(element => element.innerText.includes('P2 member updated'))
      return row?.innerText.includes('13')
    }, null, { timeout: 15000 })
    result.actions.push('member-point-decrease')

    assert.deepStrictEqual(result.actions,
      ['create', 'update', 'delete', 'member-search', 'member-point-decrease'])
    assert.deepStrictEqual(errors, [])
    assert.deepStrictEqual(failed, [])
    result.completed = true
  } finally {
    fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n')
    await context.close()
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
