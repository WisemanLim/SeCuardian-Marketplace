#!/usr/bin/env bash
# Source: SeCuardian | License: BUSL-1.1 (Vault) | Usage: internal only
# E02 T02-2: Vault AppRole + PKI 설정 스크립트
# 전제 조건: vault_init.sh 실행 완료 (KV v2 초기화)
# 사용법: bash deploy/scripts/vault_setup.sh
#         또는: make vault-setup

set -euo pipefail

VAULT_PORT="${VAULT_PORT:-8201}"
VAULT_ADDR="${VAULT_ADDR:-http://localhost:${VAULT_PORT}}"
VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN:-dev-root-token-secuardian}"

export VAULT_ADDR VAULT_TOKEN

_vault_api() {
    local method="$1" path="$2"
    local data="${3:-}"
    local args=(-sf -X "$method" "${VAULT_ADDR}${path}" -H "X-Vault-Token: ${VAULT_TOKEN}" -H "Content-Type: application/json")
    [ -n "$data" ] && args+=(-d "$data")
    curl "${args[@]}" || true
}

_vault_get() {
    curl -sf -X GET "${VAULT_ADDR}${1}" -H "X-Vault-Token: ${VAULT_TOKEN}" || true
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vault AppRole + PKI 설정 — ${VAULT_ADDR}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. SeCuardian 정책 생성 ─────────────────────────────────────────────────
echo ""
echo "▶ 1. SeCuardian ACL 정책 생성"
_vault_api PUT /v1/sys/policies/acl/secuardian-policy \
    '{"policy":"path \"secret/data/secuardian/*\" { capabilities = [\"read\", \"list\"] }\npath \"auth/approle/login\" { capabilities = [\"create\", \"read\"] }"}'
echo "  ✓ secuardian-policy 등록"

# ── 2. AppRole 인증 활성화 ──────────────────────────────────────────────────
echo ""
echo "▶ 2. AppRole 인증 엔진 활성화"
MOUNTS=$(_vault_get /v1/sys/auth)
if echo "${MOUNTS}" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'approle/' in d else 1)" 2>/dev/null; then
    echo "  ℹ AppRole 이미 활성화됨"
else
    _vault_api POST /v1/sys/auth/approle '{"type":"approle"}' > /dev/null
    echo "  ✓ AppRole 활성화"
fi

# ── 3. SeCuardian AppRole 역할 생성 ─────────────────────────────────────────
echo ""
echo "▶ 3. secuardian AppRole 역할 생성"
_vault_api POST /v1/auth/approle/role/secuardian \
    '{"token_ttl":"1h","token_max_ttl":"4h","secret_id_ttl":"24h","token_policies":["secuardian-policy"]}' > /dev/null
echo "  ✓ role: secuardian (TTL=1h, MaxTTL=4h, SecretID TTL=24h)"

# ── 4. Role ID 조회 ─────────────────────────────────────────────────────────
echo ""
echo "▶ 4. Role ID 조회"
ROLE_RESP=$(_vault_get /v1/auth/approle/role/secuardian/role-id)
ROLE_ID=$(echo "${ROLE_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['role_id'])" 2>/dev/null || echo "ERROR")
if [ "${ROLE_ID}" = "ERROR" ]; then
    echo "  ✗ Role ID 조회 실패 — AppRole 설정 확인"
    exit 1
fi
echo "  ✓ VAULT_ROLE_ID=${ROLE_ID}"

# ── 5. Secret ID 발급 ───────────────────────────────────────────────────────
echo ""
echo "▶ 5. Secret ID 발급"
SECRET_RESP=$(_vault_api POST /v1/auth/approle/role/secuardian/secret-id "")
SECRET_ID=$(echo "${SECRET_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['secret_id'])" 2>/dev/null || echo "ERROR")
if [ "${SECRET_ID}" = "ERROR" ]; then
    echo "  ✗ Secret ID 발급 실패"
    exit 1
fi
echo "  ✓ VAULT_SECRET_ID=******* (아래 출력 참조)"

# ── 6. PKI 시크릿 엔진 활성화 ───────────────────────────────────────────────
echo ""
echo "▶ 6. PKI 시크릿 엔진 활성화"
SECRET_ENGINES=$(_vault_get /v1/sys/mounts)
if echo "${SECRET_ENGINES}" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'pki/' in d else 1)" 2>/dev/null; then
    echo "  ℹ PKI 이미 활성화됨"
else
    _vault_api POST /v1/sys/mounts/pki '{"type":"pki"}' > /dev/null
    echo "  ✓ PKI 활성화"
fi

# ── 7. PKI max-lease-ttl 조정 ───────────────────────────────────────────────
echo ""
echo "▶ 7. PKI max-lease-ttl 설정 (87600h = 10년)"
_vault_api POST /v1/sys/mounts/pki/tune '{"max_lease_ttl":"87600h"}' > /dev/null
echo "  ✓ max-lease-ttl=87600h"

# ── 8. PKI Root CA 생성 ──────────────────────────────────────────────────────
echo ""
echo "▶ 8. PKI Root CA 생성 (SeCuardian Internal CA)"
CA_CHECK=$(_vault_get /v1/pki/ca/pem 2>/dev/null || echo "")
if echo "${CA_CHECK}" | grep -q "BEGIN CERTIFICATE"; then
    echo "  ℹ Root CA 이미 존재"
else
    _vault_api POST /v1/pki/root/generate/internal \
        '{"common_name":"SeCuardian Internal CA","ttl":"87600h"}' | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✓ CA Serial: {d[\"data\"].get(\"serial_number\",\"OK\")}')"
fi

# ── 9. AppRole 로그인 테스트 ────────────────────────────────────────────────
echo ""
echo "▶ 9. AppRole 로그인 테스트"
LOGIN_RESP=$(_vault_api POST /v1/auth/approle/login \
    "{\"role_id\":\"${ROLE_ID}\",\"secret_id\":\"${SECRET_ID}\"}")
TEST_TOKEN=$(echo "${LOGIN_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['auth']['client_token'])" 2>/dev/null || echo "ERROR")
if [ "${TEST_TOKEN}" = "ERROR" ]; then
    echo "  ✗ AppRole 로그인 실패"
    exit 1
fi
echo "  ✓ AppRole 로그인 성공 (클라이언트 토큰 발급)"

# ── 10. 결과 출력 ────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 설정 완료 — 아래 값을 .env.local 에 추가:"
echo ""
echo "  VAULT_ROLE_ID=${ROLE_ID}"
echo "  VAULT_SECRET_ID=${SECRET_ID}"
echo ""
echo "  ⚠ Secret ID 24시간 후 만료 — 필요 시 재발급:"
echo "    bash deploy/scripts/vault_setup.sh (또는 make vault-setup)"
echo "  ⚠ Root Token 최소 사용 — 이 AppRole로 앱 인증 교체 완료 시 revoke 권장"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
