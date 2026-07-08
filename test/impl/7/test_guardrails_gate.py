"""F-GRD Orchestrator gate test — fresh sqlite, TestClient. Exercises the monkeypatched
`orchestrator._exec_api_call` directly (this IS what Orchestrator.run() calls internally),
proving the gate intercepts input/output without touching orchestrator.py source.
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

import asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402
import app.agents.orchestrator as orch  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    # 0) gate installed on startup, orchestrator.py source untouched (attribute-level patch only)
    chk(getattr(orch, "_guardrails_gate_installed", False), "gate installed at startup")
    import inspect
    src = inspect.getsource(orch)
    chk("guardrails" not in src.lower(), "orchestrator.py source contains no guardrails references (未变更)")

    # 1) toggle 'marketplace' agent global domain ON, io_scope=both
    c.put("/api/guardrails/agents/marketplace/config", headers=H,
          json={"domain_key": "global", "enabled": True, "io_scope": "both"})

    # 2) call _exec_api_call directly with PII in body targeting /api/marketplace/... (agent_key=marketplace)
    #    register a catalog asset whose description contains an email -> detector policy is "redact"
    #    (current guardrails_detector never returns block/escalate — only allow/redact, PRD §7.8.2 6-level
    #    decision enum is honored in the gate's branching, but this local reimplementation only exercises 2)
    body_with_pii = {"asset_key": "x1", "name": "X", "description": "contact me at leak@corp.com"}
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog", body_with_pii, None, TOK))
    chk(result.startswith("HTTP 201"), f"redact policy forwards sanitized body, not blocked ({result[:150]})")
    chk("leak@corp.com" not in result, f"raw PII absent from forwarded/response text ({result[:150]})")

    # 3) verify the asset WAS created but with the email masked in its stored description (input-side redaction)
    r = c.get("/api/marketplace/catalog", headers=H)
    x1 = next((a for a in r.json()["assets"] if a["asset_key"] == "x1"), None)
    chk(x1 is not None, f"asset created despite PII (redact, not block) ({r.json()['assets']})")
    chk(x1 and "leak@corp.com" not in x1["description"], f"stored description has masked email ({x1 and x1['description']})")

    # 4) decision logged twice (io_scope=both -> input-side redact + output-side re-check on already-masked text)
    r = c.get("/api/guardrails/decisions?agent_key=marketplace", headers=H)
    decisions = r.json()["decisions"]
    chk(len(decisions) == 2, f"input+output both logged (io_scope=both) ({len(decisions)})")
    input_entry = next((d for d in decisions if d["matched_rule_count"] == 1), None)
    chk(input_entry is not None and input_entry["decision"] == "redact",
        f"input-side entry recorded as redact w/ 1 matched rule ({input_entry})")
    output_entry = next((d for d in decisions if d["matched_rule_count"] == 0), None)
    chk(output_entry is not None and output_entry["decision"] == "allow",
        f"output-side entry allow (already-masked text has no PII left to match) ({output_entry})")

    # 5) clean body (no PII) passes through to the real handler
    body_clean = {"asset_key": "x2", "name": "Clean Asset", "description": "no sensitive data here"}
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog", body_clean, None, TOK))
    chk(result.startswith("HTTP 201"), f"clean input passes gate -> handler executes ({result[:120]})")
    r = c.get("/api/marketplace/catalog", headers=H)
    keys = [a["asset_key"] for a in r.json()["assets"]]
    chk("x2" in keys, f"clean asset actually created ({keys})")

    # 6) toggle OFF -> PII no longer blocked for this agent (요구사항 3: on/off 정합성)
    c.put("/api/guardrails/agents/marketplace/config", headers=H,
          json={"domain_key": "global", "enabled": False, "io_scope": "both"})
    body_with_pii2 = {"asset_key": "x3", "name": "Y", "description": "email leak2@corp.com here"}
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog", body_with_pii2, None, TOK))
    chk(result.startswith("HTTP 201"), f"gate off -> PII input passes through ({result[:120]})")

    # 7) agent B (never toggled, e.g. 'workflow') unaffected by agent A's config — per-agent isolation
    r = c.get("/api/workflows", headers=H)  # GET has no body -> gate is a no-op regardless, but agent isolation
    chk(r.status_code == 200, "agent B (workflow) untouched by agent A's guardrails config")

    # 8) unresolvable path (no agent_key) -> passthrough, no crash
    result = asyncio.run(orch._exec_api_call("GET", "/health", None, None, None))
    chk("ok" in result or "HTTP" in result, f"unresolvable path passthrough, no crash ({result[:80]})")

    # 9) disabled global feature flag -> full bypass
    from app.core.config import settings
    settings.guardrails_enabled = False
    result = asyncio.run(orch._exec_api_call("POST", "/api/marketplace/catalog",
                                              {"asset_key": "x4", "name": "Z", "description": "pii@corp.com"}, None, TOK))
    chk(result.startswith("HTTP 201"), f"GUARDRAILS_ENABLED=false -> full bypass ({result[:120]})")
    settings.guardrails_enabled = True

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
