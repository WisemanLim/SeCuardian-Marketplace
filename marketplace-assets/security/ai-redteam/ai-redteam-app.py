import logging
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-redteam"])

# In-memory report store — max 50 entries
_report_store: deque = deque(maxlen=50)


# ---------------------------------------------------------------------------
# Isolation guard
# ---------------------------------------------------------------------------

def _check_isolation():
    if os.getenv("REDTEAM_ENABLED", "false").lower() != "true":
        raise HTTPException(403, "REDTEAM_ENABLED=true 필요")
    if os.getenv("REDTEAM_NETWORK", "") != "redteam-isolated":
        raise HTTPException(403, "redteam-isolated 네트워크 필요 — REDTEAM_NETWORK=redteam-isolated")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class LLMScanRequest(BaseModel):
    target_url: str
    attack_strategy: str  # jailbreak | prompt_injection | data_exfil | all
    iterations: int = 10
    model_id: str = "gpt-4"


class SkillScanRequest(BaseModel):
    agent_url: str
    skills: List[str]
    evaluation_prompt: str = ""


class RedTeamReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scan_type: str  # llm | skill
    target: str
    strategy: str
    status: str  # running | completed | failed
    findings: List[dict] = []
    risk_score: float = 0.0
    risk_level: str = "UNKNOWN"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""
    summary: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mock_findings(target: str, strategy: str) -> List[dict]:
    return [
        {
            "type": strategy,
            "description": f"Mock finding for {target}",
            "severity": "HIGH",
            "confidence": 0.0,
            "note": "Configure PYRIT_ENDPOINT for real scanning",
        }
    ]


