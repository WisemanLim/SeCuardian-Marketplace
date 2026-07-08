"""neosync-dlp — Neosync DLP pipeline monitor (service type).

마운트 경로: /api/addon/neosync-dlp/...
엔드포인트:
  GET  /status               Neosync API 헬스 체크
  GET  /jobs                 Job 목록 조회
  POST /jobs/run             Job 실행 트리거 (supervisor/admin)
  GET  /jobs/{job_id}/runs   Job 실행 이력 조회
  POST /run-results          Neosync → SeCuardian 결과 푸시 (no JWT)
  GET  /run-results          저장된 결과 목록 조회
  GET  /config               환경변수 설정 조회 (API key masked)
"""
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["neosync-dlp"])

# ─── 환경변수 ────────────────────────────────────────────────────────────────

NEOSYNC_API_URL = os.getenv("NEOSYNC_API_URL", "http://localhost:8080")
NEOSYNC_API_KEY = os.getenv("NEOSYNC_API_KEY", "")
NEOSYNC_ACCOUNT_ID = os.getenv("NEOSYNC_ACCOUNT_ID", "")

# ─── In-memory run result store ──────────────────────────────────────────────

_run_results: deque = deque(maxlen=100)


# ─── Pydantic models ─────────────────────────────────────────────────────────

class JobRunRequest(BaseModel):
    job_id: str
    sync_options: dict[str, Any] = {}


class RunResult(BaseModel):
    run_id: str
    job_id: str
    status: str
    rows_processed: int = 0
    errors: int = 0
    started_at: str
    completed_at: str = ""
    error_message: str = ""


# ─── 공통 HTTP 헬퍼 ─────────────────────────────────────────────────────────

def _neosync_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if NEOSYNC_API_KEY:
        headers["Authorization"] = f"Bearer {NEOSYNC_API_KEY}"
    if NEOSYNC_ACCOUNT_ID:
        headers["X-Neosync-Account-Id"] = NEOSYNC_ACCOUNT_ID
    return headers


async def _neosync_get(path: str, extra_headers: dict | None = None) -> Any:
    headers = _neosync_headers()
    if extra_headers:
        headers.update(extra_headers)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{NEOSYNC_API_URL}{path}", headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


async def _neosync_post(path: str, body: dict) -> Any:
    headers = _neosync_headers()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{NEOSYNC_API_URL}{path}", headers=headers, json=body
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ─── 엔드포인트 ─────────────────────────────────────────────────────────────

@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    """Neosync API 헬스 체크 — job 개수를 반환합니다."""
    try:
        data = await _neosync_get("/api/v1/jobs")
    except HTTPException as exc:
        return {"healthy": False, "error": exc.detail, "job_count": 0}
    except Exception as exc:
        return {"healthy": False, "error": str(exc), "job_count": 0}

    jobs = data.get("jobs", [])
    return {"healthy": True, "job_count": len(jobs)}


@router.get("/jobs")
async def list_jobs(user: dict = Depends(get_current_user)):
    """Neosync Job 목록을 조회합니다."""
    data = await _neosync_get("/api/v1/jobs")
    return data


@router.post("/jobs/run", status_code=202)
async def run_job(
    body: JobRunRequest,
    user: dict = Depends(require_role(["supervisor", "admin"])),
):
    """Job 실행을 트리거합니다 (supervisor/admin 전용)."""
    data = await _neosync_post(
        f"/api/v1/jobs/{body.job_id}/run",
        body.sync_options,
    )
    return data


@router.get("/jobs/{job_id}/runs")
async def get_job_runs(job_id: str, user: dict = Depends(get_current_user)):
    """특정 Job의 실행 이력을 조회합니다."""
    data = await _neosync_get(f"/api/v1/jobs/{job_id}/runs")
    return data


@router.post("/run-results", status_code=201)
async def push_run_result(body: RunResult, request: Request):
    """Neosync가 SeCuardian으로 결과를 푸시하는 엔드포인트 (JWT 인증 없음)."""
    _run_results.append(body.model_dump())
    return {"accepted": True, "run_id": body.run_id}


@router.get("/run-results")
async def list_run_results(
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """저장된 실행 결과 목록을 반환합니다 (최신순)."""
    results = list(_run_results)
    results.reverse()
    return {"results": results[:limit], "total": len(results)}


@router.get("/config")
async def get_config(user: dict = Depends(get_current_user)):
    """현재 환경변수 설정을 반환합니다 (API key는 마스킹)."""
    masked_key = ""
    if NEOSYNC_API_KEY:
        visible = NEOSYNC_API_KEY[:4] if len(NEOSYNC_API_KEY) >= 4 else NEOSYNC_API_KEY
        masked_key = visible + "*" * (len(NEOSYNC_API_KEY) - len(visible))

    return {
        "NEOSYNC_API_URL": NEOSYNC_API_URL,
        "NEOSYNC_API_KEY": masked_key,
        "NEOSYNC_ACCOUNT_ID": NEOSYNC_ACCOUNT_ID,
    }
