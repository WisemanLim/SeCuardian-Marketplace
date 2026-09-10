# impl/55 시험 시나리오 — E11 거버넌스 (HITL 승인 + OWASP 스코어카드)

대상: `router_governance`(`/api/governance`) + `tbl_hitl_approvals`(01_init 멱등, 양 방언). add-only.
실행: `.venv/bin/python test/impl/55/test_governance.py` (fresh sqlite, 실 TestClient — 마이그레이션 실행).

| TC | 수용 기준 |
|---|---|
| OWASP scorecard | `GET /owasp-scorecard` 200, controls 10종(LLM01~10), LLM08=HITL 게이트 score≥4, summary avg/target=4 |
| HITL create | `POST /hitl` {action:delete} → 201 pending, high_impact=true |
| HITL 검증 | 잘못된 action 422 |
| HITL list | `GET /hitl?status=pending` → pending_count≥1 |
| HITL 권한 | 일반 user approve → 403 |
| HITL approve | supervisor approve → 200 approved, decided_by 기록 |
| HITL 재처리 | 이미 처리된 건 재approve → 409 |
| HITL 없는 id | 999999 reject → 404 |
| HITL reject | {action:external} 생성 후 reject → 200 rejected |
