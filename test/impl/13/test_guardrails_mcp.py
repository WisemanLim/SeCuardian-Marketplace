"""F-GRD MCP Server 프록시 test — MCP 우선 + 실패 시 로컬 폴백. httpx monkeypatch 로 MCP 시뮬레이션."""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

import asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402
import app.main as m  # noqa: E402
import app.services.guardrails_mcp as gmcp  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'sup1','role':'supervisor','username':'sup1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── unit: MCP 미설정 → 로컬 ──
settings.guardrails_mcp_url = ""
r = asyncio.run(gmcp.validate("email a@b.com"))
chk(r["source"] == "local" and r["decision"] == "redact", f"MCP 미설정 -> local ({r['source']},{r['decision']})")

# ── unit: MCP 설정 + 정상 응답 → source=mcp, MCP 결정 반영 ──
settings.guardrails_mcp_url = "http://fake-mcp:8080"

class _Resp:
    def __init__(self, data): self._d = data
    def raise_for_status(self): pass
    def json(self): return self._d

class _Client:
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def post(self, url, json=None, headers=None):
        # MCP 가 escalate 로 강판정했다고 시뮬레이션(로컬은 redact 였을 텍스트)
        return _Resp({"decision": "escalate", "riskScore": 0.9, "matchedRules": ["mcp.rule"],
                      "categories": ["pii.custom"], "normalizedText": json["text"],
                      "redactedText": "[MCP-REDACTED]", "policyVersion": "1.0.0", "latencyMs": 12})

_orig_client = gmcp.httpx.AsyncClient
gmcp.httpx.AsyncClient = _Client
r = asyncio.run(gmcp.validate("email a@b.com", tool="validate_input"))
chk(r["source"] == "mcp" and r["decision"] == "escalate", f"MCP 정상 -> source=mcp, MCP 결정 ({r['source']},{r['decision']})")
chk(r["redactedText"] == "[MCP-REDACTED]" and r["policyVersion"] == "1.0.0", "MCP 응답 필드 정규화")

# ── unit: MCP 설정 but 연결 실패 → local-fallback ──
class _FailClient(_Client):
    async def post(self, url, json=None, headers=None):
        raise RuntimeError("connection refused")
gmcp.httpx.AsyncClient = _FailClient
r = asyncio.run(gmcp.validate("key sk-abcdefghijklmnopqrstuvwx"))
chk(r["source"] == "local-fallback" and r["decision"] == "block", f"MCP 실패 -> local-fallback + 로컬 승격 ({r['source']},{r['decision']})")

gmcp.httpx.AsyncClient = _orig_client
settings.guardrails_mcp_url = ""

# ── integration: /api/guardrails/test 가 MCP 경로 사용(미설정 시 local) ──
with TestClient(m.app) as c:
    r = c.post("/api/guardrails/test", headers=H, json={"text": "email a@b.com", "domain": "global"})
    chk(r.status_code == 200 and r.json().get("source") == "local", f"/test MCP 미설정 -> local source ({r.json().get('source')})")
    chk(r.json()["decision"] == "redact", "/test 로컬 판정 정상")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
