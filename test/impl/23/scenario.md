# 시험 시나리오 — impl/25(물리 test/impl/23): F-WF 컴포넌트 팔레트 + agent 노드 실호출 + http 노드

> 물리 디렉터리 번호(23)는 기존 `test/impl/*` 스캔 자동증가값. PRD 변경이력 상의 논리 순번은
> impl/25(직전 impl/24=화면정렬은 물리 test/impl/22, impl/23=Guardrails classifier는 물리
> test/impl/21 을 재사용해 물리·논리 번호가 이미 어긋나 있었음 — 신규 물리 디렉터리와 충돌 방지 목적).

- PRD 근거: §7.2.3 (사용자 요구, 2026-07-09) — "내장/시스템/Addon 에이전트의 세부 기능을 컴포넌트로
  사용 가능하게 하라(예: A에이전트-조회)".
- 대상: `app/services/workflow_engine.py`, `app/routers/router_workflow.py`,
  `front/src/api/workflow.ts`, `front/src/pages/workflow/WorkflowPage.tsx`.

## 검증 항목

1. `GET /api/workflow/components` — 인증 없으면 401/403, 있으면 200 + 리스트.
   - `marketplace`/`guardrails` 등 내장 에이전트의 엔드포인트가 `category=builtin` 으로 존재.
   - 각 컴포넌트가 `agent_key/agent_name/category/method/path/capability_key/label` 필드를 가짐.
   - `label` 형식이 `{agent_name}-{capability_key}`.
   - addon 전용 prefix(`/api/addon/...`)는 `tbl_agent_config` 경로에서 제외되고
     `tbl_addon_agents` 경로로만 잡힘(카테고리 `addon`).
2. **agent 노드 실호출** — `config.path` 지정 시 실제 API를 호출:
   - `GET /api/marketplace/catalog` 를 가리키는 agent 노드로 워크플로우 실행 → `status=200`,
     `body` 가 실제 API 응답(list/object)과 일치.
   - 실패 응답(404 등)이면 노드 실패 → run failed.
3. **하위호환** — `config.path` 미지정 시 기존 스텁 동작(`{"agent_key":..., "invoked": True, "input":...}`)
   그대로 유지(test/impl/2 케이스 재확인 겸 회귀).
4. **actor 토큰 권한 상승 방지** — RBAC 이 필요한 내부 API(예: admin/supervisor 전용)를
   일반 user 토큰으로 실행한 워크플로우가 agent 노드로 호출하면, 워크플로우 자체는 실행됐어도
   내부 호출은 403 을 받아 **run 이 failed** 로 종료됨(actor 권한 이상으로 동작하지 않음 확인).
5. **http 노드** — 신규 노드 타입이 `NODE_TYPES`/검증(422 아님)에 포함되고, `_http_call` 을
   monkeypatch 해 실행 결과가 `{status, body}` 로 반영됨. 4xx/5xx 응답 시 노드 실패.
6. **회귀** — `test/impl/2/test_workflow.py` 21/21 PASS 유지(위에서 별도 재확인 완료).
7. **프론트** — `tsc --noEmit` 0 오류(위에서 별도 확인 완료), `WorkflowComponent`/`listComponents`/
   `ComponentPalette` 정적 검증(런타임 브라우저 시험은 API 계약 시험으로 대체 — 기존 impl/3·18 관례 준용).

## 판정 기준
전 항목 PASS + 기존 test/impl/2 회귀 PASS.
