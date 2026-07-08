# 시험 시나리오 — impl/5: F-PG (Playground) 백엔드+프론트

- 날짜: 2026-07-08
- 대상: 플레이그라운드 (F-PG, PRD §7.7) — v0에 백엔드 없음(placeholder뿐) → PRD §7.7·§7.11.1 기반 신규 구현
- 실행: `PYTHONPATH=. python test/impl/5/test_playground.py`

## 범위
- DDL: `playground_runs` (tenant_id 선반영)
- `app/routers/router_playground.py` — `/run`(공유 LLM 폴백 실호출 + RAG 컨텍스트 주입 + degrade), `/runs`(이력)
- `services/llm_fallback.call_ollama` 재사용(F-AI 공유, PRD §7.11.1), `services/rag_pipeline.hybrid_search` 재사용(F-RAG 승격 경로)
- `tbl_agent_config` `playground` 시드
- 프론트: `api/playground.ts` + `pages/playground/PlaygroundPage.tsx`(프롬프트/모델/RAG 조합, A/B 비교 2-variant 동시 실행, 이력)

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 0 | `playground` 에이전트 시드 | agent-config 포함 |
| 1 | Ollama 미가동 상태로 실행 | 201, provider=degraded, 무중단 |
| 2 | 임의 인증 사용자 실행(RBAC 게이트 없음) | 403 아님 — 실험 도구 특성상 전 사용자 허용 |
| 3 | RAG 컬렉션 지정 실행 | 201, citations_json 에 하이브리드 검색 결과 포함 |
| 4 | 존재하지 않는 rag_collection_id | 404 |
| 5 | 실행 이력 조회 | 성공 run 개수와 일치(실패한 404 요청은 미기록) |
| 6 | 무토큰 | 401/403 |
| 7 | 프론트 타입체크 | 0 오류 |

## 판정 기준
- 13개 백엔드 assert + 프론트 tsc 0오류 = PASS.
