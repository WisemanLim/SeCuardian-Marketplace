#!/usr/bin/env bash
# Falco K8s Helm 설치 — E03 T03-3
# License: Apache-2.0
# 전제: kubectl + helm 설치, K8s 클러스터 접근 가능
# 사용: make falco-install

set -euo pipefail

FALCO_VERSION="${FALCO_VERSION:-4.8.0}"
FALCO_NAMESPACE="${FALCO_NAMESPACE:-falco}"
HELM_CHART="falcosecurity/falco"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VALUES_FILE="${PROJECT_ROOT}/deploy/k8s/falco/values.yaml"
CUSTOM_RULES="${PROJECT_ROOT}/deploy/k8s/falco/custom-rules.yaml"

echo "=== Falco ${FALCO_VERSION} K8s 설치 ==="
echo "⚠️  License: Apache-2.0 — 상업적 사용 허용"
echo "   Namespace: ${FALCO_NAMESPACE}"
echo "   eBPF 드라이버 사용 (커널 5.8+ 필요)"

# 전제 조건 확인
for cmd in kubectl helm; do
    if ! command -v "${cmd}" &>/dev/null; then
        echo "❌ ${cmd} 필요"
        case "${cmd}" in
            helm)    echo "   설치: https://helm.sh/docs/intro/install/" ;;
            kubectl) echo "   설치: https://kubernetes.io/docs/tasks/tools/" ;;
        esac
        exit 1
    fi
done

# K8s 클러스터 연결 확인
if ! kubectl cluster-info &>/dev/null 2>&1; then
    echo "❌ K8s 클러스터 연결 실패"
    echo "   minikube: minikube start"
    echo "   kind:     kind create cluster"
    exit 1
fi
echo "✅ K8s 클러스터: $(kubectl config current-context)"

# Step 1: falcosecurity Helm repo
echo ""
echo "1. falcosecurity Helm repo 추가..."
helm repo add falcosecurity https://falcosecurity.github.io/charts 2>/dev/null \
    && echo "   repo 추가됨" \
    || echo "   이미 존재"
helm repo update

# Step 2: Namespace
echo ""
echo "2. Namespace '${FALCO_NAMESPACE}'..."
kubectl create namespace "${FALCO_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
echo "   ✅ namespace 준비됨"

# Step 3: Custom rules ConfigMap
echo ""
echo "3. Custom rules ConfigMap 적용..."
kubectl create configmap falco-custom-rules \
    --from-file=custom-rules.yaml="${CUSTOM_RULES}" \
    -n "${FALCO_NAMESPACE}" \
    --dry-run=client -o yaml | kubectl apply -f -
echo "   ✅ ConfigMap falco-custom-rules 적용됨"

# Step 4: Falco Helm install
echo ""
echo "4. Falco Helm 설치/업그레이드..."
helm upgrade --install falco "${HELM_CHART}" \
    --namespace "${FALCO_NAMESPACE}" \
    --version "${FALCO_VERSION}" \
    --values "${VALUES_FILE}" \
    --wait \
    --timeout 300s

echo ""
echo "✅ Falco 설치 완료!"
echo ""
echo "   파드 상태:  kubectl get pods -n ${FALCO_NAMESPACE}"
echo "   로그:       kubectl logs -n ${FALCO_NAMESPACE} -l app.kubernetes.io/name=falco -f"
echo "   이벤트 확인: kubectl logs -n ${FALCO_NAMESPACE} -l app.kubernetes.io/name=falcosidekick -f"
echo ""
echo "Falcosidekick → SeCuardian:"
echo "   웹훅: http://secuardian.default.svc.cluster.local:8000/api/falco/events"
echo "   최소 우선순위: CRITICAL"
echo ""
echo "다음: T03-4 Falco 이벤트 수신 라우터 → make falco-receiver"
