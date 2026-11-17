#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORKSPACE_ROOT=$(cd "$ROOT/.." && pwd)
command -v node >/dev/null || { echo '需要 Node.js 22.12+ 或 20.19+' >&2; exit 1; }
command -v pnpm >/dev/null || { echo '需要 pnpm 9+' >&2; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(a<20 || (a===20 && b<19) || (a===22 && b<12) || a===21) {console.error("需要 Node.js 22.12+ 或 20.19+"); process.exit(1)}'
cd "$WORKSPACE_ROOT"
if [[ -n "${YUHENG_UI_PACKAGE:-}" ]]; then
  echo 'YUHENG_UI_PACKAGE 覆盖暂由 workspace 构建流程管理；请将覆盖包安装到 workspace 后再执行打包。' >&2
  exit 1
fi
pnpm install --frozen-lockfile --ignore-scripts
pnpm --filter yuheng-demo-ui typecheck
pnpm --filter yuheng-demo-ui build
[[ -f "$ROOT/yuheng-demo-ui/dist/index.html" ]] || { echo '前端构建未生成 dist/index.html' >&2; exit 1; }
rm -rf "$ROOT/yuheng-demo-server/yuheng-demo-server-bootstrap/target/classes/static"
