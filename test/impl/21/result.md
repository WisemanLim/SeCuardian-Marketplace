# 시험 결과 — impl/21: 가드레일 완전판정(LLM classifier) + 과탐 완화 + 실판정/휴리스틱 공존

- 날짜: 2026-07-09
- 판정: **PASS**

## 실행 결과
```
PYTHONPATH=. uv run python test/impl/21/test_guardrails_classifier.py
[PASS] 1. finance-banking 실판정+휴리스틱 공존 — {'heuristic': 198, 'regex': 2}
[PASS] 2. 카탈로그 카운트 = real+heuristic — 200=2+198
[PASS] 3. 규칙에 mode/description/priority
[PASS] 4. 단일 키워드 과탐 완화(수수료 → allow) — allow n=0
[PASS] 5. 무해 입력 → allow — n=0
[PASS] 6. classifier OFF → source=rules — rules
[PASS] 7. classifier ON → source=rules+llm — rules+llm
[PASS] 8. LLM 판정 rule_id 병합 — target=FIN_BANK_KR_008
[PASS] 9. classifier degrade → 무크래시 allow
[PASS] 10. candidates 계약(제외·limit·priority)
결과: 10 PASS / 0 FAIL
```

## 판정 구조(2단 완전판정)
1. **regex(결정적, 무LLM)** — 실판정(원본 regex) + 휴리스틱(생성 regex). 항상 동작.
2. **LLM classifier(옵션, `guardrails_classifier_enabled`)** — 규칙 메뉴(도메인당 max_rules=40, priority순, regex 기매치 제외)를
   LLM 에 제시해 패러프레이즈/문맥 위반 판정, regex 결과에 병합. 미구성/장애/파싱실패 시 regex 로 무중단 degrade.

## 과탐 완화 효과
- 생성 regex 를 **동일 예시 내 2개 키워드 공기(AND)** 로 제한 + 교차도메인 DF(≥6 도메인)=generic 제외.
- "수수료 안내 좀 부탁해요" → **allow**(기존 단일 '수수료' 규칙 오탐 제거). "KYC 없이 계좌 개설" → block 유지.
- finance-banking heuristic self-match(examplesPositive) ≈ 51% — 정밀도↑(오탐↓), 재현율 손실분은 LLM classifier 가 보완.

## 회귀
```
impl/6 ALL PASS · impl/7 ALL PASS · impl/11 ALL PASS · impl/13 ALL PASS · impl/20 12/12 PASS
```
- 프론트 tsc/build 0오류. ruff(신규/수정 py) 통과.

## 생성/수정 파일
- 수정: `scripts/build_guardrails_data.py`(DF+2키워드 게이트·mode·description·priority·dedup),
  `app/services/guardrails_rules.py`(classifier_candidates·real/heuristic 카운트 sync),
  `app/services/guardrails_detector.py`(_classify_llm·decide_multi_llm·logger),
  `app/routers/router_guardrails.py`(classifier 분기), `app/core/config.py`(classifier_enabled/max_rules),
  `app/db.py`+`sql/{sqlite,pg}/01_init.sql`(real/heuristic_rule_count 컬럼),
  `front/src/api/guardrails.ts`·`front/src/pages/guardrails/GuardrailsPage.tsx`(토글 낙관적 업데이트·오류표면화·카운트·소스),
  `app/data/guardrails/*`(재컴파일), `addon-agents/zip/emb_guardrails/`(룰셋 데이터 동봉+재패키징), PRD·README.
- 신규: `test/impl/21/{scenario,result,test_guardrails_classifier}.{md,py}`.
