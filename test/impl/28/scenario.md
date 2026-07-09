# 시험 시나리오 — impl/30(물리 test/impl/28): F-WF `enabled` 토글 PATCH 엔드포인트

> 논리 순번은 impl/30(직전 impl/29=webhook 보안 강화, 물리 test/impl/27). 물리 디렉터리는
> `test/impl/*` 자동증가값(28). PRD §7.2.7 근거.

- 대상: `app/routers/router_workflow.py`(`update_workflow`), 프론트 `WorkflowPage.tsx`
  (활성화/비활성화 버튼)·`api/workflow.ts`(`setWorkflowEnabled`).

## 검증 항목

1. **정상 토글** — `PATCH /api/workflows/{id}` `{"enabled": false}` → `enabled=false` 반영,
   이후 `{"enabled": true}` → 다시 `true`.
2. **RBAC** — user 권한 → 403.
3. **미존재 워크플로우** — 404.
4. **부수 효과 없음** — 토글 후 `definition_json`/`name`/`trigger_type` 등 다른 필드 불변.
5. **실사용 흐름 연결** — Dify 가져오기(§7.2.6, 항상 `enabled=false`)로 만든 워크플로우를
   PATCH 로 활성화한 뒤 정상 `run` 가능(§7.2.6·§7.2.7 통합 확인).
6. **비활성화 후 실행 차단** — `enabled=false` 로 되돌리면 `/run` 이 다시 409.
7. **회귀** — 백엔드 CRUD 스키마 무변경(컬럼 추가 없음)이므로 `test/impl/2`·`23`·`24`·`26`·`27`
   재실행으로 사이드이펙트 없음 확인.
8. **프론트** — `tsc --noEmit`·`vite build` 0오류(완료), 토글 버튼 정적 검증.

## 판정 기준
전 항목 PASS + test/impl/2·23·24·26·27 회귀 PASS.
