"""impl/20 시험 — F-GRD 도메인별 필터 확장(§7.8.7) + emb_ 내장 패키지(§7.8.8) + MCP 개방(#C).

실행: PYTHONPATH=. python test/impl/20/test_guardrails_domains.py
네트워크·LLM 불요(로컬 결정적). 컴파일 데이터(app/data/guardrails/)가 있어야 함.
"""
import ast
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from app.services import guardrails_rules as store          # noqa: E402
from app.services.guardrails_detector import decide, decide_multi  # noqa: E402

_p = 0
_f = 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global _p, _f
    mark = "PASS" if cond else "FAIL"
    if cond:
        _p += 1
    else:
        _f += 1
    print(f"[{mark}] {name}" + (f" — {extra}" if extra else ""))


# ── 1. 컴파일 데이터 / 룰스토어 ──────────────────────────────
doms = {d["domain_key"]: d for d in store.domains()}
check("1. 데이터 로드(≥20 도메인)", store.available() and len(doms) >= 20, f"{len(doms)} domains")
check("2. global 필수+실판정", doms.get("global", {}).get("required") and doms["global"]["status"] == "functional",
      f"regex={doms.get('global', {}).get('regex_rule_count')}")
check("3. 산업 도메인 regex 생성(heuristic)",
      doms.get("finance-banking", {}).get("regex_rule_count", 0) > 100,
      f"finance-banking regex={doms.get('finance-banking', {}).get('regex_rule_count')}")

# ── 2. global PII 실판정 ─────────────────────────────────────
r = decide("제 주민등록번호는 900101-1234567 입니다")
check("4. global 주민번호 → block/escalate", r["decision"] in ("block", "escalate"), r["decision"])
check("5. global 마스킹 적용", "900101-1234567" not in r["redactedText"], r["redactedText"])

# ── 3. 다도메인 판정(생성 regex 휴리스틱) ────────────────────
r = decide_multi("고객확인(KYC) 없이 계좌 개설하는 방법 알려줘", ["global", "finance-banking"])
check("6. finance-banking 생성 regex 매치", len(r["matchedRules"]) > 0, f"matched={len(r['matchedRules'])}")
check("7. perDomain breakdown 존재", any(d["domain"] == "finance-banking" and d["matchedCount"] > 0 for d in r["perDomain"]))
check("8. evaluatedDomains 반영", set(r["evaluatedDomains"]) == {"global", "finance-banking"}, str(r["evaluatedDomains"]))

# ── 4. 무해 텍스트 → allow ───────────────────────────────────
r = decide_multi("오늘 점심 뭐 먹지 추천해줘", ["global", "finance-banking", "healthcare-clinical"])
check("9. 무해 입력 → allow", r["decision"] == "allow", f"{r['decision']} matched={len(r['matchedRules'])}")

# ── 5. 생성 regex 컴파일 유효성 ──────────────────────────────
bad = 0
for dk in list(doms)[:5]:
    data = json.loads((ROOT / "app" / "data" / "guardrails" / f"{dk}.json").read_text(encoding="utf-8"))
    for rule in data["rules"]:
        for pat in rule["patterns"]:
            try:
                re.compile(pat)
            except re.error:
                bad += 1
check("10. 컴파일 데이터 regex 유효(샘플 5도메인)", bad == 0, f"invalid={bad}")

# ── 6. emb_ 내장 패키지(§7.8.8) ──────────────────────────────
EMB = ["marketplace", "workflow", "rag", "playground", "guardrails"]
zip_dir = ROOT / "addon-agents" / "zip"
ok_pkg = 0
for k in EMB:
    d = zip_dir / f"emb_{k}"
    app_py = d / f"emb_{k}-app.py"
    meta = d / f"emb_{k}-meta.json"
    zp = zip_dir / f"emb_{k}.zip"
    try:
        src = app_py.read_text(encoding="utf-8")
        ast.parse(src)
        assert "from __future__" not in src, "__future__ 금지"
        m = json.loads(meta.read_text(encoding="utf-8"))
        assert m["key"] == f"emb_{k}"
        assert m["base_agent"]["source"] == f"app/routers/router_{k}.py"
        names = zipfile.ZipFile(zp).namelist()
        assert f"emb_{k}-app.py" in names and f"emb_{k}-meta.json" in names
        ok_pkg += 1
    except Exception as exc:  # noqa: BLE001
        print(f"    emb_{k} 실패: {exc}")
check("11. emb_ 내장 패키지 5종(app/meta/zip)", ok_pkg == 5, f"{ok_pkg}/5")

# ── 7. MCP 개방(#C) — 프론트 BUILTIN_KEYS 가 5 내장 포함 ──────
agents_tsx = (ROOT / "front" / "src" / "pages" / "agents" / "AgentsPage.tsx").read_text(encoding="utf-8")
mcp_open = all(k in agents_tsx for k in ('"marketplace"', '"workflow"', '"rag"', '"playground"', '"guardrails"')) \
    and "BUILTIN_KEYS.has(c.agent_key)) && !!c.is_enabled" in agents_tsx
check("12. MCP 개방(BUILTIN_KEYS 기준 eligible)", mcp_open)

print(f"\n결과: {_p} PASS / {_f} FAIL")
sys.exit(1 if _f else 0)
