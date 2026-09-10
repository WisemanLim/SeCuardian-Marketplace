# 관측성 모니터 (Prometheus / Grafana / Loki) — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker 가 기동되어 있어야 완전히 동작합니다. 미기동 시 우아하게 저하됩니다.
> This agent requires an external worker; it degrades gracefully when the worker is down.

---

## 1. Worker 개요

- **도구**: [Prometheus](https://prometheus.io/) · [Grafana](https://grafana.com/) · [Loki](https://grafana.com/oss/loki/) (Apache-2.0 / AGPL-3.0)
- **역할**: 3종 스택 헬스를 집계하고 MTTD(탐지→대응) 알림·대응 이벤트를 기록·조회합니다.
- **포트**: `9090`(Prometheus) · `3000`(Grafana) · `3100`(Loki)
- **에이전트 설정 방식**: 환경변수(`os.getenv`) — SeCuardian-Basic `.env.*` 또는 compose `environment` 에 선언

## 2. 환경변수 (`optional_env`)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PROMETHEUS_URL` | Prometheus 서버 URL | `http://localhost:9090` |
| `GRAFANA_URL` | Grafana URL | `http://localhost:3000` |
| `LOKI_URL` | Loki URL | `http://localhost:3100` |

## 3. 설치 (독립 설치 예시)

```bash
docker network create obs-net 2>/dev/null || true
docker run -d --name prometheus --network obs-net -p 9090:9090 prom/prometheus:latest
docker run -d --name loki --network obs-net -p 3100:3100 grafana/loki:latest
docker run -d --name grafana --network obs-net -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD='<강한 비밀번호>' grafana/grafana:latest
curl -sf http://localhost:9090/-/ready && curl -sf http://localhost:3000/api/health && curl -sf http://localhost:3100/ready
```

## 4. 에이전트 엔드포인트 (`/api/addon/observability-monitor`)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /status` | 3종 헬스 집계 |
| `GET /metrics` | 주요 지표 요약 |
| `POST /mttd/alert · POST /mttd/response` | 탐지·대응 이벤트 기록(202) |
| `GET /mttd · DELETE /mttd` | MTTD 통계 조회·초기화 |

## 5. 미기동 시 동작

각 백엔드 미접속 시 해당 항목만 `DOWN/UNREACHABLE` 로 표기되며 MTTD 기록은 계속 동작합니다.

## 6. 확인

```bash
curl -s -H "Authorization: Bearer <token>" http://localhost:8200/api/addon/observability-monitor/status
```
