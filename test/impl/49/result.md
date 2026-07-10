# impl/49 시험 결과 — 중복 등록 확인 + 시드 보호 축소 + 카탈로그 삭제 시 시드 반환 (§7.6.6 v0.47)

- 일시: 2026-07-10
- 실행: `uv run python test/impl/49/test_asset_dup_and_delete.py`
- 판정: **PASS (29/29)**

## 결과 요약

| TC | 시나리오 | 판정 |
|---|---------|------|
| 49-01 | 신규 key 등록 — confirm 불필요 201 | PASS |
| 49-02 | 동일 key 재등록(confirm 없음) → 409 `{"code":"duplicate"}` + 기존 name/category 노출 | PASS (3) |
| 49-03 | `confirm=true` → 요청 카탈로그로 이동 등록, 중복 행 없음 | PASS (2) |
| 49-04 | `marketplace-assets/addon` 보유 key(toolproxyagent) 사용자 등록 → `deletable=true`, 삭제 200 | PASS (3) |
| 49-05 | 시드 보유 key(vasca-cve) → `deletable=false`, 삭제 403 | PASS (3) |
| 49-06 | 사용자 카탈로그 삭제 — 시드 key 는 security 반환, 일반 key 삭제, 잔존 없음 | PASS (6) |
| 49-06b | 시드 카탈로그(security) 자체 삭제 → 409 | PASS |
| 49-07 | 설치 중 자산 포함 카탈로그 삭제 409 → 해제 후 200 | PASS (4) |
| 49-08 | 프론트 정적 — dup ConfirmDialog 연동(R18-1)·api confirm·locale parity | PASS (5) |

## 회귀 확인
- `test/impl/47/test_asset_delete.py` — ALL PASS
  (TC-47-05 를 v0.47 스펙으로 갱신: 시드 key 포함 사용자 카테고리 삭제 = 409 → 반환+200)
- `test/impl/48/test_asset_register_catalog.py` — ALL PASS
  (시나리오 2 재등록에 `confirm=true` 반영 — v0.47 중복 확인 플로우)
- `front` TypeScript typecheck (`npx tsc --noEmit`) — 오류 없음
- 시험 후 저장소 오염 없음 (`addon-agents/deployed/` 잔존 파일 없음)

## 수정 파일
- `app/routers/router_marketplace.py` — `_seed_category`(시드 보호 = security/utilities 한정),
  `/catalog/zip` 중복 pre-check + `confirm`, `delete_category` 시드 반환 로직
- `front/src/api/marketplace.ts` — `confirm` 파라미터, `DuplicateAssetInfo`
- `front/src/pages/marketplace/AssetRegisterModal.tsx` — 409 duplicate → ConfirmDialog → confirm 재요청
- `front/src/locales/{ko,en}.json` — `agent.assetDupTitle`/`assetDupConfirm`
- `README.md`/`README.en.md` — §2.1 자산·Addon 파일 저장 경로 표 신설 + impl/51 노트
- `.docs/SeCMP-PRD.md` — §7.6.6 v0.47 개정 + 변경 이력
