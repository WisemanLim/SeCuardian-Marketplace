# 시험 시나리오 — impl/15: F-RAG pgvector 어댑터 (PRD §7.5)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "F-RAG pgvector 전환". `VECTOR_BACKEND` 분기 + sqlite 폴백 유지.
- 실행: `PYTHONPATH=. python test/impl/15/test_pgvector_adapter.py`

## 범위
- `app/services/vector_backend.py` — `resolve()`(pgvector: PostgreSQL+lib 모두 충족 시만, 아니면 local),
  `ensure_pg_schema`(CREATE EXTENSION vector + embedding vector 컬럼 + IVFFLAT 인덱스, pg 전용 멱등),
  `write_embedding`(pg vector 컬럼 기록), `dense_scores`(SQL `<=>` 코사인 ANN, local 이면 None→폴백).
- `rag_pipeline`: index_document 가 pg 스키마 보장+임베딩 기록, hybrid_search dense 를 pgvector 우선·python 폴백.

## 설계 제약(사용자 인지)
- pgvector 실동작 = PostgreSQL + `CREATE EXTENSION vector` 필요. 현 세션 sqlite → resolve()='local' 폴백만 검증.
  pg 경로 코드는 postgres 환경에서 활성화(pg 전용 DDL/쿼리 가드).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | pgvector 라이브러리 | import OK |
| 2 | VECTOR_BACKEND=pgvector + sqlite | resolve()='local' 폴백 |
| 3 | local 에서 pg 헬퍼 | no-op/None(무중단) |
| 4 | 로컬 하이브리드검색 | 식별자 질의 BM25 최상위(불변) |
| 5 | top hit | 식별자 문서 |

## 판정 기준
- 6개 assert 전부 PASS + impl/4 회귀 무영향 = PASS.
