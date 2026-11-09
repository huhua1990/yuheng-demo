import { spawn, spawnSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it } from 'vitest'

const source = fileURLToPath(new URL('../../yuheng-demo.sh', import.meta.url))
const fixtures: string[] = []
afterEach(() => {
  for (const directory of fixtures.splice(0)) rmSync(directory, { recursive: true, force: true })
})

function fixture(overrides: Record<string, string> = {}) {
  const root = mkdtempSync(join(tmpdir(), 'yuheng startup-'))
  fixtures.push(root)
  const bin = join(root, 'bin')
  const project = join(root, 'demo')
  const ui = join(project, 'yuheng-demo-ui')
  for (const path of [bin, join(project, 'target'), join(ui, 'node_modules'), join(ui, 'scripts')]) {
    mkdirSync(path, { recursive: true })
  }
  const executable = (name: string, content: string) =>
    writeFileSync(join(bin, name), `#!/bin/sh\n${content}\n`, { mode: 0o755 })
  copyFileSync(source, join(project, 'yuheng-demo.sh'))
  writeFileSync(join(project, 'target', 'yuheng-demo.jar'), '')
  // Frontend packaging is tested separately; startup must call the shared workflow.
  writeFileSync(join(ui, 'scripts', 'verify-local-package.mjs'),
    'console.log("FRONTEND_STARTED " + process.argv.slice(2).join(" "))\n')
  executable('node', `if [ "$1" = -p ]; then printf '%s\\n' "$MOCK_NODE_VERSION"; else exec "${process.execPath}" "$@"; fi`)
  executable('pnpm', 'echo "PNPM_STARTED $*"')
  executable('java', 'exit 0')
  // Do not launch any actual background service, even when testing broken startup code.
  executable('nohup', 'exit 0')
  executable('sleep', 'exit 0')
  executable('ps', `case "$*" in
    *comm=*)
      count=0
      [ ! -f "$FIXTURE_ROOT/ps.count" ] || count=$(cat "$FIXTURE_ROOT/ps.count")
      count=$((count + 1)); echo "$count" > "$FIXTURE_ROOT/ps.count"
      if [ "$count" -le "$MOCK_JAVA_DELAY" ]; then echo nohup; else echo java; fi ;;
    *lstart=*) printf '%s\\n' "$MOCK_BIRTH" ;;
    *args=*|*command=*) printf '%s\\n' "$MOCK_COMMAND" ;;
    *) [ "$MOCK_ALIVE" = 1 ] || exit 1 ;;
  esac
  [ "$MOCK_ALIVE" = 1 ] || exit 1`)
  executable('lsof', `case " $* " in
    *" -d cwd "*) printf 'p424242\nfcwd\nn%s\n' "$MOCK_CWD"; exit 0 ;;
    *" -iTCP:3000 "*)
      if [ "$MOCK_FRONTEND_LISTEN" = 1 ]; then echo 424242; exit 0; fi
      # An outbound connection is deliberately visible to an unfiltered query.
      case " $* " in *" -sTCP:LISTEN "*) exit 1;; esac
      echo 'Google 456 TCP local:61307->remote:3000 (ESTABLISHED)' ;;
    *" -iTCP:48080 "*)
      case " $* " in *" -p "*) [ "$MOCK_NEW_LISTEN" = 1 ] || exit 1; echo 424242; exit 0;; esac
      [ "$MOCK_BACKEND_LISTEN" = 1 ] || exit 1; echo 424242 ;;
    *) exit 1 ;;
  esac`)
  executable('curl', `printf '%s\\n' "$*" >> "$FIXTURE_ROOT/curl.log"
    count=0
    [ ! -f "$FIXTURE_ROOT/curl.count" ] || count=$(cat "$FIXTURE_ROOT/curl.count")
    count=$((count + 1)); echo "$count" > "$FIXTURE_ROOT/curl.count"
    if [ "$count" -le "$MOCK_NOT_READY_COUNT" ]; then
      printf '%s' '{"code":404,"data":null}'
    else
      printf '%s' "$MOCK_RESPONSE"
    fi
    exit "$MOCK_HTTP_EXIT"`)
  const env = {
    ...process.env,
    PATH: `${bin}:/usr/bin:/bin:/usr/sbin:/sbin`,
    HOME: join(root, 'home'),
    NVM_DIR: join(root, 'nvm'),
    FIXTURE_ROOT: root,
    MOCK_COMMAND: `java -Dspring.profiles.active=local -Dserver.port=48080 -jar ${project}/target/yuheng-demo.jar`,
    MOCK_BIRTH: 'Tue Nov  3 21:00:00 2026',
    MOCK_ALIVE: '1',
    MOCK_JAVA_DELAY: '0',
    MOCK_CWD: project,
    MOCK_NEW_LISTEN: '1',
    MOCK_BACKEND_LISTEN: '0',
    MOCK_FRONTEND_LISTEN: '0',
    MOCK_NODE_VERSION: '22.12.0',
    MOCK_RESPONSE: '{"code":0,"msg":"","data":1}',
    MOCK_NOT_READY_COUNT: '0',
    MOCK_HTTP_EXIT: '0',
    YUHENG_READINESS_ATTEMPTS: '3',
    YUHENG_READINESS_INTERVAL: '0',
    TENANT_NAME: 'Demo tenant & 中文',
    ...overrides
  }
  const run = (command: string, shell = '/bin/sh') => spawnSync(shell, [join(project, 'yuheng-demo.sh'), command], {
    cwd: root, env, encoding: 'utf8', timeout: 8000, stdio: ['ignore', 'pipe', 'pipe']
  })
  return { root, project, env, run, executable }
}

