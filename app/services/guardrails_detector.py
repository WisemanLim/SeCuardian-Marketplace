"""Guardrails `global` 도메인 로컬 판정기 (F-GRD, PRD §7.8.0/§7.8.2).

wise-Guardrails Detection-Engine 의 `register_global_privacy()` 13종 정규식 탐지기를
동일 계약(PII/신용정보 13종)으로 재구현한다. MCP Server(:8080) 연결 실패/미구성 시에도
1차 실기능 범위(global 도메인)가 무중단으로 동작하도록 로컬 폴백을 기본 경로로 둔다.

25개 업종 규칙셋은 판정기가 없는 데이터 상태(PRD §7.8.0 Critical Finding)이므로
이 모듈은 `global` 만 다룬다. 다른 domain_key 요청은 카탈로그 조회만 가능(§7.8.3).
"""
import re
from dataclasses import dataclass

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
    """PRD §7.8.2 응답 계약과 동일한 형태로 판정 결과를 반환.

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
