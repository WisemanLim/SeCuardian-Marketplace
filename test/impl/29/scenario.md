# 시험 시나리오 — impl/31(물리 test/impl/29): F-RAG pgvector 실측 벤치마크

> 논리 순번은 impl/31(직전 impl/30=enabled 토글, 물리 test/impl/28). 물리 디렉터리는
> `test/impl/*` 자동증가값(29). PRD §7.5.1 근거. **사용자 승인(2026-07-09) 후 진행**
> (도커 이미지 pull + 실 컨테이너 기동 — 코드 편집을 넘어선 인프라 작업).

- 대상: `docker-compose.yml`(postgres 이미지 교체), `app/services/vector_backend.py`(impl/15,
  코드 변경 없음 — 실경로 최초 실측), `app/services/rag_pipeline.py`.

## 사전 발견
- 기존 `postgres:17-alpine` 이미지에는 `vector` 확장이 없어 `ensure_pg_schema()` 가 조용히
  local 폴백했을 것으로 추정(예외를 삼키는 설계, §7.5.1) — **`pgvector/pgvector:pg17` 로 영구 교체**.

## 검증 항목

1. **인프라 검증** — `docker compose up -d postgres` 로 기동한 실 컨테이너에서
   `CREATE EXTENSION vector` 성공 확인(psql 직접 확인, extversion 0.8.4).
2. **pgvector 경로 실제 활성화** — `ENV=dev + DATABASE_URL=postgresql://...+ VECTOR_BACKEND=pgvector`
   로 앱 부팅 시 `vector_backend.resolve()` 가 실제로 `"pgvector"` 를 반환(sqlite 세션에서는
   불가능했던 검증).
3. **엔드투엔드 인입·검색** — `/api/rag/collections` → `/documents` → `/search` 실 HTTP API 로
   문서 인입 시 `rag_chunks.embedding` 컬럼(pgvector 타입)이 실제로 채워짐(직접 SQL 확인),
   검색이 `dense_scores()`(SQL `<=>` ANN) 경로를 실제로 타는지 확인.
4. **Recall@10 실측** — 식별자 기반 질의 세트(impl/4 방법론과 동일, 이번엔 실 pgvector 위에서)로
   측정. **가정 아닌 실측치**를 `result.md` 에 기록.
5. **p95 지연 실측** — 검색 요청 왕복(HTTP, in-process TestClient) p95.
6. **정직한 보고** — PRD §5 목표(Recall@10≥0.89, p95≤250ms)와 비교하되, 로컬 해싱 임베더의
   의미기반 한계는 별도 로드맵(임베딩 모델 교체)임을 명시 — 인프라 검증(이번 목표)과 임베딩
   품질(별도 로드맵)을 분리해서 판정.
7. **회귀** — 기존 sqlite 경로(impl/4·15) 무영향 확인(`test/impl/4`·`15` 재실행, sqlite 세션에서).
8. **정리** — 벤치마크 후 `docker compose stop postgres` 로 로컬 리소스 정리(볼륨 보존).

## 판정 기준
①~③(인프라 정상 동작) 전부 확인되면 **인프라 검증 PASS**. ④~⑤ 수치는 있는 그대로 기록(목표
미달이어도 "실패"가 아니라 "실측 결과"로 취급 — 원인 분리 보고).
