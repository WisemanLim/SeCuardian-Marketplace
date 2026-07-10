"""§7.6.2 asset register UX — auto asset_key, multi-ZIP registration, seed_assets, locales parity.

Fresh sqlite + TestClient (test/impl/1 패턴).
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

ROOT = Path(__file__).resolve().parents[3]

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

tok = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {tok}"}
utok = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {utok}"}

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def make_scaffold_zip(key: str, version: str = "2.0.0", desc: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", "# stub app\n")
        zf.writestr(
            f"{key}-meta.json",
            json.dumps({"agent_key": key, "name": f"{key} agent", "version": version,
                        "description": desc or f"{key} test asset"}),
        )
    return buf.getvalue()


with TestClient(m.app) as c:
    # A1) auto asset_key from name slug
    r = c.post("/api/marketplace/catalog", headers=H, json={"name": "Security Utils"})
    chk(r.status_code == 201 and r.json()["asset_key"] == "security-utils",
        f"A1 auto asset_key=security-utils ({r.status_code} {r.text[:120]})")

    # A2) collision -> suffix -2
    r = c.post("/api/marketplace/catalog", headers=H, json={"name": "Security Utils"})
    chk(r.status_code == 201 and r.json()["asset_key"] == "security-utils-2",
        f"A2 collision suffix ({r.status_code} {r.json().get('asset_key')})")

    # A3) non-ASCII name -> 'asset' fallback slug
    r = c.post("/api/marketplace/catalog", headers=H, json={"name": "한글이름"})
    chk(r.status_code == 201 and r.json()["asset_key"].startswith("asset"),
        f"A3 non-ascii fallback ({r.json().get('asset_key')})")

    # A4) explicit asset_key backward-compat
    r = c.post("/api/marketplace/catalog", headers=H, json={"asset_key": "explicit-key", "name": "Explicit"})
    chk(r.status_code == 201 and r.json()["asset_key"] == "explicit-key", "A4 explicit asset_key kept")

    # A5) explicit duplicate -> 409 (regression)
    r = c.post("/api/marketplace/catalog", headers=H, json={"asset_key": "explicit-key", "name": "Explicit"})
    chk(r.status_code == 409, "A5 explicit duplicate -> 409")

    # B1) multi-ZIP registration
    z1 = make_scaffold_zip("zip-agent-one")
    z2 = make_scaffold_zip("zip-agent-two", version="3.1.0")
    r = c.post("/api/marketplace/catalog/zip", headers=H,
               files=[("files", ("zip-agent-one.zip", z1, "application/zip")),
                      ("files", ("zip-agent-two.zip", z2, "application/zip"))])
    ok = r.status_code == 201 and len(r.json()["assets"]) == 2
    chk(ok, f"B1 multi-zip register 2 assets ({r.status_code} {r.text[:200]})")
    if ok:
        by_key = {a["asset_key"]: a for a in r.json()["assets"]}
        chk(by_key["zip-agent-one"]["name"] == "zip-agent-one agent", "B1 meta name applied")
        chk(by_key["zip-agent-two"]["version"] == "3.1.0", "B1 meta version applied")
        chk(all(a["checksum"] for a in r.json()["assets"]), "B1 checksum stored")

    # B2) idempotent re-upload (same key@version) -> no duplicate
    r = c.post("/api/marketplace/catalog/zip", headers=H,
               files=[("files", ("zip-agent-one.zip", make_scaffold_zip("zip-agent-one", desc="updated"), "application/zip"))])
    chk(r.status_code == 201, "B2 re-upload 201")
    r = c.get("/api/marketplace/catalog", headers=H)
    ones = [a for a in r.json()["assets"] if a["asset_key"] == "zip-agent-one"]
    chk(len(ones) == 1 and ones[0]["description"] == "updated", f"B2 idempotent update (rows={len(ones)})")

    # B3) non-zip -> 400
    r = c.post("/api/marketplace/catalog/zip", headers=H,
               files=[("files", ("evil.txt", b"nope", "text/plain"))])
    chk(r.status_code == 400, "B3 non-zip -> 400")

    # B4) RBAC: user -> 403
    r = c.post("/api/marketplace/catalog/zip", headers=UH,
               files=[("files", ("x.zip", z1, "application/zip"))])
    chk(r.status_code == 403, "B4 user -> 403")

    # B5) install zip-registered asset -> installed + agent_config upsert
    r = c.post("/api/marketplace/install/zip-agent-two", headers=H)
    chk(r.status_code == 201 and r.json()["status"] == "installed"
        and r.json()["agent_config_key"] == "zip-agent-two",
        f"B5 install zip asset ({r.status_code} {r.text[:160]})")

# C) seed_assets — 실 marketplace-assets 스캔 (subprocess, 동일 DB)
env = {**os.environ}
res = subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_assets.py")],
                     capture_output=True, text=True, env=env, cwd=ROOT)
chk(res.returncode == 0, f"C1 seed_assets exit 0 (stderr={res.stderr[-200:]})")

with TestClient(m.app) as c:
    r = c.get("/api/marketplace/catalog", headers=H, params={"category": "utilities"})
    utils = {a["asset_key"] for a in r.json()["assets"]}
    chk(len(utils) >= 6 and "server-shell" in utils and "caddy-proxy" in utils,
        f"C1 utilities seeded ({sorted(utils)})")
    r = c.get("/api/marketplace/catalog", headers=H, params={"category": "security"})
    sec = {a["asset_key"] for a in r.json()["assets"]}
    chk(len(sec) == 13 and "agentic-soc" in sec, f"C1 security 13 seeded ({len(sec)})")
    total_before = len(c.get("/api/marketplace/catalog", headers=H).json()["assets"])

res = subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_assets.py")],
                     capture_output=True, text=True, env=env, cwd=ROOT)
chk(res.returncode == 0, "C2 seed_assets rerun exit 0")
with TestClient(m.app) as c:
    total_after = len(c.get("/api/marketplace/catalog", headers=H).json()["assets"])
    chk(total_before == total_after, f"C2 idempotent ({total_before} == {total_after})")

# D2) locales parity
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
for sect, key in (("agent", "assetNameRequired"), ("agent", "assetNamePlaceholder"),
                  ("agent", "assetKeyAuto"), ("mp", "cat")):
    chk(key in ko[sect] and key in en[sect], f"D2 locale parity {sect}.{key}")
# impl/45(§7.6.4-5)에서 builtin 키 추가 — 기본 3키 포함 + ko/en 패리티로 검증
chk(set(ko["mp"]["cat"]) == set(en["mp"]["cat"]) >= {"security", "utilities", "general"}, "D2 mp.cat keys")
chk("assetKeyNameRequired" not in ko["agent"] and "assetKeyNameRequired" not in en["agent"],
    "D2 legacy key removed")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