function successful(result: ReturnType<typeof spawnSync>) {
  expect(result.error).toBeUndefined()
  expect(result.status, String(result.stdout) + String(result.stderr)).toBe(0)
}

describe('demo startup port check', () => {
  it('ignores outgoing connections to a remote port 3000', () => {
    const result = fixture().run('dev:frontend')
    successful(result)
    expect(result.stdout).toContain('FRONTEND_STARTED --dev')
  })

  it('refuses to start when a local TCP listener already owns port 3000', () => {
    const result = fixture({ MOCK_FRONTEND_LISTEN: '1' }).run('dev:frontend')
    expect(result.status).toBe(1)
    expect(result.stdout).toContain('端口 3000 被占用，无法启动')
    expect(result.stdout).not.toContain('FRONTEND_STARTED')
  })
})

describe('demo backend readiness', () => {
  it('runs sh start from another directory and waits for a real tenant response before frontend startup', () => {
    const f = fixture({ MOCK_NOT_READY_COUNT: '2' })
    const result = f.run('start')
    successful(result)
    expect(result.stdout).toContain('后端服务启动成功')
    expect(result.stdout).toContain('FRONTEND_STARTED --dev')
    expect(readFileSync(join(f.root, 'curl.count'), 'utf8').trim()).toBe('3')
    const request = readFileSync(join(f.root, 'curl.log'), 'utf8')
    expect(request).toContain('/admin-api/system/tenant/get-id-by-name')
    expect(request).toContain('--data-urlencode name=Demo tenant & 中文')
    expect(request).not.toContain('/actuator/health')
  })

  it('allows nohup to exec Java before validating the launched service', () => {
    const result = fixture({ MOCK_JAVA_DELAY: '2' }).run('start:backend')
    successful(result)
    expect(result.stdout).toContain('后端服务启动成功')
  })

  it('runs under dash as well as macOS sh', () => {
    if (!existsSync('/bin/dash')) return
    successful(fixture().run('start', '/bin/dash'))
  })

  it.each([
    '{"code":404,"msg":"Not Found","data":null}',
    '{"code":0,"data":null}',
    '{"code":0,"data":0}',
    '{"code":0,"data":"1"}',
    '{"code":0,"data":1',
    '<html>ok</html>',
    '{"nested":{"code":0,"data":1},"code":404}'
  ])('rejects an invalid success envelope: %s', (response) => {
    const f = fixture({ MOCK_RESPONSE: response })
    const result = f.run('start')
    expect(result.error).toBeUndefined()
    expect(result.status).toBe(1)
    expect(result.stdout).toContain('后端服务就绪检查失败')
    expect(result.stdout).not.toContain('FRONTEND_STARTED')
    expect(readFileSync(join(f.root, 'curl.count'), 'utf8').trim()).toBe('3')
  })

  it('does not accept a successful-looking body from an unsuccessful HTTP request', () => {
    const result = fixture({ MOCK_HTTP_EXIT: '22' }).run('start:backend')
    expect(result.status).toBe(1)
    expect(result.stdout).not.toContain('后端服务启动成功')
  })

  it('fails promptly if the launched backend exits', () => {
    const result = fixture({ MOCK_ALIVE: '0' }).run('start')
    expect(result.status).toBe(1)
    expect(result.stdout).not.toContain('FRONTEND_STARTED')
  })
})

