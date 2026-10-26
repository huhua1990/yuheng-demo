import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../src', import.meta.url))
const patterns = [
  'yuheng-ui/src/',
  '@/config/axios',
  '@/router',
  '@/store',
  '@/views/system',
  '@/views/infra'
]
const violations = []
function walk(directory) {
  for (const entry of readdirSync(directory)) {
    const file = join(directory, entry)
    const stat = statSync(file)
    if (stat.isDirectory()) walk(file)
    else if (stat.isFile()) {
      readFileSync(file, 'utf8').split(/\r?\n/).forEach((line, index) => {
        if (patterns.some((pattern) => line.includes(pattern))) {
          violations.push(`${relative(root, file)}:${index + 1}: ${line.trim()}`)
        }
      })
    }
  }
}
walk(root)
if (violations.length) {
  console.error('yuheng-demo-ui platform import boundary: FAIL')
  console.error(violations.join('\n'))
  process.exit(1)
}
console.log('yuheng-demo-ui platform import boundary: PASS')
