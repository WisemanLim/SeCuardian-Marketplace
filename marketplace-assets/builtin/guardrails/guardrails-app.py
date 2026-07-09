"""가드레일 에이전트 — ADDON 판 (guardrails).

내장 라우터 app/routers/router_guardrails.py (F-GRD) 의 ADDON 패키징.
로더가 /api/addon/guardrails prefix 로 마운트한다.
설정은 내장판(settings.*) 대신 환경변수로 주입한다.
DB·MCP 서버 없이 인메모리 저장소(deque)로 동작 — 도메인 카탈로그·텍스트 판정·결정 로그.
1차 구현: 단순 키워드 패턴으로 global(PII) 도메인 판정.
"""
import datetime
import os
import re
import uuid
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["guardrails"])

GUARDRAILS_ENABLED = os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true"
GUARDRAILS_MAX_DECISIONS = int(os.getenv("GUARDRAILS_MAX_DECISIONS", "500"))

# 도메인 카탈로그 (인메모리 초기값)
_DOMAIN_CATALOG = [
    {"domain_key": "global", "name": "PII / 신용정보", "status": "functional",
     "description": "주민등록번호·신용카드·전화번호 등 13종 개인정보 판정"},
    {"domain_key": "medical", "name": "의료정보", "status": "catalog_only",
     "description": "의료 관련 민감 정보 (1차 미구현)"},
    {"domain_key": "financial", "name": "금융정보", "status": "catalog_only",
     "description": "금융 계좌·거래 정보 (1차 미구현)"},
    {"domain_key": "legal", "name": "법률정보", "status": "catalog_only",
     "description": "법률 관련 민감 정보 (1차 미구현)"},
]

# PII 패턴 (global 도메인 — PRD §7.8.0)
_PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("resident_id", "주민등록번호", re.compile(r"\b\d{6}[-\s]?\d{7}\b")),
    ("card_number", "신용카드번호", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")),
    ("phone_kr", "한국 전화번호", re.compile(r"\b0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b")),
    ("email", "이메일", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("bank_account", "계좌번호", re.compile(r"\b\d{3,6}[-\s]?\d{2,6}[-\s]?\d{2,6}\b")),
    ("passport", "여권번호", re.compile(r"\b[A-Z]{1,2}\d{7,8}\b")),
    ("ip_address", "IP주소", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]

# 인메모리 저장소
_agent_configs: dict[str, list[dict]] = {}  # agent_key → [config]
_decisions: deque[dict] = deque(maxlen=GUARDRAILS_MAX_DECISIONS)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _detect_pii(text: str) -> tuple[list[dict], float]:
    """간단한 PII 패턴 탐지 — ADDON 인메모리 버전."""
    matched: list[dict] = []
    for rule_id, rule_name, pattern in _PII_PATTERNS:
        m = pattern.search(text)
        if m:
            matched.append({"ruleId": rule_id, "name": rule_name, "matched": m.group(0)[:30] + "..."})
    risk = min(1.0, len(matched) * 0.25)
    return matched, risk


class ConfigToggle(BaseModel):
    domain_key: str = Field(min_length=1)
    enabled: bool
    io_scope: str = "both"


class TestRequest(BaseModel):
    text: str = Field(min_length=1)
    domain: str = "global"
    agent_key: str = ""


@router.get("/status")
async def guardrails_status(_: dict = Depends(get_current_user)):
    """가드레일 에이전트 상태."""
    return {
        "guardrails_enabled": GUARDRAILS_ENABLED,
        "domains_count": len(_DOMAIN_CATALOG),
        "decisions_stored": len(_decisions),
        "functional_domains": [d["domain_key"] for d in _DOMAIN_CATALOG if d["status"] == "functional"],
        "source": "guardrails (in-memory ADDON, keyword PII detection)",
    }


@router.get("/domains")
async def list_domains(_: dict = Depends(get_current_user)):
    """가드레일 도메인 카탈로그 목록."""
    return {"domains": _DOMAIN_CATALOG}


@router.post("/test")
async def test_text(body: TestRequest, user: dict = Depends(get_current_user)):
    """임의 텍스트를 즉시 판정 — global 도메인만 실판정, 나머지는 catalog_only."""
    dom = next((d for d in _DOMAIN_CATALOG if d["domain_key"] == body.domain), None)
    if not dom:
        raise HTTPException(404, f"domain '{body.domain}' not in catalog")
    if dom["status"] != "functional":
        raise HTTPException(
            409,
            f"domain '{body.domain}' is catalog_only — no detector backend yet, use 'global'",
        )

    matched_rules, risk_score = _detect_pii(body.text)
    decision = "BLOCK" if risk_score >= 0.5 else ("WARN" if risk_score > 0 else "ALLOW")
    decision_id = str(uuid.uuid4())

    log: dict = {
        "decision_id": decision_id,
        "domain": body.domain,
        "decision": decision,
        "risk_score": risk_score,
        "matched_rules": matched_rules,
        "evaluated_domains": [body.domain],
        "agent_key": body.agent_key or None,
        "decided_at": _now(),
    }

    if body.agent_key:
        _decisions.appendleft(log)

    return {
        "decisionId": decision_id,
        "decision": decision,
        "riskScore": risk_score,
        "matchedRules": matched_rules,
        "evaluatedDomains": [body.domain],
    }


@router.get("/decisions")
async def list_decisions(
    agent_key: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    """결정 로그 목록."""
    items = list(_decisions)
    if agent_key:
        items = [d for d in items if d.get("agent_key") == agent_key]
    return {"total": len(items), "decisions": items[:limit]}


@router.get("/decisions/{decision_id}")
async def explain_decision(decision_id: str, _: dict = Depends(get_current_user)):
    """결정 단건 조회."""
    row = next((d for d in _decisions if d["decision_id"] == decision_id), None)
    if not row:
        raise HTTPException(404, "decision not found")
    return row


@router.put("/agents/{agent_key}/config")
async def set_agent_config(
    agent_key: str,
    body: ConfigToggle,
    _: dict = Depends(get_current_user),
):
    """에이전트별 가드레일 도메인 설정."""
    if body.io_scope not in ("input", "output", "both"):
        raise HTTPException(422, "io_scope must be 'input', 'output', or 'both'")
    dom = next((d for d in _DOMAIN_CATALOG if d["domain_key"] == body.domain_key), None)
    if not dom:
        raise HTTPException(404, f"domain '{body.domain_key}' not in catalog")
    configs = _agent_configs.setdefault(agent_key, [])
    existing = next((c for c in configs if c["domain_key"] == body.domain_key), None)
    if existing:
        existing["enabled"] = body.enabled
        existing["io_scope"] = body.io_scope
    else:
        configs.append({"domain_key": body.domain_key, "enabled": body.enabled, "io_scope": body.io_scope})
    return {"agent_key": agent_key, "domain_key": body.domain_key, "enabled": body.enabled, "io_scope": body.io_scope}


@router.get("/agents/{agent_key}/config")
async def get_agent_config(agent_key: str, _: dict = Depends(get_current_user)):
    """에이전트별 가드레일 설정 조회."""
    return {"agent_key": agent_key, "domains": _agent_configs.get(agent_key, [])}
