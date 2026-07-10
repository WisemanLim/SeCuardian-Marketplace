"""impl/48 — 자산 등록 회귀 수정: category 반영 + 폼 입력 반영 (격리 sqlite + TestClient, impl/1 패턴)."""
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


with TestClient(m.app) as c:
    # 1) 단일 ZIP + 폼 입력 + 신규 카탈로그 testcat — 폼 값이 meta 를 덮어씀
    r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "testcat"},
               data={"name": "테스트 자산", "name_en": "Test Asset",
                     "description": "폼 설명", "description_en": "form desc", "kind": "workflow"},
               files=[("files", ("reg-a.zip", make_zip("reg-a"), "application/zip"))])
    chk(r.status_code == 201, f"1. 단일 ZIP 등록 201 (got {r.status_code})")
    a = (r.json().get("assets") or [{}])[0]
    chk(a.get("category") == "testcat", f"1. category=testcat (got {a.get('category')})")
    chk(a.get("name") == "테스트 자산", f"1. name=폼 값 (got {a.get('name')})")
    chk(a.get("name_en") == "Test Asset", f"1. name_en=폼 값 (got {a.get('name_en')})")
    chk(a.get("description") == "폼 설명", f"1. description=폼 값 (got {a.get('description')})")
    chk(a.get("kind") == "workflow", f"1. kind=workflow (got {a.get('kind')})")

    # 2) 동일 key@version ZIP 을 movecat 으로 재등록 — 중복 없이 category 이동
    #    (§7.6.6 v0.47: 중복 재등록은 사용자 확인 confirm=true 필요 — impl/49)
    r = c.post("/api/marketplace/catalog/zip", headers=H,
               params={"category": "movecat", "confirm": "true"},
               data={"name": "이동 자산", "description": "이동 설명"},
               files=[("files", ("reg-a.zip", make_zip("reg-a"), "application/zip"))])
    chk(r.status_code == 201, f"2. 재등록 201 (got {r.status_code})")
    a = (r.json().get("assets") or [{}])[0]
    chk(a.get("category") == "movecat", f"2. 재등록 시 category 이동 (got {a.get('category')})")
    chk(a.get("name") == "이동 자산", f"2. 재등록 시 폼 name 반영 (got {a.get('name')})")

    r = c.get("/api/marketplace/catalog", headers=H)
    keys = [x["asset_key"] for x in r.json()["assets"] if x["asset_key"] == "reg-a"]
    chk(len(keys) == 1, f"2. 중복 행 없음 (got {len(keys)})")

    # 3) 신규 카탈로그에서 조회 가능
    r = c.get("/api/marketplace/catalog", headers=H, params={"category": "movecat"})
    got = [x["asset_key"] for x in r.json()["assets"]]
    chk("reg-a" in got, f"3. movecat 카탈로그에서 자산 확인 (got {got})")
    r = c.get("/api/marketplace/catalog", headers=H, params={"category": "testcat"})
    chk(r.json()["assets"] == [], "3. 이전 카탈로그(testcat)에는 잔존 없음")

    # 4) 다중 ZIP + 폼 name — 폼 무시, meta name 사용, 둘 다 요청 category
    r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "multicat"},
               data={"name": "무시될 이름", "description": "무시될 설명"},
               files=[("files", ("mz-a.zip", make_zip("mz-a", "메타A"), "application/zip")),
                      ("files", ("mz-b.zip", make_zip("mz-b", "메타B"), "application/zip"))])
    chk(r.status_code == 201, f"4. 다중 ZIP 등록 201 (got {r.status_code})")
    assets = {x["asset_key"]: x for x in r.json()["assets"]}
    chk(assets.get("mz-a", {}).get("name") == "메타A", f"4. 다중 시 meta name 사용 (got {assets.get('mz-a', {}).get('name')})")
    chk(all(x["category"] == "multicat" for x in assets.values()), "4. 다중 ZIP 전부 요청 category 소속")
    chk(all(x["kind"] == "agent" for x in assets.values()), "4. 다중 시 kind=agent 기본값")

    # 5) 폼 미전송(레거시 호출) — meta 기반 등록 하위호환
    r = c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "legacycat"},
               files=[("files", ("lg-a.zip", make_zip("lg-a", "레거시"), "application/zip"))])
    chk(r.status_code == 201, f"5. 레거시 호출 201 (got {r.status_code})")
    a = (r.json().get("assets") or [{}])[0]
    chk(a.get("name") == "레거시", f"5. meta name 사용 (got {a.get('name')})")
    chk(a.get("category") == "legacycat", f"5. category 반영 (got {a.get('category')})")

print()
if fails:
    print(f"FAIL {len(fails)}건: {fails}")
    sys.exit(1)
print("ALL PASS")
