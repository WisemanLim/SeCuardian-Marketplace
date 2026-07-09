# 시험 시나리오 — impl/29(물리 test/impl/27): F-WF webhook 보안 강화

> 논리 순번은 impl/29(직전 impl/28=Dify DSL Import, 물리 test/impl/26). 물리 디렉터리는
> `test/impl/*` 자동증가값(27). PRD §7.2.4.1 근거.

- 대상: `app/routers/router_workflow.py`(`_fernet`/`_encrypt_secret`/`_decrypt_secret`/
  `_verify_hmac_signature`/`_rate_limited`/`rotate_webhook_secret`/`trigger_webhook` 갱신),
  `app/core/config.py`(`workflow_webhook_rate_limit_per_min`), 프론트 `WorkflowPage.tsx`
  (재발급 버튼)·`api/workflow.ts`(`rotateWebhookSecret`).

## 검증 항목

1. **저장 방식 전환** — 신규 webhook 워크플로우는 `webhook_secret_enc`(Fernet)로 저장,
   응답 어디에도(`create`/`get`/`list`/`rotate`) 노출되지 않음(암호문·평문 모두).
2. **로테이션** — `POST /trigger/webhook/rotate`(admin/supervisor):
   - 신규 평문 시크릿 응답에 1회 노출.
   - **구 시크릿은 즉시 무효**(로테이션 후 구 시크릿으로 트리거 시도 → 401).
   - 신규 시크릿으로는 정상 트리거(201).
   - `trigger_type != "webhook"` 대상 → 409.
   - user 권한 → 403.
3. **HMAC 서명 검증** — `X-Webhook-Signature: sha256=<hmac-sha256(secret, raw_body)>`:
   - 올바른 서명 → 201(트리거 성공), **`X-Webhook-Secret` 헤더 없이도** 통과.
   - 잘못된 서명 → 401.
   - 서명 계산에 사용한 raw body 가 실제 저장되는 input_json 과 일치.
4. **하위호환** — 기존 `X-Webhook-Secret` 직접비교 방식도 계속 동작(둘 중 하나만 유효하면 통과).
5. **rate limit** — 워크플로우별 `settings.workflow_webhook_rate_limit_per_min` 초과 시 429.
   인증 실패 시도도 카운트됨(무차별대입 완화 확인).
6. **회귀** — `test/impl/24`(impl/26, 15/15) 가 코드 변경 없이 그대로 PASS(블랙박스 계약 유지 확인).
   `test/impl/2`·`23`·`26` 도 재확인.
7. **프론트** — `tsc --noEmit`·`vite build` 0오류(완료), 재발급 버튼 정적 검증.

## 판정 기준
전 항목 PASS + test/impl/2·23·24·26 회귀 PASS.
