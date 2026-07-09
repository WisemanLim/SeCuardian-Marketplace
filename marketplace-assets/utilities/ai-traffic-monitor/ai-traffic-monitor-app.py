"""ai-traffic-monitor — 브라우저 연결 AI 도우미의 트래픽 사용량 모니터.

마운트 경로: /api/addon/ai-traffic-monitor/...
목적: "대화 내용"이 아니라 "사용량(바이트/패킷)"을 정량 측정해 Shadow-AI 사용 현황 관측.

엔드포인트:
  GET  /status    도구 가용성(which) + 설정 요약           (로그인)
  GET  /domains   AI 도우미 도메인 카탈로그                 (로그인)
  POST /resolve   도메인 → IP 집합 해석 (dig/getent)        (로그인)
  GET  /usage     vnstat --json 인터페이스 누적 사용량       (로그인)
  POST /snapshot  nethogs -t N초 프로세스별 대역폭 스냅샷    (supervisor/admin)
  POST /capture   AI IP 필터 tcpdump N초 → tshark 집계       (supervisor/admin)
  POST /analyze   기존 pcap 재집계 (tshark)                 (supervisor/admin)
  GET  /config    환경변수 설정 (시크릿 없음)               (supervisor/admin)

보안 원칙 (읽기 전용 모니터링):
  - 모든 외부 실행은 shell=False + 내부 조립 argv (사용자 자유 문자열 실행 금지)
  - 바이너리 allowlist: dig getent vnstat nethogs tcpdump tshark
  - 입력 검증: interface/domain 정규식, IP 는 ipaddress 파싱, seconds 클램프, pcap 경로 봉쇄
  - 특권 작업(snapshot/capture/analyze/config)은 supervisor/admin
  - 도구 미설치 시 503 + 안내 (500 아님) — macOS 개발환경에서도 안전
  - ⚠️ from __future__ import annotations 금지 (동적 로더 pydantic 이슈)
"""
import asyncio
import ipaddress
import os
import re
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["ai-traffic-monitor"])

# ─── 환경변수 설정 ────────────────────────────────────────────────────────────

_DEFAULT_DOMAINS = [
    "perplexity.ai", "www.perplexity.ai",
    "gemini.google.com", "generativelanguage.googleapis.com",
    "chatgpt.com", "chat.openai.com", "api.openai.com",
    "claude.ai", "api.anthropic.com",
    "copilot.microsoft.com",
]


def _interface() -> str:
    return os.getenv("AITM_INTERFACE", "eth0")


def _domains() -> list[str]:
    raw = os.getenv("AITM_DOMAINS", "")
    if raw.strip():
        return [d.strip() for d in raw.split(",") if d.strip()]
    return list(_DEFAULT_DOMAINS)


def _capture_dir() -> str:
    return os.getenv("AITM_CAPTURE_DIR", "/tmp/ai-traffic")


def _max_capture_sec() -> int:
    return int(os.getenv("AITM_MAX_CAPTURE_SEC", "60"))


def _max_snapshot_sec() -> int:
    return int(os.getenv("AITM_MAX_SNAPSHOT_SEC", "30"))


# ─── 실행 정책 / 검증 ─────────────────────────────────────────────────────────

_ALLOWED_BINS = {"dig", "getent", "vnstat", "nethogs", "tcpdump", "tshark"}
_IFACE_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
_DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
_PCAP_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}\.(pcap|pcapng)$")

_MAX_OUTPUT = 64 * 1024  # 64KB
_INSTALL_HINT = "Debian/Ubuntu: sudo apt install -y vnstat nethogs tcpdump tshark dnsutils"


def _tool_path(binary: str) -> str:
    """allowlist 확인 후 절대 경로 반환. 미설치 시 503."""
    if binary not in _ALLOWED_BINS:
        raise HTTPException(status_code=403, detail=f"'{binary}' 는 허용되지 않은 도구입니다.")
    path = shutil.which(binary)
    if not path:
        raise HTTPException(
            status_code=503,
            detail=f"도구 미설치: '{binary}'. 설치 후 재시도하세요. {_INSTALL_HINT}",
        )
    return path


def _validate_iface(iface: str) -> str:
    iface = (iface or "").strip()
    if not _IFACE_RE.match(iface):
        raise HTTPException(status_code=400, detail=f"잘못된 인터페이스 이름: {iface!r}")
    return iface


