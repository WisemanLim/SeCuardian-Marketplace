"""Guardrails `global` 도메인 로컬 판정기 (F-GRD, PRD §7.8.0/§7.8.2).

wise-Guardrails Detection-Engine 의 `register_global_privacy()` 13종 정규식 탐지기를
동일 계약(PII/신용정보 13종)으로 재구현한다. MCP Server(:8080) 연결 실패/미구성 시에도
1차 실기능 범위(global 도메인)가 무중단으로 동작하도록 로컬 폴백을 기본 경로로 둔다.

25개 업종 규칙셋은 판정기가 없는 데이터 상태(PRD §7.8.0 Critical Finding)이므로
이 모듈은 `global` 만 다룬다. 다른 domain_key 요청은 카탈로그 조회만 가능(§7.8.3).
"""
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("uvicorn.error")

_PATTERNS: dict[str, re.Pattern] = {
    "pii.national_id_kr": re.compile(r"\b\d{6}-[1-4]\d{6}\b"),                    # 주민등록번호
    "pii.ssn_us": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                          # 미국 SSN
    "pii.my_number_jp": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),                 # 일본 마이넘버(12자리)
    "pii.passport": re.compile(r"\b[A-Z]{1,2}\d{7,8}\b"),                        # 여권번호
    "pii.email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),                    # 이메일
    "pii.phone_kr": re.compile(r"\b01[0-9]-?\d{3,4}-?\d{4}\b"),                  # 국내 휴대전화
    "pii.phone_us": re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),      # 미국 전화
    "financial.card_number": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),             # 카드번호(Luhn 별도 검증)
    "financial.iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),           # IBAN
    "secret.api_key": re.compile(
        r"\b(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"
    ),                                                                            # API 키(주요 프리픽스)
    "pii.driver_license_kr": re.compile(r"\b\d{2}-\d{6}-\d{2}\b"),               # 운전면허번호
    "pii.business_reg_no_kr": re.compile(r"\b\d{3}-\d{2}-\d{5}\b"),              # 사업자등록번호
    "pii.ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
}

DETECTOR_COUNT = len(_PATTERNS)  # 13종


def _luhn_ok(digits: str) -> bool:
    nums = [int(d) for d in digits if d.isdigit()]
    if len(nums) < 13:
        return False
    total = 0
    for i, n in enumerate(reversed(nums)):
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


@dataclass
class Match:
    rule_id: str
    category: str
    span: tuple[int, int]
    matched_text: str


def detect_global(text: str) -> list[Match]:
    """`global` 도메인 13종 정규식 탐지. 카드번호는 Luhn 통과分만 인정(오탐 억제)."""
    matches: list[Match] = []
    for rule_id, pattern in _PATTERNS.items():
        for m in pattern.finditer(text or ""):
            if rule_id == "financial.card_number" and not _luhn_ok(m.group(0)):
                continue
            matches.append(Match(rule_id=rule_id, category=rule_id, span=m.span(), matched_text=m.group(0)))
    return matches


def redact(text: str, matches: list[Match]) -> str:
    """매치 구간을 마스킹(뒤 4자리만 노출)."""
    out = text
    for m in sorted(matches, key=lambda x: x.span[0], reverse=True):
        s, e = m.span
        raw = out[s:e]
        masked = "*" * max(len(raw) - 4, 0) + raw[-4:] if len(raw) > 4 else "*" * len(raw)
        out = out[:s] + masked + out[e:]
    return out


# 고위험 카테고리 — 시크릿·신용정보·국가 식별번호. 노출 시 단순 마스킹(redact)을 넘어
# 콘텐츠 차단(block)/사람 검토(escalate)로 승격한다(PRD §7.8.2 6단계 결정 enum).
_HIGH_RISK: frozenset[str] = frozenset({
    "secret.api_key",
    "financial.card_number", "financial.iban",
    "pii.national_id_kr", "pii.ssn_us", "pii.my_number_jp",
    "pii.passport", "pii.driver_license_kr", "pii.business_reg_no_kr",
})


