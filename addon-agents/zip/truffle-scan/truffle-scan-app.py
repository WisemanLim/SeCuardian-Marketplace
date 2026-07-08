import os
from collections import deque
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["truffle-scan"])

# --- In-memory store ---

_max_len = int(os.getenv("TRUFFLE_SCAN_MAX", "200"))
_store: deque = deque(maxlen=_max_len)


# --- Pydantic models ---

class Finding(BaseModel):
    detector_name: str
    file_path: str
    line_start: int
    line_end: int
    raw_secret_masked: str
    verified: bool
    severity: str = "HIGH"


class TruffleHogResult(BaseModel):
    scan_id: str
    repo: str
    branch: str = ""
    commit: str = ""
    findings: List[Finding]
    total_findings: int
    verified_findings: int
    started_at: str
    finished_at: str


# --- Endpoints ---

@router.post("/scan-results", status_code=201)
def receive_scan_result(result: TruffleHogResult):
    """Receive a TruffleHog scan result. No JWT required. Guarded by TRUFFLE_WEBHOOK_ENABLED."""
    enabled = os.getenv("TRUFFLE_WEBHOOK_ENABLED", "true").lower()
    if enabled not in ("1", "true", "yes"):
        raise HTTPException(status_code=403, detail="Webhook receiver is disabled")

    _store.append(result)
    return {"status": "accepted", "scan_id": result.scan_id}


@router.get("/scan-results")
def list_scan_results(
    limit: int = Query(default=50, ge=1, le=_max_len),
    verified_only: bool = Query(default=False),
    _user=Depends(get_current_user),
):
    """List stored scan results, newest first."""
    results = list(_store)
    results.reverse()

    if verified_only:
        results = [r for r in results if r.verified_findings > 0]

    return results[:limit]


@router.get("/scan-results/{scan_id}")
def get_scan_result(scan_id: str, _user=Depends(get_current_user)):
    """Retrieve a single scan result with its full findings list."""
    for result in _store:
        if result.scan_id == scan_id:
            return result
    raise HTTPException(status_code=404, detail=f"Scan result '{scan_id}' not found")


@router.delete("/scan-results")
def clear_scan_results(_user=Depends(require_role("admin"))):
    """Clear all stored scan results. Admin only."""
    _store.clear()
    return {"status": "cleared"}


@router.get("/status")
def get_status(_user=Depends(get_current_user)):
    """Return stats: stored count and last scan summary."""
    if not _store:
        return {"stored_count": 0, "last_scan": None}

    last: TruffleHogResult = list(_store)[-1]
    return {
        "stored_count": len(_store),
        "max_capacity": _max_len,
        "last_scan": {
            "scan_id": last.scan_id,
            "repo": last.repo,
            "branch": last.branch,
            "commit": last.commit,
            "total_findings": last.total_findings,
            "verified_findings": last.verified_findings,
            "finished_at": last.finished_at,
        },
    }


@router.get("/config")
def get_config(_user=Depends(get_current_user)):
    """Return effective env-var configuration (no secrets exposed)."""
    return {
        "TRUFFLE_WEBHOOK_ENABLED": os.getenv("TRUFFLE_WEBHOOK_ENABLED", "true"),
        "TRUFFLE_SCAN_MAX": os.getenv("TRUFFLE_SCAN_MAX", "200"),
        "store_current_size": len(_store),
        "store_max_size": _max_len,
    }
