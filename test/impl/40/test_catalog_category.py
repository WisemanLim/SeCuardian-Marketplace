"""§7.6.3 catalog category — category-preset registration, db-fresh seed chain, modal refactor.

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

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def make_scaffold_zip(key: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", "# stub\n")
        zf.writestr(f"{key}-meta.json",
                    json.dumps({"agent_key": key, "name": f"{key} agent", "version": "1.0.0",
                                "description": f"{key} desc"}))
    return buf.getvalue()


with TestClient(m.app) as c:
    # A1) meta registration with category (per-catalog add — form path)
    r = c.post("/api/marketplace/catalog", headers=H,
               json={"name": "Sec Extra Agent", "category": "security"})
    chk(r.status_code == 201 and r.json()["category"] == "security"
        and r.json()["asset_key"] == "sec-extra-agent",
        f"A1 meta register category=security ({r.status_code} {r.json().get('category')})")

    # A2) multi-ZIP registration with category preset
    r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "utilities"},
               files=[("files", ("util-extra.zip", make_scaffold_zip("util-extra"), "application/zip"))])
    chk(r.status_code == 201 and r.json()["assets"][0]["category"] == "utilities",
        f"A2 zip register category=utilities ({r.status_code})")

    # A3) category filter returns them
    r = c.get("/api/marketplace/catalog", headers=H, params={"category": "utilities"})
    chk(any(a["asset_key"] == "util-extra" for a in r.json()["assets"]), "A3 category filter")

# B1) seed_security + seed_assets (db-fresh 체인 후반) — 격리 DB
env = {**os.environ}
for script in ("seed_security.py", "seed_assets.py"):
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                         capture_output=True, text=True, env=env, cwd=ROOT)
    chk(res.returncode == 0, f"B1 {script} exit 0 (stderr={res.stderr[-150:]})")

with TestClient(m.app) as c:
    sec = {a["asset_key"] for a in c.get("/api/marketplace/catalog", headers=H,
                                         params={"category": "security"}).json()["assets"]}
    utils = {a["asset_key"] for a in c.get("/api/marketplace/catalog", headers=H,
                                           params={"category": "utilities"}).json()["assets"]}
    # 13 seeded + sec-extra-agent(A1 에서 카테고리 추가 등록) = 14
    chk(len(sec) == 14 and {"agentic-soc", "vasca-cve", "sec-extra-agent"} <= sec,
        f"B1 security 13+1 ({len(sec)})")
    # utilities 5 seeded + util-extra from A2 (impl/52: UserManager 는 addon 으로 이관)
    chk(len(utils) == 6 and {"server-shell", "caddy-proxy", "util-extra"} <= utils,
        f"B1 utilities 5+1 ({sorted(utils)})")
    # addon/builtin 카테고리는 카탈로그에 없음 (§7.6.3-1)
    cats = {a["category"] for a in c.get("/api/marketplace/catalog", headers=H).json()["assets"]}
    chk("addon" not in cats and "builtin" not in cats, f"B1 addon/builtin excluded ({cats})")

# B2) Makefile db-fresh chain (static)
mk = (ROOT / "Makefile").read_text(encoding="utf-8")
block = mk.split("db-fresh:")[1].split("\n\n")[0]
chk(all(s in block for s in ("seed.py", "seed_security.py", "seed_assets.py")),
    "B2 db-fresh chain includes 3 seeds")

# C1) dev DB(local.db) 실 상태 — 사용자 요구 * (utilities 등록 확인).
# 라이브 DB 는 이후 UI 등록으로 증가 가능 → 시드 최소치(security 13·utilities 6종 키 포함)로 검증.
import sqlite3  # noqa: E402
con = sqlite3.connect(ROOT / "local.db")
util_keys = {r[0] for r in con.execute(
    "SELECT asset_key FROM marketplace_assets WHERE category='utilities'").fetchall()}
sec_cnt = con.execute(
    "SELECT COUNT(*) FROM marketplace_assets WHERE category='security'").fetchone()[0]
con.close()
SEED_UTILS = {"ai-traffic-monitor", "caddy-proxy", "grafana-dashboard",
              "server-shell", "truffle-scan"}  # impl/52: UserManager 는 addon 으로 이관
chk(sec_cnt >= 13 and SEED_UTILS <= util_keys,
    f"C1 dev DB registered (security={sec_cnt}, utilities={sorted(util_keys)})")

# D1) modal refactor (static)
agents_src = (ROOT / "front/src/pages/agents/AgentsPage.tsx").read_text(encoding="utf-8")
modal_src = (ROOT / "front/src/pages/marketplace/AssetRegisterModal.tsx").read_text(encoding="utf-8")
mp_src = (ROOT / "front/src/pages/marketplace/MarketplacePage.tsx").read_text(encoding="utf-8")
chk('from "../marketplace/AssetRegisterModal"' in agents_src
    and "function AssetRegisterModal" not in agents_src, "D1 AgentsPage inline modal removed")
chk("category?: string" in modal_src and "registerAssetZips(zipFiles, cat," in modal_src,
    "D1 modal category prop + zip category")  # impl/48: 폼 필드 인자 추가로 호출부 다행화
chk("setAddCategory(cat)" in mp_src and "AssetRegisterModal category={addCategory}" in mp_src,
    "D1 per-category add button wired")

# D2) locales parity
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
for sect, key in (("agent", "assetCategory"), ("agent", "assetCategoryHint"), ("mp", "addToCatalog")):
    chk(key in ko[sect] and key in en[sect], f"D2 locale parity {sect}.{key}")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
