import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { parse, compileTemplate } from '@vue/compiler-sfc'
import { describe, expect, it } from 'vitest'

const root = fileURLToPath(new URL('../..', import.meta.url))
const workspace = resolve(root, '../..')
const core = join(workspace, 'yuheng-core/yuheng-ui')
const upstream = join(workspace, 'yudao-ui-admin-vue3/src')
const businessAsset = /^assets\/(?:ai\/|audio\/|map\/|imgs\/(?:diy\/|iot\/|profile\.jpg$|wechat\.png$)|svgs\/(?:bpm\/|iot\/|pay\/|member_[^/]+\.svg$|send\.svg$))/
const rows = readFileSync(join(core, 'docs/admin-ui-migration-inventory.ndjson'), 'utf8').trim().split(/?
/).map((line) => JSON.parse(line) as { source: string; owner: string; destination: string | null })
function walk(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const file = join(directory, entry.name)
    return entry.isDirectory() ? walk(file) : [file]
  })
}
const hash = (file: string) => createHash('sha256').update(readFileSync(file)).digest('hex')

describe('consumer-owned business static assets', () => {
  it('moves every one of 51 business assets out of core without changing bytes', () => {
    const assets = rows.filter((row) => businessAsset.test(row.source))
    expect(assets).toHaveLength(51)
    const violations: string[] = []
    for (const row of assets) {
      const local = join(root, 'src', row.source)
      if (row.owner !== 'demo' || row.destination !== `yuheng-demo/yuheng-demo-ui/src/${row.source}`) violations.push(`${row.source}: wrong owner or destination`)
      if (!existsSync(local)) violations.push(`${row.source}: missing demo asset`)
      else if (hash(local) !== hash(join(upstream, row.source))) violations.push(`${row.source}: changed bytes`)
      if (existsSync(join(core, 'compat', row.source))) violations.push(`${row.source}: still in core`)
    }
    expect(violations).toEqual([])
  })

  it('resolves every migrated asset reference in scripts, templates and styles', () => {
    const violations: string[] = []
    const assets = walk(join(root, 'src')).filter((file) => /\.(?:vue|[cm]?[jt]sx?|scss|css)$/.test(file))
    for (const file of assets) {
      const content = readFileSync(file, 'utf8')
      for (const match of content.matchAll(/(?:['"(])(@\/assets\/[^'"\s)]+|yuheng-ui\/compat\/assets\/[^'"\s)]+)/g)) {
        const specifier = match[1]
        const target = specifier.startsWith('@/') ? join(root, 'src', specifier.slice(2)) : join(core, specifier.slice('yuheng-ui/'.length))
        if (!existsSync(target)) violations.push(`${relative(root, file)}: missing ${specifier}`)
        if (specifier.startsWith('yuheng-ui/compat/') && businessAsset.test(specifier.slice('yuheng-ui/compat/'.length))) violations.push(`${relative(root, file)}: business asset through core ${specifier}`)
      }
      if (/svg-icon:(?:member_|send)/.test(content)) violations.push(`${relative(root, file)}: business sprite needs consumer registration`)
    }
    expect(violations).toEqual([])
  })

  it('preserves consumer-local SVG rendering for member labels and BPM copy actions', () => {
    const member = join(root, 'src/views/member/user/detail/UserAccountInfo.vue')
    const bpm = join(root, 'src/views/bpm/processInstance/detail/ProcessInstanceOperationButton.vue')
    const content = readFileSync(member, 'utf8')
    for (const name of ['member_level', 'member_balance', 'member_expenditure_balance', 'member_recharge_balance']) {
      expect(content, name).toContain(`@/assets/svgs/${name}.svg`)
    }
    expect(readFileSync(bpm, 'utf8')).toContain('@/assets/svgs/send.svg')
    for (const file of [member, bpm]) {
      const { descriptor, errors } = parse(readFileSync(file, 'utf8'), { filename: file })
      expect(errors).toEqual([])
      const template = compileTemplate({ source: descriptor.template!.content, filename: file, id: 'asset-boundary' })
      expect(template.errors).toEqual([])
    }
  })
})
