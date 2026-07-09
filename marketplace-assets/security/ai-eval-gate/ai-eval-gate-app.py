"""AI 보안 평가 게이트 — ADDON 판 (ai-eval-gate).

내장 라우터 app/routers/router_ai_eval.py (E20 T20-1) 의 ADDON 패키징.
AI 배포 전 보안 게이트 — PyRIT / SkillSpector / agentshield 평가 결과 수집 및 게이트 판정.

라이선스:
  PyRIT:        microsoft/pyrit (MIT)
  SkillSpector: NVIDIA/SkillSpector (Apache-2.0)
  agentshield:  affaan-m/agentshield (MIT)

⚠️ AI_EVAL_GATE_ENABLED=false 기본값 — 활성화 전 보안팀 승인 필요.
로더가 /api/addon/ai-eval-gate prefix 로 마운트한다.
"""
import datetime
import os
import uuid
from collections import deque
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["ai-eval-gate"])

AI_EVAL_GATE_ENABLED = os.getenv("AI_EVAL_GATE_ENABLED", "false").lower() == "true"
AI_EVAL_URL = os.getenv("AI_EVAL_URL", "http://localhost:9450")

_scan_store: deque[dict[str, Any]] = deque(maxlen=100)
_gate_store: deque[dict[str, Any]] = deque(maxlen=50)


def _require_gate_enabled() -> None:
    if not AI_EVAL_GATE_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="AI_EVAL_GATE_ENABLED=false — 보안팀 승인 후 활성화 필요",
        )


@router.get("/status")
async def get_status(_: dict = Depends(get_current_user)) -> dict:
    """AI 보안 평가 게이트 상태."""
    scans = list(_scan_store)
    critical_open = sum(
        1 for s in scans
        if s.get("severity") in ("critical", "high") and s.get("status") != "mitigated"
    )
    return {
        "gate_enabled": AI_EVAL_GATE_ENABLED,
        "ai_eval_url": AI_EVAL_URL,
        "scans_stored": len(_scan_store),
        "critical_open": critical_open,
        "gate_results": len(_gate_store),
        "tools_supported": ["pyrit", "skillspector", "agentshield"],
    }


class EvalFinding(BaseModel):
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool: str  # pyrit|skillspector|agentshield
    category: str  # prompt_injection|jailbreak|skill_permission|tool_misuse
    severity: str  # critical|high|medium|low
    target: str = ""
    description: str = ""
    recommendation: str = ""
    raw: dict = Field(default_factory=dict)


@router.post("/scans", status_code=status.HTTP_202_ACCEPTED)
async def receive_scan(findings: list[EvalFinding]) -> dict:
    """평가 결과 수신 (인증 불필요: 내부 평가 도구 통신)."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    batch_id = str(uuid.uuid4())[:8]
    for f in findings:
        record = f.model_dump()
        record["batch_id"] = batch_id
        record["received_at"] = now
        record["status"] = "open"
        _scan_store.appendleft(record)

    critical_count = sum(1 for f in findings if f.severity in ("critical", "high"))
    return {
        "accepted": True,
        "batch_id": batch_id,
        "count": len(findings),
        "critical_high": critical_count,
        "stored": len(_scan_store),
    }


@router.get("/scans")
async def list_scans(
    limit: int = Query(20, ge=1, le=100),
    tool: str = Query("", description="pyrit|skillspector|agentshield"),
    severity: str = Query("", description="critical|high|medium|low"),
    _: dict = Depends(get_current_user),
) -> dict:
    """AI 보안 평가 결과 목록."""
    scans = list(_scan_store)
    if tool:
        tools = {t.strip().lower() for t in tool.split(",")}
        scans = [s for s in scans if s.get("tool", "").lower() in tools]
    if severity:
        sevs = {s.strip().lower() for s in severity.split(",")}
        scans = [s for s in scans if s.get("severity", "").lower() in sevs]
    return {"total": len(_scan_store), "returned": len(scans[:limit]), "scans": scans[:limit]}


class GateRequest(BaseModel):
    target: str            # 배포 대상 (모델명, 에이전트명 등)
    batch_id: str = ""     # 특정 평가 배치 ID (빈 값=최근 전체)
    min_severity: str = "high"  # 이 이상 심각도 발견 시 FAIL


@router.post("/gate")
async def evaluate_gate(
    req: GateRequest,
    _: dict = Depends(get_current_user),
) -> dict:
    """AI 배포 전 보안 게이트 통과 판정 — AI_EVAL_GATE_ENABLED=true 필요.

    PASS: min_severity 이상 심각도의 open 발견사항 없음 / FAIL: 1건 이상.
    """
    _require_gate_enabled()

    sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    min_level = sev_order.get(req.min_severity.lower(), 3)

    scans = list(_scan_store)
    if req.batch_id:
        scans = [s for s in scans if s.get("batch_id") == req.batch_id]
    if req.target:
        scans = [s for s in scans if req.target.lower() in s.get("target", "").lower()]

    blocking = [
        s for s in scans
        if sev_order.get(s.get("severity", "").lower(), 0) >= min_level
        and s.get("status") != "mitigated"
    ]

    passed = len(blocking) == 0
    gate_result = {
        "id": str(uuid.uuid4())[:8],
        "target": req.target,
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL",
        "blocking": len(blocking),
        "min_severity": req.min_severity,
        "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "findings": blocking[:10],
    }
    _gate_store.appendleft(gate_result)
    return gate_result


@router.get("/gate")
async def list_gate_results(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(get_current_user),
) -> dict:
    """최근 게이트 판정 결과 목록."""
    results = list(_gate_store)[:limit]
    return {"total": len(_gate_store), "returned": len(results), "results": results}
