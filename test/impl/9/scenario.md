# 시험 시나리오 — impl/9: F-MP 원격 레지스트리 클라이언트 (E1.5, PRD §7.3)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "F-MP 원격 레지스트리". PRD §7.3.3 라우터 계약 구현.
- 실행: `PYTHONPATH=. python test/impl/9/test_marketplace_remote.py` (원격 fetch monkeypatch)

## 범위
- `app/routers/router_marketplace_remote.py` (`/api/marketplace-remote`):
  - `GET /ping` — 연결성/인증 확인
  - `GET /catalog` — 원격 카탈로그(in-memory 캐시, `marketplace_sync_interval_sec` TTL, `?refresh=true` 강제)
  - `GET /catalog/{key}` — 원격 자산 상세
  - `POST /install/{key}` — 원격 ZIP 다운로드 → SHA256 검증 → 로컬 `marketplace_assets`(source='remote') 편입
- 원격 HTTP 접근은 `_remote_get`/`_remote_download` 로 분리(시험 monkeypatch 지점).
- `marketplace_remote_enabled=false`(기본) 시 전 엔드포인트 409 — 폐쇄망 안전 기본값(§7.3.2 에어갭).
- 프론트: `api/marketplaceRemote.ts` + MarketplacePage 원격 카탈로그 섹션(활성 시만 노출, 로컬 편입 버튼).

## 설계 결정
- install 은 **다운로드+체크섬 검증+로컬 카탈로그 편입까지** — 실제 무중단 hot-deploy(ZIP→router 마운트)
  연결은 §9.5 별도 항목(§7.6 "실 addon ZIP 파이프라인")으로 분리. §9.5 두 항목의 경계와 일치.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 기본(disabled) ping | 409 |
| 2 | enable 후 ping | 200 ok |
| 3 | catalog 최초 | live(cached=false) |
| 4 | catalog 재조회 | cached=true(원격 fetch 1회만) |
| 5 | `?refresh=true` | 캐시 우회(fetch 2회) |
| 6 | 상세 | 원격 메타 반환 |
| 7 | install(체크섬 일치) | 201, source='remote' 로 로컬 편입 |
| 8 | 로컬 카탈로그 병합 확인 | `/api/marketplace/catalog` 에 노출 |
| 9 | 중복 install | 409 |
| 10 | 체크섬 불일치 | 422 |
| 11 | user install | 403 |
| 12 | 무토큰 | 401/403 |
| 13 | 프론트 tsc/build | 0 오류 |

## 판정 기준
- 14개 백엔드 assert + 프론트 tsc/build 0오류 = PASS.
