# 시험 결과 — 다국어 설명 authoring 소스 전환 + jp 확장 (§7.11.2-5, impl/39 · 물리 test/impl/37)

> **판정**: PASS (backend 5/5 + 프론트 pickDescription/tsc + 회귀)
> **실행일**: 2026-07-09
> **환경**: macOS darwin 25.5.0 / local SQLite(격리 tmp DB) / uv + pytest / node(vite)

## 실행 명령

```bash
uv run pytest test/impl/37/ -q                # → 5 passed
node -e '<pickDescription fallback 검증>'      # → TC-37-06 OK
cd front && npx tsc --noEmit                   # → 0 오류
uv run ruff check app/db.py app/agents/orchestrator.py app/routers/router_marketplace.py scripts/seed_security.py test/impl/37/
uv run pytest test/impl/31/ test/impl/33/ -q   # 회귀 (R18-7·agent_names 싱크)
```

## 결과 상세

| ID | 판정 | 비고 |
|----|------|------|
| TC-37-01 | PASS | 내장 7종 descriptions/agent_names JSON 에 ko/en/jp 3키, split description/description_en NULL |
| TC-37-02 | PASS | agent-config API descriptions/agent_names dict(jp 포함) 반환 |
| TC-37-03 | PASS | `_active_agents_block` — descriptions(ko)/agent_names(ko) 사용(레거시 NULL 무관) |
| TC-37-04 | PASS | db.py `backfill_descriptions` 단일 정의(중복 제거) |
| TC-37-05 | PASS | marketplace install → config descriptions/agent_names JSON 기록(split 아님) |
| TC-37-06 | PASS | pickDescription: UI=ko→ko / UI=en→en / **jp-only + UI=ko + 선호=jp → jp** / 선호 없으면 첫 언어 |
| TC-37-07 | PASS | PREFERRED_LANGS jp 포함, locale.jp 라벨 ko/en, tsc 0오류 |

## 핵심 변경

- **authoring 소스 = descriptions/agent_names JSON**(§7.11.2-5): `02_seed.sql`(sqlite/pg) 내장 7종을
  `{"ko","en","jp"}` JSON 으로 직접 저자, split `description`/`description_en` authoring 폐지
  (레거시 컬럼은 읽기 폴백 스키마만 유지).
- **orchestrator**: `_active_agents_block` 이 descriptions JSON(ko→en→첫 언어)에서 프롬프트 설명 조회.
- **선호언어 확장**: `PREFERRED_LANGS` 에 jp 추가 → UI 언어 키 없을 때 `pickDescription` 이 선호언어로 표출.
- **install/seed_security**: config upsert·security 시드가 descriptions JSON 기록.
- **버그 수정**: db.py `backfill_descriptions` 중복 정의 제거(뒤 정의가 앞을 가리던 dead code).

## 사용자 요구 대응

| 요구 | 대응 |
|------|------|
| descriptions 를 `{"ko":"","en":"","jp":""}` JSON 형태로(컬럼 분리 금지) | ✅ 02_seed·install·seed_security 모두 JSON authoring, split 컬럼 authoring 폐지 |
| 언어셋 없으면 선호언어로 표출 | ✅ pickDescription `UI→선호→ko→첫 언어` (TC-37-06 jp fallback 실증) |
| 선호언어 마이페이지 설정 | ✅ ProfilePage PREFERRED_LANGS(ko/en/jp), `PATCH /auth/me`, 로그인 동기화(기존) |
