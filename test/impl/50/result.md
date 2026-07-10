# impl/50 시험 결과 — UserManager utilities → addon 이관

- 일시: 2026-07-10
- 실행: `uv run python test/impl/50/test_usermanager_move.py`
- 판정: **PASS (14/14)**

## 결과 요약

| TC | 시나리오 | 판정 |
|---|---------|------|
| 50-01 | addon 에 UserManager 디렉터리+zip, utilities 부재 | PASS (4) |
| 50-02 | 격리 DB 시드 — usermanager 미시드, utilities 5종·security 13종 | PASS (4) |
| 50-03 | 시드 고아(usermanager@utilities) 행·블롭 정리 + 로그 | PASS (2) |
| 50-04 | 사용자 등록 자산(블롭 uploaded_by=사용자) 유지 | PASS |
| 50-05 | 설치 중(active=1) 시드 고아 건너뜀 + 경고 | PASS (2) |

## 회귀 확인 (구 시험 정합 갱신 후)
- impl/34 (`pytest`) — PASS: TC-34-07 템플릿 5종 → **6종(UserManager 편입)** 갱신
- impl/36 (`pytest`) — 10 passed / 1 failed:
  - 갱신: _EXPECTED addon 6종·utilities 5종, TC-36-04 UserManager download 200,
    TC-36-01 `*_worker` 메타 디렉터리 필터(R22-4 정합)
  - **잔존 FAIL = TC-36-06 (기존 결함, 본 건 무관)**: `builtin/guardrails.zip` 에
    `data/guardrails/*.json` 구조 누락 — 이동 전 HEAD 에서도 동일 실패 확인(사전 존재). 별도 수정 필요.
- impl/40 — ALL PASS (16): B1 utilities 5+1, C1 시드 5종 부분집합,
  D1 `registerAssetZips(zipFiles, cat,` (impl/48 호출부 다행화 반영)
- impl/45 — PASS 34/34: UserManager 카테고리 utilities → addon

## dev DB 반영
`uv run python scripts/seed_assets.py` 실행 — `[seed-assets] 시드 고아 정리: usermanager` 확인,
local.db 에서 usermanager 카탈로그 행·블롭 제거(18종 스캔 = security 13 + utilities 5).

## 수정 파일
- `marketplace-assets/{utilities→addon}/UserManager{,.zip}` — git mv
- `scripts/seed_assets.py` — `_cleanup_orphaned_seed_rows` 신설
- `test/impl/{34,36,40,45}` — 스펙 정합 갱신
- `.docs/SeCMP-PRD.md` §7.6.2-4·§7.6.3-1 + 변경 이력 v0.48, `README(.en)`
