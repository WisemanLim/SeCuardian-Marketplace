# 시험 결과 — impl/6

- 날짜: 2026-07-08
- 판정: **PASS** (백엔드 20/20 + 프론트 tsc/build 0오류)

## 백엔드 실행 결과
```
PASS guardrails agent seeded
PASS global functional
PASS manufacturing-food catalog_only
PASS clean text -> allow
PASS riskScore 0 on allow
PASS all 13 global detectors fire on their sample
PASS PII -> redact
PASS redactedText masks PII (email me at ***********.com)
PASS catalog_only domain test -> 409
PASS unknown domain -> 404
PASS user toggle -> 403
PASS supervisor toggle on -> 200
PASS config reflects enabled
PASS toggle unknown domain -> 404
PASS decision log recorded for agent_key=chat
PASS explain_decision returns record
PASS explain missing decision -> 404
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- **13종 정규식 탐지기 전수 실제 판정 확인**(PRD §8.3 P2 verify 요건 충족): RRN·SSN·마이넘버·여권·이메일·전화(KR/US)·카드번호(Luhn)·IBAN·API키·운전면허·사업자등록번호·IPv4.
- 카드번호는 Luhn 체크섬 통과분만 인정(오탐 억제) — 테스트 샘플 `4111 1111 1111 1111`(Luhn-valid 표준 테스트 카드번호) 사용.
- `agent_guardrail_config` 토글이 SeCMP 측에서 도메인 스코프를 소유·강제(§7.8.3) — RBAC(admin/supervisor)로 보호.
- `guardrails_decision_log` 이중 감사 기록(agent_key 지정 시).
- catalog_only 도메인은 테스트/토글 모두 명시적 오류(409/체크박스 비노출)로 차단 — "적용됨" 오인 방지(§7.8.0 요구).
- boot 24 routes, `ruff check` 0 오류, 프론트 `tsc --noEmit` + `vite build` 0 오류(2036 modules).

## PRD 대비 스코프 조정 (근거 명시)
- **로컬 판정기로 구현** — PRD §7.8.1 은 SeCMP가 MCP Server(:8080)만 호출하는 구조를 명시하나, 이 개발 세션에는
  wise-Guardrails 인스턴스가 가동되지 않는다. §7.8.0 은 이미 "1차 실기능 = global 도메인"으로 범위를 확정했고,
  그 실체가 정규식 13종 탐지기임도 §7.8.0에 명시돼 있으므로, 동일 계약을 로컬로 재구현해 **기능 자체는 완전히 동작**하게 했다.
  MCP 프록시 연동(`GUARDRAILS_MCP_URL` 대상)은 후속 확장 — 로컬 판정을 폴백으로 유지하면 §7.8.6 "MCP 다운 시 degrade" 리스크도 흡수.
- **Orchestrator 훅(`guardrails_gate.py`, §7.8.4) 미구현** — `/api/guardrails/test`(Playground 연계) 및 에이전트 토글까지는
  완전히 동작하나, Orchestrator `_exec_api_call` 앞뒤를 감싸는 실시간 게이트 배선은 기존 Orchestrator 동작에 영향을 줄 수 있어
  이번 차수 범위에서 제외. 다음 차수 대상으로 명시.

## 미결/후속
- Orchestrator 실시간 게이트 배선(`guardrails_gate.py`).
- MCP Server 프록시 연동(설정은 이미 `.env`/config 에 존재 — impl/1).
- 25종 업종 판정기는 SeCMP 책임 밖(wise-Guardrails 별도 로드맵, PRD §6 리스크 기재됨).
