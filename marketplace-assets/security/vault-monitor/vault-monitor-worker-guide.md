# Vault 시크릿 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(HashiCorp Vault 서버)가 기동되어 있어야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [HashiCorp Vault](https://developer.hashicorp.com/vault) (BUSL-1.1 — 내부 사용 OK, 경쟁 SaaS 제공 금지)
- **역할**: 시크릿 저장(KV v2)·AppRole 인증·PKI. 본 에이전트는 헬스/봉인 상태와 AppRole·PKI 구성, KV 경로 접근성을 점검합니다.
- **연결 방식**: `VAULT_ADDR` 로 HTTP API (`/v1/sys/health`, `/v1/sys/auth`, `/v1/sys/mounts`), 인증은 AppRole(`VAULT_ROLE_ID`+`VAULT_SECRET_ID`) 우선, 폴백 `VAULT_TOKEN`
- **포트**: `8201` (호스트, SeCuardian BE 8200 과 충돌 방지) → 컨테이너 `8200`

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Docker Engine / Compose | 24.0+ / v2.20+ |
| 환경 파일 | `deploy/docker/.env.vault` (`vault.env.example` 복사) |
| (선택) vault CLI | `make vault-status` 에서 사용, 없으면 curl 폴백 |

## 3. 설치 (SeCuardian 저장소 Makefile 기준)

```bash
cp deploy/docker/vault.env.example deploy/docker/.env.vault
make vault-up        # Dev 모드 (자동 unseal, 메모리 스토리지) — docker-compose.vault.yml
make vault-status    # 봉인/초기화 상태
make vault-init      # 초기 시크릿 경로 생성 (secuardian/keycloak, secuardian/logto, secuardian/app) — 1회
make vault-setup     # AppRole + PKI 설정 — 출력된 VAULT_ROLE_ID / VAULT_SECRET_ID (24h TTL) 기록
make vault-migrate   # (선택) .env.local 시크릿 → KV v2 마이그레이션
make vault-down
```

운영 환경은 `deploy/docker/docker-compose.vault.prod.yml` (파일 스토리지, 수동 unseal) 을 사용하고 Root Token 은 초기화 후 즉시 revoke 하세요.

### 독립 설치 (저장소 없이, 개발용)

```bash
docker run -d --name vault --cap-add=IPC_LOCK -p 8201:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-root-token-secuardian hashicorp/vault:latest
export VAULT_ADDR=http://localhost:8201 VAULT_TOKEN=dev-root-token-secuardian
vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault auth enable approle
vault write auth/approle/role/secuardian token_ttl=1h secret_id_ttl=24h
vault read -field=role_id auth/approle/role/secuardian/role-id
vault write -f -field=secret_id auth/approle/role/secuardian/secret-id
```

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
VAULT_ADDR=http://localhost:8201     # 필수
VAULT_ROLE_ID=<make vault-setup 출력> # 권장 (AppRole)
VAULT_SECRET_ID=<make vault-setup 출력>
# VAULT_TOKEN=dev-root-token-secuardian  # 개발 폴백 (운영 사용 금지)
```

`/approle/status` 는 `VAULT_TOKEN` 헤더로 `sys/auth`·`sys/mounts` 를 조회하므로 토큰 또는 AppRole 중 하나는 설정되어야 합니다. `/kv/check` 는 hvac(`dependencies.python`)를 사용하며 미설치 시 501 을 반환합니다.

### (선택) 기동 시 Vault 시크릿 → 환경변수 주입

내장판의 `vault_loader` lifespan 훅은 Addon 에 포함되지 않습니다. 필요 시 배포 entrypoint 에서:

```bash
uv run python -c "import sys; sys.path.insert(0,'addon-agents/deployed/vault-monitor'); \
from vault_monitor_lib.loader import apply_to_environ; print(apply_to_environ())"
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/vault-monitor/status
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/vault-monitor/approle/status
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/vault-monitor/kv/check
```

| 증상 | 조치 |
|------|------|
| 503 `Vault 연결 실패` | `VAULT_ADDR`/포트, 컨테이너 기동 확인 |
| `health: SEALED` | `vault operator unseal` (운영 모드) |
| `secuardian_role_exists: false` | `make vault-setup` 재실행 |
| Secret ID 만료 | `make vault-setup` 재실행 후 `VAULT_SECRET_ID` 갱신 |
