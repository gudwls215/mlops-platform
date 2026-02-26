#!/bin/bash
##############################################################################
#  프론트엔드 운영 서비스 관리 스크립트
#  - systemd 서비스 기반 (터미널 종료해도 프론트엔드 유지)
#  - 자동 재시작, 부팅 시 자동 시작
#  - 사용법: ./start-frontend-prod.sh [start|stop|restart|status|logs|install]
##############################################################################

set -euo pipefail

# ──────────────── 설정 ────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
BUILD_DIR="${FRONTEND_DIR}/build"
SERVE_BIN="${FRONTEND_DIR}/node_modules/.bin/serve"
SERVICE_NAME="frontend-prod"
SERVICE_FILE="${SCRIPT_DIR}/${SERVICE_NAME}.service"
SYSTEMD_LINK="/etc/systemd/system/${SERVICE_NAME}.service"
PORT=9001
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/frontend-prod.log"

# ──────────────── 유틸리티 ────────────────
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$1] $2"
    mkdir -p "${LOG_DIR}"
    echo "${msg}" >> "${LOG_FILE}"
    echo "${msg}"
}

print_help() {
    echo ""
    echo "  프론트엔드 운영 서비스 관리"
    echo "  ──────────────────────────────────────"
    echo "  사용법: $0 [명령]"
    echo ""
    echo "  명령:"
    echo "    install   systemd 서비스 등록 (최초 1회)"
    echo "    start     서비스 시작"
    echo "    stop      서비스 중지"
    echo "    restart   서비스 재시작"
    echo "    status    서비스 상태 확인"
    echo "    logs      실시간 로그 보기 (Ctrl+C로 종료)"
    echo "    health    헬스체크"
    echo ""
}

# ──────────────── 빌드 확인 ────────────────
ensure_build() {
    if [[ ! -f "${BUILD_DIR}/index.html" ]]; then
        log "WARN" "빌드 파일 없음. 프로덕션 빌드 실행..."
        cd "${FRONTEND_DIR}"
        NODE_OPTIONS="--max-old-space-size=4096" GENERATE_SOURCEMAP=false npm run build:prod 2>&1 | tee -a "${LOG_FILE}"
        if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
            log "ERROR" "빌드 실패!"
            exit 1
        fi
    fi
}

# ──────────────── serve 바이너리 확인 ────────────────
ensure_serve() {
    if [[ ! -x "${SERVE_BIN}" ]]; then
        log "WARN" "serve 바이너리 없음. npm install 실행..."
        cd "${FRONTEND_DIR}" && npm install 2>&1 | tee -a "${LOG_FILE}"
    fi
}

# ──────────────── 정적 파일 동기화 (favicon 등) ────────────────
sync_static_files() {
    if [[ -d "${BUILD_DIR}" ]]; then
        log "INFO" "public → build 정적 파일 동기화 중..."
        local synced=0
        for fname in favicon.ico logo192.png logo512.png manifest.json robots.txt; do
            local src="${FRONTEND_DIR}/public/${fname}"
            local dst="${BUILD_DIR}/${fname}"
            if [[ -f "${src}" ]] && ! cmp -s "${src}" "${dst}" 2>/dev/null; then
                cp "${src}" "${dst}"
                log "INFO" "  ↳ ${fname} 업데이트됨"
                synced=$((synced + 1))
            fi
        done
        if [[ ${synced} -eq 0 ]]; then
            log "INFO" "  모든 정적 파일 최신 상태"
        fi
    fi
}

# ──────────────── systemd 서비스 설치 ────────────────
do_install() {
    log "INFO" "============================================"
    log "INFO" "systemd 서비스 설치"
    log "INFO" "============================================"

    # 사전 점검
    ensure_serve
    ensure_build
    sync_static_files

    # 서비스 파일 존재 확인
    if [[ ! -f "${SERVICE_FILE}" ]]; then
        log "ERROR" "서비스 파일 없음: ${SERVICE_FILE}"
        exit 1
    fi

    # 심볼릭 링크 생성
    log "INFO" "서비스 파일 등록: ${SYSTEMD_LINK}"
    sudo ln -sf "${SERVICE_FILE}" "${SYSTEMD_LINK}"
    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE_NAME}"
    log "INFO" "✅ 서비스 등록 완료 (부팅 시 자동 시작)"

    # 바로 시작
    do_start
}

