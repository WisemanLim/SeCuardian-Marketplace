# 시험 시나리오 — impl/11: F-GRD block/escalate 승격 조건

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "`guardrails_detector` 에 block/escalate 승격 조건 추가". impl/6·7 에서 판정기가
  allow/redact 2단계만 반환 → 게이트의 block/escalate 분기(이미 구현됨, impl/7)가 미발화하던 것을 활성화.
- 실행: `PYTHONPATH=. python test/impl/11/test_guardrails_escalation.py`

## 승격 정책 (PRD §7.8.2 6단계 enum 준수)
- **고위험 카테고리**: 시크릿(api_key)·신용정보(card·IBAN)·국가식별번호(주민·SSN·마이넘버·여권·운전면허·사업자).
- 매치 없음 → `allow`
- 저위험(이메일·전화·IP)만 → `redact`(마스킹 후 통과)
- 고위험 1종 → `block`(콘텐츠 차단)
- 고위험 2종 이상(복합·대량 유출) → `escalate`(사람 검토, riskScore=1.0)

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | clean | allow |
| 2 | email/phone(저위험) | redact |
| 3 | api key(고위험1) | block |
| 4 | IBAN(고위험1, 중복없음) | block |
| 5 | card(16자리, JP마이넘버와 중복 가능) | block\|escalate |
| 6 | 주민+카드(고위험2) | escalate, riskScore=1.0 |
| 7 | 고위험1+저위험1 | block |
| 8 | `/test` api key | block |
| 9 | 게이트: 고위험 입력 | HTTP 403 [BLOCKED], 핸들러 미도달·자산 미생성 |
| 10 | decision_log | block 기록 |
| 11 | 저위험 email 게이트 | redact 후 통과+마스킹 저장(기존 동작 유지) |

## 판정 기준
- 14개 assert 전부 PASS + impl/6·7 회귀(email=redact 유지) 무영향 = PASS.
- 하위호환: 저위험 PII 는 여전히 redact — 기존 시험 불변.
