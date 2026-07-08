import hashlib
import hmac
import os
import uuid
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["behavior-noti"])

_ENABLED = os.getenv("BEHAVIOR_NOTI_ENABLED", "true").lower() == "true"
_WEBHOOK_SECRET = os.getenv("BEHAVIOR_NOTI_WEBHOOK_SECRET", "")
_EVENTS_MAX = int(os.getenv("BEHAVIOR_NOTI_EVENTS_MAX", "500"))

_events: deque = deque(maxlen=_EVENTS_MAX)

VALID_BEHAVIOR_TYPES = {"file_access", "net_conn", "priv_esc", "lateral_move", "data_exfil", "anomaly"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


class BehaviorEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    host: str
    process_name: str = ""
    pid: int = 0
    behavior_type: str
    severity: str
    description: str
    raw_data: dict = Field(default_factory=dict)
    timestamp: str


async def _verify_hmac(request: Request) -> None:
    if not _WEBHOOK_SECRET:
        return
    signature = request.headers.get("X-BehaviorNoti-Signature", "")
    body = await request.body()
    expected = "sha256=" + hmac.new(
        _WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")


@router.post("/events", status_code=201)
async def receive_event(request: Request, payload: BehaviorEvent):
    if not _ENABLED:
        raise HTTPException(status_code=403, detail="Behavior notification receiver disabled")

    await _verify_hmac(request)

    if not payload.event_id:
        payload = payload.model_copy(update={"event_id": str(uuid.uuid4())})

    _events.append(payload.model_dump())
    return {"event_id": payload.event_id, "received": True}


@router.get("/events")
async def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    severity: Optional[str] = Query(default=None),
    behavior_type: Optional[str] = Query(default=None),
    host: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    items = list(_events)

    if severity:
        items = [e for e in items if e["severity"] == severity]
    if behavior_type:
        items = [e for e in items if e["behavior_type"] == behavior_type]
    if host:
        items = [e for e in items if e["host"] == host]

    return {"events": items[-limit:], "total": len(items)}


@router.delete("/events")
async def clear_events(current_user=Depends(require_role("admin"))):
    count = len(_events)
    _events.clear()
    return {"cleared": count}


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    last_event = None
    if _events:
        last = _events[-1]
        last_event = {
            "event_id": last["event_id"],
            "host": last["host"],
            "behavior_type": last["behavior_type"],
            "severity": last["severity"],
            "timestamp": last["timestamp"],
        }
    return {
        "enabled": _ENABLED,
        "event_count": len(_events),
        "last_event": last_event,
    }


@router.get("/stats")
async def get_stats(current_user=Depends(get_current_user)):
    severity_counts: dict = {}
    behavior_type_counts: dict = {}
    host_counts: dict = {}

    for event in _events:
        sev = event.get("severity", "unknown")
        btype = event.get("behavior_type", "unknown")
        host = event.get("host", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        behavior_type_counts[btype] = behavior_type_counts.get(btype, 0) + 1
        host_counts[host] = host_counts.get(host, 0) + 1

    return {
        "by_severity": severity_counts,
        "by_behavior_type": behavior_type_counts,
        "by_host": host_counts,
        "total": len(_events),
    }


@router.get("/config")
async def get_config(current_user=Depends(require_role("admin"))):
    return {
        "BEHAVIOR_NOTI_ENABLED": _ENABLED,
        "BEHAVIOR_NOTI_WEBHOOK_SECRET": "***" if _WEBHOOK_SECRET else "",
        "BEHAVIOR_NOTI_EVENTS_MAX": _EVENTS_MAX,
    }
