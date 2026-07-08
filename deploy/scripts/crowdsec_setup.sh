#!/usr/bin/env bash
# crowdsec_setup.sh — E04 T04-2
# CrowdSec 초기 설정: Bouncer API Key 발급 + .env.crowdsec 갱신
# 실행: make crowdsec-setup (crowdsec-up 이후)
set -euo pipefail

CONTAINER="${CROWDSEC_CONTAINER:-secuardian-crowdsec}"
ENV_FILE="${ENV_FILE:-deploy/docker/.env.crowdsec}"
BOUNCER_NAME="${BOUNCER_NAME:-caddy-bouncer}"

# 컨테이너 동작 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "❌ ${CONTAINER} 미실행 — make crowdsec-up 먼저 실행"
  exit 1
fi

echo "▶ CrowdSec Bouncer API Key 발급 중..."

# 기존 bouncer 있으면 삭제 후 재발급 (idempotent)
docker exec "${CONTAINER}" cscli bouncers delete "${BOUNCER_NAME}" 2>/dev/null || true

BOUNCER_KEY=$(docker exec "${CONTAINER}" cscli bouncers add "${BOUNCER_NAME}" -o raw 2>/dev/null | tail -1)

if [[ -z "${BOUNCER_KEY}" ]]; then
  echo "❌ Bouncer Key 발급 실패"
  exit 1
fi

echo "✅ Bouncer Key 발급 완료: ${BOUNCER_KEY:0:8}..."

# .env.crowdsec 갱신 (CROWDSEC_BOUNCER_KEY 라인만 교체)
if [[ -f "${ENV_FILE}" ]]; then
  if grep -q "^CROWDSEC_BOUNCER_KEY=" "${ENV_FILE}"; then
    # macOS sed -i requires extension
    sed -i.bak "s|^CROWDSEC_BOUNCER_KEY=.*|CROWDSEC_BOUNCER_KEY=${BOUNCER_KEY}|" "${ENV_FILE}" && rm -f "${ENV_FILE}.bak"
  else
    echo "CROWDSEC_BOUNCER_KEY=${BOUNCER_KEY}" >> "${ENV_FILE}"
  fi
  echo "✅ ${ENV_FILE} 업데이트 완료 (CROWDSEC_BOUNCER_KEY)"
fi

echo ""
echo "▶ Simulation mode 활성화 (초기 2주 권장)..."
docker exec "${CONTAINER}" cscli simulation enable && echo "  ✅ Simulation mode ON (탐지만, 실제 차단 없음)"

echo ""
echo "ℹ  Bouncer Key는 Vault에도 저장 권장:"
echo "   vault kv put secret/secuardian/crowdsec bouncer_key=${BOUNCER_KEY:0:8}..."
echo ""
echo "ℹ  현재 등록된 Bouncer:"
docker exec "${CONTAINER}" cscli bouncers list
echo ""
echo "ℹ  Simulation 해제 (2주 후): make crowdsec-cscli CMD=\"cscli simulation disable\""
