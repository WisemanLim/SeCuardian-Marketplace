#!/usr/bin/env python3
"""Guardrails 규칙 데이터 컴파일러 (F-GRD, PRD §7.8.7).

wise-Guardrails `Guardrails-Service/scripts/*.kr.json`(+`.en.json`) 도메인별 규칙셋을 읽어
SeCMP 가드레일 에이전트가 **내부 데이터로 관리**하는 컴파일 형식으로 변환한다:

  app/data/guardrails/<domain>.json   — 도메인별 규칙(정규식 포함)
  app/data/guardrails/_manifest.json  — 도메인 목록·상태·카운트

핵심(사용자 확정, §7.8.7):
- classifier 전용 산업 도메인 규칙에도 **regex 를 생성**해 내재화(`generated:true`, mode=heuristic).
- **실판정(원본 regex)과 휴리스틱(생성 regex)이 규칙별 mode 로 공존**한다.
- 생성 regex 오탐 완화 — **교차도메인 문서빈도(DF) 필터 + 단일 키워드 게이트**.
- LLM classifier(완전판정)용으로 규칙에 `description`·`priority`·`mode` 를 함께 컴파일.

런타임(app/services/guardrails_rules.py)은 wise-Guardrails 원본에 의존하지 않고 이 컴파일 데이터만 읽는다.

Usage:
    GUARDRAILS_SCRIPTS_DIR=/path/to/Guardrails-Service/scripts \
        uv run python scripts/build_guardrails_data.py   (또는 make guardrails-data)
"""
import glob
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

_SRC_DIR = os.getenv(
    "GUARDRAILS_SCRIPTS_DIR",
    "/Users/wise/Developer/wise-Guardrails/Guardrails-Service/scripts",
)
_OUT_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "guardrails"

# 토큰이 이 도메인 수 이상에 등장하면 저정보(generic) 로 보고 생성 키워드에서 제외
_GENERIC_DF = 6

_DISPLAY: dict[str, tuple[str, str]] = {
    "global": ("Global PII/신용정보", "Global PII / Financial"),
    "finance-banking": ("금융(은행)", "Finance (Banking)"),
    "finance-insurance": ("금융(보험)", "Finance (Insurance)"),
    "finance-securities-misc": ("금융(증권·기타)", "Finance (Securities/Misc)"),
    "healthcare-clinical": ("의료(임상)", "Healthcare (Clinical)"),
    "healthcare-non-residential-welfare": ("의료(비거주복지)", "Healthcare (Non-residential Welfare)"),
    "healthcare-residential-welfare": ("의료(거주복지)", "Healthcare (Residential Welfare)"),
    "manufacturing-apparel": ("제조업(의류)", "Manufacturing (Apparel)"),
    "manufacturing-automotive": ("제조업(자동차)", "Manufacturing (Automotive)"),
    "manufacturing-beverage": ("제조업(음료)", "Manufacturing (Beverage)"),
    "manufacturing-chemical": ("제조업(화학)", "Manufacturing (Chemical)"),
    "manufacturing-electrical": ("제조업(전기)", "Manufacturing (Electrical)"),
    "manufacturing-electronics": ("제조업(전자)", "Manufacturing (Electronics)"),
    "manufacturing-food": ("제조업(식품)", "Manufacturing (Food)"),
    "manufacturing-machinery": ("제조업(기계)", "Manufacturing (Machinery)"),
    "manufacturing-metal-primary": ("제조업(1차금속)", "Manufacturing (Primary Metal)"),
    "manufacturing-other-transport": ("제조업(기타운송장비)", "Manufacturing (Other Transport)"),
    "manufacturing-pharma": ("제조업(제약)", "Manufacturing (Pharma)"),
    "manufacturing-rubber-plastics": ("제조업(고무·플라스틱)", "Manufacturing (Rubber/Plastics)"),
    "manufacturing-textile": ("제조업(섬유)", "Manufacturing (Textile)"),
    "manufacturing-tobacco": ("제조업(담배)", "Manufacturing (Tobacco)"),
    "public-administration": ("공공행정", "Public Administration"),
    "arts-recreation": ("예술·스포츠·여가", "Arts/Recreation"),
}

