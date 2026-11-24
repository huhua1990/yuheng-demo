import { describe, expect, it } from 'vitest'
import { resolveMemberIntegrations } from '../src/views/member/integrations'

describe('optional member business integrations', () => {
  it('leaves all optional business modules disabled for a member-only consumer', () => {
    expect(resolveMemberIntegrations({})).toEqual({ pay: false, product: false, trade: false, promotion: false })
  })

  it.each(['pay', 'product', 'trade', 'promotion'] as const)('enables only the selected %s module', (module) => {
    const result = resolveMemberIntegrations({ [`VITE_MEMBER_ENABLE_${module.toUpperCase()}`]: 'true' })
    for (const key of ['pay', 'product', 'trade', 'promotion'] as const) {
      expect(result[key]).toBe(key === module)
    }
  })

  it('does not treat arbitrary values as enabled', () => {
    expect(resolveMemberIntegrations({ VITE_MEMBER_ENABLE_PAY: '1' })).toEqual({
      pay: false,
      product: false,
      trade: false,
      promotion: false
    })
  })
})
