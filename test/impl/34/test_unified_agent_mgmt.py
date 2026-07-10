"""test/impl/34 — 에이전트 통합 관리 (§7.6.1, impl/36) 검증.

    uv run pytest test/impl/34/test_unified_agent_mgmt.py -v
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app

_TEMPLATES = Path("addon-agents/_templates")
_ZIP = Path("addon-agents/zip")
_SEC_ASSETS = Path("marketplace-assets/security")
_MOVED = ("RagAgent", "ServiceAgent", "ShellAgent", "ToolProxyAgent", "UserManager")
_SECURITY_KEYS = (
    "vasca-cve", "cilium-netpol", "teler-ids", "shuffle-soar", "neosync-dlp",
    "otel-collector", "teleport-pam", "velociraptor-dfir", "ai-redteam",
    "isms-p-evidence", "behavior-noti", "agentic-soc", "ai-eval-gate",
)


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")


def _headers(user_id: str = "boss", role: str = "admin") -> dict:
    token = create_access_token({"sub": user_id, "role": role, "username": user_id})
    return {"Authorization": f"Bearer {token}"}


async def _setup_db(tmp_path, monkeypatch) -> None:
    from app import db

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/test34.db")
    await db.run_migrations()


@pytest.mark.asyncio
async def test_tc34_01_seed_base_only(tmp_path, monkeypatch):
    """TC-34-01: seed.py — 기반 시드만 (security 에이전트 config 0건)."""
    await _setup_db(tmp_path, monkeypatch)
    from scripts import seed
    await seed.main()
    from app import db
    rows = await db.fetch_all(
        "SELECT agent_key FROM tbl_agent_config WHERE nav_group = 'security'"
    )
    assert rows == []


@pytest.mark.asyncio
async def test_tc34_02_seed_security_catalog(tmp_path, monkeypatch):
    """TC-34-02: seed_security.py — 자산 13종 + blob 13종(sha256 일치), 멱등."""
    await _setup_db(tmp_path, monkeypatch)
    from scripts import seed_security
    await seed_security.main()
    await seed_security.main()  # 멱등
    from app import db
    assets = await db.fetch_all(
        "SELECT asset_key, kind, category, checksum FROM marketplace_assets WHERE category = 'security'"
    )
    assert len(assets) == 13
    assert {a["asset_key"] for a in assets} == set(_SECURITY_KEYS)
    blobs = await db.fetch_all(
        "SELECT asset_key, checksum, blob FROM marketplace_asset_blobs"
    )
    assert len(blobs) == 13
    for b in blobs:
        assert hashlib.sha256(bytes(b["blob"])).hexdigest() == b["checksum"], b["asset_key"]


@pytest.mark.asyncio
async def test_tc34_03_catalog_api_security(tmp_path, monkeypatch):
    """TC-34-03: GET /catalog?category=security — 13종, installed=false."""
    await _setup_db(tmp_path, monkeypatch)
    from scripts import seed_security
    await seed_security.main()
    async with _client() as c:
        r = await c.get("/api/marketplace/catalog", params={"category": "security"}, headers=_headers())
    assert r.status_code == 200
    assets = r.json()["assets"]
    assert len(assets) == 13
    assert all(a["installed"] is False for a in assets)
    assert all(a["kind"] == "agent" for a in assets)


@pytest.mark.asyncio
async def test_tc34_04_install_security_asset(tmp_path, monkeypatch):
    """TC-34-04: install/teler-ids — config upsert(nav_group=marketplace) + blob hot-deploy 호출."""
    await _setup_db(tmp_path, monkeypatch)
    from scripts import seed_security
    await seed_security.main()

    calls: list = []

    async def _fake_deploy(blob: bytes, asset_key: str, user: dict) -> dict:
        calls.append((asset_key, len(blob)))
        return {"status_code": 200, "body": {}}

    from app.services import addon_deploy
    monkeypatch.setattr(addon_deploy, "deploy_zip", _fake_deploy)

    async with _client() as c:
        r = await c.post("/api/marketplace/install/teler-ids", headers=_headers())
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "installed" and body["deployed"] is True
    assert calls and calls[0][0] == "teler-ids" and calls[0][1] > 0

    from app import db
    row = await db.fetch_one(
        f"SELECT nav_group, is_enabled FROM tbl_agent_config WHERE agent_key = {db._PH}",
        ("teler-ids",),
    )
    assert row and row["nav_group"] == "marketplace" and row["is_enabled"] == 1


@pytest.mark.asyncio
async def test_tc34_05_register_with_zip(tmp_path, monkeypatch):
    """TC-34-05: 자산 등록 + ZIP 첨부 업로드(스캐폴드 등록 UI 백엔드 계약)."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.post(
            "/api/marketplace/catalog",
            headers=_headers(),
            json={"asset_key": "t34-demo", "name": "T34 데모", "kind": "agent", "description": "d"},
        )
        assert r.status_code == 201, r.text

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("t34-demo-app.py", "router = None\n")
            zf.writestr("t34-demo-meta.json", json.dumps({"agent_type": "service"}))
        buf.seek(0)
        r = await c.post(
            "/api/marketplace/catalog/t34-demo/zip",
            headers=_headers(),
            files={"file": ("t34-demo.zip", buf.read(), "application/zip")},
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["asset_key"] == "t34-demo" and body["size"] > 0 and body["checksum"]


def test_tc34_06_directory_layout():
    """TC-34-06(§7.6.1-7 개정): 보안 13종 → marketplace-assets/security/, addon-agents/zip 폐지.

    상세 카테고리 레이아웃 검증은 test/impl/36 에서 수행 — 여기서는 security 이관만 확인.
    """
    for key in _SECURITY_KEYS:
        assert (_SEC_ASSETS / key).is_dir(), key
        assert (_SEC_ASSETS / f"{key}.zip").exists(), key
    assert not _ZIP.exists(), "addon-agents/zip 은 §7.6.1-7 로 폐지"


@pytest.mark.asyncio
async def test_tc34_07_templates(tmp_path, monkeypatch):
    """TC-34-07(§7.6.1-7 개정): templates list/download/scaffold — marketplace-assets/addon 기준."""
    await _setup_db(tmp_path, monkeypatch)
    async with _client() as c:
        r = await c.get("/api/addon-agents/templates/list", headers=_headers())
        named = {t["name"]: t for t in r.json()["templates"]}
        # 스캐폴드 템플릿 6종 (impl/52: UserManager utilities → addon 재이관)
        for name in ("Board", "RagAgent", "ServiceAgent", "ShellAgent", "ToolProxyAgent", "UserManager"):
            assert name in named and named[name]["has_zip"] is True, name
        assert "server-shell" not in named  # utilities 는 템플릿 아님

        r = await c.get("/api/addon-agents/templates/download/Board", headers=_headers())
        assert r.status_code == 200

        r = await c.post(
            "/api/addon-agents/scaffold",
            headers=_headers(),
            json={"agent_name": "T34Rag", "agent_type": "rag"},
        )
        assert r.status_code == 200, r.text
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            assert any(n.endswith("-app.py") for n in zf.namelist())


def test_tc34_08_locales():
    """TC-34-08: agent.system/noSystem 제거 + assetZip/assetZipHint 추가 (ko/en)."""
    for lang in ("ko", "en"):
        data = json.loads(Path(f"front/src/locales/{lang}.json").read_text(encoding="utf-8"))
        ag = data["agent"]
        assert "system" not in ag and "noSystem" not in ag, lang
        assert ag.get("assetZip") and ag.get("assetZipHint"), lang
