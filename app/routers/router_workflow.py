"""router_workflow (F-WF) — /api/workflows, /api/workflow-runs.

DAG 워크플로우 CRUD + 실행(run)·재개(HITL)·취소·SSE 스트림. SeCuardian Path A 준용.
raw-SQL 아키텍처. tenant 는 JWT 미포함이라 TENANT_DEFAULT_ID 사용. 등록/승인/취소는 admin/supervisor.

참조: SeCuardian-Marketplace-v0 router_workflow 를 async raw-SQL 로 이식.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one
from app.services.workflow_engine import NODE_TYPES, NodeError, execute_run, resume_hitl

router = APIRouter(prefix="/api", tags=["workflow"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    definition_json: dict = Field(default_factory=dict)   # {nodes:[], edges:[]}
    trigger_type: str = "manual"
    trigger_config_json: dict = Field(default_factory=dict)
    enabled: bool = True


class RunCreate(BaseModel):
    input: dict = Field(default_factory=dict)
    trigger_source: str = "manual"


class HitlDecision(BaseModel):
    approved: bool
    payload: dict = Field(default_factory=dict)


def _validate_definition(defn: dict) -> None:
    nodes = defn.get("nodes", [])
    ids: set[str] = set()
    for n in nodes:
        if "id" not in n or "type" not in n:
            raise HTTPException(422, "each node needs 'id' and 'type'")
        if n["type"] not in NODE_TYPES:
            raise HTTPException(422, f"node type must be one of {NODE_TYPES}")
        if n["id"] in ids:
            raise HTTPException(422, f"duplicate node id '{n['id']}'")
        ids.add(n["id"])
    for e in defn.get("edges", []):
        if e.get("source") not in ids or e.get("target") not in ids:
            raise HTTPException(422, f"edge references unknown node: {e}")


def _wf_out(row: dict) -> dict:
    return {**row, "definition_json": json.loads(row.get("definition_json") or "{}"),
            "trigger_config_json": json.loads(row.get("trigger_config_json") or "{}"),
            "enabled": bool(row.get("enabled"))}


async def _get_wf(workflow_id: int, tid: str) -> dict:
    wf = await fetch_one(
        f"SELECT * FROM workflows WHERE id = {_PH} AND tenant_id = {_PH}", (workflow_id, tid)
    )
    if not wf:
        raise HTTPException(404, "workflow not found")
    return wf


async def _get_run(run_id: int, tid: str) -> dict:
    run = await fetch_one(
        f"SELECT * FROM workflow_runs WHERE id = {_PH} AND tenant_id = {_PH}", (run_id, tid)
    )
    if not run:
        raise HTTPException(404, "run not found")
    return run


# ---------- Workflow CRUD ----------
@router.get("/workflows")
async def list_workflows(user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        f"SELECT * FROM workflows WHERE tenant_id = {_PH} ORDER BY id", (_tenant(),)
    )
    return {"workflows": [_wf_out(r) for r in rows]}


@router.post("/workflows", status_code=201)
async def create_workflow(
    body: WorkflowCreate, user: dict = Depends(require_role("admin", "supervisor"))
):
    _validate_definition(body.definition_json)
    tid = _tenant()
    wid = await execute_insert(
        f"INSERT INTO workflows "
        f"(tenant_id, name, description, definition_json, trigger_type, trigger_config_json, enabled, created_by) "
        f"VALUES ({','.join([_PH] * 8)})",
        (tid, body.name, body.description,
         json.dumps(body.definition_json, ensure_ascii=False), body.trigger_type,
         json.dumps(body.trigger_config_json, ensure_ascii=False),
         1 if body.enabled else 0, user.get("username") or user.get("sub") or ""),
    )
    return _wf_out(await _get_wf(wid, tid))


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, user: dict = Depends(get_current_user)):
    return _wf_out(await _get_wf(workflow_id, _tenant()))


# ---------- Run ----------
@router.post("/workflows/{workflow_id}/run", status_code=201)
async def run_workflow(
    workflow_id: int, body: RunCreate, user: dict = Depends(get_current_user)
):
    tid = _tenant()
    wf = await _get_wf(workflow_id, tid)
    if not wf.get("enabled"):
        raise HTTPException(409, "workflow disabled")
    run_id = await execute_insert(
        f"INSERT INTO workflow_runs (tenant_id, workflow_id, status, trigger_source, input_json) "
        f"VALUES ({_PH}, {_PH}, 'pending', {_PH}, {_PH})",
        (tid, workflow_id, body.trigger_source, json.dumps(body.input, ensure_ascii=False)),
    )
    run = await _get_run(run_id, tid)
    try:
        await execute_run(run)
    except NodeError:
        pass  # run.status 는 이미 failed 로 기록됨
    return await _get_run(run_id, tid)


@router.get("/workflow-runs/{run_id}")
async def get_run(run_id: int, user: dict = Depends(get_current_user)):
    return await _get_run(run_id, _tenant())


@router.get("/workflow-runs/{run_id}/nodes")
async def get_run_nodes(run_id: int, user: dict = Depends(get_current_user)):
    await _get_run(run_id, _tenant())
    rows = await fetch_all(
        f"SELECT * FROM workflow_node_runs WHERE run_id = {_PH} ORDER BY id", (run_id,)
    )
    return {"nodes": rows}


@router.post("/workflow-runs/{run_id}/hitl")
async def approve_hitl(
    run_id: int, decision: HitlDecision, user: dict = Depends(require_role("admin", "supervisor"))
):
    tid = _tenant()
    run = await _get_run(run_id, tid)
    if run["status"] != "waiting_hitl":
        raise HTTPException(409, f"run not awaiting hitl (status={run['status']})")
    try:
        await resume_hitl(run, run.get("waiting_node_id") or "", decision.approved, decision.payload)
    except NodeError:
        pass
    return await _get_run(run_id, tid)


@router.post("/workflow-runs/{run_id}/cancel")
async def cancel_run(run_id: int, user: dict = Depends(require_role("admin", "supervisor"))):
    tid = _tenant()
    run = await _get_run(run_id, tid)
    if run["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(409, f"run already terminal (status={run['status']})")
    await execute_write(
        f"UPDATE workflow_runs SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = {_PH}",
        (run_id,),
    )
    return await _get_run(run_id, tid)


@router.get("/workflow-runs/{run_id}/stream")
async def stream_run(run_id: int, user: dict = Depends(get_current_user)):
    """SSE — 노드 실행 상태 + 최종 run 상태를 이벤트로 전송."""
    tid = _tenant()
    run = await _get_run(run_id, tid)
    nodes = await fetch_all(
        f"SELECT node_id, node_type, status, attempts FROM workflow_node_runs WHERE run_id = {_PH} ORDER BY id",
        (run_id,),
    )

    async def _gen():
        for n in nodes:
            yield f"event: node\ndata: {json.dumps(n, ensure_ascii=False)}\n\n"
        final = {"run_id": run["id"], "status": run["status"], "waiting_node_id": run.get("waiting_node_id", "")}
        yield f"event: done\ndata: {json.dumps(final, ensure_ascii=False)}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")
