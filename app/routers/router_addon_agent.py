"""Addon Agent 관리 라우터 — ZIP 업로드 핫 디플로이 (F4) + Agent 카탈로그 (F22)."""
import asyncio
import io
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.addon_agent_loader import load_router
from app.core.deps import get_current_user, require_role
from app.core.i18n import norm_descriptions as _norm_descriptions
from app.db import execute_write, fetch_all, fetch_one, _PH, _IS_SQLITE

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/addon-agents", tags=["addon-agents"])

_DEPLOYED = Path("addon-agents/deployed")
# §7.6.1-7: 스캐폴드 템플릿(Board·RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent)은
# marketplace-assets/addon/ 로 일원화(구 addon-agents/{_templates,zip} 폐지)
_TEMPLATES = Path("marketplace-assets/addon")
_FRONT_DEPLOYED = Path("front/src/pages/addon/deployed")
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

_COMPOSE_FILE = Path("/app/docker-compose.yml")
_COMPOSE_BASE = [
    "docker", "compose",
    "-f", str(_COMPOSE_FILE),
    "--profile", "app", "--profile", "web",
]


async def _rebuild_web() -> None:
    """addon front 변경 후 web 컨테이너 자동 재빌드 (백그라운드 비동기)."""
    if not _COMPOSE_FILE.exists():
        logger.warning("[addon] %s 없음 — web 자동 재빌드 스킵 (컨테이너 배포 환경 아님)", _COMPOSE_FILE)
        return
    for cmd in [
        [*_COMPOSE_BASE, "build", "web"],
        [*_COMPOSE_BASE, "up", "-d", "--no-deps", "web"],
    ]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("[addon] web 재빌드 실패: %s", stderr.decode()[-500:])
            return
    logger.info("[addon] web 컨테이너 자동 재빌드 완료")


def _kill_port(port: int) -> None:
    """SIGTERM으로 포트 점유 프로세스 종료. ss(Linux) → lsof(macOS) 순으로 시도."""
    pids: list[int] = []
    try:
        r = subprocess.run(
            ["ss", "-tlnp", f"sport = :{port}"],
            capture_output=True, text=True, timeout=3,
        )
        for m in re.finditer(r"pid=(\d+)", r.stdout):
            pids.append(int(m.group(1)))
    except FileNotFoundError:
        pass
    if not pids:
        try:
            r = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=3,
            )
            pids = [int(p) for p in r.stdout.split() if p.strip().isdigit()]
        except (FileNotFoundError, ValueError):
            pass
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info("[addon] killed pid=%d on port %d", pid, port)
        except ProcessLookupError:
            pass

_VALID_TYPES = {"app", "service", "tool-proxy", "rag", "reviewer", "execution", "hitl", "memory", "federation", "shell"}

# type → template directory name mapping
_TYPE_TEMPLATE = {
    "app": "Board",
    "service": "ServiceAgent",
    "tool-proxy": "ToolProxyAgent",
    "rag": "RagAgent",
    "reviewer": "ServiceAgent",
    "execution": "ServiceAgent",
    "hitl": "ServiceAgent",
    "memory": "ServiceAgent",
    "federation": "ServiceAgent",
    "shell": "ShellAgent",
}


def _pg_to_sqlite(sql: str) -> str:
    """PostgreSQL DDL → SQLite 호환 변환 (local SQLite 환경에서만 적용)."""
    from app.core.config import settings
    if not settings.database_url.startswith("sqlite"):
        return sql
    sql = re.sub(r"\bSERIAL\b", "INTEGER", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bBOOLEAN\b", "INTEGER", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bDEFAULT\s+NOW\s*\(\)", "DEFAULT CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bDEFAULT\s+FALSE\b", "DEFAULT 0", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bDEFAULT\s+TRUE\b", "DEFAULT 1", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bVARCHAR\s*\(\s*\d+\s*\)", "TEXT", sql, flags=re.IGNORECASE)
    return sql


def _check_safe_names(zf: zipfile.ZipFile) -> None:
    """경로 탐색 공격 방지: '..' 또는 절대 경로 포함 항목 차단 (압축 해제 前 검사)."""
    for member in zf.namelist():
        if ".." in member or member.startswith("/"):
            raise ValueError(f"Unsafe path in ZIP: {member}")


def _invalid_package_message(zip_stem: str) -> str:
    """에이전트 구성 파일이 없는 ZIP 의 거부 사유 — worker 배포본은 별도 안내 (R22-6)."""
    if zip_stem.lower().endswith("_worker"):
        return (
            f"'{zip_stem}.zip' 은 에이전트가 아닌 worker 배포 패키지로 보입니다. "
            f"worker 는 플랫폼에 등록하지 않고 대상 디바이스에 직접 설치합니다 "
            f"— 에이전트 카드의 'Worker 설치 가이드' 를 참고하세요."
        )
    return (
        f"{zip_stem}-app.py 또는 {zip_stem}-front.tsx 중 하나가 ZIP 최상위에 있어야 합니다 "
        f"(ZIP 파일명과 파일 접두어가 같아야 합니다)"
    )


def _conflict_detail(agent_key: str, is_builtin: bool, registered: bool) -> dict:
    """중복 키 409 상세 — 프론트가 code 로 분기하고 message/message_en 을 그대로 노출 (R22-6).

    builtin_conflict 는 **등록 불가**(덮어쓰기 불가) — ADDON 목록은 is_builtin=0 만 표시하므로
    내장 키로 등록하면 어느 목록에서도 보이지 않는 상태가 된다. 키 변경만이 유효한 조치다.
    """
    if is_builtin:
        return {
            "code": "builtin_conflict",
            "agent_key": agent_key,
            "is_builtin": True,
            "registered": registered,
            "overwritable": False,
            "message": (
                f"'{agent_key}' 는 내장 에이전트의 키와 중복되어 ADDON 에이전트로 "
                f"등록할 수 없습니다. ZIP 파일명(= 에이전트 키)을 다른 이름으로 바꿔 등록하세요. "
                f"(내장 에이전트 '{agent_key}' 는 에이전트 관리 → 내장 에이전트 탭에서 관리합니다.)"
            ),
            "message_en": (
                f"'{agent_key}' collides with a built-in agent key and cannot be registered "
                f"as an ADDON agent. Rename the ZIP file (= agent key) and upload again. "
                f"(Built-in agent '{agent_key}' is managed under Agent Management → Built-in Agents.)"
            ),
        }
    return {
        "code": "duplicate",
        "agent_key": agent_key,
        "is_builtin": False,
        "registered": registered,
        "overwritable": True,
        "message": (
            f"'{agent_key}' 는 이미 등록된 에이전트입니다. "
            f"덮어쓰기를 선택하면 기존 등록본을 이 ZIP 으로 교체합니다."
        ),
        "message_en": (
            f"'{agent_key}' is already registered. Overwriting replaces the existing "
            f"registration with this ZIP."
        ),
    }


# R18-7: 다국어 정규화 공통 함수는 app/core/i18n.norm_descriptions 로 승격 (상단 import 참조)