def _validate_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    if not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=400, detail=f"잘못된 도메인: {domain!r}")
    return domain


def _clamp_seconds(seconds: Optional[int], max_sec: int) -> int:
    if seconds is None:
        return min(10, max_sec)
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="seconds 는 정수여야 합니다.")
    if seconds < 1:
        raise HTTPException(status_code=400, detail="seconds 는 1 이상이어야 합니다.")
    return min(seconds, max_sec)


def _decode(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    if len(text) > _MAX_OUTPUT:
        return text[:_MAX_OUTPUT] + "\n… (출력 잘림)"
    return text


async def _run(argv: list[str], timeout: float) -> tuple[int, str, str]:
    """shell=False 로 argv 실행 → (returncode, stdout, stderr). 타임아웃 시 종료."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"도구를 찾을 수 없습니다: {argv[0]}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"실행 실패: {exc}")

    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=504, detail=f"실행 시간 초과 ({timeout:.0f}초): {argv[0]}")
    return proc.returncode, _decode(out), _decode(err)


async def _run_timed_kill(argv: list[str], seconds: int, grace: float = 5.0) -> tuple[int, str, str]:
    """seconds 동안 실행 후 SIGTERM 으로 정상 종료(tcpdump/nethogs 캡처용)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"도구를 찾을 수 없습니다: {argv[0]}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"실행 실패: {exc}")

    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=seconds)
        return proc.returncode, _decode(out), _decode(err)
    except asyncio.TimeoutError:
        proc.terminate()  # SIGTERM → tcpdump 는 버퍼 flush 후 종료
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=grace)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            out, err = b"", b""
        return 0, _decode(out), _decode(err)


# ─── 도메인 → IP 해석 ─────────────────────────────────────────────────────────

async def _resolve_domain(domain: str) -> list[str]:
    """dig(우선) 또는 getent 로 A 레코드 IP 집합 반환. 유효 IP 만."""
    dig = shutil.which("dig")
    ips: list[str] = []
    if dig:
        rc, out, _ = await _run([dig, "+short", domain, "A"], timeout=8.0)
        for line in out.splitlines():
            line = line.strip()
            try:
                ipaddress.ip_address(line)
                ips.append(line)
            except ValueError:
                continue
    else:
        getent = shutil.which("getent")
        if not getent:
            raise HTTPException(
                status_code=503,
                detail=f"도구 미설치: 'dig'/'getent'. {_INSTALL_HINT}",
            )
        rc, out, _ = await _run([getent, "ahostsv4", domain], timeout=8.0)
        for line in out.splitlines():
            tok = line.split()[0] if line.split() else ""
            try:
                ipaddress.ip_address(tok)
                if tok not in ips:
                    ips.append(tok)
            except ValueError:
                continue
    return sorted(set(ips))


# ─── 요청 모델 ────────────────────────────────────────────────────────────────

class ResolveRequest(BaseModel):
    domains: Optional[list[str]] = None


class SnapshotRequest(BaseModel):
    seconds: Optional[int] = None
    interface: Optional[str] = None


class CaptureRequest(BaseModel):
    domains: Optional[list[str]] = None
    interface: Optional[str] = None
    seconds: Optional[int] = None


class AnalyzeRequest(BaseModel):
    pcap: str


# ─── 엔드포인트 ──────────────────────────────────────────────────────────────

@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    """도구 가용성 + 설정 요약."""
    tools = {b: bool(shutil.which(b)) for b in sorted(_ALLOWED_BINS)}
    return {
        "tools": tools,
        "all_available": all(tools.values()),
        "interface": _interface(),
        "domains_count": len(_domains()),
        "capture_dir": _capture_dir(),
        "max_capture_sec": _max_capture_sec(),
        "max_snapshot_sec": _max_snapshot_sec(),
        "install_hint": _INSTALL_HINT,
    }


@router.get("/domains")
async def list_domains(user: dict = Depends(get_current_user)):
    """모니터링 대상 AI 도우미 도메인 카탈로그."""
    return {"domains": _domains(), "source": "env" if os.getenv("AITM_DOMAINS", "").strip() else "default"}


