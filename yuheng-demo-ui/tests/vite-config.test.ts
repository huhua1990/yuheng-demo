import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { createServer } from 'vite'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

const viteConfig = readFileSync(new URL('../vite.config.ts', import.meta.url), 'utf8')
const require = createRequire(import.meta.url)
const coreFormRules = resolve(dirname(require.resolve('yuheng-ui/compat/platform')), 'utils/formRules.ts')

let server: Awaited<ReturnType<typeof createServer>>

beforeAll(async () => {
  server = await createServer({
    configFile: new URL('../vite.config.ts', import.meta.url).pathname,
    configFileDependencies: [],
    server: { middlewareMode: true },
    appType: 'custom'
  })
})

afterAll(async () => {
  await server?.close()
})

describe('Vite compatibility module transforms', () => {
  it('keeps auto-import dependent Core modules out of dependency pre-bundling', () => {
    expect(viteConfig).toMatch(/optimizeDeps\s*:\s*\{[^}]*exclude\s*:[^}]*['"]yuheng-ui['"]/s)
    expect(viteConfig).toMatch(/optimizeDeps\s*:\s*\{[^}]*exclude\s*:[^}]*['"]yuheng-ui\/compat\/utils\/formRules['"]/s)
  })

  it('injects Core auto-imports into files resolved through the package symlink', async () => {
    expect(viteConfig).toContain('.pnpm')
    expect(viteConfig).toContain('node_modules')
    expect(viteConfig).toContain('yuheng-ui')
    expect(viteConfig).toContain('compat')

    const transformed = await server.transformRequest(`/@fs${coreFormRules}`)

    expect(transformed?.code).toMatch(/^import\s*\{\s*useI18n\s*\}[^\n]*\nconst\s*\{\s*t\s*\}\s*=\s*useI18n\(\)/)
  })
})
