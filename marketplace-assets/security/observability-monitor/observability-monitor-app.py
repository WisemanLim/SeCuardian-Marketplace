"""observability-monitor — Observability 스택 모니터 Addon (SeCuardian router_observability.py 이식).
# Source: SeCuardian | License: Apache-2.0 | Usage: internal only

마운트: /api/addon/observability-monitor
  GET    /status         — observability_query: Prometheus/Grafana/Loki 헬스
  GET    /metrics        — metrics_query: PromQL instant query 프록시
  POST   /mttd/alert     — mttd_record: 탐지 이벤트 수집(webhook, 무인증)
  POST   /mttd/response  — 대응 완료 이벤트(webhook, 무인증)
  GET    /mttd           — mttd_query: MTTD/MTTR 집계
  DELETE /mttd           — 저장소 초기화

이식 노트: settings 비의존 — PROMETHEUS_URL/GRAFANA_URL/LOKI_URL env. ⚠️ from __future__ import annotations 금지.
"""
import datetime
import os
from collections import deque
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_current_user

_mttd_store: deque = deque(maxlen=500)

router = APIRouter(tags=["observability-monitor"])


def _prom() -> str:
    return os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")


def _grafana() -> str:
    return os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")


def _loki() -> str:
    return os.getenv("LOKI_URL", "http://localhost:3100").rstrip("/")


@router.get("/status")
async def observability_status(_: dict = Depends(get_current_user)) -> dict:
    """Prometheus / Grafana / Loki 헬스. Orchestrator intent: observability_query"""
    results: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{_prom()}/-/ready")
            results["prometheus"] = {"status": "UP" if r.status_code == 200 else "DEGRADED", "code": r.status_code}
        except httpx.ConnectError:
            results["prometheus"] = {"status": "DOWN"}
        try:
            r = await client.get(f"{_grafana()}/api/health")
            body = r.json() if r.status_code == 200 else {}
            results["grafana"] = {"status": body.get("database", "UP") if r.status_code == 200 else "DEGRADED", "code": r.status_code}
        except httpx.ConnectError:
            results["grafana"] = {"status": "DOWN"}
        try:
            r = await client.get(f"{_loki()}/ready")
            results["loki"] = {"status": "UP" if r.status_code == 200 else "DEGRADED", "code": r.status_code}
        except httpx.ConnectError:
            results["loki"] = {"status": "DOWN"}
    overall = "UP" if all(v.get("status") in {"UP", "ok"} for v in results.values()) else "PARTIAL"
    return {"overall": overall, "services": results, "endpoints": {"prometheus": _prom(), "grafana": _grafana(), "loki": _loki()}}


@router.get("/metrics")
async def query_metrics(query: str = Query(..., description="PromQL 쿼리"), _: dict = Depends(get_current_user)) -> dict:
    """Prometheus instant query 프록시. Orchestrator intent: metrics_query"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{_prom()}/api/v1/query", params={"query": query})
            r.raise_for_status()
            return r.json()
        except httpx.ConnectError:
            return {"status": "error", "error": "Prometheus DOWN", "data": None}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "error": str(exc), "data": None}


@router.post("/mttd/alert", status_code=202)
async def record_alert(request: Request) -> dict:
    """탐지 이벤트 기록(webhook, 무인증). Orchestrator intent: mttd_record"""
    body = await request.json()
    event = {
        "type": "alert",
        "detected_at": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
        "alert_id": body.get("alert_id", ""),
        "source": body.get("source", "unknown"),
        "severity": body.get("severity", "medium"),
        "responded_at": None,
        "mttd_seconds": None,
        "mttr_seconds": None,
    }
    attack_time_str = body.get("attack_time")
    if attack_time_str:
        try:
            attack_time = datetime.datetime.fromisoformat(attack_time_str.rstrip("Z"))
            if attack_time.tzinfo is None:  # naive 입력은 UTC 로 간주(offset 혼합 subtract 방지)
                attack_time = attack_time.replace(tzinfo=datetime.UTC)
            detected = datetime.datetime.now(datetime.UTC)
            event["mttd_seconds"] = (detected - attack_time).total_seconds()
        except ValueError:
            pass
    _mttd_store.append(event)
    return {"accepted": True, "event": event}


@router.post("/mttd/response", status_code=202)
async def record_response(request: Request) -> dict:
    """대응 완료 이벤트 기록(webhook, 무인증) — alert_id 로 MTTR 계산."""
    body = await request.json()
    alert_id = body.get("alert_id", "")
    responded_at = datetime.datetime.now(datetime.UTC)
    for event in reversed(list(_mttd_store)):
        if event.get("alert_id") == alert_id and event.get("type") == "alert":
            event["responded_at"] = responded_at.isoformat() + "Z"
            try:
                detected = datetime.datetime.fromisoformat(event["detected_at"].rstrip("Z"))
                event["mttr_seconds"] = (responded_at - detected).total_seconds()
            except (ValueError, KeyError):
                pass
            return {"accepted": True, "updated": event}
    resp_event = {"type": "response", "alert_id": alert_id, "responded_at": responded_at.isoformat() + "Z", "source": body.get("source", "unknown")}
    _mttd_store.append(resp_event)
    return {"accepted": True, "event": resp_event}


@router.get("/mttd")
async def get_mttd_stats(_: dict = Depends(get_current_user)) -> dict:
    """MTTD / MTTR 집계. Orchestrator intent: mttd_query"""
    events = [e for e in _mttd_store if e.get("type") == "alert"]
    mttd_values = [e["mttd_seconds"] for e in events if e.get("mttd_seconds") is not None]
    mttr_values = [e["mttr_seconds"] for e in events if e.get("mttr_seconds") is not None]

    def _avg(vals: list) -> Optional[float]:
        return round(sum(vals) / len(vals), 2) if vals else None

    return {
        "total_alerts": len(events),
        "mttd": {"avg_seconds": _avg(mttd_values), "min_seconds": round(min(mttd_values), 2) if mttd_values else None, "max_seconds": round(max(mttd_values), 2) if mttd_values else None, "sample_count": len(mttd_values)},
        "mttr": {"avg_seconds": _avg(mttr_values), "min_seconds": round(min(mttr_values), 2) if mttr_values else None, "max_seconds": round(max(mttr_values), 2) if mttr_values else None, "sample_count": len(mttr_values)},
        "recent_events": list(_mttd_store)[-20:],
    }


@router.delete("/mttd")
async def clear_mttd(_: dict = Depends(get_current_user)) -> dict:
    """MTTD/MTTR 저장소 초기화."""
    count = len(_mttd_store)
    _mttd_store.clear()
    return {"cleared": count}
