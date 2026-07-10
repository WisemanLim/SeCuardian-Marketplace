"""§7.6.6 자산 등록 ZIP 필수 + 사용자 자산·카탈로그 삭제 — 격리 sqlite + TestClient (impl/1 패턴)."""
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
utok = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {utok}"}

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def make_zip(key: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", "# stub\n")
        zf.writestr(f"{key}-meta.json", json.dumps({"agent_key": key, "name": key, "version": "1.0.0"}))
    return buf.getvalue()


with TestClient(m.app) as c:
    # 준비: 사용자 카테고리 'usercat' 에 zip 자산 2종 + 디스크 보유 키(vasca-cve) 메타 등록
    r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "usercat"},
               files=[("files", ("del-a.zip", make_zip("del-a"), "application/zip")),
                      ("files", ("del-b.zip", make_zip("del-b"), "application/zip"))])
    chk(r.status_code == 201, f"prep zip register ({r.status_code})")
    r = c.post("/api/marketplace/catalog", headers=H,
               json={"asset_key": "vasca-cve", "name": "VASCA", "category": "diskcat"})
    chk(r.status_code == 201, "prep disk-backed key register (meta-only API 유지 — impl/39 회귀)")

    # TC-47-02: deletable 플래그
    assets = {a["asset_key"]: a for a in c.get("/api/marketplace/catalog", headers=H).json()["assets"]}
    chk(assets["del-a"]["deletable"] is True, "TC-47-02 user asset deletable=true")
    chk(assets["vasca-cve"]["deletable"] is False, "TC-47-02 disk-backed deletable=false")

    # TC-47-04: 디스크 보유 → 403
    r = c.delete("/api/marketplace/catalog/vasca-cve", headers=H)
    chk(r.status_code == 403, f"TC-47-04 disk-backed delete -> 403 ({r.status_code})")

    # TC-47-04: 설치 중 → 409, 해제 후 200
    r = c.post("/api/marketplace/install/del-a", headers=H)
    chk(r.status_code == 201, "prep install del-a")
    r = c.delete("/api/marketplace/catalog/del-a", headers=H)
    chk(r.status_code == 409, f"TC-47-04 installed delete -> 409 ({r.status_code})")
    c.delete("/api/marketplace/install/del-a", headers=H)
    r = c.delete("/api/marketplace/catalog/del-a", headers=H)
    chk(r.status_code == 200, f"TC-47-04 after uninstall delete -> 200 ({r.status_code})")

    # TC-47-03: 삭제 후 잔재 없음 + 404/RBAC
    keys = [a["asset_key"] for a in c.get("/api/marketplace/catalog", headers=H).json()["assets"]]
    chk("del-a" not in keys, "TC-47-03 catalog row removed")
    r = c.get("/api/agent-config/", headers=H)
    chk(all(a["agent_key"] != "del-a" for a in r.json()["agents"]), "TC-47-03 config row removed")
    r = c.delete("/api/marketplace/catalog/del-a", headers=H)
    chk(r.status_code == 404, "TC-47-03 missing -> 404")
    r = c.delete("/api/marketplace/catalog/del-b", headers=UH)
    chk(r.status_code == 403, "TC-47-03 user role -> 403")

    # TC-47-05: 카테고리 삭제 — 디스크 보유 포함 409, 사용자 카테고리 200
    r = c.delete("/api/marketplace/catalog-category/diskcat", headers=H)
    chk(r.status_code == 409, f"TC-47-05 disk-backed category -> 409 ({r.status_code})")
    r = c.delete("/api/marketplace/catalog-category/usercat", headers=H)
    chk(r.status_code == 200 and r.json()["deleted_assets"] == ["del-b"],
        f"TC-47-05 user category deleted ({r.status_code} {r.text[:100]})")
    r = c.delete("/api/marketplace/catalog-category/usercat", headers=H)
    chk(r.status_code == 404, "TC-47-05 missing category -> 404")

# TC-47-01·06: 프론트 정적 검증
modal = (ROOT / "front/src/pages/marketplace/AssetRegisterModal.tsx").read_text(encoding="utf-8")
chk("assetZipRequired" in modal and "zipFiles.length === 0" in modal, "TC-47-01 modal zip-required guard")
chk("registerAsset(" not in modal.replace("registerAssetZips(", ""), "TC-47-01 meta-only path removed from modal")
api = (ROOT / "front/src/api/marketplace.ts").read_text(encoding="utf-8")
chk("deleteAsset" in api and "deleteCategory" in api and "deletable?: boolean" in api, "TC-47-06 api client")
page = (ROOT / "front/src/pages/marketplace/MarketplacePage.tsx").read_text(encoding="utf-8")
chk("handleDeleteAsset" in page and "handleDeleteCategory" in page and "a.deletable" in page,
    "TC-47-06 page wiring")
# TC-47-07: 삭제 확인 = 커스텀 ConfirmDialog (R18-1) — browser confirm 금지
chk("window.confirm" not in page and "<ConfirmDialog" in page and "setConfirmDel" in page,
    "TC-47-07 custom ConfirmDialog (no window.confirm)")
# TC-47-08: 등록 모달 — 카탈로그 첫 행 순서 + 필수 * 표시 + '(선택)' 라벨 제거
_cat = modal.index("assetCategory")
chk(_cat < modal.index("form.name}") and _cat < modal.index("assetKind"), "TC-47-08 category first")
chk("text-red-500 font-bold" in modal, "TC-47-08 required * marker on ZIP")
for loc in ("ko", "en"):
    ag = json.loads((ROOT / f"front/src/locales/{loc}.json").read_text(encoding="utf-8"))["agent"]
    chk(all("선택)" not in ag[k] and "optional)" not in ag[k]
            for k in ("assetNameEn", "assetDescEn", "assetZip")), f"TC-47-08 {loc} labels no-optional")
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
for sect, key in [("agent", "assetZipRequired"), ("mp", "deleteAsset"), ("mp", "deleteCategory"),
                  ("mp", "deleteAssetConfirm"), ("mp", "deleteCategoryConfirm"), ("mp", "deleteFailed")]:
    chk(key in ko[sect] and key in en[sect], f"TC-47-06 locale parity {sect}.{key}")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
