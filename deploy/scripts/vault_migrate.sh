#!/usr/bin/env bash
# Source: SeCuardian | License: BUSL-1.1 (Vault) | Usage: internal only
# E02 T02-3: .env 파일 시크릿 → Vault KV v2 마이그레이션 스크립트
# 사용법: ENV_FILE=.env.local make vault-migrate
#         또는: ENV_FILE=.env.local bash deploy/scripts/vault_migrate.sh

set -euo pipefail

VAULT_PORT="${VAULT_PORT:-8201}"
VAULT_ADDR="${VAULT_ADDR:-http://localhost:${VAULT_PORT}}"
VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN:-dev-root-token-secuardian}"
ENV_FILE="${ENV_FILE:-.env.local}"

export VAULT_ADDR VAULT_TOKEN

_vault_put() {
    local path="$1" body="$2"
    curl -sf -X POST "${VAULT_ADDR}/v1/${path}" \
        -H "X-Vault-Token: ${VAULT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "${body}" > /dev/null
}

_read_env() {
    local key="$1"
    grep -E "^${key}=" "${ENV_FILE}" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/[[:space:]]*#.*//' | tr -d "'\""
}

_json_str() {
    python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vault 시크릿 마이그레이션 — ${ENV_FILE} → ${VAULT_ADDR}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Vault 연결 확인 ──────────────────────────────────────────────────────────
echo ""
echo "▶ Vault 연결 확인"
STATUS=$(curl -sf "${VAULT_ADDR}/v1/sys/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if not d.get('sealed') else 'SEALED')" 2>/dev/null || echo "UNREACHABLE")
if [ "${STATUS}" != "OK" ]; then
    echo "  ✗ Vault 연결 실패: ${STATUS} (make vault-up 먼저 실행)"
    exit 1
fi
echo "  ✓ Vault UP"

# ── env 파일 확인 ────────────────────────────────────────────────────────────
echo ""
echo "▶ env 파일 확인: ${ENV_FILE}"
[ -f "${ENV_FILE}" ] || { echo "  ✗ ${ENV_FILE} 없음"; exit 1; }
echo "  ✓ 파일 존재"

# ── Keycloak 시크릿 마이그레이션 ─────────────────────────────────────────────
echo ""
echo "▶ Keycloak 시크릿 → secret/secuardian/keycloak"
KC_ADMIN_PASS=$(_read_env KEYCLOAK_ADMIN_PASSWORD)
KC_CLIENT_SECRET=$(_read_env KEYCLOAK_CLIENT_SECRET)

if [ -z "${KC_ADMIN_PASS}" ] && [ -z "${KC_CLIENT_SECRET}" ]; then
    echo "  ℹ KEYCLOAK_ADMIN_PASSWORD / KEYCLOAK_CLIENT_SECRET 모두 비어있음 — 건너뜀"
else
    BODY="{\"data\":{\"admin_password\":$(_json_str "${KC_ADMIN_PASS}"),\"client_secret\":$(_json_str "${KC_CLIENT_SECRET}")}}"
    _vault_put "secret/data/secuardian/keycloak" "${BODY}"
    echo "  ✓ admin_password=$([ -n "${KC_ADMIN_PASS}" ] && echo "설정됨" || echo "빈값"), client_secret=$([ -n "${KC_CLIENT_SECRET}" ] && echo "설정됨" || echo "빈값")"
fi

# ── Logto 시크릿 마이그레이션 ────────────────────────────────────────────────
echo ""
echo "▶ Logto 시크릿 → secret/secuardian/logto"
LOGTO_SECRET=$(_read_env LOGTO_APP_SECRET)

if [ -z "${LOGTO_SECRET}" ]; then
    echo "  ℹ LOGTO_APP_SECRET 비어있음 — 건너뜀"
else
    BODY="{\"data\":{\"app_secret\":$(_json_str "${LOGTO_SECRET}")}}"
    _vault_put "secret/data/secuardian/logto" "${BODY}"
    echo "  ✓ app_secret=설정됨"
fi

# ── 앱 시크릿 마이그레이션 (JWT) ────────────────────────────────────────────
echo ""
echo "▶ 앱 시크릿 → secret/secuardian/app"
JWT_KEY=$(_read_env JWT_SECRET_KEY)

if [ -z "${JWT_KEY}" ]; then
    echo "  ℹ JWT_SECRET_KEY 비어있음 — 건너뜀"
else
    BODY="{\"data\":{\"jwt_secret\":$(_json_str "${JWT_KEY}")}}"
    _vault_put "secret/data/secuardian/app" "${BODY}"
    echo "  ✓ jwt_secret=설정됨"
fi

# ── 검증: Vault에서 재조회 ───────────────────────────────────────────────────
echo ""
echo "▶ 검증: Vault KV 재조회"
for path in keycloak logto app; do
    RESP=$(curl -sf "${VAULT_ADDR}/v1/secret/data/secuardian/${path}" -H "X-Vault-Token: ${VAULT_TOKEN}" 2>/dev/null || echo "")
    if [ -n "${RESP}" ]; then
        KEYS=$(echo "${RESP}" | python3 -c "import sys,json; print(', '.join(json.load(sys.stdin)['data']['data'].keys()))" 2>/dev/null || echo "?")
        echo "  ✓ secret/secuardian/${path}: [${KEYS}]"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 마이그레이션 완료 — 앱 재시작 시 Vault에서 시크릿 자동 로드"
echo "  이제 .env.local 의 민감 값은 Vault 폴백으로 비워도 됨"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
