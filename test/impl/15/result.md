# 시험 결과 — impl/15

- 날짜: 2026-07-08
- 판정: **PASS** (6/6) + impl/4 회귀 무영향

## 실행 결과
```
PASS pgvector 라이브러리 import OK
PASS sqlite → local 폴백 (local)
PASS local dense_scores → None(폴백 신호)
PASS 로컬 하이브리드검색 정상(BM25 top)
PASS top hit = 식별자 문서
=== RESULT: ALL PASS
```

## 검증 항목
- `resolve()` 가 조건(PostgreSQL + pgvector lib + VECTOR_BACKEND=pgvector) 전부 충족 시만 'pgvector', 아니면 'local' 폴백.
- pg 전용 헬퍼(ensure_pg_schema/write_embedding/dense_scores)는 local 에서 안전한 no-op/None → 기존 sqlite 경로 100% 보존(impl/4 회귀 무영향).
- pgvector 경로 코드(vector 컬럼·IVFFLAT·`<=>` ANN) 무결성 정적 확인. 실 벤치마크(Recall@10/p95)는 postgres+pgvector 환경 필요.
- `ruff check` 0오류.

## 미결/후속
- 실 pgvector 성능(§5 KPI: Recall@10≥0.89, p95≤250ms) 측정 = postgres+pgvector 배포 후.
- 임베딩 모델 교체(현 로컬 해싱 → sentence-transformers 등, embedding_version 고정) 로드맵.
