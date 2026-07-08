# 시험 시나리오 — impl/4: F-RAG (컬렉션·수집·하이브리드 검색) 백엔드+프론트

- 날짜: 2026-07-08
- 대상: RAG 파이프라인 (F-RAG, PRD §7.5) — v0 ORM→raw-SQL 이식

## 범위
- DDL: `rag_collections`·`rag_documents`·`rag_chunks` (sqlite+pg, tenant_id)
- `app/services/embeddings.py` — 해싱 임베더(오프라인, feature hashing + L2 정규화)
- `app/services/rag_pipeline.py` — 청킹, 인덱싱, BM25(k1=1.5,b=0.75), dense cosine, RRF(k=60) 융합
- `app/routers/router_rag.py` — 컬렉션 CRUD, 문서 수집, 하이브리드 검색
- `tbl_agent_config` `rag` 시드
- 프론트: `front/src/api/rag.ts` + `pages/rag/RagPage.tsx`(컬렉션 선택·수집·검색)

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 0 | `rag` 에이전트 시드 | agent-config 포함 |
| 1 | user 컬렉션 생성 | 403 |
| 2 | 잘못된 sensitivity | 422 |
| 3 | 컬렉션 생성 | 201, embedding_dim=256 |
| 4 | 중복 이름 | 409 |
| 5 | 문서 수집(식별자 텍스트 포함) | 201, chunks≥1 |
| 6 | user 수집 | 403 |
| 7 | 문서 목록 | 2건 |
| 8 | 식별자 질의(SKU-12345) 검색 | bm25_rank=1 히트가 해당 문서 |
| 9 | 미존재 컬렉션 검색 | 404 |
| 10 | 무토큰 | 401/403 |
| 11 | 프론트 타입체크 | 0 오류 |

## 판정 기준
- 15개 백엔드 assert + 프론트 tsc 0오류 = PASS.
