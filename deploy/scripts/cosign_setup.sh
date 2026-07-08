#!/usr/bin/env bash
# Cosign (Sigstore) 이미지 서명 키 생성 — E03 T03-2
# License: Apache-2.0 (Sigstore/Cosign)
# ⚠️  cosign 설치 필요: brew install cosign

set -euo pipefail

COSIGN_KEY_DIR="${COSIGN_KEY_DIR:-deploy/secrets/cosign}"

echo "=== Cosign 키 쌍 생성 ==="
echo "⚠️  License: Apache-2.0 (Sigstore) — 상업적 사용 허용"

# cosign 설치 확인
if ! command -v cosign &>/dev/null; then
    echo ""
    echo "❌ cosign 미설치 — 설치 후 재실행"
    echo "   macOS:  brew install cosign"
    echo "   Linux:  sudo apt install cosign"
    echo "   또는:   https://github.com/sigstore/cosign/releases"
    exit 0  # graceful — cosign 없어도 다른 단계 진행 가능
fi

COSIGN_VER=$(cosign version 2>&1 | grep -E "^GitVersion|^Version" | head -1 || echo "unknown")
echo "cosign: ${COSIGN_VER}"

# 이미 키 있으면 skip (멱등)
if [[ -f "${COSIGN_KEY_DIR}/cosign.key" ]]; then
    echo ""
    echo "✅ 키 이미 존재: ${COSIGN_KEY_DIR}/cosign.{key,pub}"
    echo "   재생성: rm ${COSIGN_KEY_DIR}/cosign.key ${COSIGN_KEY_DIR}/cosign.pub && make harbor-cosign"
    exit 0
fi

mkdir -p "${COSIGN_KEY_DIR}"

echo ""
echo "키 쌍 생성 중 (비밀번호 입력 필요)..."
cosign generate-key-pair --output-key-prefix "${COSIGN_KEY_DIR}/cosign"

echo ""
echo "✅ Cosign 키 생성 완료:"
echo "   Private: ${COSIGN_KEY_DIR}/cosign.key  🔴 git 커밋 금지 (.gitignore 등록됨)"
echo "   Public:  ${COSIGN_KEY_DIR}/cosign.pub  ✅ 서명 검증 + .env.local에 경로 추가"
echo ""
echo "GitHub Actions Secrets 등록 (Settings → Secrets and variables → Actions):"
echo ""
echo "  이름: COSIGN_PRIVATE_KEY"
echo "  값:"
base64 "${COSIGN_KEY_DIR}/cosign.key"
echo ""
echo "  이름: COSIGN_PASSWORD"
echo "  값: (생성 시 입력한 비밀번호)"
echo ""
echo ".env.local 에 추가:"
echo "  COSIGN_PUB_KEY=${COSIGN_KEY_DIR}/cosign.pub"