def _parse_meta_json(dest: Path, zip_stem: str) -> dict:
    """ZIP 내 {AgentName}-meta.json 파싱. 없으면 기본값(type=app) 반환."""
    meta_file = dest / f"{zip_stem}-meta.json"
    if not meta_file.exists():
        return _norm_descriptions({"agent_type": "app", "capabilities": []})
    try:
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        if data.get("agent_type") not in _VALID_TYPES:
            # 내장 에이전트 배포본은 유형을 "type" 키로 기록한다 — 폴백 후 app 기본값
            data["agent_type"] = data.get("type") if data.get("type") in _VALID_TYPES else "app"
        return _norm_descriptions(data)
    except Exception:
        return _norm_descriptions({"agent_type": "app", "capabilities": []})


def _template_dirs() -> list[Path]:
    """스캐폴드 템플릿 디렉터리 목록 — marketplace-assets/addon/ (§7.6.1-7)."""
    if not _TEMPLATES.exists():
        return []
    dirs = [d for d in _TEMPLATES.iterdir() if d.is_dir() and not d.name.startswith(".")]
    return sorted(dirs, key=lambda d: d.name)


def _find_template_dir(name: str) -> Path | None:
    """템플릿 디렉터리 조회 — marketplace-assets/addon/ (§7.6.1-7)."""
    d = _TEMPLATES / name
    return d if d.is_dir() else None


@router.get("/templates/list")
async def list_templates(user: dict = Depends(get_current_user)):
    templates = []
    for d in _template_dirs():
        # meta.json이 있으면 유형 정보 읽기
        meta_files = list(d.glob("*-meta.json"))
        agent_type = "app"
        description = ""
        description_en = ""
        descriptions: dict = {}
        if meta_files:
            try:
                meta = _norm_descriptions(json.loads(meta_files[0].read_text(encoding="utf-8")))
                agent_type = meta.get("agent_type", "app")
                description = meta.get("description", "")
                description_en = meta.get("description_en", "")
                descriptions = meta.get("descriptions", {})
            except Exception:
                pass
        templates.append({
            "name": d.name,
            "filename": f"{d.name}.zip",
            "agent_type": agent_type,
            "description": description,
            "description_en": description_en,
            "descriptions": descriptions,
            "has_zip": (d.parent / f"{d.name}.zip").exists(),
        })
    return {"templates": templates}


@router.get("/catalog")
async def list_catalog(
    agent_type: str | None = None,
    user: dict = Depends(get_current_user),
):
    """등록된 Addon Agent 목록을 유형별로 그룹핑하여 반환."""
    sql = (
        "SELECT agent_key, agent_name, api_prefix, agent_type, has_app, has_front, "
        "is_builtin, is_active, uploaded_by, uploaded_at FROM tbl_addon_agents "
    )
    params: tuple = ()
    if agent_type and agent_type in _VALID_TYPES:
        sql += f"WHERE agent_type = {_PH} "
        params = (agent_type,)
    sql += "ORDER BY is_builtin DESC, uploaded_at DESC"
    rows = await fetch_all(sql, params)

    # 유형별 그룹핑
    groups: dict[str, list] = {}
    for row in rows:
        t = row.get("agent_type") or "app"
        groups.setdefault(t, []).append(row)

    return {
        "total": len(rows),
        "groups": groups,
        "items": rows,
    }


@router.get("/templates/download/{name}")
async def download_template(name: str, user: dict = Depends(get_current_user)):
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid template name")
    zip_path = _TEMPLATES / f"{name}.zip"
    if zip_path.exists():
        return FileResponse(str(zip_path), media_type="application/zip", filename=f"{name}.zip")
    raise HTTPException(status_code=404, detail="Template zip not found")


@router.get("/guide")
async def get_guide(user: dict = Depends(get_current_user)):
    """addon-agents/README.md 내용 반환."""
    readme = Path("addon-agents/README.md")
    if not readme.exists():
        return {"content": ""}
    return {"content": readme.read_text(encoding="utf-8")}


@router.get("/")
async def list_addons(user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        "SELECT agent_key, agent_name, api_prefix, agent_type, has_app, has_front, "
        "is_builtin, is_active, uploaded_by, uploaded_at, meta_json "
        "FROM tbl_addon_agents ORDER BY is_builtin DESC, uploaded_at DESC"
    )
    for row in rows:
        try:
            meta = _norm_descriptions(json.loads(row.get("meta_json") or "{}"))
            row["description"] = meta.get("description", "")
            row["description_en"] = meta.get("description_en", "")
            row["descriptions"] = meta.get("descriptions", {})
            row["agent_names"] = meta.get("agent_names", {})
        except Exception:
            row["description"] = ""
            row["description_en"] = ""
            row["descriptions"] = {}
            row["agent_names"] = {}
        row.pop("meta_json", None)
        # R22-3: worker 필요 여부 — 카드에 설치 가이드 아이콘 상시 노출용
        row["has_worker"] = _agent_worker_meta(row["agent_key"])[0] is not None
    return {"addons": rows}


class ScaffoldRequest(BaseModel):
    agent_name: str
    agent_type: str = "app"
    description: str = ""
    domain: str = ""
    # MCP Proxy 옵션 (#3) — REST API(OpenAPI)를 MCP 서버로 변환하는 프록시 스캐폴드
    enable_mcp_proxy: bool = False
    upstream_base_url: str = ""      # 프록시 대상 REST API 베이스 URL
    openapi_url: str = ""            # 대상 OpenAPI 스펙 URL (tool 목록 자동 도출용)
    mcp_extra_args: list[str] = []   # custom args (key:val) — 헤더/설정 주입


def _gen_mcp_proxy_app(upstream_base_url: str, openapi_url: str,
                       extra_args: list[str]) -> str:
    """MCP Proxy addon app.py 생성 — upstream OpenAPI/REST 를 MCP tool 로 변환 (#3).

    참조: /Users/wise/Developer/wise-project/MCP-Proxy-Service (operation 1개 = MCP tool 1개).
    생성된 addon 의 FastAPI 라우트는 SeCuardian MCP 계층(openapi_to_mcp)이 자동으로
    MCP tool 로 노출한다. 스펙 fetch 실패(오프라인) 시에도 generic passthrough 로 동작.
    """
    # custom args (key:val) → 기본 헤더/설정 dict (json.dumps 로 안전 임베드)
    cfg: dict = {}
    for item in extra_args:
        if not isinstance(item, str):
            continue
        idx = item.find(":")
        if idx > 0:
            cfg[item[:idx].strip()] = item[idx + 1:].strip()
        elif item.strip():
            cfg[item.strip()] = ""
    tmpl = _MCP_PROXY_APP_TEMPLATE
    tmpl = tmpl.replace("__BASE_URL__", json.dumps(upstream_base_url or "https://api.example.com"))
    tmpl = tmpl.replace("__OPENAPI_URL__", json.dumps(openapi_url or ""))
    tmpl = tmpl.replace("__EXTRA_ARGS__", json.dumps(cfg, ensure_ascii=False))
    return tmpl


