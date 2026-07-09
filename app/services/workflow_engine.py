"""Flow Engine (F-WF) — 경량 DAG 실행기 + 상태머신 (PRD §7.2.1).

노드 8종: trigger/agent/llm/condition/hitl/transform/notify/http(impl/23).
상태머신: pending→running→waiting_hitl→completed|failed|cancelled.
DAG 의미론: 노드는 모든 입력 엣지가 해소(fire/prune)된 뒤 실행. 분기/조인/병렬 지원.
retry ≤ N(settings.workflow_node_max_retries). HITL 은 승인 대기 후 재개
(완료 노드 출력은 캐시 재사용으로 결정적 재개).

참조: SeCuardian-Marketplace-v0 workflow_engine 을 async raw-SQL 아키텍처로 이식.
impl/23(PRD §7.2.3): agent 노드가 config.path 지정 시 Orchestrator의 _exec_api_call
(in-proc ASGITransport 자기호출)을 재사용해 실제 API를 호출한다. actor(실행 요청자)
Bearer 토큰을 그대로 전달해 권한 상승 없이 동작한다. path 미지정 시 기존 스텁 하위호환.
"""
import json
from collections import defaultdict
from typing import Any

import httpx

from app.core.config import settings
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one

NODE_TYPES = ("trigger", "agent", "llm", "condition", "hitl", "transform", "notify", "http")


class NodeError(Exception):
    pass


