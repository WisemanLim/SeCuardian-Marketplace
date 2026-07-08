"""impl/21 시험 — F-GRD 완전판정(LLM classifier) + 생성 regex 과탐 완화 + 실판정/휴리스틱 공존(§7.8.7).

실행: PYTHONPATH=. python test/impl/21/test_guardrails_classifier.py
LLM classifier 는 call_ollama 를 monkeypatch 해 결정적으로 시험(실제 LLM 불요).
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from app.core.config import settings                       # noqa: E402
from app.services import guardrails_rules as store         # noqa: E402
from app.services import llm_fallback                      # noqa: E402
from app.services import guardrails_detector as det        # noqa: E402
from app.services.guardrails_detector import decide_multi, decide_multi_llm  # noqa: E402

_p = _f = 0


def check(name, cond, extra=""):
    global _p, _f
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {extra}" if extra else ""))
    if cond:
        _p += 1
    else:
        _f += 1


store._RULES = None  # 최신 컴파일 데이터 강제 로드

# ── 1. 실판정(regex)+휴리스틱 공존 (§7.8.7 E) ──
fb = json.loads((ROOT / "app/data/guardrails/finance-banking.json").read_text(encoding="utf-8"))
modes = {}
for r in fb["rules"]:
    modes[r["mode"]] = modes.get(r["mode"], 0) + 1
check("1. finance-banking 실판정+휴리스틱 공존", modes.get("regex", 0) >= 1 and modes.get("heuristic", 0) >= 10, str(modes))
check("2. 카탈로그 카운트 = real+heuristic", fb["regex_rule_count"] == fb["real_rule_count"] + fb["heuristic_rule_count"],
      f"{fb['regex_rule_count']}={fb['real_rule_count']}+{fb['heuristic_rule_count']}")
check("3. 규칙에 mode/description/priority", all(k in fb["rules"][0] for k in ("mode", "description", "priority")))

# ── 2. 과탐 완화 — 단일 흔한 키워드 미발화 ──
r = decide_multi("수수료 안내 좀 부탁해요", ["finance-banking"])
check("4. 단일 키워드 과탐 완화(수수료 → allow)", r["decision"] == "allow", f"{r['decision']} n={len(r['matchedRules'])}")
r = decide_multi("오늘 날씨가 참 좋네요", ["finance-banking", "healthcare-clinical"])
check("5. 무해 입력 → allow", r["decision"] == "allow", f"n={len(r['matchedRules'])}")

# ── 3. LLM classifier OFF → regex 결과만 ──
settings.guardrails_classifier_enabled = False
base = asyncio.run(decide_multi_llm("고객확인 KYC 없이 계좌 개설", ["global", "finance-banking"]))
check("6. classifier OFF → source=rules", base["source"] == "rules", base["source"])

# ── 4. LLM classifier ON (monkeypatch) → 패러프레이즈 판정 병합 ──
settings.guardrails_classifier_enabled = True
# finance-banking 의 임의 규칙 id 하나를 LLM 이 위반으로 반환하도록 mock
target = next(c["rule_id"] for c in store.classifier_candidates("finance-banking", limit=5))


async def _fake_ollama(messages, system, **kw):
    return f'답변: ["{target}"]'


llm_fallback.call_ollama = _fake_ollama  # _classify_llm 이 함수 내부에서 import → 패치 반영
r = asyncio.run(decide_multi_llm("자금 관련 우회 문의", ["finance-banking"]))
check("7. classifier ON → source=rules+llm", r["source"] == "rules+llm", r["source"])
check("8. LLM 판정 rule_id 병합", target in r["matchedRules"], f"target={target} matched⊇llm={any(target in pd.get('llmMatched', []) for pd in r['perDomain'])}")

# ── 5. classifier degrade (LLM 비정상 응답 → regex 폴백, 무크래시) ──
async def _bad_ollama(messages, system, **kw):
    return "죄송하지만 JSON 을 반환할 수 없습니다"


llm_fallback.call_ollama = _bad_ollama
r = asyncio.run(decide_multi_llm("수수료 안내 좀 부탁해요", ["finance-banking"]))
check("9. classifier degrade → 무크래시 allow", r["decision"] == "allow", r["decision"])

# ── 6. classifier_candidates 계약 ──
cands = store.classifier_candidates("finance-banking", exclude={target}, limit=10)
check("10. candidates 계약(제외·limit·priority)",
      len(cands) <= 10 and target not in {c["rule_id"] for c in cands}
      and all(cands[i]["priority"] >= cands[i + 1]["priority"] for i in range(len(cands) - 1)))

settings.guardrails_classifier_enabled = False  # 원복
det.__dict__  # noqa: B018 — keep import used

print(f"\n결과: {_p} PASS / {_f} FAIL")
sys.exit(1 if _f else 0)
