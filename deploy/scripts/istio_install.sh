#!/usr/bin/env bash
# Istio 서비스 메쉬 설치 스크립트 — E10 T10-1
# License: Apache-2.0
# 전제: E09 Cilium CNI 동작 중
# Usage: bash deploy/scripts/istio_install.sh [--dry-run]
set -euo pipefail

ISTIO_VERSION="1.23.2"
DRY_RUN="${1:-}"

echo "=== Istio ${ISTIO_VERSION} 설치 (Cilium 위) ==="

command -v kubectl   >/dev/null 2>&1 || { echo "❌ kubectl 필요"; exit 1; }
command -v istioctl  >/dev/null 2>&1 || {
  echo "istioctl 없음 — 다운로드 중..."
  curl -L https://istio.io/downloadIstio | ISTIO_VERSION="${ISTIO_VERSION}" sh -
  export PATH="$PWD/istio-${ISTIO_VERSION}/bin:$PATH"
}

# Cilium 동작 확인
kubectl get ds -n kube-system cilium >/dev/null 2>&1 || {
  echo "❌ Cilium DaemonSet 없음 — E09 먼저 완료하세요"
  exit 1
}

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "[dry-run] istioctl install — 실제 실행 건너뜀"
  istioctl manifest generate --set profile=minimal | head -30
  exit 0
fi

# Minimal profile (Cilium이 L3/L4 담당, Istio는 L7/mTLS 담당)
istioctl install \
  --set profile=minimal \
  --set meshConfig.accessLogFile=/dev/stdout \
  --set meshConfig.accessLogEncoding=JSON \
  -y

# 네임스페이스 사이드카 자동 주입 활성화
kubectl label namespace secuardian istio-injection=enabled --overwrite
kubectl label namespace internal   istio-injection=enabled --overwrite

# mTLS STRICT 정책 적용
kubectl apply -f deploy/k8s/istio/peer-authentication.yaml
kubectl apply -f deploy/k8s/istio/authorization-policy.yaml

echo "✅ Istio 설치 완료"
echo ""
echo "Kiali 대시보드: istioctl dashboard kiali"
echo "Jaeger 트레이싱: istioctl dashboard jaeger"
