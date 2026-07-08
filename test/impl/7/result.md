# 시험 결과 — impl/7

- 날짜: 2026-07-08
- 판정: **PASS** (15/15 신규 + 기존 impl/1,2,4,5,6 전체 회귀 PASS)

## 실행 결과
```
PASS gate installed at startup
PASS orchestrator.py source contains no guardrails references (원본 무변경)
PASS redact policy forwards sanitized body, not blocked
PASS raw PII absent from forwarded/response text
PASS asset created despite PII (redact, not block)
PASS stored description has masked email
PASS input+output both logged (io_scope=both) (2)
PASS input-side entry recorded as redact w/ 1 matched rule
PASS output-side entry allow (already-masked text has no PII left to match)
PASS clean input passes gate -> handler executes
PASS clean asset actually created
PASS gate off -> PII input passes through
PASS agent B (workflow) untouched by agent A's guardrails config
PASS unresolvable path passthrough, no crash
PASS GUARDRAILS_ENABLED=false -> full bypass

=== RESULT: ALL PASS
```

## 전체 회귀
```
boot OK routes=24 (변화 없음 — 신규 라우터 없음, 게이트는 함수 재바인딩)
ruff check app/ — 신규 파일 0오류(기존 E402만)
impl/1 (F-MP)        ALL PASS
impl/2 (F-WF)        ALL PASS
impl/4 (F-RAG)       ALL PASS
impl/5 (F-PG)        ALL PASS
impl/6 (F-GRD)       ALL PASS
impl/7 (F-GRD gate)  ALL PASS
```

## 검증 항목
- **`orchestrator.py` 소스 완전 무변경** — `inspect.getsource()` 로 guardrails 관련 문자열 부재 확인. PRD §3 준용 원칙 충족.
- 모듈 속성 재바인딩(`orch._exec_api_call = gated`) 이 orchestrator 내부의 6개 이름 기반 호출 지점 전부를 가로챔 — Python 전역 이름 조회 특성 활용.
- 입력측 PII 발견 시 **실제로 치환된 값이 DB 에 저장**됨(단순 로깅이 아니라 실제 강제).
- io_scope=both 는 입력·출력 각각 독립 판정+로깅 — 이미 마스킹된 텍스트를 출력측이 재검사해도 추가 매치 없음(정상, 이중 마스킹 아님).
- 에이전트별 토글 정합성(요구사항 3) — A 에이전트 설정이 B 에이전트·미토글 시 무영향.
- `GUARDRAILS_ENABLED=false` 전역 플래그로 전체 우회 가능(운영 킬스위치).
- 예외/미해석 경로에서 항상 원 호출로 안전 폴백 — 무중단 원칙 유지.

## 발견 사항 (테스트 버그, 구현 결함 아님)
- 최초 테스트 작성 시 PII 발견 시 `block`(403) 을 기대했으나, `guardrails_detector.decide()` 는 현재
  `allow`/`redact` 2단계만 구현(§7.8.0 이 정의한 PRD 6단계 enum 중 일부). 게이트 코드 자체는 6단계
  분기(`block`/`escalate` → 403, `redact`/`sanitize` → 치환)를 전부 갖추고 있으나, 판정기가 아직
  `block` 을 반환하는 경로가 없어 해당 분기는 아직 실행되지 않음(향후 판정기 확장 시 자동 활성화).
  테스트는 실제 정책(redact)에 맞춰 수정.

## 미결/후속
- `guardrails_detector.decide()` 에 `block`/`escalate` 승격 조건 추가(예: 카드번호+API키 동시 검출 시) — 판정기 고도화, F-GRD 범위 내 후속.
- MCP Server 프록시 연동(로컬 판정이 현재 1차 경로, 원격 연동은 대체 경로로 확장 가능).
