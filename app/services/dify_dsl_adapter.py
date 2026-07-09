"""Dify DSL Import 어댑터 — 모드 A(design-time) (PRD §7.2.2·§7.2.6, impl/28).

Dify Studio 에서 export 한 DSL YAML 을 SeCMP 내부 definition_json(nodes/edges) 으로 변환한다.
실행은 SeCMP 자체 DAG 엔진(app/services/workflow_engine.py)이 그대로 수행 — 이 모듈은 파싱·매핑만.

가정/전제: Dify DSL 은 버전마다 필드가 달라질 수 있어(§7.2.2 "가정: 안정적 공개 API 로 명시
문서화되지 않은 릴리즈 존재") **관용적(lenient) 파싱**을 채택한다. 알 수 없는 필드는 무시하고,
매핑 불가 노드 타입은 크래시 대신 `transform` 플레이스홀더 + warnings 로 명시한다(§3 code 노드
유보 원칙 유지 — 실행 가능한 코드를 자동 이식하지 않는다).

노드 매핑표(§7.2.2, 2026-07-08 Dify 공식문서 실측 근거):
  start → trigger · llm → llm · if-else → condition · knowledge-retrieval → agent(rag)
  http-request → http · tool → agent(미지정) · answer/end → notify · code/미인식 → transform(경고)
"""
import yaml

NODE_TYPE_MAP = {
    "start": "trigger",
    "llm": "llm",
    "if-else": "condition",
    "knowledge-retrieval": "agent",
    "http-request": "http",
    "tool": "agent",
    "answer": "notify",
    "end": "notify",
}
UNSUPPORTED_TYPES = {"code"}

_OP_MAP = {
    "contains": "contains",
    "is": "==",
    "equals": "==",
    "not is": "!=",
    "not equals": "!=",
    "empty": "truthy",
    "not empty": "truthy",
    ">": ">",
    "<": "<",
}


class DifyDslError(Exception):
    pass


def _extract_llm_prompt(data: dict) -> tuple[str, str]:
    """prompt_template(chat 모드, role/text 리스트) 또는 prompt(completion 모드) 최선노력 추출."""
    system, prompt = "", ""
    tmpl = data.get("prompt_template")
    if isinstance(tmpl, list):
        for msg in tmpl:
            if not isinstance(msg, dict):
                continue
            role, text = msg.get("role", ""), msg.get("text", "") or msg.get("edition_type", "")
            if role == "system" and not system:
                system = text
            elif role in ("user", "human") and not prompt:
                prompt = text
    elif isinstance(tmpl, dict):
        prompt = tmpl.get("text", "")
    elif isinstance(data.get("prompt"), str):
        prompt = data["prompt"]
    return prompt, system


def _map_condition(data: dict) -> dict:
    conds = data.get("conditions") or []
    first = conds[0] if conds and isinstance(conds[0], dict) else {}
    op = _OP_MAP.get(str(first.get("comparison_operator", "")).lower(), "truthy")
    var = first.get("variable_selector") or []
    left = "$" + ".".join(str(v) for v in var) if var else None
    return {"left": left, "op": op, "right": first.get("value")}


def _map_node(dnode: dict, warnings: list[str]) -> dict:
    nid = str(dnode.get("id") or "")
    data = dnode.get("data") or {}
    dtype = str(data.get("type") or "")
    title = data.get("title") or dtype or nid

    if dtype in UNSUPPORTED_TYPES:
        warnings.append(f"node '{nid}' ({title}): type '{dtype}' unsupported(1차 유보, §3) — transform 플레이스홀더로 대체")
        return {"id": nid, "type": "transform", "config": {"output": {"_unmapped_dify_type": dtype, "note": "code 노드는 샌드박스 보안검토 선행 필요(로드맵)"}}}

    stype = NODE_TYPE_MAP.get(dtype)
    if stype is None:
        warnings.append(f"node '{nid}' ({title}): unrecognized Dify type '{dtype}' — transform 플레이스홀더로 대체")
        return {"id": nid, "type": "transform", "config": {"output": {"_unmapped_dify_type": dtype or "unknown"}}}

    if stype == "trigger":
        return {"id": nid, "type": "trigger"}
    if stype == "llm":
        prompt, system = _extract_llm_prompt(data)
        return {"id": nid, "type": "llm", "config": {"prompt": prompt, "system": system}}
    if stype == "condition":
        return {"id": nid, "type": "condition", "config": _map_condition(data)}
    if dtype == "knowledge-retrieval":
        warnings.append(f"node '{nid}' ({title}): RAG 컬렉션 재바인딩 수동 필요(§7.2.6)")
        return {"id": nid, "type": "agent", "config": {"agent_key": "rag", "note": "Dify knowledge-retrieval — 실 컬렉션 ID 수동 재바인딩 필요"}}
    if stype == "http":
        return {"id": nid, "type": "http", "config": {"url": data.get("url", ""), "method": str(data.get("method") or "GET").upper()}}
    if dtype == "tool":
        warnings.append(f"node '{nid}' ({title}): Dify 플러그인 ↔ Addon Agent 자동 1:1 매핑 불가 — 컴포넌트 팔레트로 수동 지정 필요(§7.2.6)")
        return {"id": nid, "type": "agent", "config": {"agent_key": "", "note": "Dify tool 노드 — 컴포넌트 팔레트에서 agent_key/method/path 수동 지정 필요"}}
    # answer/end
    return {"id": nid, "type": "notify", "config": {"message": data.get("answer", "") or f"{title} 완료"}}


def _map_edge(dedge: dict) -> dict:
    out = {"source": str(dedge.get("source") or ""), "target": str(dedge.get("target") or "")}
    handle = dedge.get("sourceHandle")
    if handle in ("true", "false"):
        out["when"] = handle
    return out


def import_dify_dsl(dsl_text: str) -> dict:
    """DSL YAML 텍스트 → {definition_json, name, description, dify_version, warnings}.

    파싱 실패(YAML 문법 오류)는 DifyDslError 로 명시. 구조가 예상과 달라도(빈 nodes 등)
    크래시하지 않고 빈 definition_json + warnings 로 반환한다(§7.2.6 관용적 파싱 원칙).
    """
    try:
        doc = yaml.safe_load(dsl_text)
    except yaml.YAMLError as exc:
        raise DifyDslError(f"invalid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise DifyDslError("DSL root must be a mapping")

    app_meta = doc.get("app") or {}
    name = str(app_meta.get("name") or "dify-import")
    description = str(app_meta.get("description") or "")
    version = str(doc.get("version") or "unknown")

    graph = ((doc.get("workflow") or {}).get("graph")) or {}
    dnodes = graph.get("nodes") or []
    dedges = graph.get("edges") or []

    warnings: list[str] = []
    nodes = [_map_node(n, warnings) for n in dnodes if isinstance(n, dict)]
    node_ids = {n["id"] for n in nodes}
    edges = []
    for e in dedges:
        if not isinstance(e, dict):
            continue
        me = _map_edge(e)
        if me["source"] not in node_ids or me["target"] not in node_ids:
            warnings.append(f"edge {me['source']}->{me['target']}: references node absent from parsed graph — skipped")
            continue
        edges.append(me)

    if not nodes:
        warnings.append("no nodes parsed from DSL — check workflow.graph.nodes path for this Dify version(§7.2.6 가정)")

    return {
        "name": name,
        "description": description,
        "dify_version": version,
        "definition_json": {"nodes": nodes, "edges": edges},
        "warnings": warnings,
    }
