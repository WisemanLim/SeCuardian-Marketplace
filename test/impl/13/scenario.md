# 시험 시나리오 — impl/13: F-GRD MCP Server 프록시 연동 (PRD §7.8.1/§7.8.2)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "F-GRD MCP Server 프록시 연동". wise-Guardrails MCP Server(:8080) 호출 + 로컬 폴백.
- 실행: `PYTHONPATH=. python test/impl/13/test_guardrails_mcp.py` (httpx monkeypatch 로 MCP 시뮬레이션)

## 범위
- `app/services/guardrails_mcp.py` — `validate(text, domain, tool)`: `guardrails_mcp_url` 설정 시
  `POST /mcp/tools/{validate_input|validate_output}`(x-api-key), 미설정/실패/타임아웃(3~5s) 시 로컬 `decide` 폴백(§7.8.6).
  응답 §7.8.2 ValidateResponse 정규화 + `source`("mcp"|"local"|"local-fallback") 표기.
- `router_guardrails.py /test`, `guardrails_gate.py`(입력/출력 훅) 를 `decide` 직접호출 → `validate`(MCP 경로)로 전환.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | MCP 미설정 | source=local, 로컬 판정 |
| 2 | MCP 정상 응답 | source=mcp, MCP 결정(escalate) 반영 |
| 3 | MCP 응답 필드 정규화 | redactedText/policyVersion 매핑 |
| 4 | MCP 연결 실패 | source=local-fallback + 로컬 승격(block) |
| 5 | `/test` 미설정 | source=local |
| 6 | `/test` 로컬 판정 | redact |

## 판정 기준
- 6개 assert 전부 PASS + 기존 impl/6·7·11 회귀(MCP 미설정=로컬 동일) 무영향 = PASS.
