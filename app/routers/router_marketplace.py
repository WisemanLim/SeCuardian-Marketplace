"""router_marketplace (F-MP) — /api/marketplace.

카탈로그 등록·조회·상세 + 설치 트랜잭션(단일 활성 버전)·해제. SeCuardian Path A 준용.
설치 = hot-deploy seam: install 기록 + tbl_agent_config upsert(카탈로그/Orchestrator 자동 노출).
addon(ZIP) 자산의 실제 무중단 마운트는 기존 router_addon_agent upload 파이프라인을 재사용한다
(1차: config upsert seam. addon-loader 배선은 §7.6 후속).

참조: SeCuardian-Marketplace-v0 router/service/model 을 raw-SQL 아키텍처로 이식.
설치/해제·등록은 admin 이상(require_role). tenant 는 JWT 미포함이라 TENANT_DEFAULT_ID 사용.
"""
import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.core.i18n import lang_json, norm_descriptions, parse_lang_map
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

ASSET_KINDS = ("agent", "workflow", "rag-pipeline", "tool-proxy")


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class AssetCreate(BaseModel):
    # §7.6.2: asset_key 미지정 시 name 슬러그로 서버 자동부여 (지정 시 기존 동작)
    asset_key: str = Field(default="", max_length=64)
    version: str = Field(default="0.1.0", max_length=32)
    kind: str = Field(default="agent")
    name: str = Field(min_length=1, max_length=128)
    name_en: str = Field(default="", max_length=128)
    description: str = ""
    description_en: str = ""
    # §7.11.2-5: 다국어 dict 직접 지정 ({"ko":…, "en":…, "jp":…}) — 지정 시 위 레거시 필드보다 우선.
    # 저장은 항상 dict(JSON) — 언어 확장 시 코드 수정 없이 데이터만 추가.
    names: dict[str, str] | None = None
    descriptions: dict[str, str] | None = None
    category: str = Field(default="general", max_length=64)
    min_platform_version: str = Field(default="0.1.0", max_length=32)
    governance: str = ""
    required_env: str = ""
    checksum: str = ""
    source: str = Field(default="local")