@router.post("/resolve")
async def resolve_domains(body: ResolveRequest, user: dict = Depends(get_current_user)):
    """도메인 → 현재 IP 집합 해석. CDN/Anycast 로 결과는 가변."""
    domains = [_validate_domain(d) for d in (body.domains or _domains())]
    result: dict[str, list[str]] = {}
    all_ips: set[str] = set()
    for d in domains:
        ips = await _resolve_domain(d)
        result[d] = ips
        all_ips.update(ips)
    return {"resolved": result, "unique_ips": sorted(all_ips), "ip_count": len(all_ips)}


@router.get("/usage")
async def interface_usage(
    interface: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """vnstat --json 으로 인터페이스 누적 사용량(총/일/월) 반환."""
    iface = _validate_iface(interface or _interface())
    vnstat = _tool_path("vnstat")
    rc, out, err = await _run([vnstat, "-i", iface, "--json"], timeout=10.0)
    if rc != 0:
        msg = (err.strip() or out.strip())
        low = msg.lower()
        # 설치됐으나 미구성(DB/데몬 없음·인터페이스 미등록)은 우아한 저하 → 503
        not_ready = any(k in low for k in (
            "database", "daemon", "no such file", "not found",
            "no data", "unable to", "does not exist",
        ))
        if not_ready:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"vnstat 미구성/미준비 (interface={iface}). "
                    f"초기화: `vnstat --add -i {iface}` 후 데몬 기동 "
                    f"(Linux: `sudo systemctl enable --now vnstat`, macOS: `brew services start vnstat`). "
                    f"데이터 누적까지 수 분 소요. AITM_INTERFACE 로 인터페이스 지정 가능. "
                    f"[vnstat] {msg[:300]}"
                ),
            )
        raise HTTPException(status_code=502, detail=f"vnstat 실행 실패: {msg[:500]}")

    import json as _json
    try:
        data = _json.loads(out)
        iface_data = (data.get("interfaces") or [{}])[0]
        traffic = iface_data.get("traffic", {})
        summary = {
            "total": traffic.get("total", {}),
            "days": traffic.get("day", [])[-7:],
            "months": traffic.get("month", [])[-3:],
        }
        return {"interface": iface, "summary": summary}
    except (ValueError, KeyError, IndexError):
        return {"interface": iface, "raw": out[:4000]}


