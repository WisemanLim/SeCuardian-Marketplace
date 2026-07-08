"""otel-collector — OpenTelemetry Collector metrics/status MCP tool proxy.

마운트 경로: /api/addon/otel-collector/...
엔드포인트:
  GET  /tools              지원 도구 목록
  POST /tools/{tool_name}  도구 실행
  GET  /status             헬스 요약 (otel_health 호출)
  GET  /config             환경변수 설정 조회
"""
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["otel-collector"])


# ─── 환경변수 설정 ────────────────────────────────────────────────────────────

def _health_url() -> str:
    return os.getenv("OTEL_HEALTH_URL", "http://localhost:13133")


def _zpages_url() -> str:
    return os.getenv("OTEL_ZPAGES_URL", "http://localhost:55679")


def _metrics_url() -> str:
    return os.getenv("OTEL_METRICS_URL", "http://localhost:8889")


# ─── 도구 목록 정의 ──────────────────────────────────────────────────────────

_TOOLS = [
    {
        "name": "otel_health",
        "description": "OpenTelemetry Collector 헬스 상태를 확인합니다. health_check extension 응답을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "otel_pipeline",
        "description": "Collector 파이프라인 통계를 조회합니다. receiver/processor/exporter 별 수신·전송 건수를 포함합니다.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "otel_extensions",
        "description": "활성화된 Collector extension 목록과 상태를 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "otel_metrics_sample",
        "description": "Prometheus exposition format으로 노출된 Collector 자체 메트릭 샘플 (최대 2000자)을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# ─── 내부 헬퍼 ───────────────────────────────────────────────────────────────

async def _fetch(url: str, timeout: float = 10.0) -> tuple[int, Any]:
    """URL을 GET으로 호출하고 (status_code, body) 튜플을 반환합니다."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            return resp.status_code, resp.json()
        return resp.status_code, resp.text


# ─── 엔드포인트 ──────────────────────────────────────────────────────────────

@router.get("/tools")
async def list_tools(user: dict = Depends(get_current_user)):
    """지원 도구 목록과 입력 스키마를 반환합니다."""
    return {"tools": _TOOLS}


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = {}


@router.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    body: ToolCallRequest,
    user: dict = Depends(get_current_user),
):
    """도구를 실행하고 외부 OpenTelemetry Collector 응답을 반환합니다."""
    tool = next((t for t in _TOOLS if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    try:
        if tool_name == "otel_health":
            status_code, result = await _fetch(f"{_health_url()}/")
            return {"result": result, "status_code": status_code}

        elif tool_name == "otel_pipeline":
            status_code, result = await _fetch(f"{_zpages_url()}/debug/pipelinez")
            return {"result": result, "status_code": status_code}

        elif tool_name == "otel_extensions":
            status_code, result = await _fetch(f"{_zpages_url()}/debug/extensionz")
            return {"result": result, "status_code": status_code}

        elif tool_name == "otel_metrics_sample":
            status_code, result = await _fetch(f"{_metrics_url()}/metrics")
            # Prometheus 텍스트는 클 수 있으므로 첫 2000자만 반환
            if isinstance(result, str):
                result = result[:2000]
            return {"result": result, "status_code": status_code}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"OpenTelemetry Collector 응답 타임아웃: {tool_name}")
    except httpx.ConnectError as e:
        raise HTTPException(status_code=502, detail=f"OpenTelemetry Collector 연결 실패: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OpenTelemetry Collector 호출 실패: {str(e)}")

    return {"result": None, "error": "Unknown tool"}


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    """OpenTelemetry Collector 헬스 요약을 반환합니다 (otel_health 단축 경로)."""
    try:
        status_code, result = await _fetch(f"{_health_url()}/")
        healthy = status_code == 200
        return {
            "healthy": healthy,
            "status_code": status_code,
            "detail": result,
            "health_url": _health_url(),
        }
    except httpx.ConnectError:
        return {
            "healthy": False,
            "status_code": None,
            "detail": "Connection refused — Collector may not be running",
            "health_url": _health_url(),
        }
    except httpx.HTTPError as e:
        return {
            "healthy": False,
            "status_code": None,
            "detail": str(e),
            "health_url": _health_url(),
        }


@router.get("/config")
async def get_config(user: dict = Depends(require_role("supervisor", "admin"))):
    """현재 환경변수 설정을 반환합니다 (credential 없음)."""
    return {
        "OTEL_HEALTH_URL": _health_url(),
        "OTEL_ZPAGES_URL": _zpages_url(),
        "OTEL_METRICS_URL": _metrics_url(),
        "tools_count": len(_TOOLS),
    }
