"""§7.6.4 marketplace 3-tab — static front checks + install/uninstall visibility contract.

프론트 전용 이터레이션: 정적 검증 + 설치됨 탭 판정 기준(installed 플래그)의 백엔드 실동작 확인.
Fresh sqlite + TestClient (test/impl/1 패턴).
"""
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


agents_src = (ROOT / "front/src/pages/agents/AgentsPage.tsx").read_text(encoding="utf-8")
mp_src = (ROOT / "front/src/pages/marketplace/MarketplacePage.tsx").read_text(encoding="utf-8")

# A1) tab composition + default
chk('type Tab = "catalog" | "installed" | "addon"' in agents_src, "A1 Tab type 3-way")
chk('useState<Tab>("catalog")' in agents_src, "A1 default tab = catalog")
chk('tab === "builtin"' not in agents_src, "A1 old builtin tab removed")

# A2) tab labels/counts
chk('t("agent.assetCatalog")' in agents_src and 't("agent.installedTab")' in agents_src
    and 't("agent.addon")' in agents_src, "A2 tab labels")
chk("count: catalogAssets.length" in agents_src and "count: installedConfigs.length" in agents_src
    and "count: userAddons.length" in agents_src, "A2 tab counts")

# A3) buttons per tab
chk('tab === "catalog" && isAdmin' in agents_src, "A3 register button on catalog tab")
chk('tab === "addon" && isAdmin' in agents_src, "A3 builder button on addon tab")

# B1) installed filter — impl/45(§7.6.4-6)에서 대소문자 무시 매칭으로 개정
chk("!assetByLowerKey.has(k) || installedLower.has(k)" in agents_src,
    "B1 installed filter (non-catalog OR active install)")

# B2) installed sort — impl/45(§7.6.4-5)에서 카테고리 그룹핑(builtin 최우선)으로 개정
chk("catalogOrderIdx" in agents_src and 'if (x === "builtin") return -1' in agents_src,
    "B2 sort: builtin first, catalog order after")

# B3) marketplaceChanged dispatch on install/uninstall/remote-install
chk(mp_src.count('dispatchEvent(new CustomEvent("marketplaceChanged"))') >= 3,
    "B3 dispatch on install/uninstall/remote (3+)")

# B4) AgentsPage listener + catalog reload
chk('addEventListener("marketplaceChanged", reload)' in agents_src
    and "listCatalog().then(setCatalogAssets)" in agents_src, "B4 AgentsPage listener + listCatalog")

# C1) install/uninstall → installed flag contract (설치됨 탭 판정 기준)
def make_zip(key: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{key}-app.py", "# stub\n")
        zf.writestr(f"{key}-meta.json", json.dumps({"agent_key": key, "name": key, "version": "1.0.0"}))
    return buf.getvalue()


with TestClient(m.app) as c:
    c.post("/api/marketplace/catalog/zip", headers=H, params={"category": "utilities"},
           files=[("files", ("tabtest.zip", make_zip("tabtest"), "application/zip"))])
    r = c.get("/api/marketplace/catalog/tabtest", headers=H)
    chk(r.json()["installed"] is False, "C1 registered → installed=false (설치됨 탭 숨김)")
    c.post("/api/marketplace/install/tabtest", headers=H)
    r = c.get("/api/marketplace/catalog/tabtest", headers=H)
    chk(r.json()["installed"] is True, "C1 install → installed=true (설치됨 탭 표시)")
    c.delete("/api/marketplace/install/tabtest", headers=H)
    r = c.get("/api/marketplace/catalog/tabtest", headers=H)
    chk(r.json()["installed"] is False, "C1 uninstall → installed=false (설치됨 탭 숨김)")

# D1) locales parity
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
chk(ko["agent"].get("installedTab") == "에이전트(설치됨)"
    and en["agent"].get("installedTab") == "Agents (Installed)", "D1 agent.installedTab parity")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
