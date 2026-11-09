#!/bin/sh

################################################################################
# Yuheng Demo 管理脚本
# 功能: 前后端构建、启动、停止、重启、查看状态
# 作者: Auto Generated
# 日期: 2026-11-03
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
BACKEND_DIR="${PROJECT_DIR}"
FRONTEND_DIR="${PROJECT_DIR}/yuheng-demo-ui"
BUILD_DIR="${PROJECT_DIR}/target"
DIST_DIR="${FRONTEND_DIR}/dist"

# 应用配置
APP_NAME="yuheng-demo"
JAR_NAME="${APP_NAME}.jar"
PID_FILE="${PROJECT_DIR}/${APP_NAME}.pid"
LOG_FILE="${PROJECT_DIR}/logs/application.log"
TENANT_NAME="${TENANT_NAME:-芋道源码}"
READINESS_ATTEMPTS="${YUHENG_READINESS_ATTEMPTS:-30}"
READINESS_INTERVAL="${YUHENG_READINESS_INTERVAL:-2}"

# Spring Boot 配置
SPRING_PROFILE="${SPRING_PROFILE:-local}"  # 默认使用 local 环境
SERVER_PORT="${SERVER_PORT:-48080}"        # 默认端口

# JVM 参数配置
JVM_OPTS="${JVM_OPTS:--Xms512m -Xmx1024m -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m}"

# Node 配置
FRONTEND_PORT="${FRONTEND_PORT:-3000}"     # 前端开发端口（与 vite.config.ts 保持一致）

################################################################################
# 工具函数
################################################################################

# 打印带颜色的消息
log_info() {
    printf '%b\n' "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    printf '%b\n' "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    printf '%b\n' "${RED}[ERROR]${NC} $1"
}

log_step() {
    printf '%b\n' "${BLUE}[STEP]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 命令未找到，请先安装 $1"
        exit 1
    fi
}

# Vite requires Node >= 20.19 or >= 22.12; choose an installed compatible runtime.
use_compatible_node() {
    local candidate node_bin
    node_bin=$(command -v node 2>/dev/null || true)
    if [ -n "${node_bin}" ]; then
        candidate=$("${node_bin}" -p 'process.versions.node' 2>/dev/null || true)
        if node_version_ok "${candidate}"; then
            return 0
        fi
    fi

    for node_bin in "${NVM_DIR:-${HOME}/.nvm}"/versions/node/*/bin; do
        candidate=$(basename "$(dirname "${node_bin}")")
        if [ -x "${node_bin}/node" ] && node_version_ok "$("${node_bin}/node" -p 'process.versions.node' 2>/dev/null || true)"; then
            PATH="${node_bin}:${PATH}"
            export PATH
            log_info "使用兼容 Node ${candidate}: ${node_bin}"
            return 0
        fi
    done

    log_error "Node 版本不满足 Vite 要求（>=20.19 或 >=22.12）"
    return 1
}

node_version_ok() {
    printf '%s\n' "$1" | awk '
        function split_version(value, major, minor) {
            if (split(value, parts, ".") < 2) return 0
            major = parts[1] + 0; minor = parts[2] + 0
            return (major > 22 || (major == 22 && minor >= 12) || (major == 20 && minor >= 19))
        }
        BEGIN { ok = 0 }
        { ok = split_version($0) }
        END { exit !ok }
    '
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -nP -iTCP:${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warn "端口 ${port} 已被占用"
        lsof -nP -iTCP:${port} -sTCP:LISTEN
        return 1
    fi
    return 0
}

# Validate the actual Java service, not a PID, port, or JAR basename alone.
owned_backend_process() {
    case "$1" in ''|*[!0-9]*) return 1 ;; esac
    [ "$1" -gt 1 ] || return 1
    local command executable process_cwd
    executable=$(ps -p "$1" -o comm= 2>/dev/null) || return 1
    case "${executable}" in java|*/java) ;; *) return 1 ;; esac
    command=$(ps -ww -p "$1" -o args= 2>/dev/null) || return 1
    case " ${command} " in
        *" -jar ${BUILD_DIR}/${JAR_NAME} "*) ;;
        *" -jar target/${JAR_NAME} "*|*" -jar ./target/${JAR_NAME} "*)
            # Relative argv is ambiguous until the OS confirms this process cwd.
            process_cwd=$(lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
            [ -n "${process_cwd}" ] || return 1
            process_cwd=$(CDPATH='' cd -P -- "${process_cwd}" 2>/dev/null && pwd -P) || return 1
            [ "${process_cwd}" = "$(CDPATH='' cd -P -- "${PROJECT_DIR}" && pwd -P)" ] || return 1
            ;;
        *) return 1 ;;
    esac
    case " ${command} " in *" -Dserver.port=${SERVER_PORT} "*) ;; *) return 1 ;; esac
    case " ${command} " in *" -Dspring.profiles.active=${SPRING_PROFILE} "*) ;; *) return 1 ;; esac
}

