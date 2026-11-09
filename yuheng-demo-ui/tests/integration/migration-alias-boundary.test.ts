import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

function walk(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const file = join(directory, entry)
    return statSync(file).isDirectory() ? walk(file) : [file]
  })
}

describe('migrated source alias boundary', () => {
  it('keeps core compat free of business API/view/store aliases', () => {
    const root = fileURLToPath(new URL('../../../../yuheng-core/yuheng-ui/compat', import.meta.url))
    const violations = walk(root)
      .filter((file) => /\.(?:ts|tsx|vue)$/.test(file))
      .flatMap((file) => readFileSync(file, 'utf8').split(/\r?\n/).map((line, index) => ({ file, index, line })))
      .filter(({ line }) => /from ['"]@\/(?:api|views|store)\/(?:ai|ai1|bpm|crm|erp|fms|hrm|im|iot|mall|member|mes|mp|oa|pay|pms|report|wms)\//.test(line))
      .map(({ file, index, line }) => `${relative(fileURLToPath(new URL('../../../..', import.meta.url)), file)}:${index + 1}: ${line.trim()}`)
    expect(violations).toEqual([])
  })

  it('keeps demo views free of generic platform aliases and reports business store aliases', () => {
    const root = fileURLToPath(new URL('../../src', import.meta.url))
    const violations = walk(root)
      .filter((file) => /\.(?:ts|tsx|vue)$/.test(file))
      .flatMap((file) => readFileSync(file, 'utf8').split(/\r?\n/).map((line, index) => ({ file, index, line })))
      .filter(({ line }) => /from ['"]@\/(?:config\/axios|router|store\/(?:modules\/(?:user|permission|dict|tenant)|index)|views\/(?:system|infra))/.test(line))
      .map(({ file, index, line }) => `${relative(fileURLToPath(new URL('../..', import.meta.url)), file)}:${index + 1}: ${line.trim()}`)
    expect(violations).toEqual([])
  })

  it('quarantines migrated business stores under demo-owned store paths', () => {
    const root = fileURLToPath(new URL('../../src/store/modules', import.meta.url))
    expect(existsSync(join(root, 'mall/kefu.ts'))).toBe(true)
    expect(readFileSync(join(root, 'mall/kefu.ts'), 'utf8')).not.toMatch(/yuheng-ui\/src|yuheng-core\//)
  })
})
