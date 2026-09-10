"""agentic-threat-model — 자사 AI 에이전트/MCP 위협 모델링 + 런타임 보안 스캔 에이전트.

마운트 경로: /api/addon/agentic-threat-model/...
목적: SeCuardian 자신을 포함한 MCP 서버·에이전트·스킬 설정을 스캔해 과도한 권한·시크릿 노출·
      프롬프트 인젝션 취약점을 위협 모델(표)로 산출한다. (extra-agents 후보 B, §1.6/§1.15 agentseal·hackagent)

엔드포인트:
  GET  /status       룰셋/능력 요약                          (로그인)
  GET  /rules        위협 룰 카탈로그                        (로그인)
  POST /scan-config  MCP/에이전트 설정 JSON 정적 위협모델     (로그인)
  POST /scan-mcp     라이브 MCP 서버 tool-poisoning 감사      (supervisor/admin)

보안 원칙 (정적 분석 + 읽기 전용 프로브):
  - 외부 네트워크는 scan-mcp 만 (HTTP GET, 타임아웃·크기 제한). scheme http/https 만 허용.
  - 설정 입력은 인라인 JSON (파일 접근 없음) — 임의 경로/명령 실행 없음.
  - 라이브 프로브는 supervisor/admin.
  - ⚠️ from __future__ import annotations 금지 (동적 로더 pydantic 이슈)
"""
import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["agentic-threat-model"])

_MAX_TOOLS = 500
_MAX_MCP_BYTES = 256 * 1024
_URL_RE = re.compile(r"^https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{1,2048}$")

# 시크릿·인젝션 지표 정규식 (결정적 부분판정)
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|passwd|password|bearer|aws_access|private[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9/_+.-]{8,}"
)
_INJECTION_RE = re.compile(r"(?i)(ignore (all )?previous|system prompt|jailbreak|exfiltrat|reverse shell|curl .*\| *sh)")
_DANGEROUS_TOOL_RE = re.compile(r"(?i)(exec|shell|eval|delete|drop|sudo|rm -rf|write_file|http_request|browser)")

# 위협 룰 카탈로그 (룰ID·심각도·설명)
_RULES = [
    {"id": "TM-01", "severity": "high", "title": "하드코딩 시크릿", "desc": "설정에 API 키/토큰/비밀번호가 평문 노출"},
    {"id": "TM-02", "severity": "high", "title": "과도한 도구 권한", "desc": "exec/shell/delete/write 등 고위험 도구를 승인 게이트 없이 노출"},
    {"id": "TM-03", "severity": "medium", "title": "프롬프트 인젝션 취약 프롬프트", "desc": "시스템/도구 설명에 인젝션 유발·탈취 패턴 존재"},
    {"id": "TM-04", "severity": "medium", "title": "무인증 MCP 엔드포인트", "desc": "MCP 서버 URL 에 인증 헤더/토큰 구성 없음"},
    {"id": "TM-05", "severity": "low", "title": "와일드카드 권한", "desc": "scopes/permissions 에 '*' 등 광범위 허용"},
    {"id": "TM-06", "severity": "high", "title": "MCP tool-poisoning 의심", "desc": "라이브 도구 설명에 은닉 지시/데이터 유출 유도"},
]
_RULE_SEV = {r["id"]: r["severity"] for r in _RULES}


class ScanConfigRequest(BaseModel):
    config: dict[str, Any]
    label: Optional[str] = None


class ScanMcpRequest(BaseModel):
    url: str


def _finding(rule_id: str, where: str, evidence: str) -> dict:
    return {
        "rule": rule_id,
        "severity": _RULE_SEV.get(rule_id, "low"),
        "where": where[:200],
        "evidence": (evidence or "")[:300],
    }


