#!/usr/bin/env bash
# Harbor 프로젝트 + Robot Account 설정 — E03 T03-1
# 전제: Harbor 기동 중 (make harbor-up)
# License: Apache-2.0

set -euo pipefail

HARBOR_URL="${HARBOR_URL:-http://localhost:8083}"
HARBOR_ADMIN="${HARBOR_ADMIN_USER:-admin}"
HARBOR_ADMIN_PASSWORD="${HARBOR_ADMIN_PASSWORD:-Harbor@Secuardian2026!}"
HARBOR_PROJECT="${HARBOR_PROJECT:-secuardian}"
ROBOT_NAME="${ROBOT_NAME:-secuardian-ci}"

echo "=== Harbor 프로젝트 + RBAC 설정 ==="
echo "   Harbor: ${HARBOR_URL}"
echo "   프로젝트: ${HARBOR_PROJECT}"

# Step 1: Health 확인 (최대 5회, 10초 간격)
echo ""
echo "1. Harbor Health 확인..."
STATUS="down"
for i in $(seq 1 5); do
    STATUS=$(curl -sf "${HARBOR_URL}/api/v2.0/health" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null \
        || echo "down")
    if [[ "${STATUS}" == "healthy" ]]; then
        echo "   ✅ Harbor healthy"
        break
    fi
    echo "   대기 중... (${i}/5) — 현재: ${STATUS}"
    sleep 10
done

if [[ "${STATUS}" != "healthy" ]]; then
    echo "❌ Harbor 응답 없음"
    echo "   실행: make harbor-up"
    echo "   설치 필요: make harbor-install"
    exit 1
fi

# Step 2: 프로젝트 생성
echo ""
echo "2. '${HARBOR_PROJECT}' 프로젝트 생성..."
HTTP_CODE=$(curl -s -o /tmp/harbor_proj_resp.json -w "%{http_code}" \
    -X POST "${HARBOR_URL}/api/v2.0/projects" \
    -u "${HARBOR_ADMIN}:${HARBOR_ADMIN_PASSWORD}" \
    -H "Content-Type: application/json" \
    -d "{
        \"project_name\": \"${HARBOR_PROJECT}\",
        \"public\": false,
        \"metadata\": {
            \"enable_content_trust\": \"false\",
            \"prevent_vul\": \"false\",
            \"auto_scan\": \"true\"
        }
    }")

case "${HTTP_CODE}" in
    201) echo "   ✅ 프로젝트 생성됨" ;;
    409) echo "   ℹ️  프로젝트 이미 존재 — 계속 진행" ;;
    *)
        echo "   ❌ 프로젝트 생성 실패: HTTP ${HTTP_CODE}"
        cat /tmp/harbor_proj_resp.json 2>/dev/null || true
        exit 1
        ;;
esac

# Step 3: Robot Account 생성
echo ""
echo "3. Robot Account '${ROBOT_NAME}' 생성..."
ROBOT_RESP=$(curl -sf \
    -X POST "${HARBOR_URL}/api/v2.0/robots" \
    -u "${HARBOR_ADMIN}:${HARBOR_ADMIN_PASSWORD}" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"${ROBOT_NAME}\",
        \"level\": \"project\",
        \"description\": \"SeCuardian CI/CD push/pull — E03 T03-1\",
        \"duration\": 365,
        \"permissions\": [
            {
                \"kind\": \"project\",
                \"namespace\": \"${HARBOR_PROJECT}\",
                \"access\": [
                    {\"resource\": \"repository\", \"action\": \"push\"},
                    {\"resource\": \"repository\", \"action\": \"pull\"},
                    {\"resource\": \"artifact\",   \"action\": \"read\"},
                    {\"resource\": \"artifact\",   \"action\": \"delete\"}
                ]
            }
        ]
    }" 2>/dev/null || echo "{}")

ROBOT_FULL_NAME=$(echo "${ROBOT_RESP}" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('name',''))" 2>/dev/null || echo "")
ROBOT_SECRET=$(echo "${ROBOT_RESP}" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('secret',''))" 2>/dev/null || echo "")

if [[ -n "${ROBOT_SECRET}" ]]; then
    echo "   ✅ Robot Account 생성: ${ROBOT_FULL_NAME}"
    echo ""
    echo "======================================"
    echo " Robot Account 자격증명 (한 번만 표시)"
    echo "======================================"
    echo "HARBOR_ROBOT_NAME=${ROBOT_FULL_NAME}"
    echo "HARBOR_ROBOT_SECRET=${ROBOT_SECRET}"
    echo ""
    echo ".env.local 에 추가:"
    echo "  HARBOR_URL=${HARBOR_URL}"
    echo "  HARBOR_ROBOT_NAME=${ROBOT_FULL_NAME}"
    echo "  HARBOR_ROBOT_SECRET=${ROBOT_SECRET}"
else
    echo "   ⚠️  Robot Account 이미 존재하거나 생성 실패"
    echo "   Harbor UI → Projects → ${HARBOR_PROJECT} → Robot Accounts 에서 확인"
fi

echo ""
echo "✅ Harbor 설정 완료!"
echo "   UI: ${HARBOR_URL}"
echo "   Registry: localhost:8083/${HARBOR_PROJECT}/<image>:<tag>"
echo ""
echo "이미지 푸시 예시:"
echo "  docker login localhost:8083 -u '\${HARBOR_ROBOT_NAME}' -p '\${HARBOR_ROBOT_SECRET}'"
echo "  docker tag myimage:latest localhost:8083/${HARBOR_PROJECT}/myimage:latest"
echo "  docker push localhost:8083/${HARBOR_PROJECT}/myimage:latest"
