"""F-WF Dify DSL Import 어댑터 모드 A (impl/28, PRD §7.2.2·§7.2.6). fresh sqlite, FastAPI TestClient.

회귀는 test/impl/2·23·24 로 별도 확인(본 파일은 신규 Dify Import 기능 전용).
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
from app.db import execute_write, _PH  # noqa: E402
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

DSL_FULL = """
app:
  name: "Support Triage"
  description: "Dify sample flow"
version: "0.1.0"
workflow:
  graph:
    nodes:
      - id: "n_start"
        data: {type: start, title: Start}
      - id: "n_llm"
        data:
          type: llm
          title: Classify
          prompt_template:
            - {role: system, text: "You are a classifier."}
            - {role: user, text: "Classify: {{query}}"}
      - id: "n_if"
        data:
          type: if-else
          title: Branch
          conditions:
            - {variable_selector: [n_llm, text], comparison_operator: contains, value: "urgent"}
      - id: "n_kr"
        data: {type: knowledge-retrieval, title: Search KB}
      - id: "n_http"
        data: {type: http-request, title: Notify Slack, url: "https://hooks.example.com/x", method: post}
      - id: "n_tool"
        data: {type: tool, title: Call Plugin}
      - id: "n_answer"
        data: {type: answer, title: Reply, answer: "Done"}
      - id: "n_code"
        data: {type: code, title: Custom Script}
      - id: "n_mystery"
        data: {type: some-future-type, title: Unknown}
    edges:
      - {source: n_start, target: n_llm}
      - {source: n_llm, target: n_if}
      - {source: n_if, target: n_kr, sourceHandle: "true"}
      - {source: n_if, target: n_answer, sourceHandle: "false"}
      - {source: n_kr, target: n_http}
      - {source: n_http, target: n_tool}
      - {source: n_tool, target: n_code}
      - {source: n_code, target: n_mystery}
      - {source: n_mystery, target: n_ghost}
"""

with TestClient(m.app) as c:
    # 1) RBAC — user 권한 거부
    r = c.post("/api/workflows/import/dify-dsl", headers=UH, json={"dsl": DSL_FULL})
    chk(r.status_code == 403, f"user import -> 403 ({r.status_code})")

    # 2) 잘못된 YAML
    r = c.post("/api/workflows/import/dify-dsl", headers=H, json={"dsl": "nodes: [unclosed"})
    chk(r.status_code == 422, f"invalid YAML -> 422 ({r.status_code})")

    # 3) 전종류 매핑
    r = c.post("/api/workflows/import/dify-dsl", headers=H, json={"dsl": DSL_FULL})
    chk(r.status_code == 201, f"full DSL import -> 201 ({r.status_code}, {r.text[:300]})")
    wf = r.json()
    chk(wf["name"] == "Support Triage", f"name mapped ({wf.get('name')})")
    chk(wf["enabled"] is False, f"imported workflow disabled by default ({wf.get('enabled')})")
    chk(wf.get("dify_dsl_version") == "0.1.0", f"dify_dsl_version stored ({wf.get('dify_dsl_version')})")
    chk(bool(wf.get("dify_dsl_source")), "dify_dsl_source stored (original YAML)")

    nodes = {n["id"]: n for n in wf["definition_json"]["nodes"]}
    edges = wf["definition_json"]["edges"]

    chk(nodes["n_start"]["type"] == "trigger", f"start->trigger ({nodes['n_start']['type']})")
    chk(nodes["n_llm"]["type"] == "llm", f"llm->llm ({nodes['n_llm']['type']})")
    chk(nodes["n_llm"]["config"]["system"] == "You are a classifier.", f"llm system extracted ({nodes['n_llm']['config']})")
    chk("Classify" in nodes["n_llm"]["config"]["prompt"], f"llm prompt extracted ({nodes['n_llm']['config']['prompt']})")
    chk(nodes["n_if"]["type"] == "condition", f"if-else->condition ({nodes['n_if']['type']})")
    chk(nodes["n_if"]["config"]["op"] == "contains", f"comparison_operator mapped ({nodes['n_if']['config']})")
    chk(nodes["n_if"]["config"]["right"] == "urgent", f"condition value mapped ({nodes['n_if']['config']})")
    chk(nodes["n_kr"]["type"] == "agent" and nodes["n_kr"]["config"]["agent_key"] == "rag", f"knowledge-retrieval->agent(rag) ({nodes['n_kr']})")
    chk(nodes["n_http"]["type"] == "http" and nodes["n_http"]["config"]["method"] == "POST", f"http-request->http ({nodes['n_http']})")
    chk(nodes["n_http"]["config"]["url"] == "https://hooks.example.com/x", f"http url preserved ({nodes['n_http']['config']})")
    chk(nodes["n_tool"]["type"] == "agent" and nodes["n_tool"]["config"]["agent_key"] == "", f"tool->agent(blank) ({nodes['n_tool']})")
    chk(nodes["n_answer"]["type"] == "notify" and nodes["n_answer"]["config"]["message"] == "Done", f"answer->notify ({nodes['n_answer']})")
    chk(nodes["n_code"]["type"] == "transform", f"code(unsupported)->transform ({nodes['n_code']['type']})")
    chk(nodes["n_mystery"]["type"] == "transform", f"unrecognized type->transform ({nodes['n_mystery']['type']})")

    chk(len(edges) == 8, f"missing-node edge skipped, 8 edges kept ({len(edges)})")
    e_if_kr = next((e for e in edges if e["source"] == "n_if" and e["target"] == "n_kr"), None)
    e_if_ans = next((e for e in edges if e["source"] == "n_if" and e["target"] == "n_answer"), None)
    chk(e_if_kr and e_if_kr.get("when") == "true", f"true branch when preserved ({e_if_kr})")
    chk(e_if_ans and e_if_ans.get("when") == "false", f"false branch when preserved ({e_if_ans})")

    warnings = wf["warnings"]
    chk(any("n_code" in w for w in warnings), f"code node warned ({warnings})")
    chk(any("n_tool" in w for w in warnings), f"tool node warned ({warnings})")
    chk(any("n_kr" in w for w in warnings), f"knowledge-retrieval node warned ({warnings})")
    chk(any("n_mystery" in w for w in warnings) and any("unrecognized" in w for w in warnings), f"unrecognized type warned ({warnings})")
    chk(any("n_ghost" in w or "skipped" in w for w in warnings), f"dangling edge warned ({warnings})")

    # 4) 관용적 파싱 — 빈 DSL 도 크래시 없이 201
    r = c.post("/api/workflows/import/dify-dsl", headers=H, json={"dsl": "app: {name: empty}\nversion: '1'\n"})
    chk(r.status_code == 201, f"empty-graph DSL -> 201 no crash ({r.status_code})")
    chk(len(r.json()["warnings"]) > 0, f"empty-graph DSL warns ({r.json()['warnings']})")

    # 5) 실행 안전성(보너스) — 활성화 후 실행해도 크래시(500) 없음
    import asyncio
    wid = wf["id"]
    asyncio.run(execute_write(f"UPDATE workflows SET enabled = 1 WHERE id = {_PH}", (wid,)))
    r = c.post(f"/api/workflows/{wid}/run", headers=H, json={"input": {"query": "urgent issue"}})
    chk(r.status_code == 201, f"imported workflow runs without crash ({r.status_code})")
    chk(r.json()["status"] in ("completed", "failed"), f"run reaches terminal state, no 500 ({r.json().get('status')})")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
