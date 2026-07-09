# 시험 결과 — 내장 에이전트 화면 i18n 전면 적용 + 중복 타이틀 제거 (impl/34 · 물리 impl/32)

- 일시: 2026-07-09
- 판정: **6/6 PASS**

| ID | 시험 | 판정 | 비고 |
|----|------|------|------|
| TC-32-01 | ko/en 키 패리티 | ✅ PASS | flatten 비교 ko-only/en-only 각 0건 (wf 51·wfb 55·rag 17·pg 14·mp 12·dash 17·grd 27 키) |
| TC-32-02 | 잔존 한국어 리터럴 | ✅ PASS | 8파일 코드 라인(주석 제외) 0건 — 총 137개 치환 |
| TC-32-03 | 본문 h1 제거 | ✅ PASS | Workflow/RAG/Playground/Guardrails/Dashboard 5화면 h1 제거 → pageDesc 만(R18 표준), 헤더(AppLayout) 타이틀 단독 표시 |
| TC-32-04 | nav_group 칩 매핑 | ✅ PASS | `navGroupLabel()` — "기본 Agent"/"내장 에이전트" locale 매핑, 미등록 값 원문. SeCuardian AgentsPage 에도 동기 반영 |
| TC-32-05 | tsc + build | ✅ PASS | MP `tsc --noEmit` 0오류 · `vite build` 성공(exit 0) · SeCuardian tsc 0오류 |
| TC-32-06 | Dashboard 설명 다국어 | ✅ PASS | `cfg.description`(ko 전용) → `pickDescription(descriptions, …)` R18-7 fallback 체인 적용 |

## 부수 수정

- `nav.aiAssistant` ko 오타 수정: "AI 어이스턴트" → "AI 어시스턴트"
- WorkflowBuilderPage `NODE_META` 에서 label/desc 를 분리(색상·기본설정만 유지),
  `wfb.node.{type}.label/desc` locale 키로 조회 — 신규 언어 추가 시 JSON 만 확장
- GuardrailsPage `statusBadge()` 가 라벨 키(labelKey)를 반환하도록 변경(사용처 `t()`)

## 검증 방법 재현

```bash
cd front && pnpm exec tsc --noEmit && pnpm run build
# 키 패리티·잔존 리터럴: test/impl/32/scenario.md TC-32-01/02 python 스니펫
```
