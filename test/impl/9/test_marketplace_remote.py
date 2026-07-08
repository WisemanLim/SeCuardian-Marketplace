"""F-MP E1.5 remote registry test — fresh sqlite, TestClient. Remote fetch monkeypatched to a fake host.
Covers: disabled gate, ping, catalog(+cache), install(checksum verify/mismatch), local catalog merge.
"""
import hashlib
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402
import app.main as m  # noqa: E402
import app.routers.router_marketplace_remote as rmr  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}
UH = {"Authorization": f"Bearer {create_access_token({'sub': 'u1', 'role': 'user', 'username': 'u1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── fake remote host ──
FAKE_ZIP = b"PK\x03\x04 fake addon zip payload"
FAKE_SHA = hashlib.sha256(FAKE_ZIP).hexdigest()
_fetch_calls = {"catalog": 0}

async def fake_get(path: str) -> dict:
    if path == "/ping":
        return {"version": "host-1.0"}
    if path == "/catalog":
        _fetch_calls["catalog"] += 1
        return {"assets": [{"asset_key": "remote-scanner", "version": "2.0.0", "kind": "agent",
                            "name": "Remote Scanner", "checksum": FAKE_SHA}]}
    if path.startswith("/catalog/"):
        key = path.split("/")[-1]
        return {"asset_key": key, "version": "2.0.0", "kind": "agent", "name": "Remote Scanner",
                "description": "from remote host", "checksum": FAKE_SHA, "download_path": f"/download/{key}"}
    return {}

async def fake_download(path: str) -> bytes:
    return FAKE_ZIP

rmr._remote_get = fake_get
rmr._remote_download = fake_download

with TestClient(m.app) as c:
    # 1) disabled by default -> 409
    r = c.get("/api/marketplace-remote/ping", headers=H)
    chk(r.status_code == 409, f"disabled -> 409 ({r.status_code})")

    # enable + configure host
    settings.marketplace_remote_enabled = True
    settings.marketplace_host_url = "https://fake-registry.internal"

    # 2) ping
    r = c.get("/api/marketplace-remote/ping", headers=H)
    chk(r.status_code == 200 and r.json()["ok"], f"ping ok ({r.status_code})")

    # 3) catalog (first = live, second = cached)
    r = c.get("/api/marketplace-remote/catalog", headers=H)
    chk(r.status_code == 200 and not r.json()["cached"] and len(r.json()["assets"]) == 1, f"catalog live ({r.json()})")
    r = c.get("/api/marketplace-remote/catalog", headers=H)
    chk(r.json()["cached"] and _fetch_calls["catalog"] == 1, f"catalog cached (fetch calls={_fetch_calls['catalog']})")
    r = c.get("/api/marketplace-remote/catalog?refresh=true", headers=H)
    chk(_fetch_calls["catalog"] == 2, "refresh=true bypasses cache")

    # 4) detail
    r = c.get("/api/marketplace-remote/catalog/remote-scanner", headers=H)
    chk(r.status_code == 200 and r.json()["asset_key"] == "remote-scanner", "remote detail")

    # 5) install — checksum matches -> registered into local catalog with source=remote
    r = c.post("/api/marketplace-remote/install/remote-scanner", headers=H, json={})
    chk(r.status_code == 201 and r.json()["registered"], f"remote install 201 ({r.status_code} {r.text[:120]})")
    chk(r.json()["checksum"] == FAKE_SHA, "checksum returned matches")
    chk(r.json()["asset"]["source"] == "remote", f"local asset source=remote ({r.json()['asset'].get('source')})")

    # 6) local catalog now shows the remote-origin asset
    r = c.get("/api/marketplace/catalog", headers=H)
    keys = [a["asset_key"] for a in r.json()["assets"]]
    chk("remote-scanner" in keys, f"remote asset merged into local catalog ({keys})")

    # 7) duplicate install -> 409
    r = c.post("/api/marketplace-remote/install/remote-scanner", headers=H, json={})
    chk(r.status_code == 409, "duplicate remote install -> 409")

    # 8) checksum mismatch -> 422
    r = c.post("/api/marketplace-remote/install/remote-scanner", headers=H,
               json={"version": "9.9.9", "expected_checksum": "deadbeef"})
    chk(r.status_code == 422, f"checksum mismatch -> 422 ({r.status_code})")

    # 9) RBAC: user cannot install
    r = c.post("/api/marketplace-remote/install/remote-scanner", headers=UH, json={})
    chk(r.status_code == 403, "user remote install -> 403")

    # 10) unauth
    chk(c.get("/api/marketplace-remote/catalog").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