class HitlPending(Exception):
    """HITL 승인 대기 — 실행 중단 신호."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(node_id)


# ---------- 템플릿/참조 해석 ----------
def _lookup(path: str, ctx: dict[str, Any]) -> Any:
    cur: Any = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _resolve(value: Any, ctx: dict[str, Any]) -> Any:
    """문자열 "$a.b.c" → context 경로 값. dict/list 재귀."""
    if isinstance(value, str) and value.startswith("$"):
        return _lookup(value[1:], ctx)
    if isinstance(value, dict):
        return {k: _resolve(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, ctx) for v in value]
    return value


def _render(template: str, ctx: dict[str, Any]) -> str:
    """{{a.b}} 토큰을 context 값으로 치환."""
    out = template
    start = 0
    while "{{" in out[start:]:
        i = out.index("{{", start)
        j = out.index("}}", i) if "}}" in out[i:] else -1
        if j == -1:
            break
        path = out[i + 2 : j].strip()
        val = _lookup(path, ctx)
        rep = "" if val is None else (val if isinstance(val, str) else json.dumps(val, ensure_ascii=False))
        out = out[:i] + rep + out[j + 2 :]
        start = i + len(rep)
    return out


def _eval_condition(left: Any, op: str, right: Any) -> bool:
    try:
        if op == "truthy":
            return bool(left)
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == "contains":
            return right in (left or [])
    except TypeError:
        return False
    return False


def _should_fire(edge: dict, node: dict, output: dict) -> bool:
    when = edge.get("when")
    if when is None:
        return True
    if node["type"] == "condition":
        return bool(output.get("result")) == (str(when).lower() == "true")
    return True


# ---------- 노드 실행 ----------
async def _exec_node(node: dict, ctx: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    ntype = node["type"]
    cfg = node.get("config", {}) or {}

    if ntype == "trigger":
        return {"input": ctx.get("_input", {})}

    if ntype == "transform":
        return _resolve(cfg.get("output", {}), ctx)

    if ntype == "llm":
        # 공유 LLM 폴백(Ollama). 미구성/장애 시 degrade 텍스트로 완료(무중단, PRD §7.11.1).
        from app.services.llm_fallback import call_ollama

        prompt = _render(cfg.get("prompt", ""), ctx)
        system = _render(cfg.get("system", ""), ctx)
        try:
            text = await call_ollama([{"role": "user", "content": prompt}], system=system)
            return {"text": text, "provider": "ollama"}
        except Exception as exc:  # noqa: BLE001 — LLM 미구성/장애 → degrade
            return {"text": f"[llm-degraded] {prompt}", "provider": "degraded", "error": str(exc)}

    if ntype == "agent":
        # in-process registry 조회(= tbl_agent_config seam)
        agent_key = _resolve(cfg.get("agent_key"), ctx)
        row = await fetch_one(
            f"SELECT agent_key, is_enabled FROM tbl_agent_config WHERE agent_key = {_PH}",
            (agent_key,),
        ) if agent_key else None
        if not row or not row.get("is_enabled"):
            raise NodeError(f"agent '{agent_key}' not found/enabled")
        path = cfg.get("path")
        if not path:
            # v1 하위호환 스텁 — 컴포넌트 미선택(구 워크플로우 정의) 시 기존 동작 유지.
            return {"agent_key": agent_key, "invoked": True, "input": _resolve(cfg.get("input", {}), ctx)}
        # impl/23(§7.2.3): 컴포넌트 선택 시 Orchestrator._exec_api_call 재사용해 실제 API 호출.
        from app.agents.orchestrator import _exec_api_call

        method = str(cfg.get("method") or "GET").upper()
        body = _resolve(cfg.get("body"), ctx)
        params = _resolve(cfg.get("params"), ctx)
        raw = await _exec_api_call(method, _render(str(path), ctx), body, params, ctx.get("_token"))
        status_code, body_text = _parse_exec_api_call(raw)
        if status_code and status_code >= 400:
            raise NodeError(f"agent api {method} {path} -> HTTP {status_code}: {body_text[:200]}")
        return {"agent_key": agent_key, "invoked": True, "status": status_code, "body": _try_json(body_text)}

    if ntype == "http":
        # impl/23(§7.2.3) — 외부 URL 직접 호출(Dify http-request 대응). admin-trust 경계(§6 SSRF).
        url = _render(str(cfg.get("url") or ""), ctx)
        if not url:
            raise NodeError("http node requires 'url'")
        method = str(cfg.get("method") or "GET").upper()
        headers = _resolve(cfg.get("headers", {}), ctx)
        body = _resolve(cfg.get("body"), ctx)
        params = _resolve(cfg.get("params"), ctx)
        status_code, body_text = await _http_call(method, url, headers, body, params)
        if status_code >= 400:
            raise NodeError(f"http {method} {url} -> HTTP {status_code}: {body_text[:200]}")
        return {"status": status_code, "body": _try_json(body_text)}

    if ntype == "condition":
        left = _resolve(cfg.get("left"), ctx)
        op = cfg.get("op", "truthy")
        right = _resolve(cfg.get("right"), ctx)
        return {"result": _eval_condition(left, op, right)}

    if ntype == "notify":
        return {"notified": True, "message": _render(cfg.get("message", ""), ctx)}

    if ntype == "hitl":
        raise HitlPending(node["id"])

    raise NodeError(f"unknown node type '{ntype}'")


def _parse_exec_api_call(raw: str) -> tuple[int, str]:
    """Orchestrator._exec_api_call 반환("HTTP {code}\\n{body}" | "HTTP ERROR\\n{...}") 파싱."""
    head, _, body = raw.partition("\n")
    if head.startswith("HTTP ") and head[5:].strip().isdigit():
        return int(head[5:].strip()), body
    return 0, body


def _try_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return text


async def _http_call(
    method: str, url: str, headers: dict | None, body: Any, params: dict | None
) -> tuple[int, str]:
    """impl/23 — 외부 URL 실 네트워크 호출(http 노드). 시험에서 monkeypatch 가능하도록 모듈함수로 분리."""
    async with httpx.AsyncClient(timeout=15) as c:
        kwargs: dict = {"headers": headers or {}}
        if body is not None and method not in ("GET", "HEAD"):
            kwargs["json"] = body
        if params:
            kwargs["params"] = params
        resp = await c.request(method, url, **kwargs)
        return resp.status_code, resp.text


# ---------- DB 헬퍼 ----------
async def _set_run(run_id: int, **fields) -> None:
    sets = ", ".join(f"{k} = {_PH}" for k in fields) + ", updated_at = CURRENT_TIMESTAMP"
    await execute_write(
        f"UPDATE workflow_runs SET {sets} WHERE id = {_PH}",
        (*fields.values(), run_id),
    )


async def _node_run_id(run_id: int, tenant_id: str, node_id: str, node_type: str) -> int:
    row = await fetch_one(
        f"SELECT id FROM workflow_node_runs WHERE run_id = {_PH} AND node_id = {_PH}",
        (run_id, node_id),
    )
    if row:
        return row["id"]
    return await execute_insert(
        f"INSERT INTO workflow_node_runs (tenant_id, run_id, node_id, node_type) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH})",
        (tenant_id, run_id, node_id, node_type),
    )


async def _set_node_run(nr_id: int, **fields) -> None:
    sets = ", ".join(f"{k} = {_PH}" for k in fields) + ", updated_at = CURRENT_TIMESTAMP"
    await execute_write(
        f"UPDATE workflow_node_runs SET {sets} WHERE id = {_PH}",
        (*fields.values(), nr_id),
    )


# ---------- 실행기 ----------
async def execute_run(run: dict) -> dict:
    """run 을 실행/재개. 완료 노드 출력은 캐시(재개 결정성). HITL 대기 시 waiting_hitl."""
    run_id = run["id"]
    wf = await fetch_one(f"SELECT definition_json FROM workflows WHERE id = {_PH}", (run["workflow_id"],))
    definition = json.loads((wf or {}).get("definition_json") or "{}")
    nodes = {n["id"]: n for n in definition.get("nodes", [])}
    edges = definition.get("edges", [])

    out_edges: dict[str, list[dict]] = defaultdict(list)
    indeg: dict[str, int] = {nid: 0 for nid in nodes}
    for e in edges:
        out_edges[e["source"]].append(e)
        indeg[e["target"]] = indeg.get(e["target"], 0) + 1

    # 완료 노드 캐시 로드(재개). _token: impl/23 — actor(실행 요청자) Bearer 토큰,
    # run 딕셔너리 한정 런타임 값(DB 미영속, 권한 상승 방지용 actor-scoped 전달).
    ctx: dict[str, Any] = {
        "_input": json.loads(run.get("input_json") or "{}"),
        "_token": run.get("_actor_token"),
    }
    for nr in await fetch_all(
        f"SELECT node_id, status, output_json FROM workflow_node_runs WHERE run_id = {_PH}", (run_id,)
    ):
        if nr["status"] == "completed":
            ctx[nr["node_id"]] = json.loads(nr.get("output_json") or "{}")

    await _set_run(run_id, status="running", waiting_node_id="")

    resolved_in: dict[str, int] = defaultdict(int)
    fired_in: dict[str, int] = defaultdict(int)
    done: set[str] = set(ctx.keys()) - {"_input", "_token"}
    queue: list[str] = [nid for nid in nodes if indeg.get(nid, 0) == 0]
    for nid in list(done):
        _propagate(nid, nodes, out_edges, ctx.get(nid, {}), resolved_in, fired_in, indeg, queue, done)

    while queue:
        nid = queue.pop(0)
        if nid in done or nid not in nodes:
            continue
        node = nodes[nid]

        if nid in ctx:  # 캐시된 완료 노드
            output = ctx[nid]
        else:
            output = await _run_node_with_retry(run, node, ctx)
            if output is None:  # HITL 대기
                await _set_run(run_id, status="waiting_hitl", waiting_node_id=nid)
                run["status"] = "waiting_hitl"
                run["waiting_node_id"] = nid
                return run
            ctx[nid] = output

        done.add(nid)
        _propagate(nid, nodes, out_edges, output, resolved_in, fired_in, indeg, queue, done)
        await _set_run(run_id, output_json=json.dumps({k: v for k, v in ctx.items() if k not in ("_input", "_token")}, ensure_ascii=False))

    await _set_run(run_id, status="completed")
    run["status"] = "completed"
    return run


def _propagate(nid, nodes, out_edges, output, resolved_in, fired_in, indeg, queue, done):
    for e in out_edges.get(nid, []):
        tgt = e["target"]
        resolved_in[tgt] += 1
        if _should_fire(e, nodes[nid], output):
            fired_in[tgt] += 1
        if resolved_in[tgt] >= indeg.get(tgt, 0):
            if fired_in[tgt] > 0:
                queue.append(tgt)
            else:
                done.add(tgt)  # 분기 미선택 → skip, 하위로 prune 전파
                _propagate(tgt, nodes, out_edges, {}, resolved_in, fired_in, indeg, queue, done)


async def _run_node_with_retry(run: dict, node: dict, ctx: dict) -> dict | None:
    """노드 실행 + retry. HITL → None(대기). 실패 소진 → run failed 후 NodeError."""
    run_id, tenant_id = run["id"], run["tenant_id"]
    nr_id = await _node_run_id(run_id, tenant_id, node["id"], node["type"])
    await _set_node_run(
        nr_id, status="running",
        input_json=json.dumps({k: v for k, v in ctx.items() if k not in ("_input", "_token")}, ensure_ascii=False),
    )

    max_attempts = settings.workflow_node_max_retries + 1
    last_err = ""
    for attempt in range(1, max_attempts + 1):
        try:
            output = await _exec_node(node, ctx, tenant_id)
            await _set_node_run(
                nr_id, status="completed", attempts=attempt,
                output_json=json.dumps(output, ensure_ascii=False), error="",
            )
            return output
        except HitlPending:
            await _set_node_run(nr_id, status="waiting_hitl", attempts=attempt)
            return None
        except Exception as exc:  # noqa: BLE001 — retry 대상
            last_err = str(exc)
            await _set_node_run(nr_id, attempts=attempt, error=last_err)

    await _set_node_run(nr_id, status="failed")
    err = f"node {node['id']} failed after {max_attempts} attempts: {last_err}"
    await _set_run(run_id, status="failed", error=err)
    run["status"] = "failed"
    raise NodeError(err)


async def resume_hitl(run: dict, node_id: str, approved: bool, payload: dict) -> dict:
    """HITL 승인/거부 후 재개."""
    run_id = run["id"]
    row = await fetch_one(
        f"SELECT id FROM workflow_node_runs WHERE run_id = {_PH} AND node_id = {_PH}",
        (run_id, node_id),
    )
    if not row:
        raise NodeError(f"hitl node '{node_id}' has no run record")
    if not approved:
        await _set_node_run(row["id"], status="failed", error="rejected by approver")
        await _set_run(run_id, status="failed", error=f"hitl {node_id} rejected")
        run["status"] = "failed"
        return run
    await _set_node_run(
        row["id"], status="completed",
        output_json=json.dumps({"approved": True, **payload}, ensure_ascii=False),
    )
    return await execute_run(run)
