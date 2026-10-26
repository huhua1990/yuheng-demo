import { describe, expect, it } from 'vitest'
import { installYuhengUi, registerPlatformRoutes, YuhengShell } from 'yuheng-ui'

describe('yuheng-demo-ui entry', () => {
  it('uses the public yuheng-ui entry', () => {
    expect(installYuhengUi).toBeTypeOf('function')
    expect(registerPlatformRoutes).toBeTypeOf('function')
    expect(YuhengShell).toBeDefined()
  })
})
