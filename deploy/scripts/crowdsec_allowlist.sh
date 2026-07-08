#!/usr/bin/env bash
# crowdsec_allowlist.sh — E04 T04-2
# 내부 IP 대역 CrowdSec Allowlist 등록 (FP 차단 방지)
# 실행: make crowdsec-allowlist (crowdsec-up 이후)
set -euo pipefail

CONTAINER="${CROWDSEC_CONTAINER:-secuardian-crowdsec}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "❌ ${CONTAINER} 미실행 — make crowdsec-up 먼저 실행"
  exit 1
fi

echo "▶ CrowdSec Allowlist 등록 중..."

# 내부 IP 대역 등록 (RFC 1918)
ALLOWLIST=(
  "10.0.0.0/8"
  "172.16.0.0/12"
  "192.168.0.0/16"
  "127.0.0.1"
  "::1"
)

for CIDR in "${ALLOWLIST[@]}"; do
  docker exec "${CONTAINER}" cscli decisions add \
    --ip "${CIDR}" --type allow --duration 8760h --reason "internal-network" 2>/dev/null \
    || docker exec "${CONTAINER}" cscli allowlists add \
        --name "internal-${CIDR//\//-}" \
        --ip "${CIDR}" \
        --reason "RFC1918 internal network" 2>/dev/null \
    || echo "  (skip ${CIDR} — 이미 등록됐거나 명령 미지원)"
  echo "  ✅ ${CIDR}"
done

echo ""
echo "ℹ  현재 Allowlist / Decisions:"
docker exec "${CONTAINER}" cscli decisions list --type allow 2>/dev/null || true
