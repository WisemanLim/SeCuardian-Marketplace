# 시험 시나리오 — impl/44 (물리 test/impl/42): §7.6.5 해제 시 hot-deploy 잔재 완전 정리 + 상단 설명

- 날짜: 2026-07-10
- 대상: `router_marketplace.py`(uninstall 완전 undeploy), `router_addon_agent.py`
  (`_remove_addon_artifacts` 공용 헬퍼 분리), `scripts/cleanup_addon_remnants.py`, Makefile,
  `MarketplacePage.tsx`(agentConfigChanged 발행), locales(pageDesc)

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | 유효 addon ZIP 자산 등록 + install | 201, deployed=true, `addon-agents/deployed/{key}/` 생성, `tbl_addon_agents` 행 생성 |
| A2 | uninstall | 200 `undeployed: true` — deployed 디렉터리 삭제, addon 행 삭제, MCP 설정 삭제 |
| A3 | uninstall 후 config 행 | 유지 + `is_enabled=0` (재설치 대비) |
| A4 | 재설치 | 201 — 디렉터리·행 재생성 (붕괴 없음) |
| A5 | 메타-only 자산(블롭 없음) uninstall | 200 `undeployed: false`, 오류 없음 |
| B1 | delete_addon 리팩터 회귀 (헬퍼 경유) | 시그니처·가드(404/403) 유지, 기존 흐름 무변경 |
| C1 | `scripts/cleanup_addon_remnants.py` — 격리 환경에서 고아 디렉터리·미설치 잔재 제거 | 멱등 동작 |
| C2 | dev 환경 실정리 결과 | addon 잔재 9건 + 고아 5건 제거, deployed 비움 (본 세션 실행 로그) |
| D1 | `agent.pageDesc` 자산 카탈로그 포함 (ko/en) | 문구 갱신 |
| D2 | MarketplacePage 설치/해제 시 `agentConfigChanged` 발행 | 2개소 (네비 즉시 동기화) |
| D3 | Makefile `cleanup-addons` 타겟 | 존재 |
| D4 | 프론트 `tsc --noEmit` | 0오류 |

## 실행

```bash
uv run python test/impl/42/test_uninstall_cleanup.py   # 스크립트 실행 방식(impl/1 패턴)
cd front && pnpm exec tsc --noEmit
```
