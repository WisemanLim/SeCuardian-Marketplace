"""플레이그라운드 에이전트 — ADDON 판 (emb_playground).

내장 라우터 app/routers/router_playground.py (F-PG) 의 ADDON 패키징.
로더가 /api/addon/emb_playground prefix 로 마운트한다.
설정은 내장판(settings.*) 대신 환경변수로 주입한다.
OLLAMA_URL 환경변수로 LLM 호출 시도, 미구성/장애 시 degrade 텍스트로 완료(무중단).
실행 기록은 인메모리 deque 로 보관.
"""
import datetime
import os
import time
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["emb_playground"])

PLAYGROUND_ENABLED = os.getenv("PLAYGROUND_ENABLED", "true").lower() == "true"
OLLAMA_URL = os.getenv("PLAYGROUND_OLLAMA_URL", os.getenv("OLLAMA_URL", "http://localhost:11434"))
OLLAMA_MODEL = os.getenv("PLAYGROUND_OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "llama3.2"))
PLAYGROUND_MAX_RUNS = int(os.getenv("PLAYGROUND_MAX_RUNS", "200"))

# 인메모리 저장소
_runs: deque[dict] = deque(maxlen=PLAYGROUND_MAX_RUNS)
_next_id: list[int] = [1]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _next() -> int:
    v = _next_id[0]
    _next_id[0] += 1
    return v


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system: str = ""
    model: str = ""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


async def _call_ollama(messages: list[dict], system: str, model: str) -> tuple[str, str]:
    """Ollama API 호출 — 실패 시 degrade 텍스트 반환."""
    try:
        import httpx
        payload: dict = {
            "model": model or OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "") or data.get("response", "")
            return text, "ollama"
    except Exception:
        return f"[degraded] {messages[-1].get('content', '')}", "degraded"


@router.get("/status")
async def playground_status(_: dict = Depends(get_current_user)):
    """플레이그라운드 에이전트 상태."""
    return {
        "playground_enabled": PLAYGROUND_ENABLED,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "runs_stored": len(_runs),
        "source": "emb_playground (in-memory ADDON)",
    }


@router.post("/run", status_code=201)
async def run(body: RunRequest, user: dict = Depends(get_current_user)):
    """LLM 실행 — Ollama 호출, 미구성 시 degrade(무중단)."""
    if not PLAYGROUND_ENABLED:
        raise HTTPException(403, "Playground disabled — set PLAYGROUND_ENABLED=true")
    messages = [{"role": "user", "content": body.prompt}]
    started = time.monotonic()
    text, provider = await _call_ollama(messages, body.system, body.model)
    latency_ms = int((time.monotonic() - started) * 1000)
    rid = _next()
    record = {
        "id": rid,
        "prompt": body.prompt,
        "system_prompt": body.system,
        "model": body.model or OLLAMA_MODEL,
        "response_text": text,
        "provider": provider,
        "latency_ms": latency_ms,
        "created_by": user.get("username") or user.get("sub") or "",
        "created_at": _now(),
    }
    _runs.appendleft(record)
    return record


@router.get("/runs")
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
):
    """실행 이력 목록 (최신 순)."""
    return {"total": len(_runs), "runs": list(_runs)[:limit]}


@router.get("/runs/{run_id}")
async def get_run(run_id: int, _: dict = Depends(get_current_user)):
    """실행 단건 조회."""
    run = next((r for r in _runs if r["id"] == run_id), None)
    if not run:
        raise HTTPException(404, f"run {run_id} not found")
    return run


@router.delete("/runs")
async def clear_runs(_: dict = Depends(get_current_user)):
    """실행 이력 전체 삭제."""
    count = len(_runs)
    _runs.clear()
    return {"cleared": count}
