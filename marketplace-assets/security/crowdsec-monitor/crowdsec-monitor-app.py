"""CrowdSec 위협 탐지 모니터 Addon — SeCuardian router_crowdsec.py 이식. License: MIT (CrowdSec).

마운트: /api/addon/crowdsec-monitor
  GET    /status     — LAPI 헬스 (threat_intel)
  GET    /decisions  — 차단 결정 목록 (Bouncer API Key)
  POST   /alerts     — CrowdSec HTTP notification 수신 (JWT 불필요, CROWDSEC_WEBHOOK_ENABLED=true)
  GET    /alerts, DELETE /alerts, GET /events, GET /config
"""
import datetime
import os
from collections import deque
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_user

router = APIRouter(tags=["crowdsec"])

WEBHOOK_PATH = "/api/addon/crowdsec-monitor/alerts"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(_env(name, str(default))))
    except ValueError:
        return default


def _lapi_url() -> str:
    return _env("CROWDSEC_LAPI_URL", "http://localhost:8082").rstrip("/")


# 인메모리 알림 저장소 — maxlen 은 CROWDSEC_ALERTS_MAX 와 동기화
_alert_store: deque = deque(maxlen=1000)


def _get_alert_store() -> deque:
    global _alert_store
    mx = _env_int("CROWDSEC_ALERTS_MAX", 1000)
    if _alert_store.maxlen != mx:
        _alert_store = deque(list(_alert_store)[-mx:], maxlen=mx)
    return _alert_store


@router.get("/status")
async def crowdsec_status(_: dict = Depends(get_current_user)):
    """CrowdSec LAPI 헬스 확인. Orchestrator intent: threat_intel (L3 Network)"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{_lapi_url()}/")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"CrowdSec LAPI 연결 실패: {exc}")
    return {
        "crowdsec_lapi_url": _lapi_url(),
        # LAPI 는 인증 없는 "/" 에 404 를 반환하는 것이 정상 — 응답을 받았다면 UP
        "status": "UP",
        "http_status": resp.status_code,
        "simulation_mode": _env_bool("CROWDSEC_SIMULATION_MODE", True),
        "bouncer_configured": bool(_env("CROWDSEC_BOUNCER_KEY")),
        "webhook_enabled": _env_bool("CROWDSEC_WEBHOOK_ENABLED"),
    }


@router.get("/decisions")
async def crowdsec_decisions(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=500),
    decision_type: Optional[str] = Query(default=None, description="ban / captcha / allow"),
):
    """CrowdSec 차단 결정 목록 — GET /v1/decisions (Bouncer API Key 필요). Orchestrator intent: threat_intel"""
    key = _env("CROWDSEC_BOUNCER_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="CROWDSEC_BOUNCER_KEY 미설정 — cscli bouncers add 로 발급 후 환경변수 등록",
        )
    params: dict = {"limit": limit}
    if decision_type:
        params["type"] = decision_type
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_lapi_url()}/v1/decisions", headers={"X-Api-Key": key}, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"CrowdSec LAPI 연결 실패: {exc}")
    if resp.status_code == 404:
        return {"decisions": [], "total": 0}
    if not resp.is_success:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json() or []
    return {"decisions": data, "total": len(data)}


@router.post("/alerts", status_code=202)
async def receive_crowdsec_alert(request: Request):
    """CrowdSec HTTP notification plugin → 알림 수신 (내부 전용, JWT 불필요).

    notifications/http.yaml: url = http://host.docker.internal:8200/api/addon/crowdsec-monitor/alerts
    배열 또는 단일 객체 JSON 모두 수용.
    """
    if not _env_bool("CROWDSEC_WEBHOOK_ENABLED"):
        raise HTTPException(
            status_code=403,
            detail="CrowdSec webhook 비활성화됨 — CROWDSEC_WEBHOOK_ENABLED=true 설정 필요",
        )
    body = await request.json()
    alerts = body if isinstance(body, list) else [body]
    store = _get_alert_store()
    received_at = datetime.datetime.utcnow().isoformat() + "Z"
    for alert in alerts:
        if isinstance(alert, dict):
            store.append({**alert, "_received_at": received_at})
    return {"accepted": True, "count": len(alerts), "stored": len(store)}


@router.get("/alerts")
async def list_crowdsec_alerts(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=1000),
    scenario: Optional[str] = Query(default=None, description="시나리오 필터 (부분 일치)"),
):
    """수신된 CrowdSec 알림 조회 — 최신순. Orchestrator intent: threat_intel"""
    store = _get_alert_store()
    alerts = list(store)
    if scenario:
        s = scenario.lower()
        alerts = [a for a in alerts if s in str(a.get("Scenario", a.get("scenario", ""))).lower()]
    alerts = list(reversed(alerts))[:limit]
    return {"total": len(store), "returned": len(alerts), "alerts": alerts}


@router.delete("/alerts", status_code=200)
async def clear_crowdsec_alerts(_: dict = Depends(get_current_user)):
    """알림 저장소 초기화 — 테스트·관리용."""
    store = _get_alert_store()
    count = len(store)
    store.clear()
    return {"cleared": True, "removed": count}


@router.get("/events")
async def crowdsec_events(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """수신 알림 이벤트 목록 (alerts alias)."""
    store = _get_alert_store()
    alerts = list(reversed(list(store)))[:limit]
    return {"total": len(store), "returned": len(alerts), "events": alerts}


@router.get("/config")
async def crowdsec_config(_: dict = Depends(get_current_user)):
    """CrowdSec 연결 설정 조회."""
    return {
        "lapi_url": _lapi_url(),
        "simulation_mode": _env_bool("CROWDSEC_SIMULATION_MODE", True),
        "webhook_enabled": _env_bool("CROWDSEC_WEBHOOK_ENABLED"),
        "webhook_path": WEBHOOK_PATH,
        "alerts_max": _env_int("CROWDSEC_ALERTS_MAX", 1000),
        "bouncer_configured": bool(_env("CROWDSEC_BOUNCER_KEY")),
        "env_vars": [
            "CROWDSEC_LAPI_URL", "CROWDSEC_BOUNCER_KEY", "CROWDSEC_SIMULATION_MODE",
            "CROWDSEC_WEBHOOK_ENABLED", "CROWDSEC_ALERTS_MAX",
        ],
    }
