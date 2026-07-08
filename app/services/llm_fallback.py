"""Ollama HTTP fallback — Claude API 장애 시 로컬 LLM 전환 (F3).

참조: SmartHaccp-MultiAgent app/services/llm_fallback.py (그대로 유지)
호출 우선순위: Claude API → Ollama (/api/chat, 비동기 httpx)
tool_use 미지원 — 순수 텍스트 응답만 반환.
"""
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


async def call_ollama(
    messages: list[dict[str, Any]],
    system: str,
    model: str | None = None,
    base_url: str | None = None,
    usage_out: dict | None = None,
) -> str:
    """Ollama /api/chat 엔드포인트 호출. 실패 시 에러 메시지 반환.

    usage_out 전달 시 토큰 사용량(prompt_eval_count/eval_count)을 누적 기록한다.
    """
    _model = model or settings.ollama_model
    _base = (base_url or settings.ollama_base_url).rstrip("/")

    def _to_str(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(item.get("text") or str(item))
                else:
                    parts.append(str(item))
            return " ".join(parts)
        return str(content)

    ollama_messages = [{"role": "system", "content": system}] + [
        {"role": m["role"], "content": _to_str(m["content"])}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]

    payload = {"model": _model, "messages": ollama_messages, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{_base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if usage_out is not None:
                usage_out["input_tokens"] = usage_out.get("input_tokens", 0) + int(data.get("prompt_eval_count") or 0)
                usage_out["output_tokens"] = usage_out.get("output_tokens", 0) + int(data.get("eval_count") or 0)
            return data.get("message", {}).get("content", "")
    except Exception as exc:  # noqa: BLE001
        logger.error("[llm_fallback] Ollama 호출 실패(%s %s): %s", _base, _model, exc)
        raise RuntimeError(
            f"[AI 서비스 일시 장애] 로컬 LLM({_model}) 응답 불가. Ollama 실행 및 모델 설치를 확인하세요."
        ) from exc
