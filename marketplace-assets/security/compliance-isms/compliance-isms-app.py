"""ISMS-P 자동화 증거 수집 Addon — SeCuardian router_isms.py 이식.

역할: ISMS-P 통제항목별 증거 자동 수집 / 감사 보고서 생성 (Cross-cutting, compliance_report)
연동: 다른 보안 Addon 의 /status 엔드포인트를 HTTP 로 호출 (Addon 간 파이썬 import 금지 규칙 준수)

마운트: /api/addon/compliance-isms
  GET  /status    — 증거 수집 현황
  POST /evidence  — 통제항목별 증거 수집 실행
  GET  /evidence  — 수집 증거 목록
  POST /report    — 감사 보고서 생성
  GET  /reports   — 생성된 보고서 목록
"""
import datetime
import os
from collections import deque
from typing import Optional

import httpx
from fastapi import APIRouter, Body, Depends, Query, Request

from app.core.deps import get_current_user

router = APIRouter(tags=["isms"])

_evidence_store: deque = deque(maxlen=500)
_report_store: deque = deque(maxlen=50)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _internal_base() -> str:
    return _env("ISMS_INTERNAL_BASE_URL", f"http://localhost:{_env('PORT', '8200')}").rstrip("/")


def _doc_root() -> str:
    return _env("ISMS_DOC_ROOT", os.getcwd())


# ISMS-P 통제항목 — evidence-mapping.yaml 기반 코드 상수.
# api 는 Addon 마운트 경로(/api/addon/{key}/...) — 해당 Addon 미설치 시 api_status=NOT_INSTALLED(404).
_CONTROLS = [
    {"id": "2.1.1", "title": "정보보호 정책 승인·공표", "api": None, "doc": "COMPLIANCE.md"},
    {"id": "2.5.2", "title": "접근통제 IAM/SSO", "api": "/api/addon/keycloak-monitor/status", "doc": None},
    {"id": "2.5.3", "title": "사용자 인증 MFA", "api": "/api/addon/keycloak-monitor/status", "doc": None},
    {"id": "2.6.2", "title": "세션 관리 — 권한계정 녹화", "api": "/api/addon/teleport-pam/sessions", "doc": None},
    {"id": "2.7.1", "title": "암호화 — Vault PKI/TLS", "api": "/api/addon/vault-monitor/status", "doc": None},
    {"id": "2.8.3", "title": "개인정보 가명처리 DLP", "api": "/api/addon/neosync-dlp/status", "doc": None},
    {"id": "2.9.1", "title": "시크릿 누출 방지 CI/CD", "api": None, "doc": ".github/workflows/secret-scan.yml"},
    {"id": "2.11.1", "title": "보안 사고 대응 SOAR", "api": "/api/addon/shuffle-soar/status", "doc": None},
    {"id": "2.11.2", "title": "취약점 관리 VASCA", "api": "/api/addon/vasca-cve/status", "doc": None},
    {"id": "2.12.1", "title": "SIEM 로그 수집·보존", "api": "/api/addon/wazuh-siem/status", "doc": None},
]


@router.get("/status")
async def isms_status(_: dict = Depends(get_current_user)):
    """ISMS-P 증거 수집 현황. Orchestrator intent: compliance_report (Cross-cutting)"""
    return {
        "framework": "ISMS-P 2023",
        "controls_total": len(_CONTROLS),
        "evidence_collected": len(_evidence_store),
        "reports_generated": len(_report_store),
        "auto_collect_enabled": _env_bool("ISMS_AUTO_COLLECT"),
        "report_dir": _env("ISMS_REPORT_DIR", "reports/isms"),
        "internal_base_url": _internal_base(),
        "doc_root": _doc_root(),
        "controls": [{"id": c["id"], "title": c["title"], "api": c["api"], "doc": c["doc"]} for c in _CONTROLS],
        "env_vars": ["ISMS_INTERNAL_BASE_URL", "ISMS_DOC_ROOT", "ISMS_AUTO_COLLECT", "ISMS_REPORT_DIR"],
    }


