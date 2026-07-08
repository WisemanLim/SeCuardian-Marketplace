# 시험 시나리오 — impl/6: F-GRD (Guardrails) 백엔드+프론트

- 날짜: 2026-07-08
- 대상: 거버넌스 에이전트 (F-GRD, PRD §7.8) — v0 백엔드 없음(전무) → PRD §7.8 계약 기반 신규 구현
- 실행: `PYTHONPATH=. python test/impl/6/test_guardrails.py`

## 설계 결정 (PRD §7.8.0 준용)
- **1차 실기능 범위 = `global`(PII/신용정보) 도메인만.** wise-Guardrails 는 이 세션 환경에 실행 중이 아니고,
  PRD §7.8.0 은 업스트림도 25개 업종 규칙셋이 "데이터만 존재, 판정기 없음"이라 명시한다.
  따라서 `app/services/guardrails_detector.py` 에 업스트림 `register_global_privacy()` 계약과 동일한
  **13종 정규식 탐지기**(주민번호·SSN·마이넘버·여권·이메일·전화KR/US·카드번호+Luhn·IBAN·API키·운전면허·사업자등록번호·IPv4)를
  로컬 재구현했다 — 외부 서비스 불가용 시에도 무중단 실동작을 보장.
- 25종 업종 도메인은 카탈로그만 노출(`status=catalog_only`) — PRD 본문에 실명 인용된 2건(manufacturing-food, public-administration)만 시딩,
  나머지는 wise-Guardrails 소스 미보유로 임의 생성하지 않음(추측 금지).
- 도메인 스코프는 SeCMP 가 `agent_guardrail_config` 로 소유·강제(§7.8.3 — 업스트림 미강제이므로).

## 범위
- DDL: `guardrails_domain_catalog`·`agent_guardrail_config`·`guardrails_decision_log`
- `app/services/guardrails_detector.py` — 13종 정규식 + Luhn 카드검증 + 마스킹(redact)
- `app/routers/router_guardrails.py` — `/domains`, `/agents/{key}/config`(GET/PUT), `/test`(Playground 연계), `/decisions/{id}`, `/decisions`
- `tbl_agent_config` `guardrails` 시드 + 도메인 카탈로그 시드
- 프론트: `api/guardrails.ts` + `pages/guardrails/GuardrailsPage.tsx`(카탈로그·테스트·에이전트별 토글)

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 0 | `guardrails` 에이전트 시드 | agent-config 포함 |
| 1 | 도메인 카탈로그 | global=functional, manufacturing-food=catalog_only |
| 2 | 깨끗한 텍스트 | allow, riskScore=0 |
| 3 | 13종 각각 실제 판정 | **모두** matchedRules 에 해당 rule_id 포함(P2 verify 요건: "PII 13종 각각 실제 탐지 확인") |
| 4 | PII 포함 텍스트 | redact, redactedText 에 원문 미노출(마스킹) |
| 5 | catalog_only 도메인 테스트 | 409 |
| 6 | 미존재 도메인 | 404 |
| 7 | user 토글 | 403 / supervisor 토글 | 200 |
| 8 | 미존재 도메인 토글 | 404 |
| 9 | agent_key 지정 테스트 → decision_log 기록 | 조회 시 1건 |
| 10 | explain_decision | 레코드 반환 / 미존재 404 |
| 11 | 무토큰 | 401/403 |
| 12 | 프론트 타입체크+빌드 | 0 오류 |

## 판정 기준
- 20개 백엔드 assert(13종 탐지기 전수 포함) + 프론트 tsc/build 0오류 = PASS.
