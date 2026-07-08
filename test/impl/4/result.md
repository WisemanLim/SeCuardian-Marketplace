# 시험 결과 — impl/4

- 날짜: 2026-07-08
- 판정: **PASS** (백엔드 15/15 + 프론트 tsc 0오류)

## 백엔드 실행 결과
```
PASS rag agent seeded (['general', 'chat', 'marketplace', 'workflow', 'rag'])
PASS user create collection -> 403
PASS bad sensitivity -> 422
PASS create collection 201
PASS embedding_dim default 256
PASS duplicate collection name -> 409
PASS ingest doc-a (chunks:1)
PASS ingest doc-b
PASS user ingest -> 403
PASS list documents = 2
PASS search 200
PASS search returns hits (1)
PASS top hit has bm25_rank=1
PASS top hit is the SKU doc
PASS search on missing collection -> 404
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- 하이브리드 검색: 식별자성 질의(SKU-12345)가 BM25 경로로 정확히 최상위 랭크(dense_rank=1, bm25_rank=1) — PRD §5 수용기준("식별자성 질의 → BM25 포함 Recall") 충족.
- RRF(k=60) 융합, 청킹(문자 기반 400/overlap40), 로컬 해싱 임베더(오프라인, embedding_version=local-hash-v1) 동작.
- tenant_id 격리, sensitivity 검증(general|sensitive), RBAC(admin/supervisor 수집·생성).
- boot 22 routes, `ruff check` 신규파일 0 오류, 프론트 `tsc --noEmit` 0 오류.

## 미결/후속
- pgvector/Qdrant 확장(§7.5 로드맵) — 현재는 로컬 해싱 임베더 고정.
- 문서유형별 청킹 정책, eval(Recall@10/NDCG@10) 벤치마크는 로드맵(P3).
- 프론트 브라우저 E2E 클릭 시험 미실시(타입체크·빌드로 정적 검증).
