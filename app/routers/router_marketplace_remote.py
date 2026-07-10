"""router_marketplace_remote (F-MP 확장, E1.5) — /api/marketplace-remote.

별도 운영되는 Marketplace-host(사내 온프렘 레지스트리 또는 SaaS)에 **클라이언트**로 접속해
원격 카탈로그를 검색하고, 자산을 다운로드·검증 후 로컬 카탈로그에 등록한다. PRD §7.3.

설정(config, §7.3.1): `marketplace_remote_enabled`(마스터 스위치), `marketplace_host_url`,
`marketplace_host_mode`(onprem|saas), `marketplace_api_key`(Bearer), `marketplace_tls_verify`,
`marketplace_sync_interval_sec`(캐시 TTL), `marketplace_install_verify_checksum`.

원격 HTTP 접근은 `_remote_get`/`_remote_download` 로 분리해 시험 시 monkeypatch 가능.
`install` 은 원격 ZIP 을 받아 SHA256 검증 후 **로컬 marketplace_assets 에 source='remote' 로 등록**한다.
실제 무중단 hot-deploy(ZIP→router 마운트) 연결은 §7.6 후속(이번 범위는 원격→로컬 카탈로그 편입까지).
"""
import hashlib
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, fetch_one

router = APIRouter(prefix="/api/marketplace-remote", tags=["marketplace-remote"])

# 카탈로그 캐시: {"at": epoch, "data": [...]} — sync_interval TTL
_catalog_cache: dict = {"at": 0.0, "data": None}


def _tenant() -> str:
    return settings.tenant_default_id or "default"


def _require_enabled() -> None:
    if not settings.marketplace_remote_enabled:
        raise HTTPException(409, "remote registry disabled (MARKETPLACE_REMOTE_ENABLED=false)")
    if not settings.marketplace_host_url:
        raise HTTPException(409, "MARKETPLACE_HOST_URL not configured")


def _headers() -> dict:
    h = {}
    if settings.marketplace_api_key:
        h["Authorization"] = f"Bearer {settings.marketplace_api_key}"
    if settings.marketplace_tenant_id:
        h["X-Tenant-Id"] = settings.marketplace_tenant_id
    return h


def _tls_kwargs() -> dict:
    """httpx TLS 옵션 — 사설 CA 번들(서버검증) + mTLS 클라이언트 인증서(§7.3.2)."""
    kw: dict = {}
    kw["verify"] = settings.marketplace_tls_ca_bundle or settings.marketplace_tls_verify
    if settings.marketplace_tls_client_cert:
        kw["cert"] = (
            (settings.marketplace_tls_client_cert, settings.marketplace_tls_client_key)
            if settings.marketplace_tls_client_key else settings.marketplace_tls_client_cert
        )
    return kw


async def _remote_get(path: str) -> dict:
    """원격 host 의 JSON 엔드포인트 GET. (시험 시 monkeypatch 지점)"""
    url = settings.marketplace_host_url.rstrip("/") + path
    async with httpx.AsyncClient(timeout=15.0, **_tls_kwargs()) as c:
        resp = await c.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def _remote_download(path: str) -> bytes:
    """원격 host 에서 자산 바이너리(ZIP/서명) 다운로드. (시험 시 monkeypatch 지점)"""
    url = settings.marketplace_host_url.rstrip("/") + path
    async with httpx.AsyncClient(timeout=60.0, **_tls_kwargs()) as c:
        resp = await c.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.content


@router.get("/ping")
async def ping(user: dict = Depends(get_current_user)):
    _require_enabled()
    try:
        data = await _remote_get("/ping")
    except Exception as exc:  # noqa: BLE001 — 연결 실패를 502 로 표면화
        raise HTTPException(502, f"remote host unreachable: {exc}") from exc
    return {"ok": True, "mode": settings.marketplace_host_mode, "host": settings.marketplace_host_url, "remote": data}


@router.get("/catalog")
async def remote_catalog(refresh: bool = False, user: dict = Depends(get_current_user)):
    _require_enabled()
    now = time.time()
    ttl = settings.marketplace_sync_interval_sec
    if not refresh and _catalog_cache["data"] is not None and (now - _catalog_cache["at"]) < ttl:
        return {"assets": _catalog_cache["data"], "cached": True}
    try:
        data = await _remote_get("/catalog")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"remote catalog fetch failed: {exc}") from exc
    assets = data.get("assets", data) if isinstance(data, dict) else data
    _catalog_cache["data"] = assets
    _catalog_cache["at"] = now
    return {"assets": assets, "cached": False}


