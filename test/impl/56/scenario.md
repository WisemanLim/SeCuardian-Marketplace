# impl/56 시험 시나리오 — E12 Playground 비용 추적 + Eval

대상: `router_playground` add-only 엔드포인트 `GET /cost`·`POST /eval`. 스키마 무변경(기존 토큰 컬럼 활용).
실행: `.venv/bin/python test/impl/56/test_playground_cost_eval.py` (fresh sqlite, 실 TestClient, degrade 강제).

| TC | 수용 기준 |
|---|---|
| run 생성 | `POST /run` 201 degraded |
| cost 집계 | `GET /cost` 200, totals.runs≥1, degraded=무료(0.0), currency USD |
| eval run_id | run_id + [contains, min_length] → all_passed |
| eval output | output 직접 + [regex, not_contains, contains(실패)] → 2/3 |
| eval 검증 | 빈 assertions 422 / run_id·output 둘다 없음 422 / 없는 run_id 404 / 잘못된 type 422 |