def decide(text: str) -> dict:
    """PRD §7.8.2 응답 계약과 동일한 형태로 판정 결과를 반환(내장 `global` 13종 폴백).

    승격 정책: 저위험 PII(이메일/전화/IP)만 → redact. 고위험 1종 → block.
    고위험 2종 이상(대량·복합 유출) → escalate(사람 검토).
    """
    matches = detect_global(text)
    if not matches:
        return {
            "decision": "allow", "riskScore": 0.0, "matchedRules": [], "categories": [],
            "normalizedText": text, "redactedText": text,
        }
    categories = sorted({m.category for m in matches})
    high = _HIGH_RISK.intersection(categories)
    if len(high) >= 2:
        decision, risk = "escalate", 1.0
    elif high:
        decision, risk = "block", round(min(1.0, 0.5 + 0.2 * len(matches)), 4)
    else:
        decision, risk = "redact", round(min(1.0, 0.2 * len(matches)), 4)
    return {
        "decision": decision,
        "riskScore": risk,
        "matchedRules": [m.rule_id for m in matches],
        "categories": categories,
        "normalizedText": text,
        "redactedText": redact(text, matches),
    }


# ── 다도메인 판정 (PRD §7.8.7) ──────────────────────────────────────────
# action → 결정 우선순위. block 최상위(콘텐츠 차단), escalate(사람 검토) 동급.
_ACTION_RANK = {"block": 5, "escalate": 5, "sanitize": 3, "mask": 3, "redact": 3, "warn": 1, "allow": 0}
_SEVERITY_SCORE = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.2}


def _domain_matches(text: str, domain: str):
    """룰스토어 데이터 우선, 없으면 global 내장 폴백. RuleMatch 유사 객체 리스트 반환."""
    from app.services import guardrails_rules as store
    if store.available() and store.has_domain(domain):
        return store.detect(text, domain)
    if domain == "global":
        # 내장 13종 → RuleMatch 호환(action/severity 부여)
        out = []
        for m in detect_global(text):
            act = "block" if m.category in _HIGH_RISK else "redact"
            sev = "critical" if m.category in _HIGH_RISK else "high"
            out.append(store.RuleMatch(
                rule_id=m.rule_id, domain="global", category=m.category,
                action=act, severity=sev, span=m.span, matched_text=m.matched_text,
            ))
        return out
    return []


def _aggregate_decision(matches) -> tuple[str, float]:
    if not matches:
        return "allow", 0.0
    top = max(matches, key=lambda m: _ACTION_RANK.get(m.action, 0))
    rank = _ACTION_RANK.get(top.action, 0)
    if rank >= 5:
        decision = "block" if any(m.action == "block" for m in matches) else "escalate"
    elif rank >= 3:
        decision = "redact"
    elif rank >= 1:
        decision = "warn"
    else:
        decision = "allow"
    sev = max((_SEVERITY_SCORE.get(m.severity, 0.4) for m in matches), default=0.0)
    risk = round(min(1.0, sev + 0.03 * (len(matches) - 1)), 4)
    return decision, risk


def decide_multi(text: str, domains: list[str]) -> dict:
    """여러 도메인 규칙을 동시 평가하고 통합 결정 + 도메인별 breakdown 을 반환(PRD §7.8.7).

    통합 결정 = 매치 규칙 action 중 최상위(block>redact>warn). redactedText 는 전 매치 구간 마스킹.
    """
    all_matches: list = []
    per_domain: list[dict] = []
    seen: set[str] = set()
    for dom in domains:
        if dom in seen:
            continue
        seen.add(dom)
        ms = _domain_matches(text, dom)
        d_decision, d_risk = _aggregate_decision(ms)
        per_domain.append({
            "domain": dom, "decision": d_decision, "riskScore": d_risk,
            "matchedRules": [m.rule_id for m in ms], "matchedCount": len(ms),
        })
        all_matches.extend(ms)

    decision, risk = _aggregate_decision(all_matches)
    from app.services import guardrails_rules as store
    return {
        "decision": decision,
        "riskScore": risk,
        "matchedRules": [m.rule_id for m in all_matches],
        "categories": sorted({m.category for m in all_matches if m.category}),
        "normalizedText": text,
        "redactedText": redact(text, all_matches),
        "evaluatedDomains": list(seen),
        "perDomain": per_domain,
        "source": "rules" if store.available() else "builtin",
    }


