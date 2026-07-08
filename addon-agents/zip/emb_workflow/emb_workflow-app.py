"""워크플로우 에이전트 — ADDON 판 (emb_workflow).

내장 라우터 app/routers/router_workflow.py (F-WF) 의 ADDON 패키징.
로더가 /api/addon/emb_workflow prefix 로 마운트한다.
설정은 내장판(settings.*) 대신 환경변수로 주입한다.
DB·실행 엔진 없이 인메모리 저장소(dict)로 동작 — DAG 워크플로우 CRUD + 실행 기록 관리.
"""
import datetime
import os
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["emb_workflow"])

WORKFLOW_ENABLED = os.getenv("WORKFLOW_ENABLED", "true").lower() == "true"
WORKFLOW_MAX_RUNS = int(os.getenv("WORKFLOW_MAX_RUNS", "200"))

NODE_TYPES = ("llm", "tool", "hitl", "branch", "loop", "delay")

# 인메모리 저장소
_workflows: dict[int, dict] = {}
_runs: deque[dict] = deque(maxlen=WORKFLOW_MAX_RUNS)
_next_id: list[int] = [1]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _next() -> int:
    v = _next_id[0]
    _next_id[0] += 1
    return v


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    definition_json: dict = Field(default_factory=dict)
    trigger_type: str = "manual"
    enabled: bool = True


class RunCreate(BaseModel):
    input: dict = Field(default_factory=dict)
    trigger_source: str = "manual"


class HitlDecision(BaseModel):
    approved: bool
    payload: dict = Field(default_factory=dict)


@router.get("/status")
async def workflow_status(_: dict = Depends(get_current_user)):
    """워크플로우 에이전트 상태."""
    active_runs = sum(1 for r in _runs if r.get("status") not in ("completed", "failed", "cancelled"))
    return {
        "workflow_enabled": WORKFLOW_ENABLED,
        "workflows_count": len(_workflows),
        "runs_stored": len(_runs),
        "active_runs": active_runs,
        "node_types": NODE_TYPES,
        "source": "emb_workflow (in-memory ADDON)",
    }


@router.get("/workflows")
async def list_workflows(_: dict = Depends(get_current_user)):
    """워크플로우 목록 조회."""
    return {"workflows": list(_workflows.values())}


@router.post("/workflows", status_code=201)
async def create_workflow(body: WorkflowCreate, _: dict = Depends(get_current_user)):
    """워크플로우 등록 (인메모리)."""
    nodes = body.definition_json.get("nodes", [])
    for n in nodes:
        if "id" not in n or "type" not in n:
            raise HTTPException(422, "each node needs 'id' and 'type'")
        if n["type"] not in NODE_TYPES:
            raise HTTPException(422, f"node type must be one of {NODE_TYPES}")
    wid = _next()
    wf = {
        "id": wid,
        "name": body.name,
        "description": body.description,
        "definition_json": body.definition_json,
        "trigger_type": body.trigger_type,
        "enabled": body.enabled,
        "created_at": _now(),
    }
    _workflows[wid] = wf
    return wf


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, _: dict = Depends(get_current_user)):
    """워크플로우 단건 조회."""
    wf = _workflows.get(workflow_id)
    if not wf:
        raise HTTPException(404, "workflow not found")
    return wf


@router.post("/workflows/{workflow_id}/run", status_code=201)
async def run_workflow(
    workflow_id: int,
    body: RunCreate,
    _: dict = Depends(get_current_user),
):
    """워크플로우 실행 — ADDON 판은 즉시 'completed' 로 기록 (실 엔진 없음)."""
    wf = _workflows.get(workflow_id)
    if not wf:
        raise HTTPException(404, "workflow not found")
    if not wf.get("enabled"):
        raise HTTPException(409, "workflow disabled")
    rid = _next()
    run = {
        "id": rid,
        "workflow_id": workflow_id,
        "status": "completed",
        "trigger_source": body.trigger_source,
        "input": body.input,
        "started_at": _now(),
        "finished_at": _now(),
    }
    _runs.append(run)
    return run


@router.get("/workflow-runs/{run_id}")
async def get_run(run_id: int, _: dict = Depends(get_current_user)):
    """실행 단건 조회."""
    run = next((r for r in _runs if r["id"] == run_id), None)
    if not run:
        raise HTTPException(404, "run not found")
    return run


@router.post("/workflow-runs/{run_id}/cancel")
async def cancel_run(run_id: int, _: dict = Depends(get_current_user)):
    """실행 취소."""
    run = next((r for r in _runs if r["id"] == run_id), None)
    if not run:
        raise HTTPException(404, "run not found")
    if run["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(409, f"run already terminal (status={run['status']})")
    run["status"] = "cancelled"
    run["cancelled_at"] = _now()
    return run


@router.get("/runs")
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    workflow_id: int = Query(None),
    _: dict = Depends(get_current_user),
):
    """실행 이력 목록."""
    items = list(reversed(list(_runs)))
    if workflow_id is not None:
        items = [r for r in items if r.get("workflow_id") == workflow_id]
    return {"total": len(items), "runs": items[:limit]}
