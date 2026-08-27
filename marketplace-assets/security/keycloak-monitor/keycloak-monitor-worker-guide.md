# Keycloak IAM 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(Keycloak IAM 서버)가 기동되어 있어야 동작합니다.
> This agent requires a running Keycloak server.

---

## 1. Worker 개요

- **도구 이름**: [Keycloak](https://www.keycloak.org/) (Apache-2.0)
- **역할**: OIDC/SAML 기반 IAM·SSO 서버. 본 에이전트는 헬스·OIDC 디스커버리·Realm·사용자 목록을 조회합니다.
- **연결 방식**: `KEYCLOAK_URL`(OIDC/Admin API)·`KEYCLOAK_MGMT_URL`(헬스) 로 HTTP 접근, Realm/사용자 조회는 `admin-cli` password grant (`KEYCLOAK_ADMIN_USER`/`KEYCLOAK_ADMIN_PASSWORD`)
- **포트**: `8880` (HTTP / Admin Console), `9880` (management: `/health/ready`)

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Docker Engine / Compose | 24.0+ / v2.20+ |
| PostgreSQL | Keycloak 전용 (compose 파일에 포함) |
| 환경 파일 | `deploy/docker/.env.keycloak` (`keycloak.env.example` 복사) |

## 3. 설치 (SeCuardian 저장소 Makefile 기준)

```bash
cp deploy/docker/keycloak.env.example deploy/docker/.env.keycloak
# KEYCLOAK_ADMIN_PASSWORD, KC_DB_PASSWORD 를 16자 이상 강한 값으로 변경
make keycloak-up        # docker compose -f deploy/docker/docker-compose.keycloak.yml --env-file deploy/docker/.env.keycloak up -d
make keycloak-status    # OIDC Discovery 확인
make keycloak-logs      # 로그
make keycloak-down      # 중단
```

### 독립 설치 (저장소 없이)

```bash
docker run -d --name keycloak -p 8880:8080 -p 9880:9000 \
  -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD='<강한 비밀번호>' \
  -e KC_HEALTH_ENABLED=true \
  quay.io/keycloak/keycloak:latest start-dev
curl -sf http://localhost:8880/realms/master/.well-known/openid-configuration | head -c 300
curl -sf http://localhost:9880/health/ready
```

이후 Admin Console(`http://localhost:8880`)에서 Realm `internal-realm` 과 클라이언트 `secuardian` 을 생성합니다.

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
KEYCLOAK_URL=http://localhost:8880          # 필수
KEYCLOAK_ADMIN_PASSWORD=<admin 비밀번호>    # 필수 — /realms, /users 조회에 사용. 미설정 시 503
KEYCLOAK_MGMT_URL=http://localhost:9880     # 선택 (기본값)
KEYCLOAK_REALM=internal-realm               # 선택 (기본값)
KEYCLOAK_CLIENT_ID=secuardian               # 선택 (기본값)
KEYCLOAK_ADMIN_USER=admin                   # 선택 (기본값)
```

컨테이너 배포 시 `localhost` 대신 `host.docker.internal` 또는 서비스명을 사용합니다. 운영 환경은 비밀번호를 Vault 등 시크릿 저장소에서 주입하세요.

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/keycloak-monitor/status
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/keycloak-monitor/realms
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8200/api/addon/keycloak-monitor/users?limit=10"
```

| 증상 | 조치 |
|------|------|
| 503 `Keycloak 연결 실패` | `KEYCLOAK_URL`/포트·컨테이너 기동 확인 |
| 503 `KEYCLOAK_ADMIN_PASSWORD 미설정` | 환경변수 설정 후 앱 재시작 또는 에이전트 재활성화 |
| 401 (Admin API) | admin 계정/비밀번호 확인, `admin-cli` direct access grant 활성 여부 확인 |
