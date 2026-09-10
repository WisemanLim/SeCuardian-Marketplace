# Logto IAM 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker 가 기동되어 있어야 완전히 동작합니다. 미기동 시 우아하게 저하됩니다.
> This agent requires an external worker; it degrades gracefully when the worker is down.

---

## 1. Worker 개요

- **도구**: [Logto](https://logto.io/) (MPL-2.0) — OIDC IdP (Keycloak 대안)
- **역할**: Logto 의 OIDC 디스커버리(`/oidc/.well-known/openid-configuration`)로 헬스·issuer·JWKS·token endpoint 를 요약합니다.
- **포트**: `3801`(코어/OIDC) · `3802`(Admin Console)
- **에이전트 설정 방식**: 환경변수(`os.getenv`) — SeCuardian-Basic `.env.*` 또는 compose `environment` 에 선언

## 2. 환경변수 (`optional_env`)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `LOGTO_ENDPOINT` | Logto 코어(OIDC) URL | `http://localhost:3801` |
| `LOGTO_ADMIN_URL` | Logto 관리 콘솔 URL | `http://localhost:3802` |

## 3. 설치 (독립 설치 예시)

```bash
docker network create logto-net 2>/dev/null || true
docker run -d --name logto-pg --network logto-net -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD='<강한 비밀번호>' -e POSTGRES_DB=logto postgres:17
docker run -d --name logto --network logto-net -p 3801:3001 -p 3802:3002 \
  -e DB_URL='postgres://postgres:<강한 비밀번호>@logto-pg:5432/logto' \
  -e ENDPOINT=http://localhost:3801 -e ADMIN_ENDPOINT=http://localhost:3802 \
  svhd/logto:latest sh -c 'npm run cli db seed -- --swe && npm start'
curl -sf http://localhost:3801/oidc/.well-known/openid-configuration | head -c 300
```

## 4. 에이전트 엔드포인트 (`/api/addon/logto-monitor`)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /status` | 헬스 + OIDC issuer/jwks/token endpoint |
| `GET /config` | 연결 설정(시크릿 제외) |

## 5. 미기동 시 동작

Logto 미접속 시 `/status` 는 **503** `Logto 연결 실패` 로 우아하게 저하됩니다.

## 6. 확인

```bash
curl -s -H "Authorization: Bearer <token>" http://localhost:8200/api/addon/logto-monitor/status
```
