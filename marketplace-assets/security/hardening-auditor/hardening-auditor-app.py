"""Linux 서버 하드닝 감사 Addon — SeCuardian router_hardening.py 이식. License: Apache-2.0.

마운트: /api/addon/hardening-auditor
  GET    /status   — 플레이북 설정 요약 + 최근 보고서 (endpoint_security)
  POST   /report   — Ansible audit_hardening.yml 결과 수신 (JWT 불필요, HARDENING_WEBHOOK_ENABLED=true)
  GET    /reports  — 저장된 감사 보고서 목록
  DELETE /reports  — 저장소 초기화
"""
import datetime
import os
from collections import deque
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user

router = APIRouter(tags=["hardening"])

WEBHOOK_PATH = "/api/addon/hardening-auditor/report"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(_env(name, str(default))))
    except ValueError:
        return default


# 감사 보고서 인메모리 저장소 — maxlen 은 HARDENING_REPORTS_MAX 와 동기화
_report_store: deque = deque(maxlen=100)


def _get_report_store() -> deque:
    global _report_store
    mx = _env_int("HARDENING_REPORTS_MAX", 100)
    if _report_store.maxlen != mx:
        _report_store = deque(list(_report_store)[-mx:], maxlen=mx)
    return _report_store


def _playbook_dir() -> str:
    return _env("HARDENING_PLAYBOOK_DIR", "deploy/ansible").rstrip("/")


@router.get("/status")
async def hardening_status(_: dict = Depends(get_current_user)):
    """Ansible 하드닝 플레이북 설정 요약. Orchestrator intent: endpoint_security (L2 Endpoint)"""
    store = _get_report_store()
    latest = store[-1] if store else None
    pd = _playbook_dir()
    inv = f"{pd}/inventory/hosts.yml"
    return {
        "playbook": f"{pd}/playbooks/linux_hardening.yml",
        "audit_playbook": f"{pd}/playbooks/audit_hardening.yml",
        "webhook_enabled": _env_bool("HARDENING_WEBHOOK_ENABLED"),
        "webhook_path": WEBHOOK_PATH,
        "reports_stored": len(store),
        "reports_max": store.maxlen,
        "latest_report": {
            "hostname": latest.get("hostname"),
            "audited_at": latest.get("audited_at"),
            "overall_pass": latest.get("overall_pass"),
        } if latest else None,
        "run_hints": {
            "dry_run": f"ansible-playbook -i {inv} {pd}/playbooks/linux_hardening.yml --check --diff",
            "apply": f"ansible-playbook -i {inv} {pd}/playbooks/linux_hardening.yml",
            "audit": f"ansible-playbook -i {inv} {pd}/playbooks/audit_hardening.yml",
            "audit_and_report": (
                f"ansible-playbook -i {inv} {pd}/playbooks/audit_hardening.yml "
                f"-e report_to_secuardian=true -e secuardian_report_path={WEBHOOK_PATH}"
            ),
        },
        "env_vars": ["HARDENING_WEBHOOK_ENABLED", "HARDENING_REPORTS_MAX", "HARDENING_PLAYBOOK_DIR"],
    }


@router.post("/report", status_code=201)
async def receive_audit_report(body: dict):
    """Ansible audit_hardening.yml 결과 수신. 인증 불필요 — HARDENING_WEBHOOK_ENABLED 플래그로 제어."""
    if not _env_bool("HARDENING_WEBHOOK_ENABLED"):
        raise HTTPException(status_code=403, detail="hardening webhook disabled — set HARDENING_WEBHOOK_ENABLED=true")
    store = _get_report_store()
    body["_received_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    store.append(body)
    return {
        "accepted": True,
        "stored": len(store),
        "overall_pass": body.get("overall_pass"),
        "hostname": body.get("hostname"),
    }


@router.get("/reports")
async def list_audit_reports(
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    """저장된 감사 보고서 목록 조회."""
    store = _get_report_store()
    reports: list[Any] = list(store)[-limit:]
    return {"total": len(store), "returned": len(reports), "reports": reports}


@router.delete("/reports")
async def clear_audit_reports(_: dict = Depends(get_current_user)):
    """인메모리 감사 보고서 전체 삭제."""
    store = _get_report_store()
    count = len(store)
    store.clear()
    return {"cleared": count}
