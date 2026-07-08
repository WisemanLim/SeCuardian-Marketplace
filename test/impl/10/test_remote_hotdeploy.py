"""F-MP §7.6 real ZIP hot-deploy test — remote install of a VALID addon ZIP deploys it live.

Builds a minimal valid addon package in-memory ({stem}-app.py with an APIRouter), serves it via the
monkeypatched remote host, then installs remotely. Asserts the addon router is actually mounted
(new /api/addon/{key}/... route reachable) — i.e. remote install → real hot-deploy pipeline reuse.
"""
import hashlib
import io
import os
import sys
import tempfile
import zipfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"
# addon 배포 산출물을 임시 경로로 격리(리포 오염 방지)
os.environ["ADDON_DEPLOYED_PATH"] = f"{tmp}/deployed"

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402
import app.main as m  # noqa: E402
import app.routers.router_marketplace_remote as rmr  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── build a minimal VALID addon ZIP: stem 'helloaddon' → agent_key 'helloaddon' ──
STEM = "helloaddon"
APP_PY = (
    "from fastapi import APIRouter\n"
    "# load_router() 가 prefix=/api/addon/helloaddon 를 include 시 부여 → 여기선 prefix 없이 정의\n"
    "router = APIRouter(tags=['helloaddon'])\n"
    "@router.get('/ping')\n"
    "def ping():\n"
    "    return {'addon': 'helloaddon', 'ok': True}\n"
)
META = '{"description": "hello addon", "agent_type": "app"}'
_buf = io.BytesIO()
with zipfile.ZipFile(_buf, "w") as zf:
    zf.writestr(f"{STEM}-app.py", APP_PY)
    zf.writestr(f"{STEM}-meta.json", META)
ZIP_BYTES = _buf.getvalue()
ZIP_SHA = hashlib.sha256(ZIP_BYTES).hexdigest()

async def fake_get(path: str) -> dict:
    if path == "/ping":
        return {"version": "host-1.0"}
    if path.startswith("/catalog/"):
        return {"asset_key": STEM, "version": "1.0.0", "kind": "agent", "name": "Hello Addon",
                "description": "hello addon", "checksum": ZIP_SHA, "download_path": f"/download/{STEM}"}
    return {"assets": []}

async def fake_download(path: str) -> bytes:
    return ZIP_BYTES

rmr._remote_get = fake_get
rmr._remote_download = fake_download

with TestClient(m.app) as c:
    settings.marketplace_remote_enabled = True
    settings.marketplace_host_url = "https://fake-registry.internal"

    # addon route absent before install
    r = c.get("/api/addon/helloaddon/ping", headers=H)
    chk(r.status_code == 404, f"addon route absent pre-install ({r.status_code})")

    # remote install with hot_deploy (default true)
    r = c.post(f"/api/marketplace-remote/install/{STEM}", headers=H, json={})
    chk(r.status_code == 201, f"remote install 201 ({r.status_code} {r.text[:160]})")
    body = r.json()
    chk(body["deployed"] is True, f"deployed=true (real hot-deploy) ({body.get('deployed')}, {str(body.get('deploy_result'))[:160]})")
    chk(body["asset"]["source"] == "remote", "catalog asset source=remote")

    # addon route now LIVE (hot-mounted, no restart)
    r = c.get("/api/addon/helloaddon/ping", headers=H)
    chk(r.status_code == 200 and r.json().get("ok"), f"addon route LIVE after remote install ({r.status_code} {r.text[:120]})")

    # addon registered in tbl_addon_agents (via reused upload pipeline)
    r = c.get("/api/addon-agents/", headers=H)
    addon_keys = [a["agent_key"] for a in r.json().get("addons", [])]
    chk("helloaddon" in addon_keys, f"addon registered in addon registry ({addon_keys})")

    # also in marketplace catalog
    r = c.get("/api/marketplace/catalog", headers=H)
    mp_keys = [a["asset_key"] for a in r.json()["assets"]]
    chk("helloaddon" in mp_keys, f"asset in marketplace catalog ({mp_keys})")

    # hot_deploy=false path: catalog-only (different asset), no addon mount
    async def fake_get2(path: str) -> dict:
        if path.startswith("/catalog/"):
            return {"asset_key": "catalogonly", "version": "1.0.0", "kind": "rag-pipeline",
                    "name": "Catalog Only", "checksum": ZIP_SHA, "download_path": "/download/x"}
        return {"assets": []}
    rmr._remote_get = fake_get2
    r = c.post("/api/marketplace-remote/install/catalogonly", headers=H, json={"hot_deploy": False})
    chk(r.status_code == 201 and r.json()["deployed"] is False, f"hot_deploy=false -> catalog only ({r.json().get('deployed')})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
