# 시험 결과 — impl/2

- 날짜: 2026-07-08
- 판정: **PASS** (21/21 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian/.venv`

## 실행 결과
```
PASS workflow agent seeded (['general', 'chat', 'marketplace', 'workflow'])
PASS user create -> 403
PASS bad node type -> 422
PASS edge unknown node -> 422
PASS linear run completed
PASS transform resolved $ref ({'msg': 'world'})
PASS notify rendered template ({'message': 'hi world'})
PASS cond run completed
PASS true branch fired, false pruned (['t', 'c', 'hi'])
PASS node runs: hi run, lo not
PASS false branch fired (['t', 'c', 'lo'])
PASS hitl pauses (waiting_hitl)
PASS user hitl -> 403
PASS hitl approve -> completed
PASS hitl reject -> failed
PASS agent node invoked ({'agent_key': 'chat', 'invoked': True})
PASS missing agent -> run failed
PASS retry exhausted 4 attempts
PASS cancel waiting run
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- DAG 상태머신: pending→running→(waiting_hitl)→completed|failed|cancelled 전이 확인.
- 분기 의미론: condition true/false 에 따라 한쪽 fire·다른쪽 prune(노드런 미생성).
- HITL: 일시정지→승인 재개(완료 노드 캐시 재사용, 결정적)→completed / 거부→failed.
- retry: 실패 노드 `max_attempts = workflow_node_max_retries(3)+1 = 4` 소진 후 run failed.
- 템플릿/참조: `$a.b.c` 해석 + `{{a.b}}` 렌더.
- RBAC: 생성·승인·취소 admin/supervisor 강제.
- boot: routes 20→21 (workflow 라우터 포함), `ruff check` 신규파일 0 오류.

## 미결/후속 (범위 밖)
- SSE stream 은 노드/최종 상태 스냅샷 방식(실시간 push 아님) — 실행이 요청 내 동기 완료되므로 1차 충분. 장기실행/비동기 워커는 로드맵.
- llm 노드는 Ollama 폴백(`call_ollama`) 사용, 미구성 시 degrade — 실 LLM 통합은 F-AI 공유 `generate` 후속.
- 프론트 화면(`front/src/pages/workflow/`) 미구현.
- loop/sub-flow, cron 트리거 유보(PRD §7.2.1).
