# OpenTelemetry Collector — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [OpenTelemetry Collector Contrib](https://github.com/open-telemetry/opentelemetry-collector-contrib) v0.111.0 (Apache-2.0) + [Jaeger](https://github.com/jaegertracing/jaeger) v1.61.0 (Apache-2.0)
- **역할**: 애플리케이션 텔레메트리(트레이스·메트릭·로그)를 수집·처리·내보내는 파이프라인 허브. Jaeger는 분산 추적 UI 및 저장소 역할
- **구성 서비스**:
  - `otel-collector`: OTel Collector Contrib (포트 `4317` gRPC, `4318` HTTP, `8889` Prometheus, `13133` Health)
  - `jaeger`: Jaeger All-in-One (포트 `16686` UI, `14317` OTLP gRPC offset)
- **에이전트 연결 방식**: SeCuardian이 `OTEL_HEALTH_URL`, `OTEL_ZPAGES_URL`, `OTEL_METRICS_URL`으로 Collector 상태를 조회

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian-net` 로 사전 생성 필요 |
| OTel Collector 설정 파일 | `deploy/config/otel/otel-collector.yaml` 필요 |
| 호스트 로그 접근 (선택) | `/var/log` 마운트 — 호스트 로그 수집 시 |

---

## 3. 설치 (Install)

### 3-1. Collector 설정 파일 확인

```bash
# 설정 파일 위치 확인
ls deploy/config/otel/otel-collector.yaml
```

설정 파일이 없으면 최소 설정으로 생성:

```yaml
# deploy/config/otel/otel-collector.yaml (최소 예시)
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make otel-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.otel.yml up -d
```

### 3-3. 독립 설치 (플랫폼 저장소 없이)

```yaml
# otel-standalone.yml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.111.0
    container_name: secuardian-otel-collector
    restart: unless-stopped
    ports:
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
      - "8889:8889"    # Prometheus metrics
      - "13133:13133"  # Health check
    volumes:
      - ./otel-collector.yaml:/etc/otelcol-contrib/otel-collector.yaml:ro
    command: ["--config=/etc/otelcol-contrib/otel-collector.yaml"]
    networks:
      - secuardian-net
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:13133/"]
      interval: 30s
      timeout: 5s
      retries: 3

  jaeger:
    image: jaegertracing/all-in-one:1.61.0
    container_name: secuardian-jaeger
    restart: unless-stopped
    ports:
      - "16686:16686"  # Jaeger UI
      - "14317:4317"   # OTLP gRPC (충돌 방지 오프셋)
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - SPAN_STORAGE_TYPE=memory
    networks:
      - secuardian-net

networks:
  secuardian-net:
    external: true
```

```bash
docker compose -f otel-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/otel-collector/otel-collector-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `OTEL_HEALTH_URL` | `http://localhost:13133` | Collector health_check extension URL |
| `OTEL_ZPAGES_URL` | `http://localhost:55679` | Collector zPages (파이프라인 통계) URL |
| `OTEL_METRICS_URL` | `http://localhost:8889` | Collector Prometheus 메트릭 URL |

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make otel-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/otel/status | python3 -m json.tool

# Collector 헬스 직접 확인
curl -sf http://localhost:13133/

# Prometheus 메트릭 확인
curl -sf http://localhost:8889/metrics | head -20

# zPages 파이프라인 통계 확인
curl -sf http://localhost:55679/debug/tracez | head -20

# Jaeger UI 접근
# 브라우저에서: http://localhost:16686

# 파이프라인 설정 조회
make otel-pipelines
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
make otel-logs
# 또는
docker compose -f deploy/docker/docker-compose.otel.yml logs -f

# Worker 중단
make otel-down
# 또는
docker compose -f deploy/docker/docker-compose.otel.yml down --remove-orphans
```

---

## English Summary

**Worker**: [OTel Collector Contrib](https://github.com/open-telemetry/opentelemetry-collector-contrib) v0.111.0 + [Jaeger](https://github.com/jaegertracing/jaeger) v1.61.0 (both Apache-2.0).

- **Prerequisites**: create `deploy/config/otel/otel-collector.yaml` (see minimal example in section 3-1)
- **Start**: `make otel-up` or `docker compose -f deploy/docker/docker-compose.otel.yml up -d`
- **Ports**: `4317` (OTLP gRPC), `4318` (OTLP HTTP), `8889` (Prometheus metrics), `13133` (health check), `16686` (Jaeger UI), `14317` (Jaeger OTLP gRPC offset)
- **Network**: requires external `secuardian-net` Docker network
- **Key env vars**: `OTEL_HEALTH_URL=http://localhost:13133`, `OTEL_ZPAGES_URL=http://localhost:55679`, `OTEL_METRICS_URL=http://localhost:8889`
- **Verify**: `curl http://localhost:13133/` and browse to `http://localhost:16686`
- **Stop**: `make otel-down`
