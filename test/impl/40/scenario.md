# 시험 시나리오 — impl/42 (물리 test/impl/40): §7.6.3 카탈로그 기본 등록 + 카테고리별 추가 등록

- 날짜: 2026-07-10
- 대상: Makefile(db-fresh 체인), `front/src/pages/marketplace/AssetRegisterModal.tsx`(신규 분리),
  `MarketplacePage.tsx`(카테고리별 `+ 추가`), `AgentsPage.tsx`(인라인 모달 제거), locales

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | `POST /catalog` body.category="security" (카테고리 지정 메타 등록) | 201, category=security 로 등록 |
| A2 | `POST /catalog/zip?category=utilities` (카테고리 프리셋 ZIP 등록) | 201, category=utilities 적용 |
| A3 | `GET /catalog?category=...` 필터 | 등록 자산 반환 |
| B1 | 격리 DB: seed_security + seed_assets 순차 실행(=db-fresh 체인 후반) | security 13 + utilities 6 등록 |
| B2 | Makefile `db-fresh` 체인 정적 검증 | seed.py·seed_security.py·seed_assets.py 3단 포함 |
| C1 | dev DB(local.db) 실 상태 | security 13 + utilities 6 (사용자 요구 * 반영 확인) |
| D1 | AssetRegisterModal 독립 컴포넌트 + AgentsPage 인라인 제거 (정적) | import 전환, 중복 정의 없음 |
| D2 | locales ko/en 신규 키(assetCategory·assetCategoryHint·addToCatalog) 패리티 | 양측 존재 |
| D3 | 프론트 `tsc --noEmit` | 0오류 |

## 실행

```bash
uv run python test/impl/40/test_catalog_category.py   # 스크립트 실행 방식(impl/1 패턴)
cd front && pnpm exec tsc --noEmit
```