def _gen_mcp_proxy_meta(name: str, description: str, domain: str,
                        upstream_base_url: str, openapi_url: str,
                        extra_args: list[str]) -> str:
    """MCP Proxy addon meta.json 생성 — mcp 블록에 프록시 설정 기록 (#3)."""
    meta = {
        "agent_type": "tool-proxy",
        "version": "1.0.0",
        "display_name": name,
        "description": description or f"{name} — REST API(OpenAPI)를 MCP 서버로 변환하는 프록시 Agent",
        "capabilities": [{
            "verb": "proxy",
            "domain": domain or "integration.external-api",
            "description": "외부 REST API 도구를 MCP 로 노출합니다",
        }],
        "mcp": {
            "enabled": True,
            "upstream_base_url": upstream_base_url,
            "openapi_url": openapi_url,
            "extra_args": extra_args,
        },
        "required_env": [],
        "optional_env": ["TOOL_PROXY_BASE_URL", "TOOL_PROXY_API_KEY"],
        "min_platform_version": "2.0.0",
    }
    return json.dumps(meta, ensure_ascii=False, indent=2)


# 생성될 MCP Proxy addon 의 app.py 본문 (placeholder 치환 후 사용)
_MCP_PROXY_APP_TEMPLATE = '''"""MCP Proxy Agent — 외부 REST API(OpenAPI)를 MCP Tool 로 변환하는 어댑터.

SeCuardian 스캐폴더가 생성한 MCP 프록시 addon 입니다 (#3).
- GET  /tools              upstream OpenAPI operation → tool 목록 (스펙 fetch, 오프라인 시 generic)
- POST /tools/{tool_name}  operation 실행 → upstream 호출 결과
- POST /proxy              generic passthrough {method, path, body, params}
- GET  /config             현재 연결 설정 (credential 마스킹)
"""
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["mcp-proxy-agent"])

# ─── 스캐폴드 주입 설정 (custom args 포함) ────────────────────────────────────
_BASE_URL_DEFAULT = __BASE_URL__
_OPENAPI_URL = __OPENAPI_URL__
_EXTRA_ARGS: dict = __EXTRA_ARGS__      # custom args (key:val) → 기본 헤더/설정

_spec_cache: dict = {}


def _base_url() -> str:
    return os.getenv("TOOL_PROXY_BASE_URL", _BASE_URL_DEFAULT)


def _headers() -> dict:
    """custom args 의 헤더성 항목 + API 키를 요청 헤더로 구성."""
    headers = {}
    token = os.getenv("TOOL_PROXY_API_KEY", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for k, v in _EXTRA_ARGS.items():
        # key 가 헤더명 형태(대문자/하이픈)면 헤더로 취급
        if k.lower().startswith("header.") :
            headers[k[7:]] = v
        elif k.lower() in ("authorization", "x-api-key"):
            headers[k] = v
    return headers


async def _fetch_spec() -> dict:
    if not _OPENAPI_URL:
        return {}
    if _spec_cache.get("spec") is not None:
        return _spec_cache["spec"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_OPENAPI_URL, headers=_headers())
            resp.raise_for_status()
            spec = resp.json()
            _spec_cache["spec"] = spec
            return spec
    except Exception:
        return {}


def _spec_to_tools(spec: dict) -> list[dict]:
    tools = []
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            op = item.get(method)
            if not op:
                continue
            op_id = op.get("operationId") or f"{method}_{path}"
            tools.append({
                "name": op_id,
                "description": op.get("summary") or op.get("description") or f"{method.upper()} {path}",
                "method": method.upper(),
                "path": path,
            })
    return tools


@router.get("/tools")
async def list_tools(user: dict = Depends(get_current_user)):
    """upstream OpenAPI 를 MCP tool 목록으로 변환. 스펙 없으면 generic passthrough 안내."""
    spec = await _fetch_spec()
    tools = _spec_to_tools(spec)
    if not tools:
        tools = [{
            "name": "proxy",
            "description": "generic passthrough — POST /proxy 로 {method, path, body, params} 전달",
            "method": "POST", "path": "/proxy",
        }]
    return {"base_url": _base_url(), "tools": tools, "count": len(tools)}


class ToolCallRequest(BaseModel):
    arguments: dict = {}


@router.post("/tools/{tool_name}")
async def call_tool(tool_name: str, body: ToolCallRequest,
                    user: dict = Depends(get_current_user)):
    """operation 이름으로 upstream 호출 실행."""
    spec = await _fetch_spec()
    tool = next((t for t in _spec_to_tools(spec) if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    path = tool["path"]
    args = dict(body.arguments)
    # path param 치환
    for k in list(args.keys()):
        token = "{" + k + "}"
        if token in path:
            path = path.replace(token, str(args.pop(k)))
    return await _forward(tool["method"], path, args if tool["method"] in ("POST", "PUT", "PATCH") else None,
                          args if tool["method"] in ("GET", "DELETE") else None)


class ProxyRequest(BaseModel):
    method: str = "GET"
    path: str = "/"
    body: dict | None = None
    params: dict | None = None


@router.post("/proxy")
async def proxy(req: ProxyRequest, user: dict = Depends(get_current_user)):
    """generic passthrough — 임의 upstream 경로 호출."""
    return await _forward(req.method.upper(), req.path, req.body, req.params)


async def _forward(method: str, path: str, body: dict | None, params: dict | None) -> dict:
    url = _base_url().rstrip("/") + "/" + path.lstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, url, json=body, params=params, headers=_headers())
            try:
                data = resp.json()
            except Exception:
                data = resp.text
            return {"status_code": resp.status_code, "result": data}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"upstream 호출 실패: {exc}")


@router.get("/config")
async def get_config(user: dict = Depends(require_role("supervisor", "admin"))):
    return {
        "base_url": _base_url(),
        "openapi_url": _OPENAPI_URL,
        "api_key_set": bool(os.getenv("TOOL_PROXY_API_KEY")),
        "extra_args_keys": list(_EXTRA_ARGS.keys()),
    }
'''


@router.get("/key-check/{agent_key}")
async def key_check(agent_key: str, user: dict = Depends(get_current_user)):
    """스캐폴드 이름(= 에이전트 키) 사용 가능 여부 사전 확인 (R22-7).

    배포 시점에야 409 로 알던 중복을 이름 입력 단계에서 미리 알린다.
    판정 기준은 `_deploy_zip_bytes` 와 동일 — tbl_addon_agents 등록분 + tbl_agent_config 내장 시드.
    """
    key = agent_key.strip().lower()
    if not key or not _NAME_RE.match(key):
        raise HTTPException(status_code=400, detail="agent_key 형식이 올바르지 않습니다")

    existing = await fetch_one(
        f"SELECT agent_key, is_builtin FROM tbl_addon_agents WHERE agent_key = {_PH}", (key,)
    )
    cfg = await fetch_one(
        f"SELECT agent_key FROM tbl_agent_config WHERE agent_key = {_PH}", (key,)
    )
    if not existing and not cfg:
        return {"agent_key": key, "available": True, "conflict": None}
    is_builtin = bool(existing.get("is_builtin")) if existing else bool(cfg)
    return {
        "agent_key": key,
        "available": False,
        "conflict": _conflict_detail(key, is_builtin, bool(existing)),
    }


