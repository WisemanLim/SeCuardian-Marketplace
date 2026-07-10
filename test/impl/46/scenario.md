# 시험 시나리오 — Worker 가이드 동일 적용 + 카탈로그 카드덱 개편 + 가드레일 카탈로그명 다국어 (impl/48, 물리 test/impl/46)

배경(사용자 요구 2026-07-10):
1. **Worker 설치 가이드 동일 적용** — SeCuardian impl/63 과 동일하게, MCP 가이드 스타일의
   Worker 설치 가이드 모달 + 카드 상시 가이드 아이콘을 SeCMP 에도 적용. SeCMP 는
   worker-guide/worker-package API 자체가 없어 백엔드부터 포팅(메타 소스 =
   `deployed/{key}/` → `marketplace-assets/*/{key}/` 폴백, 패키지 zip = marketplace-assets 카테고리 전역).
2. **자산 카탈로그 카드덱 개편** — ① 카탈로그 상단 설명 블록("자산 카탈로그 … (등록은 상단
   '자산 등록')") 제거 ② 설치여부 배지를 에이전트명 바로 옆으로 이동, 기존 배지 위치(우상단)에
   카드 하단의 설치/해제 버튼 이동 ③ 카테고리별 카드 색상(보안=보라, 유틸리티=파랑, 일반=초록,
   그 외=회색 기본).
3. **가드레일 카탈로그명 다국어** — 도메인 카탈로그명(예: 금융(보험))이 English 모드에서도
   한국어로 표시되는 결함. `_manifest.json` 의 `display_name_en` 을 DB(`display_name_en` 컬럼)·
   API·프론트(pickDescription)로 관통. 기동 중 DB 는 직접 패치(컬럼+값)로 즉시 반영.

| ID | 입력 | 기대 |
|----|------|------|
| TC-46-01 | worker 엔드포인트 포팅 | router_addon_agent 에 `_agent_worker_meta`/`_worker_summary`/`worker-guide`/`worker-package` 존재, toggle 활성화 응답에 worker 요약, list_addons 에 `has_worker` |
| TC-46-02 | worker 메타 해석 | `_agent_worker_meta("vasca-cve")` → bundled 블록(marketplace-assets/security/vasca-cve 폴백), `_agent_worker_meta("agentic-soc")` → external, 가이드 md 본문 확보 |
| TC-46-03 | 프론트 동일 적용 | WorkerGuideModal.tsx = SeCuardian 판과 동일(마크다운 컴포넌트 맵·prose 미사용), AgentsPage 카드 2종 `<WorkerCorner` 배선 + 모달 마운트, addonAgents.ts WorkerInfo/getWorkerGuide/has_worker, locales worker* 4키(ko/en) |
| TC-46-04 | 카탈로그 설명 제거 | MarketplacePage.tsx 에 `mp.catalogDesc` 참조 부재 |
| TC-46-05 | 카드 레이아웃 | 설치여부 배지가 assetName 과 같은 행(이름 옆), 설치/해제 버튼이 카드 우상단 flex 행, 하단 버튼 행 제거 |
| TC-46-06 | 카테고리 색상 | `CATEGORY_TONE` — security=violet, utilities=blue, general=emerald + DEFAULT_TONE 폴백 적용 |
| TC-46-07 | 가드레일 다국어 | sqlite `guardrails_domain_catalog.display_name_en` 컬럼 존재 + 23행 값 채움, sync_catalog UPDATE/INSERT 에 display_name_en, GuardrailsPage 가 pickDescription 으로 표시 |
| TC-46-08 | 정적 검증 | `py_compile` 통과 + `npx tsc --noEmit` 0오류 |

실행: `uv run pytest test/impl/46 -q` + `cd front && npx tsc --noEmit`
