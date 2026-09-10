"""impl/56 — E12 Playground 비용 추적 + Eval 실행 시험. fresh sqlite, 실 TestClient.

실행: .venv/bin/python test/impl/56/test_playground_cost_eval.py
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
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"  # 강제 degrade

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

UH = {"Authorization": f"Bearer {create_access_token({'sub': 'u1', 'role': 'user', 'username': 'u1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    # 1) run 생성(degraded)
    r = c.post("/api/playground/run", headers=UH, json={"prompt": "PORT-SCAN-42 결과 요약"})
    chk(r.status_code == 201, f"run 201 ({r.status_code})")
    run_id = r.json()["id"]
    chk(r.json()["provider"] == "degraded", "degraded provider")

    # 2) 비용 집계 — degraded=무료
    r = c.get("/api/playground/cost", headers=UH)
    chk(r.status_code == 200, f"cost 200 ({r.status_code})")
    body = r.json()
    chk("totals" in body and body["totals"]["runs"] >= 1, f"totals runs>=1 ({body.get('totals')})")
    chk(body["totals"]["cost_usd"] == 0.0, f"degraded 무료 ({body['totals']['cost_usd']})")
    chk(body["currency"] == "USD", "currency USD")

    # 3) eval — run_id + contains
    r = c.post("/api/playground/eval", headers=UH,
               json={"run_id": run_id, "assertions": [{"type": "contains", "value": "PORT-SCAN-42"},
                                                       {"type": "min_length", "value": "1"}]})
    chk(r.status_code == 200, f"eval run_id 200 ({r.status_code} {r.text[:120]})")
    chk(r.json()["score"]["all_passed"] is True, f"all_passed (degrade echoes prompt) ({r.json()['score']})")

    # 4) eval — output 직접 + regex + not_contains
    r = c.post("/api/playground/eval", headers=UH,
               json={"output": "CVE-2021-44228 detected", "assertions": [
                   {"type": "regex", "value": "CVE-\\d{4}-\\d+"},
                   {"type": "not_contains", "value": "secret"},
                   {"type": "contains", "value": "MISSING"}]})
    chk(r.status_code == 200 and r.json()["score"]["passed"] == 2 and r.json()["score"]["total"] == 3,
        f"eval output mixed 2/3 ({r.json().get('score')})")

    # 5) eval 검증 오류
    chk(c.post("/api/playground/eval", headers=UH, json={"assertions": []}).status_code == 422, "empty assertions 422")
    chk(c.post("/api/playground/eval", headers=UH, json={"assertions": [{"type": "contains", "value": "x"}]}).status_code == 422,
        "no run_id/output 422")
    chk(c.post("/api/playground/eval", headers=UH,
               json={"run_id": 999999, "assertions": [{"type": "contains", "value": "x"}]}).status_code == 404,
        "bad run_id 404")
    chk(c.post("/api/playground/eval", headers=UH,
               json={"output": "x", "assertions": [{"type": "bogus", "value": "x"}]}).status_code == 422,
        "bad assertion type 422")

print(f"\n=== RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} failing) ===")
if fails:
    print("FAILED:", fails)
sys.exit(1 if fails else 0)
