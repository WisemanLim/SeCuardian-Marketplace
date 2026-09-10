"""logto-monitor — Logto IAM 모니터링 Addon (SeCuardian router_logto.py 이식).
# Source: SeCuardian | License: internal | Usage: internal only

마운트: /api/addon/logto-monitor
  GET /status  — iam_query: 헬스 + OIDC 디스커버리
  GET /config  — 연결 설정 조회(시크릿 제외)

이식 노트: marketplace settings 비의존 — 설정은 env(LOGTO_ENDPOINT/LOGTO_ADMIN_URL)로 읽는다.
⚠️ from __future__ import annotations 금지 (동적 로더 pydantic 이슈)
"""
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user

router = APIRouter(tags=["logto-monitor"])


def _endpoint() -> str:
    return os.getenv("LOGTO_ENDPOINT", "http://localhost:3801").rstrip("/")


def _admin_url() -> str:
    return os.getenv("LOGTO_ADMIN_URL", "http://localhost:3802").rstrip("/")


@router.get("/status")
async def logto_status(_: dict = Depends(get_current_user)):
    """Logto 헬스 + OIDC 디스커버리 요약. Orchestrator intent: iam_query"""
    result: dict = {
        "logto_endpoint": _endpoint(),
        "logto_admin_url": _admin_url(),
        "health": None,
        "oidc_issuer": None,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            oidc_resp = await client.get(f"{_endpoint()}/oidc/.well-known/openid-configuration")
        if oidc_resp.is_success:
            config = oidc_resp.json()
            result["health"] = "UP"
            result["oidc_issuer"] = config.get("issuer")
            result["jwks_uri"] = config.get("jwks_uri")
            result["token_endpoint"] = config.get("token_endpoint")
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail=f"Logto 연결 실패: {exc}")
    return result


@router.get("/config")
async def logto_config(_: dict = Depends(get_current_user)):
    """연결 설정 참조 (시크릿 제외)."""
    return {
        "logto_endpoint": _endpoint(),
        "logto_admin_url": _admin_url(),
        "required_env": ["LOGTO_ENDPOINT", "LOGTO_ADMIN_URL"],
        "note": "대안 IdP — Keycloak 병행 평가",
    }