record_backend_pid() {
    local born
    born=$(ps -p "$1" -o lstart= 2>/dev/null) || return 1
    [ -n "${born}" ] || return 1
    printf '%s\n%s\n' "$1" "${born}" > "${PID_FILE}"
}

is_running() {
    local born current
    [ -f "${PID_FILE}" ] || return 1
    BACKEND_PID=$(sed -n '1p' "${PID_FILE}")
    born=$(sed -n '2p' "${PID_FILE}")
    if owned_backend_process "${BACKEND_PID}"; then
        current=$(ps -p "${BACKEND_PID}" -o lstart= 2>/dev/null) || return 1
        # A legacy one-line PID may be adopted only after validating the exact command.
        if [ -z "${born}" ] || [ "${born}" = "${current}" ]; then
            record_backend_pid "${BACKEND_PID}"
            return 0
        fi
    fi
    rm -f "${PID_FILE}"
    return 1
}

find_backend_listener() {
    local pid
    for pid in $(lsof -nP -iTCP:"${SERVER_PORT}" -sTCP:LISTEN -t 2>/dev/null); do
        if owned_backend_process "${pid}"; then
            BACKEND_PID=${pid}
            record_backend_pid "${pid}" || return 1
            return 0
        fi
    done
    return 1
}

################################################################################
# 后端相关函数
################################################################################

# 构建后端
build_backend() {
    log_step "开始构建后端项目..."

    check_command mvn

    cd "${BACKEND_DIR}"

    # 检查是否需要先构建 yuheng-core
    if [ ! -f "${HOME}/.m2/repository/com/yuheng/yuheng-server/0.1.0-SNAPSHOT/yuheng-server-0.1.0-SNAPSHOT.jar" ]; then
        log_warn "未找到 yuheng-server 依赖，是否需要先构建 yuheng-core？"
        log_warn "如果需要，请执行: cd ../yuheng-core && mvn clean install -DskipTests"
    fi

    log_info "执行 Maven 构建..."
    mvn clean package -DskipTests

    if [ -f "${BUILD_DIR}/${JAR_NAME}" ]; then
        log_info "后端构建成功: ${BUILD_DIR}/${JAR_NAME}"
    else
        log_error "后端构建失败，未找到 JAR 文件"
        exit 1
    fi
}

