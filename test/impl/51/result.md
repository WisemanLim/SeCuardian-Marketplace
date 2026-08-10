# 시험 결과 — ADDON 등록 파이프라인 오류 수정 (test/impl/51)

실행일: 2026-08-10 · 명령: `uv run pytest test/impl/51 -q`, `cd front && npx tsc --noEmit`

| ID | 결과 | 비고 |
|----|------|------|
| TC-51-01 | PASS | 내장 키 등록 불가 — force 로도 우회 불가, 압축 해제 없음 |
| TC-51-02 | PASS | 구조화 409 `duplicate` — 영문 원문 제거 |
| TC-51-03 | PASS | worker 배포본 400 + `deployed/` 잔여 0 |
| TC-51-04 | PASS | 순수 addon 활성 등록 + meta `type` 폴백 |
| TC-51-05 | PASS | 라우터 로드 실패 롤백 |
| TC-51-06 | PASS | 복원 쿼리 is_enabled 조인 + 소스 없음 경고 |
| TC-51-07 | PASS | 프론트 conflict UI·ko/en 문구 |

`uv run pytest test/impl/51 -q` → **7 passed** · `npx tsc --noEmit` 0오류.

## 비고

- SeCMP 는 마켓플레이스 **호스트**라 SeCuardian 의 `allow_builtin=True`(마켓플레이스 배포)
  경로가 없다. 따라서 내장 키 업로드는 예외 없이 등록 불가다.
- `test/impl/{49,50}` 는 pytest 수집 시 `sys.exit()` 하는 수동 하니스(`test_*.py` 명명)라
  같은 세션에서 함께 수집하면 INTERNALERROR 가 난다(기존 이슈, 본 수정과 무관).
  SeCuardian 처럼 `test/impl/conftest.py` 로 수집 제외하면 해소된다.
