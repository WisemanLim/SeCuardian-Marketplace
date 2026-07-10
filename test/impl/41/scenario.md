# 시험 시나리오 — impl/43 (물리 test/impl/41): §7.6.4 마켓플레이스 3탭 재구성

- 날짜: 2026-07-10
- 대상: `front/src/pages/agents/AgentsPage.tsx`(3탭·설치됨 필터/정렬), `MarketplacePage.tsx`
  (설치/해제 시 `marketplaceChanged` 발행), locales. **백엔드 무변경**(프론트 전용 이터레이션).

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | 탭 구성 (정적) | Tab 타입 = catalog·installed·addon, 기본 탭 catalog |
| A2 | 탭 라벨/카운트 (정적) | assetCatalog·installedTab·addon 키 + catalogAssets/installedConfigs/userAddons 카운트 |
| A3 | 자산 등록 버튼 = catalog 탭, 새 Agent 만들기 = addon 탭 (정적) | 조건 렌더 확인 |
| B1 | 설치됨 필터 (정적) | 카탈로그 외 config OR installedKeys 포함만 표시 |
| B2 | 설치됨 정렬 (정적) | 기본·내장 우선 → 카탈로그 표시 순서(카테고리 순) |
| B3 | 설치/해제/원격설치 시 `marketplaceChanged` 발행 (정적) | handleInstall·handleUninstall·handleRemoteInstall 3개소 |
| B4 | AgentsPage `marketplaceChanged` 리스너 + listCatalog 재조회 (정적) | reload 배선 |
| C1 | 설치→표시/해제→숨김 로직 검증 (백엔드 실동작) | install 후 catalog installed=true, uninstall 후 false — 설치됨 탭 판정 기준 확인 |
| D1 | locales ko/en `agent.installedTab` 패리티 | 양측 존재 |
| D2 | 프론트 `tsc --noEmit` + `pnpm build` | 0오류 |

## 실행

```bash
uv run python test/impl/41/test_three_tabs.py   # 스크립트 실행 방식(impl/1 패턴)
cd front && pnpm exec tsc --noEmit && pnpm build
```
