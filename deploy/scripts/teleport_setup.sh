#!/usr/bin/env bash
# Teleport PAM 초기 설정 — E17 T17-1
# License: AGPL-3.0
# 실행: bash deploy/scripts/teleport_setup.sh
set -euo pipefail

CONTAINER="secuardian-teleport"

echo "[teleport-setup] 컨테이너 상태 확인..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "[teleport-setup] ERROR: ${CONTAINER} 실행 중이 아닙니다."
  echo "  → make teleport-up 먼저 실행하세요."
  exit 1
fi

echo "[teleport-setup] Teleport 클러스터 준비 대기 (최대 30초)..."
for i in $(seq 1 30); do
  if docker exec "${CONTAINER}" tctl status &>/dev/null; then
    break
  fi
  sleep 1
done

echo "[teleport-setup] 관리자 초대 링크 생성..."
docker exec "${CONTAINER}" tctl users add admin \
  --roles=editor,access \
  --logins=root,ubuntu \
  || echo "[teleport-setup] 이미 admin 사용자 존재 (정상)"

echo "[teleport-setup] 노드 등록 토큰 발급 (1시간 유효)..."
docker exec "${CONTAINER}" tctl tokens add \
  --type=node \
  --ttl=1h \
  || echo "[teleport-setup] 토큰 발급 생략"

echo "[teleport-setup] 세션 녹화 정책 확인..."
docker exec "${CONTAINER}" tctl get cluster_auth_preference \
  --format=text 2>/dev/null || true

echo "[teleport-setup] 완료."
echo "  Web UI: https://localhost:3080"
echo "  tsh login --proxy=localhost:3080 --user=admin"
