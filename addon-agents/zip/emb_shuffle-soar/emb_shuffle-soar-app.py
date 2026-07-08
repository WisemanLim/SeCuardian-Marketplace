import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["shuffle-soar"])

SHUFFLE_URL = os.getenv("SHUFFLE_URL", "http://localhost:3001")
SHUFFLE_API_TOKEN = os.getenv("SHUFFLE_API_TOKEN", "")

_store: deque = deque(maxlen=200)


# --- Pydantic models ---

class WorkflowExecuteRequest(BaseModel):
    workflow_id: str
    payload: dict = Field(default_factory=dict)
    callback_url: str = ""


class ExecutionLog(BaseModel):
    exec_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: str = "pending"  # pending | running | success | failed
    result: dict = Field(default_factory=dict)
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""


# --- Helpers ---

def _shuffle_headers() -> dict:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if SHUFFLE_API_TOKEN:
        headers["Authorization"] = f"Bearer {SHUFFLE_API_TOKEN}"
    return headers


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Endpoints ---

@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    url = f"{SHUFFLE_URL.rstrip('/')}/api/v1/health"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=_shuffle_headers())
            resp.raise_for_status()
            return {"healthy": True, "data": resp.json() if resp.content else {}}
        except httpx.HTTPStatusError as e:
            return {"healthy": False, "status_code": e.response.status_code, "detail": str(e)}
        except httpx.RequestError as e:
            return {"healthy": False, "detail": f"Shuffle unreachable: {e}"}


@router.get("/workflows")
async def list_workflows(current_user=Depends(get_current_user)):
    url = f"{SHUFFLE_URL.rstrip('/')}/api/v1/workflows"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=_shuffle_headers())
            resp.raise_for_status()
            return resp.json() if resp.content else []
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Shuffle unreachable: {e}")


@router.post("/execute", status_code=202)
async def execute_workflow(
    body: WorkflowExecuteRequest,
    current_user=Depends(get_current_user),
):
    log = ExecutionLog(
        workflow_id=body.workflow_id,
        status="running",
        triggered_at=_now_iso(),
    )

    webhook_url = f"{SHUFFLE_URL.rstrip('/')}/api/v1/hooks/webhook_{body.workflow_id}"
    post_body = dict(body.payload)
    if body.callback_url:
        post_body["callback_url"] = body.callback_url

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(webhook_url, json=post_body, headers=_shuffle_headers())
            resp.raise_for_status()
            log.status = "success"
            log.result = resp.json() if resp.content else {}
            log.completed_at = _now_iso()
    except httpx.HTTPStatusError as e:
        log.status = "failed"
        log.result = {"error": str(e), "status_code": e.response.status_code}
        log.completed_at = _now_iso()
        _store.append(log.model_dump())
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        log.status = "failed"
        log.result = {"error": f"Shuffle unreachable: {e}"}
        log.completed_at = _now_iso()
        _store.append(log.model_dump())
        raise HTTPException(status_code=503, detail=f"Shuffle unreachable: {e}")

    _store.append(log.model_dump())
    return {"exec_id": log.exec_id, "status": log.status, "workflow_id": log.workflow_id}


@router.get("/executions")
async def list_executions(
    limit: int = Query(default=50, ge=1, le=200),
    workflow_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    items = list(_store)

    if workflow_id:
        items = [e for e in items if e["workflow_id"] == workflow_id]
    if status:
        items = [e for e in items if e["status"] == status]

    return {"executions": items[-limit:], "total": len(items)}


@router.post("/executions/{exec_id}/callback", status_code=200)
async def execution_callback(exec_id: str, request: Request):
    """Shuffle → SeCuardian result callback. No JWT required."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    incoming_status = body.get("status", "success")
    if incoming_status not in ("success", "failed", "running", "pending"):
        incoming_status = "success"

    updated = False
    for entry in _store:
        if entry["exec_id"] == exec_id:
            entry["status"] = incoming_status
            entry["result"] = body.get("result", body)
            entry["completed_at"] = _now_iso()
            updated = True
            break

    if not updated:
        # exec_id not in store — record it from callback data
        log = ExecutionLog(
            exec_id=exec_id,
            workflow_id=body.get("workflow_id", "unknown"),
            status=incoming_status,
            result=body.get("result", body),
            triggered_at=body.get("triggered_at", _now_iso()),
            completed_at=_now_iso(),
        )
        _store.append(log.model_dump())

    return {"exec_id": exec_id, "acknowledged": True}


@router.get("/config")
async def get_config(current_user=Depends(require_role("admin"))):
    token = SHUFFLE_API_TOKEN
    masked_token = (token[:4] + "****" + token[-4:]) if len(token) >= 8 else ("****" if token else "")
    return {
        "SHUFFLE_URL": SHUFFLE_URL,
        "SHUFFLE_API_TOKEN": masked_token,
    }
