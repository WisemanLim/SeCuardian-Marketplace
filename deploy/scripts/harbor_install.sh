#!/usr/bin/env bash
# Harbor 2.11.2 설치 스크립트 — E03 T03-1
# License: Apache-2.0
# ⚠️  초기 실행: ~780MB 다운로드 (Harbor offline installer)
# 사용: make harbor-install  또는  bash deploy/scripts/harbor_install.sh

set -euo pipefail

HARBOR_VERSION="${HARBOR_VERSION:-v2.11.2}"
HARBOR_HTTP_PORT="${HARBOR_HTTP_PORT:-8083}"
HARBOR_ADMIN_PASSWORD="${HARBOR_ADMIN_PASSWORD:-Harbor@Secuardian2026!}"
HARBOR_DB_PASSWORD="${HARBOR_DB_PASSWORD:-harbor-db-secuardian-2026}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${PROJECT_ROOT}/deploy/docker/harbor-config"
DATA_DIR="${PROJECT_ROOT}/deploy/docker/harbor-data"
LOG_DIR="/var/log/harbor"
INSTALLER_TMP="/tmp/harbor-installer-${HARBOR_VERSION}"

echo "=== Harbor ${HARBOR_VERSION} 설치 ==="
echo "⚠️  Harbor License: Apache-2.0 — 상업적 사용 허용"
echo ""

# 이미 설치됐는지 확인 (멱등)
if [[ -d "${CONFIG_DIR}/common/config" ]]; then
    echo "✅ Harbor config 이미 존재 (${CONFIG_DIR}/common/config)"
    echo "   재설치: rm -rf ${CONFIG_DIR} && make harbor-install"
    echo "   기동: make harbor-up"
    exit 0
fi

# curl 확인
if ! command -v curl &>/dev/null; then
    echo "❌ curl 필요. 설치 후 재실행."
    exit 1
fi

# Docker 확인
if ! command -v docker &>/dev/null; then
    echo "❌ Docker 필요. 설치 후 재실행."
    exit 1
fi

# 다운로드
echo "📦 Harbor ${HARBOR_VERSION} offline installer 다운로드..."
echo "   (~780MB, 네트워크 속도에 따라 수 분 소요)"
mkdir -p "${INSTALLER_TMP}"
INSTALLER_TGZ="${INSTALLER_TMP}/harbor.tgz"

curl -L --progress-bar \
    -o "${INSTALLER_TGZ}" \
    "https://github.com/goharbor/harbor/releases/download/${HARBOR_VERSION}/harbor-offline-installer-${HARBOR_VERSION}.tgz"

echo "📂 압축 해제..."
tar xzf "${INSTALLER_TGZ}" -C "${INSTALLER_TMP}"
HARBOR_DIR="${INSTALLER_TMP}/harbor"

# harbor.yml 생성 (템플릿 치환)
echo "⚙️  harbor.yml 생성..."
mkdir -p "${CONFIG_DIR}"
mkdir -p "${DATA_DIR}"
sudo mkdir -p "${LOG_DIR}" 2>/dev/null || mkdir -p "${LOG_DIR}" 2>/dev/null || true

sed \
    -e "s|HARBOR_ADMIN_PASSWORD_VALUE|${HARBOR_ADMIN_PASSWORD}|g" \
    -e "s|HARBOR_DB_PASSWORD_VALUE|${HARBOR_DB_PASSWORD}|g" \
    -e "s|HARBOR_DATA_DIR_VALUE|${DATA_DIR}|g" \
    -e "s|HARBOR_LOG_DIR_VALUE|${LOG_DIR}|g" \
    "${PROJECT_ROOT}/deploy/docker/harbor.yml.template" > "${HARBOR_DIR}/harbor.yml"

# prepare 실행 (설정 파일 생성)
echo "🔧 prepare 실행 (설정파일 생성)..."
cd "${HARBOR_DIR}"
./prepare

# harbor-config/ 에 복사
echo "📁 설정파일 → deploy/docker/harbor-config/"
mkdir -p "${CONFIG_DIR}/common"
cp -r "${HARBOR_DIR}/common/config" "${CONFIG_DIR}/common/config"
cp "${HARBOR_DIR}/harbor.yml" "${CONFIG_DIR}/harbor.yml"

# 데이터 디렉터리 구조 생성
mkdir -p "${DATA_DIR}"/{registry,database,redis,ca_download,job_logs}

echo ""
echo "✅ Harbor 설치 완료!"
echo "   설정: deploy/docker/harbor-config/"
echo "   데이터: ${DATA_DIR}"
echo ""
echo "다음 단계:"
echo "  1. make harbor-up          # Harbor 기동"
echo "  2. 헬스 대기: curl http://localhost:${HARBOR_HTTP_PORT}/api/v2.0/health"
echo "  3. make harbor-setup       # 프로젝트 + Robot Account 생성"
echo ""
echo "Harbor UI: http://localhost:${HARBOR_HTTP_PORT}"
echo "Admin:     admin / ${HARBOR_ADMIN_PASSWORD}"
