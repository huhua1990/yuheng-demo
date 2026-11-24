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
    if (url.pathname.startsWith('/admin-api/')) requests.push({ method: request.method(), path: url.pathname })
  })
  page.on('response', response => {
    const url = new URL(response.url())
    if (url.pathname.startsWith('/admin-api/member/')) {
      events.push({ method: response.request().method(), path: url.pathname, status: response.status() })
    }
  })
  const result = { errors, failed, events, requests, actions: [], pageStates: [] }
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
      return dialog?.querySelector('.el-input-number input')?.value === '19'
    }, null, { timeout: 15000 })
    await dialog.locator('.el-radio').filter({ hasText: '减少' }).click()
    const memberPointInput = dialog.locator('.el-input-number input').nth(1)
    await memberPointInput.fill('2')
    await memberPointInput.press('Tab')
    assert((await dialog.locator('.el-input-number input').nth(2).inputValue()) === '17',
      'calculated member point should be 17')
    const pointResponse = page.waitForResponse(response =>
      new URL(response.url()).pathname === '/admin-api/member/user/update-point')
    await dialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await pointResponse).status(), 200)
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    memberRow = page.locator('.el-table__body-wrapper tbody tr').filter({ hasText: 'P2 member updated' })
    await page.waitForFunction(() => {
      const row = [...document.querySelectorAll('.el-table__body-wrapper tbody tr')]
        .find(element => element.innerText.includes('P2 member updated'))
      return row?.innerText.includes('17')
    }, null, { timeout: 15000 })
    result.actions.push('member-point-decrease')

    await page.goto('http://127.0.0.1:5203/member/user/detail/990951', { waitUntil: 'domcontentloaded' })
    await page.getByText('账户明细', { exact: true }).waitFor({ timeout: 30000 })
    for (const name of ['签到', '成长值', '收货地址']) {
      await page.getByRole('tab', { name, exact: true }).click()
      await page.waitForTimeout(600)
    }
    for (const name of ['余额', '订单管理', '售后管理', '收藏记录', '优惠劵', '推广用户']) {
      assert.strictEqual(await page.getByRole('tab', { name, exact: true }).count(), 0, name)
    }
    const account = page.locator('.el-card').filter({ hasText: '账户信息' }).locator('.el-descriptions')
    for (const name of ['等级', '成长值', '当前积分', '总积分']) {
      assert((await account.innerText()).includes(name), name)
    }
    for (const name of ['当前余额', '支出金额', '充值金额']) {
      assert(!(await account.innerText()).includes(name), name)
    }
    assert(!requests.some(({ path }) => /^\/admin-api\/(pay|product|trade|promotion)\//.test(path)), requests)
    result.actions.push('member-detail-optional-disabled')

    if (process.env.YH_MEMBER_DETAIL_DIAGNOSTIC === '1') {
      const detailResponses = []
      page.on('response', response => {
        const url = new URL(response.url())
        if (url.pathname.startsWith('/admin-api/')) {
          detailResponses.push({ path: url.pathname, status: response.status() })
        }
      })
      await page.goto('http://127.0.0.1:5203/member/user/detail/990951', { waitUntil: 'domcontentloaded' })
      await page.getByText('账户明细', { exact: true }).waitFor({ timeout: 30000 })
      await page.waitForTimeout(1500)
      result.detail = { initial: detailResponses.slice(), tabs: [] }
      for (const name of ['签到', '成长值', '收货地址', '订单管理', '售后管理', '收藏记录', '优惠劵', '推广用户', '余额']) {
        const start = detailResponses.length
        await page.getByRole('tab', { name, exact: true }).click()
        await page.waitForTimeout(1200)
        result.detail.tabs.push({ name, responses: detailResponses.slice(start) })
      }
    }

    const pageChecks = [
      { route: '/member/group', api: '/admin-api/member/group/page' },
      { route: '/member/level', api: '/admin-api/member/level/list' },
      { route: '/member/record', api: '/admin-api/member/point/record/page', menu: ['会员积分'] },
      { route: '/member/sign-in-config', api: '/admin-api/member/sign-in/config/list', menu: ['会员签到', '签到配置'] },
      { route: '/member/sign-in-record', api: '/admin-api/member/sign-in/record/page', menu: ['会员签到', '签到记录'] },
      { route: '/member/config', api: '/admin-api/member/config/get' }
    ]
    for (const check of pageChecks) {
      const response = page.waitForResponse(r => new URL(r.url()).pathname === check.api)
      if (check.menu) {
        for (const menuItem of check.menu) {
          await page.getByText(menuItem, { exact: true }).last().click()
        }
      } else {
        await page.goto(`http://127.0.0.1:5203${check.route}`, { waitUntil: 'domcontentloaded' })
      }
      await page.waitForTimeout(500)
      result.pageStates.push({ route: new URL(page.url()).pathname, url: page.url(), title: await page.locator('body').innerText().then(text => text.slice(0, 160)) })
      assert.strictEqual((await response).status(), 200, `${check.route} failed to load ${check.api}`)
      result.actions.push(`page:${check.route}`)
    }

    await page.goto('http://127.0.0.1:5203/member/signin/config', { waitUntil: 'domcontentloaded' })
    await page.waitForResponse(r => new URL(r.url()).pathname === '/admin-api/member/sign-in/config/list')
    await page.getByRole('button', { name: /新增/ }).first().click()
    dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    const dayInput = dialog.locator('.el-input-number input').nth(0)
    const signInPointInput = dialog.locator('.el-input-number input').nth(1)
    const experienceInput = dialog.locator('.el-input-number input').nth(2)
    await dayInput.fill('7')
    await dayInput.press('Tab')
    await signInPointInput.fill('23')
    await signInPointInput.press('Tab')
    await experienceInput.fill('6')
    await experienceInput.press('Tab')
    const createSignInResponse = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/admin-api/member/sign-in/config/create')
    await dialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await createSignInResponse).status(), 200)
    const signInCreated = await createSignInResponse.then(response => response.json())
    const signInConfigId = signInCreated.data
    assert(signInConfigId, signInCreated)
    result.signInConfigId = signInConfigId
    result.actions.push('sign-in-config-create')
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    let signInRow = page.locator('.el-table__body-wrapper tbody tr')
      .filter({ hasText: '第 7 天' }).filter({ hasText: '23' }).filter({ hasText: '6' })
    await signInRow.waitFor({ timeout: 15000 })

    const signInDetailResponse = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/admin-api/member/sign-in/config/get')
    await signInRow.getByRole('button', { name: '编辑' }).click()
    dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    await signInDetailResponse
    await page.waitForFunction(() => {
      const dialog = [...document.querySelectorAll('.el-dialog')].find(element => element.offsetHeight)
      return dialog?.querySelectorAll('.el-input-number input')[1]?.value === '23'
    }, null, { timeout: 15000 })
    const signInPointEdit = dialog.locator('.el-input-number input').nth(1)
    await signInPointEdit.fill('24')
    await signInPointEdit.press('Tab')
    await page.waitForFunction(() => {
      const dialog = [...document.querySelectorAll('.el-dialog')].find(element => element.offsetHeight)
      return dialog?.querySelectorAll('.el-input-number input')[1]?.value === '24'
    }, null, { timeout: 5000 })
    const signInListRefresh = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/admin-api/member/sign-in/config/list')
    const updateSignInResponse = page.waitForResponse(async response => {
      if (new URL(response.url()).pathname !== '/admin-api/member/sign-in/config/update') return false
      const event = {
        method: response.request().method(),
        path: new URL(response.url()).pathname,
        status: response.status(),
        requestBody: response.request().postDataJSON(),
        responseBody: await response.json()
      }
      result.events.push(event)
      return true
    })
    await dialog.getByRole('button', { name: '确 定' }).click()
    assert.strictEqual((await updateSignInResponse).status(), 200)
    assert.strictEqual(result.events.findLast(event => event.path === '/admin-api/member/sign-in/config/update').requestBody.point, 24)
    result.actions.push('sign-in-config-update')
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    await signInListRefresh
    signInRow = page.locator('.el-table__body-wrapper tbody tr')
      .filter({ hasText: '第 7 天' }).filter({ hasText: '6' })
    await signInRow.waitFor({ timeout: 15000 })
    assert((await signInRow.innerText()).includes('24'), await signInRow.innerText())

    const deleteSignInResponse = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/admin-api/member/sign-in/config/delete')
    await signInRow.getByRole('button', { name: '删除' }).click()
    await page.locator('.el-message-box:visible').getByRole('button', { name: '确定' }).click()
    assert.strictEqual((await deleteSignInResponse).status(), 200)
    result.actions.push('sign-in-config-delete')
    await signInRow.waitFor({ state: 'detached', timeout: 15000 })

    assert.deepStrictEqual(result.actions, [
      'create', 'update', 'delete', 'member-search', 'member-point-decrease', 'member-detail-optional-disabled',
      ...pageChecks.map(({ route }) => `page:${route}`),
      'sign-in-config-create', 'sign-in-config-update', 'sign-in-config-delete'
    ])
    assert.deepStrictEqual(errors, [])
    assert.deepStrictEqual(failed, [])
    result.completed = true
  } finally {
    fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n')
    await context.close()
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