# ── LLM classifier (완전판정, PRD §7.8.7) — 패러프레이즈/문맥 위반 판정 ──
_CLASSIFIER_SYSTEM = (
    "You are a compliance guardrail classifier. Given a user TEXT and a numbered MENU of domain "
    "violation rules (id | category | description), decide which rules the TEXT actually violates. "
    "Judge intent/paraphrase, not keyword presence. Respond ONLY with a JSON array of violated rule ids, "
    'e.g. ["FIN_BANK_KR_001"]. Empty array [] if none. No prose.'
)


async def _classify_llm(text: str, domain: str, exclude: set[str]):
    """도메인 규칙 메뉴를 LLM 에 제시해 위반 rule_id 를 판정. 실패/미구성 시 [] (degrade)."""
    import json as _json

    from app.core.config import settings
    from app.services import guardrails_rules as store
    from app.services.llm_fallback import call_ollama

    cands = store.classifier_candidates(domain, exclude, settings.guardrails_classifier_max_rules)
    if not cands:
        return []
    menu = "\n".join(f"{c['rule_id']} | {c['sub_category']} | {c['description']}" for c in cands)
    by_id = {c["rule_id"]: c for c in cands}
    prompt = f"TEXT:\n{text}\n\nMENU:\n{menu}\n\nViolated rule ids as JSON array:"
    try:
        raw = await call_ollama([{"role": "user", "content": prompt}], _CLASSIFIER_SYSTEM)
        start, end = raw.find("["), raw.rfind("]")
        if start < 0 or end < 0:
            return []
        ids = _json.loads(raw[start:end + 1])
    except Exception:  # noqa: BLE001 — LLM 장애/파싱 실패 → degrade
        logger.warning("[guardrails] LLM classifier degrade (domain=%s)", domain)
        return []
    from app.services.guardrails_rules import RuleMatch
    out = []
    for rid in ids:
        c = by_id.get(rid)
        if not c:
            continue
        out.append(RuleMatch(rule_id=rid, domain=domain, category=c["sub_category"],
                             action=c["action"], severity=c["severity"], span=(0, 0), matched_text=""))
    return out


async def decide_multi_llm(text: str, domains: list[str]) -> dict:
    """regex(결정적) + LLM classifier(패러프레이즈, 옵션)의 2단 완전판정(§7.8.7).

    `guardrails_classifier_enabled` off 면 regex 결과(decide_multi)만 반환.
    """
    from app.core.config import settings
    base = decide_multi(text, domains)
    if not settings.guardrails_classifier_enabled:
        return base

    all_matches: list = []
    per_domain: list[dict] = []
    for pd in base["perDomain"]:
        dom = pd["domain"]
        regex_matches = _domain_matches(text, dom)
        excl = {m.rule_id for m in regex_matches}
        llm_matches = await _classify_llm(text, dom, excl)
        combined = regex_matches + llm_matches
        d_decision, d_risk = _aggregate_decision(combined)
        per_domain.append({
            "domain": dom, "decision": d_decision, "riskScore": d_risk,
            "matchedRules": [m.rule_id for m in combined], "matchedCount": len(combined),
            "llmMatched": [m.rule_id for m in llm_matches],
        })
        all_matches.extend(combined)

    decision, risk = _aggregate_decision(all_matches)
    return {
        "decision": decision, "riskScore": risk,
        "matchedRules": [m.rule_id for m in all_matches],
        "categories": sorted({m.category for m in all_matches if m.category}),
        "normalizedText": text, "redactedText": redact(text, all_matches),
        "evaluatedDomains": base["evaluatedDomains"], "perDomain": per_domain,
        "source": "rules+llm",
    }
