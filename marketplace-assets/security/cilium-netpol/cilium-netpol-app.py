import os
from collections import deque
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["cilium-netpol"])

CILIUM_AGENT_URL = os.getenv("CILIUM_AGENT_URL", "http://localhost:9090")
CILIUM_HUBBLE_URL = os.getenv("CILIUM_HUBBLE_URL", "http://localhost:4245")
CILIUM_WEBHOOK_ENABLED = os.getenv("CILIUM_WEBHOOK_ENABLED", "false").lower() == "true"
CILIUM_HUBBLE_MAX = int(os.getenv("CILIUM_HUBBLE_MAX", "500"))

_flow_store: deque = deque(maxlen=CILIUM_HUBBLE_MAX)


class HubbleFlow(BaseModel):
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    verdict: str  # FORWARDED / DROPPED / REDIRECTED
    reason: str
    namespace: str
    timestamp: str


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    url = f"{CILIUM_AGENT_URL}/healthz"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            return {"reachable": True, "status_code": resp.status_code, "body": resp.text}
    except Exception as exc:
        return {"reachable": False, "cilium_agent_url": CILIUM_AGENT_URL, "detail": str(exc)}


@router.get("/network-policies")
async def get_network_policies(current_user=Depends(get_current_user)):
    url = f"{CILIUM_AGENT_URL}/v1/policy"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch policies: {exc}")


@router.post("/hubble/flows", status_code=202)
async def receive_hubble_flows(request: Request):
    if not CILIUM_WEBHOOK_ENABLED:
        raise HTTPException(status_code=403, detail="Hubble webhook ingestion is disabled")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    flows = body if isinstance(body, list) else [body]
    accepted = 0
    for item in flows:
        try:
            flow = HubbleFlow(**item)
            _flow_store.append(flow)
            accepted += 1
        except Exception:
            pass
    return {"accepted": accepted, "store_size": len(_flow_store)}


@router.get("/hubble/flows", response_model=List[HubbleFlow])
async def list_hubble_flows(
    limit: Optional[int] = Query(default=100, ge=1, le=500),
    verdict: Optional[str] = Query(default=None),
    namespace: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    flows = list(_flow_store)
    if verdict:
        flows = [f for f in flows if f.verdict.upper() == verdict.upper()]
    if namespace:
        flows = [f for f in flows if f.namespace == namespace]
    return flows[-limit:]


@router.delete("/hubble/flows")
async def clear_hubble_flows(current_user=Depends(require_role("admin"))):
    count = len(_flow_store)
    _flow_store.clear()
    return {"cleared": count}


@router.get("/stats")
async def get_stats(current_user=Depends(get_current_user)):
    forwarded = sum(1 for f in _flow_store if f.verdict == "FORWARDED")
    dropped = sum(1 for f in _flow_store if f.verdict == "DROPPED")
    redirected = sum(1 for f in _flow_store if f.verdict == "REDIRECTED")
    return {
        "total": len(_flow_store),
        "forwarded": forwarded,
        "dropped": dropped,
        "redirected": redirected,
    }


@router.get("/config")
async def get_config(current_user=Depends(require_role("admin"))):
    return {
        "CILIUM_AGENT_URL": CILIUM_AGENT_URL,
        "CILIUM_HUBBLE_URL": CILIUM_HUBBLE_URL,
        "CILIUM_WEBHOOK_ENABLED": CILIUM_WEBHOOK_ENABLED,
        "CILIUM_HUBBLE_MAX": CILIUM_HUBBLE_MAX,
    }
