# impl/50 — UserManager 자산 utilities → addon 이관 (§7.6.1-7·§7.6.2-4 개정)

## 배경 (사용자 요구 2026-07-10)
`marketplace-assets/utilities/UserManager{,.zip}` 를 `marketplace-assets/addon/` 으로 이동.
결과: 카탈로그 시드 대상 제외(utilities 6→5종), 스캐폴드 템플릿 편입(addon 5→6종),
시드 보호 해제(사용자 등록 시 `deletable=true`).

## 시험 항목
| # | 시나리오 | 기대 결과 |
|---|---------|----------|
| 1 | 디렉터리 배치 | addon 에 UserManager 디렉터리+zip, utilities 에 부재 |
| 2 | 격리 DB 에 `seed_assets` 실행 | usermanager 미시드, utilities 5종·security 13종 시드 |
| 3 | 시드 고아 정리 — 구 시드 행(usermanager@utilities, 블롭 uploaded_by=seed-assets) 존재 상태로 재시드 | 행·블롭 삭제 (`_cleanup_orphaned_seed_rows`) |
| 4 | 사용자 등록 자산(블롭 uploaded_by=사용자)은 시드 디스크 미보유라도 유지 | 미삭제 |
| 5 | 설치 중(active=1) 시드 고아 | 삭제 건너뜀(경고 출력) |
| 6 | 기존 회귀 — impl/34(TC-34-07 템플릿 6종)·impl/36(배치/쌍/목록/다운로드)·impl/40(시드 5종)·impl/45(호스트 카탈로그) | ALL PASS |

## 실행
```bash
uv run python test/impl/50/test_usermanager_move.py
```
