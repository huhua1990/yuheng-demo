import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

describe('yuheng-demo-ui package boundary', () => {
  const packageJson = JSON.parse(
    readFileSync(fileURLToPath(new URL('../package.json', import.meta.url)), 'utf8')
  )

  it('consumes the platform as a versioned package dependency', () => {
    expect(packageJson.dependencies['yuheng-ui']).toBeTypeOf('string')
    expect(packageJson.dependencies['yuheng-ui']).not.toMatch(/(?:^|\/)src(?:\/|$)/)
    expect(packageJson.dependencies['yuheng-ui']).not.toContain('../../yuheng-core')
  })

  it('declares the integration package artifact without source or repository paths', () => {
    const dependency = packageJson.dependencies['yuheng-ui']
    expect(dependency).toMatch(/^file:vendor\/yuheng-ui-.*\.tgz$/)
    expect(dependency).not.toContain('src/')
    expect(dependency).not.toContain('../../yuheng-core')
  })

  it('does not import platform internals outside public exports', () => {
    const violations: string[] = []
    const walk = (directory: string) => {
      for (const entry of readdirSync(directory)) {
        const path = join(directory, entry)
        if (statSync(path).isDirectory()) walk(path)
        else {
          const content = readFileSync(path, 'utf8')
          content.split(/\r?\n/).forEach((line, index) => {
            if (line.includes('yuheng-ui/src/') || line.includes('yuheng-core/')) {
              violations.push(`${relative(process.cwd(), path)}:${index + 1}: ${line.trim()}`)
            }
          })
        }
      }
    }
    walk(fileURLToPath(new URL('../src', import.meta.url)))
    expect(violations).toEqual([])
  })
})
