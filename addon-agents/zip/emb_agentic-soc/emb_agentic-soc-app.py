import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["agentic-soc"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AGENTIC_SOC_ENABLED = os.getenv("AGENTIC_SOC_ENABLED", "true").lower() == "true"
AGENTIC_SOC_FINDINGS_MAX = int(os.getenv("AGENTIC_SOC_FINDINGS_MAX", "1000"))
SECUARDIAN_BASE_URL = os.getenv("SECUARDIAN_BASE_URL", "http://localhost:8200")

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------
findings_store: deque = deque(maxlen=AGENTIC_SOC_FINDINGS_MAX)
playbook_store: dict = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class A2AMessage(BaseModel):
    msg_id: str
    sender_agent: str
    intent: str
    payload: dict
    timestamp: str


class A2AResponse(BaseModel):
    msg_id: str
    status: str  # ok / error
    result: dict = {}
    timestamp: str


class Finding(BaseModel):
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str
    severity: str  # CRITICAL / HIGH / MEDIUM / LOW / INFO
    category: str
    title: str
    description: str
    evidence: dict = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged: bool = False


class Playbook(BaseModel):
    playbook_id: str
    name: str
    description: str
    trigger_intents: list[str]
    steps: list[str]


# ---------------------------------------------------------------------------
# Built-in playbooks
# ---------------------------------------------------------------------------
_BUILTIN_PLAYBOOKS = [
    Playbook(
        playbook_id="isolate-host",
        name="Isolate Host",
        description="Block IP via CrowdSec, notify Wazuh, and create an incident on runtime or threat intel alerts.",
        trigger_intents=["runtime_alert", "threat_intel"],
        steps=["block-ip-crowdsec", "notify-wazuh", "create-incident"],
    ),
    Playbook(
        playbook_id="revoke-credentials",
        name="Revoke Credentials",
        description="Disable Keycloak user, revoke Vault token, and write an audit log on IAM or secrets queries.",
        trigger_intents=["iam_query", "secrets_query"],
        steps=["disable-keycloak-user", "revoke-vault-token", "audit-log"],
    ),
    Playbook(
        playbook_id="create-incident",
        name="Create Incident",
        description="Open a Shuffle workflow, notify the team, and collect evidence on SIEM queries or compliance reports.",
        trigger_intents=["siem_query", "compliance_report"],
        steps=["open-shuffle-workflow", "notify-team", "collect-evidence"],
    ),
]

for _pb in _BUILTIN_PLAYBOOKS:
    playbook_store[_pb.playbook_id] = _pb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_finding(finding_id: str) -> Optional[Finding]:
    for f in findings_store:
        if f.finding_id == finding_id:
            return f
    return None


def _find_playbook_by_intent(intent: str) -> Optional[Playbook]:
    for pb in playbook_store.values():
        if intent in pb.trigger_intents:
            return pb
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/.well-known/agent.json", include_in_schema=False)
async def agent_card():
    """A2A agent card — public, no JWT required."""
    return {
        "agent_id": "agentic-soc",
        "name": "Agentic SOC",
        "type": "federation",
        "version": "1.0.0",
        "description": "Federation platform that orchestrates security agents via A2A messaging, manages findings, and executes playbooks.",
        "base_url": SECUARDIAN_BASE_URL,
        "capabilities": ["a2a", "findings", "playbooks"],
        "intents": [pb.trigger_intents for pb in playbook_store.values()],
        "endpoints": {
            "a2a": "/a2a",
            "findings": "/findings",
            "playbooks": "/playbooks",
            "status": "/status",
        },
    }


@router.post("/a2a", response_model=A2AResponse)
async def handle_a2a_message(msg: A2AMessage):
    """Handle an A2A message and route by intent to the matching playbook."""
    if not AGENTIC_SOC_ENABLED:
        raise HTTPException(status_code=503, detail="Agentic SOC is disabled")

    playbook = _find_playbook_by_intent(msg.intent)
    if playbook is None:
        return A2AResponse(
            msg_id=msg.msg_id,
            status="error",
            result={"detail": f"No playbook matches intent '{msg.intent}'"},
            timestamp=_now_iso(),
        )

    # Auto-submit a finding for this A2A event
    finding = Finding(
        source_agent=msg.sender_agent,
        severity="INFO",
        category="a2a_event",
        title=f"A2A intent received: {msg.intent}",
        description=f"Message {msg.msg_id} from {msg.sender_agent} triggered playbook '{playbook.playbook_id}'.",
        evidence={"msg_id": msg.msg_id, "payload": msg.payload, "playbook": playbook.playbook_id},
    )
    findings_store.append(finding)

    return A2AResponse(
        msg_id=msg.msg_id,
        status="ok",
        result={
            "matched_playbook": playbook.playbook_id,
            "playbook_name": playbook.name,
            "steps": playbook.steps,
            "finding_id": finding.finding_id,
        },
        timestamp=_now_iso(),
    )


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    """Platform status with finding counts and playbook count."""
    severity_counts: dict = {}
    acknowledged_count = 0
    for f in findings_store:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
        if f.acknowledged:
            acknowledged_count += 1

    return {
        "enabled": AGENTIC_SOC_ENABLED,
        "findings_total": len(findings_store),
        "findings_max": AGENTIC_SOC_FINDINGS_MAX,
        "findings_acknowledged": acknowledged_count,
        "findings_by_severity": severity_counts,
        "playbook_count": len(playbook_store),
        "timestamp": _now_iso(),
    }


@router.get("/findings")
async def list_findings(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None),
    source_agent: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    current_user=Depends(get_current_user),
):
    """List findings with optional filters."""
    results = list(findings_store)

    if severity:
        results = [f for f in results if f.severity == severity.upper()]
    if source_agent:
        results = [f for f in results if f.source_agent == source_agent]
    if acknowledged is not None:
        results = [f for f in results if f.acknowledged == acknowledged]

    # Most recent first
    results = list(reversed(results))[:limit]
    return [f.model_dump() for f in results]


