# 시험 결과 — SeCuardian impl/55 복제 싱크 (impl/31)

- 일시: 2026-07-09
- 환경: local (격리 sqlite `mp31.db`, uvicorn :8156)
- 판정: **6/6 PASS**

| ID | 시험 | 판정 | 비고 |
|----|------|------|------|
| TC-31-01 | 기동 마이그레이션·백필 | ✅ PASS | `tbl_agent_config.descriptions`·`tbl_users.preferred_lang`·`tbl_llm_usage` 생성 |
| TC-31-02 | GET /api/agent-config/ | ✅ PASS | 7개 에이전트 전부 `descriptions` dict |
| TC-31-03 | preferred_lang | ✅ PASS | PATCH `en` → GET 반영 |
| TC-31-04 | GET /api/llm/models | ✅ PASS | `{"value":"ollama","label":"Local — ollama: mistral"}` (Anthropic 키 미설정 환경 — local 만) |
| TC-31-05 | routes PUT + usage GET | ✅ PASS | PUT 200, `usage?group_by=model` 정상(빈 원장) |
| TC-31-06 | 정적 검증 | ✅ PASS | `app.main` import OK · ruff 신규 오류 0(기존 main.py E402 1건 베이스라인 동일) · front tsc PASS · `docker compose config` OK |

## 싱크 방법 기록

- 동일 파일(pre-change 기준 SeCuardian 과 바이트 일치) 13종 → 직접 복사
- 신규 파일 6종(`app/routers/router_llm.py`, `app/services/{llm_providers,llm_router,llm_metering,token_compress}.py`, `front/src/api/llm.ts`) → 복사
- 분기 파일 11종(orchestrator/config/db/compose/.env.example/locales/AgentsPage/sql 4종) → `git diff` patch 적용
- `app/main.py` → patch reject, 3개소(라우터 import·include, backfill 호출) 수동 병합
- `addon-agents/_templates` 6종 meta(dict 형 description) + zip 재패키징 복사
