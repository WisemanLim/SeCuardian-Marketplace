# CrowdSec 위협 탐지 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(CrowdSec Agent + LAPI)가 기동되어 있어야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [CrowdSec](https://www.crowdsec.net/) (MIT) — Agent(로그 파서/시나리오) + Local API(LAPI)
- **역할**: 로그 기반 공격 행위 탐지, 커뮤니티 CTI 기반 IP 차단 결정(decisions), Bouncer 연동
- **연결 방식**: `CROWDSEC_LAPI_URL` 로 LAPI 조회 (`/v1/decisions` 는 `X-Api-Key: CROWDSEC_BOUNCER_KEY`), CrowdSec HTTP notification plugin → `POST /api/addon/crowdsec-monitor/alerts`
- **포트**: LAPI `8082` (호스트) → 컨테이너 `8080`

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Docker Engine / Compose | 24.0+ / v2.20+ |
| 환경 파일 | `deploy/docker/.env.crowdsec` (`crowdsec.env.example` 복사) |
| 로그 | 감시 대상 로그 디렉터리 (`logs/`) 읽기 권한 (`GID`) |

## 3. 설치 (SeCuardian 저장소 Makefile 기준)

```bash
cp deploy/docker/crowdsec.env.example deploy/docker/.env.crowdsec
make crowdsec-up          # docker compose -f deploy/docker/docker-compose.crowdsec.yml --env-file deploy/docker/.env.crowdsec up -d
make crowdsec-status      # LAPI /health
make crowdsec-setup       # bash deploy/scripts/crowdsec_setup.sh — Bouncer API Key 발급 → .env.crowdsec 갱신
make crowdsec-allowlist   # 내부 IP 대역 allowlist (FP 방지)
make crowdsec-decisions   # cscli decisions list
make crowdsec-cscli CMD="cscli metrics"
make crowdsec-logs / make crowdsec-down
```

### webhook 알림 설정 (Addon 경로로 변경)

`deploy/config/crowdsec/notifications/http.yaml`:

```yaml
type: http
name: secuardian_webhook
log_level: info
format: |
  {{ range . }}{{ . | toJson }}{{ end }}
url: http://host.docker.internal:8200/api/addon/crowdsec-monitor/alerts
method: POST
headers:
  Content-Type: application/json
```

`deploy/config/crowdsec/profiles.yaml` 의 `notifications: [secuardian_webhook]` 을 확인한 뒤 컨테이너를 재시작합니다.

### 독립 설치 (저장소 없이)

```bash
docker run -d --name crowdsec -p 8082:8080 \
  -v crowdsec-config:/etc/crowdsec -v crowdsec-data:/var/lib/crowdsec/data \
  -v /var/log:/var/log:ro crowdsecurity/crowdsec:latest
docker exec crowdsec cscli bouncers add secuardian-bouncer   # 출력된 키 → CROWDSEC_BOUNCER_KEY
```

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
CROWDSEC_LAPI_URL=http://localhost:8082   # 필수
CROWDSEC_BOUNCER_KEY=<cscli bouncers add 출력> # /decisions 조회에 필요 (미설정 시 503)
CROWDSEC_SIMULATION_MODE=true             # 선택 — 초기 2주 시뮬레이션 권장 (표시용)
CROWDSEC_WEBHOOK_ENABLED=true             # POST /alerts 수신 허용 (기본 false → 403)
CROWDSEC_ALERTS_MAX=1000                  # 선택 — 인메모리 보관 최대 건수
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/crowdsec-monitor/status
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8200/api/addon/crowdsec-monitor/decisions?limit=10"
curl -s -X POST http://localhost:8200/api/addon/crowdsec-monitor/alerts -H "Content-Type: application/json" \
  -d '[{"Scenario":"crowdsecurity/ssh-bf","Source":{"IP":"203.0.113.9"}}]'
```

| 증상 | 조치 |
|------|------|
| 503 `LAPI 연결 실패` | 포트 8082, `docker compose ps` 확인 |
| 503 `CROWDSEC_BOUNCER_KEY 미설정` | `make crowdsec-setup` 또는 `cscli bouncers add` |
| 403 webhook | `CROWDSEC_WEBHOOK_ENABLED=true` |
| decisions 401/403 | 키 재발급, 만료·삭제된 bouncer 확인 (`cscli bouncers list`) |
