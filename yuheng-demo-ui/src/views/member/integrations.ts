export type MemberIntegrationName = 'pay' | 'product' | 'trade' | 'promotion'

export type MemberIntegrationConfig = Record<string, unknown>

export type MemberIntegrations = Record<MemberIntegrationName, boolean>

export const memberIntegrationConfig: MemberIntegrationConfig = {
  VITE_MEMBER_ENABLE_PAY: import.meta.env.VITE_MEMBER_ENABLE_PAY,
  VITE_MEMBER_ENABLE_PRODUCT: import.meta.env.VITE_MEMBER_ENABLE_PRODUCT,
  VITE_MEMBER_ENABLE_TRADE: import.meta.env.VITE_MEMBER_ENABLE_TRADE,
  VITE_MEMBER_ENABLE_PROMOTION: import.meta.env.VITE_MEMBER_ENABLE_PROMOTION
}

const enabled = (config: MemberIntegrationConfig, name: MemberIntegrationName) =>
  String(config[`VITE_MEMBER_ENABLE_${name.toUpperCase()}`] ?? '').toLowerCase() === 'true'

export const resolveMemberIntegrations = (
  config: MemberIntegrationConfig = memberIntegrationConfig
): MemberIntegrations => ({
  pay: enabled(config, 'pay'),
  product: enabled(config, 'product'),
  trade: enabled(config, 'trade'),
  promotion: enabled(config, 'promotion')
})
