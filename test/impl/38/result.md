# 시험 결과 — AI 어시스턴트 tool-call 루프 설정화 + .env.* 지원 (§7.11.2-6, impl/40 · 물리 test/impl/38)

> **판정**: PASS (6/6 + ruff + 회귀)
> **실행일**: 2026-07-09
> **환경**: macOS darwin 25.5.0 / uv + pytest (mock LLM — 실 Ollama 불요)

## 실행 명령

```bash
uv run pytest test/impl/38/ -q                          # → 6 passed
uv run ruff check app/core/config.py app/agents/orchestrator.py test/impl/38/  # → 0 오류
uv run pytest test/impl/31/ test/impl/33/ test/impl/37/ -q  # 회귀 → 5 passed
```

## 결과 상세

| ID | 판정 | 비고 |
|----|------|------|
| TC-38-01 | PASS | 임시 env 파일 `LLM_TOOL_MAX_ROUNDS=3` → `Settings.llm_tool_max_rounds == 3` (pydantic env_file) |
| TC-38-02 | PASS | 우선순위 3케이스: 기본값+DB=9→"9" / .env=4+DB=9→"4" / os.environ=2→"2" |
| TC-38-03 | PASS | 미설정→6, "3"→3, "0"→1(최소 클램프), "abc"→6(폴백) |
| TC-38-04 | PASS | 동일 `PUT /api/agent-config/ai-assistant`→405 반복 시 **LLM 정확히 2회 호출 후 조기 종료**(기존 6회), 반환은 `_format_api_error` 사용자 친화 메시지 — 원시 JSON·`<api_call>` 태그 미노출 |
| TC-38-05 | PASS | `max_rounds=1` → LLM 1회 호출로 제한 |
| TC-38-06 | PASS | seed(sqlite/pg)·`.env.*` 5파일·SettingsPage `EDITABLE_KEYS`·orchestrator env맵/DB키 전부 등재 |
| TC-38-07 | PASS | ruff 0오류, import 정상 (TC-38-02~05 가 orchestrator import 경유) |

## 비고

- 조기 종료 1차 수행 시 TC-38-04 단언이 과도(`"Method Not Allowed" not in result`)해 FAIL —
  `_format_api_error` 는 의도적으로 상태 텍스트를 포함하는 **사용자 친화 포맷**이므로
  원시 JSON(`{"detail"`)·내부 태그(`<api_call>`) 미노출 단언으로 정정 후 PASS. 구현 결함 아님.
- `.env.local/dev/staging` 는 주석 키(`# LLM_TOOL_MAX_ROUNDS=6`)로 등재 — 기본값(6)과 동일한
  값은 `_db_llm_settings` 2단계에서 ".env 미명시"로 간주돼 DB 설정이 유효한 기존 패턴 유지.
  변경 시 주석 해제 + 비기본값 입력.
- 회귀: test/impl/31·33·37 (R18-7·agent_names·다국어 authoring) 5/5 무영향.
