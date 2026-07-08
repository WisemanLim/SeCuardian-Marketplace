"""F-MP functional test — fresh sqlite, TestClient, full CRUD + install lifecycle."""
import os, tempfile, sys

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

from fastapi.testclient import TestClient
from app.core.security import create_access_token
import app.main as m

tok = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {tok}"}
utok = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {utok}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond: fails.append(msg)

with TestClient(m.app) as c:
    # 0) health + marketplace seed present
    r = c.get("/health"); chk(r.status_code == 200, "health 200")
    r = c.get("/api/agent-config/", headers=H)
    keys = [a.get("agent_key") for a in (r.json() if isinstance(r.json(), list) else r.json().get("agents", []))] if r.status_code == 200 else []
    chk(r.status_code == 200 and "marketplace" in keys, f"marketplace seeded in agent-config (got {keys})")

    # 1) empty catalog
    r = c.get("/api/marketplace/catalog", headers=H)
    chk(r.status_code == 200 and r.json()["assets"] == [], "empty catalog")

    # 2) RBAC: user cannot register
    r = c.post("/api/marketplace/catalog", headers=UH, json={"asset_key": "x", "name": "X"})
    chk(r.status_code == 403, "user register -> 403")

    # 3) register agent asset
    payload = {"asset_key": "cve-scanner", "version": "1.0.0", "kind": "agent",
               "name": "CVE 스캐너", "name_en": "CVE Scanner", "description": "취약점 스캔",
               "category": "security", "required_env": "SCAN_TOKEN"}
    r = c.post("/api/marketplace/catalog", headers=H, json=payload)
    chk(r.status_code == 201, f"register 201 ({r.status_code} {r.text[:120]})")
    chk(r.json().get("installed") is False, "registered not-installed")

    # 4) duplicate -> 409
    r = c.post("/api/marketplace/catalog", headers=H, json=payload)
    chk(r.status_code == 409, "duplicate -> 409")

    # 5) bad kind -> 422
    r = c.post("/api/marketplace/catalog", headers=H, json={"asset_key": "y", "name": "Y", "kind": "bogus"})
    chk(r.status_code == 422, "bad kind -> 422")

    # 6) install
    r = c.post("/api/marketplace/install/cve-scanner", headers=H)
    chk(r.status_code == 201 and r.json()["status"] == "installed", f"install 201 ({r.status_code} {r.text[:120]})")
    chk(r.json()["agent_config_key"] == "cve-scanner", "install upserts agent_config_key")

    # 7) catalog shows installed + active_version
    r = c.get("/api/marketplace/catalog/cve-scanner", headers=H)
    chk(r.status_code == 200 and r.json()["installed"] and r.json()["active_version"] == "1.0.0", "asset installed+active_version")

    # 8) agent_config now has cve-scanner enabled (hot-deploy seam)
    r = c.get("/api/agent-config/", headers=H)
    lst = r.json() if isinstance(r.json(), list) else r.json().get("agents", [])
    cve = next((a for a in lst if a.get("agent_key") == "cve-scanner"), None)
    chk(cve is not None and (cve.get("is_enabled") in (1, True)), f"cve-scanner in agent-config enabled ({cve})")

    # 9) installs list
    r = c.get("/api/marketplace/installs", headers=H)
    chk(r.status_code == 200 and len(r.json()["installs"]) == 1, "installs list = 1")

    # 10) re-install (new version) -> single active version
    c.post("/api/marketplace/catalog", headers=H, json={**payload, "version": "1.1.0"})
    r = c.post("/api/marketplace/install/cve-scanner", headers=H)  # latest = 1.1.0
    chk(r.status_code == 201 and r.json()["version"] == "1.1.0", "reinstall latest 1.1.0")
    r = c.get("/api/marketplace/installs", headers=H)
    actives = [i for i in r.json()["installs"] if i["active"] in (1, True)]
    chk(len(actives) == 1 and actives[0]["version"] == "1.1.0", f"single active version (got {[i['version']+':'+str(i['active']) for i in r.json()['installs']]})")

    # 11) uninstall
    r = c.delete("/api/marketplace/install/cve-scanner", headers=H)
    chk(r.status_code == 200, "uninstall 200")
    r = c.get("/api/marketplace/catalog/cve-scanner", headers=H)
    chk(not r.json()["installed"], "after uninstall not-installed")
    # uninstall again -> 404
    r = c.delete("/api/marketplace/install/cve-scanner", headers=H)
    chk(r.status_code == 404, "uninstall again -> 404")

    # 12) unauth -> 401/403
    r = c.get("/api/marketplace/catalog")
    chk(r.status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
