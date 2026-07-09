"""impl/40 — AI 어시스턴트 tool-call 루프 설정화(llm_tool_max_rounds) + .env.* 지원 시험."""
import asyncio
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_tc01_pydantic_env_file(tmp_path):
    """TC-38-01: LLM_TOOL_MAX_ROUNDS 를 .env 파일에서 읽는다."""
    from app.core.config import Settings

    env_file = tmp_path / ".env.test"
    env_file.write_text("LLM_TOOL_MAX_ROUNDS=3\n")
    s = Settings(_env_file=str(env_file))
    assert s.llm_tool_max_rounds == 3


def test_tc02_db_llm_settings_priority(monkeypatch):
    """TC-38-02: os.environ > .env(settings 비기본값) > tbl_settings > 기본값."""
    import app.db as app_db
    from app.core.config import settings as cfg
    from app.agents.orchestrator import _db_llm_settings

    async def fake_fetch_all(_sql):
        return [{"key": "llm_tool_max_rounds", "value": "9"}]

    monkeypatch.setattr(app_db, "fetch_all", fake_fetch_all)
    monkeypatch.delenv("LLM_TOOL_MAX_ROUNDS", raising=False)

    # C) 기본값(6) + DB=9 → DB 승리
    monkeypatch.setattr(cfg, "llm_tool_max_rounds", 6)
    assert asyncio.run(_db_llm_settings())["llm_tool_max_rounds"] == "9"

    # A) .env 명시(=기본값과 다른 4) → DB 덮어쓰기
    monkeypatch.setattr(cfg, "llm_tool_max_rounds", 4)
    assert asyncio.run(_db_llm_settings())["llm_tool_max_rounds"] == "4"

    # B) os.environ 최우선
    monkeypatch.setenv("LLM_TOOL_MAX_ROUNDS", "2")
    assert asyncio.run(_db_llm_settings())["llm_tool_max_rounds"] == "2"


def test_tc03_max_rounds_parse():
    """TC-38-03: 파싱·클램프·폴백."""
    from app.agents.orchestrator import Orchestrator

    assert Orchestrator._max_rounds({}) == 6
    assert Orchestrator._max_rounds({"llm_tool_max_rounds": "3"}) == 3
    assert Orchestrator._max_rounds({"llm_tool_max_rounds": "0"}) == 1
    assert Orchestrator._max_rounds({"llm_tool_max_rounds": "abc"}) == 6


def _run_rounds(monkeypatch, max_rounds):
    """동일 PUT→405 를 반복하는 mock 으로 _ollama_tool_rounds 실행, (호출수, 반환값)."""
    import app.agents.orchestrator as orch
    from app.services import llm_providers

    calls = {"chat": 0}

    async def fake_chat(_messages, _system, **_kw):
        calls["chat"] += 1
        return '<api_call>{"method":"PUT","path":"/api/agent-config/ai-assistant"}</api_call>'

    async def fake_exec(_method, _path, _body, _params, _token):
        return 'HTTP 405 Method Not Allowed\n{"detail":"Method Not Allowed"}'

    monkeypatch.setattr(llm_providers, "chat", fake_chat)
    monkeypatch.setattr(orch, "_exec_api_call", fake_exec)

    result = asyncio.run(
        orch.Orchestrator._ollama_tool_rounds(
            None, [], "sys", "ollama", "mistral", "http://x", {}, None, re,
            max_rounds=max_rounds,
        )
    )
    return calls["chat"], result


def test_tc04_early_break_on_repeated_error(monkeypatch):
    """TC-38-04: 동일 (method, path, status) 오류 반복 시 2회 후 조기 종료."""
    chat_calls, result = _run_rounds(monkeypatch, max_rounds=6)
    assert chat_calls == 2, f"조기 종료 실패: LLM {chat_calls}회 호출"
    assert result  # 사용자 친화 오류 메시지 (_format_api_error 포맷)
    assert '{"detail"' not in result  # 원시 오류 JSON 미노출
    assert "<api_call>" not in result  # 내부 프롬프트 태그 미노출


def test_tc05_max_rounds_respected(monkeypatch):
    """TC-38-05: max_rounds=1 이면 LLM 1회로 제한."""
    chat_calls, result = _run_rounds(monkeypatch, max_rounds=1)
    assert chat_calls == 1
    assert result


def test_tc06_static_wiring():
    """TC-38-06: seed·.env 파일·프론트 EDITABLE_KEYS 등재."""
    for rel in ("sql/sqlite/02_seed.sql", "sql/pg/02_seed.sql"):
        assert "llm_tool_max_rounds" in (ROOT / rel).read_text(), rel
    for rel in (".env.example", ".env.local", ".env.dev", ".env.staging", ".env.prod"):
        assert "LLM_TOOL_MAX_ROUNDS" in (ROOT / rel).read_text(), rel
    front = (ROOT / "front/src/pages/settings/SettingsPage.tsx").read_text()
    assert '"llm_tool_max_rounds"' in front
    # 백엔드 플럼빙: env 맵 + DB 조회 키
    src = (ROOT / "app/agents/orchestrator.py").read_text()
    assert '"llm_tool_max_rounds": "LLM_TOOL_MAX_ROUNDS"' in src
    assert "'llm_tool_max_rounds')" in src
