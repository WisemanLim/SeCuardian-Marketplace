"""router_marketplace_host (§7.3.5) — /api/marketplace-host.

SeCMP 를 **host(레지스트리 서버)** 로서 외부 SeCuardian 인스턴스에 공개하는 카탈로그 API.
소스 = `marketplace-assets/{category}/{Name}.zip` 파일시스템 전량 — DB 설치 여부
(marketplace_installs/tbl_addon_agents)와 무관하게 제공 자산 전부를 카테고리별로 노출한다
(레지스트리 계약, 클라이언트 측은 SeCuardian PRD §21 / 본 저장소 §7.3 remote 클라이언트).

인증: `MARKETPLACE_HOST_API_KEY` 설정 시 `Authorization: Bearer <키>` 필수(불일치 401),
미설정 시 개방(폐쇄망 온프렘 기본) — 운영(staging/prod)은 키 설정 권장.
`checksum`(ZIP SHA256, mtime 캐시)·`download_path` 는 §7.3.3 원격 클라이언트 계약과 호환.
"""
import hashlib
import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.i18n import norm_descriptions

router = APIRouter(prefix="/api/marketplace-host", tags=["marketplace-host"])

_ASSETS = Path("marketplace-assets")
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

# ZIP SHA256 캐시 — {path: (mtime, sha256)} : 카탈로그 조회마다 재해시 방지
_checksum_cache: dict[str, tuple[float, str]] = {}


def _require_host_key(authorization: str = Header(default="")) -> None:
    key = settings.marketplace_host_api_key
    if not key:
        return
    token = authorization.removeprefix("Bearer ").strip()
    if token != key:
        raise HTTPException(status_code=401, detail="invalid marketplace host api key")


def _checksum(zip_path: Path) -> str:
    mtime = zip_path.stat().st_mtime
    cached = _checksum_cache.get(str(zip_path))
    if cached and cached[0] == mtime:
        return cached[1]
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    _checksum_cache[str(zip_path)] = (mtime, digest)
    return digest


def _read_meta(category_dir: Path, stem: str) -> dict:
    """자산 디렉터리의 {stem}-meta.json 파싱 (다국어 dict 정규화, §7.11.2-5)."""
    meta_file = category_dir / stem / f"{stem}-meta.json"
    if not meta_file.exists():
        return norm_descriptions({})
    try:
        return norm_descriptions(json.loads(meta_file.read_text(encoding="utf-8")))
    except Exception:
        return norm_descriptions({})


def _asset_entry(category_dir: Path, zip_path: Path) -> dict:
    stem = zip_path.stem
    meta = _read_meta(category_dir, stem)
    names = meta.get("agent_names") or {}
    return {
        "asset_key": stem,
        "name": names.get("ko") or stem,
        "name_en": names.get("en", ""),
        "names": names,
        "description": meta.get("description", ""),
        "descriptions": meta.get("descriptions") or {},
        "version": str(meta.get("version") or "1.0.0"),
        # R22-4(SeCuardian PRD §22): {Name}_worker.zip 은 다운로드 전용 worker 자산
        "kind": "worker" if stem.endswith("_worker") else "agent",
        # R22-4: worker 자산이 지원하는 짝 에이전트 asset_key — 클라이언트가 worker 카드에서
        # 에이전트를 바로 배포할 수 있도록 노출 (meta 미기재 시 빈 문자열)
        "agent_key": str(meta.get("agent_key") or ""),
        "agent_type": meta.get("agent_type", "app"),
        "category": category_dir.name,
        "size": zip_path.stat().st_size,
        "checksum": _checksum(zip_path),
        "download_path": f"/download/{stem}",
    }


def _category_dirs() -> list[Path]:
    if not _ASSETS.exists():
        return []
    return sorted(
        (d for d in _ASSETS.iterdir() if d.is_dir() and not d.name.startswith(".")),
        key=lambda d: d.name,
    )


def _find_zip(asset_key: str) -> tuple[Path, Path] | None:
    """카테고리 전역에서 {asset_key}.zip 탐색 → (category_dir, zip_path)."""
    if not _KEY_RE.match(asset_key):
        return None
    for cat in _category_dirs():
        z = cat / f"{asset_key}.zip"
        if z.exists():
            return cat, z
    return None


@router.get("/ping")
async def ping(_: None = Depends(_require_host_key)):
    cats = [d.name for d in _category_dirs()]
    total = sum(len(list(d.glob("*.zip"))) for d in _category_dirs())
    return {"ok": True, "service": "SeCuardian-Marketplace", "categories": cats, "total": total}


@router.get("/catalog")
async def host_catalog(
    category: str | None = None,
    _: None = Depends(_require_host_key),
):
    """제공 자산 전량 목록 — 설치유무 무관, 카테고리별 groups + 평면 assets 동시 반환."""
    groups: dict[str, list[dict]] = {}
    for cat in _category_dirs():
        if category and cat.name != category:
            continue
        entries = [_asset_entry(cat, z) for z in sorted(cat.glob("*.zip"))]
        if entries:
            groups[cat.name] = entries
    assets = [a for entries in groups.values() for a in entries]
    return {
        "total": len(assets),
        "categories": list(groups.keys()),
        "groups": groups,
        "assets": assets,
    }


@router.get("/catalog/{asset_key}")
async def host_asset(asset_key: str, _: None = Depends(_require_host_key)):
    found = _find_zip(asset_key)
    if not found:
        raise HTTPException(status_code=404, detail=f"asset {asset_key} not found")
    cat, zip_path = found
    return _asset_entry(cat, zip_path)


@router.get("/download/{asset_key}")
async def host_download(asset_key: str, _: None = Depends(_require_host_key)):
    found = _find_zip(asset_key)
    if not found:
        raise HTTPException(status_code=404, detail=f"asset {asset_key} not found")
    _cat, zip_path = found
    return FileResponse(
        str(zip_path), media_type="application/zip", filename=zip_path.name
    )
