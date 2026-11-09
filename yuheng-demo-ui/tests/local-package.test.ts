import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { cpSync, copyFileSync, existsSync, mkdtempSync, mkdirSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it } from 'vitest'

const source = fileURLToPath(new URL('../scripts/verify-local-package.mjs', import.meta.url))
const fixtures: string[] = []
afterEach(() => {
  for (const directory of fixtures.splice(0)) rmSync(directory, { recursive: true, force: true })
})

function fixture(env: Record<string, string> = {}) {
  const root = mkdtempSync(join(tmpdir(), 'yuheng local-package-'))
  fixtures.push(root)
  const core = join(root, 'yuheng-core', 'yuheng-ui')
  const consumer = join(root, 'demo', 'yuheng-demo-ui')
  const bin = join(root, 'bin')
  const vendor = join(consumer, 'vendor')
  for (const path of [core, bin, vendor, join(consumer, 'scripts')]) mkdirSync(path, { recursive: true })
  copyFileSync(source, join(consumer, 'scripts', 'verify-local-package.mjs'))
  const pkg = {
    name: 'yuheng-demo-ui', private: true,
    dependencies: { 'yuheng-ui': 'file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz', vue: '3.5.34' }
  }
  const manifest = JSON.stringify(pkg, null, 2) + '\n'
  const lock = 'original lock bytes\r\n'
  writeFileSync(join(consumer, 'package.json'), manifest)
  writeFileSync(join(consumer, 'pnpm-lock.yaml'), lock)
  writeFileSync(join(core, 'package.json'), JSON.stringify({ name: 'yuheng-ui', version: '0.1.0-SNAPSHOT' }))
  writeFileSync(join(core, 'content.txt'), 'old')
  writeFileSync(join(core, 'do-not-delete.tgz'), 'unrelated archive')
  // A stand-in for pnpm records actual argv/cwd/manifest and produces a real tar archive.
  writeFileSync(join(bin, 'pnpm'), `#!${process.execPath}
const { spawnSync } = require('node:child_process')
const { appendFileSync, copyFileSync, mkdirSync, readFileSync, writeFileSync } = require('node:fs')
const { join } = require('node:path')
const args = process.argv.slice(2)
const cwd = process.cwd()
const pkg = JSON.parse(readFileSync('package.json', 'utf8'))
appendFileSync(process.env.FIXTURE_ROOT + '/calls.jsonl', JSON.stringify({args, cwd, dependency: pkg.dependencies?.['yuheng-ui']}) + '\\n')
if (cwd.endsWith('/yuheng-core/yuheng-ui')) {
  if (args[0] === 'run' && args[1] === 'build') {
    if (process.env.FAIL_CORE === '1') process.exit(6)
    mkdirSync('package', { recursive: true })
    copyFileSync('package.json', 'package/package.json')
    copyFileSync('content.txt', 'package/content.txt')
  } else if (args[0] === 'pack') {
    if (process.env.NO_ARTIFACT === '1') process.exit(0)
    if (process.env.WRONG_METADATA === '1') writeFileSync('package/package.json', JSON.stringify({name:'other',version:'1'}))
    const dest = args[args.indexOf('--pack-destination') + 1]
    const result = spawnSync('tar', ['-czf', join(dest, 'yuheng-ui-0.1.0-SNAPSHOT.tgz'), 'package'])
    process.exit(result.status)
  } else process.exit(64)
} else if (args[0] === 'install') {
  const dependency = pkg.dependencies['yuheng-ui']
  const bytes = readFileSync(dependency.slice(5))
  writeFileSync(process.env.FIXTURE_ROOT + '/installed.txt', dependency)
  writeFileSync('pnpm-lock.yaml', 'generated lock')
  if (process.env.FAIL_INSTALL === '1') process.exit(9)
} else if (args[0] === 'run' && args[1] === 'build' && process.env.FAIL_BUILD === '1') process.exit(7)
else if (!['test','run'].includes(args[0])) process.exit(64)
`, { mode: 0o755 })
  return {
    root, core, consumer, vendor, manifest, lock, env,
    calls: () => readFileSync(join(root, 'calls.jsonl'), 'utf8').trim().split('\n').map(line => JSON.parse(line)),
    run: (args: string[] = []) => spawnSync(process.execPath, [join(consumer, 'scripts', 'verify-local-package.mjs'), ...args], {
      cwd: consumer, encoding: 'utf8', timeout: 10000,
      env: { ...process.env, PATH: `${bin}:/usr/bin:/bin:/usr/sbin:/sbin`, FIXTURE_ROOT: root, ...env },
      stdio: ['ignore', 'pipe', 'pipe']
    })
  }
}

