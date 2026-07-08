#!/usr/bin/env bash
# Cilium CNI 설치 스크립트 — E09 T09-1
# License: Apache-2.0
# Usage: bash deploy/scripts/cilium_install.sh [--dry-run]
set -euo pipefail

CILIUM_VERSION="1.16.3"
NAMESPACE="kube-system"
DRY_RUN="${1:-}"

echo "=== Cilium ${CILIUM_VERSION} 설치 ==="

# kubectl + helm 확인
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl 필요"; exit 1; }
command -v helm    >/dev/null 2>&1 || { echo "❌ helm 필요"; exit 1; }

K8S_API=$(kubectl get endpoints kubernetes -n default -o jsonpath='{.subsets[0].addresses[0].ip}')
echo "K8s API Server: ${K8S_API}"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "[dry-run] helm install cilium — 실제 실행 건너뜀"
  exit 0
fi

# Cilium Helm 저장소 추가
helm repo add cilium https://helm.cilium.io/
helm repo update

# 기존 CNI 대기 경고
echo "⚠️  기존 CNI를 Cilium으로 교체합니다. 노드 롤링 재시작이 발생합니다."
echo "   운영 환경은 유지보수 창 확보 후 실행하세요."
read -r -p "계속? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "취소"; exit 0; }

helm upgrade --install cilium cilium/cilium \
  --version "${CILIUM_VERSION}" \
  --namespace "${NAMESPACE}" \
  --set k8sServiceHost="${K8S_API}" \
  --set k8sServicePort="6443" \
  -f deploy/k8s/cilium/values.yaml \
  --wait --timeout 5m

echo "✅ Cilium 설치 완료"
echo ""
echo "NetworkPolicy 적용:"
kubectl apply -f deploy/k8s/cilium/network-policies/ --dry-run=client
echo "실제 적용하려면: kubectl apply -f deploy/k8s/cilium/network-policies/"
echo ""
echo "Hubble UI: kubectl port-forward -n kube-system svc/hubble-ui 12000:80"
