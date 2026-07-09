# 시험 시나리오 — 내장 에이전트 화면 i18n 전면 적용 + 중복 타이틀 제거 (impl/34 · 물리 impl/32)

배경(§7.11.3): UI 언어 English 전환 시 Workflow(목록·빌더·캔버스)·RAG·Playground·Guardrails·
Marketplace·Dashboard 화면이 한국어 하드코딩으로 남고, 본문 h1 이 상단 헤더(AppLayout) 타이틀과
중복 표시되던 결함(사용자 스크린샷 보고).

대상: `front/src/pages/{workflow/*,rag,playground,guardrails,marketplace,dashboard}` 8파일,
`locales/{ko,en}.json`(wf/wfb/rag/pg/mp/dash/grd 신설 + nav.aiAssistant 오타 수정 + agent.group*),
`agents/AgentsPage.tsx`(nav_group 칩 locale 매핑 — SeCuardian 동기 반영).

| ID | 입력 | 기대 |
|----|------|------|
| TC-32-01 | ko/en locale 키 패리티 | flatten 비교 — ko-only/en-only 0건 |
| TC-32-02 | 8파일 잔존 한국어(주석 제외 코드 라인) | 0건 |
| TC-32-03 | 본문 h1 중복 타이틀 | Workflow/RAG/Playground/Guardrails/Dashboard h1 제거, pageDesc 만 표시 |
| TC-32-04 | AgentsPage nav_group 칩 | "기본 Agent"→Basic Agent, "내장 에이전트"→Built-in Agent (en), 미등록 값 원문 |
| TC-32-05 | tsc + build | MP tsc 0오류·vite build 성공, SeCuardian(AgentsPage 동기) tsc 0오류 |
| TC-32-06 | Dashboard 에이전트 설명 | ko 전용 `description` → `pickDescription`(R18-7 fallback 체인) |
