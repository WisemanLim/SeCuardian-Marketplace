# 시험 결과 — impl/9

- 날짜: 2026-07-08
- 판정: **PASS** (백엔드 14/14 + 프론트 tsc/build 0오류)

## 백엔드 실행 결과
```
PASS disabled -> 409
PASS ping ok (200)
PASS catalog live
PASS catalog cached (fetch calls=1)
PASS refresh=true bypasses cache
PASS remote detail
PASS remote install 201
PASS checksum returned matches
PASS local asset source=remote
PASS remote asset merged into local catalog
PASS duplicate remote install -> 409
PASS checksum mismatch -> 422
PASS user remote install -> 403
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- 마스터 스위치(`marketplace_remote_enabled`) off 기본값 → 전 엔드포인트 409(폐쇄망 안전, §7.3.2 에어갭 모드).
- 카탈로그 캐시 TTL(`marketplace_sync_interval_sec`) 준수 — 재조회 시 원격 fetch 미발생(cached=true), `?refresh=true` 로 우회.
- install: 원격 ZIP 다운로드 → **SHA256 검증**(`marketplace_install_verify_checksum`) → 일치 시 로컬 `marketplace_assets`(source='remote') 편입 → 기존 로컬 카탈로그·설치 흐름(impl/1)에 그대로 합류.
- 체크섬 불일치 422, 서명 요구 시 501(미구현 명시), RBAC(admin/supervisor), 중복 409.
- 원격 HTTP 접근을 `_remote_get`/`_remote_download` 로 분리해 실제 네트워크 없이 monkeypatch 시험 — 결정적·오프라인.
- boot 25 routes, `ruff check` 0오류, 프론트 tsc+build 0오류(2039 modules).

## 미결/후속 (범위 밖)
- **실 addon ZIP hot-deploy 연결(§7.6)** — 현재 install 은 로컬 카탈로그 편입까지. 다운로드한 ZIP 을 `router_addon_agent` upload 파이프라인(SQL→`load_router()`→무중단 마운트)에 태우는 연결은 §9.5 별도 항목.
- GPG 서명 검증(`marketplace_install_require_signature`) — 501 스텁.
- mTLS(사설 CA) 는 `marketplace_tls_verify`/`marketplace_tls_ca_bundle` config 로 노출되나 CA 번들 로딩 로직은 httpx `verify` 파라미터 확장 필요(후속).
