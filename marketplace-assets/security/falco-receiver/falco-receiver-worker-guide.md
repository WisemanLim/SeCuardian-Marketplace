# Falco 런타임 이벤트 수신기 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(Falco + Falcosidekick)가 이벤트를 push 해야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [Falco](https://falco.org/) + [Falcosidekick](https://github.com/falcosecurity/falcosidekick) (Apache-2.0)
- **역할**: eBPF/커널 모듈 기반 컨테이너·호스트 런타임 이상 행위 탐지. Falcosidekick 이 이벤트를 HTTP webhook 으로 SeCuardian 에 전달합니다.
- **연결 방식**: Falcosidekick → `POST http://<SeCuardian>:8200/api/addon/falco-receiver/events` (JWT 없음, `FALCO_WEBHOOK_ENABLED=true` 로 게이트)
- **포트**: Falcosidekick API `2801`

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Kubernetes 클러스터 + `kubectl` + `helm` | Helm 설치 경로 (SeCuardian 기본) |
| 또는 Docker 호스트 | 독립 설치 경로 |
| 네트워크 | Falcosidekick → SeCuardian 8200 도달 가능 |

## 3. 설치

### 3-1. Kubernetes (SeCuardian 저장소 Makefile 기준)

```bash
make falco-install     # bash deploy/scripts/falco_install.sh — helm install falco -n falco (falcosidekick 포함)
make falco-status      # kubectl get pods -n falco
make falco-logs
make falco-uninstall   # 주의: 런타임 탐지 중단
```

`falco_install.sh` 의 Falcosidekick webhook 주소를 **Addon 경로로 변경**합니다:

```bash
helm upgrade --install falco falcosecurity/falco -n falco --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.config.webhook.address=http://<SECUARDIAN_HOST>:8200/api/addon/falco-receiver/events \
  --set falcosidekick.config.webhook.minimumpriority=warning
```

### 3-2. Docker 독립 설치

```bash
docker run -d --name falcosidekick -p 2801:2801 \
  -e WEBHOOK_ADDRESS=http://host.docker.internal:8200/api/addon/falco-receiver/events \
  -e WEBHOOK_MINIMUMPRIORITY=warning falcosecurity/falcosidekick:latest
docker run -d --name falco --privileged -v /var/run/docker.sock:/host/var/run/docker.sock \
  -v /proc:/host/proc:ro -v /etc:/host/etc:ro \
  falcosecurity/falco:latest falco -o json_output=true \
  -o http_output.enabled=true -o http_output.url=http://host.docker.internal:2801/
```

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
FALCO_WEBHOOK_ENABLED=true                 # 필수 — false 면 POST /events 가 403
FALCO_SIDEKICK_URL=http://localhost:2801   # 선택 (표시용)
FALCO_EVENTS_MAX=1000                      # 선택 — 인메모리 보관 최대 건수
```

## 5. 동작 확인

```bash
# 수신 테스트 (JWT 불필요)
curl -s -X POST http://localhost:8200/api/addon/falco-receiver/events -H "Content-Type: application/json" \
  -d '{"output":"test","priority":"Warning","rule":"Test Rule","hostname":"local"}'
# 조회
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8200/api/addon/falco-receiver/events?limit=10&priority=warning"
```

| 증상 | 조치 |
|------|------|
| 403 `Falco webhook 비활성화됨` | `FALCO_WEBHOOK_ENABLED=true` 설정 |
| 이벤트 미수신 | Falcosidekick `webhook.address` 가 Addon 경로인지, 8200 방화벽 확인 |
| 재시작 후 이벤트 소실 | 인메모리 저장소 — 장기 보존은 Wazuh/OTel 등으로 이중 전달 |
