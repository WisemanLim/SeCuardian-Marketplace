"""router_marketplace (F-MP) — /api/marketplace.

카탈로그 등록·조회·상세 + 설치 트랜잭션(단일 활성 버전)·해제. SeCuardian Path A 준용.
설치 = hot-deploy seam: install 기록 + tbl_agent_config upsert(카탈로그/Orchestrator 자동 노출).
addon(ZIP) 자산의 실제 무중단 마운트는 기존 router_addon_agent upload 파이프라인을 재사용한다
(1차: config upsert seam. addon-loader 배선은 §7.6 후속).

참조: SeCuardian-Marketplace-v0 router/service/model 을 raw-SQL 아키텍처로 이식.
설치/해제·등록은 admin 이상(require_role). tenant 는 JWT 미포함이라 TENANT_DEFAULT_ID 사용.
"""
import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

ASSET_KINDS = ("agent", "workflow", "rag-pipeline", "tool-proxy")


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class AssetCreate(BaseModel):
    asset_key: str = Field(min_length=1, max_length=64)
    version: str = Field(default="0.1.0", max_length=32)
    kind: str = Field(default="agent")
    name: str = Field(min_length=1, max_length=128)
    name_en: str = Field(default="", max_length=128)
    description: str = ""
    category: str = Field(default="general", max_length=64)
    min_platform_version: str = Field(default="0.1.0", max_length=32)
    governance: str = ""
    required_env: str = ""
    checksum: str = ""
    source: str = Field(default="local")


async def _active_version(asset_key: str, tenant_id: str) -> str | None:
    row = await fetch_one(
        f"SELECT version FROM marketplace_installs "
        f"WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1 "
        f"ORDER BY id DESC LIMIT 1",
        (asset_key, tenant_id),
    )
    return row["version"] if row else None


async def _asset_out(asset: dict, tenant_id: str) -> dict:
    ver = await _active_version(asset["asset_key"], tenant_id)
    return {**asset, "installed": ver is not None, "active_version": ver}


@router.get("/catalog")
async def list_catalog(
    kind: str | None = None,
    category: str | None = None,
    user: dict = Depends(get_current_user),
):
    tid = _tenant()
    sql = "SELECT * FROM marketplace_assets WHERE tenant_id = " + _PH
    params: list = [tid]
    if kind:
        sql += f" AND kind = {_PH}"
        params.append(kind)
    if category:
        sql += f" AND category = {_PH}"
        params.append(category)
    sql += " ORDER BY asset_key, version DESC"
    rows = await fetch_all(sql, tuple(params))
    return {"assets": [await _asset_out(r, tid) for r in rows]}


@router.post("/catalog", status_code=201)
async def register_asset(
    body: AssetCreate,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    if body.kind not in ASSET_KINDS:
        raise HTTPException(422, f"kind must be one of {ASSET_KINDS}")
    tid = _tenant()
    dup = await fetch_one(
        f"SELECT id FROM marketplace_assets "
        f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (body.asset_key, body.version, tid),
    )
    if dup:
        raise HTTPException(409, f"asset {body.asset_key}@{body.version} already exists")
    await execute_insert(
        f"INSERT INTO marketplace_assets "
        f"(tenant_id, asset_key, version, kind, name, name_en, description, category, "
        f" min_platform_version, governance, required_env, checksum, source) "
        f"VALUES ({','.join([_PH] * 13)})",
        (
            tid, body.asset_key, body.version, body.kind, body.name, body.name_en,
            body.description, body.category, body.min_platform_version,
            body.governance, body.required_env, body.checksum, body.source,
        ),
    )
    asset = await fetch_one(
        f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (body.asset_key, body.version, tid),
    )
    return await _asset_out(asset, tid)


@router.get("/catalog/{asset_key}")
async def get_asset(asset_key: str, user: dict = Depends(get_current_user)):
    tid = _tenant()
    asset = await fetch_one(
        f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH} "
        f"ORDER BY version DESC LIMIT 1",
        (asset_key, tid),
    )
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")
    return await _asset_out(asset, tid)


