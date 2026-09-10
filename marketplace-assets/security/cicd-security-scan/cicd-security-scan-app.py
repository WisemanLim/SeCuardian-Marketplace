"""cicd-security-scan — CI/CD 파이프라인(GitHub Actions/GitLab CI) 정적 보안 감사.

마운트 경로: /api/addon/cicd-security-scan/...
목적: 자사 워크플로 정의를 정적 분석해 오설정(pwn-request, 스크립트 인젝션, 셀프호스트 러너 노출,
      과도한 권한, 하드코딩 시크릿, 미고정 액션)을 감사한다. (extra-agents 후보 G — gato-x 정적 모드)

엔드포인트:
  GET  /status         룰 요약                              (로그인)
  GET  /rules          룰 카탈로그                          (로그인)
  POST /scan-workflows 워크플로 YAML(들) 정적 감사          (로그인)

보안 원칙:
  - 인라인 텍스트만 분석(파일 접근·네트워크 없음). PyYAML 있으면 파싱, 없으면 정규식 폴백.
  - 읽기 전용 정적 분석 — 특권 불필요. ⚠️ from __future__ import annotations 금지.
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user

router = APIRouter(tags=["cicd-security-scan"])

_MAX_FILES = 100
_MAX_BYTES = 256 * 1024

_RULES = [
    {"id": "CI-01", "severity": "high", "title": "pwn-request", "desc": "pull_request_target + 신뢰 못 할 체크아웃 조합"},
    {"id": "CI-02", "severity": "high", "title": "스크립트 인젝션", "desc": "run: 에 ${{ github.event.* }} 신뢰 못 할 입력 직접 삽입"},
    {"id": "CI-03", "severity": "medium", "title": "셀프호스트 러너 노출", "desc": "public 트리거 + self-hosted runner"},
    {"id": "CI-04", "severity": "medium", "title": "과도한 권한", "desc": "permissions: write-all 또는 전역 write"},
    {"id": "CI-05", "severity": "high", "title": "하드코딩 시크릿", "desc": "워크플로에 평문 토큰/키"},
    {"id": "CI-06", "severity": "low", "title": "미고정 액션", "desc": "uses: 가 SHA 아닌 태그/브랜치 참조(@main, @v1)"},
    {"id": "CI-07", "severity": "medium", "title": "curl | sh 실행", "desc": "원격 스크립트 파이프 실행"},
]
_RULE_SEV = {r["id"]: r["severity"] for r in _RULES}

_UNTRUSTED_RE = re.compile(r"\$\{\{\s*github\.event\.(pull_request\.title|pull_request\.body|issue\.title|issue\.body|comment\.body|head_ref|pull_request\.head\.ref)")
_SECRET_RE = re.compile(r"(?i)(ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|(api[_-]?key|token|password)\s*[:=]\s*['\"][A-Za-z0-9/_+.-]{12,}['\"])")
_UNPINNED_RE = re.compile(r"uses:\s*[\w.\-/]+@(?:v?\d[\w.\-]*|main|master|latest)\b")
_CURLSH_RE = re.compile(r"curl\s+[^\n|]*\|\s*(sudo\s+)?(ba)?sh")


def _finding(rule: str, where: str, evidence: str) -> dict:
    return {"rule": rule, "severity": _RULE_SEV.get(rule, "low"), "where": where[:120], "evidence": (evidence or "")[:200]}


def _scan_one(name: str, content: str) -> list[dict]:
    if len(content.encode("utf-8", "ignore")) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"{name}: 워크플로가 너무 큽니다.")
    low = content.lower()
    findings: list[dict] = []

    if "pull_request_target" in low and re.search(r"actions/checkout", low) and re.search(r"head\.(ref|sha)|head_ref", low):
        findings.append(_finding("CI-01", name, "pull_request_target + PR head 체크아웃"))
    for mo in _UNTRUSTED_RE.finditer(content):
        # run: 컨텍스트 내인지 근사 판단
        seg = content[max(0, mo.start() - 120):mo.start()]
        if "run:" in seg or "run :" in seg:
            findings.append(_finding("CI-02", name, mo.group(0)))
    if "self-hosted" in low and any(t in low for t in ("pull_request_target", "on: [pull_request", "on:\n", "issue_comment")):
        findings.append(_finding("CI-03", name, "public 트리거 + self-hosted runner"))
    if re.search(r"permissions:\s*write-all", low) or re.search(r"permissions:\s*\n(\s+\w+:\s*write\s*\n)*\s*contents:\s*write", low):
        findings.append(_finding("CI-04", name, "전역 write 권한"))
    for mo in _SECRET_RE.finditer(content):
        findings.append(_finding("CI-05", name, mo.group(0)))
    for mo in _UNPINNED_RE.finditer(content):
        findings.append(_finding("CI-06", name, mo.group(0)))
    for mo in _CURLSH_RE.finditer(content):
        findings.append(_finding("CI-07", name, mo.group(0)))
    return findings


def _summary(findings: list[dict]) -> dict:
    c = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        c[f["severity"]] = c.get(f["severity"], 0) + 1
    risk = "high" if c["high"] else "medium" if c["medium"] else "low" if c["low"] else "clean"
    return {"risk": risk, "counts": c, "total": len(findings)}


class WorkflowFile(BaseModel):
    name: str
    content: str


class ScanWorkflowsRequest(BaseModel):
    files: list[WorkflowFile]


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    return {"agent": "cicd-security-scan", "rules": len(_RULES), "max_files": _MAX_FILES}


@router.get("/rules")
async def list_rules(user: dict = Depends(get_current_user)):
    return {"rules": _RULES}


@router.post("/scan-workflows")
async def scan_workflows(body: ScanWorkflowsRequest, user: dict = Depends(get_current_user)):
    if not body.files:
        raise HTTPException(status_code=422, detail="files 가 비어있습니다.")
    if len(body.files) > _MAX_FILES:
        raise HTTPException(status_code=413, detail=f"파일 수 상한({_MAX_FILES}) 초과")
    per_file = []
    all_findings: list[dict] = []
    for f in body.files:
        fnd = _scan_one(f.name or "workflow.yml", f.content or "")
        per_file.append({"name": f.name, "findings": fnd, "count": len(fnd)})
        all_findings.extend(fnd)
    return {"summary": _summary(all_findings), "files": per_file}
