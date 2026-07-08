#!/usr/bin/env bash
# Source: SeCuardian | License: AGPL-3.0 (TruffleHog) | Note: CI use only
# E02 T02-4: git pre-commit hook 설치 (TruffleHog 로컬 시크릿 스캔)
# 사용법: bash deploy/scripts/setup_hooks.sh
#         또는: make hooks-setup

set -euo pipefail

HOOKS_DIR=".git/hooks"

# ── Git 저장소 확인 ──────────────────────────────────────────────────────────
if [ ! -d "${HOOKS_DIR}" ]; then
    echo "✗ .git/hooks 없음 — git 저장소 루트에서 실행하세요"
    exit 1
fi

# ── TruffleHog 설치 확인 ─────────────────────────────────────────────────────
if ! command -v trufflehog > /dev/null 2>&1; then
    echo "⚠ TruffleHog 미설치 — pre-commit hook은 설치되지 않습니다"
    echo ""
    echo "  설치 방법 (macOS):"
    echo "    brew install trufflehog"
    echo ""
    echo "  설치 방법 (Linux):"
    echo "    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin"
    echo ""
    echo "  설치 후 재실행: bash deploy/scripts/setup_hooks.sh"
    echo ""
    echo "  ⚠ TruffleHog는 AGPL-3.0 — CI 실행 전용, 소스 수정·배포 시 소스 공개 의무"
    exit 0
fi

TRUFFLEHOG_VERSION=$(trufflehog --version 2>&1 | head -1 || echo "unknown")
echo "✓ TruffleHog 발견: ${TRUFFLEHOG_VERSION}"

# ── pre-commit hook 설치 ─────────────────────────────────────────────────────
cat > "${HOOKS_DIR}/pre-commit" << 'HOOK'
#!/usr/bin/env bash
# SeCuardian pre-commit: TruffleHog 시크릿 스캔 (T02-4)
# AGPL-3.0 — CI 실행 전용

set -e

if ! command -v trufflehog > /dev/null 2>&1; then
    echo "[pre-commit] TruffleHog 미설치 — 시크릿 스캔 건너뜀"
    exit 0
fi

echo "[pre-commit] TruffleHog 시크릿 스캔 중..."
if trufflehog git file://. --only-verified --fail --since-commit HEAD 2>/dev/null; then
    echo "[pre-commit] ✓ 시크릿 미발견"
else
    echo "[pre-commit] ✗ 시크릿 발견! 커밋 차단"
    echo "  → Vault에 저장 후 .env.* 에서 제거하세요 (make vault-migrate)"
    exit 1
fi
HOOK

chmod +x "${HOOKS_DIR}/pre-commit"
echo "✓ pre-commit hook 설치: ${HOOKS_DIR}/pre-commit"
echo ""
echo "이제 git commit 시 자동으로 TruffleHog 스캔이 실행됩니다."
echo "건너뛰려면 (권장하지 않음): git commit --no-verify"
