"""Vault Secrets 모니터링 Addon — SeCuardian router_vault.py 이식.
# Source: SeCuardian | License: BUSL-1.1 (Vault) | Usage: internal only

마운트: /api/addon/vault-monitor
  GET /status         — secrets_query: Vault 헬스 + 봉인 상태
  GET /config         — secrets_query: 연결 설정 조회 (시크릿 미노출)
  GET /approle/status — secrets_query: AppRole 설정 여부 + 역할 존재 확인
  GET /kv/check       — KV v2 시크릿 경로 접근 가능 여부 (hvac, 값 미노출)
"""
import pathlib
import sys

_d = str(pathlib.Path(__file__).resolve().parent)
sys.path.insert(0, _d) if _d not in sys.path else None

import asyncio  # noqa: E402

import httpx  # noqa: E402
from fastapi import APIRouter, Depends, HTTPException, Query  # noqa: E402

from app.core.deps import get_current_user  # noqa: E402
from vault_monitor_lib.client import env, get_vault_client, vault_addr  # noqa: E402
from vault_monitor_lib.loader import VAULT_SECRET_MAP  # noqa: E402

router = APIRouter(tags=["vault"])


@router.get("/status")
async def vault_status(_: dict = Depends(get_current_user)):
    """Vault 헬스 + 봉인/초기화 상태. Orchestrator intent: secrets_query

    /v1/sys/health 응답 코드: 200=active, 429=standby, 501=not_init, 503=sealed
    """
    result: dict = {
        "vault_addr": vault_addr(),
        "health": None,
        "initialized": None,
        "sealed": None,
        "version": None,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"{vault_addr()}/v1/sys/health")
        data = resp.json()
        if resp.status_code in (200, 429):
            result["health"] = "UP"
        elif resp.status_code == 503:
            result["health"] = "SEALED"
        else:
            result["health"] = "DOWN"
        result["initialized"] = data.get("initialized")
        result["sealed"] = data.get("sealed")
        result["version"] = data.get("version")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Vault 연결 실패: {exc}")
    return result


@router.get("/config")
async def vault_config(_: dict = Depends(get_current_user)):
    """Vault 연결 설정 조회 (시크릿 미포함). Orchestrator intent: secrets_query"""
    return {
        "vault_addr": vault_addr(),
        "token_configured": bool(env("VAULT_TOKEN")),
        "approle_configured": bool(env("VAULT_ROLE_ID") and env("VAULT_SECRET_ID")),
        "env_vars": ["VAULT_ADDR", "VAULT_TOKEN", "VAULT_ROLE_ID", "VAULT_SECRET_ID"],
    }


@router.get("/approle/status")
async def vault_approle_status(_: dict = Depends(get_current_user)):
    """AppRole 인증 엔진 상태 + secuardian 역할 존재 여부. Orchestrator intent: secrets_query"""
    token = env("VAULT_TOKEN")
    role_id, secret_id = env("VAULT_ROLE_ID"), env("VAULT_SECRET_ID")
    result: dict = {
        "vault_addr": vault_addr(),
        "approle_engine_enabled": False,
        "secuardian_role_exists": False,
        "pki_engine_enabled": False,
        "role_id_configured": bool(role_id),
        "secret_id_configured": bool(secret_id),
    }
    if not token and not (role_id and secret_id):
        return result
    headers = {"X-Vault-Token": token}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            auth_resp = await client.get(f"{vault_addr()}/v1/sys/auth", headers=headers)
            mounts_resp = await client.get(f"{vault_addr()}/v1/sys/mounts", headers=headers)
            if auth_resp.is_success:
                result["approle_engine_enabled"] = "approle/" in auth_resp.json()
                if result["approle_engine_enabled"]:
                    role_resp = await client.get(
                        f"{vault_addr()}/v1/auth/approle/role/secuardian", headers=headers
                    )
                    result["secuardian_role_exists"] = role_resp.is_success
        if mounts_resp.is_success:
            result["pki_engine_enabled"] = "pki/" in mounts_resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Vault 연결 실패: {exc}")
    return result


@router.get("/kv/check")
async def vault_kv_check(
    path: str = Query(default="", description="KV v2 경로 (빈 값: 기본 시크릿 맵 전체)"),
    _: dict = Depends(get_current_user),
):
    """KV v2 시크릿 경로 접근 가능 여부 확인 (값은 노출하지 않음, 키 이름만)."""
    if not env("VAULT_TOKEN") and not (env("VAULT_ROLE_ID") and env("VAULT_SECRET_ID")):
        raise HTTPException(status_code=503, detail="VAULT_TOKEN 또는 VAULT_ROLE_ID/VAULT_SECRET_ID 미설정")
    paths = [path] if path else sorted({p for p, _k in VAULT_SECRET_MAP.values()})

    def _check() -> dict:
        client = get_vault_client()
        out: dict = {"authenticated": client.is_authenticated(), "paths": []}
        for p in paths:
            try:
                data = client.secrets.kv.v2.read_secret_version(path=p)["data"]["data"]
                out["paths"].append({"path": p, "accessible": True, "keys": sorted(data.keys())})
            except Exception as exc:
                out["paths"].append({"path": p, "accessible": False, "error": type(exc).__name__})
        return out

    try:
        return await asyncio.to_thread(_check)
    except RuntimeError as exc:  # hvac 미설치
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Vault 연결 실패: {exc}")
