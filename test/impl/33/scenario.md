# 시험 시나리오 — 에이전트 표시명 다국어 agent_names 싱크 (impl/35 · 물리 impl/33)

배경(§7.11.2 확장): SeCuardian R18-7 확장 impl/56(에이전트 표시명 `agent_names` JSON)을
코드 복제로 싱크. MP 는 내장 7종 표시명이 한국어(마켓플레이스·워크플로우 등)라 en UI 에서
그대로 노출되던 부분이 해소 대상.

| ID | 입력 | 기대 |
|----|------|------|
| TC-33-01 | 서버 기동(격리 sqlite) | `agent_names` 컬럼 + 내장 7종 시드 `{"ko","en"}` (Marketplace/Workflow/RAG/Playground/Guardrails/AI Assistant/Orchestrator) |
| TC-33-02 | GET /api/agent-config/ | 전 에이전트 `agent_names` dict 반환 |
| TC-33-03 | 프론트 표시 | AgentsPage `nameOf`·AppLayout nav/헤더(names 상태 보존)·GuardrailsPage 에이전트 셀렉트 — pick 체인 적용, tsc 0오류 |
| TC-33-04 | 정적 검증 | `app.main` import OK, front tsc 0오류 |