_JOSA = ("으로", "에서", "에게", "한테", "까지", "부터", "이라", "라고", "이라고",
         "은", "는", "이", "가", "을", "를", "에", "의", "도", "로", "와", "과",
         "만", "야", "요", "다", "고", "며", "든", "나")
_STOP = frozenset({
    "방법", "알려줘", "알려", "있어", "있나", "어떻게", "관련", "대해", "대한", "해줘",
    "주세요", "하는", "해서", "하고", "하려면", "가능", "무엇", "뭐가", "뭐야", "좀",
    "정도", "그거", "이거", "저거", "우리", "너무", "정말", "진짜", "그냥", "혹시",
    "방식", "경우", "관하여", "관하", "통해", "위해", "위한", "때문", "라도", "이나",
    "설명", "안내", "개요", "예시", "내용", "사항", "확인", "처리", "사용", "적용",
})
_TOKEN_RE = re.compile(r"[A-Za-z]{3,}|[가-힣]{2,}")


def _strip_josa(tok: str) -> str:
    if re.fullmatch(r"[가-힣]+", tok):
        for j in _JOSA:
            if len(tok) > len(j) + 1 and tok.endswith(j):
                return tok[: -len(j)]
    return tok


def _tokens(text: str) -> set[str]:
    out = set()
    for raw in _TOKEN_RE.findall(text or ""):
        tok = _strip_josa(raw)
        if len(tok) >= 2 and tok not in _STOP and not tok.isdigit():
            out.add(tok)
    return out


def _keywords(examples: list[str], df: Counter) -> list[str]:
    """규칙의 식별 키워드 추출 — DF 필터 + **동일 예시 내 2개 키워드 공기(AND)**.

    과탐 완화 핵심: 단일 흔한 단어(예 '수수료')만으로는 발화하지 않도록, **한 예시 안에서
    함께 나타나는 식별 토큰 2개**(가장 풍부한 예시에서 DF 낮은순=식별력 높은순)를 AND 로 요구한다.
    → 무해한 '수수료 안내' 는 미발화, '수수료 숨기고 초과인출' 처럼 2개 공기 시에만 발화.
    2개 미만이면 매우 희소·긴 단일 토큰(DF≤1, len≥4)만 예외 허용, 그 외는 regex 미생성(→classifier).
    """
    best: list[str] = []
    for ex in examples:
        toks = [t for t in _tokens(ex) if df[t] < _GENERIC_DF]
        if len(set(toks)) > len(set(best)):
            best = toks
    ranked = sorted(set(best), key=lambda t: (df[t], -len(t)))   # 식별력(저DF) → 길이순
    if len(ranked) >= 2:
        return ranked[:2]
    if len(ranked) == 1 and df[ranked[0]] <= 1 and len(ranked[0]) >= 4:
        return ranked[:1]
    return []


def _gen_regex(kws: list[str]) -> str | None:
    if not kws:
        return None
    if len(kws) == 1:
        return re.escape(kws[0])
    return "".join(f"(?=.*{re.escape(k)})" for k in kws[:2])


def _rule_patterns(rule: dict, df: Counter) -> tuple[list[str], str]:
    """(정규식 목록, mode) — mode: regex(원본 실판정)|heuristic(생성)|classifier(없음)."""
    orig = (rule.get("patterns") or {}).get("regex") or []
    if orig:
        return list(dict.fromkeys(orig)), "regex"        # 원본 regex, 중복 제거
    ptype = rule.get("patternType") or ""
    if "classifier" in ptype or not ptype:
        gen = _gen_regex(_keywords(rule.get("examplesPositive") or [], df))
        if gen:
            return [gen], "heuristic"
    return [], "classifier"


