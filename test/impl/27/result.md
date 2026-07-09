# 시험 결과 — impl/29(물리 test/impl/27): F-WF webhook 보안 강화

- 날짜: 2026-07-09
- 판정: **PASS** (12/12 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian-Marketplace/.venv`,
  `WORKFLOW_WEBHOOK_RATE_LIMIT_PER_MIN=5`(시험 재현용 저한도)

## 실행 결과
```
PASS enc not leaked in create response
PASS valid HMAC signature -> 201 (201)
PASS raw body preserved as input ({"event": "deploy"})
PASS invalid HMAC signature -> 401 (401)
PASS legacy X-Webhook-Secret still works -> 201 (201)
PASS user rotate -> 403 (403)
PASS rotate -> 201 (201)
PASS rotated secret differs from original
PASS old secret invalidated after rotate -> 401 (401)
PASS new secret works -> 201 (201)
PASS rotate on manual workflow -> 409 (409)
PASS rate limit triggers 429 within extra bursts ([429, 429, 429, 429, 429, 429])

=== RESULT: ALL PASS
```

## 검증 항목
- 저장 전환(bcrypt→Fernet) — 암호문·평문 모두 어떤 응답에도 노출 없음.
- 로테이션 — 신규 평문 1회 노출, **구 시크릿 즉시 무효**, RBAC(user 403)·스코프(manual 409) 검증.
- HMAC 서명(`X-Webhook-Signature`) — 유효 서명 통과(시크릿 헤더 없이), 무효 서명 401,
  서명 대상 raw body 가 실제 저장 input과 일치.
- 하위호환 — 기존 `X-Webhook-Secret` 직접비교 방식 그대로 동작(impl/26 연동 무변경).
- rate limit — 저한도 설정으로 429 재현, 인증 실패 시도도 카운트됨(무차별대입 완화).

## 전체 회귀
- `test/impl/24`(impl/26, 15/15) — **코드 변경 없이 그대로 PASS**(블랙박스 계약 유지 확인, 내부
  구현이 bcrypt→Fernet 로 바뀌었어도 외부 동작 무변화).
- 전체 impl/1~27 재실행 — 전부 PASS.
- `ruff check app/ test/impl/27/` — 0 오류(main.py 기존 E402 만 잔존, 무관).
- 프론트 `tsc --noEmit`·`vite build` — 0 오류.

## 변경 요약
- `app/core/config.py`: `workflow_webhook_rate_limit_per_min: int = 30`.
- `app/routers/router_workflow.py`: `_fernet`/`_encrypt_secret`/`_decrypt_secret`/
  `_verify_hmac_signature`/`_rate_limited`(인메모리 dict) 헬퍼, `rotate_webhook_secret`
  신규 엔드포인트, `trigger_webhook` 이 `Request` 로 raw body 를 받아 HMAC 검증 지원.
- 프론트: `api/workflow.ts`(`rotateWebhookSecret`), `WorkflowPage.tsx`("시크릿 재발급" 버튼,
  webhook 트리거 워크플로우에만 노출, 기존 1회노출 배너 재사용).

## 미결/후속 (PRD §7.2.4.1·§9.5 유보)
- rate limit 은 **인메모리·단일 프로세스 한정** — 멀티 워커/인스턴스 배포 시 워커별 독립 카운트.
  강한 보장 필요 시 리버스프록시/API 게이트웨이 레벨 rate limit 병행 권장.
- Fernet 키가 `JWT_SECRET_KEY` 파생 — `JWT_SECRET_KEY` 로테이션 시 기존 webhook 시크릿 전부
  무효화(재발급 1회 필요, 운영 절차 문서화 필요).
- impl/26 에서 이미 발급된(구 `webhook_secret_hash` 필드) 워크플로우는 본 변경 이후 검증 실패 —
  재발급 1회 필요(로컬/개발 단계라 실사용 영향 없음, 별도 마이그레이션 스크립트 미작성).
