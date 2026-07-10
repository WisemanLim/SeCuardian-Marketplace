# Neosync DLP — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **라이선스 주의**: Neosync 이미지는 `NOASSERTION` 라이선스입니다. Docker 이미지 실행만 허용되며,
> 소스 수정·재배포는 금지됩니다. 법무 검토 완료 전 **프로덕션 데이터 처리를 금지**합니다 (스테이징 DB 한정).

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [Neosync](https://github.com/nucleuscloud/neosync) v0.4.44 (Nucleus Cloud, NOASSERTION)
- **역할**: 데이터 동기화·마스킹·익명화 파이프라인 관리. PII 데이터를 안전하게 변환하여 개발/스테이징 환경으로 복제
- **구성 서비스**:
  - `neosync-db`: PostgreSQL 16 (파이프라인 메타데이터 저장)
  - `neosync-api`: REST API 서버 (포트 `8080`)
  - `neosync-app`: Next.js 웹 UI (포트 `3002`)
- **에이전트 연결 방식**: SeCuardian이 `NEOSYNC_API_URL`로 Neosync API에 접근하여 파이프라인 상태 모니터링 및 Job 실행 트리거

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian-net` 로 사전 생성 필요 |
| 메모리 | 최소 2GB (API + DB + App) |
| 실행 환경 | 스테이징 DB 한정 — 프로덕션 데이터 처리 금지 |

---

## 3. 설치 (Install)

### 3-1. 환경 변수 설정

```bash
# 최소 설정 (.env 또는 환경변수)
export NEOSYNC_DB_PASSWORD="your-secure-password"  # changeme 교체 필수
export NEOSYNC_AUTH_SECRET="your-nextauth-secret"   # changeme 교체 필수
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make neosync-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.neosync.yml up -d
```

서비스 기동 순서: `neosync-db` (healthcheck 통과) → `neosync-api` → `neosync-app`

### 3-3. 독립 설치 (플랫폼 저장소 없이)

```yaml
# neosync-standalone.yml
services:
  neosync-db:
    image: postgres:16-alpine
    container_name: secuardian-neosync-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=neosync
      - POSTGRES_USER=neosync
      - POSTGRES_PASSWORD=${NEOSYNC_DB_PASSWORD:-changeme}
    volumes:
      - neosync_db:/var/lib/postgresql/data
    networks:
      - secuardian-net
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "neosync"]
      interval: 10s
      timeout: 5s
      retries: 5

  neosync-api:
    image: ghcr.io/nucleuscloud/neosync/api:0.4.44
    container_name: secuardian-neosync-api
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=neosync-db
      - DB_PORT=5432
      - DB_NAME=neosync
      - DB_USER=neosync
      - DB_PASS=${NEOSYNC_DB_PASSWORD:-changeme}
      - DB_SSL_DISABLE=true
      - NUCLEUS_ENV=development
    depends_on:
      neosync-db:
        condition: service_healthy
    networks:
      - secuardian-net

  neosync-app:
    image: ghcr.io/nucleuscloud/neosync/app:0.4.44
    container_name: secuardian-neosync-app
    restart: unless-stopped
    ports:
      - "3002:3000"
    environment:
      - NEOSYNC_API_BASE_URL=http://neosync-api:8080
      - NEXTAUTH_SECRET=${NEOSYNC_AUTH_SECRET:-changeme}
      - NEXTAUTH_URL=http://localhost:3002
    depends_on:
      - neosync-api
    networks:
      - secuardian-net

volumes:
  neosync_db:

networks:
  secuardian-net:
    external: true
```

```bash
docker compose -f neosync-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/neosync-dlp/neosync-dlp-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `NEOSYNC_API_URL` | (없음) | Neosync API base URL (예: `http://localhost:8080`) |
| `NEOSYNC_API_KEY` | (없음) | Neosync API 인증 키 (Neosync UI에서 발급) |
| `NEOSYNC_ACCOUNT_ID` | (없음) | Neosync 계정 ID |

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make neosync-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/neosync/status | python3 -m json.tool

# Neosync API 직접 확인
curl -sf http://localhost:8080/health

# Neosync 웹 UI 접근
# 브라우저에서: http://localhost:3002

# PII 패턴 조회
make neosync-pii-patterns
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
make neosync-logs
# 또는
docker compose -f deploy/docker/docker-compose.neosync.yml logs -f

# Worker 중단
make neosync-down
# 또는
docker compose -f deploy/docker/docker-compose.neosync.yml down --remove-orphans
```

---

## English Summary

**Worker**: [Neosync](https://github.com/nucleuscloud/neosync) v0.4.44 (Nucleus Cloud, NOASSERTION — run-only, no source modification or redistribution). **Staging DB only — no production data.**

- **Services**: `neosync-db` (PostgreSQL 16), `neosync-api` (port `8080`), `neosync-app` (port `3002`)
- **Start**: `make neosync-up` or `docker compose -f deploy/docker/docker-compose.neosync.yml up -d`
- **Network**: requires external `secuardian-net` Docker network
- **Key env vars for SeCuardian**: `NEOSYNC_API_URL` (e.g. `http://localhost:8080`), `NEOSYNC_API_KEY`, `NEOSYNC_ACCOUNT_ID`
- **Required secrets**: replace `NEOSYNC_DB_PASSWORD` and `NEOSYNC_AUTH_SECRET` defaults before deploying
- **Verify**: `curl http://localhost:8080/health` and browse to `http://localhost:3002`
- **Stop**: `make neosync-down`