@router.get("/catalog/{asset_key}")
async def remote_asset(asset_key: str, user: dict = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _remote_get(f"/catalog/{asset_key}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"remote asset fetch failed: {exc}") from exc


class RemoteInstallBody(BaseModel):
    version: str | None = None
    expected_checksum: str | None = Field(default=None, description="원격 메타의 SHA256 (미제공 시 원격 상세에서 조회)")
    hot_deploy: bool = Field(default=True, description="검증 통과 시 다운로드 ZIP 을 addon upload 파이프라인으로 무중단 배포(§7.6)")


async def _hot_deploy(blob: bytes, asset_key: str, user: dict) -> dict:
    """공용 배포 헬퍼 위임(§7.6). 별도 재구현 금지 — services/addon_deploy 사용."""
    from app.services.addon_deploy import deploy_zip
    return await deploy_zip(blob, asset_key, user)


@router.post("/install/{asset_key}", status_code=201)
async def remote_install(
    asset_key: str, body: RemoteInstallBody, user: dict = Depends(require_role("admin", "supervisor"))
):
    _require_enabled()
    # 1) 원격 자산 상세 조회(메타·체크섬·다운로드 경로)
    try:
        meta = await _remote_get(f"/catalog/{asset_key}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"remote asset fetch failed: {exc}") from exc
    version = body.version or meta.get("version") or "0.1.0"
    download_path = meta.get("download_path") or f"/download/{asset_key}"
    expected = body.expected_checksum or meta.get("checksum") or ""

    # 2) ZIP 다운로드 + SHA256 검증(강제 옵션)
    try:
        blob = await _remote_download(download_path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"remote download failed: {exc}") from exc
    actual = hashlib.sha256(blob).hexdigest()
    if settings.marketplace_install_verify_checksum:
        if not expected:
            raise HTTPException(422, "checksum verification required but no expected checksum available")
        if actual != expected:
            raise HTTPException(422, f"checksum mismatch (expected {expected[:12]}…, got {actual[:12]}…)")
    # 2b) GPG detached 서명 검증(엔터프라이즈 옵션, §7.3) — `.sig` 다운로드 후 공개키로 검증
    if settings.marketplace_install_require_signature:
        from app.services.signature import load_pubkey, verify_detached
        pubkey = load_pubkey(settings.marketplace_gpg_pubkey_path)
        if not pubkey:
            raise HTTPException(422, "signature required but MARKETPLACE_GPG_PUBKEY_PATH not configured/readable")
        sig_path = meta.get("signature_path") or f"{download_path}.sig"
        try:
            sig = await _remote_download(sig_path)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(422, f"signature download failed: {exc}") from exc
        if not verify_detached(blob, sig, pubkey):
            raise HTTPException(422, "GPG signature verification failed")

    # 3) 실 addon ZIP hot-deploy(§7.6) — 검증 통과분을 기존 upload 파이프라인에 in-process 재사용.
    #    유효 addon ZIP 이 아니면(예: rag-pipeline) 실패 흡수하고 catalog 편입만 진행.
    deploy_result: dict | None = None
    if body.hot_deploy:
        try:
            deploy_result = await _hot_deploy(blob, asset_key, user)
        except Exception as exc:  # noqa: BLE001 — 배포 실패가 catalog 편입을 막지 않음
            deploy_result = {"status_code": 0, "body": f"hot-deploy skipped: {exc}"}

    # 4) 로컬 marketplace_assets 편입(source='remote')
    tid = _tenant()
    dup = await fetch_one(
        f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset_key, version, tid),
    )
    if dup:
        raise HTTPException(409, f"asset {asset_key}@{version} already in local catalog")
    # R18-7: 원격 메타의 description/display_name 도 다국어 dict 허용 — 공통함수로 정규화해
    # names/descriptions JSON 으로 저장 (raw dict repr 저장 방지, 언어 확장 시 데이터만 추가)
    from app.core.i18n import lang_json, norm_descriptions
    _m = norm_descriptions(dict(meta))
    _names = _m.get("agent_names") or {}
    await execute_insert(
        f"INSERT INTO marketplace_assets "
        f"(tenant_id, asset_key, version, kind, name, name_en, description, names, descriptions, category, checksum, source) "
        f"VALUES ({','.join([_PH] * 12)})",
        (tid, asset_key, version, meta.get("kind", "agent"),
         _names.get("ko") or meta.get("name") or asset_key,
         _names.get("en") or meta.get("name_en") or "",
         _m.get("description", ""), lang_json(_names), lang_json(_m.get("descriptions")),
         meta.get("category", "general"), actual, "remote"),
    )
    asset = await fetch_one(
        f"SELECT * FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
        (asset_key, version, tid),
    )
    deployed = bool(deploy_result and deploy_result.get("status_code") in (200, 201))
    return {"registered": True, "deployed": deployed, "checksum": actual, "asset": asset, "deploy_result": deploy_result}
