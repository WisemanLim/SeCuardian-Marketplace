# 시험 결과 — 자산 디렉터리 재구성 (§7.6.1-7, impl/38 · 물리 test/impl/36)

> **판정**: PASS (impl/36 신규 + impl/34·35 개정 = 24/24, 회귀 impl/1·impl/2 ALL PASS)
> **실행일**: 2026-07-09
> **환경**: macOS darwin 25.5.0 / local SQLite(격리 tmp DB) / uv + pytest

## 실행 명령

```bash
uv run pytest test/impl/36/ test/impl/34/ test/impl/35/ -q   # → 24 passed
uv run python scripts/seed_security.py                       # 라이브 — security 13종 blob 갱신
uv run python test/impl/1/test_marketplace.py                # → ALL PASS
uv run python test/impl/2/test_workflow.py                   # → ALL PASS
uv run ruff check test/impl/36/ app/routers/router_addon_agent.py   # → All checks passed!
```

## 결과 상세

| ID | 판정 | 비고 |
|----|------|------|
| TC-36-01 | PASS | addon-agents/{zip,_templates} 부재, security/builtin/addon/utilities = 13/5/6/6 |
| TC-36-02 | PASS | 각 패키지 디렉터리+`{key}.zip` 쌍, emb_ prefix 0건 |
| TC-36-03 | PASS | templates/list = addon 5종만 (UserManager 등 utilities/builtin 미포함) |
| TC-36-04 | PASS | download/Board 200, UserManager(utilities) 404 |
| TC-36-05 | PASS | scaffold app/service/tool-proxy/rag/shell 5유형 200 (marketplace-assets/addon 조회) |
| TC-36-06 | PASS | builtin/guardrails.zip data/guardrails 구조 보존 |
| TC-36-07 | PASS | seed_security security 경로 무변경, 자산 13종 등록 |

## 최종 디렉터리 (marketplace-assets/)

| 카테고리 | 개수 | 항목 |
|----------|------|------|
| security | 13 | vasca-cve · cilium-netpol · teler-ids · shuffle-soar · neosync-dlp · otel-collector · teleport-pam · velociraptor-dfir · ai-redteam · isms-p-evidence · behavior-noti · agentic-soc · ai-eval-gate |
| builtin | 5 | marketplace · workflow · rag · playground · guardrails |
| addon | 6 | Board · RagAgent · ServiceAgent · ShellAgent · ToolProxyAgent (스캐폴드 템플릿) |
| utilities | 6 | UserManager · server-shell · ai-traffic-monitor · caddy-proxy · grafana-dashboard · truffle-scan |

`addon-agents/` 잔여: `Makefile`·`README(.en).md`·`deployed/`(런타임 bind mount).

## 코드 변경

- `router_addon_agent.py`: `_TEMPLATES = marketplace-assets/addon`, `_ZIP_CATALOG`/
  `_ZIP_TEMPLATE_NAMES` fallback 제거. `_template_dirs`/`_find_template_dir`/`download_template`
  단일 경로화.
- `addon-agents/Makefile`: `TMPL_BASE = ../marketplace-assets/addon`.
- 개정: impl/34 TC-06/07(신규 레이아웃), impl/35 TC-01/04/05(marketplace-assets 기준).
