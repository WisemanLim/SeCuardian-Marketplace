"""test/impl/37 — 다국어 설명 authoring 소스 전환 + jp 확장 (§7.11.2-5, impl/39).

    uv run pytest test/impl/37/test_multilang_descriptions.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app

_BUILTINS = ("general", "chat", "marketplace", "workflow", "rag", "playground", "guardrails")


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")


def _headers(user_id: str = "boss", role: str = "admin") -> dict:
    token = create_access_token({"sub": user_id, "role": role, "username": user_id})
    return {"Authorization": f"Bearer {token}"}


async def _setup_db(tmp_path, monkeypatch) -> None:
    from app import db
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/test37.db")
    await db.run_migrations()  # 01_init + 02_seed


@pytest.mark.asyncio
async def test_tc37_01_seed_json_authoring(tmp_path, monkeypatch):
    """TC-37-01: 내장 7종 descriptions/agent_names JSON 에 ko/en/jp, split 컬럼은 authoring 안 함(NULL)."""
    await _setup_db(tmp_path, monkeypatch)
    from app import db
    rows = await db.fetch_all(
        "SELECT agent_key, descriptions, agent_names, description, description_en "
        "FROM tbl_agent_config WHERE agent_key IN ({})".format(
            ",".join(f"'{k}'" for k in _BUILTINS)
        )
    )
    assert len(rows) == 7
    for r in rows:
        desc = json.loads(r["descriptions"])
        names = json.loads(r["agent_names"])
        assert {"ko", "en", "jp"} <= set(desc), r["agent_key"]
        assert {"ko", "en", "jp"} <= set(names), r["agent_key"]
        assert all(desc[k].strip() for k in ("ko", "en", "jp")), r["agent_key"]
        # split 컬럼은 authoring 하지 않음
        assert not (r.get("description") or ""), r["agent_key"]
        assert not (r.get("description_en") or ""), r["agent_key"]


@pytest.mark.asyncio
async def test_tc37_02_api_returns_dicts(tmp_path, monkeypatch):
    """TC-37-02: agent-config API 가 descriptions/agent_names dict(ko/en/jp) 반환."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        agents = (await c.get("/api/agent-config/", headers=_headers())).json()["agents"]
    by = {a["agent_key"]: a for a in agents}
    for k in _BUILTINS:
        assert isinstance(by[k]["descriptions"], dict) and "jp" in by[k]["descriptions"], k
        assert isinstance(by[k]["agent_names"], dict) and "jp" in by[k]["agent_names"], k


@pytest.mark.asyncio
async def test_tc37_03_orchestrator_block_uses_descriptions(tmp_path, monkeypatch):
    """TC-37-03: _active_agents_block 이 descriptions(ko)/agent_names(ko) 기반으로 생성(레거시 NULL 무관)."""
    await _setup_db(tmp_path, monkeypatch)
    from app.agents import orchestrator
    block = await orchestrator._active_agents_block()
    assert "Orchestrator (general)" in block
    # ko 설명 일부가 포함되어야 함 (레거시 description 컬럼이 NULL 이어도 descriptions 에서 조회)
    assert "중앙 오케스트레이터" in block


def test_tc37_04_backfill_single_definition():
    """TC-37-04: db.py backfill_descriptions 중복 정의 제거 — 소스에 1개만."""
    src = Path("app/db.py").read_text(encoding="utf-8")
    assert src.count("async def backfill_descriptions(") == 1


@pytest.mark.asyncio
async def test_tc37_05_install_writes_json(tmp_path, monkeypatch):
    """TC-37-05: marketplace install(agent) 이 config 에 descriptions/agent_names JSON 기록."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.post(
            "/api/marketplace/catalog",
            headers=_headers(),
            json={"asset_key": "t37-agent", "name": "T37 에이전트", "name_en": "T37 Agent",
                  "kind": "agent", "description": "테스트 자산 설명"},
        )
        assert r.status_code == 201, r.text
        r = await c.post("/api/marketplace/install/t37-agent", headers=_headers())
        assert r.status_code == 201, r.text
    from app import db
    row = await db.fetch_one(
        f"SELECT descriptions, agent_names FROM tbl_agent_config WHERE agent_key = {db._PH}",
        ("t37-agent",),
    )
    assert row and json.loads(row["descriptions"]).get("ko") == "테스트 자산 설명"
    names = json.loads(row["agent_names"])
    assert names.get("ko") == "T37 에이전트" and names.get("en") == "T37 Agent"
