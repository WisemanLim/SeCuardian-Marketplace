# 시험 시나리오 — impl/45 (물리 test/impl/43): §7.6.4-5·6 설치됨 탭 카테고리 그룹핑 + 해제 잔존 결함

- 날짜: 2026-07-10
- 대상: `front/src/pages/agents/AgentsPage.tsx`(대소문자 무시 매칭·카테고리 그룹), locales.
  **프론트 전용**(백엔드 무변경).

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | 대소문자 무시 매칭 (정적) | `asset_key.toLowerCase()`·`agent_key.toLowerCase()` 기반 필터 — usermanager↔UserManager 잔존 해소 |
| A2 | 잔존 재현 데이터 검증 (dev DB) | config `usermanager`(소문자) 존재 + 자산 `UserManager` 미설치 → 필터 로직상 숨김 판정 |
| B1 | 카테고리 그룹 구조 (정적) | installedGroups — builtin 최우선 → security → utilities → general |
| B2 | 그룹 섹션 렌더 (정적) | 설치됨 탭 `mp.cat.*` 헤더 + 그룹별 grid |
| B3 | 그룹 내 정렬 (정적) | builtin=config 순서 유지, 카탈로그 그룹=catalogOrderIdx 순 |
| C1 | `mp.cat.builtin` 로케일 ko/en 패리티 | 양측 존재 |
| C2 | 프론트 `tsc --noEmit` | 0오류 |
| D1 | 필터 로직 시뮬레이션 (Python 재현) | 설치→표시 / 해제→숨김 / 대소문자 불일치 케이스 포함 |

## 실행

```bash
uv run python test/impl/43/test_installed_grouping.py
cd front && pnpm exec tsc --noEmit
```
