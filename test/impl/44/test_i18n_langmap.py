#!/usr/bin/env python3
"""impl/46 (물리 44): 다국어 언어셋 dict 일원화 + UserManager 중복 결함 시험.

Usage:
    uv run python test/impl/44/test_i18n_langmap.py
"""
import asyncio
import io
import json
import sqlite3
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SECUARDIAN = ROOT.parent / "SeCuardian"
sys.path.insert(0, str(ROOT))

from app.core.i18n import lang_json, norm_descriptions, parse_lang_map  # noqa: E402

PASS = 0
FAIL = 0


def check(case: str, cond: bool, note: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {case} {note}")
    else:
        FAIL += 1
        print(f"  ❌ {case} {note}")


def t_a_meta_files() -> None:
    print("[A] meta.json 전수 + zip 반영")
    metas = sorted((ROOT / "marketplace-assets").glob("*/*/*-meta.json"))
    bad = []
    for p in metas:
        d = json.loads(p.read_text(encoding="utf-8"))
        dn, ds = d.get("display_name"), d.get("description")
        if not (isinstance(dn, dict) and dn.get("ko") and dn.get("en")):
            bad.append((p.name, "display_name"))
        if not (isinstance(ds, dict) and ds.get("ko") and ds.get("en")):
            bad.append((p.name, "description"))
    check("A1 meta dict ko/en 전수", len(metas) >= 29 and not bad, f"({len(metas)}종, bad={bad})")

    mismatch = []
    for p in metas:
        zip_path = p.parent.parent / f"{p.parent.name}.zip"
        if not zip_path.exists():
            continue
        with zipfile.ZipFile(zip_path) as zf:
            names = [n for n in zf.namelist() if n.endswith("-meta.json")]
            if not names or zf.read(names[0]).decode("utf-8") != p.read_text(encoding="utf-8"):
                mismatch.append(zip_path.name)
    check("A2 zip 내 meta 동기", not mismatch, f"(mismatch={mismatch})")


def t_b_common_funcs() -> None:
    print("[B] 공통 파서 단위")
    m1 = norm_descriptions({"description": {"ko": "가", "en": "a", "jp": "あ"}})
    check("B1 dict 형", m1["descriptions"] == {"ko": "가", "en": "a", "jp": "あ"}
          and m1["description"] == "가" and m1["description_en"] == "a")
    m2 = norm_descriptions({"description": "가", "description_en": "a", "display_name": "이름"})
    check("B1 레거시 split", m2["descriptions"] == {"ko": "가", "en": "a"}
          and m2["agent_names"] == {"ko": "이름"})
    m3 = norm_descriptions({"display_name": {"ko": "이름", "en": "Name"}})
    check("B1 display_name dict", m3["agent_names"] == {"ko": "이름", "en": "Name"}
          and m3["display_name"] == "이름")

    d = {"ko": "가", "en": "a"}
    check("B2 lang_json/parse_lang_map 왕복", parse_lang_map(lang_json(d)) == d)
    check("B2 오염 문자열 안전", parse_lang_map("{'ko': '가'}") == {} and parse_lang_map(None) == {}
          and parse_lang_map({"ko": "가", "en": ""}) == {"ko": "가"})

    from app.routers.router_marketplace import _parse_zip_meta
    raw = (ROOT / "marketplace-assets/utilities/UserManager.zip").read_bytes()
    meta = _parse_zip_meta(raw, "UserManager.zip")
    check("B3 _parse_zip_meta", meta["asset_key"] == "usermanager"
          and meta["name"] == "사용자 관리 (UserManager)" and meta["name_en"] == "User Manager"
          and meta["names"].get("en") == "User Manager" and meta["descriptions"].get("en"),
          f"(key={meta['asset_key']})")


def t_c_db() -> None:
    print("[C] dev DB 상태")
    conn = sqlite3.connect(ROOT / "local.db")
    cur = conn.cursor()
    n1 = cur.execute(
        "SELECT COUNT(*) FROM marketplace_assets WHERE description LIKE '{''%' OR name LIKE '{''%'"
    ).fetchone()[0]
    n2 = cur.execute(
        "SELECT COUNT(*) FROM tbl_agent_config WHERE description LIKE '{''%' OR agent_name LIKE '{''%'"
    ).fetchone()[0]
    check("C1 raw dict repr 0건", n1 == 0 and n2 == 0, f"(assets={n1}, config={n2})")

    n3 = cur.execute(
        "SELECT COUNT(*) FROM marketplace_assets WHERE asset_key <> LOWER(asset_key)"
    ).fetchone()[0]
    check("C2 asset_key 소문자", n3 == 0, f"({n3}건)")

    dups = cur.execute(
        "SELECT LOWER(agent_key), COUNT(*) c FROM tbl_agent_config GROUP BY LOWER(agent_key) HAVING c > 1"
    ).fetchall()
    um = cur.execute(
        "SELECT COUNT(*) FROM tbl_agent_config WHERE LOWER(agent_key) = 'usermanager'"
    ).fetchone()[0]
    check("C3 config 대소문자 중복 0건 (usermanager 단일)", not dups and um == 1,
          f"(dups={dups}, usermanager={um})")

    rows = cur.execute(
        "SELECT asset_key, names, descriptions FROM marketplace_assets "
        "WHERE category IN ('security','utilities')"
    ).fetchall()
    bad = [k for k, n, d in rows
           if not (parse_lang_map(n).get("ko") and parse_lang_map(n).get("en")
                   and parse_lang_map(d).get("ko") and parse_lang_map(d).get("en"))]
    check("C4 자산 names/descriptions ko+en", rows and not bad, f"({len(rows)}종, bad={bad})")
    conn.close()


async def t_d_api() -> None:
    print("[D] API in-process")
    import httpx
    from app.core.security import create_access_token
    from app.main import app as _app

    token = create_access_token({"sub": "impl44", "role": "supervisor", "username": "impl44"})
    headers = {"Authorization": f"Bearer {token}"}
    transport = httpx.ASGITransport(app=_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as c:
        r = await c.get("/api/marketplace/catalog", headers=headers)
        assets = r.json().get("assets", [])
        sec = [a for a in assets if a.get("category") in ("security", "utilities")]
        bad = [a["asset_key"] for a in sec
               if not (parse_lang_map(a.get("names")).get("en")
                       and parse_lang_map(a.get("descriptions")).get("en"))]
        leak = [a["asset_key"] for a in assets if str(a.get("description", "")).startswith("{'")]
        check("D1 catalog names/descriptions", r.status_code == 200 and sec and not bad and not leak,
              f"({len(sec)}종, bad={bad}, repr누출={leak})")

        r2 = await c.get("/api/agent-config/", headers=headers)
        agents = {a["agent_key"]: a for a in r2.json().get("agents", [])}
        builtin = ["general", "chat", "marketplace", "workflow", "rag", "playground", "guardrails"]
        bad2 = [k for k in builtin
                if not (agents.get(k, {}).get("agent_names", {}).get("en")
                        and agents.get(k, {}).get("descriptions", {}).get("en"))]
        check("D2 agent-config builtin 7종 ko/en", r2.status_code == 200 and not bad2, f"(bad={bad2})")


def t_e_install_seam() -> None:
    print("[E] install seam 로직 시뮬레이션")
    # router_marketplace.install step2 와 동일 로직 재현 — 자산 행 → config upsert 파라미터
    asset = {
        "kind": "agent", "asset_key": "UserManager", "name": "사용자 관리 (UserManager)",
        "name_en": "User Manager",
        "names": lang_json({"ko": "사용자 관리 (UserManager)", "en": "User Manager"}),
        "descriptions": lang_json({"ko": "가", "en": "a"}),
        "description": "가",
    }
    cfg_key = asset["asset_key"].lower()
    _descs = parse_lang_map(asset.get("descriptions")) or (
        {"ko": asset["description"]} if asset.get("description") else {})
    _names = parse_lang_map(asset.get("names"))
    check("E1 cfg_key 소문자 + dict 전파", cfg_key == "usermanager"
          and _descs == {"ko": "가", "en": "a"} and _names.get("en") == "User Manager")


def t_f_locales() -> None:
    print("[F] locales 패리티")
    ko = json.loads((ROOT / "front/src/locales/ko.json").read_text(encoding="utf-8"))
    en = json.loads((ROOT / "front/src/locales/en.json").read_text(encoding="utf-8"))
    check("F2 assetNameEn·assetDescEn 양측", all(
        k in ko["agent"] and k in en["agent"] for k in ("assetNameEn", "assetDescEn")))


def t_g_secuardian() -> None:
    print("[G] SeCuardian 복제")
    src = ROOT / "marketplace-assets/security"
    dst = SECUARDIAN / "addon-agents/zip"
    diff = []
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        meta_src = next(d.glob("*-meta.json"))
        meta_dst = dst / d.name / meta_src.name
        if not meta_dst.exists() or meta_dst.read_text(encoding="utf-8") != meta_src.read_text(encoding="utf-8"):
            diff.append(d.name)
        zsrc, zdst = src / f"{d.name}.zip", dst / f"{d.name}.zip"
        if not zdst.exists() or zsrc.read_bytes() != zdst.read_bytes():
            diff.append(f"{d.name}.zip")
    check("G1 addon-agents/zip 13종 동기", not diff, f"(diff={diff})")

    conn = sqlite3.connect(SECUARDIAN / "local.db")
    cur = conn.cursor()
    keys = ["general", "chat", "vasca-cve", "teler-ids", "agentic-soc"]
    rows = dict(cur.execute(
        f"SELECT agent_key, agent_names FROM tbl_agent_config WHERE agent_key IN ({','.join('?' * len(keys))})",
        keys,
    ).fetchall())
    bad = [k for k in keys if not (parse_lang_map(rows.get(k)).get("ko") and parse_lang_map(rows.get(k)).get("en"))]
    check("G2 SeCuardian agent_names ko/en", not bad, f"(bad={bad})")
    conn.close()


async def main() -> None:
    t_a_meta_files()
    t_b_common_funcs()
    t_c_db()
    await t_d_api()
    t_e_install_seam()
    t_f_locales()
    t_g_secuardian()
    print(f"\n결과: PASS {PASS} / FAIL {FAIL}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
