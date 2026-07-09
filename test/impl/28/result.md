# 시험 결과 — impl/30(물리 test/impl/28): F-WF `enabled` 토글 PATCH 엔드포인트

- 날짜: 2026-07-09
- 판정: **PASS** (11/11 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian-Marketplace/.venv`

## 실행 결과
```
PASS created enabled by default (True)
PASS unknown workflow -> 404 (404)
PASS user toggle -> 403 (403)
PASS disable ok (200, False)
PASS other fields unchanged after disable
PASS run while disabled -> 409 (409)
PASS re-enable ok (True)
PASS run after re-enable -> completed (completed)
PASS dify import disabled by default (False)
PASS dify-imported workflow enabled via PATCH (True)
PASS dify-imported workflow runs after enable (completed)

=== RESULT: ALL PASS
```

## 검증 항목
- `PATCH /api/workflows/{id}` `{"enabled": bool}` 정상 토글, RBAC(user 403), 404, 부수효과 없음(다른
  필드 불변).
- 토글 결과가 실제 `/run` 게이트(409 disabled)에 반영됨을 양방향으로 확인.
- **impl/28(Dify DSL Import)+impl/30(enabled 토글) 통합 흐름** — 항상 비활성으로 가져온 워크플로우를
  PATCH 로 활성화한 뒤 정상 실행까지 end-to-end 확인(§7.2.6·§7.2.7 연계).

## 전체 회귀
- 전체 impl/1~28 재실행 — 전부 PASS(스키마 컬럼 추가 없음 — `enabled` 컬럼은 기존 그대로 사용).
- `ruff check test/impl/28/` — 0 오류.
- 프론트 `tsc --noEmit`·`vite build` — 0 오류.

## 변경 요약
- `app/routers/router_workflow.py`: `WorkflowUpdate` 모델 + `PATCH /workflows/{id}`
  (`update_workflow`) — 1차 범위는 `enabled` 토글만.
- 프론트: `api/workflow.ts`(`setWorkflowEnabled`), `WorkflowPage.tsx`(워크플로우 행에
  "활성화"/"비활성화" 버튼 추가).

## 미결/후속
- 이름/정의(`definition_json`)/트리거 설정 등 전체 편집 PATCH는 범위 밖(§7.2.7 결정대로) — 필요 시
  별도 반복.
