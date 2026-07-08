# 시험 결과 — impl/20: 가드레일 도메인 필터 확장 + emb_ 내장 패키지 + MCP 개방

- 날짜: 2026-07-09
- 판정: **PASS**

## 실행 결과

```
PYTHONPATH=. uv run python test/impl/20/test_guardrails_domains.py
[PASS] 1. 데이터 로드(≥20 도메인) — 23 domains
[PASS] 2. global 필수+실판정 — regex=247
[PASS] 3. 산업 도메인 regex 생성(heuristic) — finance-banking regex=198
[PASS] 4. global 주민번호 → block/escalate — block
[PASS] 5. global 마스킹 적용 — 제 주민등록번호는 **********4567 입니다
[PASS] 6. finance-banking 생성 regex 매치 — matched=13
[PASS] 7. perDomain breakdown 존재
[PASS] 8. evaluatedDomains 반영 — ['global', 'finance-banking']
[PASS] 9. 무해 입력 → allow — allow matched=0
[PASS] 10. 컴파일 데이터 regex 유효(샘플 5도메인) — invalid=0
[PASS] 11. emb_ 내장 패키지 5종(app/meta/zip) — 5/5
[PASS] 12. MCP 개방(BUILTIN_KEYS 기준 eligible)
결과: 12 PASS / 0 FAIL
```

## 컴파일 데이터 요약 (`scripts/build_guardrails_data.py`)
- 23 도메인 컴파일(`global` 은 global+privacy 병합 256규칙, orig regex 57 + 생성 190).
- 산업 도메인은 대부분 classifier → 생성 regex(heuristic). finance-banking·manufacturing-food 는 원본 regex 보유 → functional.
- 생성 regex self-match(examplesPositive) ≈ 81.6%(finance-banking 기준). 총 데이터 ≈ 2.0MB(24파일).

## 회귀
```
impl/6  ALL PASS   (구계약 단정 4건 §7.8.7 로 갱신: catalog_only→적용가능·global rule_id·409·404)
impl/7  ALL PASS
impl/11 ALL PASS
impl/13 ALL PASS   (source local→rules 단정 갱신)
```
- 프론트 `pnpm exec tsc --noEmit` + `pnpm build` 0오류.
- 앱 부팅 26 routes, lifespan `sync_catalog()` 정상(23 도메인 카탈로그 동기화).

## 생성/수정 파일
- 신규: `scripts/build_guardrails_data.py`, `app/data/guardrails/*.json`(24), `app/services/guardrails_rules.py`,
  `addon-agents/zip/emb_{marketplace,workflow,rag,playground,guardrails}/`(+zip),
  `test/impl/20/{scenario,result,test_guardrails_domains}.{md,py}`.
- 수정: `app/services/guardrails_detector.py`(decide_multi), `app/routers/router_guardrails.py`(filter 토글·다도메인 /test),
  `app/db.py`(filter_enabled 컬럼 마이그레이션), `app/main.py`(sync_catalog), `sql/{sqlite,pg}/01_init.sql`,
  `front/src/api/guardrails.ts`, `front/src/pages/guardrails/GuardrailsPage.tsx`, `front/src/pages/agents/AgentsPage.tsx`(MCP 개방),
  `test/impl/6/*`·`test/impl/13/*`(구계약 단정 갱신), PRD·README.
