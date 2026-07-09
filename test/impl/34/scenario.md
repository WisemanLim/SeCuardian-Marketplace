# 시험 시나리오 — 에이전트 통합 관리 (§7.6.1, impl/36 · 물리 test/impl/34)

배경(PRD §7.6.1): ① 내장/시스템 탭 → '내장 에이전트' 단일 탭 통합(자산 카탈로그·자산 등록 편입,
Addon 탭 무변경) ② 보안 내장 13종을 marketplace_assets(category=security) 자산 카탈로그로 이관 —
emb_ 패키지 `addon-agents/zip` → `marketplace-assets/security/`, `make seed-security` 신설,
`make seed` 는 기반 시드만 ③ 자산 등록 모달 addon ZIP(스캐폴드 형식) 첨부 업로드
④ `_templates` Board 제외 5종 → `zip/` 이동(fallback).

대상: scripts/{seed,seed_security}.py, Makefile, marketplace-assets/security/,
app/routers/{router_marketplace,router_addon_agent}.py,
front(AgentsPage.tsx·MarketplacePage.tsx·api/marketplace.ts·locales).

| ID | 입력 | 기대 |
|----|------|------|
| TC-34-01 | `make seed`(격리 sqlite) | 기반 시드만 — `nav_group='security'` 행 0 |
| TC-34-02 | `make seed-security`(격리 sqlite) ×2 | marketplace_assets 13종(category=security) + blob 13종(sha256 일치), 재실행 멱등 |
| TC-34-03 | GET /api/marketplace/catalog?category=security | 13종 반환, installed=false |
| TC-34-04 | POST /api/marketplace/install/teler-ids | 201 — tbl_agent_config upsert(nav_group='marketplace'), blob hot-deploy 호출(deploy_zip 모킹) |
| TC-34-05 | 자산 등록 + POST /catalog/{key}/zip | 201 — blob 저장·checksum 반환 (zip 스캐폴드 등록 UI 백엔드 계약) |
| TC-34-06 | 디렉터리 구조 | zip/ 에 보안 emb_ 13종 부재·이동 템플릿 5종 존재, marketplace-assets/security/ 에 13종(+zip), _templates=Board 만 |
| TC-34-07 | templates list/download/scaffold | 6종 목록·다운로드·스캐폴드 fallback 정상 |
| TC-34-08 | locales·프론트 | agent.system/noSystem 제거, assetZip/assetZipHint 추가(ko/en), tsc 0오류 |
