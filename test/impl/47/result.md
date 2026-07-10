# 시험 결과 — 자산 등록 ZIP 필수 + 사용자 자산·카탈로그 삭제 (§7.6.6, impl/49 · 물리 test/impl/47)

일시: 2026-07-10 · 판정: **PASS (23/23 + 회귀 impl/39 ALL PASS + tsc 0 + 브라우저 실증)**

| ID | 결과 | 비고 |
|----|------|------|
| TC-47-01 | PASS | 모달 ZIP 필수 가드 + 메타-only 경로 제거(정적) · **브라우저 실증**: ZIP 없이 등록 클릭 → "에이전트 ZIP 파일을 1개 이상 첨부해야 등록할 수 있습니다" 오류 표시. 메타-only `POST /catalog` API 는 유지(impl/39 A1~A5 회귀 PASS) |
| TC-47-02 | PASS | zip 등록 자산 deletable=true · 디스크 보유 키(vasca-cve) deletable=false |
| TC-47-03 | PASS | 삭제 → 200 + catalog·config 행 제거, 미존재 404, user 권한 403 |
| TC-47-04 | PASS | 디스크 보유 403 · 설치 중 409 · 해제 후 200 |
| TC-47-05 | PASS | 사용자 카테고리 일괄 삭제 200(잔여 자산 목록 반환) · 디스크 보유 포함 409 · 미존재 404 |
| TC-47-06 | PASS | marketplace.ts·MarketplacePage 배선 + locales 6키 ko/en 패리티 + `tsc --noEmit` 0 |

브라우저 실증(headless, localhost:4100): test 카테고리(사용자 등록 a·asset 2종)에만
`카탈로그 삭제` 버튼 1개 + 자산 `삭제` 버튼 2개 렌더 — security·utilities(디스크 보유)는 미노출.

## 추가 요구 (사용자, 2026-07-10) — 삭제 확인 커스텀 다이얼로그 · **PASS**

`window.confirm` → 기존 커스텀 `ConfirmDialog`(R18-1, AgentsPage 동일 패턴)로 교체.
`confirmDel` 상태(asset|category) + 다이얼로그 확인 시 실제 삭제 실행.
TC-47-07 신설(정적: window.confirm 부재 + ConfirmDialog 배선) PASS + `tsc --noEmit` 0.
**브라우저 E2E 실증**: 임시 자산(e2e-tmp) 등록 → `삭제` 클릭 → 커스텀 다이얼로그
(🗑️ 아이콘·자산명 메시지·취소/삭제 버튼) 렌더 스크린샷 → `삭제` 확인 클릭 →
자산 제거·다이얼로그 닫힘·카테고리 소멸·DB 잔재 0행 확인.

## 추가 요구 2 (사용자, 2026-07-10) — 등록 모달 필드 순서·필수 표시 UX · **PASS**

① 입력 순서 = 카탈로그(category, 첫 행) → name·종류 → 이름(영문) → 설명 → 설명(영문) →
Addon ZIP 첨부(카테고리 `+ 추가` 진입 시 카탈로그 행은 기존대로 숨김) ② '(선택)' 라벨 전면
제거(assetNameEn·assetDescEn·assetZip, ko/en) — 필수 항목은 적색 `*` 표시(ZIP 첨부).
TC-47-08 신설 PASS + `tsc --noEmit` 0 + **브라우저 실증**(필드 순서·적색 * 렌더 스크린샷).

추가 보완(사용자, 2026-07-10): 라벨 `name`→`자산명`(en: Asset name)·`이름 (영문)`→`자산명 (영문)`,
필수 * 표시 = 자산명·설명·Addon ZIP 첨부 3개 + submit 검증(자산명→설명→ZIP 순 오류).
브라우저 실측: 필수 필드 `["자산명","설명","Addon ZIP 첨부"]`, 빈 제출 → "자산명을 입력하세요".

## 회귀 수정 1건 — seed_assets worker 오등록 (impl/62 유래)

impl/39 재실행 시 `C1 security 13 seeded (15)` FAIL — impl/62 가 `marketplace-assets/security/`
에 추가한 `{VASCA,BehaviorNotiService}_worker/` 메타 디렉터리를 seed_assets 가 설치형 자산으로
오등록(R22-4 위반: worker 는 다운로드 전용). `scripts/seed_assets.py` 에 `*_worker` 디렉터리
스킵 추가 → impl/39 ALL PASS 복원. 라이브 DB 에는 오등록 행 없음(확인).
