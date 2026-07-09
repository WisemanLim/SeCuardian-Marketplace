# 시험 결과 — 에이전트 표시명 다국어 agent_names 싱크 (impl/35 · 물리 impl/33)

- 일시: 2026-07-09
- 환경: local (격리 sqlite `mp33.db`, uvicorn :8158 — local.db 무변경)
- 판정: **4/4 PASS**

| ID | 시험 | 판정 | 비고 |
|----|------|------|------|
| TC-33-01 | 기동·시드 | ✅ PASS | 내장 7종 `agent_names` — marketplace=`{"ko":"마켓플레이스","en":"Marketplace"}` 등 전부 ko+en |
| TC-33-02 | GET /api/agent-config/ | ✅ PASS | 전 에이전트 `agent_names` dict(비어있지 않음) |
| TC-33-03 | 프론트 표시 체인 | ✅ PASS | AgentsPage 10개소 `nameOf`·AppLayout(nav·collapsed title·헤더, names dict 상태 보존으로 locale 전환 즉시 반영)·GuardrailsPage 셀렉트 |
| TC-33-04 | 정적 검증 | ✅ PASS | `app.main` import OK · tsc 0오류 |

## 싱크 방법 기록

- 동일 파일 5종(router_agent_config/router_addon_agent/agentConfig.ts/addonAgents.ts/GenericAddonPage) 복사
- `db.py`·`sql/{sqlite,pg}/01_init.sql` — 미커밋 상태라 patch 부분 실패 → agent_names ALTER/컬럼 수동 반영(검증)
- MP `02_seed.sql`(sqlite/pg) — 내장 7종 `agent_names` UPDATE 추가(en 표시명: Marketplace/Workflow/RAG/Playground/Guardrails/AI Assistant/Orchestrator)
- MP 고유 화면(AppLayout·GuardrailsPage) — SeCuardian 과 동일 패턴 수동 적용
- `_templates` 6종 meta `display_name` dict 형 + zip 재패키징 동기
