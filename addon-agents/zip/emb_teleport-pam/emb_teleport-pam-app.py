import os
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["teleport-pam"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TELEPORT_PROXY_URL = os.getenv("TELEPORT_PROXY_URL", "https://localhost:3080")
TELEPORT_TOKEN = os.getenv("TELEPORT_TOKEN", "")
TELEPORT_CLUSTER = os.getenv("TELEPORT_CLUSTER", "localhost")
TELEPORT_AUDIT_MAX = int(os.getenv("TELEPORT_AUDIT_MAX", "1000"))
TELEPORT_WEBHOOK_ENABLED = os.getenv("TELEPORT_WEBHOOK_ENABLED", "true").lower() == "true"

# ---------------------------------------------------------------------------
# In-memory audit store
# ---------------------------------------------------------------------------
_audit_store: deque = deque(maxlen=TELEPORT_AUDIT_MAX)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class TeleportAuditEvent(BaseModel):
    event_id: str
    event_type: str  # session.start / session.end / user.login / user.create / role.created / access_request.create / ...
    user: str
    server_id: str = ""
    session_id: str = ""
    cluster_name: str = ""
    code: str = ""
    namespace: str = ""
    timestamp: str
    raw: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _auth_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {TELEPORT_TOKEN}"}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_status():
    """Ping the Teleport proxy (no auth required)."""
    url = f"{TELEPORT_PROXY_URL}/v1/webapi/ping"
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return {"ok": True, "proxy_url": TELEPORT_PROXY_URL, "data": resp.json()}
    except httpx.HTTPStatusError as exc:
        return {"ok": False, "proxy_url": TELEPORT_PROXY_URL, "status_code": exc.response.status_code, "detail": str(exc)}
    except Exception as exc:
        return {"ok": False, "proxy_url": TELEPORT_PROXY_URL, "detail": str(exc)}


@router.get("/sessions")
async def list_sessions(
    active: Optional[bool] = Query(None, description="Filter active/inactive sessions"),
    current_user=Depends(get_current_user),
):
    """List Teleport sessions for the configured cluster."""
    url = f"{TELEPORT_PROXY_URL}/v1/webapi/sites/{TELEPORT_CLUSTER}/sessions"
    params = {}
    if active is not None:
        params["active"] = str(active).lower()
    try:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.get(url, headers=_auth_headers(), params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Teleport API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Teleport unreachable: {exc}")


@router.post("/audit/events", status_code=202)
async def receive_audit_event(request: Request):
    """Teleport webhook receiver — no JWT auth, guarded by TELEPORT_WEBHOOK_ENABLED."""
    if not TELEPORT_WEBHOOK_ENABLED:
        raise HTTPException(status_code=403, detail="Webhook receiver is disabled")

    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Normalise fields from Teleport webhook payload
    event = TeleportAuditEvent(
        event_id=body.get("uid", body.get("event_id", f"auto-{datetime.utcnow().isoformat()}")),
        event_type=body.get("event", body.get("event_type", "unknown")),
        user=body.get("user", ""),
        server_id=body.get("server_id", ""),
        session_id=body.get("sid", body.get("session_id", "")),
        cluster_name=body.get("cluster_name", TELEPORT_CLUSTER),
        code=body.get("code", ""),
        namespace=body.get("namespace", ""),
        timestamp=body.get("time", datetime.utcnow().isoformat()),
        raw=body,
    )
    _audit_store.append(event)
    return {"accepted": True, "event_id": event.event_id}


@router.get("/audit/events")
async def list_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    user: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
) -> List[TeleportAuditEvent]:
    """Return stored audit events with optional filters."""
    results = list(_audit_store)

    if event_type:
        results = [e for e in results if e.event_type == event_type]
    if user:
        results = [e for e in results if e.user == user]

    # Most recent first
    results.reverse()
    return results[:limit]


@router.delete("/audit/events")
async def clear_audit_events(current_user=Depends(require_role("admin"))):
    """Clear all stored audit events (admin only)."""
    count = len(_audit_store)
    _audit_store.clear()
    return {"cleared": count}


@router.get("/users")
async def list_users(current_user=Depends(get_current_user)):
    """List Teleport users via the API."""
    url = f"{TELEPORT_PROXY_URL}/v1/webapi/users"
    try:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.get(url, headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Teleport API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Teleport unreachable: {exc}")


@router.get("/config")
async def get_config(current_user=Depends(get_current_user)):
    """Return current agent configuration (token masked)."""
    token_raw = TELEPORT_TOKEN
    masked_token = (token_raw[:4] + "****" + token_raw[-4:]) if len(token_raw) >= 8 else ("****" if token_raw else "")
    return {
        "TELEPORT_PROXY_URL": TELEPORT_PROXY_URL,
        "TELEPORT_TOKEN": masked_token,
        "TELEPORT_CLUSTER": TELEPORT_CLUSTER,
        "TELEPORT_AUDIT_MAX": TELEPORT_AUDIT_MAX,
        "TELEPORT_WEBHOOK_ENABLED": TELEPORT_WEBHOOK_ENABLED,
        "audit_store_current_size": len(_audit_store),
    }
