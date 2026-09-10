"""api-vuln-scan — API 보안 취약점 스캐너 (OWASP API Top 10).

마운트 경로: /api/addon/api-vuln-scan/...
목적: 등록된 내부 API 의 OpenAPI 스펙을 OWASP API Top10 체크리스트로 정적 점검하고, 허용된 대상에 한해
      능동 스캔을 수행한다. (extra-agents 후보 C — Nettacker·burp-ai-agent·owasp-noir·owasp-top10-skills)

엔드포인트:
  GET  /status        룰/설정 요약                        (로그인)
  GET  /rules         OWASP API Top10 룰 카탈로그          (로그인)
  POST /analyze-spec  OpenAPI(JSON) 정적 점검             (로그인)
  POST /scan          허용 대상 능동 스캔(HTTP 프로브)     (supervisor/admin)

보안 원칙:
  - analyze-spec 은 인라인 JSON 정적 분석(네트워크 없음).
  - 능동 스캔 대상은 AVS_ALLOWED_HOSTS allowlist 만, http/https GET 프로브만.
  - ⚠️ from __future__ import annotations 금지.
"""
import os
import re
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["api-vuln-scan"])

_RULES = [
    {"id": "API1", "title": "BOLA(객체수준 권한)", "check": "경로에 {id} 파라미터가 있으나 보안 스킴 미적용"},
    {"id": "API2", "title": "취약한 인증", "check": "securitySchemes 미정의 또는 global security 없음"},
    {"id": "API3", "title": "과다 데이터 노출", "check": "응답 스키마에 password/token/ssn 등 민감 필드"},
    {"id": "API4", "title": "자원·속도 제한 없음", "check": "rate limit/페이지네이션 파라미터 부재"},
    {"id": "API5", "title": "기능수준 권한(BFLA)", "check": "관리형 경로(admin/delete)에 보안 스킴 미적용"},
    {"id": "API7", "title": "보안 설정 오류", "check": "http(평문) 서버 URL 사용"},
    {"id": "API8", "title": "인젝션", "check": "쿼리/경로 파라미터 검증 스키마 부재"},
]
_SENSITIVE_RE = re.compile(r"(?i)(password|passwd|secret|token|ssn|social_security|card_number|cvv|private_key)")
_ADMIN_RE = re.compile(r"(?i)(admin|internal|delete|/users?/\{)")
_HOST_RE = re.compile(r"^[A-Za-z0-9.:-]{1,255}$")


def _allowed_hosts() -> list[str]:
    return [h.strip().lower() for h in os.getenv("AVS_ALLOWED_HOSTS", "").split(",") if h.strip()]


def _finding(rule: str, where: str, detail: str) -> dict:
    return {"rule": rule, "where": where[:200], "detail": detail[:200]}


def _analyze_openapi(spec: dict) -> list[dict]:
    findings: list[dict] = []
    schemes = ((spec.get("components") or {}).get("securitySchemes")) or spec.get("securityDefinitions")
    global_sec = spec.get("security")
    if not schemes:
        findings.append(_finding("API2", "components.securitySchemes", "인증 스킴 미정의"))
    servers = spec.get("servers") or []
    for s in servers:
        if isinstance(s, dict) and str(s.get("url", "")).startswith("http://"):
            findings.append(_finding("API7", f"servers.{s.get('url')}", "평문 http 서버 URL"))

    paths = spec.get("paths") or {}
    for path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        has_id = bool(re.search(r"\{[^}]+\}", str(path)))
        for method, op in ops.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            op = op or {}
            secured = bool(op.get("security")) or bool(global_sec)
            if has_id and not secured:
                findings.append(_finding("API1", f"{method.upper()} {path}", "객체 식별 파라미터 · 보안 스킴 없음"))
            if _ADMIN_RE.search(f"{path}") and not secured:
                findings.append(_finding("API5", f"{method.upper()} {path}", "관리형 경로 · 보안 스킴 없음"))
            params = op.get("parameters") or []
            if not params and not has_id and method.lower() == "get":
                findings.append(_finding("API4", f"{method.upper()} {path}", "페이지네이션/제한 파라미터 부재"))
            # 응답 민감 필드
            for code, resp in (op.get("responses") or {}).items():
                if _SENSITIVE_RE.search(str(resp)):
                    findings.append(_finding("API3", f"{method.upper()} {path} → {code}", "응답에 민감 필드 노출 의심"))
                    break
    return findings


def _summary(findings: list[dict]) -> dict:
    by_rule: dict[str, int] = {}
    for f in findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    return {"total": len(findings), "by_rule": by_rule}


class AnalyzeSpecRequest(BaseModel):
    spec: dict[str, Any]


class ScanRequest(BaseModel):
    base_url: str
    paths: Optional[list[str]] = None


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    return {"agent": "api-vuln-scan", "rules": len(_RULES), "allowed_hosts": _allowed_hosts()}


@router.get("/rules")
async def list_rules(user: dict = Depends(get_current_user)):
    return {"rules": _RULES}


@router.post("/analyze-spec")
async def analyze_spec(body: AnalyzeSpecRequest, user: dict = Depends(get_current_user)):
    spec = body.spec
    if not isinstance(spec, dict) or not (spec.get("paths") or spec.get("openapi") or spec.get("swagger")):
        raise HTTPException(status_code=422, detail="유효한 OpenAPI/Swagger JSON 이 아닙니다.")
    findings = _analyze_openapi(spec)
    return {"summary": _summary(findings), "findings": findings}


@router.post("/scan")
async def scan(body: ScanRequest, user: dict = Depends(require_role("supervisor", "admin"))):
    """허용 호스트에 한해 경로별 HTTP 프로브(상태코드·인증요구 확인)."""
    parsed = urlparse((body.base_url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname or not _HOST_RE.match(parsed.hostname):
        raise HTTPException(status_code=400, detail="http/https base_url 만 허용됩니다.")
    allow = _allowed_hosts()
    if not allow:
        raise HTTPException(status_code=403, detail="AVS_ALLOWED_HOSTS 미설정 — 스캔 대상 allowlist 를 등록하세요.")
    if parsed.hostname.lower() not in allow:
        raise HTTPException(status_code=403, detail=f"대상 호스트 {parsed.hostname} 은 allowlist 에 없습니다.")
    try:
        import httpx
    except ImportError:
        raise HTTPException(status_code=503, detail="httpx 미설치 — 능동 스캔 불가")

    probe_paths = (body.paths or ["/"])[:50]
    results = []
    base = f"{parsed.scheme}://{parsed.netloc}"
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=False) as client:
            for p in probe_paths:
                if not p.startswith("/"):
                    p = "/" + p
                try:
                    r = await client.get(base + p)
                    results.append({"path": p, "status": r.status_code, "auth_required": r.status_code in (401, 403)})
                except Exception as exc:  # noqa: BLE001
                    results.append({"path": p, "error": str(exc)[:120]})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"스캔 실패: {str(exc)[:200]}")
    unauth = [r for r in results if r.get("status") == 200]
    return {"base_url": base, "probed": len(results), "results": results, "unauthenticated_200": len(unauth)}