def main() -> int:
    if not os.path.isdir(_SRC_DIR):
        print(f"[build-guardrails] 소스 디렉터리 없음: {_SRC_DIR}", file=sys.stderr)
        print("  GUARDRAILS_SCRIPTS_DIR 로 wise-Guardrails scripts 경로를 지정하세요.", file=sys.stderr)
        return 2
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(glob.glob(os.path.join(_SRC_DIR, "*.kr.json")))
    raw: dict[str, list[dict]] = {}   # domain -> rules(원본, rule_id dedup)
    ids: dict[str, set] = {}
    # ── pass 1: 도메인 병합 + 교차도메인 토큰 DF 계산 ──
    df: Counter = Counter()
    for fp in files:
        data = json.load(open(fp, encoding="utf-8"))
        dk = data.get("domain")
        if not dk:
            continue
        bucket = raw.setdefault(dk, [])
        idset = ids.setdefault(dk, set())
        domain_tokens: set[str] = set()
        for r in data.get("rules", []):
            rid = r.get("ruleId")
            if rid in idset:
                continue
            idset.add(rid)
            bucket.append(r)
            for ex in r.get("examplesPositive") or []:
                domain_tokens |= _tokens(ex)
        for tok in domain_tokens:
            df[tok] += 1

    # ── pass 2: 컴파일 ──
    manifest_domains = []
    for dk in sorted(raw):
        rules_out: list[dict] = []
        for r in raw[dk]:
            pats, mode = _rule_patterns(r, df)
            msg = r.get("messageTemplate") or {}
            rules_out.append({
                "rule_id": r.get("ruleId"),
                "io_type": r.get("ioType", "both"),
                "category": r.get("category", ""),
                "sub_category": r.get("subCategory", ""),
                "severity": r.get("severity", "medium"),
                "action": r.get("action", "warn"),
                "priority": r.get("priority", 100),
                "description": r.get("description", ""),
                "patterns": pats,
                "mode": mode,
                "generated": mode == "heuristic",
                "message_ko": msg.get("ko-KR", ""),
                "message_en": msg.get("en", ""),
            })
        regex_n = sum(1 for r in rules_out if r["mode"] == "regex")
        heur_n = sum(1 for r in rules_out if r["mode"] == "heuristic")
        # 실판정(원본 regex) 있으면 functional, 없고 휴리스틱 있으면 heuristic, 둘 다 없으면 catalog_only
        if regex_n:
            status = "functional"
        elif heur_n:
            status = "heuristic"
        else:
            status = "catalog_only"
        name_ko, name_en = _DISPLAY.get(dk, (dk, dk))
        out = {
            "domain_key": dk, "display_name": name_ko, "display_name_en": name_en,
            "status": status, "required": dk == "global",
            "rule_count": len(rules_out),
            "regex_rule_count": regex_n + heur_n,          # 판정 가능 규칙(실판정+휴리스틱)
            "real_rule_count": regex_n,                    # 실판정(원본 regex)
            "heuristic_rule_count": heur_n,                # 휴리스틱(생성 regex)
            "rules": rules_out,
        }
        json.dump(out, open(_OUT_DIR / f"{dk}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        manifest_domains.append({k: out[k] for k in (
            "domain_key", "display_name", "display_name_en", "status", "required",
            "rule_count", "regex_rule_count", "real_rule_count", "heuristic_rule_count")})
        print(f"[build-guardrails] {dk:38s} rules={len(rules_out):4d} "
              f"real={regex_n:3d} heuristic={heur_n:4d} status={status}")

    manifest = {"source": _SRC_DIR, "generic_df_threshold": _GENERIC_DF,
                "domain_count": len(manifest_domains), "domains": manifest_domains}
    json.dump(manifest, open(_OUT_DIR / "_manifest.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"[build-guardrails] 완료: {len(manifest_domains)} domains → {_OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
