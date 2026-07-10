# teler HTTP IDS — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [teler](https://github.com/kitabisa/teler) v2.0.0-rc.4 (kitabisa, Apache-2.0)
- **역할**: HTTP 로그 기반 실시간 침입 탐지 시스템(IDS). Caddy 액세스 로그를 tail하여 악성 요청, CVE 스캔, XSS, 무차별 대입 등을 탐지하고 웹훅으로 알림 발송
- **동작 방식**: 컨테이너는 공개 포트가 없습니다. `logs/caddy.log`를 실시간으로 읽어 teler 엔진에 파이핑 후 탐지 시 Slack 웹훅으로 알림
- **에이전트 연결 방식**: teler가 탐지 이벤트를 `TELER_WEBHOOK_ENABLED=true`인 경우 SeCuardian의 `POST /api/teler/alerts`로 전송. SeCuardian이 인메모리 deque에 저장 후 조회 제공

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian-net` 로 사전 생성 필요 |
| Caddy 액세스 로그 | `logs/caddy.log` 파일이 존재해야 teler가 실행됨 |
| teler 설정 파일 | `deploy/config/teler/config.yaml` 필요 |

---

## 3. 설치 (Install)

### 3-1. 설정 파일 준비

```bash
# teler 설정 파일 디렉터리 확인
ls deploy/config/teler/config.yaml
```

최소 설정 파일 예시:

```yaml
# deploy/config/teler/config.yaml
rules:
  - id: common-web-attacks
    stage: request

notifications:
  slack:
    token: ""   # SLACK_WEBHOOK 환경변수로 주입

log_format: |
  {remote_ip} {method} {uri} {status} {size}

output:
  - json
```

### 3-2. 로그 파일 디렉터리 확인

```bash
# Caddy 로그 디렉터리 확인
ls deploy/docker/../../logs/   # 또는 프로젝트 루트 logs/ 디렉터리
# 파일이 없으면 생성 (teler가 tail -n0 -F 로 대기)
mkdir -p logs && touch logs/caddy.log
```

### 3-3. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make teler-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.teler.yml up -d
```

### 3-4. 독립 설치 (플랫폼 저장소 없이)

```yaml
# teler-standalone.yml
services:
  teler:
    image: kitabisa/teler:v2.0.0-rc.4
    container_name: secuardian-teler
    restart: unless-stopped
    entrypoint: ["/bin/sh", "-c"]
    # Caddy 액세스 로그를 tail하여 teler에 파이핑
    command: ["tail -n0 -F /input/caddy.log | teler -c /etc/teler/config.yaml -x 25"]
    volumes:
      - ./teler-config.yaml:/etc/teler/config.yaml:ro
      - ./logs:/input:ro           # Caddy 로그 디렉터리
      - teler_logs:/logs
    environment:
      - SLACK_WEBHOOK=${TELER_SLACK_WEBHOOK:-}
    networks:
      - secuardian-net

volumes:
  teler_logs:

networks:
  secuardian-net:
    external: true
```

```bash
mkdir -p logs && touch logs/caddy.log
docker compose -f teler-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/teler-ids/teler-ids-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `TELER_WEBHOOK_ENABLED` | `true` | SeCuardian 웹훅 수신 엔드포인트 활성화 여부 |
| `TELER_ALERTS_MAX` | `500` | 메모리에 유지할 최대 알림 수 (deque maxlen) |

Worker 자체 환경 변수 (compose 파일 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `TELER_SLACK_WEBHOOK` | (없음) | Slack 웹훅 URL (탐지 알림 발송용) |

teler가 SeCuardian으로 알림을 보내려면 `config.yaml`의 알림 설정에 SeCuardian의 웹훅 URL을 추가하세요:

```yaml
# deploy/config/teler/config.yaml 내 알림 섹션
notifications:
  webhook:
    url: http://secuardian:8200/api/teler/alerts
    method: POST
```

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make teler-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/teler/status | python3 -m json.tool

# 이벤트 조회
make teler-events
# 또는
curl -sf http://localhost:8200/api/teler/events | python3 -m json.tool

# teler 컨테이너 실행 상태 확인
docker ps --filter name=secuardian-teler
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍 (teler 탐지 출력 포함)
make teler-logs
# 또는
docker compose -f deploy/docker/docker-compose.teler.yml logs -f

# Worker 중단
make teler-down
# 또는
docker compose -f deploy/docker/docker-compose.teler.yml down --remove-orphans
```

---

## English Summary

**Worker**: [teler](https://github.com/kitabisa/teler) v2.0.0-rc.4 (kitabisa, Apache-2.0) — real-time HTTP intrusion detection that tails Caddy access logs.

- **No exposed ports**: teler reads `logs/caddy.log` via `tail -n0 -F` and pipes to the teler engine; no HTTP port
- **Prerequisites**: `logs/caddy.log` must exist (`touch logs/caddy.log` if needed); `deploy/config/teler/config.yaml` must exist
- **Start**: `make teler-up` or `docker compose -f deploy/docker/docker-compose.teler.yml up -d`
- **Network**: requires external `secuardian-net` Docker network
- **Key env vars**: `TELER_WEBHOOK_ENABLED=true`, `TELER_ALERTS_MAX=500`; set `TELER_SLACK_WEBHOOK` for Slack notifications
- **Wire-up**: add SeCuardian webhook URL (`http://secuardian:8200/api/teler/alerts`) to `deploy/config/teler/config.yaml` notifications section
- **Verify**: `make teler-status` and `make teler-events`
- **Stop**: `make teler-down`
