# Cilium Network Policy — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **Kubernetes 전용**: Cilium은 Docker Compose 기반 설치를 지원하지 않습니다.
> Kubernetes 클러스터(CNI 레이어)에 설치해야 합니다.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [Cilium](https://github.com/cilium/cilium) (eBPF 기반 Kubernetes CNI, Apache-2.0) + [Hubble](https://github.com/cilium/hubble) (Cilium 네트워크 관찰성)
- **역할**: eBPF 기반 마이크로세그멘테이션 및 네트워크 정책 시행. Hubble은 파드 간 네트워크 플로우를 실시간 관찰하고 위반 이벤트를 기록
- **구성 요소**:
  - **Cilium Agent**: 각 노드에서 실행되는 DaemonSet (REST API: 기본 `http://localhost:9090`)
  - **Hubble Relay**: 클러스터 전역 플로우 집계 (기본 `http://localhost:4245`)
  - **Hubble UI** (선택): 시각화 대시보드
- **에이전트 연결 방식**: SeCuardian이 `CILIUM_AGENT_URL`로 Cilium Agent REST API에서 네트워크 정책 목록 조회, `CILIUM_HUBBLE_URL`로 Hubble Relay에서 플로우 이벤트 수신

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Kubernetes | v1.27 이상 |
| Helm | v3.12 이상 |
| `kubectl` | 클러스터에 연결된 상태 |
| 기존 CNI 제거 | 다른 CNI(flannel, calico 등)와 충돌 — 사전 제거 필요 |
| Linux 커널 | 4.19 이상 (eBPF 지원), 권장 5.10 이상 |

---

## 3. 설치 (Install)

### 3-1. Cilium CLI 설치

```bash
# macOS
brew install cilium-cli

# Linux
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin
```

### 3-2. Cilium CNI 설치

```bash
# Makefile 타겟 사용 (권장)
make cilium-install

# dry-run 먼저 확인
make cilium-install-dry

# 또는 cilium CLI 직접 실행
cilium install --version 1.16.0
```

> `deploy/scripts/cilium_install.sh` 스크립트를 참조합니다.

### 3-3. Hubble 활성화

```bash
# Hubble Relay 및 UI 활성화
cilium hubble enable --ui

# 또는 Helm 업그레이드로 활성화
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true
```

### 3-4. 네트워크 정책 적용

```bash
# Zone NetworkPolicy 적용 (Makefile 타겟)
make cilium-netpol-apply

# dry-run 확인
make cilium-netpol-dry

# 또는 kubectl 직접 실행
kubectl apply -f deploy/k8s/cilium/network-policies/
kubectl apply --dry-run=client -f deploy/k8s/cilium/network-policies/
```

### 3-5. Hubble UI 포트 포워드

```bash
# Hubble UI 로컬 접근 (포트 포워드)
make cilium-hubble-ui
# 브라우저에서: http://localhost:12000 (또는 make 타겟이 설정한 포트)
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/cilium-netpol/cilium-netpol-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `CILIUM_AGENT_URL` | `http://localhost:9090` | Cilium Agent REST API base URL |
| `CILIUM_HUBBLE_URL` | `http://localhost:4245` | Hubble Relay base URL |
| `CILIUM_WEBHOOK_ENABLED` | `false` | Hubble 플로우 수신 웹훅 엔드포인트 활성화 |
| `CILIUM_HUBBLE_MAX` | `500` | 메모리에 유지할 최대 Hubble 플로우 수 |

> Cilium Agent API는 기본적으로 노드 내 localhost에서만 접근 가능합니다.
> SeCuardian이 클러스터 외부에서 실행 중이라면 `kubectl port-forward`로 접근하거나
> Cilium의 API 노출 설정을 조정하세요.

```bash
# Cilium Agent API 포트 포워드 (클러스터 외부 접근 시)
kubectl port-forward -n kube-system daemonset/cilium 9090:9090

# Hubble Relay 포트 포워드
kubectl port-forward -n kube-system service/hubble-relay 4245:80
```

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용 (Cilium/Hubble 상태 + SeCuardian API)
make cilium-status

# Cilium 상태 직접 확인
cilium status

# 네트워크 정책 목록
kubectl get ciliumnetworkpolicies -A

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/cilium/status | python3 -m json.tool

# 네트워크 정책 목록 (SeCuardian 통해)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8200/api/cilium/network-policies | python3 -m json.tool

# Hubble 플로우 통계
curl -H "Authorization: Bearer <token>" \
  http://localhost:8200/api/cilium/stats | python3 -m json.tool
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# Cilium 상태 모니터링 (지속)
cilium monitor

# Hubble 플로우 실시간 관찰 (Hubble CLI)
hubble observe --follow

# Hubble UI 포트 포워드
make cilium-hubble-ui

# Cilium 제거 (주의: CNI 제거는 클러스터 네트워킹 중단)
cilium uninstall

# 네트워크 정책만 제거
kubectl delete -f deploy/k8s/cilium/network-policies/
```

---

## English Summary

**Worker**: [Cilium](https://github.com/cilium/cilium) (eBPF Kubernetes CNI, Apache-2.0) + [Hubble](https://github.com/cilium/hubble) (network observability) — **Kubernetes only, no Docker Compose**.

- **Install Cilium**: `make cilium-install` (uses `deploy/scripts/cilium_install.sh`) or `cilium install --version 1.16.0`
- **Enable Hubble**: `cilium hubble enable --ui`
- **Apply policies**: `make cilium-netpol-apply` or `kubectl apply -f deploy/k8s/cilium/network-policies/`
- **Port forwarding** (if SeCuardian is outside the cluster): `kubectl port-forward -n kube-system daemonset/cilium 9090:9090` and `kubectl port-forward -n kube-system service/hubble-relay 4245:80`
- **Key env vars**: `CILIUM_AGENT_URL=http://localhost:9090`, `CILIUM_HUBBLE_URL=http://localhost:4245`, `CILIUM_WEBHOOK_ENABLED=false`, `CILIUM_HUBBLE_MAX=500`
- **Verify**: `make cilium-status`, `cilium status`, `kubectl get ciliumnetworkpolicies -A`
- **Prerequisites**: Kubernetes 1.27+, Linux kernel 4.19+ (5.10+ recommended), remove conflicting CNIs first
