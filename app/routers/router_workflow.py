"""router_workflow (F-WF) — /api/workflows, /api/workflow-runs, /api/workflow/components.

DAG 워크플로우 CRUD + 실행(run)·재개(HITL)·취소·SSE 스트림. SeCuardian Path A 준용.
raw-SQL 아키텍처. tenant 는 JWT 미포함이라 TENANT_DEFAULT_ID 사용. 등록/승인/취소는 admin/supervisor.

impl/23(PRD §7.2.3): /workflow/components — 내장/시스템/Addon 에이전트의 OpenAPI 엔드포인트를
"{에이전트명}-{기능}" 컴포넌트로 실시간 노출(Orchestrator의 기존 OpenAPI 동적 탐지 재사용, 신규
테이블 없음). run/hitl 요청의 Bearer 토큰을 actor_token 으로 워크플로우 엔진에 전달해, agent 노드의
실 API 호출이 실행 요청자 권한 이상으로 동작하지 않도록 한다(actor-scoped, 권한 상승 없음).

impl/26(PRD §7.2.4): /workflows/{id}/trigger/webhook — JWT 없이 X-Webhook-Secret 또는
X-Webhook-Signature(HMAC, impl/29)로 워크플로우를 트리거하는 무인증 수신 엔드포인트.
워크플로우 생성자의 현재 역할을 조회해 스코프된 임시 actor 토큰을 발급, agent/http 노드가
그 권한 이상으로 동작하지 않게 한다(§7.2.3 원칙 계승).

impl/28(PRD §7.2.6): /workflows/import/dify-dsl — Dify DSL Import 어댑터 모드 A. YAML 텍스트를
`app.services.dify_dsl_adapter` 로 SeCMP definition_json 으로 변환해 워크플로우를 생성한다.
매핑 불가 노드는 크래시 대신 transform 플레이스홀더로 대체하고 warnings 로 보고, 가져온
워크플로우는 항상 enabled=false 로 생성해 사람 검토를 강제한다.

impl/29(PRD §7.2.4.1): webhook 보안 강화. 시크릿 저장을 bcrypt(단방향, impl/26)에서
Fernet 대칭암호(재사용 가능한 의존성)로 전환 — 로테이션(/rotate)과 HMAC 서명 검증에
평문 복원이 필요했기 때문. 키는 JWT_SECRET_KEY 파생(신규 env 불요). 워크플로우별 인메모리
고정윈도우 rate limit 도 함께 추가(단일 프로세스 한정, §6 리스크로 명시).

참조: SeCuardian-Marketplace-v0 router_workflow 를 async raw-SQL 로 이식.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one
from app.services.dify_dsl_adapter import DifyDslError, import_dify_dsl
from app.services.workflow_engine import NODE_TYPES, NodeError, execute_run, resume_hitl

router = APIRouter(prefix="/api", tags=["workflow"])
_bearer = HTTPBearer()

# 내장 에이전트 7종(impl/20 BUILTIN_KEYS 와 동일 기준) — 그 외 tbl_agent_config 행은 'system'.
_BUILTIN_KEYS = {"general", "chat", "marketplace", "workflow", "rag", "playground", "guardrails"}


def _tenant() -> str:
    return settings.tenant_default_id or "default"


# ---------- webhook 시크릿 암호화·HMAC·rate limit (impl/29, §7.2.4.1) ----------
def _fernet() -> Fernet:
    """JWT_SECRET_KEY 파생 키(신규 env 불요) — 키 로테이션 시 기존 webhook 시크릿도 무효화됨(§6)."""
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret_key.encode()).digest())
    return Fernet(key)


def _encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def _decrypt_secret(enc: str) -> str | None:
    try:
        return _fernet().decrypt(enc.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def _verify_hmac_signature(secret: str, raw_body: bytes, signature_header: str) -> bool:
    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header[len(prefix):])


_webhook_hits: dict[int, list[float]] = {}  # workflow_id -> 최근 요청 타임스탬프(인메모리, 단일 프로세스)


def _rate_limited(workflow_id: int) -> bool:
    now = time.monotonic()
    hits = [t for t in _webhook_hits.get(workflow_id, []) if now - t < 60]
    hits.append(now)
    _webhook_hits[workflow_id] = hits
    return len(hits) > settings.workflow_webhook_rate_limit_per_min


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
    trigger_config = json.loads(row.get("trigger_config_json") or "{}")
    # impl/26/29 — 시크릿(현재·구버전 필드 모두)은 어떤 응답에도 노출하지 않음
    trigger_config.pop("webhook_secret_hash", None)
    trigger_config.pop("webhook_secret_enc", None)
    return {**row, "definition_json": json.loads(row.get("definition_json") or "{}"),
            "trigger_config_json": trigger_config,
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


def _endpoints_to_components(agent_key: str, agent_name: str, category: str, prefix: str) -> list[dict]:
    """impl/23 — prefix 하위 OpenAPI 엔드포인트를 워크플로우 컴포넌트로 변환.

    Orchestrator._openapi_paths() 를 재사용(신규 스캐너 없음) — 에이전트가 뜨면 즉시 컴포넌트로 노출.
    """
    from app.agents.orchestrator import _openapi_paths

    out: list[dict] = []
    for path, methods in sorted(_openapi_paths().items()):
        if not (path == prefix or path.startswith(prefix + "/")):
            continue
        for method, spec in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            summary = (spec.get("summary") or spec.get("description") or "").strip().split("\n")[0]
            capability = summary or f"{method.upper()} {path.rsplit('/', 1)[-1] or path}"
            out.append({
                "agent_key": agent_key,
                "agent_name": agent_name,
                "category": category,
                "method": method.upper(),
                "path": path,
                "capability_key": capability,
                "label": f"{agent_name}-{capability}",
            })
    return out


@router.get("/workflow/components")
async def list_components(user: dict = Depends(get_current_user)):
    """impl/23(PRD §7.2.3) — 내장/시스템/Addon 에이전트별 API를 컴포넌트 목록으로 노출."""
    from app.agents.orchestrator import _probe_prefix

    components: list[dict] = []
    for r in await fetch_all(
        "SELECT agent_key, agent_name FROM tbl_agent_config WHERE is_enabled = 1 ORDER BY sort_order"
    ):
        key = r["agent_key"]
        prefix = _probe_prefix(key)
        if not prefix or prefix.startswith("/api/addon/"):
            continue
        category = "builtin" if key in _BUILTIN_KEYS else "system"
        components.extend(_endpoints_to_components(key, r["agent_name"], category, prefix))
    for r in await fetch_all(
        "SELECT agent_key, agent_name, api_prefix FROM tbl_addon_agents WHERE is_active = 1"
    ):
        components.extend(_endpoints_to_components(r["agent_key"], r["agent_name"], "addon", r["api_prefix"]))
    return {"components": components}


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
    trigger_config = dict(body.trigger_config_json)
    webhook_secret: str | None = None
    if body.trigger_type == "webhook":
        # impl/26/29(§7.2.4·7.2.4.1) — 평문은 이 응답에만 1회 노출, DB 에는 Fernet 암호문만 저장
        # (로테이션·HMAC 검증에 평문 복원이 필요해 bcrypt 대신 대칭암호 사용).
        webhook_secret = secrets.token_urlsafe(32)
        trigger_config["webhook_secret_enc"] = _encrypt_secret(webhook_secret)
    wid = await execute_insert(
        f"INSERT INTO workflows "
        f"(tenant_id, name, description, definition_json, trigger_type, trigger_config_json, enabled, created_by) "
        f"VALUES ({','.join([_PH] * 8)})",
        (tid, body.name, body.description,
         json.dumps(body.definition_json, ensure_ascii=False), body.trigger_type,
         json.dumps(trigger_config, ensure_ascii=False),
         1 if body.enabled else 0, user.get("username") or user.get("sub") or ""),
    )
    out = _wf_out(await _get_wf(wid, tid))
    if webhook_secret:
        out["webhook_secret"] = webhook_secret
    return out


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, user: dict = Depends(get_current_user)):
    return _wf_out(await _get_wf(workflow_id, _tenant()))


class WorkflowUpdate(BaseModel):
    """impl/30(§7.2.7) enabled 토글 → impl/32(§7.2.8) 부분 편집으로 확장(전 필드 optional, 하위호환)."""
    enabled: bool | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    definition_json: dict | None = None


@router.patch("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: int, body: WorkflowUpdate, user: dict = Depends(require_role("admin", "supervisor"))
):
    """impl/32(§7.2.8) — 부분 편집: enabled/name/description/definition_json.

    definition_json 전달 시 생성과 동일하게 재검증하고 version 을 +1 한다(빌더 저장 경로).
    """
    tid = _tenant()
    await _get_wf(workflow_id, tid)  # 404 if not found
    sets: list[str] = []
    params: list = []
    if body.enabled is not None:
        sets.append(f"enabled = {_PH}")
        params.append(1 if body.enabled else 0)
    if body.name is not None:
        sets.append(f"name = {_PH}")
        params.append(body.name)
    if body.description is not None:
        sets.append(f"description = {_PH}")
        params.append(body.description)
    if body.definition_json is not None:
        _validate_definition(body.definition_json)
        sets.append(f"definition_json = {_PH}")
        params.append(json.dumps(body.definition_json, ensure_ascii=False))
        sets.append("version = version + 1")
    if not sets:
        raise HTTPException(422, "no fields to update")
    await execute_write(
        f"UPDATE workflows SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = {_PH}",
        (*params, workflow_id),
    )
    return _wf_out(await _get_wf(workflow_id, tid))


class DifyDslImportRequest(BaseModel):
    dsl: str = Field(min_length=1)


@router.post("/workflows/import/dify-dsl", status_code=201)
async def import_dify_workflow(
    body: DifyDslImportRequest, user: dict = Depends(require_role("admin", "supervisor"))
):
    """impl/28(§7.2.6) — Dify DSL(YAML) → SeCMP 워크플로우. 항상 enabled=false 로 생성(사람 검토 강제)."""
    try:
        parsed = import_dify_dsl(body.dsl)
    except DifyDslError as exc:
        raise HTTPException(422, f"DSL parse error: {exc}") from exc
    _validate_definition(parsed["definition_json"])
    tid = _tenant()
    wid = await execute_insert(
        f"INSERT INTO workflows "
        f"(tenant_id, name, description, definition_json, trigger_type, trigger_config_json, "
        f"enabled, created_by, dify_dsl_source, dify_dsl_version) "
        f"VALUES ({','.join([_PH] * 10)})",
        (tid, parsed["name"], parsed["description"],
         json.dumps(parsed["definition_json"], ensure_ascii=False), "manual", "{}",
         0, user.get("username") or user.get("sub") or "", body.dsl, parsed["dify_version"]),
    )
    out = _wf_out(await _get_wf(wid, tid))
    out["warnings"] = parsed["warnings"]
    return out


# ---------- Run ----------
@router.post("/workflows/{workflow_id}/run", status_code=201)
async def run_workflow(
    workflow_id: int, body: RunCreate,
    user: dict = Depends(get_current_user),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
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
    run["_actor_token"] = creds.credentials  # impl/23 — agent/http 노드 실호출용(actor-scoped)
    try:
        await execute_run(run)
    except NodeError:
        pass  # run.status 는 이미 failed 로 기록됨
    return await _get_run(run_id, tid)


async def _actor_token_for_creator(created_by: str) -> str | None:
    """impl/26(§7.2.4) — webhook 트리거는 로그인 세션이 없으므로, 워크플로우 생성자의 현재
    역할을 조회해 그 권한으로 스코프된 임시 토큰을 발급한다(DB 미영속, 이 요청 한정).
    생성자를 찾지 못하면 None — agent/http 노드의 실 API 호출만 인증 실패로 실패한다(권한 상승 없음).
    """
    if not created_by:
        return None
    row = await fetch_one(
        f"SELECT user_id, role FROM tbl_users WHERE username = {_PH} OR user_id = {_PH} LIMIT 1",
        (created_by, created_by),
    )
    if not row:
        return None
    return create_access_token({"sub": row["user_id"], "role": row["role"], "username": created_by})


@router.post("/workflows/{workflow_id}/trigger/webhook/rotate", status_code=201)
async def rotate_webhook_secret(
    workflow_id: int, user: dict = Depends(require_role("admin", "supervisor"))
):
    """impl/29(§7.2.4.1) — webhook 시크릿 재발급. 신규 평문은 이 응답에만 1회 노출, 구 시크릿 즉시 무효."""
    tid = _tenant()
    wf = await _get_wf(workflow_id, tid)
    if wf.get("trigger_type") != "webhook":
        raise HTTPException(409, "workflow is not webhook-triggered")
    trigger_config = json.loads(wf.get("trigger_config_json") or "{}")
    new_secret = secrets.token_urlsafe(32)
    trigger_config["webhook_secret_enc"] = _encrypt_secret(new_secret)
    trigger_config.pop("webhook_secret_hash", None)  # impl/26 구필드 정리(있었다면)
    await execute_write(
        f"UPDATE workflows SET trigger_config_json = {_PH}, updated_at = CURRENT_TIMESTAMP WHERE id = {_PH}",
        (json.dumps(trigger_config, ensure_ascii=False), workflow_id),
    )
    out = _wf_out(await _get_wf(workflow_id, tid))
    out["webhook_secret"] = new_secret
    return out


@router.post("/workflows/{workflow_id}/trigger/webhook", status_code=201)
async def trigger_webhook(
    workflow_id: int, request: Request,
    x_webhook_secret: str | None = Header(default=None),
    x_webhook_signature: str | None = Header(default=None),
):
    """impl/26/29(§7.2.4·7.2.4.1) — 무인증 외부 수신 엔드포인트.

    X-Webhook-Secret(직접비교) 또는 X-Webhook-Signature(HMAC-SHA256, 시크릿 미전송) 중
    하나만 유효하면 통과 — 하위호환 유지. 워크플로우별 인메모리 rate limit 적용(단일 프로세스).
    """
    tid = _tenant()
    wf = await _get_wf(workflow_id, tid)
    if wf.get("trigger_type") != "webhook":
        raise HTTPException(404, "workflow is not webhook-triggered")
    if not wf.get("enabled"):
        raise HTTPException(409, "workflow disabled")
    if _rate_limited(workflow_id):
        raise HTTPException(429, "webhook rate limit exceeded")

    trigger_config = json.loads(wf.get("trigger_config_json") or "{}")
    secret_enc = trigger_config.get("webhook_secret_enc")
    secret = _decrypt_secret(secret_enc) if secret_enc else None
    raw_body = await request.body()
    authorized = bool(secret) and (
        (x_webhook_secret is not None and hmac.compare_digest(x_webhook_secret, secret))
        or (x_webhook_signature is not None and _verify_hmac_signature(secret, raw_body, x_webhook_signature))
    )
    if not authorized:
        raise HTTPException(401, "invalid or missing X-Webhook-Secret / X-Webhook-Signature")

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        payload = {}
    run_id = await execute_insert(
        f"INSERT INTO workflow_runs (tenant_id, workflow_id, status, trigger_source, input_json) "
        f"VALUES ({_PH}, {_PH}, 'pending', 'webhook', {_PH})",
        (tid, workflow_id, json.dumps(payload, ensure_ascii=False)),
    )
    run = await _get_run(run_id, tid)
    run["_actor_token"] = await _actor_token_for_creator(wf.get("created_by") or "")
    try:
        await execute_run(run)
    except NodeError:
        pass
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
    run_id: int, decision: HitlDecision,
    user: dict = Depends(require_role("admin", "supervisor")),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
):
    tid = _tenant()
    run = await _get_run(run_id, tid)
    if run["status"] != "waiting_hitl":
        raise HTTPException(409, f"run not awaiting hitl (status={run['status']})")
    run["_actor_token"] = creds.credentials  # impl/23 — 재개 후 agent/http 노드 실호출용
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
