"""test/impl/52 — 설치·배포 경로 중복 확인 일원화 (SeCuardian R22-7 동일 적용).

로컬 install 의 중복 판정(_check_install_conflict), deploy_zip 의 force 전달,
스캐폴드 사전 확인(key-check), worker→에이전트 링크를 DB 없이 검증한다.
"""
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.routers import router_addon_agent as addon_mod
from app.routers import router_marketplace as mp
from app.routers import router_marketplace_host as host

ROOT = Path(__file__).resolve().parents[3]
USER = {"sub": "tester"}
ASSET = {"asset_key": "vasca-cve", "version": "1.0.0", "kind": "agent"}


@pytest.fixture
def fake_rows(monkeypatch):
    """fetch_one 응답 지정 — {'config': …, 'install': …}."""
    state = {"config": None, "install": None}

    async def fake_fetch_one(sql: str, params=()):
        if "tbl_agent_config" in sql:
            return state["config"]
        if "marketplace_installs" in sql:
            return state["install"]
        return None

    monkeypatch.setattr(mp, "fetch_one", fake_fetch_one)
    return state


# ── TC-52-01~05: 로컬 install 중복 판정 ──────────────────────────────────────

@pytest.mark.asyncio
async def test_tc_52_01_agent_config_occupied(fake_rows):
    fake_rows["config"] = {"agent_key": "vasca-cve", "nav_group": "security"}
    with pytest.raises(HTTPException) as exc:
        await mp._check_install_conflict(ASSET, "default", False)
    assert exc.value.status_code == 409
    detail = exc.value.detail
    assert detail["code"] == "install_conflict"
    assert detail["reason"] == "agent_config_occupied"
    assert detail["overwritable"] is True
    assert detail["message"] and detail["message_en"]


@pytest.mark.asyncio
async def test_tc_52_02_same_version_already_active(fake_rows):
    fake_rows["install"] = {"id": 7}
    with pytest.raises(HTTPException) as exc:
        await mp._check_install_conflict(ASSET, "default", False)
    assert exc.value.detail["reason"] == "already_installed"
    assert "1.0.0" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_tc_52_03_no_conflict_passes(fake_rows):
    await mp._check_install_conflict(ASSET, "default", False)   # 예외 없음


@pytest.mark.asyncio
async def test_tc_52_04_force_skips_checks(fake_rows):
    fake_rows["config"] = {"agent_key": "vasca-cve", "nav_group": "security"}
    fake_rows["install"] = {"id": 7}
    await mp._check_install_conflict(ASSET, "default", True)     # 확인 후 진행


@pytest.mark.asyncio
async def test_tc_52_05_marketplace_origin_config_ok(fake_rows):
    """자기 출처(마켓플레이스 설치본) 설정 행은 중복 확인 대상 아님."""
    fake_rows["config"] = {"agent_key": "vasca-cve", "nav_group": "marketplace"}
    await mp._check_install_conflict(ASSET, "default", False)


# ── TC-52-06: deploy_zip force 전달 ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_tc_52_06_deploy_zip_force_flag(monkeypatch):
    from app.services import addon_deploy

    sent: list[dict] = []

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"agent_key": "x"}

    class _Client:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, files=None, data=None):
            sent.append(data)
            return _Resp()

    monkeypatch.setattr(addon_deploy.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(addon_deploy.httpx, "ASGITransport", lambda app: None)
    monkeypatch.setattr(addon_deploy, "create_access_token", lambda claims: "tok")
    monkeypatch.setitem(__import__("sys").modules, "app.main", type("M", (), {"app": object()}))

    await addon_deploy.deploy_zip(b"zip", "vasca-cve", USER, force=False)
    await addon_deploy.deploy_zip(b"zip", "vasca-cve", USER, force=True)
    assert [d["force"] for d in sent] == ["false", "true"]


# ── TC-52-07: 원격 install 은 409 를 흡수하지 않는다 ─────────────────────────

def test_tc_52_07_remote_install_surfaces_409():
    src = (ROOT / "app/routers/router_marketplace_remote.py").read_text(encoding="utf-8")
    assert "force=body.force" in src
    assert 'deploy_result.get("status_code") == 409' in src
    assert "raise HTTPException(409, detail)" in src


# ── TC-52-08: 스캐폴드 사전 확인 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tc_52_08_key_check(monkeypatch):
    state = {"addon": None, "config": None}

    async def fake_fetch_one(sql: str, params=()):
        if "tbl_addon_agents" in sql:
            return state["addon"]
        if "tbl_agent_config" in sql:
            return state["config"]
        return None

    monkeypatch.setattr(addon_mod, "fetch_one", fake_fetch_one)

    assert (await addon_mod.key_check("FreshName", USER))["available"] is True

    state["config"] = {"agent_key": "vasca-cve"}
    r = await addon_mod.key_check("vasca-cve", USER)
    assert r["available"] is False and r["conflict"]["code"] == "builtin_conflict"

    state["addon"] = {"agent_key": "myagent", "is_builtin": 0}
    r = await addon_mod.key_check("MyAgent", USER)
    assert r["conflict"]["code"] == "duplicate" and r["agent_key"] == "myagent"

    with pytest.raises(HTTPException) as exc:
        await addon_mod.key_check("bad..key", USER)
    assert exc.value.status_code == 400


# ── TC-52-09: worker → 짝 에이전트 링크 ─────────────────────────────────────

def test_tc_52_09_worker_agent_key_exposed():
    cat = ROOT / "marketplace-assets/security"
    pairs = {"BehaviorNotiService_worker": "behavior-noti", "VASCA_worker": "vasca-cve"}
    for worker, agent in pairs.items():
        entry = host._asset_entry(cat, cat / f"{worker}.zip")
        assert entry["kind"] == "worker"
        assert entry["agent_key"] == agent
        assert (cat / f"{agent}.zip").exists()
    assert host._asset_entry(cat, cat / "behavior-noti.zip")["agent_key"] == ""


# ── TC-52-10: 프론트 배선 ────────────────────────────────────────────────────

def test_tc_52_10_front_wiring():
    page = (ROOT / "front/src/pages/marketplace/MarketplacePage.tsx").read_text(encoding="utf-8")
    assert "confirmInstall" in page and "handleConfirmInstall" in page
    assert "installAsset(a.asset_key, a.version, force)" in page
    assert "remoteInstall(a.asset_key, a.checksum, force)" in page

    api = (ROOT / "front/src/api/marketplace.ts").read_text(encoding="utf-8")
    assert "force = false" in api
    rapi = (ROOT / "front/src/api/marketplaceRemote.ts").read_text(encoding="utf-8")
    assert "force = false" in rapi

    addon_api = (ROOT / "front/src/api/addonAgents.ts").read_text(encoding="utf-8")
    assert "checkAgentKey" in addon_api and "/addon-agents/key-check/" in addon_api

    builder = (ROOT / "front/src/pages/agents/AgentBuilderModal.tsx").read_text(encoding="utf-8")
    assert "nameConflict" in builder and "scConflict" in builder
    assert "handleDeploy(force = false)" in builder
    assert "onClick={handleDeploy}" not in builder

    for loc in ("ko", "en"):
        d = json.loads((ROOT / f"front/src/locales/{loc}.json").read_text(encoding="utf-8"))
        for k in ("installConflictTitle", "installOverwrite", "installFailed"):
            assert k in d["mp"], f"{loc} mp.{k} 누락"
