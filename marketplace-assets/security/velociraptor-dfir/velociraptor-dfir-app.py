import os
import uuid
import httpx
from collections import deque
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["velociraptor-dfir"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VELOCIRAPTOR_URL = os.getenv("VELOCIRAPTOR_URL", "https://localhost:8000")
VELOCIRAPTOR_API_KEY = os.getenv("VELOCIRAPTOR_API_KEY", "")
VELOCIRAPTOR_ORG_ID = os.getenv("VELOCIRAPTOR_ORG_ID", "root")

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------
_hunts: dict = {}          # hunt_id -> dict
_results: deque = deque(maxlen=200)   # HuntResult dicts

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class HuntRequest(BaseModel):
    name: str
    description: str = ""
    artifact: str  # e.g. "Linux.Sys.Crontab"
    vql: str = ""
    target_os: str = "linux"
    parameters: dict = Field(default_factory=dict)


class Hunt(BaseModel):
    hunt_id: str
    name: str
    artifact: str
    status: str  # pending / running / completed
    created_at: str
    created_by: str
    result_count: int = 0


class HuntResult(BaseModel):
    hunt_id: str
    client_id: str
    artifact: str
    rows: list[dict]
    collected_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _velo_headers() -> dict:
    return {"X-API-Key": VELOCIRAPTOR_API_KEY, "Content-Type": "application/json"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_status():
    """Proxy to Velociraptor server info endpoint."""
    url = f"{VELOCIRAPTOR_URL}/api/v1/GetServerInfo"
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(url, headers=_velo_headers())
        return {"velociraptor_url": VELOCIRAPTOR_URL, "status_code": resp.status_code, "body": resp.json()}
    except Exception as exc:
        return {"velociraptor_url": VELOCIRAPTOR_URL, "error": str(exc), "reachable": False}


@router.post("/hunts", response_model=Hunt)
async def create_hunt(
    payload: HuntRequest,
    current_user=Depends(require_role("supervisor", "admin")),
):
    """Create a new hunt (supervisor/admin only)."""
    hunt_id = str(uuid.uuid4())
    hunt = {
        "hunt_id": hunt_id,
        "name": payload.name,
        "description": payload.description,
        "artifact": payload.artifact,
        "vql": payload.vql,
        "target_os": payload.target_os,
        "parameters": payload.parameters,
        "status": "pending",
        "created_at": _now_iso(),
        "created_by": getattr(current_user, "email", str(current_user)),
        "result_count": 0,
    }
    _hunts[hunt_id] = hunt

    # Attempt to forward to Velociraptor
    velo_body = {
        "hunt_description": payload.description,
        "artifact_names": [payload.artifact],
        "condition": {"os": {"os": payload.target_os}},
        "spec": {"artifacts": [payload.artifact]},
    }
    if payload.parameters:
        velo_body["spec"]["parameters"] = {"env": [{"key": k, "value": v} for k, v in payload.parameters.items()]}

    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.post(
                f"{VELOCIRAPTOR_URL}/api/v1/CreateHunt",
                headers=_velo_headers(),
                json=velo_body,
            )
        if resp.status_code == 200:
            body = resp.json()
            hunt["status"] = "running"
            hunt["velociraptor_hunt_id"] = body.get("hunt_id", "")
            _hunts[hunt_id] = hunt
    except Exception:
        pass  # store remains pending; Velociraptor unavailable

    return Hunt(**{k: hunt[k] for k in Hunt.model_fields})


@router.get("/hunts", response_model=list[Hunt])
async def list_hunts(current_user=Depends(get_current_user)):
    """List all hunts."""
    return [Hunt(**{k: h[k] for k in Hunt.model_fields}) for h in _hunts.values()]


@router.get("/hunts/{hunt_id}", response_model=Hunt)
async def get_hunt(hunt_id: str, current_user=Depends(get_current_user)):
    """Get single hunt detail."""
    hunt = _hunts.get(hunt_id)
    if not hunt:
        raise HTTPException(status_code=404, detail="Hunt not found")
    return Hunt(**{k: hunt[k] for k in Hunt.model_fields})


@router.post("/hunts/{hunt_id}/results", response_model=HuntResult)
async def receive_hunt_results(hunt_id: str, payload: HuntResult):
    """Receive artifact results pushed from Velociraptor (no JWT required)."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")

    result = payload.model_copy(update={"hunt_id": hunt_id, "collected_at": _now_iso()})
    _results.append(result.model_dump())

    # Update result count on the hunt
    _hunts[hunt_id]["result_count"] = _hunts[hunt_id].get("result_count", 0) + len(payload.rows)
    if _hunts[hunt_id]["status"] != "completed":
        _hunts[hunt_id]["status"] = "running"

    return result


@router.delete("/hunts/{hunt_id}")
async def delete_hunt(
    hunt_id: str,
    current_user=Depends(require_role("supervisor", "admin")),
):
    """Remove a hunt (supervisor/admin only)."""
    if hunt_id not in _hunts:
        raise HTTPException(status_code=404, detail="Hunt not found")
    _hunts.pop(hunt_id)
    return {"deleted": hunt_id}


@router.get("/clients")
async def list_clients(
    query: str = Query(default=".", description="Search query for Velociraptor clients"),
    current_user=Depends(get_current_user),
):
    """Proxy SearchClients to Velociraptor."""
    url = f"{VELOCIRAPTOR_URL}/api/v1/SearchClients"
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(url, headers=_velo_headers(), params={"query": query, "limit": 100})
        return {"status_code": resp.status_code, "body": resp.json()}
    except Exception as exc:
        return {"error": str(exc), "reachable": False}


@router.get("/config")
async def get_config(current_user=Depends(require_role("admin"))):
    """Return current env config (API key masked)."""
    key = VELOCIRAPTOR_API_KEY
    masked_key = (key[:4] + "****" + key[-4:]) if len(key) > 8 else "****"
    return {
        "VELOCIRAPTOR_URL": VELOCIRAPTOR_URL,
        "VELOCIRAPTOR_API_KEY": masked_key,
        "VELOCIRAPTOR_ORG_ID": VELOCIRAPTOR_ORG_ID,
    }