@router.post("/findings", status_code=201)
async def submit_finding(finding: Finding):
    """Submit a finding from any agent — no JWT required."""
    if not AGENTIC_SOC_ENABLED:
        raise HTTPException(status_code=503, detail="Agentic SOC is disabled")

    # Ensure auto-fields are fresh (pydantic defaults already handle this,
    # but guard against a caller supplying their own values)
    finding.finding_id = str(uuid.uuid4())
    finding.timestamp = _now_iso()
    finding.acknowledged = False

    valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
    if finding.severity.upper() not in valid_severities:
        raise HTTPException(status_code=422, detail=f"severity must be one of {valid_severities}")
    finding.severity = finding.severity.upper()

    findings_store.append(finding)
    return finding.model_dump()


@router.patch("/findings/{finding_id}/acknowledge")
async def acknowledge_finding(finding_id: str, current_user=Depends(get_current_user)):
    """Mark a finding as acknowledged."""
    finding = _get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.acknowledged = True
    return {"finding_id": finding_id, "acknowledged": True, "timestamp": _now_iso()}


@router.get("/playbooks")
async def list_playbooks(current_user=Depends(get_current_user)):
    """List all playbooks."""
    return [pb.model_dump() for pb in playbook_store.values()]


@router.post("/playbooks/{playbook_id}/execute")
async def execute_playbook(
    playbook_id: str,
    current_user=Depends(require_role(["supervisor", "admin"])),
):
    """Execute a playbook and log each step as a finding."""
    playbook = playbook_store.get(playbook_id)
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    step_findings = []
    for step in playbook.steps:
        f = Finding(
            source_agent="agentic-soc",
            severity="INFO",
            category="playbook_execution",
            title=f"Playbook step executed: {step}",
            description=f"Playbook '{playbook.name}' ({playbook_id}) step '{step}' executed.",
            evidence={"playbook_id": playbook_id, "step": step},
        )
        findings_store.append(f)
        step_findings.append({"step": step, "finding_id": f.finding_id})

    return {
        "playbook_id": playbook_id,
        "playbook_name": playbook.name,
        "steps_executed": len(playbook.steps),
        "step_findings": step_findings,
        "timestamp": _now_iso(),
    }


@router.get("/config")
async def get_config(current_user=Depends(require_role(["admin"]))):
    """Return Agentic SOC environment configuration."""
    return {
        "AGENTIC_SOC_ENABLED": os.getenv("AGENTIC_SOC_ENABLED", "true"),
        "AGENTIC_SOC_FINDINGS_MAX": os.getenv("AGENTIC_SOC_FINDINGS_MAX", "1000"),
        "SECUARDIAN_BASE_URL": os.getenv("SECUARDIAN_BASE_URL", "http://localhost:8200"),
    }
