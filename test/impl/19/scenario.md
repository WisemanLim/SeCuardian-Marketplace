# 시험 시나리오 — impl/19: F-PG 토큰 사용량 추적 (관측성, PRD §7.9)

- 날짜: 2026-07-08
- 대상: Playground 실행의 토큰(prompt_eval/eval) 추적. `call_ollama` usage_out 미연결 → 연결.
- 실행: `PYTHONPATH=. python test/impl/19/test_playground_tokens.py` (Ollama httpx mock)

## 범위
- `playground_runs` 컬럼 `input_tokens`/`output_tokens` 추가(양 dialect).
- `router_playground.run` — `call_ollama(..., usage_out=usage)` 로 토큰 수집·저장.
- `router_dashboard.summary` — playground 토큰 합계(`playground.tokens`) 노출.
- 프론트: PlaygroundPage 이력 토큰 열, DashboardPage 'PG 토큰 누적' 카드.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | run | 201 |
| 2 | provider | ollama(mock) |
| 3 | 토큰 기록 | input=42, output=17 |
| 4 | 이력 토큰 | 노출 |
| 5 | 대시보드 합계 | tokens=59 |
| 6 | degrade 경로 | tokens 0 |

## 판정 기준
- 6개 assert + impl/5·17 회귀 무영향 + 프론트 tsc/build 0오류 = PASS.
