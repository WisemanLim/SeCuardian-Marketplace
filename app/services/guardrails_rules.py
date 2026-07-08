"""Guardrails 규칙 룰스토어 (F-GRD, PRD §7.8.7).

`app/data/guardrails/` 에 컴파일된 도메인 규칙(정규식 포함)을 로드·캐시하고, 도메인 단위 탐지를
제공한다. 데이터는 `scripts/build_guardrails_data.py` 가 wise-Guardrails 규칙셋에서 생성한다
(classifier 규칙에는 regex 를 생성해 내재화 — `generated:true`). 런타임은 원본에 의존하지 않는다.

데이터가 없으면(무배포 CI 등) 빈 스토어로 동작하고, 호출측은 `guardrails_detector` 의 내장
`global` 13종 폴백으로 대체한다(무중단).
"""
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "guardrails"


@dataclass
class RuleMatch:
    rule_id: str
    domain: str
    category: str
    action: str          # block | redact | mask | sanitize | warn | allow
    severity: str        # low | medium | high | critical
    span: tuple[int, int]
    matched_text: str


@dataclass
class _CompiledRule:
    rule_id: str
    category: str
    action: str
    severity: str
    patterns: list[re.Pattern]


# domain_key -> list[_CompiledRule]
_RULES: dict[str, list[_CompiledRule]] | None = None
# domain_key -> list[dict] (LLM classifier 메뉴용 규칙 메타, priority 내림차순)
_CANDIDATES: dict[str, list[dict]] | None = None
_MANIFEST: dict | None = None


def _compile_patterns(r: dict) -> list[re.Pattern]:
    pats: list[re.Pattern] = []
    for p in r.get("patterns", []):
        try:
            pats.append(re.compile(p))
        except re.error:
            logger.debug("[guardrails_rules] regex 컴파일 실패 %s: %r", r.get("rule_id"), p)
    return pats


def _load() -> None:
    global _RULES, _CANDIDATES, _MANIFEST
    if _RULES is not None:
        return
    _RULES, _CANDIDATES = {}, {}
    manifest_path = _DATA_DIR / "_manifest.json"
    if not manifest_path.exists():
        logger.warning("[guardrails_rules] 컴파일 데이터 없음(%s) — 내장 global 폴백 사용", _DATA_DIR)
        _MANIFEST = {"domain_count": 0, "domains": []}
        return
    _MANIFEST = json.loads(manifest_path.read_text(encoding="utf-8"))
    for dom in _MANIFEST.get("domains", []):
        dk = dom["domain_key"]
        fp = _DATA_DIR / f"{dk}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        compiled: list[_CompiledRule] = []
        cands: list[dict] = []
        for r in data.get("rules", []):
            cands.append({
                "rule_id": r["rule_id"], "sub_category": r.get("sub_category", ""),
                "description": r.get("description", ""), "action": r.get("action", "warn"),
                "severity": r.get("severity", "medium"), "priority": r.get("priority", 100),
                "mode": r.get("mode", "classifier"),
            })
            pats = _compile_patterns(r)
            if not pats:
                continue
            compiled.append(_CompiledRule(
                rule_id=r["rule_id"], category=r.get("category", ""),
                action=r.get("action", "warn"), severity=r.get("severity", "medium"),
                patterns=pats,
            ))
        _RULES[dk] = compiled
        cands.sort(key=lambda c: c["priority"], reverse=True)
        _CANDIDATES[dk] = cands
    logger.info("[guardrails_rules] %d 도메인 규칙 로드", len(_RULES))


def classifier_candidates(domain: str, exclude: set[str] | None = None, limit: int = 40) -> list[dict]:
    """LLM classifier 메뉴용 규칙 목록(priority 내림차순, regex 기매치 제외, limit 개)."""
    _load()
    ex = exclude or set()
    return [c for c in (_CANDIDATES or {}).get(domain, []) if c["rule_id"] not in ex][:limit]


def available() -> bool:
    """컴파일 데이터가 로드됐고 규칙이 하나라도 있으면 True."""
    _load()
    return bool(_RULES)


def domains() -> list[dict]:
    """매니페스트 도메인 목록(카탈로그 시드용)."""
    _load()
    return list((_MANIFEST or {}).get("domains", []))


def has_domain(domain_key: str) -> bool:
    _load()
    return domain_key in (_RULES or {})


async def sync_catalog() -> int:
    """컴파일 매니페스트의 모든 도메인을 `guardrails_domain_catalog` 에 upsert(멱등).

    사용자 토글(`filter_enabled`)은 기존 값을 보존하되, 필수 도메인(global)은 항상 1·is_required=1.
    main.py lifespan 에서 마이그레이션 이후 1회 호출. 반환: upsert 한 도메인 수.
    """
    from app.db import _PH, execute_write, fetch_one
    doms = domains()
    if not doms:
        return 0
    for d in doms:
        dk = d["domain_key"]
        required = 1 if d.get("required") else 0
        existing = await fetch_one(
            f"SELECT filter_enabled FROM guardrails_domain_catalog WHERE domain_key = {_PH}", (dk,)
        )
        real_n = d.get("real_rule_count", 0)
        heur_n = d.get("heuristic_rule_count", 0)
        if existing:
            fe = 1 if required else existing["filter_enabled"]
            await execute_write(
                f"UPDATE guardrails_domain_catalog SET display_name = {_PH}, status = {_PH}, "
                f"rule_count = {_PH}, regex_rule_count = {_PH}, real_rule_count = {_PH}, "
                f"heuristic_rule_count = {_PH}, is_required = {_PH}, "
                f"filter_enabled = {_PH}, last_synced_at = CURRENT_TIMESTAMP WHERE domain_key = {_PH}",
                (d["display_name"], d["status"], d["rule_count"], d["regex_rule_count"],
                 real_n, heur_n, required, fe, dk),
            )
        else:
            await execute_write(
                f"INSERT INTO guardrails_domain_catalog "
                f"(domain_key, display_name, status, rule_count, regex_rule_count, real_rule_count, "
                f"heuristic_rule_count, is_required, filter_enabled, last_synced_at) "
                f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, CURRENT_TIMESTAMP)",
                (dk, d["display_name"], d["status"], d["rule_count"], d["regex_rule_count"],
                 real_n, heur_n, required, required),
            )
    logger.info("[guardrails_rules] 카탈로그 %d 도메인 동기화", len(doms))
    return len(doms)


def detect(text: str, domain: str) -> list[RuleMatch]:
    """단일 도메인 규칙 매칭. lookahead-only regex 는 span 이 0폭이므로 전체 구간으로 표기."""
    _load()
    out: list[RuleMatch] = []
    body = text or ""
    for rule in (_RULES or {}).get(domain, []):
        for pat in rule.patterns:
            m = pat.search(body)
            if not m:
                continue
            s, e = m.span()
            if s == e:  # 0폭(lookahead) — 마스킹 대상 구간 없음, 판정 신호로만 사용
                s, e = 0, 0
            out.append(RuleMatch(
                rule_id=rule.rule_id, domain=domain, category=rule.category,
                action=rule.action, severity=rule.severity, span=(s, e),
                matched_text=m.group(0),
            ))
            break  # 규칙당 1회 매치로 충분(중복 억제)
    return out
