"""F-PG functional test — fresh sqlite, TestClient. Degrade path, RAG-augmented run, history."""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"
# 오프라인 시험 환경 — Ollama 미가동을 전제로 degrade 경로만 검증(존재하지 않는 포트로 강제)
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

TOK = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
H = {"Authorization": f"Bearer {TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    r = c.get("/api/agent-config/", headers=H)
    keys = [a["agent_key"] for a in (r.json() if isinstance(r.json(), list) else r.json().get("agents", []))]
    chk("playground" in keys, f"playground agent seeded ({keys})")

    # 1) plain run (no RAG) — Ollama unreachable -> degrade, still 201
    r = c.post("/api/playground/run", headers=H, json={"prompt": "hello world"})
    chk(r.status_code == 201, f"run 201 ({r.status_code} {r.text[:150]})")
    body = r.json()
    chk(body["provider"] == "degraded", f"degrade provider on unreachable ollama ({body.get('provider')})")
    chk("hello world" in body["response_text"], f"degrade text echoes prompt ({body.get('response_text')})")
    chk(body["citations_json"] == "[]", f"no citations without rag_collection_id ({body.get('citations_json')})")
    chk(body["latency_ms"] >= 0, "latency recorded")

    # 2) any authenticated user (no RBAC gate) can run
    chk(r.status_code != 403, "no RBAC gate on run (plain user allowed)")

    # 3) RAG-augmented run
    stok = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
    SH = {"Authorization": f"Bearer {stok}"}
    rc = c.post("/api/rag/collections", headers=SH, json={"name": "kb"})
    cid = rc.json()["id"]
    c.post(f"/api/rag/collections/{cid}/documents", headers=SH, json={
        "title": "doc", "text": "The SECRET-CODE-9981 unlocks the vault door mechanism."
    })
    r = c.post("/api/playground/run", headers=H, json={"prompt": "SECRET-CODE-9981", "rag_collection_id": cid})
    chk(r.status_code == 201, f"rag-augmented run 201 ({r.status_code})")
    body = r.json()
    import json as _json
    cits = _json.loads(body["citations_json"])
    chk(len(cits) >= 1, f"citations populated ({cits})")
    chk("SECRET-CODE-9981" in cits[0]["text"], f"citation matches injected doc ({cits[0]['text'][:50]})")

    # 4) missing rag_collection_id -> 404
    r = c.post("/api/playground/run", headers=H, json={"prompt": "x", "rag_collection_id": 99999})
    chk(r.status_code == 404, "missing rag collection -> 404")

    # 5) history — 2건(plain + rag-augmented); 404 케이스는 insert 되지 않음
    r = c.get("/api/playground/runs", headers=H)
    chk(r.status_code == 200 and len(r.json()["runs"]) == 2, f"history = 2 runs ({len(r.json().get('runs', []))})")

    # 6) unauth
    chk(c.get("/api/playground/runs").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
