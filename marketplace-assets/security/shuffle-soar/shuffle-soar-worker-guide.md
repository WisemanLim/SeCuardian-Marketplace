# Shuffle SOAR — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **라이선스**: Shuffle (Apache-2.0), TheHive (AGPL-3.0), Cortex (AGPL-3.0).
> AGPL-3.0 도구는 네트워크 서비스로 제공 시 소스 공개 의무가 있습니다.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [Shuffle SOAR](https://github.com/Shuffle/Shuffle) v1.4.2 (Apache-2.0) + [TheHive](https://github.com/TheHive-Project/TheHive) v5.3.3 (AGPL-3.0) + [Cortex](https://github.com/TheHive-Project/Cortex) v3.1.8 (AGPL-3.0)
- **역할**: 보안 워크플로 자동화(SOAR). Shuffle은 웹훅 기반 워크플로 실행, TheHive는 케이스 관리, Cortex는 분석기/대응 앱 실행
- **구성 서비스**:
  - `shuffle-frontend`: Shuffle UI (포트 `3001`)
  - `shuffle-backend`: Shuffle API 서버 (내부, 포트 공개 없음)
  - `shuffle-orborus`: 워크플로 실행 엔진 (Docker socket 필요)
  - `shuffle-database`: Google Cloud Datastore 에뮬레이터 (내부)
  - `thehive`: 케이스 관리 (포트 `9000`)
  - `cassandra`: TheHive DB 백엔드 (내부)
  - `cortex`: 분석기 실행 (포트 `9001`)
- **에이전트 연결 방식**: SeCuardian이 `SHUFFLE_URL`과 `SHUFFLE_API_TOKEN`으로 Shuffle API에 접근하여 워크플로 트리거 및 실행 결과 수신

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 (Docker socket 접근 필요) |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian-net` 로 사전 생성 필요 |
| 메모리 | 최소 4GB (Cassandra + TheHive + Shuffle + Cortex) |
| `/var/run/docker.sock` | shuffle-orborus 실행을 위해 Docker socket 마운트 필요 |

---

## 3. 설치 (Install)

### 3-1. 환경 변수 설정

```bash
export SHUFFLE_ENCRYPTION_KEY="your-secure-encryption-key"  # changeme 교체 필수
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make soar-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.soar.yml up -d
```

서비스 기동 순서: `shuffle-database` (healthcheck 통과) → `cassandra` → `shuffle-backend` → `shuffle-frontend` + `shuffle-orborus` + `thehive` + `cortex`

### 3-3. 독립 설치 (플랫폼 저장소 없이)

핵심 서비스만 포함한 최소 구성:

```yaml
# shuffle-soar-standalone.yml
services:
  shuffle-backend:
    image: ghcr.io/shuffle/shuffle-backend:1.4.2
    container_name: secuardian-shuffle-backend
    restart: unless-stopped
    environment:
      - DATASTORE_EMULATOR_HOST=shuffle-database:8000
      - SHUFFLE_APP_HOTLOAD_FOLDER=/shuffle-apps
      - SHUFFLE_FILE_LOCATION=/shuffle-files
      - BASE_URL=http://localhost:3001
      - SHUFFLE_ENCRYPTION_MODIFIER=${SHUFFLE_ENCRYPTION_KEY:-changeme}
      - SHUFFLE_ELASTIC=false
    volumes:
      - shuffle_apps:/shuffle-apps
      - shuffle_files:/shuffle-files
    depends_on:
      shuffle-database:
        condition: service_healthy
    networks:
      - secuardian-net

  shuffle-frontend:
    image: ghcr.io/shuffle/shuffle-frontend:1.4.2
    container_name: secuardian-shuffle-frontend
    restart: unless-stopped
    ports:
      - "3001:80"
    environment:
      - BACKEND_HOSTNAME=shuffle-backend
    depends_on:
      - shuffle-backend
    networks:
      - secuardian-net

  shuffle-orborus:
    image: ghcr.io/shuffle/shuffle-orborus:1.4.0
    container_name: secuardian-shuffle-orborus
    restart: unless-stopped
    environment:
      - SHUFFLE_APP_SDK_VERSION=1.2.0
      - ENVIRONMENT_NAME=Shuffle
      - BASE_URL=http://shuffle-backend:5001
      - DOCKER_API_VERSION=1.40
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - shuffle-backend
    networks:
      - secuardian-net

  shuffle-database:
    image: google/cloud-sdk:emulators
    container_name: secuardian-shuffle-db
    restart: unless-stopped
    environment:
      - CLOUDSDK_CORE_DISABLE_PROMPTS=1
      - CLOUDSDK_CORE_PROJECT=shuffle
    command: ["gcloud", "beta", "emulators", "datastore", "start", "--host-port=0.0.0.0:8000", "--no-store-on-disk", "--project=shuffle"]
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "8000"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - secuardian-net
    volumes:
      - shuffle_db:/data

volumes:
  shuffle_apps:
  shuffle_files:
  shuffle_db:

networks:
  secuardian-net:
    external: true
```

```bash
docker compose -f shuffle-soar-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/shuffle-soar/shuffle-soar-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `SHUFFLE_URL` | `http://localhost:3001` | Shuffle SOAR 인스턴스 base URL |
| `SHUFFLE_API_TOKEN` | (없음) | Shuffle API 인증 Bearer 토큰 (Shuffle UI에서 발급) |

### API 토큰 발급

```bash
# Shuffle UI 접근 후 Settings > API Keys에서 발급
# 브라우저에서: http://localhost:3001
```

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make soar-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/soar/status | python3 -m json.tool

# Shuffle UI 접근
# 브라우저에서: http://localhost:3001

# TheHive 접근
# 브라우저에서: http://localhost:9000

# Cortex 접근
# 브라우저에서: http://localhost:9001

# 케이스 목록 조회
make soar-cases
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍 (전체)
make soar-logs
# 또는
docker compose -f deploy/docker/docker-compose.soar.yml logs -f

# 특정 서비스 로그
docker compose -f deploy/docker/docker-compose.soar.yml logs -f shuffle-backend

# Worker 중단
make soar-down
# 또는
docker compose -f deploy/docker/docker-compose.soar.yml down --remove-orphans
```

---

## English Summary

**Worker**: [Shuffle SOAR](https://github.com/Shuffle/Shuffle) v1.4.2 (Apache-2.0) + [TheHive](https://github.com/TheHive-Project/TheHive) v5.3.3 (AGPL-3.0) + [Cortex](https://github.com/TheHive-Project/Cortex) v3.1.8 (AGPL-3.0).

- **Start**: `make soar-up` or `docker compose -f deploy/docker/docker-compose.soar.yml up -d`
- **Ports**: `3001` (Shuffle UI), `9000` (TheHive), `9001` (Cortex)
- **Network**: requires external `secuardian-net` Docker network; shuffle-orborus needs `/var/run/docker.sock`
- **Key env vars**: `SHUFFLE_URL=http://localhost:3001`, `SHUFFLE_API_TOKEN` (issue from Shuffle UI Settings > API Keys)
- **Required secret**: replace `SHUFFLE_ENCRYPTION_KEY` default (`changeme`) before deploying
- **Verify**: `make soar-status` and browse to `http://localhost:3001`
- **Stop**: `make soar-down`
- **AGPL-3.0 note**: TheHive and Cortex require source disclosure if modified and served over a network
