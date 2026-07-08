"""F-PG 토큰 사용량 추적 test (관측성, PRD §7.9) — call_ollama usage_out → playground_runs + dashboard 합계.
httpx monkeypatch 로 Ollama /api/chat 응답(prompt_eval_count/eval_count) 시뮬레이션.
"""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402
import app.services.llm_fallback as lf  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'u1','role':'user','username':'u1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── mock Ollama /api/chat with token counts ──
class _Resp:
    status_code = 200
    def raise_for_status(self): pass
    def json(self):
        return {"message": {"content": "mocked answer"}, "prompt_eval_count": 42, "eval_count": 17}
class _Client:
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def post(self, url, json=None): return _Resp()

_orig = lf.httpx.AsyncClient
lf.httpx.AsyncClient = _Client

with TestClient(m.app) as c:
    r = c.post("/api/playground/run", headers=H, json={"prompt": "count my tokens"})
    chk(r.status_code == 201, f"run 201 ({r.status_code})")
    body = r.json()
    chk(body["provider"] == "ollama", f"provider ollama (mock) ({body.get('provider')})")
    chk(body["input_tokens"] == 42 and body["output_tokens"] == 17, f"tokens recorded ({body.get('input_tokens')},{body.get('output_tokens')})")

    # history exposes tokens
    r = c.get("/api/playground/runs", headers=H)
    run0 = r.json()["runs"][0]
    chk(run0["input_tokens"] == 42 and run0["output_tokens"] == 17, "history has tokens")

    # dashboard summary aggregates tokens
    r = c.get("/api/dashboard/summary", headers=H)
    pg = r.json()["playground"]
    chk(pg["runs"] == 1 and pg["tokens"] == 59, f"dashboard playground tokens sum=59 ({pg})")

    # degrade path (no mock error) → tokens 0
    lf.httpx.AsyncClient = _orig
    import app.core.config as cfg
    cfg.settings.ollama_base_url = "http://127.0.0.1:1"
    r = c.post("/api/playground/run", headers=H, json={"prompt": "degrade"})
    chk(r.json()["provider"] == "degraded" and r.json()["input_tokens"] == 0, "degrade → tokens 0")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
