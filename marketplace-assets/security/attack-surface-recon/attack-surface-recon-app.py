"""attack-surface-recon — 외부 공격표면 OSINT 정찰 에이전트.

마운트 경로: /api/addon/attack-surface-recon/...
목적: 자사 도메인을 대상으로 서브도메인·DNS·WHOIS·포트를 정찰해 "우리 조직이 외부에 어떻게 노출돼 있는가"를
      정기 리포트한다. (extra-agents 후보 A — spiderfoot·reconftw·subfinder·nmap 계열 CLI 래핑)

엔드포인트:
  GET  /status   도구 가용성 + 대상 allowlist 요약     (로그인)
  GET  /targets  스캔 허용 도메인 목록                 (로그인)
  POST /recon    subfinder/dig/whois 정찰(수동적)      (로그인)
  POST /scan     nmap 포트스캔(능동적)                 (supervisor/admin)

보안 원칙:
  - 대상은 ASR_ALLOWED_DOMAINS allowlist 에 등록된 도메인(+서브도메인)만 — 자유 입력 차단.
  - shell=False + argv, 바이너리 allowlist, 도메인 정규식 검증.
  - 능동 스캔(nmap)은 supervisor/admin.
  - 도구 미설치 시 503. ⚠️ from __future__ import annotations 금지.
"""
import asyncio
import os
import re
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["attack-surface-recon"])

_ALLOWED_BINS = {"subfinder", "dig", "whois", "nmap"}
_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9](-?[A-Za-z0-9])*\.)+[A-Za-z]{2,}$")
_MAX_OUTPUT = 64 * 1024
_INSTALL_HINT = "Debian/Ubuntu: sudo apt install -y dnsutils whois nmap; subfinder: go install ...@latest"


def _allowed_domains() -> list[str]:
    raw = os.getenv("ASR_ALLOWED_DOMAINS", "")
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _max_ports() -> str:
    return os.getenv("ASR_NMAP_PORTS", "1-1024")


def _tool(binary: str) -> str:
    if binary not in _ALLOWED_BINS:
        raise HTTPException(status_code=403, detail=f"'{binary}' 는 허용되지 않은 도구입니다.")
    path = shutil.which(binary)
    if not path:
        raise HTTPException(status_code=503, detail=f"도구 미설치: '{binary}'. {_INSTALL_HINT}")
    return path


def _validate_target(domain: str) -> str:
    domain = (domain or "").strip().lower()
    if not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=400, detail=f"잘못된 도메인: {domain!r}")
    allow = _allowed_domains()
    if not allow:
        raise HTTPException(status_code=403, detail="ASR_ALLOWED_DOMAINS 미설정 — 스캔 대상 allowlist 를 먼저 등록하세요.")
    if not any(domain == a or domain.endswith("." + a) for a in allow):
        raise HTTPException(status_code=403, detail=f"대상 {domain} 은 allowlist 에 없습니다.")
    return domain


def _decode(raw: bytes) -> str:
    t = raw.decode("utf-8", errors="replace")
    return t if len(t) <= _MAX_OUTPUT else t[:_MAX_OUTPUT] + "\n… (출력 잘림)"


async def _run(argv: list[str], timeout: float) -> tuple[int, str, str]:
    try:
        proc = await asyncio.create_subprocess_exec(*argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"도구를 찾을 수 없습니다: {argv[0]}")
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=504, detail=f"실행 시간 초과 ({timeout:.0f}초): {argv[0]}")
    return proc.returncode, _decode(out), _decode(err)


class ReconRequest(BaseModel):
    domain: str


class ScanRequest(BaseModel):
    domain: str
    ports: Optional[str] = None


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    tools = {b: bool(shutil.which(b)) for b in sorted(_ALLOWED_BINS)}
    return {
        "tools": tools,
        "all_available": all(tools.values()),
        "allowed_domains": _allowed_domains(),
        "nmap_ports": _max_ports(),
        "install_hint": _INSTALL_HINT,
    }


@router.get("/targets")
async def list_targets(user: dict = Depends(get_current_user)):
    return {"allowed_domains": _allowed_domains(), "source": "ASR_ALLOWED_DOMAINS"}


@router.post("/recon")
async def recon(body: ReconRequest, user: dict = Depends(get_current_user)):
    """수동적 정찰: 서브도메인(subfinder) + A레코드(dig) + 등록정보(whois)."""
    domain = _validate_target(body.domain)
    result: dict = {"domain": domain}

    subfinder = shutil.which("subfinder")
    if subfinder:
        rc, out, _ = await _run([subfinder, "-silent", "-d", domain], timeout=60.0)
        result["subdomains"] = sorted({ln.strip() for ln in out.splitlines() if ln.strip()})
    else:
        result["subdomains"] = None
        result["subdomains_note"] = "subfinder 미설치 — 서브도메인 열거 생략"

    dig = _tool("dig")
    rc, out, _ = await _run([dig, "+short", domain, "A"], timeout=10.0)
    result["a_records"] = [ln.strip() for ln in out.splitlines() if ln.strip()]

    whois = shutil.which("whois")
    if whois:
        rc, out, _ = await _run([whois, domain], timeout=15.0)
        keep = [ln for ln in out.splitlines() if re.search(r"(?i)(registrar|creation|expiry|name server|org)", ln)]
        result["whois"] = keep[:20]
    return result


@router.post("/scan")
async def scan(body: ScanRequest, user: dict = Depends(require_role("supervisor", "admin"))):
    """능동적 포트스캔(nmap). 대상 allowlist + 포트범위 제한."""
    domain = _validate_target(body.domain)
    ports = (body.ports or _max_ports()).strip()
    if not re.match(r"^[0-9,\-]{1,64}$", ports):
        raise HTTPException(status_code=400, detail="ports 는 숫자·쉼표·하이픈만 허용됩니다.")
    nmap = _tool("nmap")
    rc, out, err = await _run([nmap, "-Pn", "-T3", "-p", ports, "--open", domain], timeout=180.0)
    open_ports = []
    for line in out.splitlines():
        mo = re.match(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)", line.strip())
        if mo:
            open_ports.append({"port": int(mo.group(1)), "proto": mo.group(2), "service": mo.group(3)})
    return {"domain": domain, "ports": ports, "open_ports": open_ports, "open_count": len(open_ports)}
