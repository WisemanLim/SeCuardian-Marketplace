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
from app.services.guardrails_mcp import validate

router = APIRouter(prefix="/api/guardrails", tags=["guardrails"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class ConfigToggle(BaseModel):
    domain_key: str = Field(min_length=1)
    enabled: bool
    io_scope: str = "both"  # input | output | both


class TestRequest(BaseModel):
    text: str = Field(min_length=1)
    domain: str = "global"
    agent_key: str | None = None  # 지정 시 guardrails_decision_log 에 기록


@router.get("/domains")
async def list_domains(user: dict = Depends(get_current_user)):
    rows = await fetch_all("SELECT * FROM guardrails_domain_catalog ORDER BY status DESC, domain_key")
    return {"domains": rows}


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


@router.post("/test")
async def test_text(body: TestRequest, user: dict = Depends(get_current_user)):
    """Playground 연계(§7.8.5) — 임의 텍스트를 즉시 판정. `global` 외 도메인은 카탈로그 전용(§7.8.0)."""
    dom = await fetch_one(
        "SELECT status FROM guardrails_domain_catalog WHERE domain_key = " + _PH, (body.domain,)
    )
    if not dom:
        raise HTTPException(404, f"domain '{body.domain}' not in catalog")
    if dom["status"] != "functional":
        raise HTTPException(
            409, f"domain '{body.domain}' is catalog_only — no detector backend yet (PRD §7.8.0), use 'global'"
        )

    result = await validate(body.text, domain=body.domain, tool="validate_input", tenant_id=_tenant())
    decision_id = str(uuid.uuid4())
    result["decisionId"] = decision_id
    result["evaluatedDomains"] = [body.domain]

    if body.agent_key:
        await execute_insert(
            f"INSERT INTO guardrails_decision_log "
            f"(agent_key, decision_id, domain_key, decision, risk_score, matched_rule_count, tenant_id) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
            (body.agent_key, decision_id, body.domain, result["decision"], result["riskScore"],
             len(result["matchedRules"]), _tenant()),
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
