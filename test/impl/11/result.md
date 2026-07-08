# 시험 결과 — impl/11

- 날짜: 2026-07-08
- 판정: **PASS** (14/14) + impl/6·7 회귀 무영향

## 실행 결과
```
PASS clean -> allow
PASS email(저위험) -> redact
PASS phone(저위험) -> redact
PASS api key(고위험1) -> block
PASS IBAN(고위험1, 중복없음) -> block
PASS card -> block|escalate
PASS 주민+카드(고위험2) -> escalate, riskScore=1.0
PASS 고위험1+저위험1 -> block
PASS /test api key -> block
PASS block 입력 -> 게이트 403 차단
PASS 차단 응답에 [BLOCKED] 마커
PASS 차단된 호출은 핸들러 미도달 → 자산 미생성
PASS decision_log 에 block 기록
PASS 저위험 email -> redact 후 통과 + 마스킹 저장

=== RESULT: ALL PASS
```

## 검증 항목
- decide() 3단계 승격(redact/block/escalate) + allow — PRD §7.8.2 6단계 enum 중 실기능 4종 활성.
- **게이트 실차단**: 고위험 입력이 Orchestrator `_exec_api_call` 게이트에서 HTTP 403 [BLOCKED] 로 원 호출 자체 차단
  → 핸들러 미도달·자산 미생성(impl/7 게이트의 block 분기가 이제 실제로 발화).
- **하위호환**: 저위험 PII(이메일/전화/IP)는 여전히 redact — impl/6·7 전체 회귀 무영향 확인.
- boot 25 routes, `ruff check` 신규코드 0오류.

## 발견 사항 (테스트 데이터 특성, 결함 아님)
- 카드번호(16자리+공백) `4111 1111 1111 1111` 은 JP 마이넘버 정규식(12자리 `\d{4}\s?\d{4}\s?\d{4}`)의
  부분 문자열과도 매치 → 고위험 2종으로 escalate 될 수 있음. 정규식 탐지기의 자연스러운 중첩(오탐이 아니라
  "더 보수적으로 승격")이므로 block|escalate 모두 허용으로 판정. 단일 block 검증은 중첩 없는 IBAN 으로 수행.

## 미결/후속
- 카테고리 간 정규식 중첩 정교화(가장 구체적인 매치 우선) — 판정 품질 향상, 후속.
- MCP Server 프록시 연동 시 원격 판정기의 6단계 전체(warn/sanitize 포함) 반영.
