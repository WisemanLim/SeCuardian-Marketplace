"""Addon Agent 동적 핫 디플로이 로더 (F4).

참조: SmartHaccp-MultiAgent app/addon_agent_loader.py
패턴: importlib.util.spec_from_file_location → router 추출 → app.include_router()
"""
import importlib.util
import logging
import re
from pathlib import Path

from fastapi import FastAPI

logger = logging.getLogger("uvicorn.error")

_app: FastAPI | None = None
_DEPLOYED_DIR = Path("addon-agents/deployed")
_active_prefixes: set[str] = set()  # /api/addon/{key} — 활성 라우트 추적


def _pg_to_sqlite(sql: str) -> str:
    """PostgreSQL DDL → SQLite 호환 변환 (SQLite 환경에서만 적용)."""
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


async def apply_sql(sql_path: str) -> None:
    """addon SQL 파일 실행 (CREATE TABLE IF NOT EXISTS — 멱등)."""
    from app.db import execute_write
    path = Path(sql_path)
    if not path.exists():
        logger.warning("[addon_loader] sql_path 없음: %s", sql_path)
        return
    sql_text = path.read_text(encoding="utf-8")
    for stmt in sql_text.split(";"):
        stmt = _pg_to_sqlite(stmt.strip())
        if stmt:
            try:
                await execute_write(stmt)
            except Exception:
                pass  # IF NOT EXISTS 충돌 무시
    logger.info("[addon_loader] sql applied: %s", sql_path)


async def init(app: FastAPI) -> None:
    global _app
    _app = app
    await _load_all_from_disk()


async def _load_all_from_disk() -> None:
    """DB 에 등록된 활성 Addon Agent — SQL 적용 후 라우터 로드 (앱 재시작 복원)."""
    from app.db import fetch_all
    # 설정에서 비활성화된 에이전트(tbl_agent_config.is_enabled=0)는 복원하지 않는다 —
    # 보안 승인 전 기본 비활성인 내장 에이전트의 라우트가 패키지 등록만으로 열리던 결함 방지 (R22-6).
    rows = await fetch_all(
        "SELECT a.agent_key, a.router_path, a.api_prefix, a.sql_path "
        "FROM tbl_addon_agents a "
        "LEFT JOIN tbl_agent_config c ON c.agent_key = a.agent_key "
        "WHERE a.is_active = 1 AND COALESCE(c.is_enabled, 1) = 1"
    )
    count = 0
    stale = 0
    for row in rows:
        router_path = row.get("router_path") or ""
        # 소스 파일이 사라진 등록분(수동 삭제·배포 실패 잔여)은 오류가 아니라 경고로 알린다
        if router_path and not Path(router_path).exists():
            stale += 1
            logger.warning(
                "[addon_loader] %s 소스 없음 — 등록 정보만 남아 스킵: %s",
                row["agent_key"], router_path,
            )
            continue
        if row.get("sql_path"):
            await apply_sql(row["sql_path"])
        if load_router(row["agent_key"], row["router_path"], row["api_prefix"]):
            count += 1
    logger.info(
        "[addon_loader] restored %d/%d addon(s) from DB%s",
        count, len(rows), f" (소스 없음 {stale}건)" if stale else "",
    )


def _remove_routes_for_prefix(api_prefix: str) -> None:
    """app.routes 에서 해당 prefix 로 시작하는 기존 라우트 제거 (재업로드 대비)."""
    if _app is None:
        return
    _app.router.routes = [
        r for r in _app.router.routes
        if not getattr(r, "path", "").startswith(api_prefix)
    ]
    _app.openapi_schema = None  # 스키마 캐시 무효화 → 다음 openapi() 재생성


def load_router(agent_key: str, router_path: str, api_prefix: str) -> bool:
    """ZIP 배포 후 라우터 파일을 런타임에 등록."""
    if _app is None:
        logger.error("[addon_loader] app 미초기화")
        return False
    if not router_path:
        return False

    try:
        spec = importlib.util.spec_from_file_location(f"addon_{agent_key}", router_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"spec 로드 실패: {router_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        router = getattr(module, "router", None)
        if router is None:
            raise AttributeError(f"{router_path} 에 'router' 변수 없음")
        # 재업로드(force) 시 기존 라우트를 먼저 제거 — 미제거 시 옛 핸들러가
        # app.routes 앞쪽에 남아 먼저 매칭되어 코드 수정이 반영되지 않음
        _remove_routes_for_prefix(api_prefix)
        _app.include_router(router, prefix=api_prefix)
        _active_prefixes.add(api_prefix)
        logger.info("[addon_loader] loaded %s → %s", agent_key, api_prefix)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("[addon_loader] %s 로드 실패: %s", agent_key, exc)
        return False


def unload_router(agent_key: str, api_prefix: str) -> None:
    """활성 prefix 제거 — FastAPI 라우트는 런타임 삭제 불가, 미들웨어로 차단."""
    _active_prefixes.discard(api_prefix)
    logger.info("[addon_loader] unloaded %s (prefix blocked)", agent_key)


def is_active_prefix(request_path: str) -> bool:
    """요청 경로가 활성 addon prefix에 속하는지 확인."""
    for prefix in _active_prefixes:
        if request_path.startswith(prefix):
            return True
    return False