# 启动后端
start_backend() {
    check_command lsof
    check_command curl
    use_compatible_node || return 1
    if is_running || find_backend_listener; then
        log_warn "后端服务已在运行中 (PID: ${BACKEND_PID})"
        wait_for_backend
        return $?
    fi

    if [ ! -f "${BUILD_DIR}/${JAR_NAME}" ]; then
        log_error "未找到 JAR 文件，请先执行构建"
        exit 1
    fi

    # 检查端口
    if ! check_port ${SERVER_PORT}; then
        log_error "端口 ${SERVER_PORT} 被占用，无法启动"
        exit 1
    fi

    log_step "启动后端服务..."

    # 创建日志目录
    mkdir -p "$(dirname "${LOG_FILE}")"

    # 启动 Spring Boot 应用
    nohup java ${JVM_OPTS} \
        "-Dspring.profiles.active=${SPRING_PROFILE}" \
        "-Dserver.port=${SERVER_PORT}" \
        -jar "${BUILD_DIR}/${JAR_NAME}" \
        > "${LOG_FILE}" 2>&1 &

    local pid attempt=0 born current
    pid=$!
    # nohup may still be execing Java. Preserve its birth time while waiting,
    # and do not adopt a process that has reused the just-launched PID.
    born=$(ps -p "${pid}" -o lstart= 2>/dev/null) || {
        log_error "后端进程已退出，请检查日志: ${LOG_FILE}"
        return 1
    }
    while ! owned_backend_process "${pid}"; do
        current=$(ps -p "${pid}" -o lstart= 2>/dev/null) || break
        [ -n "${born}" ] && [ "${born}" = "${current}" ] || break
        [ "${attempt}" -lt 5 ] || break
        attempt=$((attempt + 1))
        sleep 1
    done
    current=$(ps -p "${pid}" -o lstart= 2>/dev/null) || current=''
    if ! owned_backend_process "${pid}" || [ "${born}" != "${current}" ]; then
        log_error "后端进程已退出或归属已改变，请检查日志: ${LOG_FILE}"
        return 1
    fi
    BACKEND_PID=${pid}
    record_backend_pid "${pid}" || return 1

    log_info "后端服务启动中... (PID: ${pid})"
    log_info "日志文件: ${LOG_FILE}"
    log_info "Spring Profile: ${SPRING_PROFILE}"
    log_info "端口: ${SERVER_PORT}"

    # 等待服务启动
    log_info "等待服务启动..."
    wait_for_backend
}

# Use the tenant lookup used by the UI login flow; HTTP 200 with API code 404 is not ready.
wait_for_backend() {
    local attempt=0 response
    case "${READINESS_ATTEMPTS}" in ''|*[!0-9]*) log_error "就绪检查次数必须为正整数"; return 1 ;; esac
    while [ "${attempt}" -lt "${READINESS_ATTEMPTS}" ]; do
        attempt=$((attempt + 1))
        if ! is_running; then
            log_error "后端进程已退出或归属已改变，请检查日志: ${LOG_FILE}"
            return 1
        fi
        if lsof -nP -a -p "${BACKEND_PID}" -iTCP:"${SERVER_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1 &&
            response=$(curl --fail --silent --show-error --max-time 2 --get \
                --data-urlencode "name=${TENANT_NAME}" \
                "http://127.0.0.1:${SERVER_PORT}/admin-api/system/tenant/get-id-by-name" 2>/dev/null) &&
            printf '%s' "${response}" | node -e '
                let input = "";
                process.stdin.setEncoding("utf8");
                process.stdin.on("data", chunk => input += chunk);
                process.stdin.on("end", () => {
                    try {
                        const body = JSON.parse(input);
                        process.exit(body?.code === 0 && Number.isSafeInteger(body.data) && body.data > 0 ? 0 : 1);
                    } catch { process.exit(1); }
                });
            '; then
            log_info "后端服务启动成功！"
            log_info "访问地址: http://localhost:${SERVER_PORT}"
            return 0
        fi
        [ "${attempt}" -ge "${READINESS_ATTEMPTS}" ] || sleep "${READINESS_INTERVAL}"
    done
    log_error "后端服务就绪检查失败（租户: ${TENANT_NAME}），请检查日志: ${LOG_FILE}"
    return 1
}