@router.post("/scaffold")
async def scaffold_addon(
    body: ScaffoldRequest,
    user: dict = Depends(get_current_user),
):
    """agent_type + name으로 스캐폴딩 ZIP 생성·다운로드.

    enable_mcp_proxy=true 면 upstream REST/OpenAPI 를 MCP 로 변환하는 프록시 addon 을
    생성한다 (#3, tool-proxy 유형). custom args(mcp_extra_args)는 헤더/설정으로 주입.
    """
    # 이름 검증: PascalCase 또는 단어 허용
    name = body.agent_name.strip()
    if not name or not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", name):
        raise HTTPException(status_code=400, detail="agent_name은 영문자로 시작해야 합니다 (PascalCase 권장)")
    if body.agent_type not in _VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"agent_type은 {sorted(_VALID_TYPES)} 중 하나여야 합니다")

    # ── MCP Proxy 스캐폴드 (#3) — 템플릿 대신 upstream 연동 프록시 생성 ──────────
    if body.enable_mcp_proxy:
        app_py = _gen_mcp_proxy_app(body.upstream_base_url, body.openapi_url, body.mcp_extra_args)
        meta_json = _gen_mcp_proxy_meta(
            name, body.description, body.domain,
            body.upstream_base_url, body.openapi_url, body.mcp_extra_args,
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{name}-app.py", app_py)
            zf.writestr(f"{name}-meta.json", meta_json)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
        )

    # 기반 템플릿 디렉터리 결정
    tmpl_dir_name = _TYPE_TEMPLATE.get(body.agent_type, "ServiceAgent")
    tmpl_dir = _find_template_dir(tmpl_dir_name)
    if tmpl_dir is None:
        raise HTTPException(status_code=404, detail=f"템플릿 미존재: {tmpl_dir_name}")

    # ZIP을 메모리에서 생성 (템플릿 파일 복사 + 이름 치환)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_file in sorted(tmpl_dir.iterdir()):
            if src_file.is_dir() or src_file.suffix in (".pyc",):
                continue
            # 파일명: 템플릿명 → 요청 이름으로 치환
            new_filename = src_file.name.replace(tmpl_dir_name, name)
            try:
                content = src_file.read_text(encoding="utf-8")
                # 파일 내 템플릿명도 치환 (클래스명, 변수명 등)
                content = content.replace(tmpl_dir_name, name)
                # meta.json의 description/domain 업데이트
                if new_filename.endswith("-meta.json"):
                    try:
                        meta = json.loads(content)
                        if body.description:
                            meta["description"] = body.description
                        if body.domain:
                            for cap in meta.get("capabilities", []):
                                cap["domain"] = body.domain
                        meta["agent_type"] = body.agent_type
                        content = json.dumps(meta, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                zf.writestr(new_filename, content)
            except UnicodeDecodeError:
                # 바이너리 파일은 그대로 복사
                zf.write(src_file, new_filename)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )


# ── F26 Agent ZIP 추출 / F27 Standalone 배포 번들 export ─────────────────────

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _resolve_agent_source(row: dict) -> tuple[Path, str]:
    """등록된 에이전트의 소스 디렉터리와 파일 스템({Stem}-app.py 의 Stem) 결정.

    내장(builtin)은 router_path 가 _templates/ 를, 업로드본은 deployed/ 를 가리킨다.
    """
    router_path = row.get("router_path") or ""
    if router_path:
        p = Path(router_path)
        if p.exists():
            return p.parent, p.name.removesuffix("-app.py")
    d = _DEPLOYED / row["agent_key"]
    if d.exists():
        for pattern, suffix in (("*-app.py", "-app.py"), ("*-front.tsx", "-front.tsx"), ("*-meta.json", "-meta.json")):
            files = sorted(d.glob(pattern))
            if files:
                return d, files[0].name.removesuffix(suffix)
    raise HTTPException(status_code=404, detail="에이전트 소스 파일을 찾을 수 없습니다")


async def _ensure_key_available(new_key: str) -> None:
    """새 agent_key 중복 검사 — tbl_addon_agents + tbl_agent_config 모두 확인."""
    for table in ("tbl_addon_agents", "tbl_agent_config"):
        dup = await fetch_one(
            f"SELECT agent_key FROM {table} WHERE agent_key = {_PH}", (new_key,)
        )
        if dup:
            raise HTTPException(
                status_code=409,
                detail=f"'{new_key}' 는 이미 등록된 에이전트와 중복됩니다. 다른 이름을 사용하세요.",
            )


def _provenance_note(row: dict) -> str:
    return (
        f"Derived from base agent '{row['agent_name']}' ({row['agent_key']}) "
        f"— source: SeCuardian"
    )


