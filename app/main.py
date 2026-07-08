"""secuardian — FastAPI entrypoint.

참조: SmartHaccp-MultiAgent app/main.py
"""
from contextlib import asynccontextmanager

import json

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings


def _cors_list(raw: str) -> list[str]:
    """JSON array OR comma-separated string → list[str]."""
    v = raw.strip()
    if not v:
        return ["http://localhost:4100"]
    if v.startswith("["):
        return json.loads(v)
    return [o.strip() for o in v.split(",") if o.strip()]

# [CUSTOMIZE] 도메인 라우터 추가 시 여기에 import
from app.routers import (
    router_auth,
    router_users,
    router_agent,
    router_chat_history,  # 사용자별 대화이력 + 만족도 피드백 (R18-2, R18-3)
    router_suggestions,   # 관리자 건의전달 (R18-4)
    router_addon_agent,   # Addon Agent 핫디플로이 (ZIP 업로드·무중단 마운트)
    router_settings,
    router_setup,
    router_agent_config,
    router_agent_registry,
    router_a2a,
    router_mcp,
    router_mcp_config,
    router_marketplace,   # Marketplace 내장 에이전트 (F-MP)
    router_workflow,      # Workflow 내장 에이전트 (F-WF)
    router_rag,           # RAG 내장 에이전트 (F-RAG)
    router_playground,    # Playground 내장 에이전트 (F-PG)
    router_guardrails,    # Guardrails 내장 에이전트 (F-GRD)
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: 컬럼 마이그레이션(기존 DB ALTER) → DB 마이그레이션(init+seed) → 기본 관리자 시드 → Addon 로더
    # 컬럼 ALTER 를 먼저 실행해야 02_seed.sql 이 신규 컬럼(description 등)을 참조해도 기존 DB에서 실패하지 않는다.
    from app.db import apply_column_migrations, run_migrations, seed_default_admin
    from app.addon_agent_loader import init as addon_init

    await apply_column_migrations()
    await run_migrations()
    await seed_default_admin()
    await addon_init(app)
    from app.services import mcp_proxy_server
    await mcp_proxy_server.init_from_db()  # tbl_mcp_configs 기준 MCP proxy 서버 복원

    # Ollama 예열 — 콜드스타트 첫 토큰 지연 방지 (백그라운드, best-effort)
    import asyncio
    warmup_task: asyncio.Task | None = None
    if settings.ollama_warmup_enabled:
        from app.services.ollama_warmup import warmup_loop
        warmup_task = asyncio.create_task(warmup_loop(), name="ollama-warmup")

    yield
    # shutdown
    if warmup_task:
        warmup_task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def addon_guard(request: Request, call_next):
    """비활성 addon API 요청 차단."""
    path = request.url.path
    if path.startswith("/api/addon/"):
        from app.addon_agent_loader import is_active_prefix
        if not is_active_prefix(path):
            return JSONResponse({"detail": "비활성화된 에이전트입니다."}, status_code=404)
    return await call_next(request)


app.include_router(router_auth.router)
app.include_router(router_users.router)
app.include_router(router_agent.router)
app.include_router(router_chat_history.router)  # 대화이력·피드백 (R18-2, R18-3)
app.include_router(router_suggestions.router)   # 관리자 건의 (R18-4)
app.include_router(router_addon_agent.router)   # Addon Agent 핫디플로이
app.include_router(router_settings.router)
app.include_router(router_setup.router)
app.include_router(router_agent_config.router)
app.include_router(router_agent_registry.router)
app.include_router(router_a2a.router)        # A2A Protocol v1.0 (F12)
app.include_router(router_mcp.router)        # MCP JSON-RPC 2.0 (F12)
app.include_router(router_mcp_config.router) # MCP Proxy 설정 관리 (F12)
app.include_router(router_marketplace.router)  # Marketplace 내장 에이전트 (F-MP)
app.include_router(router_workflow.router)      # Workflow 내장 에이전트 (F-WF)
app.include_router(router_rag.router)           # RAG 내장 에이전트 (F-RAG)
app.include_router(router_playground.router)    # Playground 내장 에이전트 (F-PG)
app.include_router(router_guardrails.router)    # Guardrails 내장 에이전트 (F-GRD)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "env": settings.env,
        "mode": "standalone" if settings.agent_standalone else "embedded",
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus 스크레이프 엔드포인트 (deploy/config/prometheus/prometheus.yml 의 secuardian-api job).

    기본 레지스트리(프로세스·GC 메트릭)를 노출한다. 도메인 메트릭은 필요 시
    prometheus_client Counter/Gauge 로 추가한다.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
