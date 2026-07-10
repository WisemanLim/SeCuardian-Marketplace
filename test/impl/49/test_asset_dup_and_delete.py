"""impl/49 — 중복 등록 확인 + 시드 보호 축소 + 카탈로그 삭제 시 시드 반환 (§7.6.6 v0.47, impl/1 패턴)."""
import io
import json
import os
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


def make_zip(key: str, name: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", "# stub\n")
        zf.writestr(f"{key}-meta.json", json.dumps(
            {"agent_key": key, "name": name or f"meta-{key}", "version": "1.0.0"}))
    return buf.getvalue()


def reg(c, key, cat, confirm=False, name=""):
    params = {"category": cat}
    if confirm:
        params["confirm"] = "true"
    return c.post("/api/marketplace/catalog/zip", headers=H, params=params,
                  files=[("files", (f"{key}.zip", make_zip(key, name), "application/zip"))])


with TestClient(m.app) as c:
    # TC-49-01: 신규 key 등록 — confirm 불필요
    r = reg(c, "dup-x", "cat1", name="중복시험")
    chk(r.status_code == 201, f"TC-49-01 신규 등록 201 ({r.status_code})")

    # TC-49-02: 동일 key 를 다른 카탈로그로 confirm 없이 → 409 duplicate + 기존 정보
    r = reg(c, "dup-x", "cat2")
    chk(r.status_code == 409, f"TC-49-02 중복 등록 409 ({r.status_code})")
    d = r.json().get("detail") or {}
    chk(d.get("code") == "duplicate", f"TC-49-02 code=duplicate ({d})")
    a0 = (d.get("assets") or [{}])[0]
    chk(a0.get("asset_key") == "dup-x" and a0.get("category") == "cat1",
        f"TC-49-02 기존 카탈로그 정보 노출 ({a0})")

    # TC-49-03: confirm=true → 요청 카탈로그로 이동 등록, 중복 행 없음
    r = reg(c, "dup-x", "cat2", confirm=True)
    chk(r.status_code == 201, f"TC-49-03 confirm 등록 201 ({r.status_code})")
    rows = [a for a in c.get("/api/marketplace/catalog", headers=H).json()["assets"]
            if a["asset_key"] == "dup-x"]
    chk(len(rows) == 1 and rows[0]["category"] == "cat2",
        f"TC-49-03 cat2 이동·단일 행 ({[(x['category']) for x in rows]})")

    # TC-49-04: addon 디스크 보유 key(toolproxyagent) — 사용자 등록 자산은 삭제 가능
    r = reg(c, "toolproxyagent", "usercat")
    chk(r.status_code == 201, f"TC-49-04 addon key 등록 201 ({r.status_code})")
    a = r.json()["assets"][0]
    chk(a["deletable"] is True, f"TC-49-04 addon 유래 deletable=true ({a['deletable']})")
    r = c.delete("/api/marketplace/catalog/toolproxyagent", headers=H)
    chk(r.status_code == 200, f"TC-49-04 addon 유래 삭제 200 ({r.status_code})")

    # TC-49-05: 시드 디스크 보유 key(vasca-cve) — 보호 유지
    r = reg(c, "vasca-cve", "seedreg")
    chk(r.status_code == 201, f"TC-49-05 시드 key 등록 201 ({r.status_code})")
    a = r.json()["assets"][0]
    chk(a["deletable"] is False, f"TC-49-05 시드 deletable=false ({a['deletable']})")
    r = c.delete("/api/marketplace/catalog/vasca-cve", headers=H)
    chk(r.status_code == 403, f"TC-49-05 시드 삭제 403 ({r.status_code})")

    # TC-49-06: 카탈로그 삭제 — 시드 key 는 security 반환, 일반 key 는 삭제
    r = reg(c, "vasca-cve", "mixcat", confirm=True)
    chk(r.status_code == 201, f"TC-49-06 시드 key mixcat 이동 ({r.status_code})")
    r = reg(c, "plain-y", "mixcat")
    chk(r.status_code == 201, f"TC-49-06 일반 key mixcat 등록 ({r.status_code})")
    r = c.delete("/api/marketplace/catalog-category/mixcat", headers=H)
    body = r.json() if r.status_code == 200 else {}
    chk(r.status_code == 200, f"TC-49-06 사용자 카탈로그 삭제 200 ({r.status_code} {r.text[:120]})")
    chk(set(body.get("deleted_assets", [])) == {"plain-y"},
        f"TC-49-06 일반 key 삭제 ({body.get('deleted_assets')})")
    chk(set(body.get("returned_assets", [])) == {"vasca-cve"},
        f"TC-49-06 시드 key 반환 목록 ({body.get('returned_assets')})")
    assets = {a["asset_key"]: a for a in c.get("/api/marketplace/catalog", headers=H).json()["assets"]}
    chk(assets.get("vasca-cve", {}).get("category") == "security",
        f"TC-49-06 시드 key security 복귀 ({assets.get('vasca-cve', {}).get('category')})")
    chk("plain-y" not in assets, "TC-49-06 일반 key 카탈로그 잔존 없음")

    # TC-49-06b: 시드 카탈로그 자체 삭제 → 409 (기본 제공 보호)
    r = c.delete("/api/marketplace/catalog-category/security", headers=H)
    chk(r.status_code == 409, f"TC-49-06b 시드 카탈로그 삭제 차단 409 ({r.status_code})")

    # TC-49-07: 설치 중 자산 포함 카탈로그 삭제 → 409, 해제 후 200
    r = reg(c, "plain-z", "instcat")
    chk(r.status_code == 201, f"TC-49-07 등록 ({r.status_code})")
    r = c.post("/api/marketplace/install/plain-z", headers=H)
    chk(r.status_code == 201, f"TC-49-07 설치 ({r.status_code})")
    r = c.delete("/api/marketplace/catalog-category/instcat", headers=H)
    chk(r.status_code == 409, f"TC-49-07 설치 중 카탈로그 삭제 409 ({r.status_code})")
    c.delete("/api/marketplace/install/plain-z", headers=H)
    r = c.delete("/api/marketplace/catalog-category/instcat", headers=H)
    chk(r.status_code == 200, f"TC-49-07 해제 후 삭제 200 ({r.status_code})")

# TC-49-08: 프론트 정적 검증 — dup ConfirmDialog 연동 + locale parity
modal = (ROOT / "front/src/pages/marketplace/AssetRegisterModal.tsx").read_text(encoding="utf-8")
chk("dupAssets" in modal and "<ConfirmDialog" in modal and "submit(true)" in modal,
    "TC-49-08 modal dup ConfirmDialog wiring")
chk("window.confirm" not in modal, "TC-49-08 no browser confirm (R18-1)")
api = (ROOT / "front/src/api/marketplace.ts").read_text(encoding="utf-8")
chk("confirm" in api and "DuplicateAssetInfo" in api, "TC-49-08 api confirm param")
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
for key in ("assetDupTitle", "assetDupConfirm"):
    chk(key in ko["agent"] and key in en["agent"], f"TC-49-08 locale parity agent.{key}")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
