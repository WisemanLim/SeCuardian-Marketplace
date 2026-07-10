#!/usr/bin/env python3
"""marketplace-assets 스캔 → 자산 카탈로그 시드 스크립트 (§7.6.2).

Usage:
    uv run python scripts/seed_assets.py
    make seed-assets

포함 내용:
  - marketplace-assets/{security,utilities}/ 를 스캔해 {key}-meta.json 기반으로
    marketplace_assets 에 **미등록 자산만 INSERT** (category = 디렉터리명).
    기존 등록분(seed_security 의 curated 설명 포함)은 갱신하지 않는다.
  - marketplace_asset_blobs: {key}.zip 블롭 checksum upsert (설치 시 hot-deploy).

builtin(코어 내장)·addon(스캐폴드 템플릿)은 카탈로그 시드 대상이 아니다.
보안 13종의 curated ko/en 설명 시드는 seed_security.py(=make seed-security) 담당.
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings as _settings
from app.db import _PH, apply_column_migrations, execute_insert, execute_write, fetch_one, run_migrations

_ASSETS_ROOT = Path(__file__).resolve().parent.parent / "marketplace-assets"
_CATEGORIES = ("security", "utilities")


def _tenant() -> str:
    return _settings.tenant_default_id or "default"


def _read_meta(asset_dir: Path) -> dict:
    metas = sorted(asset_dir.glob("*-meta.json"))
    if not metas:
        return {}
    return json.loads(metas[0].read_text(encoding="utf-8"))


async def _seed_one(category: str, asset_dir: Path, tid: str) -> None:
    meta = _read_meta(asset_dir)
    asset_key = str(meta.get("agent_key") or meta.get("key") or asset_dir.name)
    name = str(meta.get("name") or asset_key)
    name_en = str(meta.get("name_en") or "")
    version = str(meta.get("version") or "1.0.0")
    desc = str(meta.get("description") or "")

    zip_path = _ASSETS_ROOT / category / f"{asset_dir.name}.zip"
    raw = zip_path.read_bytes() if zip_path.exists() else b""
    checksum = hashlib.sha256(raw).hexdigest() if raw else ""

    dup = await fetch_one(
        f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH}",
        (asset_key, tid),
    )
    if dup:
        print(f"[seed-assets] {category}/{asset_key}: 기존 등록 유지(스킵)")
    else:
        await execute_insert(
            f"INSERT INTO marketplace_assets "
            f"(tenant_id, asset_key, version, kind, name, name_en, description, category, "
            f" min_platform_version, governance, required_env, checksum, source) "
            f"VALUES ({','.join([_PH] * 13)})",
            (tid, asset_key, version, "agent", name, name_en, desc, category,
             "0.1.0", "", "", checksum, "local"),
        )
        print(f"[seed-assets] {category}/{asset_key}: 카탈로그 등록 (v{version})")

    if not raw:
        print(f"[seed-assets]   ⚠️ zip 미존재: {zip_path}")
        return
    blob = await fetch_one(
        f"SELECT id, checksum FROM marketplace_asset_blobs "
        f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset_key, version, tid),
    )
    if blob and blob.get("checksum") == checksum:
        return
    await execute_write(
        f"DELETE FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset_key, version, tid),
    )
    await execute_insert(
        f"INSERT INTO marketplace_asset_blobs (tenant_id, asset_key, version, filename, checksum, blob, uploaded_by) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
        (tid, asset_key, version, f"{asset_dir.name}.zip", checksum, raw, "seed-assets"),
    )
    print(f"[seed-assets]   blob 등록: {asset_dir.name}.zip ({len(raw)} bytes)")


async def main() -> None:
    await apply_column_migrations()
    await run_migrations()

    tid = _tenant()
    total = 0
    for category in _CATEGORIES:
        cat_dir = _ASSETS_ROOT / category
        if not cat_dir.is_dir():
            print(f"[seed-assets] ⚠️ 디렉터리 없음: {cat_dir}")
            continue
        for asset_dir in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
            await _seed_one(category, asset_dir, tid)
            total += 1

    print(f"\n[seed-assets] 완료! {'/'.join(_CATEGORIES)} 자산 {total}종 스캔")
    print("  확인: 에이전트 관리 → 내장 에이전트 탭 → 자산 카탈로그 (카테고리별 표시)")


if __name__ == "__main__":
    asyncio.run(main())
