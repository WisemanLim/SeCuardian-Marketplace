# 시험 결과 — impl/25(물리 test/impl/23): F-WF 컴포넌트 팔레트 + agent 노드 실호출 + http 노드

- 날짜: 2026-07-09
- 판정: **PASS** (18/18 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian-Marketplace/.venv`

## 실행 결과
```
PASS no token -> 401/403 (401)
PASS components 200 (200)
PASS components non-empty (27)
PASS component has required fields
PASS label format
PASS marketplace catalog component present ([...])
PASS marketplace category=builtin (builtin)
PASS no addon-prefix leak into non-addon category ([])
PASS real agent call run completed (completed)
PASS real agent call status 200 (200)
PASS real agent call body parsed as JSON (<class 'dict'>)
PASS legacy stub unchanged ({'agent_key': 'chat', 'invoked': True, 'input': {}})
PASS user can run (workflow itself allows any authed user, 201)
PASS actor(user) lacks admin -> node call 403 -> run failed (failed)
PASS http node run completed (completed)
PASS http node output ({'status': 200, 'body': {'echo': ..., 'method': 'POST'}})
PASS http node 5xx -> run failed (failed)
PASS http node type passes validation (201)

=== RESULT: ALL PASS
```

## 검증 항목
- `GET /api/workflow/components` — 인증 게이트, 내장/시스템/Addon 3분류, 필드 형태, `label` 포맷.
- Orchestrator 의 기존 OpenAPI 동적 탐지(`_probe_prefix`/`_openapi_paths`) 재사용 확인(신규 스캐너 없음).
- `agent` 노드 — `config.path` 지정 시 `_exec_api_call` 재사용으로 실 API 호출, 응답 `{status, body}` 반영.
- **하위호환**: `config.path` 미지정 시 v1 스텁(`{agent_key, invoked, input}`) 그대로 유지.
- **actor-scoped 권한**: 워크플로우 실행자(user)가 admin 전용 API를 컴포넌트로 호출하면 내부 403 →
  NodeError → run failed(권한 상승 불가 확인).
- 신규 `http` 노드 — `_http_call` monkeypatch 로 실행/에러(5xx→failed) 검증, NODE_TYPES 검증(422 아님).

## 전체 회귀
- `test/impl/2` 21/21 PASS(기존 agent 노드 스텁 케이스 포함) — 회귀 없음.
- 전체 impl/1~23 재실행 — 전부 PASS(신규 코드가 마켓플레이스/가드레일/RAG/플레이그라운드 등
  기존 기능에 부작용 없음).
- 백엔드: `ruff check app/services/workflow_engine.py app/routers/router_workflow.py test/impl/23/` — 0 오류.
- 부팅: `import app.main` boot OK, routes=26(신규 라우트 없음 — 기존 `/api` 워크플로우 라우터 내 경로 추가).
- 프론트: `tsc --noEmit` 0 오류.

## 미결/후속 (PRD §7.2.3·§9.5 유보)
- 편집형(드래그) 워크플로우 캔버스 — 현재 캔버스는 읽기전용 시각화, 컴포넌트 팔레트+a11y 폼이 1차 편집 수단.
- Dify DSL Import 어댑터(모드 A) — §7.2.2 기존 설계, 로드맵 P5 유지.
- webhook 수신 트리거·code 노드 — `trigger_type` 필드는 있으나 외부 HTTP 수신 엔드포인트 미구현,
  code 노드는 샌드박스 보안 검토 선행 필요.
- `http` 노드 SSRF 완화(URL allow-list·사설대역 차단)는 admin-trust 경계로 1차 대응, 강한 통제는 로드맵(P5 하드닝).
