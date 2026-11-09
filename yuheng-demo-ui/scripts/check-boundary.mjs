import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../src', import.meta.url))
const patterns = [
  /yuheng-ui\/src\//,
  /yuheng-core\//,
  /from ['"]yudao-ui-admin-vue3/,
  /from ['"]@\/config\/axios/,
  /from ['"]@\/router(?:\/|['"])/,
  /from ['"]@\/store\/(?:modules\/(?:user|permission|dict|tenant)|index(?:\.[^'"]+)?['"])/,
  /from ['"]@\/views\/(?:system|infra)\//
]

const violations = []
function walk(directory) {
  for (const entry of readdirSync(directory)) {
    const file = join(directory, entry)
    if (statSync(file).isDirectory()) walk(file)
    else if (/\.(?:ts|tsx|vue|js|mjs)$/.test(file)) {
      readFileSync(file, 'utf8').split(/\r?\n/).forEach((line, index) => {
        if (patterns.some((pattern) => pattern.test(line))) {
          violations.push(`${relative(root, file)}:${index + 1}: ${line.trim()}`)
        }
      })
    }
  }
}
walk(root)
if (violations.length) {
  console.error('yuheng-demo-ui boundary: FAIL')
  console.error(violations.join('\n'))
  process.exitCode = 1
} else {
  console.log('yuheng-demo-ui boundary: PASS')
}
