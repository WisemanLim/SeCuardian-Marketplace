# impl/48 시험 결과 — 자산 등록 회귀 수정 (카탈로그·폼 입력 반영)

- 일시: 2026-07-10
- 실행: `uv run python test/impl/48/test_asset_register_catalog.py`
- 판정: **PASS (19/19)**

## 결과 요약

| # | 시나리오 | 판정 |
|---|---------|------|
| 1 | 단일 ZIP + 폼 입력 + 신규 카탈로그 testcat — category/name/name_en/description/kind 폼 값 반영 | PASS (6) |
| 2 | 동일 key@version 재등록 시 movecat 이동 + 폼 name 반영 + 중복 행 없음 | PASS (4) |
| 3 | 신규 카탈로그에서 조회 가능, 이전 카탈로그 잔존 없음 | PASS (2) |
| 4 | 다중 ZIP — 폼 name 무시(meta 우선), 전부 요청 category, kind=agent 기본 | PASS (4) |
| 5 | 폼 미전송(레거시 호출) — meta 기반 등록 하위호환 | PASS (3) |

## 회귀 확인
- `test/impl/47/test_asset_delete.py` 재실행 — ALL PASS (자산 삭제·카탈로그 삭제 §7.6.6 불변)
- `front` TypeScript typecheck (`npx tsc --noEmit`) — 오류 없음

## 수정 파일
- `app/routers/router_marketplace.py` — `/catalog/zip` UPDATE 분기 category 반영,
  단일 ZIP 폼 오버라이드(name/name_en/description/description_en/kind Form 필드)
- `front/src/api/marketplace.ts` — `registerAssetZips` fields 전송
- `front/src/pages/marketplace/AssetRegisterModal.tsx` — 폼 값 전달
