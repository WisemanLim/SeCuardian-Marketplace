# 시험 결과 — impl/42 (물리 test/impl/40): §7.6.3 카탈로그 기본 등록 + 카테고리별 추가 등록

- 날짜: 2026-07-10
- 판정: **PASS** (16/16)
- 실행: `uv run python test/impl/40/test_catalog_category.py` (격리 sqlite + TestClient)

| # | 케이스 | 결과 |
|---|---|---|
| A1 | 카테고리 지정 메타 등록 (body.category=security, asset_key 자동부여) | ✅ 201 |
| A2 | 카테고리 프리셋 ZIP 등록 (`/catalog/zip?category=utilities`) | ✅ 201 |
| A3 | category 필터 조회 | ✅ |
| B1 | seed_security + seed_assets 체인(격리 DB) → security 13(+1)·utilities 6(+1) | ✅ |
| B1 | addon·builtin 카테고리 카탈로그 제외 (§7.6.3-1) | ✅ |
| B2 | Makefile db-fresh 3단 시드 체인 (seed→seed-security→seed-assets) | ✅ |
| C1 | **dev DB(local.db) 실 등록 상태 — security 13 + utilities 6** (사용자 요구 * 완료) | ✅ |
| D1 | AssetRegisterModal 독립 분리·AgentsPage 인라인 제거·카테고리별 `+ 추가` 배선 | ✅ 3건 |
| D2 | locales ko/en 신규 3키 패리티 | ✅ |
| D3 | 프론트 `tsc --noEmit` | ✅ 0오류 |

## 회귀

| 시험 | 결과 |
|---|---|
| test/impl/39 (§7.6.2 자산 등록 UX, 25케이스) | ✅ ALL PASS |
| test/impl/1 (F-MP CRUD·설치 수명주기) | ✅ ALL PASS |
| test/impl/34 (§7.6.1 탭 통합) | ✅ exit 0 |

## 비고

- 초기 실행 시 B1 `security 13` 기대가 FAIL(14) — A1 케이스가 security 에 1건 추가 등록한
  것을 미반영한 **시험 기대값 오류**로 판정, 13+1 로 정정 후 ALL PASS (구현 결함 아님).
- 백엔드 무변경 — category 는 기존 `AssetCreate.category`·`/catalog/zip?category=` 계약 재사용.
