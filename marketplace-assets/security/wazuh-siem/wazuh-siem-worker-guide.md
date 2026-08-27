# Wazuh SIEM 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(Wazuh Manager/Indexer/Dashboard)가 기동되어 있어야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [Wazuh](https://wazuh.com/) 4.9+ (GPL-2.0 — API 연동만, 코드 결합 없음) + OpenSearch (Apache-2.0)
- **역할**: 호스트 에이전트 로그 수집·룰 기반 탐지·FIM·취약점 탐지 SIEM. 본 에이전트는 Manager REST API 조회와 webhook 알림 수신을 담당합니다.
- **연결 방식**: `WAZUH_API_URL` (HTTPS self-signed, Basic Auth `WAZUH_API_USER`/`WAZUH_API_PASSWORD`), Wazuh `<integration>` → `POST /api/addon/wazuh-siem/alerts`
- **포트**: API `55000`, Indexer `9200`, Dashboard `5601`, 에이전트 `1514/udp`, 등록 `1515`

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Docker Engine / Compose | 24.0+ / v2.20+ |
| 메모리 | 최소 4GB (OpenSearch JVM 2GB) |
| 커널 | `sysctl -w vm.max_map_count=262144` |
| 환경 파일 | `deploy/docker/.env.wazuh` (`wazuh.env.example` 복사, 비밀번호 3종 변경 필수) |

## 3. 설치 (SeCuardian 저장소 Makefile 기준)

```bash
cp deploy/docker/wazuh.env.example deploy/docker/.env.wazuh   # WAZUH_API_PASSWORD 등 변경
sudo sysctl -w vm.max_map_count=262144
make wazuh-certs     # TLS 인증서 생성 (최초 1회)
make wazuh-up        # Manager + Indexer + Dashboard (첫 기동 5~10분)
make wazuh-status    # curl -sk -u wazuh:<pw> https://localhost:55000/
make wazuh-logs / make wazuh-down
# 대상 서버 Wazuh Agent 배포 (Ansible)
make wazuh-agent-check
make wazuh-agent-deploy MANAGER_IP=<manager ip> [GROUP=linux-servers]
```

### webhook 알림 설정 (Addon 경로로 변경)

`deploy/config/wazuh/ossec.conf` (또는 컨테이너 `/var/ossec/etc/ossec.conf`) 에 추가 후 Manager 재시작:

```xml
<integration>
  <name>custom-secuardian</name>
  <hook_url>http://host.docker.internal:8200/api/addon/wazuh-siem/alerts</hook_url>
  <level>7</level>
  <alert_format>json</alert_format>
</integration>
```

`custom-secuardian` 스크립트는 `/var/ossec/integrations/` 에 배치합니다 (Wazuh 공식 `custom-integration` 예제를 hook_url 로 POST 하도록 사용).

### 독립 설치 (저장소 없이)

```bash
git clone https://github.com/wazuh/wazuh-docker.git -b v4.9.2 && cd wazuh-docker/single-node
docker compose -f generate-indexer-certs.yml run --rm generator
docker compose up -d
```

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
WAZUH_API_URL=https://localhost:55000    # 필수
WAZUH_API_PASSWORD=<API 비밀번호>         # 필수 — 미설정 시 /agents 503, /status UNCONFIGURED
WAZUH_API_USER=wazuh                     # 선택 (기본값)
WAZUH_INDEXER_URL=https://localhost:9200 # 선택 (표시용)
WAZUH_DASHBOARD_URL=https://localhost:5601
WAZUH_WEBHOOK_ENABLED=true               # POST /alerts 수신 허용 (기본 false → 403)
WAZUH_ALERTS_MAX=1000                    # 선택
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/wazuh-siem/status
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8200/api/addon/wazuh-siem/agents?status=active"
curl -s -X POST http://localhost:8200/api/addon/wazuh-siem/alerts -H "Content-Type: application/json" \
  -d '{"rule":{"level":10,"description":"test"},"agent":{"name":"web-01"}}'
```

| 증상 | 조치 |
|------|------|
| `status: DOWN` | 첫 기동 5~10분 대기, 포트 55000 확인 |
| 401 (API) | `WAZUH_API_USER`/`WAZUH_API_PASSWORD` 가 `.env.wazuh` 와 일치하는지 확인 |
| 403 webhook | `WAZUH_WEBHOOK_ENABLED=true` |
| Indexer 기동 실패 | `vm.max_map_count`, 인증서 디렉터리 권한(`chmod 755`) 확인 |
