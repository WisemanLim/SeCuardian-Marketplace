"""router_guardrails (F-GRD) — /api/guardrails.

PRD §7.8 준용. wise-Guardrails 는 도메인 인가를 강제하지 않으므로(§7.8.3),
SeCMP 가 `agent_guardrail_config` 에서 도메인 스코프를 소유·강제한다.

1차 실기능 범위(§7.8.0): `global`(PII/신용정보 13종) 도메인만 실판정.
판정기는 `services/guardrails_detector.py`(로컬 재구현) — MCP Server 연동은 향후
`GUARDRAILS_MCP_URL` 대상 프록시로 확장 가능하나, 1차는 로컬 판정으로 무중단 보장.
`guardrails_decision_log` 는 SeCMP 측 이중 감사(업스트림 Audit Service TTL 미구현 리스크 완화, §6).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one
from app.services.guardrails_detector import decide_multi, decide_multi_llm

router = APIRouter(prefix="/api/guardrails", tags=["guardrails"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class ConfigToggle(BaseModel):
    domain_key: str = Field(min_length=1)
    enabled: bool
    io_scope: str = "both"  # input | output | both


class TestRequest(BaseModel):
    text: str = Field(min_length=1)
    domain: str = "global"                 # 하위호환(단일 도메인) — domains 미지정 시 참고
    domains: list[str] | None = None       # 지정 시 이 도메인들만 평가(§7.8.7)
    agent_key: str | None = None           # 지정 시 guardrails_decision_log 에 기록


class DomainFilterToggle(BaseModel):
    enabled: bool


@router.get("/domains")
async def list_domains(user: dict = Depends(get_current_user)):
    # is_required(global) 우선 → filter_enabled → domain_key 순 정렬
    rows = await fetch_all(
        "SELECT * FROM guardrails_domain_catalog ORDER BY is_required DESC, status DESC, domain_key"
    )
    return {"domains": rows}


@router.put("/domains/{domain_key}/filter")
async def set_domain_filter(
    domain_key: str, body: DomainFilterToggle,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    """도메인 카탈로그 `필터적용` 토글(§7.8.7). 필수(global) 도메인은 해제 불가."""
    dom = await fetch_one(
        "SELECT is_required FROM guardrails_domain_catalog WHERE domain_key = " + _PH, (domain_key,)
    )
    if not dom:
        raise HTTPException(404, f"domain '{domain_key}' not in catalog")
    if dom["is_required"] and not body.enabled:
        raise HTTPException(409, f"domain '{domain_key}' is required and cannot be disabled")
    await execute_write(
        f"UPDATE guardrails_domain_catalog SET filter_enabled = {_PH} WHERE domain_key = {_PH}",
        (1 if body.enabled else 0, domain_key),
    )
    return {"domain_key": domain_key, "filter_enabled": body.enabled}


@router.get("/agents/{agent_key}/config")
async def get_agent_config(agent_key: str, user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        f"SELECT * FROM agent_guardrail_config WHERE agent_key = {_PH} ORDER BY domain_key", (agent_key,)
    )
    return {"agent_key": agent_key, "domains": rows}


@router.put("/agents/{agent_key}/config")
async def set_agent_config(
    agent_key: str, body: ConfigToggle, user: dict = Depends(require_role("admin", "supervisor"))
):
    if body.io_scope not in ("input", "output", "both"):
        raise HTTPException(422, "io_scope must be 'input', 'output', or 'both'")
    dom = await fetch_one(
        "SELECT domain_key FROM guardrails_domain_catalog WHERE domain_key = " + _PH, (body.domain_key,)
    )
    if not dom:
        raise HTTPException(404, f"domain '{body.domain_key}' not in catalog")
    existing = await fetch_one(
        f"SELECT 1 AS x FROM agent_guardrail_config WHERE agent_key = {_PH} AND domain_key = {_PH}",
        (agent_key, body.domain_key),
    )
    who = user.get("username") or user.get("sub") or ""
    if existing:
        await execute_write(
            f"UPDATE agent_guardrail_config SET enabled = {_PH}, io_scope = {_PH}, updated_by = {_PH}, "
            f"updated_at = CURRENT_TIMESTAMP WHERE agent_key = {_PH} AND domain_key = {_PH}",
            (1 if body.enabled else 0, body.io_scope, who, agent_key, body.domain_key),
        )
    else:
        await execute_insert(
            f"INSERT INTO agent_guardrail_config (agent_key, domain_key, enabled, io_scope, updated_by) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
            (agent_key, body.domain_key, 1 if body.enabled else 0, body.io_scope, who),
        )
    return {"agent_key": agent_key, "domain_key": body.domain_key, "enabled": body.enabled, "io_scope": body.io_scope}


async def _resolve_test_domains(body: TestRequest) -> list[str]:
    """평가 대상 도메인 결정(§7.8.7): 필수(global) + filter_enabled=1 도메인.

    명시 요청 우선순위: body.domains > body.domain(단일, 기본 global). 항상 필수 도메인은 포함.
    """
    required = [r["domain_key"] for r in await fetch_all(
        "SELECT domain_key FROM guardrails_domain_catalog WHERE is_required = 1"
    )] or ["global"]
    if body.domains:
        chosen = list(body.domains)
    elif body.domain and body.domain != "global":
        chosen = [body.domain]
    else:
        chosen = [r["domain_key"] for r in await fetch_all(
            "SELECT domain_key FROM guardrails_domain_catalog WHERE filter_enabled = 1"
        )]
    # 필수 도메인 항상 포함(중복 제거, 순서 보존)
    seen: set[str] = set()
    ordered: list[str] = []
    for dk in required + chosen:
        if dk not in seen:
            seen.add(dk)
            ordered.append(dk)
    return ordered


@router.post("/test")
async def test_text(body: TestRequest, user: dict = Depends(get_current_user)):
    """Playground 연계(§7.8.5) — 임의 텍스트를 다도메인 판정(§7.8.7).

    필수(global) + `필터적용` 도메인(또는 요청 domains)을 동시 평가. 로컬 결정적 판정
    (regex 원본 + 생성 regex). MCP 는 게이트 경로에서 사용, 테스트는 로컬 룰스토어로 즉시 판정.
    """
    domains = await _resolve_test_domains(body)
    if settings.guardrails_classifier_enabled:
        result = await decide_multi_llm(body.text, domains)  # regex + LLM 완전판정(§7.8.7)
    else:
        result = decide_multi(body.text, domains)            # regex 결정적 판정
    decision_id = str(uuid.uuid4())
    result["decisionId"] = decision_id

    if body.agent_key:
        await execute_insert(
            f"INSERT INTO guardrails_decision_log "
            f"(agent_key, decision_id, domain_key, decision, risk_score, matched_rule_count, tenant_id) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
            (body.agent_key, decision_id, ",".join(domains)[:64], result["decision"],
             result["riskScore"], len(result["matchedRules"]), _tenant()),
        )
    return result


@router.get("/decisions/{decision_id}")
async def explain_decision(decision_id: str, user: dict = Depends(get_current_user)):
    row = await fetch_one(
        "SELECT * FROM guardrails_decision_log WHERE decision_id = " + _PH, (decision_id,)
    )
    if not row:
        raise HTTPException(404, "decision not found")
    return row


@router.get("/decisions")
async def list_decisions(agent_key: str | None = None, limit: int = 50, user: dict = Depends(get_current_user)):
    tid = _tenant()
    sql = f"SELECT * FROM guardrails_decision_log WHERE tenant_id = {_PH}"
    params: list = [tid]
    if agent_key:
        sql += f" AND agent_key = {_PH}"
        params.append(agent_key)
    sql += f" ORDER BY id DESC LIMIT {_PH}"
    params.append(min(limit, 200))
    return {"decisions": await fetch_all(sql, tuple(params))}