@router.post("/evidence", status_code=202)
async def collect_evidence(
    request: Request,
    _: dict = Depends(get_current_user),
    control_ids: list = Body(default=[], description="수집할 통제항목 ID 목록 (빈 목록=전체)"),
):
    """통제항목별 증거 수집 — 연동 Addon /status 호출(호출자 JWT 전달) + 문서 존재 확인."""
    targets = [c for c in _CONTROLS if not control_ids or c["id"] in control_ids]
    collected_at = datetime.datetime.utcnow().isoformat() + "Z"
    auth_header = request.headers.get("authorization", "")
    results: list = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for ctrl in targets:
            evidence: dict = {"control_id": ctrl["id"], "title": ctrl["title"], "collected_at": collected_at}
            if ctrl["api"]:
                evidence["api_url"] = ctrl["api"]
                try:
                    resp = await client.get(
                        f"{_internal_base()}{ctrl['api']}",
                        headers={"Authorization": auth_header} if auth_header else {},
                    )
                    if resp.status_code == 404:
                        evidence["api_status"] = "NOT_INSTALLED"
                    else:
                        evidence["api_status"] = "OK" if resp.is_success else f"ERROR:{resp.status_code}"
                except Exception as exc:
                    evidence["api_status"] = f"UNREACHABLE: {type(exc).__name__}"
            if ctrl["doc"]:
                evidence["doc_path"] = ctrl["doc"]
                evidence["doc_exists"] = os.path.isfile(os.path.join(_doc_root(), ctrl["doc"]))
            results.append(evidence)
            _evidence_store.append(evidence)

    return {"accepted": True, "collected": len(results), "results": results}


@router.get("/evidence")
async def list_evidence(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=500),
    control_id: Optional[str] = Query(default=None),
):
    """수집된 증거 목록 — 최신순."""
    items = list(reversed(list(_evidence_store)))
    if control_id:
        items = [e for e in items if e.get("control_id") == control_id]
    items = items[:limit]
    return {"total": len(_evidence_store), "returned": len(items), "evidence": items}


@router.post("/report", status_code=202)
async def generate_report(
    _: dict = Depends(get_current_user),
    payload: dict = Body(default={}),
):
    """ISMS-P 감사 보고서 생성 — 수집 증거 기반 통제항목별 준수 요약. Orchestrator intent: compliance_report"""
    generated_at = datetime.datetime.utcnow().isoformat() + "Z"
    evidence_list = list(_evidence_store)

    control_summary: list = []
    for ctrl in _CONTROLS:
        ctrl_evidence = [e for e in evidence_list if e.get("control_id") == ctrl["id"]]
        if ctrl_evidence:
            latest = sorted(ctrl_evidence, key=lambda x: x.get("collected_at", ""))[-1]
            api_ok = latest.get("api_status") == "OK"
            doc_ok = latest.get("doc_exists", True)
            status = "COMPLIANT" if (api_ok or "api_status" not in latest) and doc_ok else "NON_COMPLIANT"
        else:
            status = "NOT_COLLECTED"
        control_summary.append({"id": ctrl["id"], "title": ctrl["title"], "status": status})

    compliant = sum(1 for c in control_summary if c["status"] == "COMPLIANT")
    report = {
        "id": f"ISMS-RPT-{len(_report_store) + 1:04d}",
        "framework": "ISMS-P 2023",
        "generated_at": generated_at,
        "requester": payload.get("requester", "secuardian"),
        "controls_total": len(_CONTROLS),
        "compliant": compliant,
        "non_compliant": sum(1 for c in control_summary if c["status"] == "NON_COMPLIANT"),
        "not_collected": sum(1 for c in control_summary if c["status"] == "NOT_COLLECTED"),
        "compliance_rate": round(compliant / len(_CONTROLS) * 100, 1),
        "summary": control_summary,
        "retention_years": 5,
    }
    _report_store.append(report)
    return {"accepted": True, "report_id": report["id"], "compliance_rate": report["compliance_rate"], "report": report}


@router.get("/reports")
async def list_reports(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=50),
):
    """생성된 보고서 목록 — 최신순."""
    items = list(reversed(list(_report_store)))[:limit]
    return {"total": len(_report_store), "returned": len(items), "reports": items}
