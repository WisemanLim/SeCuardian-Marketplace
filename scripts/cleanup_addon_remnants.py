#!/usr/bin/env python3
"""hot-deploy 잔재 일괄 정리 스크립트 (§7.6.5).

Usage:
    uv run python scripts/cleanup_addon_remnants.py
    make cleanup-addons

정리 대상 (멱등):
  A) 활성 설치(marketplace_installs.active=1)가 없는 카탈로그 자산의 hot-deploy 잔재 —
     tbl_addon_agents 행(자산 키와 대소문자 무시 매칭) + addon-agents/deployed/{key}/ +
     front/src/pages/addon/deployed/{key}.tsx + MCP 설정. tbl_agent_config 행은 유지(재설치 대비).
  B) tbl_addon_agents 행이 없는 고아 addon-agents/deployed/ 디렉터리
     (과거 결함·중단된 시험 실행으로 남은 것).

카탈로그 자산과 무관한 사용자 ADDON(tbl_addon_agents 에 행이 있고 자산 키와 불일치)은 건드리지 않는다.
front 화면이 있던 잔재를 지운 경우 반영을 위해 web 재빌드(앱 경유 또는 재기동)가 필요할 수 있다.
"""
import asyncio
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import _PH, fetch_all, fetch_one

_DEPLOYED = Path("addon-agents/deployed")


async def main() -> None:
    from app.routers.router_addon_agent import _remove_addon_artifacts

    assets = await fetch_all("SELECT DISTINCT asset_key, tenant_id FROM marketplace_assets", ())
    removed_rows, removed_orphans = [], []

    # A) 활성 설치 없는 자산의 addon 잔재
    for a in assets:
        active = await fetch_one(
            f"SELECT id FROM marketplace_installs WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1",
            (a["asset_key"], a["tenant_id"]),
        )
        if active:
            continue
        addon = await fetch_one(
            f"SELECT agent_key, sql_path FROM tbl_addon_agents WHERE LOWER(agent_key) = LOWER({_PH})",
            (a["asset_key"],),
        )
        if addon:
            await _remove_addon_artifacts(
                addon["agent_key"], addon.get("sql_path") or "",
                delete_config=False, rebuild_web=False,
            )
            removed_rows.append(addon["agent_key"])
            print(f"[cleanup] A) 미설치 자산 잔재 제거: {addon['agent_key']}")

    # B) addon 행 없는 고아 deployed 디렉터리
    rows = await fetch_all("SELECT agent_key FROM tbl_addon_agents", ())
    known = {r["agent_key"].lower() for r in rows}
    if _DEPLOYED.is_dir():
        for d in sorted(p for p in _DEPLOYED.iterdir() if p.is_dir()):
            if d.name.lower() not in known:
                shutil.rmtree(d)
                removed_orphans.append(d.name)
                print(f"[cleanup] B) 고아 deployed 디렉터리 제거: {d.name}")

    print(f"\n[cleanup] 완료 — addon 잔재 {len(removed_rows)}건, 고아 디렉터리 {len(removed_orphans)}건 제거")
    if removed_rows:
        print("  front 화면이 있던 항목은 web 재빌드(또는 재기동) 후 좌측 메뉴에서 사라집니다.")


if __name__ == "__main__":
    asyncio.run(main())
