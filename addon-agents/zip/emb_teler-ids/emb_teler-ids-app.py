import os
import uuid
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["teler-ids"])

TELER_WEBHOOK_ENABLED = os.getenv("TELER_WEBHOOK_ENABLED", "true").lower() == "true"
TELER_ALERTS_MAX = int(os.getenv("TELER_ALERTS_MAX", "500"))

_alerts: deque = deque(maxlen=TELER_ALERTS_MAX)


class TelerAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    message: str
    remote_addr: str
    request_uri: str = ""
    request_method: str = ""
    user_agent: str = ""
    severity: str = "MEDIUM"
    timestamp: str


@router.post("/alerts", status_code=201)
async def receive_alert(payload: TelerAlert):
    if not TELER_WEBHOOK_ENABLED:
        raise HTTPException(status_code=403, detail="Webhook disabled")

    if not payload.alert_id:
        payload = payload.model_copy(update={"alert_id": str(uuid.uuid4())})

    _alerts.append(payload.model_dump())
    return {"alert_id": payload.alert_id, "received": True}


@router.get("/alerts")
async def list_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    category: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    items = list(_alerts)

    if category:
        items = [a for a in items if a["category"] == category]
    if severity:
        items = [a for a in items if a["severity"] == severity]

    return {"alerts": items[-limit:], "total": len(items)}


@router.delete("/alerts")
async def clear_alerts(current_user=Depends(require_role("admin"))):
    count = len(_alerts)
    _alerts.clear()
    return {"cleared": count}


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    return {
        "webhook_enabled": TELER_WEBHOOK_ENABLED,
        "alerts_count": len(_alerts),
        "alerts_max": TELER_ALERTS_MAX,
    }


@router.get("/stats")
async def get_stats(current_user=Depends(get_current_user)):
    category_counts: dict = {}
    severity_counts: dict = {}

    for alert in _alerts:
        cat = alert.get("category", "unknown")
        sev = alert.get("severity", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "by_category": category_counts,
        "by_severity": severity_counts,
        "total": len(_alerts),
    }


@router.get("/config")
async def get_config(current_user=Depends(require_role("admin"))):
    return {
        "TELER_WEBHOOK_ENABLED": TELER_WEBHOOK_ENABLED,
        "TELER_ALERTS_MAX": TELER_ALERTS_MAX,
    }
