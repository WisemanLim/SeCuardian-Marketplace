"""Keycloak OIDC 연동 — JWKS 캐시 · Admin API 헬퍼 (app/core/keycloak.py 이식).

설정은 호출 시점에 환경변수에서 읽는다 (settings 미의존).
  KEYCLOAK_URL, KEYCLOAK_MGMT_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID,
  KEYCLOAK_ADMIN_USER, KEYCLOAK_ADMIN_PASSWORD
"""
import os
import time
from typing import Any, Optional

import httpx


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def keycloak_url() -> str:
    return env("KEYCLOAK_URL", "http://localhost:8880").rstrip("/")


def keycloak_mgmt_url() -> str:
    return env("KEYCLOAK_MGMT_URL", "http://localhost:9880").rstrip("/")


def keycloak_realm() -> str:
    return env("KEYCLOAK_REALM", "internal-realm")


# ── JWKS 캐시 (TTL 1h) ────────────────────────────────────────────────────────
_jwks_cache: dict = {}
_jwks_cached_at: float = 0.0
_JWKS_TTL = 3600.0


async def _fetch_jwks(realm: str) -> dict:
    url = f"{keycloak_url()}/realms/{realm}/protocol/openid-connect/certs"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def get_jwks(realm: Optional[str] = None) -> dict:
    """JWKS 가져오기 (TTL 캐시). realm 미지정 시 KEYCLOAK_REALM 사용."""
    global _jwks_cache, _jwks_cached_at
    target = realm or keycloak_realm()
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_cached_at) < _JWKS_TTL:
        return _jwks_cache
    _jwks_cache = await _fetch_jwks(target)
    _jwks_cached_at = now
    return _jwks_cache


# ── Admin API 헬퍼 ────────────────────────────────────────────────────────────
async def get_admin_token(realm: str = "master") -> str:
    """Admin CLI 토큰 취득 (password grant)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{keycloak_url()}/realms/{realm}/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "username": env("KEYCLOAK_ADMIN_USER", "admin"),
                "password": env("KEYCLOAK_ADMIN_PASSWORD", ""),
                "grant_type": "password",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def admin_get(path: str) -> Any:
    """Keycloak Admin REST API GET. path 예: "realms", "realms/x/users?max=50"."""
    token = await get_admin_token()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{keycloak_url()}/admin/{path}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
