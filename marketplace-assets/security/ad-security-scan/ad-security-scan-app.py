"""ad-security-scan — Active Directory 보안 점검 에이전트.

마운트 경로: /api/addon/ad-security-scan/...
목적: AD 환경의 취약 설정(Kerberoasting 대상·AS-REP roasting·취약 ACL·비만료 암호·과도한 위임)을 점검한다.
      (extra-agents 후보 F — ADScanPro·NetSPI/AD-PathFinder) 1차는 수집 데이터(JSON) 정적 분석 + 라이브 수집 래핑.

엔드포인트:
  GET  /status   룰/도구 요약                                (로그인)
  GET  /rules    점검 룰 카탈로그                            (로그인)
  POST /analyze  수집된 AD 객체(JSON) 정적 취약설정 점검     (로그인)
  POST /scan     라이브 수집(도구 래핑, 대상 allowlist)      (supervisor/admin)

보안 원칙:
  - analyze 는 수집 데이터 정적 분석(네트워크 없음).
  - 라이브 수집(scan)은 supervisor/admin + ADS_ALLOWED_DOMAINS + 도구(bloodhound-python) 미설치 시 503.
  - ⚠️ from __future__ import annotations 금지.
"""
import os
import re
import shutil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["ad-security-scan"])

_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9](-?[A-Za-z0-9])*\.)+[A-Za-z]{2,}$")

_RULES = [
    {"id": "AD-01", "severity": "high", "title": "Kerberoasting 대상", "desc": "servicePrincipalName 보유 사용자 계정(비 gMSA)"},
    {"id": "AD-02", "severity": "high", "title": "AS-REP Roasting", "desc": "DONT_REQ_PREAUTH 플래그 계정"},
    {"id": "AD-03", "severity": "medium", "title": "비만료 암호", "desc": "DONT_EXPIRE_PASSWORD 플래그 계정"},
    {"id": "AD-04", "severity": "high", "title": "무제약 위임", "desc": "TRUSTED_FOR_DELEGATION 컴퓨터/사용자"},
    {"id": "AD-05", "severity": "medium", "title": "취약 ACL", "desc": "일반 사용자에게 GenericAll/WriteDacl 권한"},
    {"id": "AD-06", "severity": "low", "title": "오래된 암호", "desc": "pwdLastSet 이 180일 초과"},
]
_RULE_SEV = {r["id"]: r["severity"] for r in _RULES}

# userAccountControl 비트
_UAC = {"DONT_EXPIRE_PASSWORD": 0x10000, "TRUSTED_FOR_DELEGATION": 0x80000, "DONT_REQ_PREAUTH": 0x400000}


def _allowed_domains() -> list[str]:
    return [d.strip().lower() for d in os.getenv("ADS_ALLOWED_DOMAINS", "").split(",") if d.strip()]


def _finding(rule: str, obj: str, detail: str) -> dict:
    return {"rule": rule, "severity": _RULE_SEV.get(rule, "low"), "object": obj[:200], "detail": detail[:200]}


def _analyze_objects(objects: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for o in objects:
        if not isinstance(o, dict):
            continue
        name = str(o.get("sAMAccountName") or o.get("name") or o.get("dn") or "?")
        uac = 0
        try:
            uac = int(o.get("userAccountControl") or 0)
        except (TypeError, ValueError):
            uac = 0
        spns = o.get("servicePrincipalName") or o.get("spn") or []
        is_user = str(o.get("objectClass", "user")).lower().find("computer") < 0
        if spns and is_user and not str(name).endswith("$"):
            findings.append(_finding("AD-01", name, f"SPN {spns if isinstance(spns, str) else ','.join(spns)}"))
        if uac & _UAC["DONT_REQ_PREAUTH"]:
            findings.append(_finding("AD-02", name, "DONT_REQ_PREAUTH"))
        if uac & _UAC["DONT_EXPIRE_PASSWORD"]:
            findings.append(_finding("AD-03", name, "DONT_EXPIRE_PASSWORD"))
        if uac & _UAC["TRUSTED_FOR_DELEGATION"]:
            findings.append(_finding("AD-04", name, "TRUSTED_FOR_DELEGATION"))
        acl = o.get("acl") or o.get("aces") or []
        if isinstance(acl, list):
            for ace in acl:
                if isinstance(ace, dict) and str(ace.get("right", "")).lower() in ("genericall", "writedacl", "writeowner"):
                    if str(ace.get("principal_tier", "")).lower() in ("", "user", "low"):
                        findings.append(_finding("AD-05", name, f"{ace.get('right')} ← {ace.get('principal')}"))
        try:
            if int(o.get("pwdLastSetDays", 0)) > 180:
                findings.append(_finding("AD-06", name, f"pwdLastSet {o.get('pwdLastSetDays')}일 전"))
        except (TypeError, ValueError):
            pass
    return findings


def _summary(findings: list[dict]) -> dict:
    c = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        c[f["severity"]] = c.get(f["severity"], 0) + 1
    risk = "high" if c["high"] else "medium" if c["medium"] else "low" if c["low"] else "clean"
    return {"risk": risk, "counts": c, "total": len(findings)}


class AnalyzeRequest(BaseModel):
    objects: list[dict[str, Any]]


class ScanRequest(BaseModel):
    domain: str


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    return {
        "agent": "ad-security-scan",
        "rules": len(_RULES),
        "allowed_domains": _allowed_domains(),
        "collector": bool(shutil.which("bloodhound-python") or shutil.which("bloodhound.py")),
    }


@router.get("/rules")
async def list_rules(user: dict = Depends(get_current_user)):
    return {"rules": _RULES}


@router.post("/analyze")
async def analyze(body: AnalyzeRequest, user: dict = Depends(get_current_user)):
    """수집된 AD 객체(JSON) 배열을 정적 점검한다."""
    if not isinstance(body.objects, list) or not body.objects:
        raise HTTPException(status_code=422, detail="objects 는 비어있지 않은 배열이어야 합니다.")
    if len(body.objects) > 100000:
        raise HTTPException(status_code=413, detail="객체 수 상한 초과")
    findings = _analyze_objects(body.objects)
    return {"analyzed": len(body.objects), "summary": _summary(findings), "findings": findings}


@router.post("/scan")
async def scan(body: ScanRequest, user: dict = Depends(require_role("supervisor", "admin"))):
    """라이브 AD 수집(bloodhound-python 래핑). 대상 allowlist + 도구 필요."""
    domain = (body.domain or "").strip().lower()
    if not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=400, detail=f"잘못된 도메인: {domain!r}")
    allow = _allowed_domains()
    if not allow:
        raise HTTPException(status_code=403, detail="ADS_ALLOWED_DOMAINS 미설정 — 대상 allowlist 를 등록하세요.")
    if domain not in allow:
        raise HTTPException(status_code=403, detail=f"대상 {domain} 은 allowlist 에 없습니다.")
    collector = shutil.which("bloodhound-python") or shutil.which("bloodhound.py")
    if not collector:
        raise HTTPException(
            status_code=503,
            detail="라이브 수집 도구 미설치(bloodhound-python). 오프라인 수집 후 /analyze 로 정적 점검하세요.",
        )
    # 라이브 수집은 도메인 자격증명·격리 환경이 필요 — 1차는 안전하게 미수행 안내(mock-first, PRD §3).
    raise HTTPException(
        status_code=501,
        detail="라이브 AD 수집은 도메인 자격증명·격리 실행 환경 구성 후 활성화됩니다(1차 mock-first). 수집 데이터는 /analyze 로 점검하세요.",
    )
