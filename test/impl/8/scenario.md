# 시험 시나리오 — impl/8: 대시보드 화면 (F-WEB, PRD §7.11)

- 날짜: 2026-07-08
- 대상: PRD §9.5 잔여 항목 "대시보드 — `/api/agents` 카탈로그+헬스 요약 화면(현재 nav 만 존재)".
  프론트 전용 구현(백엔드 API 변경 없음, 기존 `/health`·`/api/agent-config/` 재사용).
- 실행: 정적 검증(`tsc --noEmit` + `vite build`) — 백엔드 변경 없어 test/impl 파이썬 시험 불필요.

## 범위
- `front/src/api/health.ts` — `/health`(루트, `/api` 프리픽스 밖) 전용 axios 클라이언트.
- `front/vite.config.ts` — dev 프록시에 `/health` 항목 추가(기존 `/api`·`/mcp` 패턴과 동일).
- `front/src/pages/dashboard/DashboardPage.tsx` — 서버상태·환경·에이전트 전체/활성/필수 카운트,
  5개 내장 에이전트 빠른링크(활성 표시 점 + 설명), nav_group 별 집계 테이블.
- `App.tsx` — `/dashboard` 라우트 추가, 루트(`/`)·와일드카드(`*`) 리다이렉트를 `/chat` → `/dashboard` 로 변경.
- `AppLayout.tsx` — nav 최상단(AI Assistant 위)에 대시보드 항목 + 헤더타이틀 매핑.
- `locales/{ko,en}.json` — `nav.dashboard` 키.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | `pnpm exec tsc --noEmit` | 0 오류 |
| 2 | `pnpm exec vite build` | 성공(2038 modules) |
| 3 | 백엔드 boot | 무영향(routes=24, 변경 없음) |
| 4 | 루트 경로(`/`) 접근 | `/dashboard` 로 리다이렉트(기존 `/chat` 대신) |

## 판정 기준
- 4개 항목 전부 충족 = PASS.
