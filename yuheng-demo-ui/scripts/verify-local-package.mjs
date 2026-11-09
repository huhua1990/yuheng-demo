#!/usr/bin/env node
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync,
  readdirSync, rmSync, writeFileSync
} from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

const script = fileURLToPath(import.meta.url)
const root = resolve(dirname(script), '..')
const mode = process.argv[2] ?? '--verify'
const modes = ['--verify', '--build', '--dev', '--ci']

function compatible(version) {
  const [major, minor] = version.split('.').map(Number)
  return major > 22 || (major === 22 && minor >= 12) || (major === 20 && minor >= 19)
}

// This entry point also works when invoked directly with an unsupported default node.
if (!compatible(process.versions.node)) {
  const versions = join(process.env.NVM_DIR || join(homedir(), '.nvm'), 'versions', 'node')
  let selected
  if (existsSync(versions)) {
    for (const entry of readdirSync(versions).sort().reverse()) {
      const node = join(versions, entry, 'bin', 'node')
      const probe = spawnSync(node, ['-p', 'process.versions.node'], { encoding: 'utf8' })
      if (probe.status === 0 && compatible(probe.stdout.trim())) { selected = node; break }
    }
  }
  if (!selected) {
    console.error('Node 版本不满足 Vite 要求（>=20.19 或 >=22.12）；请安装兼容 Node 或配置 NVM_DIR')
    process.exit(1)
  }
  const result = spawnSync(selected, [script, ...process.argv.slice(2)], {
    stdio: 'inherit', env: { ...process.env, PATH: `${dirname(selected)}:${process.env.PATH || ''}` }
  })
  process.exit(result.status ?? 1)
}

class CommandError extends Error {
  constructor(message, status = 1) { super(message); this.status = status }
}

function run(command, args, cwd, extraEnv = {}) {
  const result = spawnSync(command, args, {
    cwd, stdio: 'inherit', env: { ...process.env, ...extraEnv }
  })
  if (result.error || result.status !== 0) {
    throw new CommandError(`${command} ${args.join(' ')} failed: ${result.error?.message || result.signal || result.status}`, result.status || 1)
  }
}

const packagePath = join(root, 'package.json')
const lockPath = join(root, 'pnpm-lock.yaml')
const packageBackup = readFileSync(packagePath)
const lockBackup = existsSync(lockPath) ? readFileSync(lockPath) : null
let modified = false
let staging
const restore = () => {
  if (!modified) return
  writeFileSync(packagePath, packageBackup)
  if (lockBackup === null) rmSync(lockPath, { force: true })
  else writeFileSync(lockPath, lockBackup)
  modified = false
}

// pnpm dev is synchronous, so restore before starting it. Also protect metadata on interruption.
for (const [signal, status] of [['SIGINT', 130], ['SIGTERM', 143]]) {
  process.on(signal, () => { restore(); process.exit(status) })
}

try {
  if (!modes.includes(mode)) throw new Error(`Usage: verify-local-package.mjs [${modes.join('|')}]`)
  const pkg = JSON.parse(packageBackup.toString())
  const dependency = pkg.dependencies?.['yuheng-ui']
  const vendorDependency = /^file:vendor\/[a-zA-Z0-9_.-]+\.tgz$/.test(dependency || '')
  // The integration thread may temporarily install an absolute tarball. Dev always
  // rebuilds from core, so use a demo-owned copy instead of trusting/writing that path.
  const temporaryDevDependency = mode === '--dev' && /^file:\/.+\.tgz$/.test(dependency || '')
  if ((!vendorDependency && !temporaryDevDependency) || pkg.pnpm?.overrides?.['yuheng-ui']) {
    throw new Error('Expected yuheng-ui as a file:vendor/*.tgz dependency without a pnpm override')
  }
  const coreRoot = process.env.YUHENG_CORE_ROOT
    ? resolve(process.env.YUHENG_CORE_ROOT)
    : resolve(root, '../../yuheng-core')
  const coreUi = join(coreRoot, 'yuheng-ui')
  if (!existsSync(join(coreUi, 'package.json'))) throw new Error(`Missing yuheng-core source: ${coreUi}`)
  const corePkg = JSON.parse(readFileSync(join(coreUi, 'package.json'), 'utf8'))
  if (corePkg.name !== 'yuheng-ui' || !corePkg.version) throw new Error('Expected core package name yuheng-ui and a version')

  // Pack only into demo-owned staging. Never delete or reuse tarballs in the source checkout.
  const vendor = join(root, 'vendor')
  mkdirSync(vendor, { recursive: true })
  staging = mkdtempSync(join(vendor, '.pack-'))
  run('pnpm', ['run', 'build'], coreUi)
  run('pnpm', ['pack', '--pack-destination', staging], coreUi)
  const packed = readdirSync(staging).filter(name => name.endsWith('.tgz'))
  if (packed.length !== 1) throw new Error(`Expected exactly one packed core artifact, found ${packed.length}`)
  const source = join(staging, packed[0])
  const metadata = spawnSync('tar', ['-xOf', source, 'package/package.json'], { encoding: 'utf8' })
  if (metadata.status !== 0) throw new Error('Cannot read packed core package metadata')
  const artifactPkg = JSON.parse(metadata.stdout)
  if (artifactPkg.name !== corePkg.name || artifactPkg.version !== corePkg.version) {
    throw new Error('Packed artifact name/version does not match the core package')
  }
  const hash = createHash('sha256').update(readFileSync(source)).digest('hex')
  const filename = `yuheng-ui-${hash}.tgz`
  const artifact = join(vendor, filename)
  copyFileSync(source, artifact)
  // Keep the declared file dependency available while giving pnpm a fresh immutable store key.
  const declared = vendorDependency
    ? resolve(root, dependency.slice(5))
    : join(vendor, 'yuheng-ui-0.1.0-SNAPSHOT.tgz')
  if (!declared.startsWith(`${vendor}${sep}`)) throw new Error('Local artifact must stay within vendor')
  if (declared !== artifact) copyFileSync(source, declared)
  console.log(`Local package: file:vendor/${filename} (${artifactPkg.name}@${artifactPkg.version})`)

  pkg.dependencies['yuheng-ui'] = `file:vendor/${filename}`
  modified = true
  writeFileSync(packagePath, `${JSON.stringify(pkg, null, 2)}\n`)
  // Keep the existing lock as the resolution baseline. Only the changed artifact needs refreshing.
  if (mode === '--ci') {
    run('pnpm', ['install', '--lockfile-only', '--no-frozen-lockfile'], root)
    run('pnpm', ['install', '--frozen-lockfile'], root)
  } else {
    run('pnpm', ['install', '--no-frozen-lockfile'], root)
  }
  restore()

  const commands = mode === '--dev' ? [['run', 'dev']]
    : mode === '--build' ? [['run', 'build']]
      : [['test'], ['run', 'typecheck'], ['run', 'build'], ['run', 'lint:platform-imports']]
  for (const command of commands) run('pnpm', command, root, { YUHENG_UI_LOCAL_VERIFY: '1' })
} catch (error) {
  console.error(error.message)
  process.exitCode = error instanceof CommandError ? error.status : 1
} finally {
  restore()
  if (staging) rmSync(staging, { recursive: true, force: true })
}
