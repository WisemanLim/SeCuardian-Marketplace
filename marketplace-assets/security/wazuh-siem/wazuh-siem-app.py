"""Wazuh SIEM 모니터 Addon — SeCuardian router_wazuh.py 이식. License: GPL-2.0 (Wazuh) — API 연동만.

마운트: /api/addon/wazuh-siem
  GET    /status  — Manager API 헬스 + 에이전트 요약 (siem_query)
  GET    /agents  — 에이전트 목록
  GET    /alerts  — 수신 알림 조회
  POST   /alerts  — Wazuh integration webhook 수신 (JWT 불필요, WAZUH_WEBHOOK_ENABLED=true)
  DELETE /alerts  — 저장소 초기화
  GET    /config  — 연결 설정 조회
"""
import datetime
import os
from collections import deque

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_user

router = APIRouter(tags=["wazuh"])

WEBHOOK_PATH = "/api/addon/wazuh-siem/alerts"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(_env(name, str(default))))
    except ValueError:
        return default


def _api_url() -> str:
    return _env("WAZUH_API_URL", "https://localhost:55000").rstrip("/")


def _wazuh_auth() -> httpx.Auth:
    return httpx.BasicAuth(_env("WAZUH_API_USER", "wazuh"), _env("WAZUH_API_PASSWORD", ""))


def _require_credentials() -> None:
    if not _env("WAZUH_API_PASSWORD"):
        raise HTTPException(status_code=503, detail="WAZUH_API_PASSWORD 미설정")


# Wazuh 알림 인메모리 저장소 — maxlen 은 WAZUH_ALERTS_MAX 와 동기화
_alert_store: deque = deque(maxlen=1000)


def _get_alert_store() -> deque:
    global _alert_store
    mx = _env_int("WAZUH_ALERTS_MAX", 1000)
    if _alert_store.maxlen != mx:
        _alert_store = deque(list(_alert_store)[-mx:], maxlen=mx)
    return _alert_store


@router.get("/status")
async def wazuh_status(_: dict = Depends(get_current_user)):
    """Wazuh Manager API 헬스 + 에이전트 요약. Orchestrator intent: siem_query (L5 Detection)"""
    store = _get_alert_store()
    base = {
        "wazuh_api_url": _api_url(),
        "webhook_enabled": _env_bool("WAZUH_WEBHOOK_ENABLED"),
        "alerts_stored": len(store),
    }
    if not _env("WAZUH_API_PASSWORD"):
        return {**base, "status": "UNCONFIGURED", "error": "WAZUH_API_PASSWORD 미설정"}
    try:
        async with httpx.AsyncClient(auth=_wazuh_auth(), verify=False, timeout=10.0) as client:
            resp = await client.get(f"{_api_url()}/")
            agents_resp = await client.get(f"{_api_url()}/agents", params={"limit": 5, "status": "all"})
    except httpx.HTTPError as exc:
        return {**base, "status": "DOWN", "error": str(exc)}
    api_data = resp.json() if resp.is_success else {}
    agents_data = agents_resp.json() if agents_resp.is_success else {}
    return {
        **base,
        "status": "UP" if resp.is_success else "DOWN",
        "http_status": resp.status_code,
        "version": api_data.get("data", {}).get("api_version", "unknown"),
        "agents_total": agents_data.get("data", {}).get("total_affected_items", 0),
        "agents_summary": agents_data.get("data", {}).get("affected_items", [])[:3],
    }


@router.get("/agents")
async def wazuh_agents(
    limit: int = Query(25, ge=1, le=500),
    status: str = Query("all", description="active|disconnected|never_connected|pending|all"),
    _: dict = Depends(get_current_user),
):
    """Wazuh 에이전트 목록 조회."""
    _require_credentials()
    try:
        async with httpx.AsyncClient(auth=_wazuh_auth(), verify=False, timeout=10.0) as client:
            resp = await client.get(f"{_api_url()}/agents", params={"limit": limit, "status": status})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Wazuh API 연결 실패: {exc}")
    if not resp.is_success:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.get("/alerts")
async def wazuh_alerts(
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    """수신된 Wazuh 알림 조회 (WAZUH_WEBHOOK_ENABLED=true 시 POST /alerts 로 수신)."""
    store = _get_alert_store()
    alerts = list(store)[-limit:]
    return {"total": len(store), "returned": len(alerts), "alerts": alerts}


@router.post("/alerts", status_code=202)
async def receive_wazuh_alert(request: Request):
    """Wazuh Manager → webhook 수신. 인증 불필요 — WAZUH_WEBHOOK_ENABLED 플래그로 제어.

    Wazuh Integration 설정: /var/ossec/etc/ossec.conf <integration> 블록에 이 URL 등록.
    단일 객체 또는 배열 모두 수용.
    """
    if not _env_bool("WAZUH_WEBHOOK_ENABLED"):
        raise HTTPException(status_code=403, detail="wazuh webhook disabled — set WAZUH_WEBHOOK_ENABLED=true")
    body = await request.json()
    store = _get_alert_store()
    events = body if isinstance(body, list) else [body]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for event in events:
        if isinstance(event, dict):
            event["_received_at"] = now
            store.append(event)
    return {"accepted": True, "count": len(events), "stored": len(store)}


@router.delete("/alerts")
async def clear_wazuh_alerts(_: dict = Depends(get_current_user)):
    """인메모리 알림 전체 삭제."""
    store = _get_alert_store()
    count = len(store)
    store.clear()
    return {"cleared": count}


@router.get("/config")
async def wazuh_config(_: dict = Depends(get_current_user)):
    """Wazuh 연결 설정 조회 (시크릿 미노출)."""
    return {
        "wazuh_api_url": _api_url(),
        "api_user": _env("WAZUH_API_USER", "wazuh"),
        "api_password_configured": bool(_env("WAZUH_API_PASSWORD")),
        "indexer_url": _env("WAZUH_INDEXER_URL", "https://localhost:9200"),
        "dashboard_url": _env("WAZUH_DASHBOARD_URL", "https://localhost:5601"),
        "webhook_enabled": _env_bool("WAZUH_WEBHOOK_ENABLED"),
        "webhook_path": WEBHOOK_PATH,
        "alerts_max": _env_int("WAZUH_ALERTS_MAX", 1000),
        "env_vars": [
            "WAZUH_API_URL", "WAZUH_API_USER", "WAZUH_API_PASSWORD", "WAZUH_INDEXER_URL",
            "WAZUH_DASHBOARD_URL", "WAZUH_WEBHOOK_ENABLED", "WAZUH_ALERTS_MAX",
        ],
    }