# ──────────────── 시작 ────────────────
do_start() {
    log "INFO" "============================================"
    log "INFO" "프론트엔드 운영 서비스 시작"
    log "INFO" "============================================"

    # 시작 전 정적 파일 동기화
    sync_static_files

    # 기존 포트 점유 프로세스 정리 (systemd 외 잔여 프로세스)
    local old_pids
    old_pids=$(lsof -ti:${PORT} 2>/dev/null || true)
    if [[ -n "${old_pids}" ]]; then
        if ! systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
            log "WARN" "포트 ${PORT} 점유 프로세스 정리: ${old_pids}"
            echo "${old_pids}" | xargs -r kill -9 2>/dev/null || true
            sleep 1
        fi
    fi

    sudo systemctl start "${SERVICE_NAME}"
    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        local pid
        pid=$(systemctl show -p MainPID --value "${SERVICE_NAME}")
        log "INFO" "────────────────────────────────────────────"
        log "INFO" "🚀 프론트엔드 운영 가동 완료"
        log "INFO" "   URL: http://0.0.0.0:${PORT}"
        log "INFO" "   PID: ${pid}"
        log "INFO" "   터미널 종료해도 서비스 유지됨"
        log "INFO" "────────────────────────────────────────────"
    else
        log "ERROR" "서비스 시작 실패"
        sudo systemctl status "${SERVICE_NAME}" --no-pager -l
        exit 1
    fi
}

# ──────────────── 중지 ────────────────
do_stop() {
    log "INFO" "프론트엔드 서비스 중지..."
    sudo systemctl stop "${SERVICE_NAME}"
    log "INFO" "✅ 서비스 중지됨"
}

# ──────────────── 재시작 ────────────────
do_restart() {
    log "INFO" "프론트엔드 서비스 재시작..."
    sync_static_files
    sudo systemctl restart "${SERVICE_NAME}"
    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        local pid
        pid=$(systemctl show -p MainPID --value "${SERVICE_NAME}")
        log "INFO" "🔄 재시작 성공 (PID: ${pid})"
    else
        log "ERROR" "재시작 실패"
        sudo systemctl status "${SERVICE_NAME}" --no-pager -l
        exit 1
    fi
}

# ──────────────── 상태 확인 ────────────────
do_status() {
    echo ""
    echo "  ──── systemd 서비스 상태 ────"
    sudo systemctl status "${SERVICE_NAME}" --no-pager -l 2>/dev/null || echo "  서비스 미등록 (install 먼저 실행하세요)"
    echo ""

    # 헬스체크
    echo "  ──── 헬스체크 ────"
    if curl -sf -o /dev/null --connect-timeout 3 "http://127.0.0.1:${PORT}" 2>/dev/null; then
        echo "  ✅ HTTP 응답 정상 (포트 ${PORT})"
    else
        echo "  ❌ HTTP 응답 없음 (포트 ${PORT})"
    fi
    echo ""
}

# ──────────────── 로그 ────────────────
do_logs() {
    echo "  실시간 로그 (Ctrl+C로 종료)"
    echo "  ──────────────────────────────────────"
    sudo journalctl -u "${SERVICE_NAME}" -f --no-pager
}

# ──────────────── 헬스체크 ────────────────
do_health() {
    if curl -sf -o /dev/null --connect-timeout 3 "http://127.0.0.1:${PORT}" 2>/dev/null; then
        echo "✅ healthy (port ${PORT})"
        exit 0
    else
        echo "❌ unhealthy (port ${PORT})"
        exit 1
    fi
}

# ──────────────── 메인 ────────────────
case "${1:-}" in
    install)  do_install ;;
    start)    do_start ;;
    stop)     do_stop ;;
    restart)  do_restart ;;
    status)   do_status ;;
    logs)     do_logs ;;
    health)   do_health ;;
    *)        print_help ;;
esac
 