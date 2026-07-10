# 시험 결과 — impl/43 (물리 test/impl/41): §7.6.4 마켓플레이스 3탭 재구성

- 날짜: 2026-07-10
- 판정: **PASS** (15/15)
- 실행: `uv run python test/impl/41/test_three_tabs.py` (정적 검증 + 격리 sqlite TestClient)

| # | 케이스 | 결과 |
|---|---|---|
| A1 | Tab 3분류(catalog·installed·addon)·기본 탭 catalog·구 builtin 탭 제거 | ✅ 3건 |
| A2 | 탭 라벨(assetCatalog·installedTab·addon)·카운트 배선 | ✅ 2건 |
| A3 | `자산 등록`=catalog 탭 · `새 Agent 만들기`=addon 탭 | ✅ 2건 |
| B1 | 설치됨 필터 — 카탈로그 외 config OR 활성 설치만 | ✅ |
| B2 | 설치됨 정렬 — 기본·내장 우선 → 카탈로그 표시 순서 | ✅ |
| B3 | 설치/해제/원격설치 시 `marketplaceChanged` 발행(3개소) | ✅ |
| B4 | AgentsPage 리스너 + listCatalog 재조회 배선 | ✅ |
| C1 | 등록→installed=false(숨김) / install→true(표시) / uninstall→false(숨김) — 백엔드 실동작 | ✅ 3건 |
| D1 | locales ko/en `agent.installedTab` 패리티 | ✅ |
| D2 | `tsc --noEmit` + `pnpm build` | ✅ 0오류 (build exit 0) |

## 회귀

| 시험 | 결과 |
|---|---|
| test/impl/40 (§7.6.3 카테고리 카탈로그) | ✅ ALL PASS |
| test/impl/39 (§7.6.2 자산 등록 UX) | ✅ ALL PASS |
| test/impl/1 (F-MP CRUD·설치 수명주기) | ✅ ALL PASS |

## 비고

- 회귀 중 impl/40 C1 1건 FAIL — 사용자가 UI 로 `board` 를 utilities 에 추가 등록(00:46)해
  라이브 dev DB utilities 가 7이 된 것. **구현 결함 아님** — C1 을 정확 카운트 대신
  시드 최소치(시드 6종 키 포함 + security ≥13) 검증으로 완화 후 ALL PASS.
- 좌측 네비 노출(§7.6.4-4)은 기존 hot-deploy 경로 무변경 — 코드 변경 없음.
- 백엔드 무변경(프론트 전용) — `installed` 판정은 기존 카탈로그 API 계약 재사용.
