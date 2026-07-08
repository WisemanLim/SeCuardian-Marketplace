# 시험 시나리오 — impl/21: 가드레일 완전판정(LLM classifier) + 과탐 완화 + 실판정/휴리스틱 공존

- 날짜: 2026-07-09
- 대상(PRD §7.8.7, 변경이력 v0.18 impl/23)
- 실행: `PYTHONPATH=. uv run python test/impl/21/test_guardrails_classifier.py` (call_ollama monkeypatch, LLM 불요)

## 범위
- **LLM classifier(완전판정)**: `guardrails_classifier_enabled`(기본 off) 시 `/test` 가 regex 후 도메인 규칙 메뉴를
  LLM(`call_ollama`)에 제시해 패러프레이즈 위반 판정 → `decide_multi_llm`, `source="rules+llm"`, degrade-safe.
- **과탐 완화**: 생성 regex 를 **동일 예시 내 2개 키워드 공기(AND)** 로 제한 + 교차도메인 DF 필터 →
  단일 흔한 키워드('수수료') 오탐 제거.
- **실판정+휴리스틱 공존(E)**: 규칙별 `mode`(regex/heuristic/classifier), 카탈로그 `real_rule_count`+`heuristic_rule_count` 분리.
- (병행) 필터 토글 낙관적 업데이트+오류 표면화, emb_guardrails 룰셋 데이터 동봉.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 실판정+휴리스틱 공존 | finance-banking regex≥1 + heuristic≥10 |
| 2 | 카탈로그 카운트 | regex = real + heuristic |
| 3 | 규칙 필드 | mode·description·priority 존재 |
| 4 | 과탐 완화 | "수수료 안내" → allow |
| 5 | 무해 입력 | allow |
| 6 | classifier OFF | source=rules |
| 7 | classifier ON | source=rules+llm |
| 8 | LLM 판정 병합 | mock rule_id 매치 반영 |
| 9 | classifier degrade | 비정상 응답 → 무크래시 allow |
| 10 | candidates 계약 | 제외·limit·priority 정렬 |

## 판정 기준
- test_guardrails_classifier.py 10/10 PASS + 회귀 impl/6·7·11·13·20 ALL PASS + 프론트 tsc/build 0오류 = PASS.
