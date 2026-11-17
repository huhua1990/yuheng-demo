#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
command -v mvn >/dev/null || { echo '需要 Maven' >&2; exit 1; }
BACKEND_JAR="$ROOT/yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
BACKEND_JAR_ORIGINAL="$BACKEND_JAR.original"
if [[ -f "$BACKEND_JAR" || -f "$BACKEND_JAR_ORIGINAL" ]]; then
  command -v lsof >/dev/null || { echo '构建前需安装 lsof，以确认后端 JAR 未被运行进程占用' >&2; exit 1; }
  for jar in "$BACKEND_JAR" "$BACKEND_JAR_ORIGINAL"; do
    [[ -f "$jar" ]] || continue
    if lsof "$jar" >/dev/null 2>&1; then
      echo '后端 JAR 正被运行进程使用；请先运行 scripts/stop.sh，再重新构建' >&2
      exit 1
    fi
  done
fi
echo '构建后端并将前端资源打入 JAR...'
mvn -DskipTests package
echo "构建完成: $ROOT/yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar 和 $ROOT/yuheng-demo-ui/dist"