describe('demo backend ownership', () => {
  it('recognizes its exact listening backend even when the PID file is missing', () => {
    const f = fixture({ MOCK_BACKEND_LISTEN: '1' })
    successful(f.run('start:backend'))
    expect(readFileSync(join(f.project, 'yuheng-demo.pid'), 'utf8')).toMatch(/^424242\n/)
  })

  it('status discovers an exact backend started with a relative JAR path from this checkout', () => {
    const f = fixture({ MOCK_BACKEND_LISTEN: '1' })
    f.env.MOCK_COMMAND = 'java -Dspring.profiles.active=local -Dserver.port=48080 -jar target/yuheng-demo.jar'
    const result = f.run('status')
    successful(result)
    expect(result.stdout).toContain('后端服务运行中')
    expect(readFileSync(join(f.project, 'yuheng-demo.pid'), 'utf8')).toMatch(/^424242\n/)
  })

  it.each(['target/yuheng-demo.jar', './target/yuheng-demo.jar'])(
    'adopts a relative JAR only when the process cwd proves checkout ownership: %s', (jar) => {
      const f = fixture({ MOCK_BACKEND_LISTEN: '1' })
      f.env.MOCK_COMMAND = `java -Dspring.profiles.active=local -Dserver.port=48080 -jar ${jar}`
      successful(f.run('start:backend'))
    }
  )

  it('refuses a relative JAR launched in a different checkout', () => {
    const f = fixture({ MOCK_BACKEND_LISTEN: '1', MOCK_CWD: '/other/checkout' })
    f.env.MOCK_COMMAND = 'java -Dspring.profiles.active=local -Dserver.port=48080 -jar target/yuheng-demo.jar'
    expect(f.run('start:backend').status).toBe(1)
  })

  it.each([
    'java -Dspring.profiles.active=local -Dserver.port=48080 -jar /other/target/yuheng-demo.jar',
    'java -Dspring.profiles.active=local -Dserver.port=48080 -jar /other/target/yuheng-demo.jar.backup',
    'some-unrelated-command'
  ])('does not adopt another listener: %s', (command) => {
    const f = fixture({ MOCK_BACKEND_LISTEN: '1', MOCK_COMMAND: command })
    const result = f.run('start:backend')
    expect(result.status).toBe(1)
    expect(result.stdout).toContain('端口 48080 被占用，无法启动')
    expect(existsSync(join(f.root, 'curl.log'))).toBe(false)
  })

  it.each([
    ['a different port', '-Dserver.port=48080', '-Dserver.port=48081'],
    ['a different profile', '-Dspring.profiles.active=local', '-Dspring.profiles.active=prod'],
    ['a JAR filename suffix', 'yuheng-demo.jar', 'yuheng-demo.jar.backup']
  ])('does not adopt the same checkout with %s', (_name, before, after) => {
    const f = fixture({ MOCK_BACKEND_LISTEN: '1' })
    f.env.MOCK_COMMAND = f.env.MOCK_COMMAND.replace(before, after)
    const result = f.run('start:backend')
    expect(result.status).toBe(1)
    expect(result.stdout).toContain('端口 48080 被占用，无法启动')
  })

  it('does not accept a tenant response if the listener is not the owned backend', () => {
    const f = fixture({ MOCK_NEW_LISTEN: '0' })
    const result = f.run('start:backend')
    expect(result.status).toBe(1)
    expect(existsSync(join(f.root, 'curl.log'))).toBe(false)
  })

  it('readiness-checks a backend recorded in a valid PID file', () => {
    const f = fixture({ MOCK_RESPONSE: '{"code":404,"data":null}' })
    writeFileSync(join(f.project, 'yuheng-demo.pid'), '424242\n')
    expect(f.run('start').status).toBe(1)
  })

  it('rejects a PID reused since the backend was recorded', () => {
    const f = fixture()
    writeFileSync(join(f.project, 'yuheng-demo.pid'), '424242\nA different start time\n')
    const result = f.run('status:backend')
    successful(result)
    expect(result.stdout).toContain('后端服务未运行')
  })

  it('stop leaves an unrelated live PID and an unrelated frontend listener alone', async () => {
    const child = spawn('/bin/sleep', ['30'], { stdio: 'ignore' })
    try {
      const f = fixture({ MOCK_COMMAND: '/bin/sleep 30', MOCK_FRONTEND_LISTEN: '1' })
      writeFileSync(join(f.project, 'yuheng-demo.pid'), `${child.pid}\n`)
      successful(f.run('stop'))
      expect(() => process.kill(child.pid!, 0)).not.toThrow()
    } finally {
      child.kill()
      await new Promise((resolve) => child.once('close', resolve))
    }
  })
})

describe('demo Node runtime discovery', () => {
  it.each(['20.19.0', '20.20.1', '22.12.0', '24.1.0'])(
    'accepts compatible Node %s', (version) => {
      successful(fixture({ MOCK_NODE_VERSION: version }).run('dev:frontend'))
    }
  )

  it.each(['16.13.2', '20.18.0', '21.7.0', '22.11.0'])(
    'rejects unsupported Node %s without a compatible nvm installation', (version) => {
      const result = fixture({ MOCK_NODE_VERSION: version }).run('dev:frontend')
      expect(result.status).toBe(1)
      expect(result.stdout).toContain('Node 版本不满足')
    }
  )

  it('finds compatible Node under NVM_DIR with node16 as the default', () => {
    const f = fixture({ MOCK_NODE_VERSION: '16.13.2' })
    const nodePath = join(f.env.NVM_DIR, 'versions/node/v22.12.0/bin/node')
    mkdirSync(dirname(nodePath), { recursive: true })
    writeFileSync(nodePath, `#!/bin/sh\nif [ "$1" = -p ]; then echo 22.12.0; else exec "${process.execPath}" "$@"; fi\n`, { mode: 0o755 })
    const result = f.run('dev:frontend')
    successful(result)
    expect(result.stdout).toContain('v22.12.0')
    expect(result.stdout).toContain('FRONTEND_STARTED --dev')
  })
})
