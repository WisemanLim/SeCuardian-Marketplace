# 시험 시나리오 — impl/26(물리 test/impl/24): F-WF webhook 수신 트리거

> 논리 순번은 impl/26(직전 impl/25=컴포넌트 팔레트, 물리 test/impl/23). 물리 디렉터리는
> `test/impl/*` 자동증가값(24). PRD §7.2.4 근거.

- 대상: `app/routers/router_workflow.py`(`create_workflow`/`_wf_out`/`trigger_webhook`/
  `_actor_token_for_creator`), `front/src/api/workflow.ts`, `front/src/pages/workflow/WorkflowPage.tsx`.

## 검증 항목

1. **시크릿 발급** — `trigger_type="webhook"` 워크플로우 생성 시 응답에 `webhook_secret`(평문) 포함.
   재조회(`GET /workflows/{id}`, `GET /workflows`)에는 `webhook_secret`도 `webhook_secret_hash`도 노출되지 않음.
2. **트리거 인증** — `POST /workflows/{id}/trigger/webhook`:
   - 시크릿 미지정/오지정 → 401.
   - 올바른 시크릿(`X-Webhook-Secret`) → 실행, `trigger_source="webhook"` 로 run 기록.
   - `trigger_type != "webhook"`(manual 워크플로우) 대상 호출 → 404.
   - `enabled=false` 워크플로우 → 409.
3. **JWT 불필요** — `Authorization` 헤더 없이도(시크릿만으로) 트리거 가능.
4. **actor 신원 상속** — webhook 트리거 run 안의 `agent` 노드가 컴포넌트를 실제로 호출할 때,
   워크플로우 **생성자(admin/supervisor)의 역할**로 동작(예: `GET /api/marketplace/catalog` 성공).
   생성자를 찾을 수 없는 경우(비정상 `created_by`) 실호출 노드는 인증 실패로 그 노드만 실패
   (권한 상승 없이 안전하게 실패).
5. **하위호환** — `trigger_type="manual"`(기본값) 생성 흐름은 impl/2·25 시험과 동일하게 유지
   (webhook 관련 필드 없음, 회귀 무영향).
6. **프론트** — `tsc --noEmit` 0 오류(완료), 트리거 타입 선택 UI·시크릿 1회 배너 정적 검증
   (기존 impl/3·18·25 관례대로 브라우저 시험은 API 계약 시험으로 대체).

## 판정 기준
전 항목 PASS + test/impl/2·23 회귀 PASS.
