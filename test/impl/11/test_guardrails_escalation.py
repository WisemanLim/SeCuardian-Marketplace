"""F-GRD block/escalate 승격 + 게이트 실차단 test — fresh sqlite, TestClient.
decide() 승격 정책(저위험=redact / 고위험1=block / 고위험2+=escalate) + Orchestrator 게이트가
block/escalate 시 원 호출을 실제로 차단(HTTP 403 [BLOCKED])하는지 확인.
"""
import asyncio
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
import app.agents.orchestrator as orch  # noqa: E402
from app.services.guardrails_detector import decide  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# ── unit: decide() 승격 정책 ──
chk(decide("hello")["decision"] == "allow", "clean -> allow")
chk(decide("email me at a@b.com")["decision"] == "redact", "email(저위험) -> redact")
chk(decide("call 010-1234-5678")["decision"] == "redact", "phone(저위험) -> redact")
r = decide("key sk-abcdefghijklmnopqrstuvwx")
chk(r["decision"] == "block", f"api key(고위험1) -> block ({r['decision']})")
r = decide("iban GB29NWBK60161331926819")
chk(r["decision"] == "block", f"IBAN(고위험1, 중복없음) -> block ({r['decision']})")
# card(16자리+공백)는 JP 마이넘버(12자리) 패턴과도 겹쳐 고위험 2종 → escalate 될 수 있음(정상)
r = decide("card 4111 1111 1111 1111")
chk(r["decision"] in ("block", "escalate"), f"card -> block|escalate ({r['decision']})")
r = decide("rrn 900101-1234567 and card 4111111111111111")
chk(r["decision"] == "escalate" and r["riskScore"] == 1.0, f"주민+카드(고위험2) -> escalate ({r['decision']}, {r['riskScore']})")
r = decide("rrn 900101-1234567 with email x@y.com")
chk(r["decision"] == "block", f"고위험1+저위험1 -> block ({r['decision']})")

with TestClient(m.app) as c:
    # /test 엔드포인트가 승격 결정 반영
    r = c.post("/api/guardrails/test", headers=H, json={"text": "key sk-abcdefghijklmnopqrstuvwx", "domain": "global"})
    chk(r.json()["decision"] == "block", f"/test api key -> block ({r.json()['decision']})")

    # ── 게이트 실차단: 고위험 입력 → 원 호출 차단(HTTP 403 [BLOCKED]) ──
    c.put("/api/guardrails/agents/marketplace/config", headers=H,
          json={"domain_key": "global", "enabled": True, "io_scope": "both"})
    # marketplace 자산 등록 바디에 API 키(고위험) 포함 → 게이트가 차단, 자산 미생성
    body = {"asset_key": "leaky", "name": "X", "description": "token sk-abcdefghijklmnopqrstuvwx"}
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog", body, None, TOK))
    chk(result.startswith("HTTP 403"), f"block 입력 -> 게이트 403 차단 ({result[:120]})")
    chk("[BLOCKED]" in result, "차단 응답에 [BLOCKED] 마커")
    r = c.get("/api/marketplace/catalog", headers=H)
    keys = [a["asset_key"] for a in r.json()["assets"]]
    chk("leaky" not in keys, f"차단된 호출은 핸들러 미도달 → 자산 미생성 ({keys})")

    # decision_log 에 block 기록
    r = c.get("/api/guardrails/decisions?agent_key=marketplace", headers=H)
    decs = r.json()["decisions"]
    chk(any(d["decision"] == "block" for d in decs), f"decision_log 에 block 기록 ({[d['decision'] for d in decs]})")

    # 저위험(email)은 여전히 통과+마스킹(redact) — 승격이 기존 동작 안 깸
    body2 = {"asset_key": "okmasked", "name": "Y", "description": "email a@b.com"}
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog", body2, None, TOK))
    chk(result.startswith("HTTP 201"), f"저위험 email -> redact 후 통과 ({result[:80]})")
    r = c.get("/api/marketplace/catalog", headers=H)
    ok = next((a for a in r.json()["assets"] if a["asset_key"] == "okmasked"), None)
    chk(ok is not None and "a@b.com" not in ok["description"], f"email 마스킹 저장 ({ok and ok['description']})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
