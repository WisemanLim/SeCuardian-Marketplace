"""F-WF 풀스크린 빌더 — PATCH 부분 편집 확장 (impl/32, PRD §7.2.8). fresh sqlite, FastAPI TestClient.

회귀는 test/impl/2·26·28 재실행으로 별도 확인.
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

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}
UTOK = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {UTOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    defn_v1 = {"nodes": [{"id": "t", "type": "trigger"}], "edges": []}
    r = c.post("/api/workflows", headers=H, json={
        "name": "builder-wf", "description": "orig", "definition_json": defn_v1,
    })
    wid = r.json()["id"]
    v0 = r.json()["version"]
    chk(r.status_code == 201, f"create ok ({r.status_code})")

    # 1) enabled 단독 하위호환 — version 불변
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"enabled": False})
    chk(r.status_code == 200 and r.json()["enabled"] is False, f"enabled-only patch ok ({r.status_code})")
    chk(r.json()["version"] == v0, f"enabled patch keeps version ({r.json()['version']} == {v0})")
    c.patch(f"/api/workflows/{wid}", headers=H, json={"enabled": True})

    # 2) name/description 부분 편집 — 미전달 필드 보존, version 불변
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"name": "builder-wf-2"})
    j = r.json()
    chk(j["name"] == "builder-wf-2" and j["description"] == "orig", "name-only patch preserves description")
    chk(j["definition_json"] == defn_v1 and j["version"] == v0, "name patch keeps definition/version")
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"description": "desc-2"})
    chk(r.json()["description"] == "desc-2" and r.json()["name"] == "builder-wf-2", "description-only patch ok")

    # 3+4) definition 편집(빌더 position 좌표 포함) — 왕복 일치 + version +1
    defn_v2 = {
        "nodes": [
            {"id": "t", "type": "trigger", "position": {"x": 40, "y": 120}},
            {"id": "llm1", "type": "llm", "config": {"prompt": "hi {{t.input.q}}"}, "position": {"x": 300, "y": 120}},
            {"id": "notify1", "type": "notify", "config": {"message": "{{llm1.text}}"}, "position": {"x": 560, "y": 120}},
        ],
        "edges": [{"source": "t", "target": "llm1"}, {"source": "llm1", "target": "notify1"}],
    }
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"definition_json": defn_v2})
    j = r.json()
    chk(r.status_code == 200 and j["definition_json"] == defn_v2, "definition patch round-trips (incl. position)")
    chk(j["version"] == v0 + 1, f"definition patch bumps version ({j['version']} == {v0 + 1})")

    # 5) 결합 PATCH(name+definition) — version +1 추가
    defn_v3 = {**defn_v2, "edges": [{"source": "t", "target": "llm1"},
                                    {"source": "llm1", "target": "notify1", "when": ""}]}
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"name": "builder-wf-3", "definition_json": defn_v3})
    chk(r.json()["name"] == "builder-wf-3" and r.json()["version"] == v0 + 2, "combined patch ok (name + version+1)")

    # 6) 잘못된 definition — 422 + 기존 정의/version 불변
    bad_type = {"nodes": [{"id": "x", "type": "nope"}], "edges": []}
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"definition_json": bad_type})
    chk(r.status_code == 422, f"bad node type -> 422 ({r.status_code})")
    bad_edge = {"nodes": [{"id": "a", "type": "trigger"}], "edges": [{"source": "a", "target": "ghost"}]}
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"definition_json": bad_edge})
    chk(r.status_code == 422, f"edge to unknown node -> 422 ({r.status_code})")
    r = c.get(f"/api/workflows/{wid}", headers=H)
    chk(r.json()["definition_json"] == defn_v3 and r.json()["version"] == v0 + 2,
        "definition/version unchanged after 422s")

    # 7) 빈 바디 -> 422
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={})
    chk(r.status_code == 422, f"empty body -> 422 ({r.status_code})")

    # 8) RBAC/404
    r = c.patch(f"/api/workflows/{wid}", headers=UH, json={"name": "hax"})
    chk(r.status_code == 403, f"user patch -> 403 ({r.status_code})")
    r = c.patch("/api/workflows/999999", headers=H, json={"name": "none"})
    chk(r.status_code == 404, f"unknown id -> 404 ({r.status_code})")

    # 9) 편집 후 run — 새 정의(llm degrade 포함) 기준으로 완료
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {"q": "ping"}})
    chk(r.status_code == 201 and r.json()["status"] == "completed",
        f"run after builder edits -> completed ({r.json().get('status')})")
    r = c.get(f"/api/workflow-runs/{r.json()['id']}/nodes", headers=H)
    kinds = [n["node_type"] for n in r.json()["nodes"]]
    chk(kinds == ["trigger", "llm", "notify"], f"run executed new definition ({kinds})")

print()
if fails:
    print(f"FAILED: {len(fails)}")
    sys.exit(1)
print("ALL PASS")
