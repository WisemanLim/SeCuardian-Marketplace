"""§7.6.4-5·6 installed-tab grouping + case-insensitive match — static + logic simulation.

프론트 전용 이터레이션: AgentsPage 정적 검증 + 필터/그룹 로직 Python 재현 + dev DB 재현 데이터 확인.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


src = (ROOT / "front/src/pages/agents/AgentsPage.tsx").read_text(encoding="utf-8")

# A1) case-insensitive matching (§7.6.4-6)
chk("a.asset_key.toLowerCase()" in src and "c.agent_key.toLowerCase()" in src,
    "A1 case-insensitive catalog match")
chk("assetByLowerKey" in src and "installedLower" in src, "A1 lower-key maps")

# B1) group order — builtin first, then catalog category order
chk('if (x === "builtin") return -1' in src and 'if (y === "builtin") return 1' in src,
    "B1 builtin group first")
chk('CATEGORY_ORDER = ["security", "utilities", "general"]' in src, "B1 category order")

# B2) grouped section render on installed tab
chk("installedGroups.map(([cat, items])" in src and "mp.cat.${cat}" in src,
    "B2 grouped sections with mp.cat headers")

# B3) in-group sort — builtin keeps config order, catalog groups by catalog index
chk('if (cat !== "builtin")' in src and "catalogOrderIdx.get(x.agent_key.toLowerCase())" in src,
    "B3 in-group sort")

# C1) locales
ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
chk("builtin" in ko["mp"]["cat"] and "builtin" in en["mp"]["cat"], "C1 mp.cat.builtin parity")

# A2) dev DB 재현 데이터 — usermanager(소문자 config) + UserManager(자산, 미설치)
con = sqlite3.connect(ROOT / "local.db")
cfg_keys = {r[0] for r in con.execute("SELECT agent_key FROM tbl_agent_config").fetchall()}
assets = {r[0]: r[1] for r in con.execute(
    "SELECT asset_key, "
    "(SELECT COUNT(*) FROM marketplace_installs i WHERE i.asset_key=marketplace_assets.asset_key AND i.active=1) "
    "FROM marketplace_assets").fetchall()}
con.close()
has_repro = "usermanager" in cfg_keys and "UserManager" in assets
chk(has_repro, f"A2 repro data present (usermanager cfg={'usermanager' in cfg_keys})")

# D1) 필터/그룹 로직 Python 재현 — AgentsPage 와 동일 규칙
CATEGORY_ORDER = ["security", "utilities", "general"]


def cat_order(c):
    return CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else len(CATEGORY_ORDER)


def simulate(configs, catalog):
    """configs: [(agent_key)], catalog: {asset_key: (category, installed)} → 그룹 [(cat, [keys])]."""
    by_lower = {k.lower(): (k, v[0], v[1]) for k, v in catalog.items()}
    installed = {k.lower() for k, v in catalog.items() if v[1]}
    kept = [c for c in configs if c.lower() not in by_lower or c.lower() in installed]
    groups: dict = {}
    for c in kept:
        a = by_lower.get(c.lower())
        cat = (a[1] or "general") if a else "builtin"
        groups.setdefault(cat, []).append(c)
    ordered = sorted(groups.items(), key=lambda kv: (kv[0] != "builtin", cat_order(kv[0]), kv[0]))
    return ordered


catalog = {
    "UserManager": ("utilities", False),   # 해제됨 — 숨김 대상 (대소문자 불일치 재현)
    "vasca-cve": ("security", True),
    "server-shell": ("utilities", True),
    "board": ("utilities", False),
}
configs = ["general", "chat", "marketplace", "usermanager", "vasca-cve", "server-shell", "board"]
result = simulate(configs, catalog)
flat = {c for _, items in result for c in items}
chk("usermanager" not in flat and "board" not in flat, "D1 uninstalled hidden (case-insensitive)")
chk("vasca-cve" in flat and "server-shell" in flat, "D1 installed shown")
cats = [c for c, _ in result]
chk(cats == ["builtin", "security", "utilities"], f"D1 group order ({cats})")
chk(result[0][1] == ["general", "chat", "marketplace"], "D1 builtin keeps config order")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
