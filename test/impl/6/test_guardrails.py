"""F-GRD functional test — fresh sqlite, TestClient. global PII detect, agent toggle, decision log, catalog scope."""
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

# 13종 각각 최소 1개 실제 탐지 확인 (PRD §8.3 P2 verify 요건)
SAMPLES = {
    "pii.national_id_kr": "900101-1234567",
    "pii.ssn_us": "123-45-6789",
    "pii.my_number_jp": "1234 5678 9012",
    "pii.passport": "M12345678",
    "pii.email": "user@example.com",
    "pii.phone_kr": "010-1234-5678",
    "pii.phone_us": "(212) 555-0134",
    "financial.card_number": "4111 1111 1111 1111",  # Luhn-valid test card
    "financial.iban": "GB29NWBK60161331926819",
    "secret.api_key": "sk-abcdefghijklmnopqrstuvwx",
    "pii.driver_license_kr": "11-123456-01",
    "pii.business_reg_no_kr": "123-45-67890",
    "pii.ipv4": "192.168.1.100",
}

with TestClient(m.app) as c:
    r = c.get("/api/agent-config/", headers=H)
    keys = [a["agent_key"] for a in (r.json() if isinstance(r.json(), list) else r.json().get("agents", []))]
    chk("guardrails" in keys, f"guardrails agent seeded ({keys})")

    # domain catalog
    r = c.get("/api/guardrails/domains", headers=H)
    doms = {d["domain_key"]: d for d in r.json()["domains"]}
    chk(doms.get("global", {}).get("status") == "functional", f"global functional ({doms.get('global')})")
    chk(doms.get("manufacturing-food", {}).get("status") == "catalog_only", "manufacturing-food catalog_only")

    # 1) no PII -> allow
    r = c.post("/api/guardrails/test", headers=H, json={"text": "hello, nice weather today"})
    chk(r.status_code == 200 and r.json()["decision"] == "allow", f"clean text -> allow ({r.json()})")
    chk(r.json()["riskScore"] == 0.0, "riskScore 0 on allow")

    # 2) each of 13 detectors fires
    all_ok = True
    for rule_id, sample in SAMPLES.items():
        rr = c.post("/api/guardrails/test", headers=H, json={"text": f"context: {sample} end"})
        matched = rr.json().get("matchedRules", [])
        ok = rr.status_code == 200 and rule_id in matched
        if not ok:
            all_ok = False
            print(f"  -> {rule_id} sample={sample!r} matched={matched}")
    chk(all_ok, "all 13 global detectors fire on their sample")

    # 3) decision -> redact + redactedText masked
    r = c.post("/api/guardrails/test", headers=H, json={"text": "email me at secret@corp.com"})
    chk(r.json()["decision"] == "redact", f"PII -> redact ({r.json()['decision']})")
    chk("secret@corp.com" not in r.json()["redactedText"], f"redactedText masks PII ({r.json()['redactedText']})")

    # 4) catalog_only domain -> 409
    r = c.post("/api/guardrails/test", headers=H, json={"text": "x", "domain": "manufacturing-food"})
    chk(r.status_code == 409, f"catalog_only domain test -> 409 ({r.status_code})")

    # 5) unknown domain -> 404
    r = c.post("/api/guardrails/test", headers=H, json={"text": "x", "domain": "nope"})
    chk(r.status_code == 404, "unknown domain -> 404")

    # 6) agent toggle — user forbidden, supervisor allowed
    r = c.put("/api/guardrails/agents/chat/config", headers=UH, json={"domain_key": "global", "enabled": True})
    chk(r.status_code == 403, "user toggle -> 403")
    r = c.put("/api/guardrails/agents/chat/config", headers=H, json={"domain_key": "global", "enabled": True})
    chk(r.status_code == 200 and r.json()["enabled"] is True, f"supervisor toggle on -> 200 ({r.json()})")
    r = c.get("/api/guardrails/agents/chat/config", headers=H)
    chk(r.json()["domains"][0]["enabled"] in (1, True), f"config reflects enabled ({r.json()})")

    # 6b) unknown domain toggle -> 404
    r = c.put("/api/guardrails/agents/chat/config", headers=H, json={"domain_key": "bogus", "enabled": True})
    chk(r.status_code == 404, "toggle unknown domain -> 404")

    # 7) agent A (on) vs agent B (off) — same guardrails/test call is domain-scoped regardless,
    #    but decision_log records differ per agent_key when passed (요구사항 3: 토글 정합성)
    c.post("/api/guardrails/test", headers=H, json={"text": "card 4111111111111111", "domain": "global", "agent_key": "chat"})
    r = c.get("/api/guardrails/decisions?agent_key=chat", headers=H)
    chk(len(r.json()["decisions"]) == 1, f"decision log recorded for agent_key=chat ({r.json()})")
    decision_id = r.json()["decisions"][0]["decision_id"]

    # explain_decision
    r = c.get(f"/api/guardrails/decisions/{decision_id}", headers=H)
    chk(r.status_code == 200 and r.json()["decision_id"] == decision_id, "explain_decision returns record")

    # missing decision
    r = c.get("/api/guardrails/decisions/nope-xyz", headers=H)
    chk(r.status_code == 404, "explain missing decision -> 404")

    # 8) unauth
    chk(c.get("/api/guardrails/domains").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
