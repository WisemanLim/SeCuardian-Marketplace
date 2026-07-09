# 시험 결과 — impl/31(물리 test/impl/29): F-RAG pgvector 실측 벤치마크

- 날짜: 2026-07-09
- 판정: **인프라 검증 PASS** + **실측 목표 달성**(7/7 assert)
- 환경: 실 PostgreSQL(`pgvector/pgvector:pg17`, Docker), `docker exec ... psql` 로 확장 확인,
  FastAPI TestClient(`ENV=dev`, `VECTOR_BACKEND=pgvector`, `DATABASE_URL=postgresql://app:app@localhost:5432/app`)

## 사전 발견 및 수정
`docker-compose.yml` 의 `postgres` 서비스가 plain `postgres:17-alpine` 이미지를 사용해
**`vector` 확장이 없었다** — `ensure_pg_schema()`(impl/15)가 예외를 삼키고 조용히 local 폴백하는
설계라 지금까지 드러나지 않았던 잠재 결함. `pgvector/pgvector:pg17` 이미지로 **영구 교체**함
(§7.5.1). 확장 설치 확인:
```
$ docker exec ... psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
 extname | extversion
---------+------------
 vector  | 0.8.4
```

## 실행 결과
```
PASS vector_backend.resolve() == pgvector (pgvector)
PASS create collection (201, ...)
PASS pgvector embedding column populated for all chunks ({'n': 40})

--- 실측 결과 (N=40) ---
Recall@10 (identifier queries): 1.000  (목표 §5: >=0.89)
p50 latency: 18.3ms  p95 latency: 20.8ms  (목표 §5: p95<=250ms)
PASS Recall@10 target met (1.000)
PASS p95 latency target met (20.8ms)
PASS pgvector search path returns non-trivial results (40/40)
PASS search with no match still 200 (no crash) (200)

=== BENCHMARK SUMMARY ===
Recall@10=1.000 p50=18.3ms p95=20.8ms N=40

=== RESULT: ALL PASS
```

## 실측 수치 — PRD §5 목표 대비

| 지표 | 목표(§5) | 실측 | 판정 |
|---|---|---|---|
| Recall@10 | ≥ 0.89 | **1.000** | ✅ 초과 달성 |
| p95 지연 | ≤ 250ms | **20.8ms** | ✅ 초과 달성(약 12배 여유) |
| p50 지연 | (참고) | 18.3ms | — |

## 해석 — 인프라 검증 vs 임베딩 품질 분리 보고
- 이번 벤치마크는 **식별자(SKU) 기반 질의 세트**(impl/4 와 동일 방법론)로, pgvector ANN 경로가
  실제로 동작하는지(①확장 설치 ②`resolve()="pgvector"` ③임베딩 컬럼 기록 ④검색 시 SQL `<=>`
  사용 ⑤응답 지연)를 검증하는 데 목적이 있다. **인프라 자체는 완전히 정상 동작**한다.
- 식별자 질의는 BM25(sparse) 성분이 강하게 기여하므로 Recall@10=1.000 은 하이브리드 검색 전체의
  성능이며, **로컬 해싱 임베더(dense 단독)의 의미 기반 검색 품질까지 증명하지는 않는다** — 진짜
  파라프레이즈(동의어/문맥) 질의에 대한 dense 전용 성능은 별도 로드맵인 "임베딩 모델 교체"
  (sentence-transformers/OpenAI, §9.5)에서 재평가 필요. 이번 실측은 **§7.5.1 이 목표한 인프라
  실측**을 완결한 것으로, PRD 부록 B/§5 의 수치가 더 이상 전량 `가정:` 이 아님을 의미한다.

## 전체 회귀
- sqlite 경로(impl/4 15/15, impl/15 6/6) 재실행 — 전부 PASS, pgvector 경로 활성화가 sqlite 세션에
  영향 없음 확인.
- 마이그레이션 로그에 초기 부팅 시 "relation ... does not exist" 경고 다수 출력됨(컬럼 마이그레이션
  루프가 01_init.sql 실행 전에 먼저 시도되는 기존 순서 때문, `app/db.py` 기존 설계) — 무해하며
  최종적으로 스키마 정상 생성됨(본 시험으로 확인). 별도 조치 불필요.

## 정리
- `docker compose stop postgres` 로 컨테이너 정지(볼륨 보존, 재기동 시 재사용 가능).
- `docker-compose.yml` 이미지 교체는 **영구 반영**(임시 우회 아님) — 향후 postgres 프로파일
  기동 시 자동으로 pgvector 지원.

## 미결/후속
- 임베딩 모델 교체(sentence-transformers/OpenAI) 후 파라프레이즈 질의 세트로 dense 단독 성능
  재평가 필요(§9.5, 이번 범위 밖).
- mTLS 핸드셰이크, 실 wise-Guardrails MCP 통합은 여전히 별도 인프라 필요(§9.5 잔여).
