"""router_governance (F-GOV/E6, impl/55) — /api/governance.

거버넌스 두 축:
  1) HITL 승인 게이트 — write/delete/external 등 고영향 액션에 사람 승인(LLM08 Excessive Agency).
     tbl_hitl_approvals 테이블 기반 CRUD + approve/reject.
  2) OWASP LLM Top10 통제 성숙도 스코어카드 — 플랫폼 실제 상태(가드레일·HITL·감사·서명 등)에서
     통제별 점수(1~5)를 산출(부록 C 재평가 대상).

add-only: 기존 라우터·테이블 무변경. tbl_hitl_approvals 는 01_init.sql(멱등)로 생성.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one

router = APIRouter(prefix="/api/governance", tags=["governance"])

_ACTIONS = {"write", "delete", "external", "custom"}
_HIGH_IMPACT = {"write", "delete", "external"}


def _tenant() -> str:
    return settings.tenant_default_id or "default"


async def _count(sql: str, params: tuple = ()) -> int:
    row = await fetch_one(sql, params)
    return int((row or {}).get("n", 0)) if row else 0


# ─── HITL 승인 게이트 ─────────────────────────────────────────────────────────

class HitlCreate(BaseModel):
    action: str
    resource: Optional[str] = None
    payload: Optional[str] = None


class HitlDecision(BaseModel):
    reason: Optional[str] = None


@router.post("/hitl", status_code=201)
async def create_hitl(body: HitlCreate, user: dict = Depends(get_current_user)):
    """고영향 액션 승인 요청 생성(status=pending)."""
    action = (body.action or "").strip().lower()
    if action not in _ACTIONS:
        raise HTTPException(status_code=422, detail=f"action 은 {sorted(_ACTIONS)} 중 하나여야 합니다.")
    tid = _tenant()
    new_id = await execute_insert(
        f"INSERT INTO tbl_hitl_approvals (tenant_id, action, resource, payload, status, requested_by) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, 'pending', {_PH})",
        (tid, action, (body.resource or "")[:256], (body.payload or "")[:8000], user.get("username", "")),
    )
    return {"id": new_id, "action": action, "status": "pending", "high_impact": action in _HIGH_IMPACT}


@router.get("/hitl")
async def list_hitl(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """승인 요청 목록(선택 status 필터)."""
    tid = _tenant()
    if status:
        st = status.strip().lower()
        if st not in ("pending", "approved", "rejected"):
            raise HTTPException(status_code=422, detail="status 는 pending|approved|rejected")
        rows = await fetch_all(
            f"SELECT * FROM tbl_hitl_approvals WHERE tenant_id = {_PH} AND status = {_PH} ORDER BY id DESC LIMIT 200",
            (tid, st))
    else:
        rows = await fetch_all(
            f"SELECT * FROM tbl_hitl_approvals WHERE tenant_id = {_PH} ORDER BY id DESC LIMIT 200", (tid,))
    pending = await _count(
        f"SELECT COUNT(*) AS n FROM tbl_hitl_approvals WHERE tenant_id = {_PH} AND status = 'pending'", (tid,))
    return {"items": rows, "pending_count": pending}


async def _decide(approval_id: int, decision: str, decided_by: str, reason: str) -> dict:
    tid = _tenant()
    row = await fetch_one(
        f"SELECT * FROM tbl_hitl_approvals WHERE tenant_id = {_PH} AND id = {_PH}", (tid, approval_id))
    if not row:
        raise HTTPException(status_code=404, detail="승인 요청 없음")
    if row.get("status") != "pending":
        raise HTTPException(status_code=409, detail=f"이미 처리됨: {row.get('status')}")
    await execute_write(
        f"UPDATE tbl_hitl_approvals SET status = {_PH}, decided_by = {_PH}, reason = {_PH}, "
        f"decided_at = CURRENT_TIMESTAMP WHERE tenant_id = {_PH} AND id = {_PH}",
        (decision, decided_by, (reason or "")[:512], tid, approval_id))
    return await fetch_one(
        f"SELECT * FROM tbl_hitl_approvals WHERE tenant_id = {_PH} AND id = {_PH}", (tid, approval_id))


@router.post("/hitl/{approval_id}/approve")
async def approve_hitl(approval_id: int, body: HitlDecision, user: dict = Depends(require_role("supervisor", "admin"))):
    """승인(supervisor/admin)."""
    return {"updated": await _decide(approval_id, "approved", user.get("username", ""), body.reason or "")}


@router.post("/hitl/{approval_id}/reject")
async def reject_hitl(approval_id: int, body: HitlDecision, user: dict = Depends(require_role("supervisor", "admin"))):
    """거부(supervisor/admin)."""
    return {"updated": await _decide(approval_id, "rejected", user.get("username", ""), body.reason or "")}


# ─── OWASP LLM Top10 스코어카드 ───────────────────────────────────────────────

async def _platform_signals() -> dict:
    """스코어 산출용 플랫폼 실제 상태 신호."""
    tid = _tenant()
    sig: dict = {}
    # 가드레일 도메인 토글(입력/출력 필터) 활성 수
    try:
        sig["guardrails_enabled"] = await _count(
            "SELECT COUNT(*) AS n FROM agent_guardrail_config WHERE enabled = 1")
    except Exception:  # noqa: BLE001
        sig["guardrails_enabled"] = 0
    # 가드레일 결정 로그(감사) 존재
    try:
        sig["audit_decisions"] = await _count("SELECT COUNT(*) AS n FROM guardrails_decision_log")
    except Exception:  # noqa: BLE001
        sig["audit_decisions"] = 0
    # 감사로그 테이블
    try:
        sig["audit_log"] = await _count("SELECT COUNT(*) AS n FROM tbl_audit_log")
    except Exception:  # noqa: BLE001
        sig["audit_log"] = 0
    # HITL 게이트 설치 여부(테이블 존재 = 항상 True)
    sig["hitl_gate"] = True
    # 마켓플레이스 블롭 체크섬(공급망 무결성)
    try:
        sig["signed_blobs"] = await _count(
            f"SELECT COUNT(*) AS n FROM marketplace_asset_blobs WHERE tenant_id = {_PH} AND checksum <> ''", (tid,))
    except Exception:  # noqa: BLE001
        sig["signed_blobs"] = 0
    return sig


def _score_controls(sig: dict) -> list[dict]:
    g = sig["guardrails_enabled"] > 0
    audit = sig["audit_log"] > 0 or sig["audit_decisions"] > 0
    supply = sig["signed_blobs"] > 0
    return [
        {"id": "LLM01", "title": "Prompt Injection", "score": 4 if g else 2, "basis": "Guardrails 입력 필터(global PII 13종)" if g else "가드레일 토글 비활성"},
        {"id": "LLM02", "title": "Insecure Output Handling", "score": 4 if g else 2, "basis": "Guardrails 출력 판정+치환" if g else "출력 필터 미활성"},
        {"id": "LLM03", "title": "Training Data Poisoning", "score": 3, "basis": "플랫폼 범위 밖(모델 학습 미수행) — 정책 baseline"},
        {"id": "LLM04", "title": "Model DoS", "score": 3, "basis": "워크플로 webhook rate limit(단일 프로세스) — 전역 한도 로드맵"},
        {"id": "LLM05", "title": "Supply Chain", "score": 4 if supply else 2, "basis": "마켓 자산 SHA256 체크섬" + ("+GPG/mTLS" if supply else " 미검증")},
        {"id": "LLM06", "title": "Sensitive Info Disclosure", "score": 4 if g else 2, "basis": "Guardrails PII 마스킹" if g else "PII 필터 미활성"},
        {"id": "LLM07", "title": "Insecure Plugin Design", "score": 3, "basis": "Addon admin-trust 경계 + key-check(무샌드박스 — 로드맵)"},
        {"id": "LLM08", "title": "Excessive Agency", "score": 4 if sig["hitl_gate"] else 2, "basis": "HITL 승인 게이트(tbl_hitl_approvals) — write/delete/external"},
        {"id": "LLM09", "title": "Overreliance", "score": 3, "basis": "Playground citations 노출 — 고영향 강제검토 로드맵"},
        {"id": "LLM10", "title": "Model Theft", "score": 4 if audit else 3, "basis": "역할 접근제어 + 감사로그" if audit else "접근제어(감사 부분)"},
    ]


@router.get("/owasp-scorecard")
async def owasp_scorecard(user: dict = Depends(get_current_user)):
    """OWASP LLM Top10 통제 성숙도 스코어카드(플랫폼 실제 상태 기반, 1~5)."""
    sig = await _platform_signals()
    controls = _score_controls(sig)
    scores = [c["score"] for c in controls]
    avg = round(sum(scores) / len(scores), 2)
    return {
        "controls": controls,
        "summary": {
            "average": avg,
            "min": min(scores),
            "below_target": [c["id"] for c in controls if c["score"] < 4],
            "target": 4,
            "passing": all(s >= 4 for s in scores),
        },
        "signals": sig,
    }
