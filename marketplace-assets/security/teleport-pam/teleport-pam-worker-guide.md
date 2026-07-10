# Teleport PAM — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **라이선스**: Teleport는 AGPL-3.0입니다. 네트워크 서비스로 수정·배포 시 소스 공개 의무가 있습니다.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [Teleport](https://github.com/gravitational/teleport) v15.4.7 (Gravitational, AGPL-3.0)
- **이미지**: `public.ecr.aws/gravitational/teleport-distroless:15.4.7` (공식 distroless 이미지)
- **역할**: 인프라 특권 접근 관리(PAM). SSH·RDP·Kubernetes·DB에 대한 단일 엔트리포인트, JIT 승인, 세션 녹화, 감사 이벤트 스트리밍 제공
- **포트**:
  - `3023`: SSH Proxy
  - `3025`: Auth Server gRPC
  - `3080`: Web UI + HTTPS (ACME)
  - `3026`: Kubernetes Proxy
  - `3036`: MySQL Proxy
- **에이전트 연결 방식**: SeCuardian이 `TELEPORT_PROXY_URL`과 `TELEPORT_TOKEN`으로 Teleport API에 접근하여 감사 이벤트 수신 및 세션·사용자 목록 조회

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| `secuardian-net` Docker network | `docker network create secuardian_default` 로 사전 생성 필요 |
| Teleport 설정 파일 | `deploy/config/teleport/teleport.yaml` 필요 |
| 도메인·HTTPS | 프로덕션에서는 유효한 도메인 필요 (ACME TLS) |

---

## 3. 설치 (Install)

### 3-1. Teleport 설정 파일 준비 (최초 1회)

```bash
# 설정 파일 디렉터리 생성
mkdir -p deploy/config/teleport

# 최소 설정 파일 예시 생성
cat > deploy/config/teleport/teleport.yaml << 'EOF'
teleport:
  nodename: teleport.internal
  data_dir: /var/lib/teleport
  log:
    output: stderr
    severity: INFO

auth_service:
  enabled: true
  cluster_name: localhost
  tokens:
    - "node:your-join-token-here"

ssh_service:
  enabled: true

proxy_service:
  enabled: true
  listen_addr: 0.0.0.0:3023
  web_listen_addr: 0.0.0.0:3080
  tunnel_listen_addr: 0.0.0.0:3024
  public_addr: localhost:3080
  https_keypairs: []
EOF
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (권장)
make teleport-up
# 기동 후 안내: [teleport] Web UI: https://localhost:3080

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.teleport.yml up -d
```

### 3-3. 초기 관리자 계정·토큰 발급

```bash
# Makefile 설정 스크립트 실행
make teleport-setup
# 또는 deploy/scripts/teleport_setup.sh 직접 실행
bash deploy/scripts/teleport_setup.sh
```

### 3-4. 독립 설치 (플랫폼 저장소 없이)

```yaml
# teleport-standalone.yml
services:
  teleport:
    image: public.ecr.aws/gravitational/teleport-distroless:15.4.7
    container_name: secuardian-teleport
    hostname: teleport.internal
    restart: unless-stopped
    ports:
      - "3023:3023"  # SSH Proxy
      - "3025:3025"  # Auth Server gRPC
      - "3080:3080"  # Web UI + HTTPS
      - "3026:3026"  # Kubernetes Proxy
      - "3036:3036"  # MySQL Proxy
    volumes:
      - teleport-data:/var/lib/teleport
      - ./teleport.yaml:/etc/teleport/teleport.yaml:ro
    environment:
      TELEPORT_SKIP_VERSION_CHECK: "true"
    networks:
      - secuardian-net

volumes:
  teleport-data:

networks:
  secuardian-net:
    external: true
```

```bash
docker compose -f teleport-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/teleport-pam/teleport-pam-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `TELEPORT_PROXY_URL` | `https://localhost:3080` | Teleport 프록시 base URL |
| `TELEPORT_TOKEN` | (없음) | Teleport API 호출용 Bearer 토큰 |
| `TELEPORT_CLUSTER` | `localhost` | Teleport 클러스터 이름 |
| `TELEPORT_AUDIT_MAX` | `1000` | 메모리에 유지할 최대 감사 이벤트 수 (deque maxlen) |
| `TELEPORT_WEBHOOK_ENABLED` | `true` | 웹훅 수신 엔드포인트 활성화 여부 |

> **주의**: Teleport API 호출은 self-signed 인증서에 대해 `verify=False`로 동작합니다.
> `POST /audit/events`는 의도적으로 인증 없이 열려 있습니다 — 네트워크/방화벽 레벨에서 보호하세요.
> 감사 이벤트는 인메모리(deque)에 저장되므로 재시작 시 소멸됩니다. 영속성이 필요하면 DB sink를 추가하세요.

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make teleport-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/teleport/status | python3 -m json.tool

# Teleport Web UI 접근
# 브라우저에서: https://localhost:3080 (self-signed 인증서 경고 무시)

# 세션 목록 조회
make teleport-sessions

# 감사 이벤트 조회
make teleport-audit
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
make teleport-logs
# 또는
docker compose -f deploy/docker/docker-compose.teleport.yml logs -f

# 감사 이벤트 조회
curl -sf http://localhost:8200/api/teleport/audit | python3 -m json.tool

# Worker 중단
make teleport-down
# 또는
docker compose -f deploy/docker/docker-compose.teleport.yml down
```

---

## English Summary

**Worker**: [Teleport](https://github.com/gravitational/teleport) v15.4.7 (Gravitational, AGPL-3.0) — privileged access management (PAM) with SSH/RDP/K8s/DB proxying, JIT approvals, and session recording.

- **Image**: `public.ecr.aws/gravitational/teleport-distroless:15.4.7` (official, no tag on gravitational/teleport)
- **Prerequisites**: create `deploy/config/teleport/teleport.yaml`; run `make teleport-setup` to issue initial admin account and token
- **Start**: `make teleport-up` or `docker compose -f deploy/docker/docker-compose.teleport.yml up -d`
- **Ports**: `3023` (SSH), `3025` (Auth gRPC), `3080` (Web UI + HTTPS), `3026` (Kubernetes), `3036` (MySQL)
- **Network**: requires external `secuardian_default` Docker network
- **Key env vars**: `TELEPORT_PROXY_URL=https://localhost:3080`, `TELEPORT_TOKEN` (required), `TELEPORT_CLUSTER=localhost`, `TELEPORT_AUDIT_MAX=1000`, `TELEPORT_WEBHOOK_ENABLED=true`
- **Security note**: `POST /audit/events` is unauthenticated — protect at network/firewall level; audit events are in-memory only (lost on restart)
- **Verify**: `make teleport-status` and browse to `https://localhost:3080`
- **Stop**: `make teleport-down`
