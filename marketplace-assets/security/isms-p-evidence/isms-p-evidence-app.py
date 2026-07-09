"""ISMS-P 자동화 증거 수집 — ADDON 판 (isms-p-evidence).

내장 라우터 app/routers/router_isms.py (E22 T22-1) 의 ADDON 패키징.
역할: ISMS-P 통제항목별 증거 자동 수집 / 감사 보고서 생성
연동: Wazuh + Keycloak + Vault + Teleport + VASCA + Neosync + SOAR + DFIR

로더가 /api/addon/isms-p-evidence prefix 로 마운트한다.
"""
import datetime
import os
from collections import deque

import httpx
from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user

router = APIRouter(tags=["isms-p-evidence"])

ISMS_AUTO_COLLECT = os.getenv("ISMS_AUTO_COLLECT", "false").lower() == "true"
ISMS_REPORT_DIR = os.getenv("ISMS_REPORT_DIR", "logs/isms-reports")
BACKEND_BASE = os.getenv("ISMS_BACKEND_BASE", "http://localhost:8200")

_evidence_store: deque[dict] = deque(maxlen=500)
_report_store: deque[dict] = deque(maxlen=50)

# ISMS-P 통제항목 — evidence-mapping.yaml 대응 코드 상수
_CONTROLS = [
    {"id": "2.1.1", "title": "정보보호 정책 승인·공표",   "api": None,                     "doc": "docs/COMPLIANCE.md"},
    {"id": "2.5.2", "title": "접근통제 IAM/SSO",          "api": "/api/keycloak/status",   "doc": None},
    {"id": "2.5.3", "title": "사용자 인증 MFA",            "api": "/api/keycloak/status",   "doc": None},
    {"id": "2.6.2", "title": "세션 관리 — 권한계정 녹화", "api": "/api/teleport/sessions", "doc": None},
    {"id": "2.7.1", "title": "암호화 — Vault PKI/TLS",     "api": "/api/vault/status",      "doc": None},
    {"id": "2.8.3", "title": "개인정보 가명처리 DLP",      "api": "/api/neosync/status",    "doc": None},
    {"id": "2.9.1", "title": "시크릿 누출 방지 CI/CD",     "api": None,                     "doc": ".github/workflows/secret-scan.yml"},
    {"id": "2.11.1", "title": "보안 사고 대응 SOAR",       "api": "/api/soar/status",       "doc": None},
    {"id": "2.11.2", "title": "취약점 관리 VASCA",         "api": "/api/vasca/status",      "doc": None},
    {"id": "2.12.1", "title": "SIEM 로그 수집·보존",       "api": "/api/wazuh/status",      "doc": None},
]


@router.get("/status")
async def isms_status(_: dict = Depends(get_current_user)):
    """ISMS-P 증거 수집 현황 조회."""
    return {
        "framework": "ISMS-P 2023",
        "controls_total": len(_CONTROLS),
        "evidence_collected": len(_evidence_store),
        "reports_generated": len(_report_store),
        "auto_collect_enabled": ISMS_AUTO_COLLECT,
        "report_dir": ISMS_REPORT_DIR,
        "evidence_mapping": "deploy/config/isms/evidence-mapping.yaml",
        "controls": [{"id": c["id"], "title": c["title"]} for c in _CONTROLS],
    }


@router.post("/evidence", status_code=202)
async def collect_evidence(
    _: dict = Depends(get_current_user),
    control_ids: list[str] = Body(default=[], description="수집할 통제항목 ID 목록 (빈 목록=전체)"),
):
    """ISMS-P 통제항목별 증거 수집 실행 — 내부 API 상태 + 문서 존재 확인."""
    targets = [c for c in _CONTROLS if not control_ids or c["id"] in control_ids]
    collected_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for ctrl in targets:
            evidence: dict = {
                "control_id": ctrl["id"],
                "title": ctrl["title"],
                "collected_at": collected_at,
            }
            if ctrl["api"]:
                try:
                    resp = await client.get(f"{BACKEND_BASE}{ctrl['api']}")
                    evidence["api_status"] = "OK" if resp.is_success else "ERROR"
                    evidence["api_url"] = ctrl["api"]
                except Exception as exc:
                    evidence["api_status"] = f"UNREACHABLE: {type(exc).__name__}"
            if ctrl["doc"]:
                evidence["doc_exists"] = os.path.isfile(ctrl["doc"])
                evidence["doc_path"] = ctrl["doc"]
            results.append(evidence)
            _evidence_store.append(evidence)

    return {"accepted": True, "collected": len(results), "results": results}


@router.get("/evidence")
async def list_evidence(
    _: dict = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=500),
    control_id: str | None = Query(default=None),
):
    """수집된 증거 목록 조회 — 최신순."""
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
    """ISMS-P 감사 보고서 생성 — 수집 증거 기반 통제항목별 준수 현황 요약."""
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    evidence_list = list(_evidence_store)

    control_summary: list[dict] = []
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
        "id": f"ISMS-RPT-{len(_report_store)+1:04d}",
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
    return {
        "accepted": True,
        "report_id": report["id"],
        "compliance_rate": report["compliance_rate"],
        "report": report,
    }