# 停止后端
stop_backend() {
    if ! is_running; then
        log_warn "后端服务未运行"
        return 0
    fi
    local pid attempt=0
    pid=${BACKEND_PID}
    log_step "停止后端服务 (PID: ${pid})..."
    kill "${pid}" || return 1
    while [ "${attempt}" -lt 30 ]; do
        if ! is_running || [ "${pid}" != "${BACKEND_PID}" ]; then
            log_info "后端服务已停止"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    # Revalidate immediately before escalating; never signal a recycled/unrelated PID.
    if is_running && [ "${pid}" = "${BACKEND_PID}" ]; then
        log_warn "进程未能正常停止，尝试强制终止..."
        kill -9 "${pid}" || return 1
        rm -f "${PID_FILE}"
    fi
    log_info "后端服务已停止"
}

# 查看后端状态
status_backend() {
    if is_running || find_backend_listener; then
        local pid=${BACKEND_PID}
        log_info "后端服务运行中"
        echo "  PID: ${pid}"
        echo "  端口: ${SERVER_PORT}"
        echo "  Profile: ${SPRING_PROFILE}"
        echo "  日志: ${LOG_FILE}"
        echo ""
        echo "进程信息:"
        ps -f -p ${pid}
    else
        log_warn "后端服务未运行"
    fi
}

# 查看后端日志
logs_backend() {
    if [ ! -f "${LOG_FILE}" ]; then
        log_error "日志文件不存在: ${LOG_FILE}"
        exit 1
    fi

    local lines=${1:-100}
    log_info "显示最后 ${lines} 行日志..."
    tail -n ${lines} -f "${LOG_FILE}"
}

################################################################################
# 前端相关函数
################################################################################

# 构建前端
build_frontend() {
    log_step "开始构建前端项目..."

    use_compatible_node || exit 1
    check_command pnpm

    cd "${FRONTEND_DIR}"

    # Build/copy a fresh content-addressed core artifact and install it before building.
    node scripts/verify-local-package.mjs --build

    if [ -d "${DIST_DIR}" ]; then
        log_info "前端构建成功: ${DIST_DIR}"
        du -sh "${DIST_DIR}"
    else
        log_error "前端构建失败，未找到 dist 目录"
        exit 1
    fi
}

# 启动前端开发服务器
start_frontend_dev() {
    log_step "启动前端开发服务器..."

    use_compatible_node || exit 1
    check_command pnpm
    check_command lsof

    cd "${FRONTEND_DIR}"

    # 检查端口
    if ! check_port ${FRONTEND_PORT}; then
        log_error "端口 ${FRONTEND_PORT} 被占用，无法启动"
        exit 1
    fi

    log_info "启动 Vite 开发服务器..."
    log_info "访问地址: http://localhost:${FRONTEND_PORT}"
    node scripts/verify-local-package.mjs --dev
}

################################################################################
# 完整构建和启动
################################################################################

# 完整构建
build_all() {
    log_step "========================================"
    log_step "开始完整构建 (前端 + 后端)"
    log_step "========================================"

    build_backend
    build_frontend

    log_info "========================================"
    log_info "完整构建完成！"
    log_info "========================================"
}

# 启动所有服务
start_all() {
    log_step "========================================"
    log_step "启动所有服务 (后端 + 前端开发服务器)"
    log_step "========================================"

    # 启动后端
    start_backend

    # 启动前端（这会阻塞终端）
    log_info "即将启动前端开发服务器..."
    log_warn "前端服务将占用当前终端，使用 Ctrl+C 停止"

    start_frontend_dev
}

# 停止所有服务
stop_all() {
    log_step "========================================"
    log_step "停止所有服务"
    log_step "========================================"

    stop_backend

    # The foreground frontend is stopped with Ctrl+C; a port alone proves no ownership.
    log_info "前端开发服务器请在其终端使用 Ctrl+C 停止"
    log_info "所有服务已停止"
}

# 重启所有服务
restart_all() {
    log_step "========================================"
    log_step "重启所有服务"
    log_step "========================================"

    stop_all
    sleep 2
    start_all
}

