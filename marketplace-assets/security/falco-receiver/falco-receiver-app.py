"""Falco 런타임 이벤트 수신 Addon — SeCuardian router_falco.py 이식. License: Apache-2.0 (Falco).

마운트: /api/addon/falco-receiver
  POST   /events — Falcosidekick webhook 수신 (JWT 불필요, FALCO_WEBHOOK_ENABLED=true 필요)
  GET    /events — 저장 이벤트 조회 (runtime_alert)
  DELETE /events — 저장소 초기화
  GET    /status, GET /config
"""
import datetime
import os
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.core.deps import get_current_user

router = APIRouter(tags=["falco"])

WEBHOOK_PATH = "/api/addon/falco-receiver/events"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(_env(name, str(default))))
    except ValueError:
        return default


# 인메모리 이벤트 저장소 — maxlen 은 FALCO_EVENTS_MAX 와 동기화
_event_store: deque = deque(maxlen=1000)


def _get_store() -> deque:
    global _event_store
    mx = _env_int("FALCO_EVENTS_MAX", 1000)
    if _event_store.maxlen != mx:
        _event_store = deque(list(_event_store)[-mx:], maxlen=mx)
    return _event_store


class FalcoEvent(BaseModel):
    """Falcosidekick webhook 페이로드 모델."""

    model_config = ConfigDict(extra="allow")

    uuid: Optional[str] = None
    output: str
    priority: str
    rule: str
    time: Optional[str] = None
    output_fields: Optional[dict] = None
    source: Optional[str] = None
    tags: Optional[list] = None
    hostname: Optional[str] = None


@router.post("/events", status_code=202)
async def receive_falco_event(event: FalcoEvent):
    """Falcosidekick → 이벤트 수신 (내부 전용, JWT 불필요). FALCO_WEBHOOK_ENABLED=true 미설정 시 403."""
    if not _env_bool("FALCO_WEBHOOK_ENABLED"):
        raise HTTPException(
            status_code=403,
            detail="Falco webhook 비활성화됨 — FALCO_WEBHOOK_ENABLED=true 설정 필요",
        )
    store = _get_store()
    store.append({**event.model_dump(), "_received_at": datetime.datetime.utcnow().isoformat() + "Z"})
    return {"accepted": True, "stored": len(store)}


@router.get("/events")
async def list_falco_events(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=1000),
    priority: Optional[str] = Query(default=None, description="우선순위 필터 (critical/warning/notice 등, 대소문자 무시)"),
):
    """저장된 Falco 이벤트 조회 — 최신순. Orchestrator intent: runtime_alert"""
    store = _get_store()
    events = list(store)
    if priority:
        p = priority.lower()
        events = [e for e in events if str(e.get("priority", "")).lower() == p]
    events = list(reversed(events))[:limit]
    return {"total": len(store), "returned": len(events), "events": events}


@router.delete("/events", status_code=200)
async def clear_falco_events(_: dict = Depends(get_current_user)):
    """이벤트 저장소 초기화 — 테스트·관리용."""
    store = _get_store()
    count = len(store)
    store.clear()
    return {"cleared": True, "removed": count}


@router.get("/status")
async def falco_status(_: dict = Depends(get_current_user)):
    """Falco 연결 상태 및 이벤트 현황."""
    store = _get_store()
    enabled = _env_bool("FALCO_WEBHOOK_ENABLED")
    return {
        "webhook_enabled": enabled,
        "sidekick_url": _env("FALCO_SIDEKICK_URL", "http://localhost:2801"),
        "events_stored": len(store),
        "events_max": store.maxlen,
        "status": "active" if enabled else "passive",
    }


@router.get("/config")
async def falco_config(_: dict = Depends(get_current_user)):
    """Falco 연결 설정 조회."""
    return {
        "sidekick_url": _env("FALCO_SIDEKICK_URL", "http://localhost:2801"),
        "webhook_enabled": _env_bool("FALCO_WEBHOOK_ENABLED"),
        "events_max": _env_int("FALCO_EVENTS_MAX", 1000),
        "webhook_path": WEBHOOK_PATH,
        "sidekick_config_hint": f"config.webhook.address = http://<host>:8200{WEBHOOK_PATH}",
        "env_vars": ["FALCO_SIDEKICK_URL", "FALCO_WEBHOOK_ENABLED", "FALCO_EVENTS_MAX"],
    }