def _run_llm_scan(req: LLMScanRequest) -> tuple[List[dict], float, str]:
    """Run LLM scan via PyRIT or return mock results."""
    pyrit_endpoint = os.getenv("PYRIT_ENDPOINT", "")
    if not pyrit_endpoint:
        return _mock_findings(req.target_url, req.attack_strategy), 0.0, "MOCK"

    try:
        import httpx  # optional dep; present in execution environments
        api_key = os.getenv("PYRIT_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        payload = {
            "target_url": req.target_url,
            "attack_strategy": req.attack_strategy,
            "iterations": req.iterations,
            "model_id": req.model_id,
        }
        resp = httpx.post(f"{pyrit_endpoint}/scan", json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        findings = data.get("findings", [])
        risk_score = float(data.get("risk_score", 0.0))
        risk_level = data.get("risk_level", "UNKNOWN")
        return findings, risk_score, risk_level
    except Exception as exc:
        logger.error("PyRIT scan error: %s", exc)
        return [{"type": "error", "description": str(exc), "severity": "UNKNOWN", "confidence": 0.0}], 0.0, "ERROR"


def _run_skill_scan(req: SkillScanRequest) -> tuple[List[dict], float, str]:
    """Run skill scan via SkillSpector or return mock results."""
    spector_url = os.getenv("SKILLSPECTOR_URL", "")
    strategy = ",".join(req.skills) if req.skills else "skill-check"
    if not spector_url:
        return _mock_findings(req.agent_url, strategy), 0.0, "MOCK"

    try:
        import httpx
        payload = {
            "agent_url": req.agent_url,
            "skills": req.skills,
            "evaluation_prompt": req.evaluation_prompt,
        }
        resp = httpx.post(f"{spector_url}/evaluate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        findings = data.get("findings", [])
        risk_score = float(data.get("risk_score", 0.0))
        risk_level = data.get("risk_level", "UNKNOWN")
        return findings, risk_score, risk_level
    except Exception as exc:
        logger.error("SkillSpector scan error: %s", exc)
        return [{"type": "error", "description": str(exc), "severity": "UNKNOWN", "confidence": 0.0}], 0.0, "ERROR"


def _find_report(report_id: str) -> dict | None:
    for r in _report_store:
        if r["report_id"] == report_id:
            return r
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_status(
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /status accessed by user=%s", getattr(current_user, "id", "unknown"))
    _check_isolation()
    return {
        "REDTEAM_ENABLED": os.getenv("REDTEAM_ENABLED", "false"),
        "REDTEAM_NETWORK": os.getenv("REDTEAM_NETWORK", ""),
        "report_count": len(_report_store),
    }


@router.post("/scan/llm", response_model=RedTeamReport)
async def scan_llm(
    body: LLMScanRequest,
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /scan/llm accessed by user=%s target=%s", getattr(current_user, "id", "unknown"), body.target_url)
    _check_isolation()

    report = RedTeamReport(
        scan_type="llm",
        target=body.target_url,
        strategy=body.attack_strategy,
        status="running",
    )
    report_dict = report.model_dump()
    _report_store.append(report_dict)

    try:
        findings, risk_score, risk_level = _run_llm_scan(body)
        report_dict.update(
            status="completed",
            findings=findings,
            risk_score=risk_score,
            risk_level=risk_level,
            completed_at=_now_iso(),
            summary=f"Scan completed: {len(findings)} finding(s), risk_level={risk_level}",
        )
    except Exception as exc:
        logger.error("LLM scan failed: %s", exc)
        report_dict.update(status="failed", completed_at=_now_iso(), summary=str(exc))

    return report_dict


@router.post("/scan/skill", response_model=RedTeamReport)
async def scan_skill(
    body: SkillScanRequest,
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /scan/skill accessed by user=%s target=%s", getattr(current_user, "id", "unknown"), body.agent_url)
    _check_isolation()

    strategy = ",".join(body.skills) if body.skills else "skill-check"
    report = RedTeamReport(
        scan_type="skill",
        target=body.agent_url,
        strategy=strategy,
        status="running",
    )
    report_dict = report.model_dump()
    _report_store.append(report_dict)

    try:
        findings, risk_score, risk_level = _run_skill_scan(body)
        report_dict.update(
            status="completed",
            findings=findings,
            risk_score=risk_score,
            risk_level=risk_level,
            completed_at=_now_iso(),
            summary=f"Skill scan completed: {len(findings)} finding(s), risk_level={risk_level}",
        )
    except Exception as exc:
        logger.error("Skill scan failed: %s", exc)
        report_dict.update(status="failed", completed_at=_now_iso(), summary=str(exc))

    return report_dict


@router.get("/reports", response_model=List[RedTeamReport])
async def list_reports(
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /reports (list) accessed by user=%s", getattr(current_user, "id", "unknown"))
    _check_isolation()
    return list(_report_store)


@router.get("/reports/{report_id}", response_model=RedTeamReport)
async def get_report(
    report_id: str,
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /reports/%s accessed by user=%s", report_id, getattr(current_user, "id", "unknown"))
    _check_isolation()
    report = _find_report(report_id)
    if not report:
        raise HTTPException(404, f"Report {report_id} not found")
    return report


@router.delete("/reports")
async def clear_reports(
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /reports (delete) accessed by user=%s", getattr(current_user, "id", "unknown"))
    _check_isolation()
    _report_store.clear()
    return {"message": "All reports cleared", "report_count": 0}


@router.get("/config")
async def get_config(
    request: Request,
    current_user=Depends(require_role("supervisor")),
):
    logger.warning("ai-redteam /config accessed by user=%s", getattr(current_user, "id", "unknown"))
    _check_isolation()
    return {
        "REDTEAM_ENABLED": os.getenv("REDTEAM_ENABLED", "false"),
        "REDTEAM_NETWORK": os.getenv("REDTEAM_NETWORK", ""),
        "PYRIT_ENDPOINT": os.getenv("PYRIT_ENDPOINT", ""),
        "PYRIT_API_KEY": "***" if os.getenv("PYRIT_API_KEY") else "",
        "SKILLSPECTOR_URL": os.getenv("SKILLSPECTOR_URL", ""),
    }