# 清理构建产物
clean_all() {
    log_step "清理构建产物..."

    # 清理后端
    if [ -d "${BUILD_DIR}" ]; then
        log_info "删除后端 target 目录..."
        rm -rf "${BUILD_DIR}"
    fi

    # 清理前端
    if [ -d "${DIST_DIR}" ]; then
        log_info "删除前端 dist 目录..."
        rm -rf "${DIST_DIR}"
    fi

    if [ -d "${FRONTEND_DIR}/node_modules" ]; then
        log_info "删除前端 node_modules 目录..."
        rm -rf "${FRONTEND_DIR}/node_modules"
    fi

    # 清理日志
    if [ -f "${LOG_FILE}" ]; then
        log_info "删除日志文件..."
        rm -f "${LOG_FILE}"
    fi

    # 清理 PID 文件
    if [ -f "${PID_FILE}" ]; then
        rm -f "${PID_FILE}"
    fi

    log_info "清理完成"
}

################################################################################
# 帮助信息
################################################################################

show_help() {
    cat << EOF
${GREEN}Yuheng Demo 管理脚本${NC}

${BLUE}使用方法:${NC}
    $0 [命令] [选项]

${BLUE}命令:${NC}
    ${GREEN}完整操作:${NC}
        build           - 构建前后端
        start           - 启动后端 + 前端开发服务器
        stop            - 停止所有服务
        restart         - 重启所有服务
        status          - 查看所有服务状态
        clean           - 清理构建产物

    ${GREEN}后端操作:${NC}
        build:backend   - 仅构建后端
        start:backend   - 仅启动后端
        stop:backend    - 仅停止后端
        restart:backend - 重启后端
        status:backend  - 查看后端状态
        logs           - 查看后端日志 (默认100行)
        logs [行数]     - 查看指定行数的日志

    ${GREEN}前端操作:${NC}
        build:frontend  - 仅构建前端
        dev:frontend    - 启动前端开发服务器
        start:frontend  - 同 dev:frontend

${BLUE}环境变量:${NC}
    SPRING_PROFILE  - Spring 配置文件 (默认: local)
    SERVER_PORT     - 后端服务端口 (默认: 48080)
    FRONTEND_PORT   - 前端开发端口 (默认: 3000)
    TENANT_NAME     - 就绪检查租户名称 (默认: 芋道源码)
    NVM_DIR         - nvm 安装目录 (默认: ~/.nvm)
    JVM_OPTS        - JVM 参数 (默认: -Xms512m -Xmx1024m ...)

${BLUE}示例:${NC}
    # 完整构建并启动
    $0 build && $0 start

    # 仅启动后端（生产模式）
    SPRING_PROFILE=prod SERVER_PORT=8080 $0 start:backend

    # 查看实时日志
    $0 logs

    # 清理并重新构建
    $0 clean && $0 build

${BLUE}注意事项:${NC}
    1. 首次运行需要先构建 yuheng-core 依赖
    2. 前端开发模式 (start/dev:frontend) 会占用终端
    3. 生产环境建议先构建前端，再通过 Nginx 代理访问
    4. 默认后端端口 48080，前端端口 3000

EOF
}

################################################################################
# 主函数
################################################################################

main() {
    cd "${PROJECT_DIR}"

    case "${1:-}" in
        # 完整操作
        build)
            build_all
            ;;
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        status)
            status_backend
            ;;
        clean)
            clean_all
            ;;

        # 后端操作
        build:backend)
            build_backend
            ;;
        start:backend)
            start_backend
            ;;
        stop:backend)
            stop_backend
            ;;
        restart:backend)
            stop_backend
            sleep 2
            start_backend
            ;;
        status:backend)
            status_backend
            ;;
        logs)
            logs_backend ${2:-100}
            ;;

        # 前端操作
        build:frontend)
            build_frontend
            ;;
        start:frontend|dev:frontend|dev)
            start_frontend_dev
            ;;

        # 帮助
        -h|--help|help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
