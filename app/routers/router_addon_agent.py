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
from app.db import execute_write, fetch_all, fetch_one, _PH, _IS_SQLITE

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/addon-agents", tags=["addon-agents"])

_DEPLOYED = Path("addon-agents/deployed")
_TEMPLATES = Path("addon-agents/_templates")
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


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    """경로 탐색 공격 방지: '..' 또는 절대 경로 포함 항목 차단."""
    for member in zf.namelist():
        if ".." in member or member.startswith("/"):
            raise ValueError(f"Unsafe path in ZIP: {member}")
    zf.extractall(dest)


def _norm_descriptions(meta: dict) -> dict:
    """R18-7: meta 의 description 을 다국어 dict 로 정규화.

    허용 형식 — ① dict 형: description={"ko": "...", "en": "..."} (확장형, 타 언어 키 허용)
               ② 레거시: description(문자열=ko) + description_en(문자열=en)
    정규화 후 meta 에는 세 키가 모두 존재: description(ko 문자열, 하위호환),
    description_en(en 문자열, 하위호환), descriptions(dict).
    """
    desc = meta.get("description")
    d: dict[str, str] = {}
    if isinstance(desc, dict):
        d = {k: v for k, v in desc.items() if isinstance(v, str) and v.strip()}
    elif isinstance(desc, str) and desc.strip():
        d["ko"] = desc.strip()
    en = meta.get("description_en")
    if isinstance(en, str) and en.strip():
        d.setdefault("en", en.strip())
    # dict 형이 넘어온 경우에도 legacy 키 병행 유지
    existing = meta.get("descriptions")
    if isinstance(existing, dict):
        for k, v in existing.items():
            if isinstance(v, str) and v.strip():
                d.setdefault(k, v.strip())
    meta["descriptions"] = d
    meta["description"] = d.get("ko", "")
    meta["description_en"] = d.get("en", "")
    # R18-7 확장: display_name 도 dict 형(다국어) 허용 → agent_names 정규화
    disp = meta.get("display_name")
    names: dict[str, str] = {}
    if isinstance(disp, dict):
        names = {k: v for k, v in disp.items() if isinstance(v, str) and v.strip()}
    elif isinstance(disp, str) and disp.strip():
        names["ko"] = disp.strip()
    existing_names = meta.get("agent_names")
    if isinstance(existing_names, dict):
        for k, v in existing_names.items():
            if isinstance(v, str) and v.strip():
                names.setdefault(k, v.strip())
    meta["agent_names"] = names
    meta["display_name"] = names.get("ko", "") or (disp if isinstance(disp, str) else "")
    return meta


def _parse_meta_json(dest: Path, zip_stem: str) -> dict:
    """ZIP 내 {AgentName}-meta.json 파싱. 없으면 기본값(type=app) 반환."""
    meta_file = dest / f"{zip_stem}-meta.json"
    if not meta_file.exists():
        return _norm_descriptions({"agent_type": "app", "capabilities": []})
    try:
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        if data.get("agent_type") not in _VALID_TYPES:
            data["agent_type"] = "app"
        return _norm_descriptions(data)
    except Exception:
        return _norm_descriptions({"agent_type": "app", "capabilities": []})


