# Velociraptor DFIR — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [Velociraptor](https://github.com/Velocidex/velociraptor) v0.72.4 (Velocidex, Apache-2.0 라이선스)
- **역할**: 엔드포인트 포렌식 헌팅 및 아티팩트 수집 플랫폼. 에이전트(클라이언트)를 원격에서 쿼리하여 메모리 덤프, 파일시스템 아티팩트, 프로세스 목록 등을 수집
- **에이전트 연결 방식**: SeCuardian이 `VELOCIRAPTOR_URL`과 `VELOCIRAPTOR_API_KEY`로 Velociraptor REST API에 접근하여 헌트 생성·조회·결과 수신 수행
- **포트**: `8889` (Web GUI, HTTPS self-signed), `8000` (gRPC API / 클라이언트 연결)

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian-net` 로 사전 생성 필요 |
| Velociraptor 서버 설정 파일 | `deploy/config/velociraptor/server.config.yaml` 필요 |
| 실행 환경 | 격리 스테이징 환경 전용 — 프로덕션 직접 실행 금지 |

---

## 3. 설치 (Install)

### 3-1. 서버 설정 파일 생성 (최초 1회)

```bash
# Velociraptor 설정 파일 생성 (컨테이너 외부에서)
docker run --rm velocidex/velociraptor:v0.72.4 \
  config generate -i > deploy/config/velociraptor/server.config.yaml
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make dfir-up
# 기동 후 안내: [dfir] Web GUI: https://localhost:8889

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.dfir.yml up -d
```

### 3-3. 독립 설치 (플랫폼 저장소 없이)

```yaml
# velociraptor-standalone.yml
services:
  velociraptor:
    image: velocidex/velociraptor:v0.72.4
    container_name: secuardian-velociraptor
    restart: unless-stopped
    command: frontend -v
    ports:
      - "8889:8889"   # Web GUI (HTTPS self-signed)
      - "8000:8000"   # gRPC API
    volumes:
      - velociraptor-data:/velociraptor
      - ./velociraptor-config:/etc/velociraptor:ro
    environment:
      VELOCIRAPTOR_CONFIG: /etc/velociraptor/server.config.yaml
    networks:
      - secuardian-net

volumes:
  velociraptor-data:

networks:
  secuardian-net:
    external: true
```

```bash
# 설정 디렉터리 준비
mkdir -p ./velociraptor-config
# 위 설정 파일 생성 명령으로 server.config.yaml 생성 후 해당 디렉터리에 배치
docker compose -f velociraptor-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/velociraptor-dfir/velociraptor-dfir-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `VELOCIRAPTOR_URL` | `https://localhost:8000` | Velociraptor 서버 base URL (gRPC API) |
| `VELOCIRAPTOR_API_KEY` | (없음) | Velociraptor REST API 인증 키 (`X-API-Key` 헤더) |
| `VELOCIRAPTOR_ORG_ID` | `root` | Velociraptor 조직 ID |

> 주의: Velociraptor API 호출은 self-signed 인증서로 인해 `verify=False`로 동작합니다. 프로덕션에서는 인증서를 교체하세요.

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make dfir-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/dfir/status | python3 -m json.tool

# Velociraptor Web GUI 접근
# 브라우저에서: https://localhost:8889 (self-signed 인증서 경고 무시)

# 헌트 목록 조회
make dfir-hunts
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
make dfir-logs
# 또는
docker compose -f deploy/docker/docker-compose.dfir.yml logs -f

# Worker 중단
docker compose -f deploy/docker/docker-compose.dfir.yml down
```

---

## English Summary

**Worker**: [Velociraptor](https://github.com/Velocidex/velociraptor) v0.72.4 (Velocidex, Apache-2.0) — endpoint forensic hunting and artifact collection platform.

- **Prerequisites**: create `deploy/config/velociraptor/server.config.yaml` (use `docker run velocidex/velociraptor config generate -i`)
- **Start**: `make dfir-up` or `docker compose -f deploy/docker/docker-compose.dfir.yml up -d`
- **Ports**: `8889` (HTTPS Web GUI), `8000` (gRPC API / client connections)
- **Network**: requires external `secuardian-net` Docker network
- **Key env vars**: `VELOCIRAPTOR_URL=https://localhost:8000`, `VELOCIRAPTOR_API_KEY` (required for API auth), `VELOCIRAPTOR_ORG_ID=root`
- **Note**: API calls use `verify=False` for self-signed certs — replace certs in production
- **Verify**: `make dfir-status` and browse to `https://localhost:8889`
- **Stop**: `docker compose -f deploy/docker/docker-compose.dfir.yml down`
