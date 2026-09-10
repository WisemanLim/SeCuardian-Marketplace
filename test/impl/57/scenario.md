# impl/57 시험 시나리오 — E7(부분) Qdrant 벡터 백엔드 어댑터

대상: `app/services/vector_backend.py` qdrant 경로 추가(add-only) + config `qdrant_*` 필드 + rag_pipeline
write_embedding 에 collection_id 전달. 단일 컬렉션(청크=포인트, payload.collection_id 필터).
전제(mock-first): qdrant-client 미설치(오프라인/폐쇄망 기본) — VECTOR_BACKEND=qdrant 여도 local 우아한 폴백.
실행: `.venv/bin/python test/impl/57/test_qdrant_backend.py` (fresh sqlite, 실 TestClient).

| TC | 수용 기준 |
|---|---|
| resolve 폴백 | VECTOR_BACKEND=qdrant + qdrant-client 미설치 → resolve()='local' |
| ops 폴백 안전 | ensure/write/dense 폴백 무크래시(dense=None) |
| RAG E2E 무중단 | qdrant 선택이어도 컬렉션 생성·문서 ingest·검색 정상(local 폴백) |
| RBAC 유지 | user ingest → 403 |

> qdrant-client + 실 Qdrant 서버 구비 시 resolve()='qdrant' 경로 활성화(별도 인프라 검증). 코드 경로는 시험됨.