@router.get("/templates/list")
async def list_templates(user: dict = Depends(get_current_user)):
    if not _TEMPLATES.exists():
        return {"templates": []}
    templates = []
    for d in sorted(_TEMPLATES.iterdir()):
        if not d.is_dir():
            continue
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
            "has_zip": (_TEMPLATES / f"{d.name}.zip").exists(),
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
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Template zip not found")
    return FileResponse(str(zip_path), media_type="application/zip", filename=f"{name}.zip")


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
    tmpl_dir = _TEMPLATES / tmpl_dir_name
    if not tmpl_dir.exists():
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
    return {"agent_key": agent_key, "is_active": bool(new_active)}


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
    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail=f"'{agent_key}' already exists. Use force=true to overwrite.",
        )

    # 내장 에이전트 키와의 충돌 판정 — 업로드 前부터 tbl_agent_config 에 존재하고(=시드된 내장)
    # addon 행은 아직 없다면, 이 업로드는 내장 에이전트의 패키지(built-in) 로 간주해 is_builtin=1 로 표시한다.
    # → 에이전트 관리 UI/AI 어시스턴트 목록이 addon(is_builtin=0)만 ADDON 으로 분류하므로,
    #    내장이 ADDON 목록으로 이중 노출되어 내장 목록에서 사라지고 ADDON 갯수가 부풀려지던 결함을 방지.
    if existing:
        is_builtin = int(existing.get("is_builtin") or 0)  # 재업로드 시 기존 분류 보존
    else:
        cfg_pre = await fetch_one(
            f"SELECT agent_key FROM tbl_agent_config WHERE agent_key = {_PH}", (agent_key,)
        )
        is_builtin = 1 if cfg_pre else 0

    dest = _DEPLOYED / agent_key
    dest.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            _safe_extract(zf, dest)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="유효하지 않은 ZIP 파일")

    app_file = dest / f"{zip_stem}-app.py"
    front_file = dest / f"{zip_stem}-front.tsx"
    has_app = app_file.exists()
    has_front = front_file.exists()

    if not has_app and not has_front:
        raise HTTPException(
            status_code=400,
            detail=f"{zip_stem}-app.py 또는 {zip_stem}-front.tsx 중 하나가 ZIP에 있어야 합니다",
        )

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

    # 라우터 핫 로드 (app.py 있을 때만)
    api_prefix = f"/api/addon/{agent_key}"
    ok = False
    if has_app:
        ok = load_router(agent_key, str(app_file), api_prefix)
        if not ok:
            raise HTTPException(status_code=500, detail="라우터 로드 실패 — app.py 문법 오류 확인")

    # DB 등록
    router_path = str(app_file) if has_app else ""
    if existing:
        await execute_write(
            f"UPDATE tbl_addon_agents SET agent_name={_PH}, router_path={_PH}, "
            f"api_prefix={_PH}, has_app={_PH}, has_front={_PH}, sql_path={_PH}, "
            f"agent_type={_PH}, meta_json={_PH}, "
            f"uploaded_by={_PH}, uploaded_at=CURRENT_TIMESTAMP "
            f"WHERE agent_key={_PH}",
            (agent_name, router_path, api_prefix, int(has_app), int(has_front),
             sql_path_val, agent_type, meta_json_val, user["sub"], agent_key),
        )
    else:
        await execute_write(
            f"INSERT INTO tbl_addon_agents "
            f"(agent_key, agent_name, router_path, api_prefix, has_app, has_front, "
            f"sql_path, agent_type, meta_json, is_builtin, uploaded_by) "
            f"VALUES ({_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH},{_PH})",
            (agent_key, agent_name, router_path, api_prefix, int(has_app), int(has_front),
             sql_path_val, agent_type, meta_json_val, is_builtin, user["sub"]),
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

    return {
        "agent_key": agent_key,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "api_prefix": api_prefix,
        "has_app": has_app,
        "has_front": has_front,
        "message": "배포 완료" + (" (프론트 포함 — 백그라운드 web 재빌드 시작, 약 30초 후 활성화)" if has_front else ""),
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

    # 1. addon이 생성한 테이블 DROP
    sql_path = row.get("sql_path") or ""
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

    # 4. DB 레코드 삭제
    await execute_write(
        f"DELETE FROM tbl_addon_agents WHERE agent_key = {_PH}", (agent_key,)
    )
    await execute_write(
        f"DELETE FROM tbl_agent_config WHERE agent_key = {_PH}", (agent_key,)
    )

    if had_front:
        asyncio.create_task(_rebuild_web())

    return {"message": f"'{agent_key}' 삭제 완료. 라우터 제거는 앱 재시작 필요." + (" 백그라운드 web 재빌드 시작." if had_front else "")}
