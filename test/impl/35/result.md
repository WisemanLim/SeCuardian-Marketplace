# 시험 결과 — emb_ 규약 폐지 (§7.6.1-6, impl/37 · 물리 test/impl/35)

> **판정**: PASS (5/5 + 회귀 impl/34 8/8·impl/1·impl/2 ALL PASS + 라이브 seed-security 갱신)
> **실행일**: 2026-07-09
> **환경**: macOS darwin 25.5.0 / local SQLite(격리 tmp DB) / uv + pytest

## 실행 명령

```bash
uv run pytest test/impl/35/ test/impl/34/ -q        # → 13 passed
uv run python test/impl/1/test_marketplace.py       # → ALL PASS
uv run python test/impl/2/test_workflow.py          # → ALL PASS
uv run python scripts/seed_security.py              # 라이브 local.db — blob 13종 {key}.zip 갱신
uv run ruff check test/impl/35/ scripts/seed_security.py   # → All checks passed!
```

## 결과 상세

| ID | 판정 | 비고 |
|----|------|------|
| TC-35-01 | PASS | zip/ emb_* 0건 — marketplace·workflow·rag·playground·guardrails·server-shell + 템플릿 5 + 순수 4 |
| TC-35-02 | PASS | marketplace-assets/security 13종(무 prefix), meta `key`/`agent_key` == 디렉터리명 |
| TC-35-03 | PASS | seed-security blob 13종 filename `{key}.zip`, sha256 일치 |
| TC-35-04 | PASS | guardrails.zip — app/meta + `data/guardrails/*.json` 구조 보존(-r 재압축) |
| TC-35-05 | PASS | zip/·marketplace-assets/ 텍스트 emb_ 0건 (ai-traffic-monitor README 문구 정리 포함) |
| TC-35-06 | PASS | 회귀 — impl/34(개정판 8건)·impl/1(F-MP)·impl/2(F-WF) |

## rename 내역

- `addon-agents/zip/`: emb_{marketplace,playground,rag,workflow,guardrails,server-shell} →
  prefix 제거 (guardrails 는 `data/` 하위구조 보존 재압축).
- `marketplace-assets/security/`: emb_* 13종 → prefix 제거.
- `scripts/seed_security.py`: blob 경로/filename `emb_{key}.zip` → `{key}.zip`.
- 시험 보정: impl/34 TC-34-06 을 무 prefix 레이아웃으로 개정.
