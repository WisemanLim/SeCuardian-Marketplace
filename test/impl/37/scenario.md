# 시험 시나리오 — 다국어 설명 authoring 소스 전환 + jp 확장 (§7.11.2-5, impl/39 · 물리 test/impl/37)

배경(사용자 오류 보고 2026-07-09): 에이전트 description 이 "확장 가능 구조로 개선됐다"고 했으나
실제로는 authoring 소스가 split 컬럼(`description`/`description_en`)이라 타 언어 추가 경로가
없어 사실상 미적용. 요구: `descriptions` 를 `{"ko":"","en":"","jp":""}` 형태 JSON 으로(컬럼 분리 금지),
언어셋 없으면 **선호언어**(마이페이지 설정)로 표출.

대상: sql/{sqlite,pg}/02_seed.sql, app/db.py(중복 제거), app/agents/orchestrator.py,
app/routers/router_marketplace.py, scripts/seed_security.py, front(locale.ts·ProfilePage·locales).

| ID | 입력 | 기대 |
|----|------|------|
| TC-37-01 | 격리 sqlite 기동+seed | 내장 7종 `descriptions`·`agent_names` JSON 에 **ko/en/jp 3키** 존재, split `description`/`description_en` NULL(authoring 안 함) |
| TC-37-02 | GET /api/agent-config/ | 각 에이전트 `descriptions` dict(ko/en/jp)·`agent_names` dict 반환 |
| TC-37-03 | `_active_agents_block()` | descriptions(ko) 기반 설명 포함(레거시 description NULL 이어도 정상), agent_names(ko) 이름 사용 |
| TC-37-04 | db.py backfill_descriptions | 단일 정의(중복 제거) — import 후 함수 1개 |
| TC-37-05 | marketplace install(agent) | tbl_agent_config `descriptions`·`agent_names` JSON 기록(split 아님) |
| TC-37-06 | pickDescription 로직(단위) | UI=ko→ko / UI=en→en / **jp-only 설명 + UI=ko + 선호=jp → jp**(언어셋 없을 때 선호언어 fallback) |
| TC-37-07 | 프론트 | PREFERRED_LANGS jp 포함, locale.jp 라벨 ko/en 존재, tsc 0오류 |
