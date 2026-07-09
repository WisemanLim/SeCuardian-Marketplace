"""test/impl/35 — emb_ 규약 폐지 (§7.6.1-6, impl/37) 검증.

    uv run pytest test/impl/35/test_prefix_removal.py -v
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from app.core.config import settings

# §7.6.1-7: addon-agents/zip 폐지 → marketplace-assets/<카테고리>/
_ASSETS = Path("marketplace-assets")
_SEC_ASSETS = _ASSETS / "security"
_BUILTIN = _ASSETS / "builtin"
_SECURITY_KEYS = (
    "vasca-cve", "cilium-netpol", "teler-ids", "shuffle-soar", "neosync-dlp",
    "otel-collector", "teleport-pam", "velociraptor-dfir", "ai-redteam",
    "isms-p-evidence", "behavior-noti", "agentic-soc", "ai-eval-gate",
)


def test_tc35_01_no_prefix_layout():
    """TC-35-01(§7.6.1-7 개정): addon-agents/zip 폐지, marketplace-assets 하위에 emb_* 0건."""
    assert not Path("addon-agents/zip").exists()
    for cat in ("security", "builtin", "addon", "utilities"):
        d = _ASSETS / cat
        assert d.is_dir(), cat
        assert not any(x.name.startswith("emb_") for x in d.iterdir()), cat


def test_tc35_02_security_assets_naming():
    """TC-35-02: security 자산 13종(무 prefix) — meta key == 디렉터리명."""
    dirs = sorted(d.name for d in _SEC_ASSETS.iterdir() if d.is_dir())
    assert dirs == sorted(_SECURITY_KEYS)
    for key in _SECURITY_KEYS:
        meta = json.loads((_SEC_ASSETS / key / f"{key}-meta.json").read_text(encoding="utf-8"))
        # meta 는 key 또는 agent_key 필드 사용 (패키지별 상이)
        assert (meta.get("key") or meta.get("agent_key")) == key, key
        with zipfile.ZipFile(_SEC_ASSETS / f"{key}.zip") as zf:
            names = set(zf.namelist())
        assert f"{key}-app.py" in names and f"{key}-meta.json" in names, key


@pytest.mark.asyncio
async def test_tc35_03_seed_security_plain_blobs(tmp_path, monkeypatch):
    """TC-35-03: seed_security — blob filename {key}.zip, sha256 일치."""
    from app import db

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/test35.db")
    await db.run_migrations()
    from scripts import seed_security
    await seed_security.main()
    blobs = await db.fetch_all(
        "SELECT asset_key, filename, checksum, blob FROM marketplace_asset_blobs"
    )
    assert len(blobs) == 13
    for b in blobs:
        assert b["filename"] == f"{b['asset_key']}.zip", b["filename"]
        assert hashlib.sha256(bytes(b["blob"])).hexdigest() == b["checksum"], b["asset_key"]


def test_tc35_04_guardrails_zip_structure():
    """TC-35-04(§7.6.1-7 개정): guardrails.zip(builtin/) — app/meta + data/guardrails 구조 보존."""
    with zipfile.ZipFile(_BUILTIN / "guardrails.zip") as zf:
        names = zf.namelist()
    assert "guardrails-app.py" in names
    assert "guardrails-meta.json" in names
    assert any(n.startswith("data/guardrails/") and n.endswith(".json") for n in names)


def test_tc35_05_no_emb_strings():
    """TC-35-05(§7.6.1-7 개정): marketplace-assets/ 텍스트 소스에 emb_ 0건."""
    hits = []
    for f in _ASSETS.rglob("*"):
        if f.suffix in (".py", ".json", ".sql", ".md", ".tsx"):
            if "emb_" in f.read_text(encoding="utf-8", errors="ignore"):
                hits.append(str(f))
    assert hits == [], hits
