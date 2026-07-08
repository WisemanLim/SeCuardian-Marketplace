"""F-WF functional test — fresh sqlite, TestClient. DAG exec, condition, HITL, agent, retry, RBAC."""
import json
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

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}
UTOK = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {UTOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

def mkwf(c, defn, name="wf"):
    r = c.post("/api/workflows", headers=H, json={"name": name, "definition_json": defn})
    assert r.status_code == 201, r.text
    return r.json()["id"]

with TestClient(m.app) as c:
    # seed check
    r = c.get("/api/agent-config/", headers=H)
    keys = [a["agent_key"] for a in (r.json() if isinstance(r.json(), list) else r.json().get("agents", []))]
    chk("workflow" in keys, f"workflow agent seeded ({keys})")

    # RBAC + validation
    r = c.post("/api/workflows", headers=UH, json={"name": "x", "definition_json": {}})
    chk(r.status_code == 403, "user create -> 403")
    r = c.post("/api/workflows", headers=H, json={"name": "x", "definition_json": {"nodes": [{"id": "a", "type": "bogus"}]}})
    chk(r.status_code == 422, "bad node type -> 422")
    r = c.post("/api/workflows", headers=H, json={"name": "x", "definition_json": {"nodes": [{"id": "a", "type": "trigger"}], "edges": [{"source": "a", "target": "z"}]}})
    chk(r.status_code == 422, "edge unknown node -> 422")

    # 1) linear: trigger -> transform -> notify (template render)
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "x", "type": "transform", "config": {"output": {"msg": "$t.input.name"}}},
        {"id": "n", "type": "notify", "config": {"message": "hi {{x.msg}}"}},
    ], "edges": [{"source": "t", "target": "x"}, {"source": "x", "target": "n"}]}
    wid = mkwf(c, defn, "linear")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {"name": "world"}})
    chk(r.status_code == 201 and r.json()["status"] == "completed", f"linear run completed ({r.json().get('status')})")
    out = json.loads(r.json()["output_json"])
    chk(out.get("x", {}).get("msg") == "world", f"transform resolved $ref ({out.get('x')})")
    chk(out.get("n", {}).get("message") == "hi world", f"notify rendered template ({out.get('n')})")

    # 2) condition branch: true path fires, false pruned
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "c", "type": "condition", "config": {"left": "$t.input.n", "op": ">", "right": 5}},
        {"id": "hi", "type": "notify", "config": {"message": "big"}},
        {"id": "lo", "type": "notify", "config": {"message": "small"}},
    ], "edges": [
        {"source": "t", "target": "c"},
        {"source": "c", "target": "hi", "when": "true"},
        {"source": "c", "target": "lo", "when": "false"},
    ]}
    wid = mkwf(c, defn, "cond")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {"n": 10}})
    rid = r.json()["id"]
    out = json.loads(r.json()["output_json"])
    chk(r.json()["status"] == "completed", "cond run completed")
    chk("hi" in out and "lo" not in out, f"true branch fired, false pruned ({list(out)})")
    nodes = c.get(f"/api/workflow-runs/{rid}/nodes", headers=H).json()["nodes"]
    nkeys = {n["node_id"]: n["status"] for n in nodes}
    chk(nkeys.get("hi") == "completed" and "lo" not in nkeys, f"node runs: hi run, lo not ({nkeys})")

    # false path
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {"n": 1}})
    out = json.loads(r.json()["output_json"])
    chk("lo" in out and "hi" not in out, f"false branch fired ({list(out)})")

    # 3) HITL: pause -> approve -> complete
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "h", "type": "hitl"},
        {"id": "n", "type": "notify", "config": {"message": "done"}},
    ], "edges": [{"source": "t", "target": "h"}, {"source": "h", "target": "n"}]}
    wid = mkwf(c, defn, "hitl")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    rid = r.json()["id"]
    chk(r.json()["status"] == "waiting_hitl" and r.json()["waiting_node_id"] == "h", f"hitl pauses ({r.json().get('status')})")
    # user cannot approve
    r = c.post(f"/api/workflow-runs/{rid}/hitl", headers=UH, json={"approved": True})
    chk(r.status_code == 403, "user hitl -> 403")
    r = c.post(f"/api/workflow-runs/{rid}/hitl", headers=H, json={"approved": True})
    chk(r.status_code == 200 and r.json()["status"] == "completed", f"hitl approve -> completed ({r.json().get('status')})")

    # HITL reject
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    rid = r.json()["id"]
    r = c.post(f"/api/workflow-runs/{rid}/hitl", headers=H, json={"approved": False})
    chk(r.json()["status"] == "failed", f"hitl reject -> failed ({r.json().get('status')})")

    # 4) agent node: existing enabled agent (chat) invoked
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "chat"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    wid = mkwf(c, defn, "agent-ok")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    out = json.loads(r.json()["output_json"])
    chk(r.json()["status"] == "completed" and out.get("a", {}).get("invoked"), f"agent node invoked ({out.get('a')})")

    # 5) agent node missing -> retry exhausted -> run failed
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "nope-xyz"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    wid = mkwf(c, defn, "agent-bad")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    rid = r.json()["id"]
    chk(r.json()["status"] == "failed", f"missing agent -> run failed ({r.json().get('status')})")
    nodes = c.get(f"/api/workflow-runs/{rid}/nodes", headers=H).json()["nodes"]
    an = next((n for n in nodes if n["node_id"] == "a"), None)
    chk(an and an["status"] == "failed" and an["attempts"] == 4, f"retry exhausted 4 attempts ({an})")

    # 6) cancel a waiting run
    wid = mkwf(c, {"nodes": [{"id": "t", "type": "trigger"}, {"id": "h", "type": "hitl"}], "edges": [{"source": "t", "target": "h"}]}, "cancelme")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    rid = r.json()["id"]
    r = c.post(f"/api/workflow-runs/{rid}/cancel", headers=H)
    chk(r.status_code == 200 and r.json()["status"] == "cancelled", "cancel waiting run")

    # 7) unauth
    chk(c.get("/api/workflows").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
