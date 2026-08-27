"""Keycloak IAM 모니터링 Addon — SeCuardian router_keycloak.py 이식.
# Source: SeCuardian | License: internal | Usage: internal only

마운트: /api/addon/keycloak-monitor
  GET /status  — iam_query: 헬스 + OIDC 디스커버리
  GET /realms  — iam_query: Realm 목록
  GET /users   — iam_query: 사용자 목록
  GET /config  — 연결 설정 조회
"""
import pathlib
import sys

_d = str(pathlib.Path(__file__).resolve().parent)
sys.path.insert(0, _d) if _d not in sys.path else None

import httpx  # noqa: E402
from fastapi import APIRouter, Depends, HTTPException, Query  # noqa: E402

from app.core.deps import get_current_user  # noqa: E402
from keycloak_monitor_lib.client import (  # noqa: E402
    admin_get,
    env,
    keycloak_mgmt_url,
    keycloak_realm,
    keycloak_url,
)

router = APIRouter(tags=["keycloak"])


def _require_admin_password() -> None:
    if not env("KEYCLOAK_ADMIN_PASSWORD"):
        raise HTTPException(status_code=503, detail="KEYCLOAK_ADMIN_PASSWORD 미설정")


@router.get("/status")
async def keycloak_status(_: dict = Depends(get_current_user)):
    """Keycloak 헬스 + OIDC 디스커버리 요약. Orchestrator intent: iam_query"""
    result: dict = {
        "keycloak_url": keycloak_url(),
        "realm": keycloak_realm(),
        "health": None,
        "oidc_issuer": None,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            health_resp = await client.get(f"{keycloak_mgmt_url()}/health/ready")
            oidc_resp = await client.get(
                f"{keycloak_url()}/realms/{keycloak_realm()}/.well-known/openid-configuration"
            )
        if health_resp.is_success:
            result["health"] = health_resp.json()
        if oidc_resp.is_success:
            result["oidc_issuer"] = oidc_resp.json().get("issuer")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Keycloak 연결 실패: {exc}")
    return result


@router.get("/realms")
async def list_realms(_: dict = Depends(get_current_user)):
    """모든 Realm 목록 (Admin API). Orchestrator intent: iam_query"""
    _require_admin_password()
    try:
        realms = await admin_get("realms")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Keycloak 연결 실패: {exc}")
    return [
        {
            "realm": r["realm"],
            "displayName": r.get("displayName", ""),
            "enabled": r.get("enabled", False),
        }
        for r in realms
    ]


@router.get("/users")
async def list_users(
    realm: str = Query(default=None, description="Realm 이름 (기본: KEYCLOAK_REALM)"),
    search: str = Query(default="", description="사용자명·이메일 검색"),
    limit: int = Query(default=50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    """Realm 사용자 목록 (Admin API). Orchestrator intent: iam_query"""
    _require_admin_password()
    target_realm = realm or keycloak_realm()
    qs = f"search={search}&max={limit}" if search else f"max={limit}"
    try:
        users = await admin_get(f"realms/{target_realm}/users?{qs}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Keycloak 연결 실패: {exc}")
    return [
        {
            "id": u["id"],
            "username": u.get("username"),
            "email": u.get("email"),
            "enabled": u.get("enabled"),
            "emailVerified": u.get("emailVerified"),
            "createdTimestamp": u.get("createdTimestamp"),
        }
        for u in users
    ]


@router.get("/config")
async def keycloak_config(_: dict = Depends(get_current_user)):
    """Keycloak 연결 설정 조회 (시크릿 미노출)."""
    return {
        "keycloak_url": keycloak_url(),
        "mgmt_url": keycloak_mgmt_url(),
        "realm": keycloak_realm(),
        "client_id": env("KEYCLOAK_CLIENT_ID", "secuardian"),
        "admin_user": env("KEYCLOAK_ADMIN_USER", "admin"),
        "admin_password_configured": bool(env("KEYCLOAK_ADMIN_PASSWORD")),
        "oidc_discovery": f"{keycloak_url()}/realms/{keycloak_realm()}/.well-known/openid-configuration",
        "env_vars": [
            "KEYCLOAK_URL", "KEYCLOAK_MGMT_URL", "KEYCLOAK_REALM",
            "KEYCLOAK_CLIENT_ID", "KEYCLOAK_ADMIN_USER", "KEYCLOAK_ADMIN_PASSWORD",
        ],
    }
