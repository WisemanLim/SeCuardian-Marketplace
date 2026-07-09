import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_user, require_role

router = APIRouter(tags=["caddy-proxy"])

CADDY_ADMIN_URL = os.getenv("CADDY_ADMIN_URL", "http://localhost:2019")
CADDY_ADMIN_TOKEN = os.getenv("CADDY_ADMIN_TOKEN", "")

TOOLS = [
    {
        "name": "caddy_status",
        "description": "Retrieve Caddy server status via metrics or config endpoint.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "caddy_config",
        "description": "Retrieve the full current Caddy configuration.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "caddy_routes",
        "description": "List all HTTP server routes from Caddy configuration.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "caddy_reload",
        "description": "Reload Caddy with a new JSON configuration (supervisor/admin only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "description": "Full Caddy JSON configuration to load.",
                }
            },
            "required": ["config"],
        },
    },
]


def _build_headers() -> dict:
    headers = {"Accept": "application/json"}
    if CADDY_ADMIN_TOKEN:
        headers["Authorization"] = f"Bearer {CADDY_ADMIN_TOKEN}"
    return headers


async def _caddy_get(path: str) -> Any:
    url = f"{CADDY_ADMIN_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=_build_headers())
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Caddy unreachable: {e}")


async def _caddy_post(path: str, body: Any) -> Any:
    url = f"{CADDY_ADMIN_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=body, headers=_build_headers())
            resp.raise_for_status()
            return resp.json() if resp.content else {"ok": True}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Caddy unreachable: {e}")


# --- Tool dispatch ---

async def _run_caddy_status() -> Any:
    try:
        return await _caddy_get("/metrics")
    except HTTPException:
        return await _caddy_get("/config")


async def _run_caddy_config() -> Any:
    return await _caddy_get("/config/")


async def _run_caddy_routes() -> Any:
    return await _caddy_get("/config/apps/http/servers")


async def _run_caddy_reload(config: dict) -> Any:
    return await _caddy_post("/load", config)


# --- Endpoints ---

@router.get("/tools")
async def list_tools(current_user=Depends(get_current_user)):
    return {"tools": TOOLS}


@router.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    body = await request.json()
    arguments = body.get("arguments", {})

    if tool_name == "caddy_status":
        result = await _run_caddy_status()
    elif tool_name == "caddy_config":
        result = await _run_caddy_config()
    elif tool_name == "caddy_routes":
        result = await _run_caddy_routes()
    elif tool_name == "caddy_reload":
        await require_role(["supervisor", "admin"])(current_user)
        config = arguments.get("config")
        if config is None:
            raise HTTPException(status_code=422, detail="'config' argument required")
        result = await _run_caddy_reload(config)
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return {"tool": tool_name, "result": result}


@router.get("/status")
async def caddy_health_summary(current_user=Depends(get_current_user)):
    try:
        data = await _run_caddy_status()
        return {"healthy": True, "data": data}
    except HTTPException as e:
        return {"healthy": False, "detail": e.detail}


@router.get("/config")
async def caddy_connection_config(current_user=Depends(get_current_user)):
    masked_url = CADDY_ADMIN_URL
    has_token = bool(CADDY_ADMIN_TOKEN)
    return {
        "admin_url": masked_url,
        "auth_configured": has_token,
    }
