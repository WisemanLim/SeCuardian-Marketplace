"""Addon ZIP 무중단 배포 헬퍼 (F-MP §7.6) — Marketplace 로컬/원격 install 공용.

다운로드/업로드한 addon ZIP 바이트를 기존 `/api/addon-agents/upload` 엔드포인트로 **in-process 재사용**
배포한다(별도 재구현 금지, PRD §7.3.3). extract→SQL→load_router→DB 등록이 그대로 실행되어
무중단 라이브 마운트된다. 유효 addon ZIP 이 아니면 upload 가 4xx 를 반환 → 호출측이 흡수.
"""
import httpx

from app.core.security import create_access_token


async def deploy_zip(blob: bytes, asset_key: str, user: dict, force: bool = True) -> dict:
    """ZIP 바이트를 addon upload 파이프라인으로 in-process 배포. 반환: {status_code, body}.

    force=False 면 기등록 키는 upload 가 409(중복 확인)을 반환한다 — 호출측이 사용자
    확인 후 force=True 로 재요청해야 한다 (R22-7).
    """
    from app.main import app as _app
    token = create_access_token({
        "sub": user.get("sub"), "role": user.get("role"),
        "username": user.get("username") or user.get("sub"),
    })
    transport = httpx.ASGITransport(app=_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as c:
        resp = await c.post(
            "/api/addon-agents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (f"{asset_key}.zip", blob, "application/zip")},
            data={"force": "true" if force else "false"},
        )
    return {"status_code": resp.status_code, "body": resp.json() if resp.status_code < 500 else resp.text}
