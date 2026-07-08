"""Guardrails Orchestrator 게이트 (F-GRD, PRD §7.8.4).

Orchestrator 코드 자체는 무변경 원칙(§3)을 지키기 위해, `app.agents.orchestrator._exec_api_call`
을 **얇은 래퍼로 몽키패치**해 요청/응답 훅을 건다. `_exec_api_call` 은 orchestrator 모듈 내부에서
이름으로 호출되므로(전역 조회), 모듈 속성을 재바인딩하면 orchestrator.py 소스 수정 없이 모든
내부 호출 지점(6곳)을 가로챌 수 있다.

검사 범위: `global` 도메인만(§7.8.0 — 유일한 실판정 도메인). 대상 에이전트는 REST 경로에서 추론
(`/api/addon/{key}/...` → key, 내장 에이전트 경로 → 고정 key). `agent_guardrail_config` 에 해당
에이전트+`global`+enabled=1 행이 없으면 게이트를 통과시킨다(기본 off, §DDL 기본값과 일치).

로컬 판정기(`guardrails_detector`)는 네트워크 의존이 없어 자체 예외만 방어하면 되므로, 예외 발생 시
게이트를 건너뛰고 원 호출을 그대로 수행한다(무중단 — MCP 다운 시 auto-degrade 와 동일한 원칙).
"""
import json
import logging
import uuid

logger = logging.getLogger("uvicorn.error")

_BUILTIN_PREFIXES = ("marketplace", "workflow", "rag", "playground", "guardrails", "agent")


def _resolve_agent_key(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2 or parts[0] != "api":
        return None
    if parts[1] == "addon" and len(parts) >= 3:
        return parts[2]
    if parts[1] in _BUILTIN_PREFIXES:
        return parts[1]
    return None


async def _get_scope(agent_key: str) -> str | None:
    from app.db import _PH, fetch_one
    row = await fetch_one(
        f"SELECT io_scope FROM agent_guardrail_config "
        f"WHERE agent_key = {_PH} AND domain_key = 'global' AND enabled = 1",
        (agent_key,),
    )
    return row["io_scope"] if row else None


async def _log_decision(agent_key: str, decision_id: str, result: dict) -> None:
    from app.core.config import settings
    from app.db import _PH, execute_insert
    try:
        await execute_insert(
            f"INSERT INTO guardrails_decision_log "
            f"(agent_key, decision_id, domain_key, decision, risk_score, matched_rule_count, tenant_id) "
            f"VALUES ({_PH}, {_PH}, 'global', {_PH}, {_PH}, {_PH}, {_PH})",
            (agent_key, decision_id, result["decision"], result["riskScore"],
             len(result["matchedRules"]), settings.tenant_default_id or "default"),
        )
    except Exception:  # noqa: BLE001 — 감사 실패가 요청 흐름을 막아선 안 됨
        logger.exception("[guardrails_gate] decision log 기록 실패")


def install() -> None:
    """`orchestrator._exec_api_call` 을 게이트 래퍼로 교체. main.py lifespan 에서 1회 호출."""
    import app.agents.orchestrator as orch
    from app.services.guardrails_mcp import validate

    if getattr(orch, "_guardrails_gate_installed", False):
        return
    original = orch._exec_api_call

    async def gated(method: str, path: str, body: dict | None, params: dict | None, token: str | None) -> str:
        from app.core.config import settings
        if not settings.guardrails_enabled:
            return await original(method, path, body, params, token)

        agent_key = _resolve_agent_key(path)
        if not agent_key:
            return await original(method, path, body, params, token)

        try:
            scope = await _get_scope(agent_key)
        except Exception:  # noqa: BLE001 — DB 조회 실패 시 게이트 스킵(무중단)
            logger.exception("[guardrails_gate] scope 조회 실패, 게이트 스킵")
            return await original(method, path, body, params, token)
        if not scope:
            return await original(method, path, body, params, token)

        # ── 입력 검사 ──
        if scope in ("input", "both") and body:
            text = json.dumps(body, ensure_ascii=False)
            result = await validate(text, tool="validate_input")
            decision_id = str(uuid.uuid4())
            await _log_decision(agent_key, decision_id, result)
            if result["decision"] in ("block", "escalate"):
                return f"HTTP 403\n{json.dumps({'detail': '[BLOCKED] guardrails: PII/신용정보 탐지', 'decisionId': decision_id}, ensure_ascii=False)}"
            if result["decision"] in ("redact", "sanitize") and result["matchedRules"]:
                try:
                    body = json.loads(result["redactedText"])
                except Exception:  # noqa: BLE001 — 재파싱 실패 시 원본 유지(무중단)
                    pass

        raw = await original(method, path, body, params, token)

        # ── 출력 검사 ──
        if scope in ("output", "both") and raw:
            head, _, rest = raw.partition("\n")
            if rest:
                result = await validate(rest, tool="validate_output")
                decision_id = str(uuid.uuid4())
                await _log_decision(agent_key, decision_id, result)
                if result["decision"] in ("block", "escalate"):
                    rest = "[BLOCKED]"
                elif result["decision"] in ("redact", "sanitize") and result["matchedRules"]:
                    rest = result["redactedText"]
                raw = f"{head}\n{rest}"

        return raw

    orch._exec_api_call = gated
    orch._guardrails_gate_installed = True
    logger.info("[guardrails_gate] installed")
