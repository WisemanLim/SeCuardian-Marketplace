#!/usr/bin/env bash
# Source: SeCuardian | License: BUSL-1.1 (Vault) | Usage: internal only
# E02 T02-1: Vault Dev 모드 초기화 스크립트
# - vault server -dev 는 자동 init + unseal — 이 스크립트는 상태 확인 + 기본 시크릿 경로 생성
# - Vault CLI 호스트 미설치 시 curl 로 HTTP API 호출
# 사용법: bash deploy/scripts/vault_init.sh

set -euo pipefail

VAULT_PORT="${VAULT_PORT:-8201}"
VAULT_ADDR="${VAULT_ADDR:-http://localhost:${VAULT_PORT}}"
VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN:-dev-root-token-secuardian}"

_vault_api() {
    local method="$1" path="$2"
    local data="${3:-}"
    local args=(-sf -X "$method" "${VAULT_ADDR}${path}" -H "X-Vault-Token: ${VAULT_TOKEN}" -H "Content-Type: application/json")
    [ -n "$data" ] && args+=(-d "$data")
    curl "${args[@]}"
}

echo "▶ Vault 상태 확인: ${VAULT_ADDR}"
STATUS=$(_vault_api GET /v1/sys/health || true)
echo "${STATUS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  initialized={d[\"initialized\"]}  sealed={d[\"sealed\"]}  version={d[\"version\"]}')"

echo ""
echo "▶ KV v2 시크릿 엔진 확인"
MOUNTS=$(_vault_api GET /v1/sys/mounts || echo "{}")
if echo "${MOUNTS}" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'secret/' in d else 1)" 2>/dev/null; then
    echo "  ✓ kv-v2 (secret/) 이미 활성화"
else
    _vault_api POST /v1/sys/mounts/secret '{"type":"kv","options":{"version":"2"}}' > /dev/null
    echo "  ✓ kv-v2 활성화"
fi

echo ""
echo "▶ SeCuardian 초기 시크릿 경로 생성"
_vault_api POST /v1/secret/data/secuardian/keycloak \
    '{"data":{"admin_password":"CHANGE_ME","client_secret":"CHANGE_ME"}}' > /dev/null
echo "  ✓ secret/secuardian/keycloak"

_vault_api POST /v1/secret/data/secuardian/logto \
    '{"data":{"app_secret":"CHANGE_ME"}}' > /dev/null
echo "  ✓ secret/secuardian/logto"

_vault_api POST /v1/secret/data/secuardian/app \
    '{"data":{"jwt_secret":"CHANGE_ME_32CHARS_MIN"}}' > /dev/null
echo "  ✓ secret/secuardian/app"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vault Dev — Root Token: ${VAULT_TOKEN}"
echo "  UI: ${VAULT_ADDR}/ui"
echo "  ⚠ Root Token 최소 사용 — T02-2에서 AppRole 로 교체"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
