"""F-MP §7.6 로컬 자산 실 ZIP 배포 test — 로컬 카탈로그 자산에 ZIP 첨부 → install 시 무중단 hot-deploy."""
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

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'sup1','role':'supervisor','username':'sup1'})}"}
UH = {"Authorization": f"Bearer {create_access_token({'sub':'u1','role':'user','username':'u1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# valid addon ZIP: stem 'localaddon' → agent_key 'localaddon' (router prefix 는 load_router 가 부여)
STEM = "localaddon"
APP_PY = ("from fastapi import APIRouter\n"
          "router = APIRouter(tags=['localaddon'])\n"
          "@router.get('/ping')\n"
          "def ping():\n    return {'addon':'localaddon','ok':True}\n")
_buf = io.BytesIO()
with zipfile.ZipFile(_buf, "w") as zf:
    zf.writestr(f"{STEM}-app.py", APP_PY)
    zf.writestr(f"{STEM}-meta.json", '{"description":"local addon"}')
ZIP = _buf.getvalue()
SHA = hashlib.sha256(ZIP).hexdigest()

with TestClient(m.app) as c:
    # 1) register catalog asset (agent, key=localaddon)
    r = c.post("/api/marketplace/catalog", headers=H,
               json={"asset_key": "localaddon", "version": "1.0.0", "kind": "agent", "name": "Local Addon"})
    chk(r.status_code == 201, f"register asset ({r.status_code})")

    # 2) install WITHOUT zip → config seam only, deployed=false
    r = c.post("/api/marketplace/install/localaddon", headers=H)
    chk(r.status_code == 201 and r.json().get("deployed") is False, f"install w/o zip -> deployed false ({r.json().get('deployed')})")
    chk(c.get("/api/addon/localaddon/ping", headers=H).status_code == 404, "addon route absent (no zip)")

    # 3) attach ZIP (user forbidden)
    r = c.post("/api/marketplace/catalog/localaddon/zip", headers=UH,
               files={"file": ("localaddon.zip", ZIP, "application/zip")})
    chk(r.status_code == 403, "user zip upload -> 403")
    # non-zip rejected
    r = c.post("/api/marketplace/catalog/localaddon/zip", headers=H,
               files={"file": ("x.txt", b"nope", "text/plain")})
    chk(r.status_code == 400, "non-zip -> 400")
    # valid attach
    r = c.post("/api/marketplace/catalog/localaddon/zip", headers=H,
               files={"file": ("localaddon.zip", ZIP, "application/zip")})
    chk(r.status_code == 201 and r.json()["checksum"] == SHA, f"zip attached w/ checksum ({r.status_code})")

    # 4) re-install WITH zip → real hot-deploy, addon route LIVE
    r = c.post("/api/marketplace/install/localaddon", headers=H)
    chk(r.status_code == 201 and r.json().get("deployed") is True, f"install w/ zip -> deployed true ({r.json().get('deployed')})")
    r = c.get("/api/addon/localaddon/ping", headers=H)
    chk(r.status_code == 200 and r.json().get("ok"), f"addon route LIVE after local install ({r.status_code} {r.text[:80]})")

    # 5) addon registered in addon registry (upload pipeline reused)
    r = c.get("/api/addon-agents/", headers=H)
    chk("localaddon" in [a["agent_key"] for a in r.json().get("addons", [])], "addon registered via reused pipeline")

    # 6) asset meta checksum synced
    r = c.get("/api/marketplace/catalog/localaddon", headers=H)
    chk(r.json().get("checksum") == SHA, "asset meta checksum synced")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