function successful(result: ReturnType<typeof spawnSync>) {
  expect(result.error).toBeUndefined()
  expect(result.status, String(result.stdout) + String(result.stderr)).toBe(0)
}

function restored(f: ReturnType<typeof fixture>) {
  expect(readFileSync(join(f.consumer, 'package.json'), 'utf8')).toBe(f.manifest)
  expect(readFileSync(join(f.consumer, 'pnpm-lock.yaml'), 'utf8')).toBe(f.lock)
  expect(readdirSync(f.vendor).filter(name => name.startsWith('.pack-'))).toEqual([])
}

describe('local package refresh workflow', () => {
  it('builds and packs adjacent core, copies the artifact to demo vendor, then installs by content hash', () => {
    const f = fixture()
    successful(f.run(['--build']))
    const installed = readFileSync(join(f.root, 'installed.txt'), 'utf8')
    expect(installed).toMatch(/^file:vendor\/yuheng-ui-[a-f0-9]{64}\.tgz$/)
    const hash = createHash('sha256').update(readFileSync(join(f.consumer, installed.slice(5)))).digest('hex')
    expect(installed).toContain(hash)
    expect(readFileSync(join(f.vendor, 'yuheng-ui-0.1.0-SNAPSHOT.tgz'))).toEqual(readFileSync(join(f.consumer, installed.slice(5))))
    expect(f.calls().map(call => call.args)).toEqual([
      ['run', 'build'], ['pack', '--pack-destination', expect.any(String)],
      ['install', '--no-frozen-lockfile'], ['run', 'build']
    ])
    expect(readFileSync(join(f.core, 'do-not-delete.tgz'), 'utf8')).toBe('unrelated archive')
    restored(f)
  })

  it('uses a new pnpm store key when different core content has the same package version', () => {
    const f = fixture()
    successful(f.run(['--build']))
    const original = readFileSync(join(f.root, 'installed.txt'), 'utf8')
    writeFileSync(join(f.core, 'content.txt'), 'new content with the same version')
    successful(f.run(['--build']))
    const updated = readFileSync(join(f.root, 'installed.txt'), 'utf8')
    expect(updated).not.toBe(original)
    expect(existsSync(join(f.consumer, original.slice(5)))).toBe(true)
    restored(f)
  })

  it('default verification runs all consumer checks after restoring original metadata', () => {
    const f = fixture()
    successful(f.run())
    const checks = f.calls().slice(3)
    expect(checks.map(call => call.args)).toEqual([['test'], ['run', 'typecheck'], ['run', 'build'], ['run', 'lint:platform-imports']])
    expect(checks.every(call => call.dependency === 'file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz')).toBe(true)
    restored(f)
  })

  it('refreshes dependencies before dev and restores metadata before the foreground process', () => {
    const f = fixture()
    successful(f.run(['--dev']))
    const calls = f.calls()
    expect(calls[calls.length - 1].args).toEqual(['run', 'dev'])
    expect(calls[calls.length - 1].dependency).toBe('file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz')
    restored(f)
  })

  it('dev tolerates a temporary absolute tarball dependency without overwriting that tarball', () => {
    const f = fixture()
    const external = join(f.root, 'temporary core.tgz')
    writeFileSync(external, 'do not overwrite the main thread artifact')
    const manifest = f.manifest.replace('file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz', `file:${external}`)
    writeFileSync(join(f.consumer, 'package.json'), manifest)
    successful(f.run(['--dev']))
    expect(readFileSync(external, 'utf8')).toBe('do not overwrite the main thread artifact')
    expect(readFileSync(join(f.consumer, 'package.json'), 'utf8')).toBe(manifest)
    expect(readFileSync(join(f.consumer, 'pnpm-lock.yaml'), 'utf8')).toBe(f.lock)
    expect(readFileSync(join(f.root, 'installed.txt'), 'utf8')).toMatch(/^file:vendor\/yuheng-ui-[a-f0-9]{64}\.tgz$/)
    expect(existsSync(join(f.vendor, 'yuheng-ui-0.1.0-SNAPSHOT.tgz'))).toBe(true)
    const calls = f.calls()
    expect(calls[calls.length - 1].args).toEqual(['run', 'dev'])
    expect(calls[calls.length - 1].dependency).toBe(`file:${external}`)
  })

  it('CI still rejects absolute temporary package dependencies', () => {
    const f = fixture()
    const manifest = f.manifest.replace('file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz', 'file:/tmp/core.tgz')
    writeFileSync(join(f.consumer, 'package.json'), manifest)
    expect(f.run(['--ci']).status).toBe(1)
    expect(readFileSync(join(f.consumer, 'package.json'), 'utf8')).toBe(manifest)
    expect(existsSync(join(f.root, 'calls.jsonl'))).toBe(false)
  })

  it('CI refreshes the artifact lock entry before frozen install, then runs all checks', () => {
    const f = fixture()
    successful(f.run(['--ci']))
    expect(f.calls().map(call => call.args)).toEqual([
      ['run', 'build'], ['pack', '--pack-destination', expect.any(String)],
      ['install', '--lockfile-only', '--no-frozen-lockfile'], ['install', '--frozen-lockfile'],
      ['test'], ['run', 'typecheck'], ['run', 'build'], ['run', 'lint:platform-imports']
    ])
    restored(f)
  })

  it.each([['FAIL_CORE', '6'], ['FAIL_INSTALL', '9'], ['FAIL_BUILD', '7']])(
    'restores exact package/lock bytes when %s occurs', (key, status) => {
      const f = fixture({ [key]: '1' })
      expect(f.run(['--build']).status).toBe(Number(status))
      restored(f)
    }
  )

  it('preserves the absence of a lockfile after verification', () => {
    const f = fixture()
    rmSync(join(f.consumer, 'pnpm-lock.yaml'))
    successful(f.run(['--build']))
    expect(existsSync(join(f.consumer, 'pnpm-lock.yaml'))).toBe(false)
  })

  it.each(['NO_ARTIFACT', 'WRONG_METADATA'])('rejects unusable pack output (%s)', (key) => {
    const f = fixture({ [key]: '1' })
    expect(f.run(['--build']).status).toBe(1)
    expect(existsSync(join(f.root, 'installed.txt'))).toBe(false)
    restored(f)
  })

  it('uses an explicit core checkout root for CI instead of assuming sibling layout', () => {
    const f = fixture()
    const checkout = join(f.root, 'demo', 'yuheng-core')
    mkdirSync(checkout, { recursive: true })
    // Move the fixture core into the same nested layout used by actions/checkout.
    const moved = join(checkout, 'yuheng-ui')
    cpSync(f.core, moved, { recursive: true })
    rmSync(f.core, { recursive: true, force: true })
    f.env.YUHENG_CORE_ROOT = checkout
    successful(f.run(['--ci']))
    expect(f.calls()[0].cwd).toBe(realpathSync(moved))
    restored(f)
  })

  it('fails clearly when adjacent core source is missing without changing metadata', () => {
    const f = fixture()
    rmSync(f.core, { recursive: true, force: true })
    const result = f.run(['--build'])
    expect(result.status).toBe(1)
    expect(result.stdout + result.stderr).toContain('Missing yuheng-core source')
    restored(f)
  })

  it('rejects metadata that points outside demo vendor', () => {
    const f = fixture()
    writeFileSync(join(f.consumer, 'package.json'), f.manifest.replace('file:vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz', 'file:../../external.tgz'))
    expect(f.run(['--build']).status).toBe(1)
    expect(existsSync(join(f.root, 'calls.jsonl'))).toBe(false)
  })
})

describe('consumer CI local artifact wiring', () => {
  it('checks out core and installs its build dependencies before the shared CI verifier', () => {
    const workflow = readFileSync(fileURLToPath(new URL('../../.github/workflows/consumer-verify.yml', import.meta.url)), 'utf8')
    const uiJob = workflow.slice(workflow.indexOf('  verify-ui:'))
    expect(uiJob).toContain('repository: huhua1990/yuheng-core')
    expect(uiJob).toContain('path: yuheng-core')
    expect(uiJob).toContain("node-version: '22.23.2'")
    expect(uiJob).toContain('working-directory: yuheng-core/yuheng-ui')
    expect(uiJob).toContain('run: pnpm install --frozen-lockfile')
    expect(uiJob).toContain('YUHENG_CORE_ROOT: ${{ github.workspace }}/yuheng-core')
    expect(uiJob).toContain('run: node scripts/verify-local-package.mjs --ci')
    expect(uiJob.indexOf('run: pnpm install --frozen-lockfile')).toBeLessThan(uiJob.indexOf('run: node scripts/verify-local-package.mjs --ci'))
    expect(uiJob).not.toContain("p.dependencies['yuheng-ui'] !== '0.1.0-SNAPSHOT'")
  })
})
