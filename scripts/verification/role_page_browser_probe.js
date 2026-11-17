const { chromium } = require('playwright')
const fs = require('fs')
const assert = require('assert')

const base = process.env.YH_BROWSER_BASE
const output = process.env.YH_BROWSER_OUTPUT
const result = { base, viewports: {}, consoleErrors: [], pageErrors: [], requestFailed: [], writes: [] }

async function inspectViewport(browser, width, height, label) {
  const context = await browser.newContext({ viewport: { width, height } })
  const page = await context.newPage()
  page.on('pageerror', error => result.pageErrors.push({ label, message: error.message }))
  page.on('console', message => {
    if (message.type() === 'error') result.consoleErrors.push({ label, message: message.text() })
  })
  page.on('requestfailed', request => result.requestFailed.push({
    label, path: new URL(request.url()).pathname, failure: request.failure()?.errorText
  }))
  page.on('request', request => {
    const path = new URL(request.url()).pathname
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(request.method()) && path.startsWith('/admin-api/system/role')) {
      result.writes.push({ label, method: request.method(), path })
    }
  })
  try {
    await page.goto(`${base}/login?redirect=/system/role`, { waitUntil: 'domcontentloaded' })
    const user = page.locator('input[placeholder="请输入用户名"]')
    await user.waitFor({ state: 'visible', timeout: 30000 })
    await user.fill(process.env.YH_BROWSER_USERNAME)
    await page.locator('input[placeholder="请输入密码"]:visible').fill(process.env.YH_BROWSER_PASSWORD)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 })
    await page.goto(`${base}/system/role`, { waitUntil: 'domcontentloaded' })
    await page.getByPlaceholder('请输入角色名称').waitFor({ timeout: 30000 })
    const rows = page.locator('.el-table__body-wrapper tbody tr')
    await rows.first().waitFor({ timeout: 30000 })

    const initial = await page.evaluate(() => ({
      viewport: innerWidth,
      document: { clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth },
      rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length,
      visibleText: document.body.innerText.includes('角色管理')
    }))
    result.viewports[label] = { initial }

    const newButton = page.getByRole('button', { name: /新增/ }).first()
    await page.keyboard.press('Escape').catch(() => {})
    await page.mouse.move(width - 5, height - 5)
    await page.waitForTimeout(500)
    const overlay = page.locator('.v-layout > .opacity-30')
    if (await overlay.isVisible().catch(() => false)) {
      await overlay.click({ position: { x: Math.max(1, width - 10), y: Math.max(1, height - 10) } })
      await overlay.waitFor({ state: 'detached', timeout: 10000 })
    }
    await page.mouse.move(width - 5, height - 5)
    await page.mouse.click(Math.max(1, width - 10), Math.max(1, height - 10))
    await page.waitForTimeout(300)
    result.viewports[label].beforeClick = await newButton.evaluate(element => {
      const rect = element.getBoundingClientRect()
      const x = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2))
      const y = Math.max(0, Math.min(innerHeight - 1, rect.top + rect.height / 2))
      const hit = document.elementFromPoint(x, y)
      const menu = document.querySelector('.v-menu')
      const menuRect = menu?.getBoundingClientRect()
      return {
        button: { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom },
        point: { x, y },
        hit: hit ? { tag: hit.tagName, className: hit.className, text: hit.textContent?.trim().slice(0, 100) } : null,
        menu: menuRect ? { left: menuRect.left, right: menuRect.right, width: menuRect.width } : null,
        overlayVisible: !!document.querySelector('.v-layout > .opacity-30')
      }
    })
    await page.screenshot({ path: `${output}-${label}-before-click.png` })
    assert.strictEqual(result.viewports[label].beforeClick.hit?.text, '新增')
    await newButton.click()
    const dialog = page.locator('.el-dialog:visible')
    await dialog.waitFor({ timeout: 15000 })
    const form = dialog.getByPlaceholder('请输入角色名称')
    await form.fill('browser cancel probe')
    const geometry = await dialog.evaluate(element => {
      const rect = element.getBoundingClientRect()
      const input = element.querySelector('input[placeholder="请输入角色名称"]')?.getBoundingClientRect()
      const footer = element.querySelector('.el-dialog__footer')?.getBoundingClientRect()
      return {
        dialog: { left: rect.left, right: rect.right, width: rect.width, scrollWidth: element.scrollWidth },
        input: input ? { left: input.left, right: input.right, width: input.width } : null,
        footer: footer ? { left: footer.left, right: footer.right } : null,
        viewport: document.documentElement.clientWidth
      }
    })
    result.viewports[label].dialog = geometry
    await dialog.getByRole('button', { name: '取 消' }).click()
    await dialog.waitFor({ state: 'hidden', timeout: 15000 })
    result.viewports[label].cancelWrites = result.writes.filter(item => item.label === label).length
    assert.strictEqual(result.viewports[label].cancelWrites, 0)
    assert(geometry.dialog.right <= geometry.viewport + 1)
    assert(geometry.input && geometry.input.width >= 100)
    if (width >= 768) {
      const collapse = page.locator('#v-tool-header .v-collapse').first()
      await collapse.click()
      const menu = page.locator('.v-menu .el-menu--collapse').first()
      await menu.waitFor({ state: 'visible', timeout: 10000 })
      const system = menu.locator(':scope > .el-sub-menu').filter({ hasText: '系统管理' }).first()
      await system.locator(':scope > .el-sub-menu__title').hover()
      const popup = page.locator('.v-menu-popper--vertical:visible').filter({ hasText: '角色管理' }).first()
      await popup.waitFor({ state: 'visible', timeout: 10000 })
      result.viewports[label].collapsedHoverShowsRole = true
      await page.mouse.move(width - 5, height - 5)
      await collapse.click()
      const activeRole = page.locator('.v-menu .el-menu-item.is-active').filter({ hasText: '角色管理' }).first()
      await activeRole.waitFor({ state: 'visible', timeout: 10000 })
      result.viewports[label].expandedActiveRoleVisible = true
    }
  } finally {
    await context.close()
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
  try {
    for (const [width, height, label] of [[1440, 900, 'desktop-1440x900'], [390, 844, 'mobile-390x844'], [320, 844, 'mobile-320x844']]) {
      try { await inspectViewport(browser, width, height, label) }
      catch (error) { result.errors = result.errors || {}; result.errors[label] = error.stack }
    }
    assert.deepStrictEqual(result.errors || {}, {})
    assert.deepStrictEqual(result.consoleErrors, [])
    assert.deepStrictEqual(result.pageErrors, [])
    assert.deepStrictEqual(result.requestFailed, [])
    result.completed = true
  } finally {
    fs.writeFileSync(`${output}.json`, JSON.stringify(result, null, 2) + '\n')
    await browser.close()
  }
})().catch(error => { console.error(error); process.exitCode = 1 })
