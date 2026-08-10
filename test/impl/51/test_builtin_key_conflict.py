"""test/impl/51 — 내장 에이전트 키 중복 업로드 처리 (SeCuardian R22-6 동일 적용).

업로드 파이프라인(upload_addon)의 중복 판정·압축 해제 시점·활성 동기화를 DB 없이 검증한다
(fetch_one/execute_write/load_router 를 모듈 네임스페이스에서 대체).
"""
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

from app.routers import router_addon_agent as mod

ROOT = Path(__file__).resolve().parents[3]
USER = {"sub": "tester"}


def _zip_bytes(stem: str, meta: dict | None = None, worker: bool = False) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        if worker:
            zf.writestr(f"{stem}/bin/README", "worker binary bundle")
        else:
            zf.writestr(f"{stem}-app.py", "from fastapi import APIRouter\nrouter = APIRouter()\n")
        if meta is not None:
            zf.writestr(f"{stem}-meta.json", json.dumps(meta, ensure_ascii=False))
    return buf.getvalue()


def _upload_file(stem: str, raw: bytes) -> UploadFile:
    return UploadFile(filename=f"{stem}.zip", file=io.BytesIO(raw))


@pytest.fixture
def fake_db(monkeypatch, tmp_path):
    state = {"addon": None, "config": None, "writes": [], "loaded": []}

    async def fake_fetch_one(sql: str, params=()):
        if "tbl_addon_agents" in sql:
            return state["addon"]
        if "tbl_agent_config" in sql:
            return state["config"]
        return None

    async def fake_execute_write(sql: str, params=()):
        state["writes"].append((sql, params))

    monkeypatch.setattr(mod, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(mod, "execute_write", fake_execute_write)
    monkeypatch.setattr(mod, "load_router", lambda k, p, x: state["loaded"].append(k) or True)
    monkeypatch.setattr(mod, "_DEPLOYED", tmp_path / "deployed")
    return state


@pytest.mark.asyncio
async def test_tc_51_01_builtin_key_rejected(fake_db):
    """내장 키 업로드 → 409 builtin_conflict, force 로도 우회 불가."""
    fake_db["config"] = {"agent_key": "vasca-cve", "is_enabled": 1}
    for force in (False, True):
        with pytest.raises(HTTPException) as exc:
            await mod.upload_addon(_upload_file("vasca-cve", _zip_bytes("vasca-cve")), force, USER)
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "builtin_conflict"
        assert exc.value.detail["overwritable"] is False
    assert fake_db["writes"] == [] and fake_db["loaded"] == []
    assert not (mod._DEPLOYED / "vasca-cve").exists()   # 압축 해제 없음


@pytest.mark.asyncio
async def test_tc_51_02_duplicate_message(fake_db):
    """기존 ADDON 재업로드 → 409 duplicate (영문 force=true 원문 제거)."""
    fake_db["addon"] = {"agent_key": "myagent", "is_builtin": 0}
    with pytest.raises(HTTPException) as exc:
        await mod.upload_addon(_upload_file("MyAgent", _zip_bytes("MyAgent")), False, USER)
    detail = exc.value.detail
    assert detail["code"] == "duplicate" and detail["overwritable"] is True
    assert "force=true" not in detail["message"]


@pytest.mark.asyncio
async def test_tc_51_03_invalid_package_not_extracted(fake_db):
    """worker 배포본 등 구성 파일 미충족 ZIP → 400 + deployed/ 미생성."""
    raw = _zip_bytes("BehaviorNotiService_worker", worker=True)
    with pytest.raises(HTTPException) as exc:
        await mod.upload_addon(_upload_file("BehaviorNotiService_worker", raw), False, USER)
    assert exc.value.status_code == 400
    assert "worker 배포 패키지" in exc.value.detail
    assert not (mod._DEPLOYED / "behaviornotiservice_worker").exists()


@pytest.mark.asyncio
async def test_tc_51_04_plain_addon_deploys_active(fake_db):
    """순수 addon → 활성 등록 + 라우터 로드, meta 의 type 폴백."""
    raw = _zip_bytes("MyAgent", {"type": "service"})
    result = await mod.upload_addon(_upload_file("MyAgent", raw), False, USER)
    assert result["is_builtin"] is False
    assert result["is_active"] is True
    assert result["agent_type"] == "service"
    assert fake_db["loaded"] == ["myagent"]


@pytest.mark.asyncio
async def test_tc_51_05_router_load_failure_rolls_back(fake_db, monkeypatch):
    """라우터 로드 실패 → 500 + 신규 배포 디렉터리 롤백."""
    monkeypatch.setattr(mod, "load_router", lambda *a, **k: False)
    with pytest.raises(HTTPException) as exc:
        await mod.upload_addon(_upload_file("BrokenAgent", _zip_bytes("BrokenAgent")), False, USER)
    assert exc.value.status_code == 500
    assert not (mod._DEPLOYED / "brokenagent").exists()


def test_tc_51_06_loader_respects_agent_config():
    src = (ROOT / "app/addon_agent_loader.py").read_text(encoding="utf-8")
    assert "LEFT JOIN tbl_agent_config" in src
    assert "COALESCE(c.is_enabled, 1) = 1" in src
    assert "소스 없음" in src            # 소스 파일 부재는 ERROR 가 아니라 경고


def test_tc_51_07_front_conflict_ui():
    api = (ROOT / "front/src/api/addonAgents.ts").read_text(encoding="utf-8")
    assert "export function parseDeployError" in api and "builtin_conflict" in api
    modal = (ROOT / "front/src/pages/agents/AgentBuilderModal.tsx").read_text(encoding="utf-8")
    assert "handleOverwrite" in modal
    assert 'conflict.code === "builtin_conflict"' in modal
    for loc in ("ko", "en"):
        keys = json.loads((ROOT / f"front/src/locales/{loc}.json").read_text(encoding="utf-8"))["agent"]
        assert {"conflictBuiltinTitle", "conflictDuplicateTitle", "conflictOverwrite"} <= set(keys)
