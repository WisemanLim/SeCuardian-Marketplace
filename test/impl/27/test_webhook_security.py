"""F-WF webhook 보안 강화 — 로테이션/HMAC/rate limit (impl/29, PRD §7.2.4.1).

fresh sqlite, FastAPI TestClient. 회귀는 test/impl/2·23·24·26 로 별도 확인.
"""
import hashlib
import hmac as hmac_mod
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
os.environ["WORKFLOW_WEBHOOK_RATE_LIMIT_PER_MIN"] = "5"  # 시험은 낮은 한도로 429 재현

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
    # 준비 — webhook 워크플로우 생성
    r = c.post("/api/workflows", headers=H, json={
        "name": "wh-sec", "trigger_type": "webhook",
        "definition_json": {"nodes": [{"id": "t", "type": "trigger"}], "edges": []},
    })
    wid = r.json()["id"]
    secret1 = r.json()["webhook_secret"]
    chk("webhook_secret_enc" not in r.json().get("trigger_config_json", {}), "enc not leaked in create response")

    # 1) HMAC 서명으로 트리거(X-Webhook-Secret 헤더 없이)
    raw = json.dumps({"event": "deploy"}).encode()
    sig = "sha256=" + hmac_mod.new(secret1.encode(), raw, hashlib.sha256).hexdigest()
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Signature": sig}, content=raw)
    chk(r.status_code == 201, f"valid HMAC signature -> 201 ({r.status_code})")
    run = c.get(f"/api/workflow-runs/{r.json()['id']}", headers=H).json()
    chk(json.loads(run["input_json"]) == {"event": "deploy"}, f"raw body preserved as input ({run['input_json']})")

    # 2) 잘못된 서명 -> 401
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Signature": "sha256=deadbeef"}, content=raw)
    chk(r.status_code == 401, f"invalid HMAC signature -> 401 ({r.status_code})")

    # 3) 하위호환 — 기존 X-Webhook-Secret 직접비교 방식도 계속 동작
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret1}, content=b"{}")
    chk(r.status_code == 201, f"legacy X-Webhook-Secret still works -> 201 ({r.status_code})")

    # 4) 로테이션
    r = c.post(f"/api/workflows/{wid}/trigger/webhook/rotate", headers=UH)
    chk(r.status_code == 403, f"user rotate -> 403 ({r.status_code})")
    r = c.post(f"/api/workflows/{wid}/trigger/webhook/rotate", headers=H)
    chk(r.status_code == 201, f"rotate -> 201 ({r.status_code})")
    secret2 = r.json()["webhook_secret"]
    chk(secret2 != secret1, "rotated secret differs from original")

    # 구 시크릿 즉시 무효
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret1}, content=b"{}")
    chk(r.status_code == 401, f"old secret invalidated after rotate -> 401 ({r.status_code})")
    # 신규 시크릿 정상 동작
    r = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret2}, content=b"{}")
    chk(r.status_code == 201, f"new secret works -> 201 ({r.status_code})")

    # manual 워크플로우 rotate -> 409
    r = c.post("/api/workflows", headers=H, json={"name": "manual-x", "definition_json": {"nodes": [{"id": "t", "type": "trigger"}], "edges": []}})
    mid = r.json()["id"]
    r = c.post(f"/api/workflows/{mid}/trigger/webhook/rotate", headers=H)
    chk(r.status_code == 409, f"rotate on manual workflow -> 409 ({r.status_code})")

    # 5) rate limit(한도 5/분, wid 는 이미 3회 성공 호출 소진 — 401/그외 실패시도도 카운트되므로 넉넉히 추가 호출)
    codes = []
    for _ in range(6):
        rr = c.post(f"/api/workflows/{wid}/trigger/webhook", headers={"X-Webhook-Secret": secret2}, content=b"{}")
        codes.append(rr.status_code)
    chk(429 in codes, f"rate limit triggers 429 within extra bursts ({codes})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
