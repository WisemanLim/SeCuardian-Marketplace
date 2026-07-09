"""F-WF `enabled` 토글 PATCH 엔드포인트 (impl/30, PRD §7.2.7). fresh sqlite, FastAPI TestClient.

회귀는 test/impl/2·23·24·26·27 로 별도 확인.
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
    defn = {"nodes": [{"id": "t", "type": "trigger"}], "edges": []}
    r = c.post("/api/workflows", headers=H, json={"name": "toggle-me", "definition_json": defn})
    wid = r.json()["id"]
    chk(r.json()["enabled"] is True, f"created enabled by default ({r.json()['enabled']})")

    # 1) 404
    r = c.patch("/api/workflows/999999", headers=H, json={"enabled": False})
    chk(r.status_code == 404, f"unknown workflow -> 404 ({r.status_code})")

    # 2) RBAC
    r = c.patch(f"/api/workflows/{wid}", headers=UH, json={"enabled": False})
    chk(r.status_code == 403, f"user toggle -> 403 ({r.status_code})")

    # 3) 정상 토글: disable
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"enabled": False})
    chk(r.status_code == 200 and r.json()["enabled"] is False, f"disable ok ({r.status_code}, {r.json().get('enabled')})")
    chk(r.json()["name"] == "toggle-me" and r.json()["definition_json"] == defn, "other fields unchanged after disable")

    # 4) 비활성 상태에서 run -> 409
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    chk(r.status_code == 409, f"run while disabled -> 409 ({r.status_code})")

    # 5) 재활성화 -> run 성공
    r = c.patch(f"/api/workflows/{wid}", headers=H, json={"enabled": True})
    chk(r.status_code == 200 and r.json()["enabled"] is True, f"re-enable ok ({r.json().get('enabled')})")
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {}})
    chk(r.status_code == 201 and r.json()["status"] == "completed", f"run after re-enable -> completed ({r.json().get('status')})")

    # 6) Dify 가져오기(항상 disabled) + PATCH 활성화 통합 흐름(§7.2.6·§7.2.7)
    dsl = "app:\n  name: dify-toggle\nversion: '1'\nworkflow:\n  graph:\n    nodes:\n      - id: n1\n        data: {type: start}\n    edges: []\n"
    r = c.post("/api/workflows/import/dify-dsl", headers=H, json={"dsl": dsl})
    dwid = r.json()["id"]
    chk(r.json()["enabled"] is False, f"dify import disabled by default ({r.json()['enabled']})")
    r = c.patch(f"/api/workflows/{dwid}", headers=H, json={"enabled": True})
    chk(r.status_code == 200 and r.json()["enabled"] is True, f"dify-imported workflow enabled via PATCH ({r.json().get('enabled')})")
    r = c.post(f"/api/workflows/{dwid}/run", headers=H, json={"input": {}})
    chk(r.status_code == 201 and r.json()["status"] == "completed", f"dify-imported workflow runs after enable ({r.json().get('status')})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
