# 시험 시나리오 — impl/7: F-GRD Orchestrator 게이트 배선 (`guardrails_gate.py`, PRD §7.8.4)

- 날짜: 2026-07-08
- 대상: impl/6 에서 잔여로 남긴 "Orchestrator 실시간 게이트 배선" — PRD §9.5 다음단계 1순위.
- 실행: `PYTHONPATH=. python test/impl/7/test_guardrails_gate.py`

## 설계
- `app/agents/orchestrator.py` 는 **무변경**(PRD §3 준용 원칙). `_exec_api_call` 은 모듈 내부에서
  이름으로 호출되므로(전역 조회), `app/agents/guardrails_gate.py` 가 `orch._exec_api_call` 속성을
  게이트 래퍼로 재바인딩해 6곳의 내부 호출 지점을 소스 수정 없이 가로챈다.
- `main.py` lifespan 에서 `addon_init` 직후 `guardrails_gate.install()` 1회 호출.
- 대상 에이전트는 REST 경로에서 추론(`/api/addon/{key}/...` → key, 내장 에이전트 경로 → 고정 key).
  `agent_guardrail_config` 에 `global`+enabled=1 행이 없으면 게이트 통과(기본 off).
- 입력(io_scope=input/both): 요청 바디를 JSON 직렬화해 판정 → `redact`/`sanitize` 시 재파싱해 치환,
  `block`/`escalate` 시 원 호출 자체를 생략하고 `HTTP 403 [BLOCKED]` 반환.
- 출력(io_scope=output/both): 응답 텍스트에 동일 판정 적용.
- 판정마다 `guardrails_decision_log` 이중 기록.
- 예외/미설정 시 항상 원 호출로 폴백(무중단).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 0 | 부팅 시 게이트 설치 확인 | `orch._guardrails_gate_installed = True` |
| 1 | `orchestrator.py` 소스에 guardrails 참조 없음 | 원본 무변경 검증 |
| 2 | PII 포함 입력(marketplace, global on, both) | redact 정책 → 201(차단 아님), 응답에 원문 PII 없음 |
| 3 | 실제 저장된 값 확인 | 자산은 생성됨, description 에 마스킹된 값 저장(입력측 치환이 실제 반영됨) |
| 4 | decision_log | 입력측(redact,matched=1) + 출력측(allow,matched=0, 이미 마스킹된 텍스트라 재매치 없음) 2건 |
| 5 | 깨끗한 입력 | 정상 통과·생성 |
| 6 | 토글 OFF 후 동일 PII 입력 | 그대로 통과(정합성 — 요구사항 3) |
| 7 | 미토글 에이전트(workflow) | 영향 없음(에이전트별 격리) |
| 8 | 에이전트 추론 불가 경로(`/health`) | 무크래시 패스스루 |
| 9 | `GUARDRAILS_ENABLED=false` | 전체 우회 |

## 판정 기준
- 15개 assert 전부 PASS + 기존 impl/1,2,4,5,6 전체 회귀 PASS + boot/ruff 무영향 = PASS.
