"""Harbor 레지스트리 모니터링 Addon — SeCuardian router_harbor.py 이식. License: Apache-2.0 (Harbor).

마운트: /api/addon/harbor-scanner
  GET /status       — Harbor Health API
  GET /config       — 연결 설정 조회 (시크릿 미노출)
  GET /scan-policy  — 프로젝트 Trivy 스캔 정책 + Cosign 상태
"""
import asyncio
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user

router = APIRouter(tags=["harbor"])


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _harbor_url() -> str:
    return _env("HARBOR_URL", "http://localhost:8083").rstrip("/")


def _project() -> str:
    return _env("HARBOR_PROJECT", "secuardian")


@router.get("/status")
async def harbor_status(_: dict = Depends(get_current_user)):
    """Harbor Health API — GET /api/v2.0/health."""
    try:
        async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
            resp = await client.get(f"{_harbor_url()}/api/v2.0/health")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Harbor 연결 실패: {exc}")
    if resp.is_success:
        data = resp.json()
        return {
            "harbor_url": _harbor_url(),
            "status": data.get("status", "unknown"),
            "components": data.get("components", []),
        }
    return {"harbor_url": _harbor_url(), "status": "DOWN", "components": [], "http_status": resp.status_code}


@router.get("/config")
async def harbor_config(_: dict = Depends(get_current_user)):
    """Harbor 연결 설정 조회 (시크릿 미노출)."""
    return {
        "harbor_url": _harbor_url(),
        "harbor_project": _project(),
        "admin_user": _env("HARBOR_ADMIN_USER", "admin"),
        "admin_configured": bool(_env("HARBOR_ADMIN_PASSWORD")),
        "robot_configured": bool(_env("HARBOR_ROBOT_SECRET")),
        "cosign_configured": bool(_env("COSIGN_PUB_KEY")),
        "env_vars": [
            "HARBOR_URL", "HARBOR_PROJECT", "HARBOR_ADMIN_USER", "HARBOR_ADMIN_PASSWORD",
            "HARBOR_ROBOT_NAME", "HARBOR_ROBOT_SECRET", "COSIGN_PUB_KEY",
        ],
    }


@router.get("/scan-policy")
async def harbor_scan_policy(_: dict = Depends(get_current_user)):
    """프로젝트 Trivy 스캔 정책 + Cosign 상태 조회."""
    if not _env("HARBOR_ADMIN_PASSWORD"):
        return {"project": _project(), "configured": False, "detail": "HARBOR_ADMIN_PASSWORD 미설정"}
    auth = (_env("HARBOR_ADMIN_USER", "admin"), _env("HARBOR_ADMIN_PASSWORD"))
    try:
        async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
            proj_resp, scanners_resp = await asyncio.gather(
                client.get(f"{_harbor_url()}/api/v2.0/projects/{_project()}", auth=auth),
                client.get(f"{_harbor_url()}/api/v2.0/scanners", auth=auth),
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Harbor 연결 실패: {exc}")

    meta: dict = proj_resp.json().get("metadata", {}) if proj_resp.is_success else {}
    scanners: list = scanners_resp.json() if scanners_resp.is_success else []
    trivy = next((s for s in scanners if "trivy" in str(s.get("name", "")).lower()), None)

    return {
        "project": _project(),
        "configured": True,
        "auto_scan": meta.get("auto_scan") == "true",
        "prevent_vul": meta.get("prevent_vul") == "true",
        "severity_threshold": meta.get("severity", "none"),
        "trivy_registered": trivy is not None,
        "trivy_name": trivy["name"] if trivy else None,
        "cosign_configured": bool(_env("COSIGN_PUB_KEY")),
    }
