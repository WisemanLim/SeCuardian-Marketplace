"""F-WEB 대시보드 실시간 위젯 test — /api/dashboard/summary + /activity 집계."""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"  # playground degrade

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'sup1','role':'supervisor','username':'sup1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    # baseline summary
    r = c.get("/api/dashboard/summary", headers=H)
    chk(r.status_code == 200, "summary 200")
    s = r.json()
    chk(s["server"]["status"] == "ok" and "vector_backend" in s["server"], "server block")
    chk(s["agents"]["total"] >= 4 and s["agents"]["enabled"] >= 4, f"agents counts ({s['agents']})")
    chk(all(k in s for k in ("marketplace", "workflow", "rag", "playground", "guardrails")), "all sections present")
    base_pg = s["playground"]["runs"]
    base_grd = s["guardrails"]["decisions"]

    # generate activity
    c.post("/api/playground/run", headers=H, json={"prompt": "hi"})
    c.post("/api/guardrails/agents/chat/config", headers=H, json={"domain_key": "global", "enabled": True})
    c.post("/api/guardrails/test", headers=H, json={"text": "key sk-abcdefghijklmnopqrstuvwx", "domain": "global", "agent_key": "chat"})
    cid = c.post("/api/rag/collections", headers=H, json={"name": "kb"}).json()["id"]

    r = c.get("/api/dashboard/summary", headers=H)
    s = r.json()
    chk(s["playground"]["runs"] == base_pg + 1, f"playground run counted ({s['playground']['runs']})")
    chk(s["guardrails"]["decisions"] == base_grd + 1 and s["guardrails"]["blocked"] >= 1, f"guardrails decision+blocked ({s['guardrails']})")
    chk(s["rag"]["collections"] >= 1, "rag collection counted")

    # activity stream
    r = c.get("/api/dashboard/activity?limit=10", headers=H)
    chk(r.status_code == 200, "activity 200")
    kinds = {a["kind"] for a in r.json()["activity"]}
    chk("playground" in kinds and "guardrails" in kinds, f"activity has playground+guardrails ({kinds})")

    # unauth
    chk(c.get("/api/dashboard/summary").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
