#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUNTIME="$ROOT/logs/lifecycle"
BACKEND_PORT=${BACKEND_PORT:-48080}
UI_PORT=${UI_PORT:-5173}
UI_HOST=${UI_HOST:-127.0.0.1}
export SPRING_DATA_REDIS_HOST="${YUHENG_REDIS_HOST:-${SPRING_DATA_REDIS_HOST:-127.0.0.1}}"
export SPRING_DATA_REDIS_PORT="${YUHENG_REDIS_PORT:-${SPRING_DATA_REDIS_PORT:-6379}}"
export SPRING_DATA_REDIS_DATABASE="${YUHENG_REDIS_DATABASE:-${SPRING_DATA_REDIS_DATABASE:-0}}"
BACKEND_JAR="$ROOT/yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
LAUNCHD_DOMAIN="gui/$(id -u)"
BACKEND_LABEL="com.yuheng.demo.backend"
UI_LABEL="com.yuheng.demo.ui"
[[ -f "$BACKEND_JAR" && -f "$ROOT/yuheng-demo-ui/dist/index.html" ]] || { echo '请先运行 scripts/build.sh' >&2; exit 1; }
command -v python3 >/dev/null || { echo '需要 Python 3' >&2; exit 1; }
command -v java >/dev/null || { echo '需要 Java 17+' >&2; exit 1; }
mkdir -p "$RUNTIME"
for component in backend ui; do
  if [[ -f "$RUNTIME/$component.pid" ]]; then
    echo "$component: PID 文件已存在，请先运行 scripts/stop.sh 检查" >&2; exit 1
  fi
done
python3 - "$BACKEND_PORT" "$UI_PORT" <<'PY'
import socket, sys
ports = [int(value) for value in sys.argv[1:]]
if len(set(ports)) != 2 or any(not 0 < port < 65536 for port in ports):
    raise SystemExit('前后端端口必须不同且在 1-65535 范围内')
for port in ports:
    with socket.socket() as sock:
        try:
            sock.bind(('0.0.0.0', port))
        except OSError:
            raise SystemExit('端口 {} 已被占用'.format(port))
PY
cd "$ROOT"
launchd_enabled=0
if [[ "$(uname -s)" == "Darwin" ]] && command -v launchctl >/dev/null; then
  launchd_enabled=1
fi

write_launchd_plist() {
  local plist="$1"
  local label="$2"
  local program="$3"
  shift 3
  local args=("$@")
  PLIST_PATH="$plist" PLIST_LABEL="$label" PLIST_PROGRAM="$program" \
  PLIST_ARGUMENTS="$(printf '%s\n' "${args[@]}")" \
  PLIST_WORKDIR="$ROOT" PLIST_STDOUT="$RUNTIME/${label##*.}.log" \
  PLIST_STDERR="$RUNTIME/${label##*.}.log" \
  YUHENG_DB_HOST="${YUHENG_DB_HOST-}" \
  YUHENG_DB_PORT="${YUHENG_DB_PORT-}" \
  YUHENG_DB_NAME="${YUHENG_DB_NAME-}" \
  YUHENG_DB_USERNAME="${YUHENG_DB_USERNAME-}" \
  YUHENG_DB_PASSWORD="${YUHENG_DB_PASSWORD-}" \
  YUHENG_REDIS_PASSWORD="${YUHENG_REDIS_PASSWORD-}" \
  YUHENG_REDIS_HOST="${YUHENG_REDIS_HOST-}" \
  YUHENG_REDIS_PORT="${YUHENG_REDIS_PORT-}" \
  YUHENG_REDIS_DATABASE="${YUHENG_REDIS_DATABASE-}" \
  SPRING_DATA_REDIS_HOST="$SPRING_DATA_REDIS_HOST" \
  SPRING_DATA_REDIS_PORT="$SPRING_DATA_REDIS_PORT" \
  SPRING_DATA_REDIS_DATABASE="$SPRING_DATA_REDIS_DATABASE" \
  python3 - <<'PY'
import os
import plistlib
from pathlib import Path

arguments = os.environ["PLIST_ARGUMENTS"].splitlines()
env = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
}
for name in (
    "YUHENG_DB_HOST",
    "YUHENG_DB_PORT",
    "YUHENG_DB_NAME",
    "YUHENG_DB_USERNAME",
    "YUHENG_DB_PASSWORD",
    "YUHENG_REDIS_PASSWORD",
    "YUHENG_REDIS_HOST",
    "YUHENG_REDIS_PORT",
    "YUHENG_REDIS_DATABASE",
    "SPRING_DATA_REDIS_HOST",
    "SPRING_DATA_REDIS_PORT",
    "SPRING_DATA_REDIS_DATABASE",
):
    value = os.environ.get(name)
    if value:
        env[name] = value
