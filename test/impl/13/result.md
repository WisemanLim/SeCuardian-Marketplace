# 시험 결과 — impl/13

- 날짜: 2026-07-08
- 판정: **PASS** (6/6) + impl/6·7·11 회귀 무영향

## 실행 결과
```
PASS MCP 미설정 -> local (local,redact)
PASS MCP 정상 -> source=mcp, MCP 결정 (mcp,escalate)
PASS MCP 응답 필드 정규화
PASS MCP 실패 -> local-fallback + 로컬 승격 (local-fallback,block)
PASS /test MCP 미설정 -> local source (local)
PASS /test 로컬 판정 정상
=== RESULT: ALL PASS
```

## 검증 항목
- MCP Server(:8080) `POST /mcp/tools/validate_input|validate_output` 호출 계약(§7.8.2) + x-api-key 인증.
- **자동 폴백(§7.8.6)**: 미설정/연결실패/타임아웃 시 로컬 판정기로 무중단 전환, `source` 로 경로 표기.
- MCP 판정 우선(escalate 등 서버 결정 반영), 응답 필드(redactedText·policyVersion·latencyMs) 정규화.
- 게이트·`/test` 모두 MCP 경로로 통일 — 기존 로컬 동작은 미설정 폴백으로 100% 보존(회귀 무영향).
- `ruff check` 0오류.

## 미결/후속
- 실 wise-Guardrails MCP Server 대상 통합 시험은 해당 서비스 가동 필요(현재 monkeypatch 로 계약 검증).
- `explain_decision` 의 MCP 프록시(Audit Service `decision_events` 조회)는 SeCMP 자체 `guardrails_decision_log` 사용 중 — MCP explain 연동은 후속 선택.
