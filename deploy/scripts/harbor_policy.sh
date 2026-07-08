#!/usr/bin/env bash
# Harbor Trivy 스캐너 + Critical CVE 정책 설정 — E03 T03-2
# 전제: Harbor 기동 중 (make harbor-up && make harbor-setup)
# License: Apache-2.0

set -euo pipefail

HARBOR_URL="${HARBOR_URL:-http://localhost:8083}"
HARBOR_ADMIN="${HARBOR_ADMIN_USER:-admin}"
HARBOR_ADMIN_PASSWORD="${HARBOR_ADMIN_PASSWORD:-Harbor@Secuardian2026!}"
HARBOR_PROJECT="${HARBOR_PROJECT:-secuardian}"

_auth_header() {
    echo "Authorization: Basic $(echo -n "${HARBOR_ADMIN}:${HARBOR_ADMIN_PASSWORD}" | base64)"
}

echo "=== Harbor Trivy + CVE 정책 설정 ==="
echo "   Harbor: ${HARBOR_URL} | 프로젝트: ${HARBOR_PROJECT}"

# Step 1: Health check
echo ""
echo "1. Harbor Health 확인..."
STATUS=$(curl -sf "${HARBOR_URL}/api/v2.0/health" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null \
    || echo "down")
if [[ "${STATUS}" != "healthy" ]]; then
    echo "❌ Harbor 응답 없음 (현재: ${STATUS})"
    echo "   실행: make harbor-up && make harbor-setup"
    exit 1
fi
echo "   ✅ ${STATUS}"

# Step 2: Trivy 스캐너 UUID 조회
echo ""
echo "2. Trivy 스캐너 확인..."
SCANNERS=$(curl -sf -H "$(_auth_header)" \
    "${HARBOR_URL}/api/v2.0/scanners" 2>/dev/null || echo "[]")

TRIVY_UUID=$(echo "${SCANNERS}" | python3 -c "
import sys, json
scanners = json.load(sys.stdin)
t = next((s for s in scanners if 'trivy' in s.get('name','').lower()), None)
print(t['uuid'] if t else '')
" 2>/dev/null || echo "")

if [[ -z "${TRIVY_UUID}" ]]; then
    echo "   ⚠️  Trivy 미등록 — Harbor UI → Administration → Interrogation Services 확인"
else
    echo "   ✅ Trivy UUID: ${TRIVY_UUID}"
fi

# Step 3: 프로젝트 ID 조회
echo ""
echo "3. 프로젝트 '${HARBOR_PROJECT}' ID 조회..."
PROJ_RESP=$(curl -sf -H "$(_auth_header)" \
    "${HARBOR_URL}/api/v2.0/projects?name=${HARBOR_PROJECT}" 2>/dev/null || echo "[]")

PROJ_ID=$(echo "${PROJ_RESP}" | python3 -c "
import sys, json
projects = json.load(sys.stdin)
p = next((x for x in projects if x['name'] == '${HARBOR_PROJECT}'), None)
print(p['project_id'] if p else '')
" 2>/dev/null || echo "")

if [[ -z "${PROJ_ID}" ]]; then
    echo "   ❌ 프로젝트 미존재 — make harbor-setup 먼저 실행"
    exit 1
fi
echo "   ✅ 프로젝트 ID: ${PROJ_ID}"

# Step 4: Trivy를 프로젝트 기본 스캐너로 설정 (UUID 있는 경우)
if [[ -n "${TRIVY_UUID}" ]]; then
    echo ""
    echo "4. Trivy → 프로젝트 기본 스캐너 설정..."
    CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X PUT "${HARBOR_URL}/api/v2.0/projects/${PROJ_ID}/scanner" \
        -H "$(_auth_header)" \
        -H "Content-Type: application/json" \
        -d "{\"uuid\": \"${TRIVY_UUID}\"}")
    [[ "${CODE}" =~ ^2 ]] && echo "   ✅ Trivy 설정됨" || echo "   ⚠️  HTTP ${CODE} (이미 설정됐을 수 있음)"
fi

# Step 5: CVE 정책 — auto_scan=true, prevent_vul=true, severity=critical
echo ""
echo "5. CVE 정책 설정 (auto_scan=true, prevent_vul=true, severity=critical)..."
CODE=$(curl -s -o /tmp/harbor_policy_resp.json -w "%{http_code}" \
    -X PUT "${HARBOR_URL}/api/v2.0/projects/${PROJ_ID}" \
    -H "$(_auth_header)" \
    -H "Content-Type: application/json" \
    -d '{
        "metadata": {
            "auto_scan": "true",
            "prevent_vul": "true",
            "severity": "critical"
        }
    }')

case "${CODE}" in
    200)
        echo "   ✅ 정책 적용됨"
        ;;
    *)
        echo "   ❌ 실패: HTTP ${CODE}"
        cat /tmp/harbor_policy_resp.json 2>/dev/null || true
        exit 1
        ;;
esac

echo ""
echo "✅ 완료!"
echo "   auto_scan:    push 시 자동 Trivy 스캔"
echo "   prevent_vul:  Critical CVE 발견 시 이미지 배포 차단"
echo "   severity:     critical 이상 차단 (high/medium/low 허용)"
echo ""
echo "다음: Cosign 서명 설정 → make harbor-cosign"
