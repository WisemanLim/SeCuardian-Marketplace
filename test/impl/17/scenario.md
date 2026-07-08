# 시험 시나리오 — impl/17: 대시보드 실시간 위젯 (F-WEB)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "대시보드 실시간 위젯". 요약/활동 집계 엔드포인트 + 프론트 10초 폴링.
- 실행: `PYTHONPATH=. python test/impl/17/test_dashboard_summary.py` + 프론트 tsc/build.

## 범위
- `app/routers/router_dashboard.py` — `/api/dashboard/summary`(서버·에이전트·마켓·워크플로우·RAG·플레이그라운드·가드레일 카운트),
  `/api/dashboard/activity`(워크플로우 run·플레이그라운드·가드레일 판정 최신순 병합).
- 프론트 `api/dashboard.ts` + DashboardPage 실시간 위젯(활동 통계 4카드 + 최근 활동 리스트, `setInterval` 10초 폴링).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | summary 200 | 성공 |
| 2 | server 블록 | status·vector_backend 포함 |
| 3 | agents 카운트 | total≥4, enabled≥4 |
| 4 | 전 섹션 존재 | marketplace/workflow/rag/playground/guardrails |
| 5 | playground 실행 카운트 | +1 |
| 6 | guardrails 판정+차단 카운트 | +1, blocked≥1 |
| 7 | rag 컬렉션 카운트 | ≥1 |
| 8 | activity 200 | 성공 |
| 9 | activity 종류 | playground+guardrails 포함 |
| 10 | 무토큰 | 401/403 |
| 11 | 프론트 tsc/build | 0오류(2040 modules) |

## 판정 기준
- 10개 백엔드 assert + 프론트 tsc/build 0오류 = PASS.