def _slugify(name: str) -> str:
    """name → asset_key 슬러그 (소문자·영숫자·하이픈, §7.6.2). 비ASCII 만이면 'asset'."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug[:64] or "asset"


async def _unique_asset_key(name: str, tenant_id: str) -> str:
    """슬러그 충돌 시 -2, -3 … 접미로 유일 키 자동부여."""
    base = _slugify(name)
    key = base
    n = 2
    while await fetch_one(
        f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH}",
        (key, tenant_id),
    ):
        key = f"{base[: 64 - len(str(n)) - 1]}-{n}"
        n += 1
    return key


async def _active_version(asset_key: str, tenant_id: str) -> str | None:
    row = await fetch_one(
        f"SELECT version FROM marketplace_installs "
        f"WHERE asset_key = {_PH} AND tenant_id = {_PH} AND active = 1 "
        f"ORDER BY id DESC LIMIT 1",
        (asset_key, tenant_id),
    )
    return row["version"] if row else None


_MARKET_ASSETS_DIR = Path("marketplace-assets")


# §7.6.6 v0.47: 시드 보호 = seed_assets 대상 디렉터리만 — addon(스캐폴드)·builtin 유래
# 사용자 등록 자산은 삭제 가능해야 하므로 보호 범위에서 제외한다.
_SEED_CATEGORIES = ("security", "utilities")


def _seed_category(asset_key: str) -> str | None:
    """시드 카탈로그 디렉터리(`marketplace-assets/{security,utilities}/{key}.zip`, 대소문자 무시)
    보유 시 해당 카테고리명 반환 — 시드 보호 자산 판별(§7.6.6 v0.47)."""
    key = asset_key.lower()
    for cat_name in _SEED_CATEGORIES:
        cat = _MARKET_ASSETS_DIR / cat_name
        if not cat.is_dir():
            continue
        for z in cat.glob("*.zip"):
            if z.stem.lower() == key:
                return cat_name
    return None


def _disk_backed(asset_key: str) -> bool:
    """시드 보호 자산 여부 — 시드(security/utilities) 보유 자산은 삭제 불가
    (seed 재실행 시 재등장하므로 삭제가 무의미 + 기본 제공 보호)."""
    return _seed_category(asset_key) is not None


async def _asset_out(asset: dict, tenant_id: str) -> dict:
    ver = await _active_version(asset["asset_key"], tenant_id)
    return {
        **asset, "installed": ver is not None, "active_version": ver,
        # §7.6.6: 사용자 등록 자산(디스크 미보유)만 삭제 가능
        "deletable": not _disk_backed(asset["asset_key"]),
    }


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
    asset_key = body.asset_key.strip()
    if asset_key:
        dup = await fetch_one(
            f"SELECT id FROM marketplace_assets "
            f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (asset_key, body.version, tid),
        )
        if dup:
            raise HTTPException(409, f"asset {asset_key}@{body.version} already exists")
    else:
        # §7.6.2: asset_key 자동부여 — name 슬러그 + 충돌 접미
        asset_key = await _unique_asset_key(body.name, tid)
    # §7.11.2-5: 모든 입력(dict 형·레거시 필드)을 공통함수로 정규화 → names/descriptions JSON 저자
    _m = norm_descriptions({
        "display_name": body.names or {"ko": body.name, "en": body.name_en},
        "description": body.descriptions or {"ko": body.description, "en": body.description_en},
    })
    await execute_insert(
        f"INSERT INTO marketplace_assets "
        f"(tenant_id, asset_key, version, kind, name, name_en, description, names, descriptions, category, "
        f" min_platform_version, governance, required_env, checksum, source) "
        f"VALUES ({','.join([_PH] * 15)})",
        (
            tid, asset_key, body.version, body.kind,
            _m["agent_names"].get("ko") or body.name, _m["agent_names"].get("en", ""),
            _m["description"], lang_json(_m["agent_names"]), lang_json(_m["descriptions"]),
            body.category, body.min_platform_version,
            body.governance, body.required_env, body.checksum, body.source,
        ),
    )
    asset = await fetch_one(
        f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset_key, body.version, tid),
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


def _install_conflict_detail(asset_key: str, reason: str, extra: str, extra_en: str) -> dict:
    """설치 중복 409 상세 — 프론트가 code 로 분기하고 message/message_en 을 노출 (R22-7).

    확인(force=true) 후에는 진행 가능하므로 overwritable=true.
    """
    return {
        "code": "install_conflict",
        "asset_key": asset_key,
        "reason": reason,
        "overwritable": True,
        "message": f"'{asset_key}' {extra} 계속하면 이 자산으로 덮어씁니다.",
        "message_en": f"'{asset_key}' {extra_en} Continuing overwrites it with this asset.",
    }


async def _check_install_conflict(asset: dict, tid: str, force: bool) -> None:
    """설치 전 중복 확인 (R22-7) — 확인 없는 조용한 덮어쓰기 금지.

    ① 마켓플레이스 출처가 아닌 `tbl_agent_config` 키 점유(내장·타출처 에이전트)
    ② 동일 버전이 이미 활성 설치됨
    """
    if force:
        return
    asset_key = asset["asset_key"]
    if asset["kind"] == "agent":
        cfg = await fetch_one(
            f"SELECT agent_key, nav_group FROM tbl_agent_config WHERE agent_key = {_PH}",
            (asset_key.lower(),),
        )
        if cfg and (cfg.get("nav_group") or "") != "marketplace":
            raise HTTPException(409, _install_conflict_detail(
                asset_key, "agent_config_occupied",
                "는 마켓플레이스 설치본이 아닌 기존(내장) 에이전트로 이미 등록되어 있습니다.",
                "is already registered as an existing (built-in) agent, not a marketplace install.",
            ))
    active = await fetch_one(
        f"SELECT id FROM marketplace_installs WHERE asset_key = {_PH} AND version = {_PH} "
        f"AND tenant_id = {_PH} AND active = 1",
        (asset_key, asset["version"], tid),
    )
    if active:
        raise HTTPException(409, _install_conflict_detail(
            asset_key, "already_installed",
            f"{asset['version']} 은 이미 설치(활성)되어 있습니다.",
            f"{asset['version']} is already installed and active.",
        ))


@router.post("/install/{asset_key}", status_code=201)
async def install(
    asset_key: str,
    version: str | None = None,
    force: bool = False,   # R22-7: 중복은 사용자 확인 후에만 덮어쓰기
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

    await _check_install_conflict(asset, tid, force)

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
        #    §7.11.2-5: descriptions/agent_names 를 JSON(다국어 확장형)으로 저자.
        cfg_key = None
        if asset["kind"] == "agent":
            # §7.6.5: addon 업로드 파이프라인이 zip 스템을 소문자화하므로 config 키도 소문자로
            # 통일 — 대소문자 혼용 시 tbl_agent_config 에 동일 에이전트가 2행(중복 카드) 생기는 결함 방지.
            cfg_key = asset["asset_key"].lower()
            # §7.11.2-5: 자산의 names/descriptions JSON(dict) 그대로 전파 — 레거시 컬럼은 폴백만
            _descs = parse_lang_map(asset.get("descriptions"))
            if not _descs and asset.get("description"):
                _descs = {"ko": asset["description"]}
            _names = parse_lang_map(asset.get("names"))
            if not _names:
                _names = {"ko": asset["name"]}
                if asset.get("name_en"):
                    _names["en"] = asset["name_en"]
            descriptions = lang_json(_descs)
            agent_names = lang_json(_names)
            exists = await fetch_one(
                f"SELECT agent_key FROM tbl_agent_config WHERE agent_key = {_PH}", (cfg_key,)
            )
            if exists:
                await execute_write(
                    f"UPDATE tbl_agent_config SET agent_name = {_PH}, description = {_PH}, "
                    f"descriptions = {_PH}, agent_names = {_PH}, is_enabled = 1, nav_group = 'marketplace', "
                    f"updated_at = CURRENT_TIMESTAMP WHERE agent_key = {_PH}",
                    (asset["name"], asset["description"], descriptions, agent_names, cfg_key),
                )
            else:
                await execute_write(
                    f"INSERT INTO tbl_agent_config "
                    f"(agent_key, agent_name, is_enabled, is_required, nav_group, description, descriptions, agent_names) "
                    f"VALUES ({_PH}, {_PH}, 1, 0, 'marketplace', {_PH}, {_PH}, {_PH})",
                    (cfg_key, asset["name"], asset["description"], descriptions, agent_names),
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


# ── §7.6.6: 사용자 등록 자산·카탈로그(카테고리) 삭제 ─────────────────────────

async def _delete_asset_rows(asset_key: str, tid: str) -> None:
    """자산 삭제 공용 — assets(전 버전)·blobs·installs 이력·marketplace config 행 정리."""
    await execute_write(
        f"DELETE FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND tenant_id = {_PH}",
        (asset_key, tid),
    )
    await execute_write(
        f"DELETE FROM marketplace_installs WHERE asset_key = {_PH} AND tenant_id = {_PH}",
        (asset_key, tid),
    )
    await execute_write(
        f"DELETE FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH}",
        (asset_key, tid),
    )
    # marketplace 설치가 만든 config 행 정리 (LOWER — upload 파이프라인 소문자화 대응)
    await execute_write(
        f"DELETE FROM tbl_agent_config WHERE LOWER(agent_key) = LOWER({_PH}) AND nav_group = 'marketplace'",
        (asset_key,),
    )


async def _assert_deletable(asset_key: str, tid: str) -> None:
    """삭제 가능 검증 — 존재·디스크 비보유·활성 설치 없음 (§7.6.6)."""
    asset = await fetch_one(
        f"SELECT asset_key FROM marketplace_assets WHERE asset_key = {_PH} AND tenant_id = {_PH} LIMIT 1",
        (asset_key, tid),
    )
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")
    if _disk_backed(asset_key):
        raise HTTPException(403, f"{asset_key}: 기본 제공 자산(marketplace-assets 보유)은 삭제할 수 없습니다")
    if await _active_version(asset_key, tid):
        raise HTTPException(409, f"{asset_key}: 설치된 자산입니다 — 먼저 해제하세요")


@router.delete("/catalog/{asset_key}")
async def delete_asset(
    asset_key: str,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    """사용자 등록 자산 삭제 — 디스크 미보유(deletable)·비설치 자산만 (§7.6.6)."""
    tid = _tenant()
    await _assert_deletable(asset_key, tid)
    await _delete_asset_rows(asset_key, tid)
    return {"deleted": asset_key}


@router.delete("/catalog-category/{category}")
async def delete_category(
    category: str,
    user: dict = Depends(require_role("admin", "supervisor")),
):
    """사용자 카탈로그(카테고리) 일괄 삭제 (§7.6.6 v0.47).

    설치 중 자산만 차단(409). 시드 보호 자산(security/utilities 디스크 보유)이
    사용자 카탈로그로 이동돼 있으면 삭제 대신 원 시드 카탈로그로 반환한다 —
    사용자가 만든 카탈로그는 항상 삭제 가능. 시드 카탈로그 자체에 시드 자산이
    남아 있으면 409(기본 제공 카탈로그 보호).
    """
    tid = _tenant()
    rows = await fetch_all(
        f"SELECT DISTINCT asset_key FROM marketplace_assets WHERE category = {_PH} AND tenant_id = {_PH}",
        (category, tid),
    )
    if not rows:
        raise HTTPException(404, f"category {category} not found")
    keys = [r["asset_key"] for r in rows]
    blockers: list[str] = []
    for k in keys:
        if await _active_version(k, tid):
            blockers.append(f"{k}(설치됨)")
        elif _seed_category(k) == category:
            blockers.append(f"{k}(기본 제공)")
    if blockers:
        raise HTTPException(409, f"삭제 불가 자산 존재: {', '.join(blockers)}")
    deleted: list[str] = []
    returned: list[str] = []
    for k in keys:
        seed_cat = _seed_category(k)
        if seed_cat:
            # 시드 보호 자산 — 삭제 대신 원 시드 카탈로그로 반환
            await execute_write(
                f"UPDATE marketplace_assets SET category = {_PH}, updated_at = CURRENT_TIMESTAMP "
                f"WHERE asset_key = {_PH} AND tenant_id = {_PH}",
                (seed_cat, k, tid),
            )
            returned.append(k)
        else:
            await _delete_asset_rows(k, tid)
            deleted.append(k)
    return {"deleted_category": category, "deleted_assets": deleted, "returned_assets": returned}


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


def _parse_zip_meta(raw: bytes, filename: str) -> dict:
    """ZIP 내 {key}-meta.json 파싱 → asset_key/name/version/description 추출 (§7.6.2).

    meta 미존재 시 파일명 스템({key}.zip → key)으로 폴백.
    R18-7: description/display_name 은 다국어 dict 형({"ko":…, "en":…, …})·레거시 문자열 모두 허용 —
    공통함수 norm_descriptions 로 정규화해 raw dict repr 이 카탈로그에 저장되던 결함을 방지.
    """
    stem = re.sub(r"\.zip$", "", filename)
    meta: dict = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = sorted(
            (n for n in zf.namelist() if n.endswith("-meta.json")),
            key=lambda n: n.count("/"),
        )
        if names:
            meta = json.loads(zf.read(names[0]).decode("utf-8"))
    meta = norm_descriptions(meta)
    key = _slugify(str(meta.get("agent_key") or meta.get("key") or stem))
    agent_names = meta.get("agent_names") or {}
    return {
        "asset_key": key,
        "name": str(agent_names.get("ko") or meta.get("name") or key),
        "name_en": str(agent_names.get("en") or meta.get("name_en") or ""),
        "names": agent_names,
        "descriptions": meta.get("descriptions") or {},
        "version": str(meta.get("version") or "1.0.0"),
        "description": str(meta.get("description") or ""),
    }


@router.post("/catalog/zip", status_code=201)
async def register_assets_from_zips(
    files: list[UploadFile] = File(...),
    category: str = "general",
    confirm: bool = False,
    name: str = Form(""),
    name_en: str = Form(""),
    description: str = Form(""),
    description_en: str = Form(""),
    kind: str = Form(""),
    user: dict = Depends(require_role("admin", "supervisor")),
):
    """§7.6.2: ZIP 다중 등록 — 각 ZIP 의 {key}-meta.json 기반 자산 등록 + 블롭 저장(멱등).

    동일 key@version 존재 시 메타·블롭 갱신(요청 category 로 이동 포함).
    §7.6.6: 단일 ZIP + 폼 name 입력 시 폼 값(name/description/kind)이 ZIP meta 를 덮어씀 —
    등록 모달의 필수 입력이 실제 카탈로그 표기에 반영되도록 한다.
    §7.6.6 v0.47: 기존 등록 asset_key 포함 시 confirm 없이는 409
    {"code":"duplicate","assets":[…]} — 사용자가 확인(confirm=true)하면 요청 카탈로그로 이동 등록.
    설치 시 기존 hot-deploy 계약 그대로.
    """
    tid = _tenant()
    uploader = user.get("username") or user.get("sub") or ""
    entries: list[tuple[str, bytes, dict]] = []
    for f in files:
        if not f.filename or not f.filename.endswith(".zip"):
            raise HTTPException(400, f"ZIP 파일만 허용됩니다: {f.filename}")
        raw = await f.read()
        try:
            meta = _parse_zip_meta(raw, f.filename)
        except (zipfile.BadZipFile, ValueError, KeyError) as exc:
            raise HTTPException(400, f"{f.filename}: ZIP 파싱 실패 — {exc}") from exc
        if len(files) == 1 and name.strip():
            _m = norm_descriptions({
                "display_name": {"ko": name.strip(), "en": name_en.strip()},
                "description": {"ko": description.strip(), "en": description_en.strip()},
            })
            meta.update(
                name=_m["agent_names"].get("ko") or name.strip(),
                name_en=_m["agent_names"].get("en", ""),
                names=_m["agent_names"],
                description=_m["description"],
                descriptions=_m["descriptions"],
            )
        entries.append((f.filename, raw, meta))
    if not confirm:
        # §7.6.6 v0.47: 중복 pre-check — 이미 등록된 key 는 사용자 확인 후에만 재등록(이동)
        dups: list[dict] = []
        for _, _, meta in entries:
            row = await fetch_one(
                f"SELECT name, category FROM marketplace_assets "
                f"WHERE asset_key = {_PH} AND tenant_id = {_PH} ORDER BY version DESC LIMIT 1",
                (meta["asset_key"], tid),
            )
            if row:
                dups.append({"asset_key": meta["asset_key"],
                             "name": row["name"], "category": row["category"]})
        if dups:
            raise HTTPException(409, {"code": "duplicate", "assets": dups})
    asset_kind = kind if (len(files) == 1 and kind in ASSET_KINDS) else "agent"
    out: list[dict] = []
    for filename, raw, meta in entries:
        checksum = hashlib.sha256(raw).hexdigest()
        exists = await fetch_one(
            f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (meta["asset_key"], meta["version"], tid),
        )
        if exists:
            # 요청 category 반영 — 기존 key@version 재등록 시 지정 카탈로그로 이동
            await execute_write(
                f"UPDATE marketplace_assets SET name = {_PH}, name_en = {_PH}, description = {_PH}, "
                f"names = {_PH}, descriptions = {_PH}, category = {_PH}, checksum = {_PH}, "
                f"updated_at = CURRENT_TIMESTAMP "
                f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
                (meta["name"], meta["name_en"], meta["description"],
                 lang_json(meta["names"]), lang_json(meta["descriptions"]),
                 category, checksum, meta["asset_key"], meta["version"], tid),
            )
        else:
            await execute_insert(
                f"INSERT INTO marketplace_assets "
                f"(tenant_id, asset_key, version, kind, name, name_en, description, names, descriptions, category, "
                f" min_platform_version, governance, required_env, checksum, source) "
                f"VALUES ({','.join([_PH] * 15)})",
                (tid, meta["asset_key"], meta["version"], asset_kind, meta["name"], meta["name_en"],
                 meta["description"], lang_json(meta["names"]), lang_json(meta["descriptions"]),
                 category, "0.1.0", "", "", checksum, "local"),
            )
        await execute_write(
            f"DELETE FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (meta["asset_key"], meta["version"], tid),
        )
        await execute_insert(
            f"INSERT INTO marketplace_asset_blobs (tenant_id, asset_key, version, filename, checksum, blob, uploaded_by) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
            (tid, meta["asset_key"], meta["version"], filename, checksum, raw, uploader),
        )
        asset = await fetch_one(
            f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (meta["asset_key"], meta["version"], tid),
        )
        out.append(await _asset_out(asset, tid))
    return {"assets": out}


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
    # agent config 비활성화 (marketplace 로 설치된 addon 만) — 키 대소문자 혼용 이력 방어(LOWER)
    await execute_write(
        f"UPDATE tbl_agent_config SET is_enabled = 0, updated_at = CURRENT_TIMESTAMP "
        f"WHERE LOWER(agent_key) = LOWER({_PH}) AND nav_group = 'marketplace'",
        (asset_key,),
    )
    # §7.6.5: hot-deploy 산출물 완전 정리 — addon 행(대소문자 무시)·deployed 디렉터리·front tsx·MCP.
    # upload 파이프라인이 키를 소문자화할 수 있어 LOWER 매칭. config 행은 유지(재설치 대비).
    from app.routers.router_addon_agent import _DEPLOYED, _remove_addon_artifacts
    undeployed = False
    addon = await fetch_one(
        f"SELECT agent_key, sql_path FROM tbl_addon_agents WHERE LOWER(agent_key) = LOWER({_PH})",
        (asset_key,),
    )
    if addon:
        await _remove_addon_artifacts(addon["agent_key"], addon.get("sql_path") or "", delete_config=False)
        undeployed = True
    else:
        # 행 없이 남은 고아 배포 디렉터리 방어적 제거
        leftover = _DEPLOYED / asset_key
        if leftover.exists():
            shutil.rmtree(leftover)
            undeployed = True
    return {"uninstalled": asset_key, "undeployed": undeployed}


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
