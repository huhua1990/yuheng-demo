#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUNTIME="$ROOT/logs/lifecycle"
LAUNCHD_DOMAIN="gui/$(id -u)"
result=0
for component in ui backend; do
  file="$RUNTIME/$component.pid"
  [[ -f "$file" ]] || { echo "$component: 没有由脚本记录的进程"; continue; }
  IFS='|' read -r pid started marker label < "$file" || true
  if [[ ! "${pid:-}" =~ ^[0-9]+$ || -z "${started:-}" || ! "${marker:-}" =~ ^yuheng-(backend|ui)-[0-9]+-[0-9]+$ ]]; then
    echo "$component: PID 文件无效，未停止任何进程" >&2; result=1; continue
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    if [[ -n "${label:-}" ]] && command -v launchctl >/dev/null && [[ "$(uname -s)" == "Darwin" ]]; then
      launchctl bootout "$LAUNCHD_DOMAIN/$label" 2>/dev/null || true
    fi
    rm -f "$file" "$RUNTIME/$component.plist"; echo "$component: 进程已退出"; continue
  fi
  actual_started=$(ps -p "$pid" -o lstart= | xargs)
  actual_command=$(ps -p "$pid" -o command=)
  if [[ "$actual_started" != "$started" || "$actual_command" != *"$marker"* ]]; then
    echo "$component: 进程身份不匹配，未停止 PID $pid" >&2; result=1; continue
  fi
  if [[ -n "${label:-}" ]] && command -v launchctl >/dev/null && [[ "$(uname -s)" == "Darwin" ]]; then
    launchctl bootout "$LAUNCHD_DOMAIN/$label" 2>/dev/null || kill "$pid"
  else
    kill "$pid"
  fi
  for ((i=0; i<50; i++)); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "$component: 进程未退出，保留 PID 文件" >&2; result=1
  else
    rm -f "$file" "$RUNTIME/$component.plist"; echo "$component: 已停止"
  fi
done
exit "$result"
