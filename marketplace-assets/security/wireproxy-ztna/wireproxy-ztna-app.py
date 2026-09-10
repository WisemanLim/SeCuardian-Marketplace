"""wireproxy-ztna — WireProxy ZTNA 모니터 Addon (SeCuardian router_wireproxy.py 이식).
# Source: SeCuardian | License: ISC | Usage: internal only

마운트: /api/addon/wireproxy-ztna
  GET /status  — ztna: SOCKS5 프록시 상태(경유 외부 IP)
  GET /config  — 설정 참조(시크릿 제외)

이식 노트: settings 비의존 — WIREPROXY_SOCKS5_HOST/PORT env. ⚠️ from __future__ import annotations 금지.
"""
import os

import httpx
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(tags=["wireproxy-ztna"])


def _host() -> str:
    return os.getenv("WIREPROXY_SOCKS5_HOST", "127.0.0.1")


def _port() -> int:
    try:
        return int(os.getenv("WIREPROXY_SOCKS5_PORT", "25344"))
    except ValueError:
        return 25344


@router.get("/status")
async def wireproxy_status(_: dict = Depends(get_current_user)):
    """WireProxy SOCKS5 프록시 상태. Orchestrator intent: ztna (L3 Network)"""
    socks = f"{_host()}:{_port()}"
    try:
        async with httpx.AsyncClient(proxies={"all://": f"socks5://{socks}"}, timeout=5.0) as client:
            resp = await client.get("http://ifconfig.me/ip")
        return {
            "wireproxy_socks5": socks,
            "status": "UP",
            "proxy_ip": resp.text.strip(),
            "note": "프록시 경유 외부 IP — 내부 IP와 다르면 정상",
        }
    except Exception:  # noqa: BLE001
        return {
            "wireproxy_socks5": socks,
            "status": "UNREACHABLE",
            "note": "WireProxy 미기동 — make wireproxy-up 실행 (또는 httpx[socks] 미설치)",
        }


@router.get("/config")
async def wireproxy_config(_: dict = Depends(get_current_user)):
    """WireProxy 설정 참조 (시크릿 제외)."""
    return {
        "license": "ISC",
        "socks5": f"{_host()}:{_port()}",
        "secrets_required": ["WIREGUARD_PRIVATE_KEY", "WIREGUARD_SERVER_PUBLIC_KEY", "WIREGUARD_SERVER_ENDPOINT"],
        "keycloak_prereq": "Keycloak OAuth2 Device Flow 인증 선행 (E01)",
    }