@router.post("/install/{asset_key}", status_code=201)
async def install(
    asset_key: str,
    version: str | None = None,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    tid = _tenant()
    if version:
        asset = await fetch_one(
            f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (asset_key, version, tid),
        )
    else:
        asset = await fetch_one(
            f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH} "
            f"ORDER BY version DESC LIMIT 1",
            (asset_key, tid),
        )
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")

    installed_by = user.get("username") or user.get("sub") or ""
    try:
        # 1) 기존 활성 설치 비활성화 (단일 활성 버전)
        await execute_write(
            f"UPDATE marketplace_installs SET active = 0, status = 'rolled_back', "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1",
            (asset_key, tid),
        )
        # 2) hot-deploy seam: agent 유형만 tbl_agent_config upsert → 카탈로그/Orchestrator 노출
        cfg_key = None
        if asset["kind"] == "agent":
            cfg_key = asset["asset_key"]
            exists = await fetch_one(
                f"SELECT agent_key FROM tbl_agent_config WHERE agent_key = {_PH}", (cfg_key,)
            )
            if exists:
                await execute_write(
                    f"UPDATE tbl_agent_config SET agent_name = {_PH}, description = {_PH}, "
                    f"description_en = {_PH}, is_enabled = 1, nav_group = 'marketplace', "
                    f"updated_at = CURRENT_TIMESTAMP WHERE agent_key = {_PH}",
                    (asset["name"], asset["description"], asset["name_en"] or asset["name"], cfg_key),
                )
            else:
                await execute_write(
                    f"INSERT INTO tbl_agent_config "
                    f"(agent_key, agent_name, is_enabled, is_required, nav_group, description, description_en) "
                    f"VALUES ({_PH}, {_PH}, 1, 0, 'marketplace', {_PH}, {_PH})",
                    (cfg_key, asset["name"], asset["description"], asset["name_en"] or asset["name"]),
                )
        # 3) install 기록
        iid = await execute_insert(
            f"INSERT INTO marketplace_installs "
            f"(tenant_id, asset_key, version, status, active, installed_by, agent_config_key) "
            f"VALUES ({_PH}, {_PH}, {_PH}, 'installed', 1, {_PH}, {_PH})",
            (tid, asset["asset_key"], asset["version"], installed_by, cfg_key),
        )
    except Exception as exc:  # noqa: BLE001 — 부분 설치 방지: 실패 기록 후 500
        await execute_insert(
            f"INSERT INTO marketplace_installs "
            f"(tenant_id, asset_key, version, status, active, installed_by, error) "
            f"VALUES ({_PH}, {_PH}, {_PH}, 'failed', 0, {_PH}, {_PH})",
            (tid, asset["asset_key"], asset["version"], installed_by, str(exc)),
        )
        raise HTTPException(500, f"install failed (rolled back): {exc}") from exc

    # 4) 실 ZIP hot-deploy(§7.6) — 업로드된 ZIP 블롭이 있으면 addon upload 파이프라인 in-proc 재사용.
    #    없으면(대부분의 메타-only 자산) config upsert seam 까지만(무중단).
    deployed = False
    blob_row = await fetch_one(
        f"SELECT blob FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset["asset_key"], asset["version"], tid),
    )
    if blob_row and blob_row.get("blob"):
        from app.services.addon_deploy import deploy_zip
        try:
            res = await deploy_zip(bytes(blob_row["blob"]), asset["asset_key"], user)
            deployed = res.get("status_code") in (200, 201)
        except Exception:  # noqa: BLE001 — 배포 실패가 설치 기록을 무효화하지 않음(무중단)
            deployed = False

    return {
        "id": iid, "asset_key": asset["asset_key"], "version": asset["version"],
        "status": "installed", "active": True, "agent_config_key": cfg_key, "deployed": deployed,
    }


@router.post("/catalog/{asset_key}/zip", status_code=201)
async def upload_asset_zip(
    asset_key: str,
    version: str | None = None,
    file: UploadFile = File(...),
    user: dict = Depends(require_role("admin", "supervisor")),
):
    """등록된 로컬 자산에 addon ZIP 을 첨부(저장) — 이후 install 시 실 hot-deploy 됨(§7.6)."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "ZIP 파일만 허용됩니다")
    tid = _tenant()
    if version:
        asset = await fetch_one(
            f"SELECT asset_key, version FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (asset_key, version, tid),
        )
    else:
        asset = await fetch_one(
            f"SELECT asset_key, version FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH} "
            f"ORDER BY version DESC LIMIT 1",
            (asset_key, tid),
        )
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")
    raw = await file.read()
    checksum = hashlib.sha256(raw).hexdigest()
    await execute_write(
        f"DELETE FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset["asset_key"], asset["version"], tid),
    )
    await execute_insert(
        f"INSERT INTO marketplace_asset_blobs (tenant_id, asset_key, version, filename, checksum, blob, uploaded_by) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
        (tid, asset["asset_key"], asset["version"], file.filename, checksum, raw,
         user.get("username") or user.get("sub") or ""),
    )
    # 자산 메타의 checksum 동기화
    await execute_write(
        f"UPDATE marketplace_assets SET checksum = {_PH}, updated_at = CURRENT_TIMESTAMP "
        f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (checksum, asset["asset_key"], asset["version"], tid),
    )
    return {"asset_key": asset["asset_key"], "version": asset["version"], "checksum": checksum, "size": len(raw)}


@router.delete("/install/{asset_key}")
async def uninstall(
    asset_key: str,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    tid = _tenant()
    active = await fetch_one(
        f"SELECT id FROM marketplace_installs WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1",
        (asset_key, tid),
    )
    if not active:
        raise HTTPException(404, f"no active install for {asset_key}")
    await execute_write(
        f"UPDATE marketplace_installs SET active = 0, status = 'uninstalled', "
        f"updated_at = CURRENT_TIMESTAMP WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1",
        (asset_key, tid),
    )
    # agent config 비활성화 (marketplace 로 설치된 addon 만)
    await execute_write(
        f"UPDATE tbl_agent_config SET is_enabled = 0, updated_at = CURRENT_TIMESTAMP "
        f"WHERE agent_key = {_PH} AND nav_group = 'marketplace'",
        (asset_key,),
    )
    return {"uninstalled": asset_key}


@router.get("/installs")
async def list_installs(
    asset_key: str | None = None,
    user: dict = Depends(get_current_user),
):
    tid = _tenant()
    sql = "SELECT * FROM marketplace_installs WHERE tenant_id = " + _PH
    params: list = [tid]
    if asset_key:
        sql += f" AND asset_key = {_PH}"
        params.append(asset_key)
    sql += " ORDER BY id DESC"
    return {"installs": await fetch_all(sql, tuple(params))}
