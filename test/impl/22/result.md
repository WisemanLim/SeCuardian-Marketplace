# 시험 결과 — impl/22: 화면 정렬 표준화(.page)

- 날짜: 2026-07-09
- 판정: **PASS**

## 실행 결과
```
PYTHONPATH=. uv run python test/impl/22/test_alignment.py
[PASS] 1. index.css .page 표준 정의
[PASS] 2.DashboardPage.tsx .page 사용·가운데정렬 제거
[PASS] 2.WorkflowPage.tsx .page 사용·가운데정렬 제거
[PASS] 2.RagPage.tsx .page 사용·가운데정렬 제거
[PASS] 2.PlaygroundPage.tsx .page 사용·가운데정렬 제거
[PASS] 2.GuardrailsPage.tsx .page 사용·가운데정렬 제거
[PASS] 2.AgentsPage.tsx .page 사용·가운데정렬 제거
[PASS] 3. ChatPage 예외(현행 유지)
[PASS] 4. 빌드 CSS 에 .page 방출
[PASS] 5a. Board/UserManager .page 적용
[PASS] 5b. 셸(emb_server-shell) 예외(h-full 유지)
결과: 11 PASS / 0 FAIL
```
- 빌드 CSS: `.page{width:100%;max-width:var(--container-6xl);padding:calc(var(--spacing)*4)}` (+ sm:p-6 미디어쿼리).
- 프론트 tsc/build 0오류.

## 표준 정의
- `.page` = `w-full max-w-6xl p-4 sm:p-6` (`front/src/index.css`, `@layer components`).
- 좌측정렬(`mx-auto` 금지) · 반응형(sm 패딩) · 최대폭 6xl.
- 신규 에이전트(내장·Addon) 화면 최상위 컨테이너 기준 — addon-agents 가이드(README ko/en) 반영.

## 변경 화면
- 적용: dashboard·workflow·rag·playground·guardrails·agents(마켓플레이스 허브) + addon Board·UserManager 템플릿.
- 예외(현행 유지): ChatPage(AI 어시스턴트, 사용자 지시), ShellAgent·emb_server-shell(전체높이 셸).

## 생성/수정 파일
- 신규: `front/src/index.css`(.page), `test/impl/22/{scenario,result,test_alignment}.{md,py}`.
- 수정: 6개 페이지 루트 컨테이너, `addon-agents/_templates/{Board,UserManager}/*-front.tsx`,
  PRD §7.11+변경이력, README.md/README.en.md, addon-agents/README.md/README.en.md.
