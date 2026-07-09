"""test/impl/36 — 자산 디렉터리 재구성 (§7.6.1-7, impl/38) 검증.

    uv run pytest test/impl/36/test_asset_reorg.py -v
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app

_ASSETS = Path("marketplace-assets")
_EXPECTED = {
    "security": (
        "vasca-cve", "cilium-netpol", "teler-ids", "shuffle-soar", "neosync-dlp",
        "otel-collector", "teleport-pam", "velociraptor-dfir", "ai-redteam",
        "isms-p-evidence", "behavior-noti", "agentic-soc", "ai-eval-gate",
    ),
    "builtin": ("marketplace", "workflow", "rag", "playground", "guardrails"),
    "addon": ("Board", "RagAgent", "ServiceAgent", "ShellAgent", "ToolProxyAgent"),
    "utilities": ("UserManager", "server-shell", "ai-traffic-monitor",
                  "caddy-proxy", "grafana-dashboard", "truffle-scan"),
}


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")


def _headers(user_id: str = "boss", role: str = "admin") -> dict:
    token = create_access_token({"sub": user_id, "role": role, "username": user_id})
    return {"Authorization": f"Bearer {token}"}


async def _setup_db(tmp_path, monkeypatch) -> None:
    from app import db
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/test36.db")
    await db.run_migrations()


def test_tc36_01_directory_layout():
    """TC-36-01: addon-agents/{zip,_templates} 부재, 4 카테고리 각 개수 일치."""
    assert not Path("addon-agents/zip").exists()
    assert not Path("addon-agents/_templates").exists()
    for cat, keys in _EXPECTED.items():
        dirs = sorted(d.name for d in (_ASSETS / cat).iterdir()
                      if d.is_dir() and not d.name.startswith("."))
        assert dirs == sorted(keys), cat


def test_tc36_02_pairs_and_no_prefix():
    """TC-36-02: 각 패키지 디렉터리+zip 쌍, emb_ prefix 0건."""
    for cat, keys in _EXPECTED.items():
        for key in keys:
            assert (_ASSETS / cat / key).is_dir(), f"{cat}/{key}"
            assert (_ASSETS / cat / f"{key}.zip").exists(), f"{cat}/{key}.zip"
            assert not key.startswith("emb_"), key


@pytest.mark.asyncio
async def test_tc36_03_templates_list_addon_only(tmp_path, monkeypatch):
    """TC-36-03: templates/list = addon/ 5종만 (utilities/builtin 미포함)."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.get("/api/addon-agents/templates/list", headers=_headers())
    assert r.status_code == 200
    names = {t["name"] for t in r.json()["templates"]}
    assert names == set(_EXPECTED["addon"])


@pytest.mark.asyncio
async def test_tc36_04_download(tmp_path, monkeypatch):
    """TC-36-04: download/Board 200, utilities UserManager 404."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.get("/api/addon-agents/templates/download/Board", headers=_headers())
        assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
        r404 = await c.get("/api/addon-agents/templates/download/UserManager", headers=_headers())
        assert r404.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("agent_type", ["app", "service", "tool-proxy", "rag", "shell"])
async def test_tc36_05_scaffold(tmp_path, monkeypatch, agent_type):
    """TC-36-05: 스캐폴드 — marketplace-assets/addon 조회로 유형별 zip 생성."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.post(
            "/api/addon-agents/scaffold",
            headers=_headers(),
            json={"agent_name": f"T36{agent_type.replace('-', '').capitalize()}",
                  "agent_type": agent_type},
        )
    assert r.status_code == 200, r.text
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert any(n.endswith("-app.py") for n in zf.namelist())


def test_tc36_06_guardrails_structure():
    """TC-36-06: builtin/guardrails.zip — data/guardrails 구조 보존."""
    with zipfile.ZipFile(_ASSETS / "builtin" / "guardrails.zip") as zf:
        names = zf.namelist()
    assert "guardrails-app.py" in names
    assert any(n.startswith("data/guardrails/") and n.endswith(".json") for n in names)


@pytest.mark.asyncio
async def test_tc36_07_seed_security_still_works(tmp_path, monkeypatch):
    """TC-36-07: seed_security — security 경로 무변경, 자산 13종 등록."""
    await _setup_db(tmp_path, monkeypatch)
    from scripts import seed_security
    await seed_security.main()
    from app import db
    rows = await db.fetch_all(
        "SELECT asset_key FROM marketplace_assets WHERE category = 'security'"
    )
    assert {r["asset_key"] for r in rows} == set(_EXPECTED["security"])