@router.post("/snapshot")
async def process_snapshot(
    body: SnapshotRequest,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """nethogs -t 로 N초 프로세스별 송/수신 대역폭 스냅샷 (root 필요)."""
    iface = _validate_iface(body.interface or _interface())
    seconds = _clamp_seconds(body.seconds, _max_snapshot_sec())
    nethogs = _tool_path("nethogs")
    # -t: trace(텍스트) 모드, -d: 갱신 주기(초)
    argv = [nethogs, "-t", "-d", "1", iface]
    rc, out, err = await _run_timed_kill(argv, seconds=seconds)

    # 텍스트 파싱: "program/pid/uid<TAB>sent<TAB>received" (best-effort)
    processes = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            prog, sent, recv = (p.strip() for p in parts)
            try:
                processes.append({"program": prog, "sent_kb": float(sent), "recv_kb": float(recv)})
            except ValueError:
                continue
    return {
        "interface": iface,
        "seconds": seconds,
        "processes": processes,
        "parsed": len(processes),
        "raw": out[:4000] if not processes else None,
        "stderr": err[:1000] or None,
    }


@router.post("/capture")
async def capture_traffic(
    body: CaptureRequest,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """AI 도메인 IP 로 향하는 HTTPS 트래픽을 N초 캡처 → tshark 로 바이트/패킷 집계 (root 필요)."""
    iface = _validate_iface(body.interface or _interface())
    seconds = _clamp_seconds(body.seconds, _max_capture_sec())
    domains = [_validate_domain(d) for d in (body.domains or _domains())]

    tcpdump = _tool_path("tcpdump")
    tshark = _tool_path("tshark")

    # 1) 도메인 → IP 해석
    ip_map: dict[str, list[str]] = {}
    all_ips: list[str] = []
    for d in domains:
        ips = await _resolve_domain(d)
        ip_map[d] = ips
        for ip in ips:
            if ip not in all_ips:
                all_ips.append(ip)
    if not all_ips:
        raise HTTPException(status_code=422, detail="해석된 IP 가 없어 캡처할 수 없습니다.")

    # 2) capture filter 조립 (pcap 문법 — 내부 조립, IP 는 검증됨)
    host_expr = " or ".join(f"host {ip}" for ip in all_ips)
    pcap_filter = f"({host_expr}) and tcp port 443"

    # 3) pcap 경로 (capture_dir 하위)
    cap_dir = _capture_dir()
    try:
        os.makedirs(cap_dir, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"캡처 디렉터리 생성 실패: {exc}")
    pcap_name = f"aitm-{iface}-{seconds}s-{len(all_ips)}ips.pcap"
    pcap_path = os.path.join(cap_dir, pcap_name)

    # 4) tcpdump 캡처 (seconds 후 SIGTERM 종료)
    argv = [tcpdump, "-i", iface, "-nn", "-s", "0", "-w", pcap_path, pcap_filter]
    await _run_timed_kill(argv, seconds=seconds)

    if not os.path.exists(pcap_path):
        raise HTTPException(status_code=500, detail="pcap 파일이 생성되지 않았습니다 (권한/인터페이스 확인).")

    # 5) tshark 집계
    packets, total_bytes = await _tshark_aggregate(tshark, pcap_path)
    return {
        "interface": iface,
        "seconds": seconds,
        "domains": ip_map,
        "unique_ips": all_ips,
        "filter": pcap_filter,
        "pcap": pcap_path,
        "packets": packets,
        "bytes": total_bytes,
    }


@router.post("/analyze")
async def analyze_pcap(
    body: AnalyzeRequest,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """capture_dir 하위의 기존 pcap 을 tshark 로 재집계."""
    pcap_path = _safe_pcap_path(body.pcap)
    tshark = _tool_path("tshark")
    packets, total_bytes = await _tshark_aggregate(tshark, pcap_path)
    return {
        "pcap": pcap_path,
        "packets": packets,
        "bytes": total_bytes,
        "size_on_disk": os.path.getsize(pcap_path),
    }


@router.get("/config")
async def get_config(user: dict = Depends(require_role("supervisor", "admin"))):
    """현재 환경변수 설정 (시크릿 없음)."""
    return {
        "AITM_INTERFACE": _interface(),
        "AITM_DOMAINS": os.getenv("AITM_DOMAINS", "") or "(default catalog)",
        "AITM_CAPTURE_DIR": _capture_dir(),
        "AITM_MAX_CAPTURE_SEC": _max_capture_sec(),
        "AITM_MAX_SNAPSHOT_SEC": _max_snapshot_sec(),
        "allowed_tools": sorted(_ALLOWED_BINS),
    }


# ─── 내부 헬퍼: pcap 집계 / 경로 봉쇄 ─────────────────────────────────────────

async def _tshark_aggregate(tshark: str, pcap_path: str) -> tuple[int, int]:
    """tshark 로 프레임 개수(패킷)와 총 바이트(frame.len 합) 반환."""
    rc, out, err = await _run(
        [tshark, "-r", pcap_path, "-T", "fields", "-e", "frame.len"],
        timeout=60.0,
    )
    if rc != 0:
        raise HTTPException(status_code=502, detail=f"tshark 분석 실패: {err.strip() or out.strip()}")
    packets = 0
    total = 0
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            total += int(line)
            packets += 1
        except ValueError:
            continue
    return packets, total


def _safe_pcap_path(name: str) -> str:
    """pcap 경로를 capture_dir 하위로 봉쇄. 경로 탈출·확장자 위반 차단."""
    name = (name or "").strip()
    base = os.path.basename(name)
    if base != name or not _PCAP_NAME_RE.match(base):
        raise HTTPException(
            status_code=400,
            detail="pcap 은 capture_dir 하위 파일명(.pcap/.pcapng)만 허용됩니다.",
        )
    cap_dir = os.path.realpath(_capture_dir())
    full = os.path.realpath(os.path.join(cap_dir, base))
    if os.path.commonpath([cap_dir, full]) != cap_dir:
        raise HTTPException(status_code=400, detail="경로 탈출이 감지되었습니다.")
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail=f"pcap 파일 없음: {base}")
    return full
