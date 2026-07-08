# 시험 시나리오 — impl/20: 가드레일 도메인 필터 확장 + emb_ 내장 패키지 + MCP 개방

- 날짜: 2026-07-09
- 대상(PRD §7.8.7/§7.8.8, 변경이력 v0.17 impl/21+22 + MCP 개방 #C)
- 실행: `PYTHONPATH=. uv run python test/impl/20/test_guardrails_domains.py`
- 전제: `app/data/guardrails/`(컴파일 규칙 데이터) 존재 — `scripts/build_guardrails_data.py` 로 생성.

## 범위
- **A. 도메인 필터 확장(§7.8.7)**: wise-Guardrails 규칙 24 도메인을 `app/data/guardrails/` 로 내재화,
  classifier 규칙에 **regex 생성**. 룰스토어(`guardrails_rules.py`) + 다도메인 판정(`decide_multi`).
  `guardrails_domain_catalog.filter_enabled`(global=필수 잠금) + `PUT /domains/{key}/filter` + `/test` 다도메인.
  프론트 카탈로그 `필터적용` 토글 + 도메인별 결과.
- **B. emb_ 내장 패키지(§7.8.8)**: `emb_{marketplace,workflow,rag,playground,guardrails}` ADDON 패키지 생성.
- **C. MCP 개방**: 내장 REQUIRED 5종(마켓플레이스~가드레일)의 MCP 잠금 해제(프론트 `BUILTIN_KEYS` 기준 eligible).

## 시험 케이스 (test_guardrails_domains.py)
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 데이터 로드 | ≥20 도메인 |
| 2 | global 필수+실판정 | required + functional |
| 3 | 산업 도메인 regex 생성 | finance-banking regex>100 |
| 4 | global 주민번호 | block/escalate |
| 5 | global 마스킹 | 주민번호 미노출 |
| 6 | finance-banking 생성 regex | KYC 우회 문구 매치 |
| 7 | perDomain breakdown | finance-banking matchedCount>0 |
| 8 | evaluatedDomains | {global, finance-banking} |
| 9 | 무해 입력 | allow |
| 10 | 생성 regex 유효성 | 컴파일 오류 0(샘플 5도메인) |
| 11 | emb_ 내장 패키지 | 5종 app/meta/zip 정상 |
| 12 | MCP 개방 | BUILTIN_KEYS eligible 로직 |

## 회귀
- 기존 가드레일 시험 impl/6·7·11·13 — 계약 변경(§7.8.7)으로 impl/6(4)·impl/13(1) 의 **구계약 단정만 갱신**
  (catalog_only→적용가능, global 13→256규칙, 409/404→관대, source local→rules). 동작 회귀 없음.
- 프론트 tsc/build 0오류.

## 판정 기준
- test_guardrails_domains.py 12/12 PASS + impl/6·7·11·13 ALL PASS + 프론트 tsc/build 0오류 = PASS.
