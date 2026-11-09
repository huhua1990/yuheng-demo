import { describe, expect, it } from 'vitest'
import { installYuhengUi, registerPlatformRoutes, YuhengShell } from 'yuheng-ui'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

describe('yuheng-demo-ui entry', () => {
  it('uses the public yuheng-ui entry', () => {
    expect(installYuhengUi).toBeTypeOf('function')
    expect(registerPlatformRoutes).toBeTypeOf('function')
    expect(YuhengShell).toBeDefined()
  })

  it('connects the installed platform runtime to the consumer router', () => {
    const entry = readFileSync(fileURLToPath(new URL('../src/main.ts', import.meta.url)), 'utf8')
    expect(entry).toMatch(/const runtime\s*=\s*installYuhengUi/)
    expect(entry).toContain('runtime.registerRoutes(router)')
    expect(entry).not.toContain('registerPlatformRoutes(router)')
  })

  it('serves the consumer UI locally and proxies API requests to the backend', () => {
    const viteConfig = readFileSync(fileURLToPath(new URL('../vite.config.ts', import.meta.url)), 'utf8')
    expect(viteConfig).toContain("host: '127.0.0.1'")
    expect(viteConfig).toContain('port: 3000')
    expect(viteConfig).toContain("'/admin-api':")
    expect(viteConfig).toContain("env.VITE_BACKEND_ORIGIN ?? 'http://127.0.0.1:48080'")
  })

  it('enables tenant headers to match the local backend profile', () => {
    const entry = readFileSync(fileURLToPath(new URL('../src/main.ts', import.meta.url)), 'utf8')
    expect(entry).toContain('tenantEnabled')
    const envExample = readFileSync(
      fileURLToPath(new URL('../.env.local.example', import.meta.url)),
      'utf8'
    )
    expect(envExample).toContain('VITE_APP_TENANT_ENABLE=true')
  })
})
