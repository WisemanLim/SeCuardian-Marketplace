"""soc-intel-fusion — 위협 인텔리전스 통합 조회 에이전트.

마운트 경로: /api/addon/soc-intel-fusion/...
목적: CVE 식별자를 받아 NVD(CVE)·FIRST(EPSS)·CISA(KEV) 를 통합 조회하고 위험도를 융합한다.
      (extra-agents 후보 E — cve-mcp-server·IntelOwl·nmap-vulners) vasca-cve(자산 CVE)·agentic-soc 보완.

엔드포인트:
  GET  /status   소스 가용성 요약                        (로그인)
  GET  /sources  통합 소스 카탈로그                      (로그인)
  POST /lookup   CVE → CVE+EPSS+KEV 융합 조회            (로그인)

보안 원칙:
  - 외부 조회는 공개 위협 인텔 API(GET)만. SIF_OFFLINE=1 또는 httpx 미설치 시 오프라인(구조만 반환).
  - CVE ID 정규식 검증. ⚠️ from __future__ import annotations 금지.
"""
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user

router = APIRouter(tags=["soc-intel-fusion"])

_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,19}$", re.IGNORECASE)
_TIMEOUT = 8.0
_SOURCES = [
    {"id": "nvd", "name": "NVD CVE", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0", "provides": "CVSS·설명"},
    {"id": "epss", "name": "FIRST EPSS", "url": "https://api.first.org/data/v1/epss", "provides": "악용확률(EPSS)"},
    {"id": "kev", "name": "CISA KEV", "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", "provides": "알려진 악용 여부"},
]


def _offline() -> bool:
    if os.getenv("SIF_OFFLINE", "").strip() in ("1", "true", "yes"):
        return True
    try:
        import httpx  # noqa: F401
        return False
    except ImportError:
        return True


class LookupRequest(BaseModel):
    cve: str


def _fuse(cvss: Optional[float], epss: Optional[float], in_kev: bool) -> dict:
    # 융합 우선순위: KEV(악용중) > 높은 EPSS > 높은 CVSS
    if in_kev:
        prio = "critical"
    elif epss is not None and epss >= 0.5:
        prio = "high"
    elif cvss is not None and cvss >= 9.0:
        prio = "high"
    elif cvss is not None and cvss >= 7.0:
        prio = "medium"
    else:
        prio = "low"
    return {"priority": prio, "cvss": cvss, "epss": epss, "in_kev": in_kev}


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    return {"agent": "soc-intel-fusion", "offline": _offline(), "sources": [s["id"] for s in _SOURCES]}


@router.get("/sources")
async def list_sources(user: dict = Depends(get_current_user)):
    return {"sources": _SOURCES, "offline": _offline()}


@router.post("/lookup")
async def lookup(body: LookupRequest, user: dict = Depends(get_current_user)):
    cve = (body.cve or "").strip().upper()
    if not _CVE_RE.match(cve):
        raise HTTPException(status_code=400, detail="CVE-YYYY-NNNN 형식이 아닙니다.")

    if _offline():
        return {
            "cve": cve,
            "offline": True,
            "note": "오프라인 모드 — 외부 위협 인텔 조회 불가. SIF_OFFLINE 해제 + httpx 필요.",
            "fusion": _fuse(None, None, False),
        }

    import httpx
    cvss: Optional[float] = None
    epss: Optional[float] = None
    in_kev = False
    errors: dict[str, str] = {}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # NVD
            try:
                r = await client.get(_SOURCES[0]["url"], params={"cveId": cve})
                vulns = (r.json() or {}).get("vulnerabilities") or []
                if vulns:
                    metrics = (((vulns[0].get("cve") or {}).get("metrics")) or {})
                    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                        if metrics.get(key):
                            cvss = float(metrics[key][0]["cvssData"]["baseScore"])
                            break
            except Exception as exc:  # noqa: BLE001
                errors["nvd"] = str(exc)[:120]
            # EPSS
            try:
                r = await client.get(_SOURCES[1]["url"], params={"cve": cve})
                data = (r.json() or {}).get("data") or []
                if data:
                    epss = float(data[0].get("epss"))
            except Exception as exc:  # noqa: BLE001
                errors["epss"] = str(exc)[:120]
            # KEV
            try:
                r = await client.get(_SOURCES[2]["url"])
                kev = (r.json() or {}).get("vulnerabilities") or []
                in_kev = any(str(v.get("cveID", "")).upper() == cve for v in kev)
            except Exception as exc:  # noqa: BLE001
                errors["kev"] = str(exc)[:120]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"위협 인텔 조회 실패: {str(exc)[:200]}")

    return {"cve": cve, "offline": False, "fusion": _fuse(cvss, epss, in_kev), "errors": errors or None}
