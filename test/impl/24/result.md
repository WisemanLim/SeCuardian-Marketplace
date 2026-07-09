# 시험 결과 — impl/26(물리 test/impl/24): F-WF webhook 수신 트리거

- 날짜: 2026-07-09
- 판정: **PASS** (15/15 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian-Marketplace/.venv`

## 실행 결과
```
PASS seed real user sup1 (201, ...)
PASS create webhook workflow (201)
PASS webhook_secret present in create response (True)
PASS hash not leaked in create response
PASS no secret/hash on refetch ({})
PASS missing secret -> 401 (401)
PASS wrong secret -> 401 (401)
PASS correct secret, no JWT -> 201 (201)
PASS webhook run completed (completed)
PASS agent node real call via creator role ({'agent_key': 'marketplace', 'invoked': True, 'status': 200, 'body': {'assets': []}})
PASS trigger_source=webhook recorded (webhook)
PASS manual workflow webhook trigger -> 404 (404)
PASS disabled workflow -> 409 (409)
PASS unknown creator run created (201)
PASS unknown creator -> node call fails safely, run failed (failed)

=== RESULT: ALL PASS
```

## 검증 항목
- 시크릿 발급: `trigger_type="webhook"` 생성 응답에만 평문 노출, 재조회(`GET`)에는 시크릿·해시 둘 다 없음.
- 트리거 인증: `X-Webhook-Secret` 미지정/오지정 401, 정상 시크릿 201(JWT 불필요).
- 스코프 검증: `trigger_type != "webhook"` 대상 404, `enabled=false` 대상 409.
- **actor 신원 상속**: 생성자(`sup1`, 실 `tbl_users` 행 보유)의 역할로 `agent` 노드 실 API 호출 성공.
- **안전한 실패**: 생성자가 `tbl_users` 에 없는 경우(phantom-sup) actor 토큰 미발급 → 해당 노드만 실패,
  run 전체가 `failed` 로 안전 종료(권한 상승 없음, 크래시 없음).

## 전체 회귀
- `test/impl/2` 21/21, `test/impl/23` 18/18 PASS — 회귀 없음.
- 전체 impl/1~24 재실행 — 전부 PASS.
- `ruff check app/routers/router_workflow.py test/impl/24/` — 0 오류.
- 프론트 `tsc --noEmit` — 0 오류.

## 미결/후속 (PRD §7.2.4·§9.5 유보)
- 시크릿 로테이션 엔드포인트 없음(재발급은 워크플로우 재생성으로 대체) — 사용성 갭, 로드맵.
- HMAC 페이로드 서명, rate limiting 없음 — 운영 시 리버스프록시 레벨 완화 권장(§6 리스크 기록).
- 워크플로우 `enabled` 토글용 PATCH 엔드포인트가 아직 없어(§9.5 기존 갭), 시험에서 DB 직접 조작으로
  disabled 케이스를 재현 — 향후 PATCH 엔드포인트 추가 시 이 갭도 함께 해소 가능.
