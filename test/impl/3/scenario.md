# 시험 시나리오 — impl/3: F-WF Designer 프론트(E3) + F-MP 프론트

- 날짜: 2026-07-08
- 대상: 기존 백엔드(impl/1 F-MP, impl/2 F-WF)에 대한 SPA 화면. PRD §7.11 a11y 폼 편집기 1차(React Flow 캔버스는 로드맵).

## 범위
- `front/src/api/{workflow,marketplace}.ts` — 백엔드 계약 타입 + axios 클라이언트
- `front/src/pages/workflow/WorkflowPage.tsx` — 목록·생성(노드/엣지 폼 편집기)·실행·HITL 승인/거부·취소·노드런 테이블
- `front/src/pages/marketplace/MarketplacePage.tsx` — 카탈로그·등록·설치·해제
- `front/src/pages/{rag,playground,guardrails}/*Page.tsx` — placeholder(후속 차수 대상)
- `App.tsx` 라우트 5종 + `AppLayout.tsx` nav 5종 + `locales/{ko,en}.json` nav 키

## 시험 방법
정적 검증(백엔드 이미 impl/1·impl/2 에서 API 시험 완료 — 이번은 프론트 컴파일·번들 무결성 확인):
1. `pnpm exec tsc --noEmit` — 타입 오류 0
2. `pnpm exec vite build` — 프로덕션 번들 성공

## 판정 기준
- 두 명령 모두 오류 0 = PASS.
