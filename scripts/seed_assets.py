#!/usr/bin/env python3
"""marketplace-assets 스캔 → 자산 카탈로그 시드 스크립트 (§7.6.2).

Usage:
    uv run python scripts/seed_assets.py
    make seed-assets

포함 내용:
  - marketplace-assets/{security,utilities}/ 를 스캔해 {key}-meta.json 기반으로
    marketplace_assets 에 upsert (category = 디렉터리명, 멱등).
    meta 의 display_name/description 은 다국어 dict({"ko":…, "en":…})·레거시 문자열 모두 허용
    (_norm_descriptions 정규화 — str(dict) raw repr 저장 결함 방지, R18-7).
  - marketplace_asset_blobs: {key}.zip 블롭 checksum upsert (설치 시 hot-deploy).
  - 레거시 정규화: 대소문자 혼용 asset_key → 소문자 통일 + tbl_agent_config 중복 행 제거
    (예: 'UserManager'(install seam) vs 'usermanager'(addon 배포) 이중 노출 결함 해소).

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
from app.core.i18n import lang_json, norm_descriptions
from app.db import _PH, apply_column_migrations, execute_insert, execute_write, fetch_all, fetch_one, run_migrations

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
    # R18-7: display_name/description 다국어 dict 정규화 (공통함수, 레거시 문자열 겸용)
    meta = norm_descriptions(_read_meta(asset_dir))
    # addon 업로드 파이프라인(zip 스템 소문자화)과 키 일치 — 대소문자 혼용 중복 방지
    asset_key = str(meta.get("agent_key") or meta.get("key") or asset_dir.name).lower()
    agent_names = meta.get("agent_names") or {}
    name = str(agent_names.get("ko") or meta.get("name") or asset_key)
    name_en = str(agent_names.get("en") or meta.get("name_en") or "")
    names_json = lang_json(agent_names)
    descs_json = lang_json(meta.get("descriptions"))
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
        # 멱등 갱신 — meta 기반 이름·설명 최신화 (설치 상태 불변, raw dict repr 오염 행 복구 포함)
        await execute_write(
            f"UPDATE marketplace_assets SET name = {_PH}, name_en = {_PH}, description = {_PH}, "
            f"names = {_PH}, descriptions = {_PH}, checksum = {_PH}, updated_at = CURRENT_TIMESTAMP "
            f"WHERE id = {_PH}",
            (name, name_en, desc, names_json, descs_json, checksum, dup["id"]),
        )
        print(f"[seed-assets] {category}/{asset_key}: 기존 등록 갱신")
    else:
        await execute_insert(
            f"INSERT INTO marketplace_assets "
            f"(tenant_id, asset_key, version, kind, name, name_en, description, names, descriptions, category, "
            f" min_platform_version, governance, required_env, checksum, source) "
            f"VALUES ({','.join([_PH] * 15)})",
            (tid, asset_key, version, "agent", name, name_en, desc, names_json, descs_json, category,
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


async def _normalize_legacy_keys(tid: str) -> None:
    """대소문자 혼용 레거시 키 정규화 (멱등).

    - marketplace_assets/-_blobs/-_installs 의 asset_key 를 소문자로 통일
      (소문자 행이 이미 있으면 대문자 행 삭제 — meta 기반 upsert 가 최신본 재생성)
    - tbl_agent_config: 소문자 쌍둥이가 있는 대소문자 혼용 행 제거
      (예: 'UserManager' + 'usermanager' 2행 → 'usermanager' 유지, 중복 카드 해소)
    """
    for row in await fetch_all(
        f"SELECT id, asset_key FROM marketplace_assets WHERE tenant_id = {_PH}", (tid,)
    ):
        key = row["asset_key"]
        low = key.lower()
        if key == low:
            continue
        twin = await fetch_one(
            f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH}",
            (low, tid),
        )
        if twin:
            await execute_write(f"DELETE FROM marketplace_assets WHERE id = {_PH}", (row["id"],))
        else:
            await execute_write(
                f"UPDATE marketplace_assets SET asset_key = {_PH} WHERE id = {_PH}", (low, row["id"])
            )
        for table in ("marketplace_asset_blobs", "marketplace_installs"):
            await execute_write(
                f"UPDATE {table} SET asset_key = {_PH} WHERE asset_key = {_PH} AND tenant_id = {_PH}",
                (low, key, tid),
            )
        print(f"[seed-assets] 키 정규화: {key} → {low}")

    for row in await fetch_all("SELECT agent_key FROM tbl_agent_config"):
        key = row["agent_key"]
        low = key.lower()
        if key == low:
            continue
        twin = await fetch_one(
            f"SELECT agent_key FROM tbl_agent_config WHERE agent_key = {_PH}", (low,)
        )
        if twin:
            await execute_write(f"DELETE FROM tbl_agent_config WHERE agent_key = {_PH}", (key,))
            print(f"[seed-assets] config 중복 제거: {key} (유지: {low})")

    # marketplace 설치 이력이 있는 config 행의 빈 nav_group 복구 — uninstall 경로가
    # nav_group='marketplace' 를 조건으로 하므로 비어 있으면 해제 시 비활성화가 누락된다.
    for row in await fetch_all(
        f"SELECT DISTINCT asset_key FROM marketplace_installs WHERE tenant_id = {_PH}", (tid,)
    ):
        await execute_write(
            f"UPDATE tbl_agent_config SET nav_group = 'marketplace' "
            f"WHERE agent_key = {_PH} AND (nav_group IS NULL OR nav_group = '')",
            (row["asset_key"].lower(),),
        )


async def _repair_dict_repr_rows(tid: str) -> None:
    """과거 str(dict) 저장 결함으로 "{'ko': …}" raw repr 이 들어간 행 복구 (멱등).

    marketplace_assets·tbl_agent_config 의 name/description 이 python dict repr 이면
    literal_eval 로 dict 화 → ko 문자열 + names/descriptions JSON 으로 재저장.
    """
    import ast

    def _as_dict(text: str | None) -> dict | None:
        if not text or not text.startswith("{'"):
            return None
        try:
            obj = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return None
        return obj if isinstance(obj, dict) else None

    for row in await fetch_all(
        f"SELECT id, asset_key, name, description FROM marketplace_assets WHERE tenant_id = {_PH}", (tid,)
    ):
        names_d = _as_dict(row.get("name"))
        descs_d = _as_dict(row.get("description"))
        if not names_d and not descs_d:
            continue
        meta = norm_descriptions({
            "display_name": names_d or row.get("name") or "",
            "description": descs_d or row.get("description") or "",
        })
        await execute_write(
            f"UPDATE marketplace_assets SET name = {_PH}, name_en = {_PH}, description = {_PH}, "
            f"names = {_PH}, descriptions = {_PH}, updated_at = CURRENT_TIMESTAMP WHERE id = {_PH}",
            (meta["agent_names"].get("ko") or row["asset_key"], meta["agent_names"].get("en", ""),
             meta["description"], lang_json(meta["agent_names"]), lang_json(meta["descriptions"]),
             row["id"]),
        )
        print(f"[seed-assets] dict repr 복구: {row['asset_key']}")

    for row in await fetch_all("SELECT agent_key, agent_name, description FROM tbl_agent_config"):
        names_d = _as_dict(row.get("agent_name"))
        descs_d = _as_dict(row.get("description"))
        if not names_d and not descs_d:
            continue
        meta = norm_descriptions({
            "display_name": names_d or row.get("agent_name") or "",
            "description": descs_d or row.get("description") or "",
        })
        await execute_write(
            f"UPDATE tbl_agent_config SET agent_name = {_PH}, description = {_PH}, "
            f"agent_names = {_PH}, descriptions = {_PH}, updated_at = CURRENT_TIMESTAMP "
            f"WHERE agent_key = {_PH}",
            (meta["agent_names"].get("ko") or row["agent_key"], meta["description"],
             lang_json(meta["agent_names"]), lang_json(meta["descriptions"]), row["agent_key"]),
        )
        print(f"[seed-assets] config dict repr 복구: {row['agent_key']}")


async def _cleanup_orphaned_seed_rows(tid: str) -> None:
    """시드 유래 고아 행 정리 (멱등) — 시드 디렉터리에서 제거/이동된 자산의 카탈로그 행 삭제.

    대상 = 블롭 uploaded_by='seed-assets'(시드가 만든 행)이면서 현재
    `marketplace-assets/{security,utilities}/{key}.zip` 이 없는 key
    (예: UserManager 의 utilities → addon 이관). 사용자가 UI 로 등록한 자산
    (uploaded_by=사용자)은 건드리지 않는다. 활성 설치 중이면 건너뛴다(먼저 해제).
    """
    disk_keys = {
        z.stem.lower()
        for category in _CATEGORIES
        if (_ASSETS_ROOT / category).is_dir()
        for z in (_ASSETS_ROOT / category).glob("*.zip")
    }
    rows = await fetch_all(
        f"SELECT DISTINCT asset_key FROM marketplace_asset_blobs "
        f"WHERE tenant_id = {_PH} AND uploaded_by = 'seed-assets'",
        (tid,),
    )
    for row in rows:
        key = row["asset_key"]
        if key.lower() in disk_keys:
            continue
        active = await fetch_one(
            f"SELECT id FROM marketplace_installs WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1",
            (key, tid),
        )
        if active:
            print(f"[seed-assets] ⚠️ 시드 고아 {key}: 설치 중 — 해제 후 재실행 시 정리")
            continue
        for table, cond in (
            ("marketplace_asset_blobs", f"asset_key = {_PH} AND tenant_id = {_PH}"),
            ("marketplace_installs", f"asset_key = {_PH} AND tenant_id = {_PH}"),
            ("marketplace_assets", f"asset_key = {_PH} AND tenant_id = {_PH}"),
        ):
            await execute_write(f"DELETE FROM {table} WHERE {cond}", (key, tid))
        await execute_write(
            f"DELETE FROM tbl_agent_config WHERE LOWER(agent_key) = LOWER({_PH}) AND nav_group = 'marketplace'",
            (key,),
        )
        print(f"[seed-assets] 시드 고아 정리: {key} (시드 디렉터리 미보유)")


async def main() -> None:
    await apply_column_migrations()
    await run_migrations()

    tid = _tenant()
    await _normalize_legacy_keys(tid)
    await _repair_dict_repr_rows(tid)
    await _cleanup_orphaned_seed_rows(tid)
    total = 0
    for category in _CATEGORIES:
        cat_dir = _ASSETS_ROOT / category
        if not cat_dir.is_dir():
            print(f"[seed-assets] ⚠️ 디렉터리 없음: {cat_dir}")
            continue
        for asset_dir in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
            # R22-4: {Name}_worker 는 다운로드 전용 worker 자산 — 설치형 카탈로그 시드 제외
            if asset_dir.name.endswith("_worker"):
                continue
            await _seed_one(category, asset_dir, tid)
            total += 1

    print(f"\n[seed-assets] 완료! {'/'.join(_CATEGORIES)} 자산 {total}종 스캔")
    print("  확인: 에이전트 관리 → 내장 에이전트 탭 → 자산 카탈로그 (카테고리별 표시)")


if __name__ == "__main__":
    asyncio.run(main())
