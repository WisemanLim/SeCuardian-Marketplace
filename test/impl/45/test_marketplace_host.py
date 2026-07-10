#!/usr/bin/env python3
"""impl/47 (물리 45): Marketplace-host 공개 카탈로그 API (§7.3.5) 시험.

Usage:
    uv run python test/impl/45/test_marketplace_host.py
"""
import asyncio
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from fastapi import HTTPException  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.routers import router_marketplace_host as host  # noqa: E402

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


def fs_zip_count(category: str | None = None) -> int:
    base = ROOT / "marketplace-assets"
    dirs = [base / category] if category else [d for d in base.iterdir() if d.is_dir()]
    return sum(len(list(d.glob("*.zip"))) for d in dirs if d.exists())


def main() -> int:
    import os
    os.chdir(ROOT)  # 라우터의 상대경로(marketplace-assets) 기준

    # TC-45-01: ping
    print("TC-45-01: GET /ping")
    ping = asyncio.run(host.ping(None))
    check("ok/service", ping["ok"] is True and ping["service"] == "SeCuardian-Marketplace")
    check("categories", set(ping["categories"]) == {"addon", "builtin", "security", "utilities"},
          str(ping["categories"]))
    check("total == 파일시스템 zip 수", ping["total"] == fs_zip_count(), f"({ping['total']})")

    # TC-45-02: catalog 전량 (설치유무 무관)
    print("TC-45-02: GET /catalog — 전량·설치유무 무관")
    cat = asyncio.run(host.host_catalog(None, None))
    check("total 일치", cat["total"] == fs_zip_count(), f"({cat['total']})")
    check("groups 키 == categories", set(cat["groups"].keys()) == set(cat["categories"]))
    keys = {a["asset_key"]: a["category"] for a in cat["assets"]}
    for k, c in (("Board", "addon"), ("rag", "builtin"), ("agentic-soc", "security"), ("UserManager", "addon")):
        check(f"{k} ∈ {c}", keys.get(k) == c)
    src = (ROOT / "app/routers/router_marketplace_host.py").read_text()
    check("DB 미참조(설치유무 무관)", "from app.db" not in src and "fetch_" not in src)

    # TC-45-03: category 필터
    print("TC-45-03: GET /catalog?category=security")
    sec = asyncio.run(host.host_catalog("security", None))
    check("security 그룹만", sec["categories"] == ["security"])
    check("자산 수 == security zip 수", sec["total"] == fs_zip_count("security"), f"({sec['total']})")

    # TC-45-04: 상세 + checksum
    print("TC-45-04: GET /catalog/Board 상세")
    detail = asyncio.run(host.host_asset("Board", None))
    zip_bytes = (ROOT / "marketplace-assets/addon/Board.zip").read_bytes()
    check("checksum == 실 ZIP SHA256", detail["checksum"] == hashlib.sha256(zip_bytes).hexdigest())
    check("download_path", detail["download_path"] == "/download/Board")
    check("category/version", detail["category"] == "addon" and bool(detail["version"]))
    check("다국어 names dict", isinstance(detail["names"], dict) and bool(detail["names"]))

    # TC-45-05: download
    print("TC-45-05: GET /download/Board")
    resp = asyncio.run(host.host_download("Board", None))
    check("FileResponse 경로 == 실 zip", Path(resp.path).resolve() == (ROOT / "marketplace-assets/addon/Board.zip").resolve())
    check("바이트 SHA256 == checksum", hashlib.sha256(Path(resp.path).read_bytes()).hexdigest() == detail["checksum"])

    # TC-45-06: 인증 (MARKETPLACE_HOST_API_KEY)
    print("TC-45-06: 인증 — API 키 설정/미설정")
    orig = settings.marketplace_host_api_key
    try:
        settings.marketplace_host_api_key = "test-key-45"
        for label, hdr, expect_401 in (
            ("헤더 없음", "", True),
            ("오류 키", "Bearer wrong", True),
            ("일치 키", "Bearer test-key-45", False),
        ):
            try:
                host._require_host_key(hdr)
                check(label, not expect_401)
            except HTTPException as exc:
                check(label, expect_401 and exc.status_code == 401)
        settings.marketplace_host_api_key = ""
        host._require_host_key("")  # 미설정 → 개방 (예외 없음)
        check("미설정 개방", True)
    finally:
        settings.marketplace_host_api_key = orig

    # TC-45-07: 경로 탐색/미존재
    print("TC-45-07: 경로 탐색 방지·미존재 404")
    for bad in ("../etc", "a/b", "..", ".hidden", "nonexistent-key-xyz"):
        try:
            asyncio.run(host.host_asset(bad, None))
            check(f"404: {bad}", False)
        except HTTPException as exc:
            check(f"404: {bad}", exc.status_code == 404)

    # TC-45-08: 정적 검증
    print("TC-45-08: 배선·설정·env 정적 검증")
    main_py = (ROOT / "app/main.py").read_text()
    check("main.py 라우터 등록", "router_marketplace_host" in main_py
          and "include_router(router_marketplace_host.router)" in main_py)
    check("config marketplace_host_api_key", hasattr(settings, "marketplace_host_api_key"))
    import re
    for env in (".env.example", ".env.local", ".env.dev", ".env.staging", ".env.prod"):
        t = (ROOT / env).read_text()
        has = "MARKETPLACE_HOST_API_KEY" in t
        # 빈 값 + 인라인 주석 조합 금지 (dotenv 가 주석을 값으로 파싱하는 결함 방지)
        bad_inline = bool(re.search(r"^MARKETPLACE_HOST_API_KEY=[ \t]+#", t, re.M))
        check(f"{env} 키 존재·형식", has and not bad_inline)

    print(f"\n결과: PASS {PASS} / FAIL {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
