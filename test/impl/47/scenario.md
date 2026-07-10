# 시험 시나리오 — 자산 등록 ZIP 필수 + 사용자 자산·카탈로그 삭제 (§7.6.6, impl/49 · 물리 test/impl/47)

배경(사용자 결함 보고 2026-07-10): ① `자산 등록`·카테고리 `+ 추가` 가 ZIP 0개(메타만)로도
등록됨 — 실제 에이전트 파일 없는 빈 자산 생성 ② 사용자 등록 자산(TEST 등)은 삭제 수단 없음.

요구: ZIP 1개 이상 있어야 등록. 사용자 등록 자산(디스크 `marketplace-assets/` 미보유)은
자산 삭제 + 카탈로그(카테고리) 삭제 기능 제공.

| ID | 입력 | 기대 |
|----|------|------|
| TC-47-01 | 등록 모달 ZIP 필수 | AssetRegisterModal — zipFiles 0개 시 `agent.assetZipRequired` 오류·제출 차단, 메타-only `registerAsset` 경로 제거(zip 경로만). 메타-only `POST /catalog` 는 AI/프로그래매틱용 유지(회귀: impl/39 A1~A5) |
| TC-47-02 | deletable 플래그 | zip 등록 사용자 자산 → `deletable=true`, 디스크 보유 키(vasca-cve) → `deletable=false` |
| TC-47-03 | 사용자 자산 삭제 | `DELETE /catalog/{key}` → 200, catalog 목록·blobs·installs·config 행 제거. 미존재 → 404, user 권한 → 403 |
| TC-47-04 | 보호 가드 | 디스크 보유 자산 삭제 → 403, 설치 중 자산 삭제 → 409(해제 후 200) |
| TC-47-05 | 카테고리 삭제 | 사용자 카테고리(zip 자산 2종) `DELETE /catalog-category/{cat}` → 200 + 전체 제거. 디스크 보유 포함 카테고리 → 409, 미존재 → 404 |
| TC-47-06 | 프론트 배선·locale | MarketplacePage 삭제 버튼 2종(deletable 조건), marketplace.ts deleteAsset/deleteCategory, locales 6키 ko/en 패리티, `tsc --noEmit` 0오류 |

실행: `uv run python test/impl/47/test_asset_delete.py` + `cd front && npx tsc --noEmit`
