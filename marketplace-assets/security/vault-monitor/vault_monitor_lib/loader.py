"""Vault KV v2 → 환경변수 오버라이드 로더 (app/core/vault_loader.py 이식, 선택 헬퍼).

내장판은 lifespan 훅에서 settings 객체를 패치했으나, Addon 은 코어 settings 에 접근하지 않는다.
대신 `load_vault_overrides()` 로 {ENV_NAME: value} 를 얻어 배포 계층(entrypoint 스크립트 등)에서
`os.environ` 에 주입하거나 `apply_to_environ()` 로 현재 프로세스 환경에 반영한다.
연결 불가·미인증 시 {} 반환 (env 폴백, 예외 없음).
"""
import logging
import os

from .client import get_vault_client

logger = logging.getLogger(__name__)

# 환경변수명 → (Vault KV v2 경로, 키)
VAULT_SECRET_MAP: dict = {
    "KEYCLOAK_ADMIN_PASSWORD": ("secuardian/keycloak", "admin_password"),
    "KEYCLOAK_CLIENT_SECRET": ("secuardian/keycloak", "client_secret"),
    "LOGTO_APP_SECRET": ("secuardian/logto", "app_secret"),
    "JWT_SECRET_KEY": ("secuardian/app", "jwt_secret"),
}

_PLACEHOLDERS = ("", "CHANGE_ME", "CHANGE_ME_32CHARS_MIN")


def load_vault_overrides(secret_map: dict = None) -> dict:
    """Vault KV v2 에서 시크릿 로드. 반환: {ENV_NAME: value} (플레이스홀더 값 제외)."""
    secret_map = secret_map or VAULT_SECRET_MAP
    try:
        client = get_vault_client()
        if not client.is_authenticated():
            logger.warning("[vault-monitor] 미인증 — env 폴백")
            return {}
        result: dict = {}
        path_cache: dict = {}
        for name, (path, key) in secret_map.items():
            if path not in path_cache:
                try:
                    resp = client.secrets.kv.v2.read_secret_version(path=path)
                    path_cache[path] = resp["data"]["data"]
                except Exception:
                    path_cache[path] = {}
            val = path_cache[path].get(key, "")
            if val not in _PLACEHOLDERS:
                result[name] = val
        return result
    except Exception as exc:
        logger.warning(f"[vault-monitor] Vault 로드 실패, env 폴백: {exc}")
        return {}


def apply_to_environ(overwrite: bool = False) -> int:
    """load_vault_overrides() 결과를 os.environ 에 반영. 반환: 적용 개수."""
    applied = 0
    for name, val in load_vault_overrides().items():
        if overwrite or not os.getenv(name):
            os.environ[name] = val
            applied += 1
    if applied:
        logger.info(f"[vault-monitor] {applied}개 시크릿 Vault에서 로드됨")
    return applied
