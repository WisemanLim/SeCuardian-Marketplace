"""impl/55 — E11 거버넌스(HITL 승인 + OWASP 스코어카드) 시험. fresh sqlite, 실 TestClient.

실행: .venv/bin/python test/impl/55/test_governance.py
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

UTOK = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
STOK = create_access_token({"sub": "s1", "role": "supervisor", "username": "sup"})
UH = {"Authorization": f"Bearer {UTOK}"}
SH = {"Authorization": f"Bearer {STOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    # ── OWASP 스코어카드 ──
    r = c.get("/api/governance/owasp-scorecard", headers=UH)
    chk(r.status_code == 200, f"scorecard 200 ({r.status_code} {r.text[:120]})")
    body = r.json()
    chk(len(body["controls"]) == 10, f"10 controls ({len(body['controls'])})")
    ids = {c2["id"] for c2 in body["controls"]}
    chk(ids == {f"LLM0{i}" for i in range(1, 10)} | {"LLM10"}, f"LLM01..10 ({sorted(ids)})")
    llm08 = next(c2 for c2 in body["controls"] if c2["id"] == "LLM08")
    chk("HITL" in llm08["basis"] and llm08["score"] >= 4, f"LLM08 HITL gate scored ({llm08})")
    chk("average" in body["summary"] and body["summary"]["target"] == 4, "summary avg/target")

    # ── HITL 플로우 ──
    r = c.post("/api/governance/hitl", headers=UH, json={"action": "delete", "resource": "db.users"})
    chk(r.status_code == 201 and r.json()["status"] == "pending", f"create 201 pending ({r.status_code} {r.text[:120]})")
    aid = r.json()["id"]
    chk(r.json()["high_impact"] is True, "delete = high_impact")

    r = c.post("/api/governance/hitl", headers=UH, json={"action": "bogus"})
    chk(r.status_code == 422, f"invalid action 422 ({r.status_code})")

    r = c.get("/api/governance/hitl?status=pending", headers=UH)
    chk(r.status_code == 200 and r.json()["pending_count"] >= 1, f"list pending ({r.json().get('pending_count')})")

    # 권한: 일반 user 는 승인 불가
    r = c.post(f"/api/governance/hitl/{aid}/approve", headers=UH, json={})
    chk(r.status_code == 403, f"user approve 403 ({r.status_code})")

    # supervisor 승인
    r = c.post(f"/api/governance/hitl/{aid}/approve", headers=SH, json={"reason": "checked"})
    chk(r.status_code == 200 and r.json()["updated"]["status"] == "approved", f"supervisor approve ({r.status_code} {r.text[:120]})")
    chk(r.json()["updated"]["decided_by"] == "sup", "decided_by recorded")

    # 재승인 409
    r = c.post(f"/api/governance/hitl/{aid}/approve", headers=SH, json={})
    chk(r.status_code == 409, f"re-approve 409 ({r.status_code})")

    # 없는 id 404
    r = c.post("/api/governance/hitl/999999/reject", headers=SH, json={})
    chk(r.status_code == 404, f"missing id 404 ({r.status_code})")

    # reject 경로
    r = c.post("/api/governance/hitl", headers=UH, json={"action": "external", "resource": "webhook"})
    aid2 = r.json()["id"]
    r = c.post(f"/api/governance/hitl/{aid2}/reject", headers=SH, json={"reason": "policy"})
    chk(r.status_code == 200 and r.json()["updated"]["status"] == "rejected", f"reject ({r.status_code})")

print(f"\n=== RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} failing) ===")
if fails:
    print("FAILED:", fails)
sys.exit(1 if fails else 0)
