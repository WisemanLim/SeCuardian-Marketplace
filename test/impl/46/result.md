# 시험 결과 — Worker 가이드 동일 적용 + 카탈로그 카드덱 개편 + 가드레일 카탈로그명 다국어 (impl/48, 물리 test/impl/46)

일시: 2026-07-10 · 판정: **PASS (5/5 + tsc 0오류)**

| ID | 결과 | 비고 |
|----|------|------|
| TC-46-01 | PASS | worker-guide/worker-package 엔드포인트 + toggle worker 요약 + list_addons has_worker 포팅 |
| TC-46-02 | PASS | `_agent_worker_meta("vasca-cve")` → bundled(VASCA_worker.zip, marketplace-assets/security/vasca-cve 폴백, 가이드 md 존재), agentic-soc → external |
| TC-46-03 | PASS | WorkerGuideModal SeCuardian 동일본, AgentsPage 카드 2개소 WorkerCorner + 모달 마운트, addonAgents.ts WorkerInfo/getWorkerGuide/has_worker, locales worker* 4키 ko/en |
| TC-46-04·05·06 | PASS | catalogDesc 제거, 배지=이름 옆·설치버튼=우상단·하단 버튼 행 제거, CATEGORY_TONE(security=violet·utilities=blue·general=emerald)+DEFAULT_TONE |
| TC-46-07 | PASS | sqlite display_name_en 컬럼 + 23행 값(기동 중 DB 직접 패치), sync_catalog UPDATE/INSERT 관통, GuardrailsPage pickDescription 표시 |
| TC-46-08 | PASS | `py_compile`/uv import OK + `npx tsc --noEmit` exit 0 |

실행 로그: `uv run pytest test/impl/46 -q` → 5 passed. `cd front && npx tsc --noEmit` → exit 0.

메모: 수정 1건 — 시험 자체 결함(TC-46-03 이 주석 내 "prose" 문자열에 오탐) → 클래스 문자열
기준 정정 후 PASS. 가드레일 display_name_en 은 신규 DB(init SQL)·기존 DB(db.py 멱등 ALTER)·
기동 중 dev DB(직접 패치) 3경로 모두 커버. 백엔드 재기동 시 sync_catalog 가 멱등 재동기화.

## 재시험 (오류 수정) — 2026-07-10 · **PASS (6/6)**

사용자 결함 보고 2건: ① 에이전트(설치됨) 탭에서 비활성화/활성화 시 설치 가이드 팝업 미표시
② 카드덱에 Worker 가이드 아이콘 미표시.
원인: ① `patch_agent`(config 경로)가 worker 요약을 반환하지 않음 + 프론트 `handleToggle` 이
응답 worker 를 확인하지 않음(SeCuardian 은 impl/62 에서 양 경로 구현, SeCMP 미포팅)
② `workerKeys` 가 addons 만 참조 — 설치됨 탭 카드는 configs 기반.
수정: `patch_agent` 활성화 응답 worker 요약 + `list_agents` `has_worker` + 프론트
`patchAgentConfig` worker 타입·`handleToggle` 팝업·`workerKeys = configs ∪ addons`
(TC-46-09 신설 PASS). SeCuardian 측 아이콘 동일 수정 = test/impl/63 TC-63-05.

## 재재시험 (근본 원인 — 구버전 배포본 메타) — 2026-07-10 · **PASS (6/6 + 브라우저 실증)**

사용자 재보고: 캐시 삭제·서비스 재기동에도 미반영. 헤드리스 브라우저(browse)로 실 사용
흐름 재현해 근본 원인 확정:
- 카탈로그 설치 시 `marketplace_asset_blobs` 의 **구버전 zip blob**(impl/62 worker 블록
  추가 이전 등록분)이 `addon-agents/deployed/{key}/` 에 배포됨 → deployed meta 에
  `worker` 블록 없음.
- `_agent_worker_meta` 가 deployed meta 를 찾으면 worker 없어도 **조기 return None** —
  `marketplace-assets/*/{key}` 폴백에 도달 불가 → `has_worker=false`·팝업/아이콘 모두 미동작.

수정 2건:
1. **로직**: `_agent_worker_meta` — worker 없는 meta 는 `break` 로 다음 base 폴백
   (SeCuardian 동일 적용, deployed→zip 폴백도 같은 패턴).
2. **데이터**: 디스크 zip(worker 블록 포함, 소스 오브 트루스) 기준으로
   `marketplace_asset_blobs` 20종 blob + checksum 멱등 갱신, vasca-cve 재설치로
   deployed meta 현행화.

실증(headless browse, localhost:4100): 로그인 → 마켓플레이스 → 에이전트(설치됨) 탭 —
VASCA 카드에 Worker 가이드 아이콘 렌더 확인, 클릭 시 신규 스타일 모달(amber 배너·섹션·
코드 하이라이트·패키지 다운로드 버튼) 표시 스크린샷 확보. `has_worker=true` 4종
(vasca-cve·behavior-noti·agentic-soc·ai-eval-gate) API 실측.
