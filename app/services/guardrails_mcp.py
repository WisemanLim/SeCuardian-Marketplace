"""Guardrails MCP Server 프록시 클라이언트 (F-GRD, PRD §7.8.1/§7.8.2).

wise-Guardrails MCP Server(:8080) 의 `POST /mcp/tools/validate_input|validate_output` 를 호출하고,
연결 불가/미구성/타임아웃 시 로컬 판정기(`guardrails_detector.decide`)로 **자동 폴백**한다(무중단, §7.8.6).
MCP 응답은 §7.8.2 ValidateResponse 계약을 그대로 사용하므로 로컬 결과와 동일 형태로 정규화한다.

설정: `guardrails_mcp_url`(빈 값이면 로컬 전용), `guardrails_api_key`(x-api-key), `guardrails_enabled`.
"""
import logging

import httpx

from app.core.config import settings
from app.services.guardrails_detector import decide as _local_decide

logger = logging.getLogger("uvicorn.error")

# MCP 응답 정규화 시 로컬 계약과 맞출 키
_KEYS = ("decision", "riskScore", "matchedRules", "categories", "normalizedText", "redactedText")


def _normalize(data: dict, text: str) -> dict:
    return {
        "decision": data.get("decision", "allow"),
        "riskScore": float(data.get("riskScore", 0.0) or 0.0),
        "matchedRules": data.get("matchedRules", []) or [],
        "categories": data.get("categories", []) or [],
        "normalizedText": data.get("normalizedText", text),
        "redactedText": data.get("redactedText", text),
        "source": "mcp",
        "policyVersion": data.get("policyVersion"),
        "latencyMs": data.get("latencyMs"),
    }


async def validate(text: str, domain: str = "global", tool: str = "validate_input",
                   session_id: str = "", tenant_id: str = "") -> dict:
    """MCP Server 로 판정 요청. 실패 시 로컬 decide 폴백.

    반환에는 `source`("mcp"|"local"|"local-fallback") 를 포함해 어느 경로로 판정됐는지 표시한다.
    """
    if not settings.guardrails_mcp_url:
        return {**_local_decide(text), "source": "local"}

    url = settings.guardrails_mcp_url.rstrip("/") + f"/mcp/tools/{tool}"
    headers = {"Content-Type": "application/json"}
    if settings.guardrails_api_key:
        headers["x-api-key"] = settings.guardrails_api_key
    payload = {"text": text, "domain": domain, "locale": "ko-KR",
               "sessionId": session_id, "tenantId": tenant_id}
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:  # PRD §7.8.2 권장 타임아웃 3~5s
            resp = await c.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return _normalize(resp.json(), text)
    except Exception as exc:  # noqa: BLE001 — MCP 장애 → 로컬 폴백(무중단, §7.8.6)
        logger.warning("[guardrails_mcp] MCP 호출 실패, 로컬 폴백: %s", exc)
        return {**_local_decide(text), "source": "local-fallback"}
