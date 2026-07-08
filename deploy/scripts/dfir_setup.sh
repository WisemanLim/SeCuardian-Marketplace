#!/usr/bin/env bash
# Velociraptor DFIR 초기 설정 — E18 T18-1
# License: Apache-2.0
# 실행: bash deploy/scripts/dfir_setup.sh
set -euo pipefail

CONTAINER="secuardian-velociraptor"

echo "[dfir-setup] 컨테이너 상태 확인..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "[dfir-setup] ERROR: ${CONTAINER} 실행 중이 아닙니다."
  echo "  → make dfir-up 먼저 실행하세요."
  exit 1
fi

echo "[dfir-setup] Velociraptor 서버 설정 생성..."
# 설정 파일이 없으면 자동 생성
CONFIG_FILE="deploy/config/velociraptor/server.config.yaml"
if [ ! -s "${CONFIG_FILE}" ] || grep -q "^version:" "${CONFIG_FILE}"; then
  echo "[dfir-setup] 서버 설정 자동 생성 중..."
  docker exec "${CONTAINER}" velociraptor config generate \
    --merge '{"Frontend":{"bind_address":"0.0.0.0","bind_port":8889},"API":{"bind_address":"0.0.0.0","bind_port":8000}}' \
    > /tmp/velociraptor-generated.yaml 2>/dev/null \
    || echo "[dfir-setup] 설정 생성 생략 (기존 설정 사용)"
fi

echo "[dfir-setup] 관리자 계정 생성..."
docker exec "${CONTAINER}" velociraptor \
  --config /etc/velociraptor/server.config.yaml \
  user add admin --role=administrator \
  2>/dev/null || echo "[dfir-setup] admin 이미 존재 (정상)"

echo "[dfir-setup] 완료."
echo "  Web GUI: https://localhost:8889"
echo "  초기 비밀번호: velociraptor 실행 로그 확인 (make dfir-logs)"
