#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
command -v node >/dev/null || { echo '需要 Node.js 22.12+ 或 20.19+' >&2; exit 1; }
command -v pnpm >/dev/null || { echo '需要 pnpm 9+' >&2; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(a<20 || (a===20 && b<19) || (a===22 && b<12) || a===21) {console.error("需要 Node.js 22.12+ 或 20.19+"); process.exit(1)}'
command -v rsync >/dev/null || { echo '需要 rsync' >&2; exit 1; }

UI_SOURCE="$ROOT/yuheng-demo-ui"
EXPECTED_UI_VERSION=$(node -p 'require(process.argv[1]).dependencies?.["yuheng-ui"]' "$UI_SOURCE/package.json")
[[ "$EXPECTED_UI_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-.+)?$ ]] || {
  echo "yuheng-ui 依赖必须是固定版本，当前为: $EXPECTED_UI_VERSION" >&2
  exit 1
}

if [[ -n "${YUHENG_UI_PACKAGE:-}" && "$YUHENG_UI_PACKAGE" != /* ]]; then
  YUHENG_UI_PACKAGE="$ROOT/$YUHENG_UI_PACKAGE"
  export YUHENG_UI_PACKAGE
fi

TEMP_UI=$(mktemp -d "${TMPDIR:-/tmp}/yuheng-demo-ui.XXXXXX")
cleanup() { rm -rf "$TEMP_UI"; }
trap cleanup EXIT
rsync -a --exclude node_modules --exclude dist --exclude .vite "$UI_SOURCE/" "$TEMP_UI/"

if [[ -n "${YUHENG_UI_PACKAGE:-}" ]]; then
  [[ -f "$YUHENG_UI_PACKAGE" ]] || { echo "YUHENG_UI_PACKAGE 文件不存在: $YUHENG_UI_PACKAGE" >&2; exit 1; }
  PACKAGE_INFO=$(tar -xOzf "$YUHENG_UI_PACKAGE" package/package.json 2>/dev/null) || {
    echo 'YUHENG_UI_PACKAGE 不是有效的 npm tarball' >&2
    exit 1
  }
  PACKAGE_NAME=$(node -e 'const p=JSON.parse(process.argv[1]); process.stdout.write(p.name || "")' "$PACKAGE_INFO")
  PACKAGE_VERSION=$(node -e 'const p=JSON.parse(process.argv[1]); process.stdout.write(p.version || "")' "$PACKAGE_INFO")
  [[ "$PACKAGE_NAME" == "yuheng-ui" ]] || { echo "YUHENG_UI_PACKAGE 包名错误: $PACKAGE_NAME" >&2; exit 1; }
  [[ "$PACKAGE_VERSION" == "$EXPECTED_UI_VERSION" ]] || {
    echo "yuheng-ui 版本不匹配: manifest=$EXPECTED_UI_VERSION package=$PACKAGE_VERSION" >&2
    exit 1
  }
  node - "$TEMP_UI/package.json" "$YUHENG_UI_PACKAGE" <<'NODE'
const fs = require('node:fs')
const [manifestPath, packagePath] = process.argv.slice(2)
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
manifest.dependencies['yuheng-ui'] = `file:${packagePath}`
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`)
NODE
  pnpm --dir "$TEMP_UI" install --offline --ignore-scripts --no-frozen-lockfile
else
  pnpm --dir "$TEMP_UI" install --frozen-lockfile --ignore-scripts
fi
pnpm --dir "$TEMP_UI" typecheck
pnpm --dir "$TEMP_UI" build
rm -rf "$UI_SOURCE/dist"
cp -R "$TEMP_UI/dist" "$UI_SOURCE/dist"
[[ -f "$ROOT/yuheng-demo-ui/dist/index.html" ]] || { echo '前端构建未生成 dist/index.html' >&2; exit 1; }
rm -rf "$ROOT/yuheng-demo-server/yuheng-demo-server-bootstrap/target/classes/static"
