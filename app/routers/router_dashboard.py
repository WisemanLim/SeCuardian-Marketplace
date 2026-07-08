"""router_dashboard (F-WEB) — /api/dashboard.

대시보드 실시간 위젯용 집계 엔드포인트. 기존 테이블을 읽어 카운트·최근 활동을 요약한다.
프론트가 주기적으로 폴링해 서버 상태·에이전트·최근 실행/판정을 표시한다.
"""
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import _PH, fetch_all, fetch_one

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


async def _count(sql: str, params: tuple = ()) -> int:
    row = await fetch_one(sql, params)
    return int((row or {}).get("n", 0))


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user)):
    """서버·에이전트·내장 에이전트 실행/판정 요약(실시간 폴링 대상)."""
    tid = _tenant()
    agents_total = await _count("SELECT COUNT(*) AS n FROM tbl_agent_config")
    agents_enabled = await _count("SELECT COUNT(*) AS n FROM tbl_agent_config WHERE is_enabled = 1")
    addons_active = await _count("SELECT COUNT(*) AS n FROM tbl_addon_agents WHERE is_active = 1")

    # 내장 에이전트 활동(테이블 존재 전제 — 마이그레이션으로 항상 생성됨)
    mp_assets = await _count(f"SELECT COUNT(*) AS n FROM marketplace_assets WHERE tenant_id = {_PH}", (tid,))
    mp_installed = await _count(
        f"SELECT COUNT(*) AS n FROM marketplace_installs WHERE tenant_id = {_PH} AND active = 1", (tid,))
    wf_total = await _count(f"SELECT COUNT(*) AS n FROM workflows WHERE tenant_id = {_PH}", (tid,))
    wf_runs = await _count(f"SELECT COUNT(*) AS n FROM workflow_runs WHERE tenant_id = {_PH}", (tid,))
    wf_waiting = await _count(
        f"SELECT COUNT(*) AS n FROM workflow_runs WHERE tenant_id = {_PH} AND status = 'waiting_hitl'", (tid,))
    rag_collections = await _count(f"SELECT COUNT(*) AS n FROM rag_collections WHERE tenant_id = {_PH}", (tid,))
    pg_runs = await _count(f"SELECT COUNT(*) AS n FROM playground_runs WHERE tenant_id = {_PH}", (tid,))
    pg_tok_row = await fetch_one(
        f"SELECT COALESCE(SUM(input_tokens),0) AS i, COALESCE(SUM(output_tokens),0) AS o "
        f"FROM playground_runs WHERE tenant_id = {_PH}", (tid,))
    pg_tokens = int((pg_tok_row or {}).get("i", 0)) + int((pg_tok_row or {}).get("o", 0))
    grd_decisions = await _count(f"SELECT COUNT(*) AS n FROM guardrails_decision_log WHERE tenant_id = {_PH}", (tid,))
    grd_blocked = await _count(
        f"SELECT COUNT(*) AS n FROM guardrails_decision_log WHERE tenant_id = {_PH} "
        f"AND decision IN ('block','escalate')", (tid,))

    return {
        "server": {"status": "ok", "env": settings.env,
                   "guardrails_enabled": settings.guardrails_enabled,
                   "vector_backend": settings.vector_backend},
        "agents": {"total": agents_total, "enabled": agents_enabled, "addons_active": addons_active},
        "marketplace": {"assets": mp_assets, "installed": mp_installed},
        "workflow": {"total": wf_total, "runs": wf_runs, "waiting_hitl": wf_waiting},
        "rag": {"collections": rag_collections},
        "playground": {"runs": pg_runs, "tokens": pg_tokens},
        "guardrails": {"decisions": grd_decisions, "blocked": grd_blocked},
    }


@router.get("/activity")
async def activity(limit: int = 10, user: dict = Depends(get_current_user)):
    """최근 활동 스트림 — 워크플로우 run·플레이그라운드 실행·가드레일 판정 최신순 병합."""
    tid = _tenant()
    lim = min(limit, 50)
    wf = await fetch_all(
        f"SELECT id, workflow_id, status, created_at FROM workflow_runs WHERE tenant_id = {_PH} "
        f"ORDER BY id DESC LIMIT {_PH}", (tid, lim))
    pg = await fetch_all(
        f"SELECT id, provider, latency_ms, created_at FROM playground_runs WHERE tenant_id = {_PH} "
        f"ORDER BY id DESC LIMIT {_PH}", (tid, lim))
    grd = await fetch_all(
        f"SELECT id, agent_key, decision, created_at FROM guardrails_decision_log WHERE tenant_id = {_PH} "
        f"ORDER BY id DESC LIMIT {_PH}", (tid, lim))
    items = (
        [{"kind": "workflow", "ts": r.get("created_at"), "detail": f"run #{r['id']} → {r['status']}"} for r in wf]
        + [{"kind": "playground", "ts": r.get("created_at"), "detail": f"run #{r['id']} ({r['provider']}, {r['latency_ms']}ms)"} for r in pg]
        + [{"kind": "guardrails", "ts": r.get("created_at"), "detail": f"{r['agent_key']} → {r['decision']}"} for r in grd]
    )
    items.sort(key=lambda x: str(x.get("ts") or ""), reverse=True)
    return {"activity": items[:lim]}
