# 시험 시나리오 — AI 어시스턴트 tool-call 루프 설정화 + .env.* 지원 (§7.11.2-6, impl/40 · 물리 test/impl/38)

배경(사용자 요구 2026-07-09): AI 어시스턴트가 API 오류 시 내부 자가수정 루프(하드코딩 6라운드)를
돌며, 존재하지 않는 메서드 반복 호출(예: `PUT /api/agent-config/ai-assistant` → 405 × 6회) 시
LLM 호출이 낭비됨. 요구: ① 루프 횟수를 시스템에서 관리 ② **`.env.*` 를 통해 설정 가능**.

대상: app/core/config.py(`llm_tool_max_rounds`), app/agents/orchestrator.py
(`_db_llm_settings`·`_max_rounds`·`_ollama_tool_rounds` 조기 종료), sql/{sqlite,pg}/02_seed.sql,
front SettingsPage `EDITABLE_KEYS`, `.env.example`·`.env.{local,dev,staging,prod}`.

| ID | 입력 | 기대 |
|----|------|------|
| TC-38-01 | 임시 env 파일 `LLM_TOOL_MAX_ROUNDS=3` 로 `Settings(_env_file=...)` 생성 | `llm_tool_max_rounds == 3` (pydantic env_file 경로 동작) |
| TC-38-02 | `_db_llm_settings` 우선순위 3케이스 | A) settings=4(.env 명시)+DB=9 → "4" B) os.environ=2 → "2"(최우선) C) 기본값+DB=9 → "9" |
| TC-38-03 | `Orchestrator._max_rounds` 파싱 | 미설정→6, "3"→3, "0"→1(클램프), "abc"→6(기본 폴백) |
| TC-38-04 | `_ollama_tool_rounds` 동일 405 반복(mock chat+API) | LLM 호출 **정확히 2회** 후 조기 종료, 사용자 친화 오류 반환(원시 405 미노출) |
| TC-38-05 | `_ollama_tool_rounds(max_rounds=1)` | LLM 호출 1회로 제한(설정값 존중) |
| TC-38-06 | seed·env 파일·프론트 정적 검증 | sqlite/pg seed 에 `llm_tool_max_rounds` 행, `.env.*` 5파일에 `LLM_TOOL_MAX_ROUNDS` 키, SettingsPage `EDITABLE_KEYS` 포함 |
| TC-38-07 | ruff + import 회귀 | `ruff check` 0오류, `app.agents.orchestrator`·`app.core.config` import 정상 |
