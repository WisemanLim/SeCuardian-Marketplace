"""§7.6.5 uninstall full undeploy — deployed dir/addon row cleanup, pageDesc, cleanup script.

Fresh sqlite + TestClient (test/impl/1 패턴).
주의: hot-deploy 는 실제 파일시스템(addon-agents/deployed)에 쓰므로 고유 키 사용 + 종료 시 원복.
"""
import io
import json
import os
import shutil
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
os.chdir(ROOT)  # deployed 경로는 상대 — 저장소 루트 기준 고정

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

tok = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {tok}"}

KEY = "undeploy-e2e"
DEPLOYED = ROOT / "addon-agents" / "deployed" / KEY

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def make_addon_zip(key: str) -> bytes:
    app_py = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n\n"
        "@router.get('/ping')\n"
        "def ping():\n"
        "    return {'ok': True}\n"
    )
    meta = {"agent_key": key, "name": f"{key} agent", "version": "1.0.0",
            "description": "undeploy e2e", "router_prefix": f"/{key}"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", app_py)
        zf.writestr(f"{key}-meta.json", json.dumps(meta))
    return buf.getvalue()


import sqlite3  # noqa: E402


def q(sql, args=()):
    con = sqlite3.connect(f"{tmp}/t.db")
    rows = con.execute(sql, args).fetchall()
    con.close()
    return rows


try:
    with TestClient(m.app) as c:
        # A1) register + install → deployed dir + addon row
        r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "utilities"},
                   files=[("files", (f"{KEY}.zip", make_addon_zip(KEY), "application/zip"))])
        chk(r.status_code == 201, f"A1 zip register ({r.status_code})")
        r = c.post(f"/api/marketplace/install/{KEY}", headers=H)
        chk(r.status_code == 201 and r.json()["deployed"] is True,
            f"A1 install deployed=true ({r.status_code} {r.text[:120]})")
        chk(DEPLOYED.is_dir(), "A1 deployed dir created")
        chk(len(q("SELECT 1 FROM tbl_addon_agents WHERE LOWER(agent_key)=LOWER(?)", (KEY,))) == 1,
            "A1 addon row created")

        # A2) uninstall → full cleanup
        r = c.delete(f"/api/marketplace/install/{KEY}", headers=H)
        chk(r.status_code == 200 and r.json().get("undeployed") is True,
            f"A2 uninstall undeployed=true ({r.status_code} {r.text[:120]})")
        chk(not DEPLOYED.exists(), "A2 deployed dir removed")
        chk(len(q("SELECT 1 FROM tbl_addon_agents WHERE LOWER(agent_key)=LOWER(?)", (KEY,))) == 0,
            "A2 addon row removed")
        chk(len(q("SELECT 1 FROM tbl_mcp_configs WHERE agent_key=?", (KEY,))) == 0,
            "A2 mcp config removed")

        # A3) config row kept + disabled
        rows = q("SELECT is_enabled FROM tbl_agent_config WHERE agent_key=?", (KEY,))
        chk(len(rows) == 1 and rows[0][0] == 0, f"A3 config kept+disabled ({rows})")

        # A4) reinstall → recreated
        r = c.post(f"/api/marketplace/install/{KEY}", headers=H)
        chk(r.status_code == 201 and DEPLOYED.is_dir(), "A4 reinstall recreates deploy")
        c.delete(f"/api/marketplace/install/{KEY}", headers=H)  # 정리
        chk(not DEPLOYED.exists(), "A4 re-uninstall cleans again")

        # A5) meta-only asset uninstall → undeployed=false, no error
        c.post("/api/marketplace/catalog", headers=H, json={"name": "Meta Only X"})
        c.post("/api/marketplace/install/meta-only-x", headers=H)
        r = c.delete("/api/marketplace/install/meta-only-x", headers=H)
        chk(r.status_code == 200 and r.json().get("undeployed") is False,
            f"A5 meta-only uninstall ({r.status_code} {r.text[:100]})")

        # B1) delete_addon regression — 404 guard intact
        r = c.delete("/api/addon-agents/nonexistent-key", headers=H)
        chk(r.status_code == 404, "B1 delete_addon 404 guard")

    # C1) cleanup script — 고아 디렉터리 제거 (격리 키)
    orphan = ROOT / "addon-agents" / "deployed" / "orphan-e2e"
    orphan.mkdir(parents=True, exist_ok=True)
    import subprocess
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "cleanup_addon_remnants.py")],
                         capture_output=True, text=True, env={**os.environ}, cwd=ROOT)
    chk(res.returncode == 0 and not orphan.exists(),
        f"C1 cleanup removes orphan dir (exit={res.returncode})")
    res2 = subprocess.run([sys.executable, str(ROOT / "scripts" / "cleanup_addon_remnants.py")],
                          capture_output=True, text=True, env={**os.environ}, cwd=ROOT)
    chk(res2.returncode == 0, "C1 cleanup idempotent rerun")
finally:
    # 실 FS 잔재 방지 — 시험 키 디렉터리 원복
    for k in (KEY, "orphan-e2e"):
        d = ROOT / "addon-agents" / "deployed" / k
        if d.exists():
            shutil.rmtree(d)
    tsx = ROOT / "front/src/pages/addon/deployed" / f"{KEY}.tsx"
    if tsx.exists():
        tsx.unlink()

# D) static checks
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
chk("자산 카탈로그" in ko["agent"]["pageDesc"], "D1 ko pageDesc mentions catalog")
chk("asset catalog" in en["agent"]["pageDesc"].lower(), "D1 en pageDesc mentions catalog")
mp_src = (ROOT / "front/src/pages/marketplace/MarketplacePage.tsx").read_text(encoding="utf-8")
chk(mp_src.count('CustomEvent("agentConfigChanged")') >= 2, "D2 agentConfigChanged on install/uninstall")
mk = (ROOT / "Makefile").read_text(encoding="utf-8")
chk("cleanup-addons:" in mk and "cleanup_addon_remnants.py" in mk, "D3 Makefile cleanup-addons target")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
