"""F-MP GPG 서명 검증 + mTLS test (§7.3 엔터프라이즈 옵션).
실 GPG 키쌍으로 detached 서명·검증(python-gnupg) + 원격 install 서명 강제 경로 + mTLS httpx kwargs.
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

import asyncio  # noqa: E402
import gnupg  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402
import app.main as m  # noqa: E402
import app.routers.router_marketplace_remote as rmr  # noqa: E402
from app.services.signature import verify_detached  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'sup1','role':'supervisor','username':'sup1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── build addon ZIP + real GPG keypair + detached signature ──
STEM = "signedaddon"
_buf = io.BytesIO()
with zipfile.ZipFile(_buf, "w") as zf:
    zf.writestr(f"{STEM}-app.py", "from fastapi import APIRouter\nrouter=APIRouter()\n@router.get('/ping')\ndef p(): return {'ok':True}\n")
    zf.writestr(f"{STEM}-meta.json", '{"description":"signed"}')
ZIP = _buf.getvalue()
SHA = hashlib.sha256(ZIP).hexdigest()

_gpghome = tempfile.mkdtemp()
gpg = gnupg.GPG(gnupghome=_gpghome)
key = gpg.gen_key(gpg.gen_key_input(name_email="pub@secmp", key_type="RSA", key_length=2048, no_protection=True))
PUBKEY = gpg.export_keys(str(key.fingerprint))
SIG = gpg.sign(ZIP, keyid=str(key.fingerprint), detach=True).data
BAD_SIG = gpg.sign(b"other data", keyid=str(key.fingerprint), detach=True).data

# ── unit: verify_detached ──
chk(verify_detached(ZIP, SIG, PUBKEY) is True, "valid detached signature -> True")
chk(verify_detached(ZIP, BAD_SIG, PUBKEY) is False, "wrong-data signature -> False")
chk(verify_detached(b"tampered", SIG, PUBKEY) is False, "tampered data -> False")
chk(verify_detached(ZIP, SIG, "") is False, "no pubkey -> False")

# ── mTLS kwargs ──
settings.marketplace_tls_ca_bundle = "/tmp/ca.pem"
settings.marketplace_tls_client_cert = "/tmp/client.pem"
settings.marketplace_tls_client_key = "/tmp/client.key"
kw = rmr._tls_kwargs()
chk(kw["verify"] == "/tmp/ca.pem", f"CA bundle → verify path ({kw.get('verify')})")
chk(kw["cert"] == ("/tmp/client.pem", "/tmp/client.key"), f"mTLS client cert pair ({kw.get('cert')})")
settings.marketplace_tls_ca_bundle = ""; settings.marketplace_tls_client_cert = ""; settings.marketplace_tls_client_key = ""
chk(rmr._tls_kwargs() == {"verify": True}, "defaults → verify True, no cert")

# ── integration: remote install with signature required ──
pubfile = os.path.join(tmp, "pub.asc")
open(pubfile, "w").write(PUBKEY)
settings.marketplace_remote_enabled = True
settings.marketplace_host_url = "https://fake"
settings.marketplace_install_require_signature = True
settings.marketplace_gpg_pubkey_path = pubfile

async def fake_get(path):
    return {"asset_key": STEM, "version": "1.0.0", "kind": "agent", "name": "Signed",
            "checksum": SHA, "download_path": f"/download/{STEM}", "signature_path": f"/download/{STEM}.sig"}
async def fake_dl_ok(path):
    return SIG if path.endswith(".sig") else ZIP
async def fake_dl_badsig(path):
    return BAD_SIG if path.endswith(".sig") else ZIP

rmr._remote_get = fake_get

with TestClient(m.app) as c:
    # valid signature → 201 (deployed via reused pipeline)
    rmr._remote_download = fake_dl_ok
    r = c.post(f"/api/marketplace-remote/install/{STEM}", headers=H, json={})
    chk(r.status_code == 201, f"signed install (valid sig) -> 201 ({r.status_code} {r.text[:120]})")

    # bad signature → 422
    rmr._remote_download = fake_dl_badsig
    r = c.post(f"/api/marketplace-remote/install/{STEM}", headers=H, json={"version": "2.0.0"})
    chk(r.status_code == 422, f"bad signature -> 422 ({r.status_code})")

    # signature required but pubkey unset → 422
    settings.marketplace_gpg_pubkey_path = ""
    rmr._remote_download = fake_dl_ok
    r = c.post(f"/api/marketplace-remote/install/{STEM}", headers=H, json={"version": "3.0.0"})
    chk(r.status_code == 422, f"no pubkey configured -> 422 ({r.status_code})")

settings.marketplace_install_require_signature = False
settings.marketplace_remote_enabled = False
import shutil
for d in ("addon-agents/deployed/signedaddon",):
    shutil.rmtree(d, ignore_errors=True)

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
