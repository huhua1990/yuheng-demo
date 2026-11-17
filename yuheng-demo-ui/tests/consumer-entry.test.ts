import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { installYuhengUi, registerPlatformRoutes, YuhengShell } from 'yuheng-ui'

const mainSource = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8')
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')) as {
  dependencies?: Record<string, string>
  devDependencies?: Record<string, string>
}

describe('yuheng-demo-ui entry', () => {
  it('consumes a versioned yuheng-ui package contract', () => {
    const version = packageJson.dependencies?.['yuheng-ui']
    expect(version).toBe('0.1.0-SNAPSHOT')
    expect(version).not.toMatch(/^workspace:/)
  })

  it('declares direct runtime imports used by the demo UI', () => {
    for (const dependency of ['@iconify/vue', '@iconify/json', 'echarts', 'lodash-es']) {
      expect(packageJson.dependencies?.[dependency]).toBeTypeOf('string')
    }
  })

  it('declares lodash-es type definitions for package consumers', () => {
    expect(packageJson.devDependencies?.['@types/lodash-es']).toBeTypeOf('string')
  })

  it('uses the public yuheng-ui entry', () => {
    expect(installYuhengUi).toBeTypeOf('function')
    expect(registerPlatformRoutes).toBeTypeOf('function')
    expect(YuhengShell).toBeDefined()
  })

  it('registers the Core Iconify collections required by compatibility views', () => {
    expect(mainSource).toContain("import { addCollection } from '@iconify/vue'")
    expect(mainSource).toContain("import epIcons from '@iconify/json/json/ep.json'")
    expect(mainSource).toContain('addCollection(epIcons)')
    expect(mainSource).toContain('addCollection(faIcons)')
    expect(mainSource).toContain('addCollection(faSolidIcons)')
  })

  it('enables tenant-aware login for the tenant-enforced backend', () => {
    expect(mainSource).toMatch(/installYuhengUi\(app,\s*\{[\s\S]*tenantEnabled:\s*true/)
  })

  it('defaults the login tenant to the seeded platform tenant', () => {
    const env = readFileSync(new URL('../.env', import.meta.url), 'utf8')
    expect(env).toMatch(/^VITE_APP_DEFAULT_LOGIN_TENANT=芋道源码$/m)
  })

  it('installs the runtime navigation guard for permission menus and direct links', () => {
    expect(mainSource).toMatch(/(?:const|let)\s+(\w+)\s*=\s*installYuhengUi\(app,[\s\S]*?\1\.registerRoutes\(router\)/)
  })

  it('uses the complete platform layout and resolves backend menus to complete views', () => {
    expect(mainSource).toContain('completePlatformRoutes')
    expect(mainSource).toContain('platformViewComponents')
    expect(mainSource).toContain('setupCompletePlatform')
    expect(mainSource).toMatch(/resolveComponent\s*:/)
  })

  it('does not replace Core components when registering additional compat components', () => {
    expect(mainSource).toMatch(/if\s*\(!app\.component\('DocAlert'\)\)\s*app\.component\('DocAlert',\s*DocAlert\)/)
    expect(mainSource).toMatch(/if\s*\(!app\.component\('DictTag'\)\)\s*app\.component\('DictTag',\s*DictTag\)/)
    expect(mainSource).not.toMatch(/app\.component\('(?:Pagination|ContentWrap|ContentDetailWrap|Dialog)'/)
  })

  it('resolves copied demo business views separately from platform views', () => {
    expect(mainSource).toContain('businessViewComponents')
    expect(mainSource).toContain('businessViewComponents[')
    expect(mainSource).toContain('...businessViewComponents')
  })
})