def _walk_strings(obj: Any, path: str = "$"):
    """설정 트리를 순회하며 (경로, 키, 문자열값) 방출."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def _analyze_config(config: dict) -> list[dict]:
    findings: list[dict] = []
    # 문자열 전수 검사 — 시크릿/인젝션/와일드카드
    for path, val in _walk_strings(config):
        if _SECRET_RE.search(f"{path.split('.')[-1]}={val}") or _SECRET_RE.search(val):
            findings.append(_finding("TM-01", path, val))
        if _INJECTION_RE.search(val):
            findings.append(_finding("TM-03", path, val))
        if val.strip() == "*" or val.strip().endswith(":*") or val.strip() == "all":
            findings.append(_finding("TM-05", path, val))
    # 도구 목록 — 고위험 도구 + 승인 게이트 여부
    tools = config.get("tools") or config.get("mcp_tools") or []
    if isinstance(tools, list):
        for i, t in enumerate(tools[:_MAX_TOOLS]):
            name = (t.get("name") if isinstance(t, dict) else str(t)) or ""
            approves = bool(isinstance(t, dict) and (t.get("require_approval") or t.get("human_approval")))
            if _DANGEROUS_TOOL_RE.search(str(name)) and not approves:
                findings.append(_finding("TM-02", f"tools[{i}].{name}", "고위험 도구 · 승인 게이트 없음"))
    # MCP 서버 — 인증 구성 여부
    servers = config.get("mcpServers") or config.get("mcp_servers") or {}
    if isinstance(servers, dict):
        for sname, sconf in servers.items():
            blob = str(sconf).lower()
            if not any(k in blob for k in ("authorization", "token", "apikey", "api_key", "header", "bearer")):
                findings.append(_finding("TM-04", f"mcpServers.{sname}", "인증 헤더/토큰 미구성"))
    return findings


def _score(findings: list[dict]) -> dict:
    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    risk = "critical" if counts["high"] >= 3 else "high" if counts["high"] else "medium" if counts["medium"] else "low" if counts["low"] else "clean"
    return {"risk": risk, "counts": counts, "total": len(findings)}


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    return {
        "agent": "agentic-threat-model",
        "modes": ["static:scan-config", "runtime:scan-mcp"],
        "rules": len(_RULES),
        "max_tools": _MAX_TOOLS,
        "network": "scan-mcp only (http/https GET)",
    }


@router.get("/rules")
async def list_rules(user: dict = Depends(get_current_user)):
    return {"rules": _RULES}


@router.post("/scan-config")
async def scan_config(body: ScanConfigRequest, user: dict = Depends(get_current_user)):
    """MCP/에이전트 설정 JSON 을 정적 분석해 위협모델을 산출한다."""
    if not isinstance(body.config, dict) or not body.config:
        raise HTTPException(status_code=422, detail="config 는 비어있지 않은 JSON 객체여야 합니다.")
    findings = _analyze_config(body.config)
    return {"label": body.label, "summary": _score(findings), "findings": findings}


@router.post("/scan-mcp")
async def scan_mcp(body: ScanMcpRequest, user: dict = Depends(require_role("supervisor", "admin"))):
    """라이브 MCP 서버의 tools/list 를 조회해 tool-poisoning 지표를 감사한다."""
    url = (body.url or "").strip()
    if not _URL_RE.match(url):
        raise HTTPException(status_code=400, detail="http/https URL 만 허용됩니다.")
    try:
        import httpx  # 플랫폼 기본 의존성
    except ImportError:
        raise HTTPException(status_code=503, detail="httpx 미설치 — 런타임 MCP 프로브 불가")

    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"MCP 서버 접속 실패: {str(exc)[:200]}")
    if len(resp.content or b"") > _MAX_MCP_BYTES:
        raise HTTPException(status_code=413, detail="MCP 응답이 너무 큽니다.")
    try:
        data = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="MCP 응답이 JSON 이 아닙니다.")

    tools = ((data.get("result") or {}).get("tools")) if isinstance(data, dict) else None
    findings: list[dict] = []
    if isinstance(tools, list):
        for i, t in enumerate(tools[:_MAX_TOOLS]):
            desc = str((t.get("description") if isinstance(t, dict) else "") or "")
            name = str((t.get("name") if isinstance(t, dict) else "") or "")
            if _INJECTION_RE.search(desc):
                findings.append(_finding("TM-06", f"tools[{i}].{name}", desc))
            if _DANGEROUS_TOOL_RE.search(name):
                findings.append(_finding("TM-02", f"tools[{i}].{name}", "고위험 도구 노출"))
    return {"url": url, "tool_count": len(tools or []), "summary": _score(findings), "findings": findings}