data = {
    "Label": os.environ["PLIST_LABEL"],
    "ProgramArguments": [os.environ["PLIST_PROGRAM"], *arguments],
    "WorkingDirectory": os.environ["PLIST_WORKDIR"],
    "StandardOutPath": os.environ["PLIST_STDOUT"],
    "StandardErrorPath": os.environ["PLIST_STDERR"],
    "EnvironmentVariables": env,
    "RunAtLoad": True,
    "ProcessType": "Interactive",
    "ThrottleInterval": 5,
}
path = Path(os.environ["PLIST_PATH"])
path.write_bytes(plistlib.dumps(data, fmt=plistlib.FMT_XML, sort_keys=False))
PY
}

find_marker_pid() {
  local marker="$1"
  ps -axo pid=,command= | awk -v marker="$marker" '$0 ~ marker {print $1; exit}'
}

backend_marker="yuheng-backend-$$-$RANDOM"
backend_plist="$RUNTIME/backend.plist"
if [[ "$launchd_enabled" == 1 ]]; then
  launchctl bootout "$LAUNCHD_DOMAIN/$BACKEND_LABEL" 2>/dev/null || true
  write_launchd_plist "$backend_plist" "$BACKEND_LABEL" "$(command -v java)" \
    "-Dyuheng.lifecycle=$backend_marker" -jar "$BACKEND_JAR" "--server.port=$BACKEND_PORT"
  launchctl bootstrap "$LAUNCHD_DOMAIN" "$backend_plist"
  launchctl kickstart -k "$LAUNCHD_DOMAIN/$BACKEND_LABEL"
else
  nohup java "-Dyuheng.lifecycle=$backend_marker" -jar "$BACKEND_JAR" "--server.port=$BACKEND_PORT" > "$RUNTIME/backend.log" 2>&1 &
fi
backend_pid=""
ready=0
for ((i=0; i<60; i++)); do
  backend_pid=$(find_marker_pid "$backend_marker" || true)
  if [[ -n "$backend_pid" ]] && ! kill -0 "$backend_pid" 2>/dev/null; then backend_pid=""; fi
  if grep -Fq 'Started YuhengDemoApplication' "$RUNTIME/backend.log" 2>/dev/null && python3 - "$BACKEND_PORT" <<'PY'
import socket, sys
try:
    with socket.create_connection(('127.0.0.1', int(sys.argv[1])), timeout=0.5): pass
except OSError: raise SystemExit(1)
PY
  then ready=1; break; fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "后端未就绪，请查看 $RUNTIME/backend.log" >&2
  "$ROOT/scripts/stop.sh" || true
  exit 1
fi
started=$(ps -p "$backend_pid" -o lstart= | xargs)
printf '%s|%s|%s|%s\n' "$backend_pid" "$started" "$backend_marker" "$BACKEND_LABEL" > "$RUNTIME/backend.pid"
ui_marker="yuheng-ui-$$-$RANDOM"
ui_plist="$RUNTIME/ui.plist"
if [[ "$launchd_enabled" == 1 ]]; then
  launchctl bootout "$LAUNCHD_DOMAIN/$UI_LABEL" 2>/dev/null || true
  write_launchd_plist "$ui_plist" "$UI_LABEL" "$(command -v python3)" \
    "$ROOT/scripts/ui_server.py" --root "$ROOT/yuheng-demo-ui/dist" --host "$UI_HOST" \
    --port "$UI_PORT" --backend "http://127.0.0.1:$BACKEND_PORT" --instance "$ui_marker"
  launchctl bootstrap "$LAUNCHD_DOMAIN" "$ui_plist"
  launchctl kickstart -k "$LAUNCHD_DOMAIN/$UI_LABEL"
else
  nohup python3 "$ROOT/scripts/ui_server.py" --root "$ROOT/yuheng-demo-ui/dist" --host "$UI_HOST" --port "$UI_PORT" --backend "http://127.0.0.1:$BACKEND_PORT" --instance "$ui_marker" > "$RUNTIME/ui.log" 2>&1 &
fi
ui_pid=""
for ((i=0; i<10; i++)); do
  ui_pid=$(find_marker_pid "$ui_marker" || true)
  if [[ -n "$ui_pid" ]] && kill -0 "$ui_pid" 2>/dev/null; then break; fi
  ui_pid=""
  sleep 1
done
if [[ -z "$ui_pid" ]]; then
  echo "前端未启动，请查看 $RUNTIME/ui.log" >&2
  "$ROOT/scripts/stop.sh" || true
  exit 1
fi
started=$(ps -p "$ui_pid" -o lstart= | xargs)
printf '%s|%s|%s|%s\n' "$ui_pid" "$started" "$ui_marker" "$UI_LABEL" > "$RUNTIME/ui.pid"
sleep 1
if ! kill -0 "$ui_pid" 2>/dev/null || ! python3 - "$UI_PORT" <<'PY'
import socket, sys
try:
    with socket.create_connection(('127.0.0.1', int(sys.argv[1])), timeout=0.5): pass
except OSError: raise SystemExit(1)
PY
then
  echo "前端未启动，请查看 $RUNTIME/ui.log" >&2
  "$ROOT/scripts/stop.sh" || true
  exit 1
fi
echo "后端: http://127.0.0.1:$BACKEND_PORT"
echo "前端: http://$UI_HOST:$UI_PORT"
echo "日志: $RUNTIME"