def _derived_meta(meta: dict, row: dict, new_name: str, description: str) -> dict:
    """파생 meta.json — description 에 base 에이전트 출처를 항상 명시 (라이선스/출처 표기)."""
    note = _provenance_note(row)
    base_desc = description or meta.get("description", "")
    meta["display_name"] = meta.get("display_name") or new_name
    meta["description"] = f"[{note}] {base_desc}".strip()
    meta["base_agent"] = {
        "agent_key": row["agent_key"],
        "agent_name": row["agent_name"],
        "platform": "SeCuardian",
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return meta


class ExportRequest(BaseModel):
    new_name: str
    description: str = ""


@router.post("/{agent_key}/export")
async def export_addon(
    agent_key: str,
    body: ExportRequest,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """내장/ADDON 에이전트를 **새 이름**의 ZIP 으로 추출 (F26).

    - 새 이름은 기존 에이전트와 중복 금지 (409)
    - meta.json description 에 base 에이전트 출처 자동 명시
    """
    row = await fetch_one(
        f"SELECT agent_key, agent_name, agent_type, router_path, meta_json "
        f"FROM tbl_addon_agents WHERE agent_key = {_PH}",
        (agent_key,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Addon not found")

    new_name = body.new_name.strip()
    if not new_name or not _NAME_RE.match(new_name):
        raise HTTPException(status_code=400, detail="new_name은 영문자로 시작해야 합니다 (PascalCase 권장)")
    new_key = new_name.lower()
    await _ensure_key_available(new_key)

    src_dir, stem = _resolve_agent_source(row)

    buf = io.BytesIO()
    meta_written = False
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_file in sorted(src_dir.iterdir()):
            if src_file.is_dir() or src_file.suffix in (".pyc", ".zip"):
                continue
            new_filename = src_file.name.replace(stem, new_name)
            try:
                content = src_file.read_text(encoding="utf-8")
                content = content.replace(stem, new_name)
                if new_filename.endswith("-meta.json"):
                    try:
                        meta = json.loads(content)
                    except Exception:
                        meta = {"agent_type": row.get("agent_type") or "app", "capabilities": []}
                    meta = _derived_meta(meta, row, new_name, body.description)
                    content = json.dumps(meta, ensure_ascii=False, indent=2)
                    meta_written = True
                zf.writestr(new_filename, content)
            except UnicodeDecodeError:
                zf.writestr(new_filename, src_file.read_bytes())
        if not meta_written:
            meta = _derived_meta(
                {"agent_type": row.get("agent_type") or "app", "capabilities": []},
                row, new_name, body.description,
            )
            zf.writestr(f"{new_name}-meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

    buf.seek(0)
    logger.info("[addon] export %s → %s.zip (by %s)", agent_key, new_name, user.get("sub"))
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{new_name}.zip"'},
    )


_BUNDLE_DIRS = ("app", "sql", "standalone")
_BUNDLE_FILES = ("pyproject.toml", "uv.lock")
_BUNDLE_SKIP = ("__pycache__", ".pyc", ".zip")


def _sql_quote(text: str) -> str:
    return text.replace("'", "''")


def _standalone_seed_sql(row: dict, stem: str, has_app: bool) -> str:
    """번들 기동 시 run_migrations 가 실행할 03_standalone_seed.sql (idempotent)."""
    key = row["agent_key"]
    name = _sql_quote(row["agent_name"])
    router_path = f"addon-agents/deployed/{key}/{stem}-app.py" if has_app else ""
    description = ""
    try:
        # dict 형(description={"ko":..}) meta 도 안전 처리 — 정규화 후 ko 문자열 사용
        description = _sql_quote(
            _norm_descriptions(json.loads(row.get("meta_json") or "{}")).get("description", "")
        )
    except Exception:
        pass
    return (
        "-- standalone bundle seed (auto-generated, idempotent)\n"
        "INSERT OR IGNORE INTO tbl_addon_agents\n"
        "  (agent_key, agent_name, router_path, sql_path, api_prefix, has_app, has_front,"
        " is_builtin, is_active, agent_type, uploaded_by)\n"
        f"VALUES ('{key}', '{name}', '{router_path}', '', '/api/addon/{key}',"
        f" {int(has_app)}, 0, 0, 1, '{row.get('agent_type') or 'app'}', 'standalone');\n"
        "INSERT OR IGNORE INTO tbl_agent_config (agent_key, agent_name, is_enabled, description)\n"
        f"VALUES ('{key}', '{name}', 1, '{description}');\n"
    )


def _standalone_dockerfile(agent_port: int) -> str:
    return f"""FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev || uv sync

COPY app/ ./app/
COPY sql/ ./sql/
COPY standalone/ ./standalone/
COPY addon-agents/ ./addon-agents/

ARG AGENT_PORT={agent_port}
ENV AGENT_STANDALONE=true \\
    AGENT_PORT=${{AGENT_PORT}}

EXPOSE ${{AGENT_PORT}}
CMD ["sh", "-c", "uv run uvicorn standalone.standalone_app:app --host 0.0.0.0 --port ${{AGENT_PORT:-{agent_port}}}"]
"""


def _standalone_compose(key: str, image: str, a2a_port: int, mcp_port: int | None) -> str:
    ports = [f'      - "{a2a_port}:{a2a_port}"   # A2A + MCP (동일 앱)']
    if mcp_port and mcp_port != a2a_port:
        ports.append(f'      - "{mcp_port}:{a2a_port}"   # MCP 전용 host 포트 매핑')
    ports_yaml = "\n".join(ports)
    return f"""# auto-generated by /api/addon-agents/{key}/export-standalone
services:
  {key}-standalone:
    build:
      context: .
      args:
        AGENT_PORT: {a2a_port}
    image: {image}
    env_file: .env.standalone
    ports:
{ports_yaml}
    restart: unless-stopped
"""


def _standalone_env(key: str, a2a_port: int) -> str:
    return f"""# Standalone Agent 환경설정 (auto-generated)
ENV=local
AGENT_STANDALONE=true
AGENT_KEY={key}
AGENT_PORT={a2a_port}
AGENT_BASE_URL=http://localhost:{a2a_port}
# 필수: LLM API 키 입력
ANTHROPIC_API_KEY=
# Docker/NAT 환경에서 MCP URL host 명시 (선택)
MCP_HOST=
# dev/staging/prod 로 전환 시: DATABASE_URL=postgresql://app:app@postgres:5432/app_db
DATABASE_URL=sqlite:///./local.db
"""


def _standalone_readme(key: str, name: str, image: str, a2a_port: int, mcp_port: int | None) -> str:
    mcp_line = f"- MCP 전용 host 포트: `{mcp_port}` → `http://localhost:{mcp_port}/mcp`\n" if mcp_port and mcp_port != a2a_port else ""
    return f"""# {name} — Standalone 배포 번들

> 본 번들은 SeCuardian 에서 자동 생성되었습니다.
> Base agent: '{name}' ({key}) — 출처: SeCuardian

## 실행

```bash
# 1. API 키 입력
vi .env.standalone   # ANTHROPIC_API_KEY=sk-ant-...

# 2. Docker Compose 기동
docker compose up -d --build

# 3. 헬스체크
curl http://localhost:{a2a_port}/health
```

## 포트

- A2A + MCP 서비스 포트: `{a2a_port}`
  - AgentCard: `http://localhost:{a2a_port}/.well-known/agent-card.json`
  - MCP JSON-RPC: `http://localhost:{a2a_port}/mcp` (per-agent: `/mcp/{key}`)
{mcp_line}
포트 변경: `.env.standalone` 의 `AGENT_PORT` 와 `docker-compose.yml` 의 `ports` 를 함께 수정.

## 이미지 export (tar)

```bash
docker compose build
docker save -o {image.replace(":", "_").replace("/", "_")}.tar {image}
# 대상 서버: docker load -i <파일>.tar
```

## 직접 실행 (Docker 없이)

```bash
uv sync
AGENT_KEY={key} uv run uvicorn standalone.standalone_app:app --port {a2a_port}
```
"""


class StandaloneExportRequest(BaseModel):
    a2a_port: int = 8001
    mcp_port: int | None = None
    image_name: str = ""


@router.post("/{agent_key}/export-standalone")
async def export_standalone(
    agent_key: str,
    body: StandaloneExportRequest,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """에이전트 독자실행(Standalone) 배포 번들 ZIP 생성 (F27).

    포함: 플랫폼 standalone 런타임(app/·sql/·standalone/) + 에이전트 파일 +
    포트 사용자 지정 Dockerfile / docker-compose.yml / .env.standalone 자동생성.
    """
    row = await fetch_one(
        f"SELECT agent_key, agent_name, agent_type, router_path, meta_json "
        f"FROM tbl_addon_agents WHERE agent_key = {_PH}",
        (agent_key,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Addon not found")

    for port, label in ((body.a2a_port, "a2a_port"), (body.mcp_port, "mcp_port")):
        if port is not None and not (1024 <= port <= 65535):
            raise HTTPException(status_code=400, detail=f"{label} 는 1024–65535 범위여야 합니다")

    src_dir, stem = _resolve_agent_source(row)
    has_app = (src_dir / f"{stem}-app.py").exists()
    image = body.image_name.strip() or f"secuardian-agent-{agent_key}:latest"

    root = Path(".")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 플랫폼 런타임 소스
        for d in _BUNDLE_DIRS:
            for f in sorted((root / d).rglob("*")):
                rel = str(f.relative_to(root))
                if f.is_dir() or any(s in rel for s in _BUNDLE_SKIP):
                    continue
                zf.write(f, rel)
        for name in _BUNDLE_FILES:
            if (root / name).exists():
                zf.write(root / name, name)
        # 에이전트 파일 → addon-agents/deployed/{agent_key}/
        for f in sorted(src_dir.iterdir()):
            if f.is_dir() or f.suffix in (".pyc", ".zip"):
                continue
            zf.write(f, f"addon-agents/deployed/{agent_key}/{f.name}")
        # 기동 시드 + 포트 지정 설정 파일 자동생성
        seed = _standalone_seed_sql(row, stem, has_app)
        zf.writestr("sql/sqlite/03_standalone_seed.sql", seed)
        zf.writestr(
            "sql/pg/03_standalone_seed.sql",
            seed.replace("INSERT OR IGNORE", "INSERT").replace(
                ";\n", " ON CONFLICT (agent_key) DO NOTHING;\n"
            ),
        )
        zf.writestr("Dockerfile", _standalone_dockerfile(body.a2a_port))
        zf.writestr(
            "docker-compose.yml",
            _standalone_compose(agent_key, image, body.a2a_port, body.mcp_port),
        )
        zf.writestr(".env.standalone", _standalone_env(agent_key, body.a2a_port))
        zf.writestr(
            "README-standalone.md",
            _standalone_readme(agent_key, row["agent_name"], image, body.a2a_port, body.mcp_port),
        )

    buf.seek(0)
    logger.info("[addon] export-standalone %s (a2a=%d mcp=%s, by %s)",
                agent_key, body.a2a_port, body.mcp_port, user.get("sub"))
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{agent_key}-standalone.zip"'},
    )


# ── R22: 에이전트 Worker 동봉·독립 설치 — 가이드 조회·패키지 다운로드 ─────────

_MARKET_ASSETS = Path("marketplace-assets")


def _agent_worker_meta(agent_key: str) -> tuple[dict | None, Path | None]:
    """meta.json 의 worker 블록 해석 — deployed/{key}/ → marketplace-assets/*/{key}/ 폴백 (R22-3)."""
    bases = [_DEPLOYED / agent_key]
    if _MARKET_ASSETS.exists():
        bases += [
            d / agent_key
            for d in _MARKET_ASSETS.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
    for base in bases:
        if not base.is_dir():
            continue
        for meta_file in sorted(base.glob("*-meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            worker = meta.get("worker")
            if isinstance(worker, dict) and worker.get("required"):
                return worker, base
            break  # 이 base 의 meta 에 worker 없음(구버전 배포본 가능) → 다음 base 폴백
    return None, None


def _worker_summary(worker: dict, agent_key: str) -> dict:
    """활성화 응답·가이드 응답 공용 worker 요약 (R22-3)."""
    summary = {
        "required": True,
        "kind": worker.get("kind", "external"),
        "name": worker.get("name", ""),
        "version": worker.get("version", ""),
        "guide_path": f"/api/addon-agents/{agent_key}/worker-guide",
    }
    if worker.get("package"):
        summary["package"] = worker["package"]
        summary["download_path"] = f"/api/addon-agents/{agent_key}/worker-package"
    return summary


@router.get("/{agent_key}/worker-guide")
async def worker_guide(agent_key: str, user: dict = Depends(get_current_user)):
    """worker 설치 가이드 md + worker 요약 반환 — 활성화 시 프론트 모달 소스 (R22-3)."""
    if not _NAME_RE.match(agent_key):
        raise HTTPException(status_code=400, detail="invalid agent_key")
    worker, src = _agent_worker_meta(agent_key)
    if not worker:
        raise HTTPException(status_code=404, detail="worker 가 필요 없는 에이전트입니다")
    content = ""
    guide_name = worker.get("guide") or ""
    if guide_name and "/" not in guide_name and ".." not in guide_name and src:
        f = src / guide_name
        if f.exists():
            content = f.read_text(encoding="utf-8")
    return {"agent_key": agent_key, "worker": _worker_summary(worker, agent_key), "guide": content}


@router.get("/{agent_key}/worker-package")
async def worker_package(agent_key: str, user: dict = Depends(get_current_user)):
    """bundled worker 배포 패키지(zip) 다운로드 — marketplace-assets/{category}/{package} (R22-3)."""
    if not _NAME_RE.match(agent_key):
        raise HTTPException(status_code=400, detail="invalid agent_key")
    worker, _src = _agent_worker_meta(agent_key)
    if not worker or not worker.get("package"):
        raise HTTPException(status_code=404, detail="bundled worker 패키지가 없는 에이전트입니다")
    package = Path(worker["package"]).name  # 경로 성분 제거
    if _MARKET_ASSETS.exists():
        for d in _MARKET_ASSETS.iterdir():
            if d.is_dir() and (d / package).exists():
                return FileResponse(str(d / package), media_type="application/zip", filename=package)
    raise HTTPException(status_code=404, detail=f"worker 패키지 없음: {package}")


@router.patch("/{agent_key}/toggle")
async def toggle_addon(
    agent_key: str,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """Addon is_active 토글 — tbl_agent_config.is_enabled 도 동기화."""
    row = await fetch_one(
        f"SELECT is_active, router_path, api_prefix, sql_path FROM tbl_addon_agents WHERE agent_key = {_PH}", (agent_key,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Addon not found")
    new_active = 0 if row["is_active"] else 1
    await execute_write(
        f"UPDATE tbl_addon_agents SET is_active = {_PH} WHERE agent_key = {_PH}",
        (new_active, agent_key),
    )
    await execute_write(
        f"UPDATE tbl_agent_config SET is_enabled = {_PH} WHERE agent_key = {_PH}",
        (new_active, agent_key),
    )
    from app import addon_agent_loader
    if new_active and row.get("router_path"):
        if row.get("sql_path"):
            await addon_agent_loader.apply_sql(row["sql_path"])
        addon_agent_loader.load_router(agent_key, row["router_path"], row["api_prefix"])
    elif not new_active and row.get("api_prefix"):
        addon_agent_loader.unload_router(agent_key, row["api_prefix"])
        from app.services import mcp_proxy_server
        await mcp_proxy_server.stop(agent_key)
        await execute_write(
            f"DELETE FROM tbl_mcp_configs WHERE agent_key = {_PH}", (agent_key,)
        )
    result = {"agent_key": agent_key, "is_active": bool(new_active)}
    # R22-3: 활성화 시 worker 필요 에이전트 → 프론트가 설치 가이드 모달 자동 표시
    if new_active:
        worker, _src = _agent_worker_meta(agent_key)
        if worker:
            result["worker"] = _worker_summary(worker, agent_key)
    return result


@router.post("/upload")
async def upload_addon(
    file: UploadFile = File(...),
    force: bool = Form(False),
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """ZIP 업로드 → 유효성 검사 → 파일 배포 → SQL 실행 → 핫 라우터 등록 → DB 기록."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="ZIP 파일만 허용됩니다")

    raw = await file.read()
    if len(raw) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="ZIP 최대 크기 10MB 초과")

    zip_stem = Path(file.filename).stem       # e.g. "ExampleAddon"
    agent_key = zip_stem.lower()              # e.g. "exampleaddon"
    agent_name = zip_stem

    existing = await fetch_one(
        f"SELECT agent_key, is_builtin FROM tbl_addon_agents WHERE agent_key = {_PH}", (agent_key,)
    )
    cfg_pre = await fetch_one(
        f"SELECT agent_key, is_enabled FROM tbl_agent_config WHERE agent_key = {_PH}", (agent_key,)
    )

    # 내장 에이전트 키와의 충돌 판정 — 업로드 前부터 tbl_agent_config 에 존재하고(=시드된 내장)
    # addon 행은 아직 없다면, 이 업로드는 내장 에이전트의 패키지(built-in) 로 간주된다.
    if existing:
        is_builtin = int(existing.get("is_builtin") or 0)  # 재업로드 시 기존 분류 보존
    else:
        is_builtin = 1 if cfg_pre else 0

    # 내장 키 충돌은 등록 불가 — force 로도 우회할 수 없다. ADDON 목록은 is_builtin=0 만
    # 표시하므로 내장 키로 등록하면 "등록 성공인데 어느 목록에도 없는" 상태가 된다 (R22-6).
    if is_builtin:
        raise HTTPException(
            status_code=409,
            detail=_conflict_detail(agent_key, True, bool(existing)),
        )
    # 일반 중복(이미 등록된 ADDON)은 사용자 확인 후 덮어쓰기 가능
    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail=_conflict_detail(agent_key, False, True),
        )

    # ZIP 내용 검증은 **디스크에 풀기 前** 수행한다 — 등록 불가 패키지(구성 파일 미충족·
    # worker 배포본 등)가 addon-agents/deployed/ 에 남던 결함 방지 (R22-6).
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="유효하지 않은 ZIP 파일") from exc

    with zf:
        try:
            _check_safe_names(zf)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        names = set(zf.namelist())
        if f"{zip_stem}-app.py" not in names and f"{zip_stem}-front.tsx" not in names:
            raise HTTPException(status_code=400, detail=_invalid_package_message(zip_stem))

        dest = _DEPLOYED / agent_key
        newly_created = not dest.exists()
        dest.mkdir(parents=True, exist_ok=True)
        try:
            zf.extractall(dest)
        except Exception:
            if newly_created:
                shutil.rmtree(dest, ignore_errors=True)
            raise

    app_file = dest / f"{zip_stem}-app.py"
    front_file = dest / f"{zip_stem}-front.tsx"
    has_app = app_file.exists()
    has_front = front_file.exists()

    # Front TSX → front/src/pages/addon/deployed/{agent_key}.tsx
    if has_front:
        _FRONT_DEPLOYED.mkdir(parents=True, exist_ok=True)
        shutil.copy2(front_file, _FRONT_DEPLOYED / f"{agent_key}.tsx")

    # SQL 실행 (있으면)
    sql_file = dest / f"{zip_stem}-sql.sql"
    sql_path_val = str(sql_file) if sql_file.exists() else ""
    if sql_file.exists():
        sql_text = sql_file.read_text(encoding="utf-8")
        for stmt in sql_text.split(";"):
            stmt = _pg_to_sqlite(stmt.strip())
            if stmt:
                try:
                    await execute_write(stmt)
                except Exception:
                    pass  # IF NOT EXISTS 등 기존 객체 충돌 무시

    # meta.json 파싱 (F22)
    meta = _parse_meta_json(dest, zip_stem)
    agent_type = meta.get("agent_type", "app")
    meta_json_val = json.dumps(meta, ensure_ascii=False)

    # 활성 상태는 기존 설정(tbl_agent_config.is_enabled)을 따른다 — 보안 승인 전 기본 비활성인
    # 내장 에이전트를 패키지 업로드가 임의로 활성화하지 않도록 한다 (R22-6).
    is_active = int(cfg_pre.get("is_enabled") or 0) if cfg_pre else 1

    # 라우터 핫 로드 (app.py 있고 활성 상태일 때만)
    api_prefix = f"/api/addon/{agent_key}"
    if has_app and is_active:
        if not load_router(agent_key, str(app_file), api_prefix):
            # 등록 실패분이 deployed/ 에 남지 않도록 신규 생성분은 되돌린다 (R22-6)
            if newly_created:
                shutil.rmtree(dest, ignore_errors=True)
            raise HTTPException(status_code=500, detail="라우터 로드 실패 — app.py 문법 오류 확인")
    elif has_app:
        logger.info("[addon] %s 비활성 상태 — 라우터 로드 스킵 (활성화 시 로드)", agent_key)

    # DB 등록
    router_path = str(app_file) if has_app else ""
    if existing:
        await execute_write(
            f"UPDATE tbl_addon_agents SET agent_name={_PH}, router_path={_PH}, "
            f"api_prefix={_PH}, has_app={_PH}, has_front={_PH}, sql_path={_PH}, "
            f"agent_type={_PH}, meta_json={_PH}, is_active={_PH}, "
            f"uploaded_by={_PH}, uploaded_at=CURRENT_TIMESTAMP "
            f"WHERE agent_key={_PH}",
            (agent_name, router_path, api_prefix, int(has_app), int(has_front),
             sql_path_val, agent_type, meta_json_val, is_active, user["sub"], agent_key),
        )
    else:
        await execute_write(
            f"INSERT INTO tbl_addon_agents "
            f"(agent_key, agent_name, router_path, api_prefix, has_app, has_front, "
            f"sql_path, agent_type, meta_json, is_builtin, is_active, uploaded_by) "
            f"VALUES ({_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH})",
            (agent_key, agent_name, router_path, api_prefix, int(has_app), int(has_front),
             sql_path_val, agent_type, meta_json_val, is_builtin, is_active, user["sub"]),
        )

    # Agent 설정 등록 (이미 있으면 스킵) — 설명은 meta_json 기준으로 항상 최신화 (다국어 dict + 레거시)
    description = meta.get("description", "")
    description_en = meta.get("description_en", "")
    descriptions_json = json.dumps(meta.get("descriptions") or {}, ensure_ascii=False)
    await execute_write(
        f"INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, description, description_en, descriptions) "
        f"VALUES ({_PH},{_PH},1,{_PH},{_PH},{_PH}) ON CONFLICT(agent_key) DO NOTHING",
        (agent_key, agent_name, description, description_en, descriptions_json),
    )
    if description:
        await execute_write(
            f"UPDATE tbl_agent_config SET description = {_PH} WHERE agent_key = {_PH}",
            (description, agent_key),
        )
    if description_en:
        await execute_write(
            f"UPDATE tbl_agent_config SET description_en = {_PH} WHERE agent_key = {_PH}",
            (description_en, agent_key),
        )
    if meta.get("descriptions"):
        await execute_write(
            f"UPDATE tbl_agent_config SET descriptions = {_PH} WHERE agent_key = {_PH}",
            (descriptions_json, agent_key),
        )
    # R18-7 확장: meta display_name(다국어) → agent_names 동기
    if meta.get("agent_names"):
        await execute_write(
            f"UPDATE tbl_agent_config SET agent_names = {_PH} WHERE agent_key = {_PH}",
            (json.dumps(meta["agent_names"], ensure_ascii=False), agent_key),
        )

    # Capability 인덱스 등록 (F23) — meta_json의 capabilities 배열 저장
    capabilities = meta.get("capabilities", [])
    if capabilities:
        # 기존 capability 제거 후 재삽입 (force=true 대응)
        try:
            await execute_write(
                f"DELETE FROM tbl_addon_agent_capabilities WHERE agent_key = {_PH}", (agent_key,)
            )
        except Exception:
            pass
        _cap_conflict = "OR IGNORE" if _IS_SQLITE else ""
        _cap_on_conflict = "" if _IS_SQLITE else "ON CONFLICT DO NOTHING"
        for cap in capabilities:
            if not isinstance(cap, dict):
                continue
            verb = cap.get("verb", "")
            domain = cap.get("domain", "")
            if not verb or not domain:
                continue
            cap_key = f"{agent_key}.{verb}.{domain}"
            try:
                await execute_write(
                    f"INSERT {_cap_conflict} INTO tbl_addon_agent_capabilities "
                    f"(agent_key, capability_key, verb, domain, description, input_schema, output_schema, qos_json) "
                    f"VALUES ({_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH}) {_cap_on_conflict}",
                    (
                        agent_key, cap_key, verb, domain,
                        cap.get("description", ""),
                        json.dumps(cap.get("input_schema")) if cap.get("input_schema") else None,
                        json.dumps(cap.get("output_schema")) if cap.get("output_schema") else None,
                        json.dumps(cap.get("qos")) if cap.get("qos") else None,
                    ),
                )
            except Exception:
                pass

    if has_front:
        asyncio.create_task(_rebuild_web())

    front_note = " (프론트 포함 — 백그라운드 web 재빌드 시작, 약 30초 후 활성화)" if has_front else ""
    front_note_en = " (front included — web rebuild started in background, active in ~30s)" if has_front else ""
    return {
        "agent_key": agent_key,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "api_prefix": api_prefix,
        "has_app": has_app,
        "has_front": has_front,
        "is_builtin": bool(is_builtin),
        "is_active": bool(is_active),
        "message": "배포 완료" + front_note,
        "message_en": "Deployed" + front_note_en,
    }


def _extract_table_names(sql_path: str) -> list[str]:
    """SQL 파일에서 CREATE TABLE 대상 테이블명 추출."""
    try:
        src = Path(sql_path).read_text(encoding="utf-8")
        return re.findall(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)", src, re.IGNORECASE)
    except Exception:
        return []


class AddonPatch(BaseModel):
    agent_name: str | None = None


@router.patch("/{agent_key}")
async def patch_addon(
    agent_key: str,
    body: AddonPatch,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """Addon agent 속성 수정 (이름 등)."""
    row = await fetch_one(
        f"SELECT agent_key FROM tbl_addon_agents WHERE agent_key = {_PH}", (agent_key,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Addon not found")
    if body.agent_name:
        await execute_write(
            f"UPDATE tbl_addon_agents SET agent_name = {_PH} WHERE agent_key = {_PH}",
            (body.agent_name, agent_key),
        )
        await execute_write(
            f"UPDATE tbl_agent_config SET agent_name = {_PH} WHERE agent_key = {_PH}",
            (body.agent_name, agent_key),
        )
    return {"message": "Updated", "agent_key": agent_key}


async def _remove_addon_artifacts(
    agent_key: str, sql_path: str, *, delete_config: bool = True, rebuild_web: bool = True,
) -> bool:
    """addon hot-deploy 산출물 완전 정리 — delete_addon 과 marketplace uninstall 공용 (§7.6.5).

    테이블 DROP → deployed/ 디렉터리·front tsx 삭제 → MCP 중지/설정 삭제 → DB 행 삭제
    → front 있었으면 web 재빌드. 반환: front tsx 존재 여부(재빌드 시작 여부).
    라이브 라우터 완전 제거는 앱 재시작 필요(기존 계약).
    """
    # 1. addon이 생성한 테이블 DROP
    if sql_path:
        for table in _extract_table_names(sql_path):
            try:
                await execute_write(f"DROP TABLE IF EXISTS {table}")
            except Exception:
                pass

    # 2. 배포 파일 제거
    agent_dir = _DEPLOYED / agent_key
    if agent_dir.exists():
        shutil.rmtree(agent_dir)

    front_tsx = _FRONT_DEPLOYED / f"{agent_key}.tsx"
    had_front = front_tsx.exists()
    if had_front:
        front_tsx.unlink()

    # 3. MCP 포트 프로세스 종료 + 설정 삭제
    from app.services import mcp_proxy_server
    await mcp_proxy_server.stop(agent_key)
    cfg = await fetch_one(
        f"SELECT port FROM tbl_mcp_configs WHERE agent_key = {_PH} AND port IS NOT NULL",
        (agent_key,),
    )
    if cfg and cfg["port"]:
        _kill_port(int(cfg["port"]))
    await execute_write(
        f"DELETE FROM tbl_mcp_configs WHERE agent_key = {_PH}", (agent_key,)
    )

    # 4. DB 레코드 삭제 — marketplace uninstall 은 config 행을 유지(is_enabled=0, 재설치 대비)
    await execute_write(
        f"DELETE FROM tbl_addon_agents WHERE agent_key = {_PH}", (agent_key,)
    )
    if delete_config:
        await execute_write(
            f"DELETE FROM tbl_agent_config WHERE agent_key = {_PH}", (agent_key,)
        )

    if had_front and rebuild_web:
        asyncio.create_task(_rebuild_web())
    return had_front


@router.delete("/{agent_key}")
async def delete_addon(
    agent_key: str,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    row = await fetch_one(
        f"SELECT agent_key, sql_path, is_builtin FROM tbl_addon_agents WHERE agent_key = {_PH}",
        (agent_key,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Addon not found")
    if row.get("is_builtin"):
        raise HTTPException(status_code=403, detail="내장 에이전트는 삭제할 수 없습니다.")

    had_front = await _remove_addon_artifacts(agent_key, row.get("sql_path") or "")

    return {"message": f"'{agent_key}' 삭제 완료. 라우터 제거는 앱 재시작 필요." + (" 백그라운드 web 재빌드 시작." if had_front else "")}
