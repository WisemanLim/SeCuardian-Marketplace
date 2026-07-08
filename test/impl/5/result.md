# 시험 결과 — impl/5

- 날짜: 2026-07-08
- 판정: **PASS** (백엔드 13/13 + 프론트 tsc 0오류)

## 백엔드 실행 결과
```
PASS playground agent seeded
PASS run 201
PASS degrade provider on unreachable ollama (degraded)
PASS degrade text echoes prompt
PASS no citations without rag_collection_id ([])
PASS latency recorded
PASS no RBAC gate on run (plain user allowed)
PASS rag-augmented run 201
PASS citations populated
PASS citation matches injected doc
PASS missing rag collection -> 404
PASS history = 2 runs (2)
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- Ollama 장애/미가동 시 `provider=degraded` 텍스트로 무중단 완료(PRD §7.11.1 준용).
- RAG 컬렉션 지정 시 `hybrid_search` 결과가 `citations_json` 에 채워지고 프롬프트에 컨텍스트로 주입.
- 실험 도구 특성상 RBAC 게이트 없음(모든 인증 사용자 실행 가능) — 등록/설치형 자산(F-MP/F-WF/F-RAG)과 의도적으로 다른 권한 모델.
- boot 23 routes, `ruff check` 0 오류, 프론트 `tsc --noEmit` 0 오류.

## 미결/후속
- 비용(cost) 추적 미구현 — Claude API 키 미구성 환경 기준, Ollama 만 무료 로컬 실행이라 실질적 비용 데이터 없음. Claude 연동 시 추가.
- eval(정량 평가 세트) 실행은 로드맵.
- 프론트 브라우저 E2E 클릭 시험 미실시.
