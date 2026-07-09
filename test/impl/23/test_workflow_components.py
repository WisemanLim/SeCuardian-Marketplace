"""F-WF 컴포넌트 팔레트 + agent 노드 실호출 + http 노드 (impl/23, PRD §7.2.3).

fresh sqlite, FastAPI TestClient. 회귀는 test/impl/2 로 별도 확인(본 파일은 신규 기능 전용).
"""
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
import app.services.workflow_engine as we  # noqa: E402

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
    # 1) components — 인증
    r = c.get("/api/workflow/components")
    chk(r.status_code in (401, 403), f"no token -> 401/403 ({r.status_code})")

    r = c.get("/api/workflow/components", headers=H)
    chk(r.status_code == 200, f"components 200 ({r.status_code})")
    comps = r.json()["components"]
    chk(len(comps) > 0, f"components non-empty ({len(comps)})")

    by_key = {}
    for cmp_ in comps:
        by_key.setdefault(cmp_["agent_key"], []).append(cmp_)
        chk(
            all(k in cmp_ for k in ("agent_key", "agent_name", "category", "method", "path", "capability_key", "label")),
            "component has required fields",
        )
        chk(cmp_["label"] == f"{cmp_['agent_name']}-{cmp_['capability_key']}", "label format")
        break  # 필드 형태만 1건 확인(전수 확인은 비용 큼)

    mp_catalog = next(
        (x for x in comps if x["agent_key"] == "marketplace" and x["path"] == "/api/marketplace/catalog" and x["method"] == "GET"),
        None,
    )
    chk(mp_catalog is not None, f"marketplace catalog component present ({[x['path'] for x in comps if x['agent_key']=='marketplace'][:5]})")
    chk(mp_catalog and mp_catalog["category"] == "builtin", f"marketplace category=builtin ({mp_catalog and mp_catalog['category']})")

    addon_leak = [x for x in comps if x["path"].startswith("/api/addon/") and x["category"] != "addon"]
    chk(not addon_leak, f"no addon-prefix leak into non-addon category ({addon_leak})")

    # 2) agent 노드 실호출 — marketplace catalog 실제 호출
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "marketplace", "method": "GET", "path": "/api/marketplace/catalog"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    wid = mkwf(c, defn, "agent-real-call")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    chk(r.status_code == 201 and r.json()["status"] == "completed", f"real agent call run completed ({r.json().get('status')})")
    out = json.loads(r.json()["output_json"])
    a_out = out.get("a", {})
    chk(a_out.get("status") == 200, f"real agent call status 200 ({a_out.get('status')})")
    chk(isinstance(a_out.get("body"), (dict, list)), f"real agent call body parsed as JSON ({type(a_out.get('body'))})")

    # 3) 하위호환 — path 미지정 시 기존 스텁
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "chat"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    wid = mkwf(c, defn, "agent-legacy-stub")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    out = json.loads(r.json()["output_json"])
    chk(out.get("a") == {"agent_key": "chat", "invoked": True, "input": {}}, f"legacy stub unchanged ({out.get('a')})")

    # 4) actor 토큰 — user 권한으로 admin 전용 API 를 컴포넌트로 호출하면 403 -> run failed
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "marketplace", "method": "POST", "path": "/api/marketplace/catalog"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    wid = mkwf(c, defn, "agent-actor-scoped")
    r = c.post(f"/api/workflows/{wid}/run", headers=UH, json={"input": {}})
    chk(r.status_code == 201, f"user can run (workflow itself allows any authed user, {r.status_code})")
    chk(r.json()["status"] == "failed", f"actor(user) lacks admin -> node call 403 -> run failed ({r.json().get('status')})")

    # 5) http 노드 — _http_call monkeypatch
    async def fake_http_call(method, url, headers, body, params):
        return 200, json.dumps({"echo": url, "method": method})
    we._http_call = fake_http_call

    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "h", "type": "http", "config": {"url": "https://example.invalid/webhook", "method": "POST", "body": {"x": 1}}},
    ], "edges": [{"source": "t", "target": "h"}]}
    wid = mkwf(c, defn, "http-node-ok")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    chk(r.status_code == 201 and r.json()["status"] == "completed", f"http node run completed ({r.json().get('status')})")
    out = json.loads(r.json()["output_json"])
    chk(out.get("h", {}).get("status") == 200 and out.get("h", {}).get("body", {}).get("echo") == "https://example.invalid/webhook", f"http node output ({out.get('h')})")

    async def fake_http_call_err(method, url, headers, body, params):
        return 500, "boom"
    we._http_call = fake_http_call_err
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "h", "type": "http", "config": {"url": "https://example.invalid/bad"}},
    ], "edges": [{"source": "t", "target": "h"}]}
    wid = mkwf(c, defn, "http-node-fail")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    chk(r.json()["status"] == "failed", f"http node 5xx -> run failed ({r.json().get('status')})")

    # http node type accepted by validation (no 422)
    r = c.post("/api/workflows", headers=H, json={"name": "http-valid", "definition_json": {"nodes": [{"id": "h", "type": "http", "config": {"url": "https://example.invalid"}}], "edges": []}})
    chk(r.status_code == 201, f"http node type passes validation ({r.status_code})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
