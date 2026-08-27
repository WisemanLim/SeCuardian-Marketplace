"""Vault hvac 클라이언트 팩토리 — AppRole 우선, 폴백 VAULT_TOKEN (app/core/vault.py 이식).
# License: BUSL-1.1 (HashiCorp Vault) | Usage: internal only

설정은 호출 시점에 환경변수에서 읽는다: VAULT_ADDR, VAULT_TOKEN, VAULT_ROLE_ID, VAULT_SECRET_ID.
hvac 는 지연 import — 미설치 환경에서도 모듈 로드는 성공한다.
"""
import os


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def vault_addr() -> str:
    return env("VAULT_ADDR", "http://localhost:8201").rstrip("/")


def get_vault_client():
    """인증된 hvac.Client 반환.

    우선순위: 1) AppRole (VAULT_ROLE_ID + VAULT_SECRET_ID) 2) VAULT_TOKEN 3) 미인증(연결 테스트 전용)
    Raises: RuntimeError — hvac 미설치
    """
    try:
        import hvac
    except ImportError as exc:
        raise RuntimeError("hvac 패키지 미설치 — dependencies.python 의 hvac 설치 필요") from exc

    client = hvac.Client(url=vault_addr())
    role_id, secret_id = env("VAULT_ROLE_ID"), env("VAULT_SECRET_ID")
    if role_id and secret_id:
        result = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
        client.token = result["auth"]["client_token"]
    elif env("VAULT_TOKEN"):
        client.token = env("VAULT_TOKEN")
    return client


def get_secret(path: str, key: str) -> str:
    """KV v2 시크릿 값 조회. 예: get_secret("secuardian/keycloak", "admin_password")"""
    client = get_vault_client()
    data = client.secrets.kv.v2.read_secret_version(path=path)
    return data["data"]["data"][key]
