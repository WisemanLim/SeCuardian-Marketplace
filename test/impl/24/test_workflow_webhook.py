"""F-WF webhook 수신 트리거 (impl/26, PRD §7.2.4). fresh sqlite, FastAPI TestClient.

회귀는 test/impl/2·23 로 별도 확인(본 파일은 신규 webhook 기능 전용).
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
from app.db import execute_write, _PH  # noqa: E402
import app.main as m  # noqa: E402

# sup1 = 실제 tbl_users 행 보유(창조자 역할 조회 성공 케이스), phantom-sup = 토큰만 존재(조회 실패 케이스)
TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}
PHANTOM_TOK = create_access_token({"sub": "phantom-sup", "role": "supervisor", "username": "phantom-sup"})
PH_H = {"Authorization": f"Bearer {PHANTOM_TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    # tbl_users 실 행 생성 — 이후 webhook 트리거의 actor 토큰 발급 대상
    r = c.post("/api/users/", headers=H, json={
        "user_id": "sup1", "username": "sup1", "password": "testpass123456", "role": "supervisor",
    })
    chk(r.status_code == 201, f"seed real user sup1 ({r.status_code}, {r.text[:200]})")

    # 1) webhook 워크플로우 생성 — 시크릿 1회 노출
    defn = {"nodes": [
        {"id": "t", "type": "trigger"},
        {"id": "a", "type": "agent", "config": {"agent_key": "marketplace", "method": "GET", "path": "/api/marketplace/catalog"}},
    ], "edges": [{"source": "t", "target": "a"}]}
    r = c.post("/api/workflows", headers=H, json={"name": "wh1", "trigger_type": "webhook", "definition_json": defn})
    chk(r.status_code == 201, f"create webhook workflow ({r.status_code})")
    wf = r.json()
    wid = wf["id"]
    secret = wf.get("webhook_secret")
    chk(bool(secret), f"webhook_secret present in create response ({secret is not None})")
    chk("webhook_secret_hash" not in wf.get("trigger_config_json", {}), "hash not leaked in create response")

    # 재조회에는 시크릿/해시 전혀 없음
    r = c.get(f"/api/workflows/{wid}", headers=H)
    chk("webhook_secret" not in r.json() and "webhook_secret_hash" not in r.json().get("trigger_config_json", {}), f"no secret/hash on refetch ({r.json().get('trigger_config_json')})")

    # 2) 인증 실패 케이스
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", json={})
    chk(r.status_code == 401, f"missing secret -> 401 ({r.status_code})")
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": "wrong-secret"}, json={})
    chk(r.status_code == 401, f"wrong secret -> 401 ({r.status_code})")

    # 3) JWT 없이, 올바른 시크릿만으로 트리거 성공 + actor(sup1) 권한 상속으로 실 API 호출 성공
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret}, json={})
    chk(r.status_code == 201, f"correct secret, no JWT -> 201 ({r.status_code})")
    run = r.json()
    chk(run["status"] == "completed", f"webhook run completed ({run.get('status')})")
    out = json.loads(run["output_json"])
    chk(out.get("a", {}).get("status") == 200, f"agent node real call via creator role ({out.get('a')})")
    r2 = c.get(f"/api/workflow-runs/{run['id']}", headers=H)
    chk(r2.json().get("trigger_source") == "webhook", f"trigger_source=webhook recorded ({r2.json().get('trigger_source')})")

    # 4) manual 워크플로우 대상 webhook 트리거 -> 404
    r = c.post("/api/workflows", headers=H, json={"name": "manual1", "definition_json": {"nodes": [{"id": "t", "type": "trigger"}], "edges": []}})
    mid = r.json()["id"]
    r = c.post(f"/api/workflows/{mid}/trigger/webhook", headers={"X-Webhook-Secret": "whatever"}, json={})
    chk(r.status_code == 404, f"manual workflow webhook trigger -> 404 ({r.status_code})")

    # 5) disabled 워크플로우 -> 409 (PATCH 엔드포인트 없음 — 시험 내부에서 직접 비활성화)
    import asyncio
    asyncio.run(execute_write(f"UPDATE workflows SET enabled = 0 WHERE id = {_PH}", (wid,)))
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret}, json={})
    chk(r.status_code == 409, f"disabled workflow -> 409 ({r.status_code})")
    asyncio.run(execute_write(f"UPDATE workflows SET enabled = 1 WHERE id = {_PH}", (wid,)))

    # 6) 생성자가 tbl_users 에 없는 경우 — actor 토큰 없이 안전하게 노드만 실패(권한 상승 없음)
    r = c.post("/api/workflows", headers=PH_H, json={"name": "wh2", "trigger_type": "webhook", "definition_json": defn})
    wid2 = r.json()["id"]
    secret2 = r.json()["webhook_secret"]
    r = c.post(f"/api/workflows/{wid2}/trigger/webhook", headers={"X-Webhook-Secret": secret2}, json={})
    chk(r.status_code == 201, f"unknown creator run created ({r.status_code})")
    chk(r.json()["status"] == "failed", f"unknown creator -> node call fails safely, run failed ({r.json().get('status')})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
