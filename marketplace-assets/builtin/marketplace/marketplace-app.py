"""마켓플레이스 에이전트 — ADDON 판 (marketplace).

내장 라우터 app/routers/router_marketplace.py (F-MP) 의 ADDON 패키징.
로더가 /api/addon/marketplace prefix 로 마운트한다.
설정은 내장판(settings.*) 대신 환경변수로 주입한다.
DB 없이 인메모리 저장소(deque)로 동작 — 마켓플레이스 카탈로그·설치 이력 조회·등록 가능.
"""
import datetime
import os
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["marketplace"])

MARKETPLACE_ENABLED = os.getenv("MARKETPLACE_ENABLED", "true").lower() == "true"
MARKETPLACE_MAX_ASSETS = int(os.getenv("MARKETPLACE_MAX_ASSETS", "200"))

ASSET_KINDS = ("agent", "workflow", "rag-pipeline", "tool-proxy")

# 인메모리 저장소
_assets: deque[dict] = deque(maxlen=MARKETPLACE_MAX_ASSETS)
_installs: deque[dict] = deque(maxlen=500)
_next_id: list[int] = [1]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _next() -> int:
    v = _next_id[0]
    _next_id[0] += 1
    return v


class AssetCreate(BaseModel):
    asset_key: str = Field(min_length=1, max_length=64)
    version: str = Field(default="0.1.0", max_length=32)
    kind: str = Field(default="agent")
    name: str = Field(min_length=1, max_length=128)
    name_en: str = Field(default="", max_length=128)
    description: str = ""
    category: str = Field(default="general", max_length=64)
    source: str = Field(default="local")


def _asset_with_install(asset: dict) -> dict:
    install = next(
        (i for i in reversed(list(_installs))
         if i["asset_key"] == asset["asset_key"] and i.get("active")),
        None,
    )
    return {
        **asset,
        "installed": install is not None,
        "active_version": install["version"] if install else None,
    }


@router.get("/status")
async def marketplace_status(_: dict = Depends(get_current_user)):
    """마켓플레이스 에이전트 상태."""
    return {
        "marketplace_enabled": MARKETPLACE_ENABLED,
        "assets_stored": len(_assets),
        "installs_stored": len(_installs),
        "asset_kinds": ASSET_KINDS,
        "source": "marketplace (in-memory ADDON)",
    }


@router.get("/catalog")
async def list_catalog(
    kind: str = Query(None),
    category: str = Query(None),
    _: dict = Depends(get_current_user),
):
    """마켓플레이스 카탈로그 목록 (kind·category 필터 가능)."""
    items = list(_assets)
    if kind:
        items = [a for a in items if a.get("kind") == kind]
    if category:
        items = [a for a in items if a.get("category") == category]
    return {"assets": [_asset_with_install(a) for a in items]}


@router.get("/catalog/{asset_key}")
async def get_asset(asset_key: str, _: dict = Depends(get_current_user)):
    """특정 자산 상세 조회 (최신 버전 우선)."""
    asset = next((a for a in reversed(list(_assets)) if a["asset_key"] == asset_key), None)
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")
    return _asset_with_install(asset)


@router.post("/catalog", status_code=201)
async def register_asset(body: AssetCreate, _: dict = Depends(get_current_user)):
    """카탈로그에 자산 등록 (인메모리)."""
    if body.kind not in ASSET_KINDS:
        raise HTTPException(422, f"kind must be one of {ASSET_KINDS}")
    dup = next(
        (a for a in _assets if a["asset_key"] == body.asset_key and a["version"] == body.version),
        None,
    )
    if dup:
        raise HTTPException(409, f"asset {body.asset_key}@{body.version} already exists")
    asset = {
        "id": _next(),
        "asset_key": body.asset_key,
        "version": body.version,
        "kind": body.kind,
        "name": body.name,
        "name_en": body.name_en,
        "description": body.description,
        "category": body.category,
        "source": body.source,
        "created_at": _now(),
    }
    _assets.append(asset)
    return _asset_with_install(asset)


@router.post("/install/{asset_key}", status_code=201)
async def install(
    asset_key: str,
    version: str = Query(None),
    _: dict = Depends(get_current_user),
):
    """자산 설치 — 기존 활성 버전을 비활성화하고 신규 설치 기록."""
    if version:
        asset = next((a for a in _assets if a["asset_key"] == asset_key and a["version"] == version), None)
    else:
        asset = next((a for a in reversed(list(_assets)) if a["asset_key"] == asset_key), None)
    if not asset:
        raise HTTPException(404, f"asset {asset_key} not found")
    # 기존 활성 설치 비활성화
    for i in _installs:
        if i["asset_key"] == asset_key and i.get("active"):
            i["active"] = False
            i["status"] = "rolled_back"
    iid = _next()
    _installs.append({
        "id": iid,
        "asset_key": asset_key,
        "version": asset["version"],
        "status": "installed",
        "active": True,
        "installed_at": _now(),
    })
    return {"id": iid, "asset_key": asset_key, "version": asset["version"], "status": "installed", "active": True}


@router.delete("/install/{asset_key}")
async def uninstall(asset_key: str, _: dict = Depends(get_current_user)):
    """활성 설치 해제."""
    install = next(
        (i for i in reversed(list(_installs)) if i["asset_key"] == asset_key and i.get("active")),
        None,
    )
    if not install:
        raise HTTPException(404, f"no active install for {asset_key}")
    install["active"] = False
    install["status"] = "uninstalled"
    return {"uninstalled": asset_key}


@router.get("/installs")
async def list_installs(
    asset_key: str = Query(None),
    _: dict = Depends(get_current_user),
):
    """설치 이력 조회."""
    items = list(_installs)
    if asset_key:
        items = [i for i in items if i["asset_key"] == asset_key]
    return {"installs": list(reversed(items))}
