# 시험 시나리오 — impl/12: 좌측 nav '사용자' 하단 재배치 (F-WEB, UI)

- 날짜: 2026-07-08
- 신규 요구(§4.5, 사용자 지시): 좌측 네비게이션의 '사용자(사용자 관리)' 항목을 로그인 사용자(supervisor) 블록
  **바로 위 하단**으로 이동. wise-SeCuardian 워크스페이스 전 프로젝트 적용(SeCuardian, SeCuardian-Marketplace; `*-v0` 제외).
- 실행: 정적 검증(`tsc --noEmit` + `vite build`) — 순수 레이아웃 변경, 백엔드 무관.

## 범위
- `front/src/components/layout/AppLayout.tsx` — '사용자 관리' `NavLink` 를 상단 `<nav flex-1>` 내부에서
  꺼내 `</nav>` 직후·User block `<div>` 직전에 별도 `<nav className="px-2 pb-1">` 로 배치.
  admin/supervisor 게이트(`isAdmin`)·아이콘·i18n·collapsed 동작 그대로 유지.
- 2개 프로젝트 동일 패턴 적용(구조 동일).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | SeCuardian `tsc --noEmit` | 0 오류 |
| 2 | SeCuardian `vite build` | 성공(2026 modules) |
| 3 | Marketplace `tsc --noEmit` | 0 오류 |
| 4 | Marketplace `vite build` | 성공(2039 modules) |
| 5 | 위치 | '사용자' 가 상단 nav 목록에서 제거되고 유저 블록 바로 위에 렌더 |

## 판정 기준
- 두 프로젝트 tsc/build 0오류 = PASS. (v0 미적용 확인)
