# SeCuardian-Marketplace (SeCMP)

> **[English →](README.en.md)** · wise-dev-standard / **python-fastapi × ict-saas(govtech·security 오버레이)**
> SeCuardian 의 Orchestrator + AI Assistant + Addon 핫디플로이 아키텍처를 준용하고, 그 위에
> **Marketplace · Workflow · RAG · Playground · Guardrails** 내장 에이전트를 얹는 엔터프라이즈 온프렘 플랫폼.
>
> 문서: [PRD](.docs/SeCMP-PRD.md) · [COMPLIANCE.md](COMPLIANCE.md) · [AGENTS.md](AGENTS.md)

---

## 1. 개요

SeCMP 는 SeCuardian 코어(중앙 Orchestrator + AI Assistant + ZIP 무중단 핫디플로이 + 4-테이블 에이전트 관리)를
기반으로, AI 에이전트·워크플로우·지식베이스(RAG)를 **탐색·설치·버전관리·거버넌스**하는 플랫폼이다.

**구현 현황** (상세: [PRD §9](.docs/SeCMP-PRD.md)):

| 영역 | 상태 |
|---|---|
| Orchestrator + AI Assistant (F-AI), Setup Wizard (F-SETUP) | ✅ 완료 |
| Addon 핫디플로이 (ZIP 업로드·무중단 마운트) | ✅ 복원 |
| 대시보드 (`/dashboard` — 서버상태+에이전트 요약+빠른링크) | ✅ 완료 |
| Marketplace (F-MP: 카탈로그·설치·단일활성버전, **에이전트 관리 통합 허브**) — 백엔드+프론트 | 🟡 |
| Workflow (F-WF: DAG 엔진·8노드[+http]·retry·HITL·SSE·**컴포넌트 팔레트·webhook 트리거(로테이션+HMAC+rate limit)·풀스크린 빌더(팔레트 drag&drop+인스펙터)·Dify DSL Import·부분 편집 PATCH**) — 백엔드+a11y 폼 프론트 | 🟡 |
| RAG (F-RAG: 청킹·BM25+dense·RRF 하이브리드검색·**pgvector 실측완료**) — 백엔드+프론트 | 🟡 |
| Playground (F-PG: 프롬프트/모델/RAG 실험·A/B) — 백엔드+프론트 | 🟡 |
| Guardrails (F-GRD: 실판정+휴리스틱 공존·**도메인 규칙 24종 내재화·필터적용 토글·다도메인·LLM classifier(옵션) 완전판정**·Orchestrator 게이트) — 백엔드+프론트 | 🟡 |
| 환경 분리/키(F-ENV), 웹 포털(F-WEB), 거버넌스(F-GOV) | 🟡 부분 |
| 다국어 설명 확장 구조 + Local LLM 다양화 (SeCuardian R18-7·R19 복제 싱크, §7.11.2) | ✅ 싱크 |

> 5개 내장 에이전트 모두 백엔드+프론트 동작(시험 PASS). 🟡 = 확장 항목(원격 레지스트리·React Flow 캔버스·pgvector·MCP 프록시 등) 잔존. 상세: [PRD §9](.docs/SeCMP-PRD.md#9-구현-현황-implementation-status--2026-07-08-기준).
>
> **자산 등록 ZIP 필수 + 사용자 자산·카탈로그 삭제(impl/49·물리 `test/impl/47`, §7.6.6)**: ① `자산 등록`·카테고리 `+ 추가` 모달은 이제 **addon ZIP 1개 이상 첨부 필수** — 실제 에이전트 파일 없는 빈 자산 등록 차단(메타-only `POST /api/marketplace/catalog` 는 AI 어시스턴트·프로그래매틱 경로용 유지) ② 카탈로그 응답에 `deletable`(디스크 `marketplace-assets/*/{key}.zip` 미보유 = 사용자 등록 자산) 노출 ③ `DELETE /api/marketplace/catalog/{asset_key}` — deletable·비설치 자산만(디스크 보유 403·설치 중 409), assets 전 버전·blobs·installs 이력·marketplace config 행 정리 ④ `DELETE /api/marketplace/catalog-category/{category}` — 전 자산 deletable·비설치 시 카탈로그 일괄 삭제 ⑤ UI: 미설치 사용자 자산 카드 `삭제` 버튼 + 전 자산 deletable 카테고리 헤더 `카탈로그 삭제` 버튼(admin) — 확인은 커스텀 ConfirmDialog(R18-1) ⑥ 회귀 수정: `seed_assets` 가 impl/62 의 `*_worker` 메타 디렉터리를 설치형 자산으로 오등록하던 결함 스킵 처리(R22-4).
>
> **Worker 설치 가이드 동일 적용 + 카탈로그 카드덱 개편 + 가드레일 카탈로그명 다국어(impl/48·물리 `test/impl/46`)**: ① SeCuardian impl/63 동일 적용 — `/api/addon-agents/{key}/worker-{guide,package}` 포팅(메타 = `deployed/{key}` → `marketplace-assets/*/{key}` 폴백, 패키지 zip = marketplace-assets 카테고리 전역), 활성화 응답 worker 요약 + list_addons `has_worker`, MCP 가이드 톤 WorkerGuideModal + 카드 상시 가이드 아이콘(WorkerCorner) ② 자산 카탈로그 — 상단 설명 블록 제거, 설치여부 배지 = 자산명 옆·설치/해제 버튼 = 카드 우상단, 카테고리별 카드 색상(security=보라·utilities=파랑·general=초록) ③ 가드레일 도메인 카탈로그명 다국어 — `guardrails_domain_catalog.display_name_en`(init+멱등 ALTER) 을 `sync_catalog`·API·`pickDescription` 으로 관통, English 모드 영문 표시.
>
> **Marketplace-host 공개 카탈로그 API(impl/47·물리 `test/impl/45`, §7.3.5)**: SeCMP 를 host(레지스트리 서버)로서 외부 SeCuardian 에 개방 — `/api/marketplace-host/{ping,catalog,catalog/{key},download/{key}}`. 소스는 `marketplace-assets/{category}/{Name}.zip` 파일시스템 **전량(설치유무 무관)**, 카테고리별 groups+assets 반환, `checksum`(ZIP SHA256)·`download_path` 로 클라이언트 검증 지원. 인증은 `MARKETPLACE_HOST_API_KEY`(설정 시 Bearer 필수, 미설정 개방 — `.env.local`/`.env.prod` 는 임의 발급 키를 SeCuardian `MARKETPLACE_API_KEY` 와 페어링). 클라이언트 측(3종 배포 방식 scaffold/zip/marketplace)은 SeCuardian R21(test/impl/61).
>
> **다국어 언어셋 dict 일원화 + 설치됨 중복 해소(impl/46·물리 `test/impl/44`, §7.11.2-5)**: ① 전 자산 meta.json(29종)의 `display_name`/`description` 을 `{"ko":…, "en":…}` dict 로 통일하고 zip 재빌드 — **언어 확장(jp/ch/…) 시 코드 수정 없이 데이터 키만 추가**하는 원칙 확립(split 컬럼 authoring 금지). ② 공통 파서 **`app/core/i18n.py`**(`norm_descriptions`/`parse_lang_map`/`lang_json`) 신설 — addon 업로드·마켓플레이스 등록(ZIP/API/원격)·시드가 전부 이 함수로 정규화(종전 `str(dict)` 저장으로 카탈로그 카드에 `{'ko': …}` raw repr 이 노출되던 결함 수정, 기존 오염 행은 `seed-assets` 가 멱등 복구). ③ `marketplace_assets` 에 **`names`/`descriptions` JSON 컬럼** 추가 — 카탈로그 카드가 프론트 공통함수 `parseLangMap`+`pickDescription`(fallback: UI언어→선호언어→ko→첫 언어) 으로 언어 전환에 즉시 반응, 자산 등록 모달도 다국어 dict 로 전송. ④ **asset_key/config 키 소문자 통일** — install seam("UserManager")과 addon 배포("usermanager")가 `tbl_agent_config` 에 2행을 만들어 에이전트(설치됨) 탭에 중복 카드가 뜨던 결함 해소(`seed-assets` 가 기존 대소문자 혼용 키·중복 행·빈 nav_group 을 멱등 정규화). ⑤ SeCuardian 복제 싱크 — `core/i18n.py`·`locale.ts` 동기, `seed_security` 에 `agent_names` JSON 저자 추가, 보안 13종 meta+zip 을 `addon-agents/zip/` 에 복제.
>
> **UI 구성(impl/20 → impl/36 → impl/43·물리 `test/impl/41`, §7.6.4 3탭 재구성)**: 별도 `에이전트 관리` 메뉴 없이 **마켓플레이스 메뉴가 통합 에이전트 허브**다. 상단탭 3분류 — **자산 카탈로그**(기본 탭: 카테고리별 자산 목록·`+ 추가`·`자산 등록`·원격 레지스트리) / **에이전트(설치됨)**(기본·내장 config + **활성 설치된** 카탈로그 에이전트만 — 카탈로그에서 설치하면 나타나고 해제하면 숨김, 카탈로그 매칭은 대소문자 무시 §7.6.4-6. 카탈로그와 동일한 **카테고리 섹션 그룹**으로 표시: builtin → security → utilities → general …) / **Addon 에이전트**(사용자 업로드, `새 Agent 만들기`). 내장 5종(마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일)은 **REQUIRED(비활성 불가)**. 설치/해제/등록 시 `marketplaceChanged` 이벤트로 탭 간 즉시 동기화되며, 자산 등록 모달에서 **addon ZIP(스캐폴드 형식) 다중 첨부** 시 설치에서 hot-deploy 된다(화면 있는 에이전트는 설치 시 좌측 메뉴 노출).
>
> **보안 에이전트 자산 카탈로그 이관(impl/36, §7.6.1)**: 종전 '시스템 에이전트' 탭의 SeCuardian 보안 내장 13종(vasca-cve·cilium-netpol·teler-ids·shuffle-soar·neosync-dlp·otel-collector·teleport-pam·velociraptor-dfir·ai-redteam·isms-p-evidence·behavior-noti·agentic-soc·ai-eval-gate)은 **자산 카탈로그(marketplace_assets, category=security)** 로 이관 — `make seed-security` 로 등록(zip 블롭 포함)하고 카탈로그에서 설치한다. 패키지 13종은 **`marketplace-assets/security/`** 에서 관리(§7.6.1-6 `emb_` 폐지, §7.6.1-7 `addon-agents/zip` 폐지). `make seed` 는 기반 시드(설정·계정)만 수행.
>
> **자산 등록 UX 개선 + 카테고리 카탈로그(impl/41·물리 `test/impl/39`, §7.6.2)**: ① `자산 등록` 모달에서 `asset_key` 입력 제거 — **name(예: `security`)만 입력**하면 서버가 name 슬러그로 asset_key 를 자동부여(충돌 시 `-2` 접미, API 로 명시하면 기존 동작 유지) ② **addon ZIP 다중 첨부** — `새 Agent 만들기` ZIP 업로드처럼 여러 ZIP 을 동시 선택하면 각 ZIP 의 `{key}-meta.json` 기반으로 자산이 개별 등록(신규 `POST /api/marketplace/catalog/zip`)되고 블롭이 저장돼 설치 시 hot-deploy 된다 ③ 자산 카탈로그는 **category(보안 security·유틸리티 utilities·일반 general …) 별 섹션**으로 그룹 표시 ④ `make seed-assets`(`scripts/seed_assets.py`) — `marketplace-assets/{security,utilities}/` 스캔으로 미등록 자산만 카탈로그 INSERT(utilities 6종 편입) ⑤ 등록 완료 시 카탈로그 즉시 갱신(`marketplaceChanged` 이벤트).
>
> **카탈로그 기본 등록 + 카테고리별 추가 등록(impl/42·물리 `test/impl/40`, §7.6.3)**: `marketplace-assets/` 4분류 중 **security·utilities 만 자산 카탈로그 기본 등록 대상**(addon=스캐폴드 템플릿·builtin=코어 내장 제외) — `make db-fresh` 가 seed(기반)→seed-security→seed-assets 를 순차 수행해 초기화 직후에도 security(13)·utilities(6) 가 등록 상태다. 자산 카탈로그의 **각 카테고리 섹션 헤더 `+ 추가` 버튼**(admin)으로 해당 카탈로그에 에이전트(메타 또는 ZIP 다중)를 바로 추가할 수 있고, 상단 `자산 등록` 버튼은 **카탈로그 생성(category 자유 입력, 기본 general) + 자산 등록**을 담당한다.
>
> **마켓플레이스 설치/미설치 동작 상세**: 자산 카탈로그 카드의 배지는 해당 자산의 활성 설치 여부를 뜻한다.
> - **미설치**: `marketplace_assets` 에 메타만 등록된 상태 — 카탈로그에서 탐색·상세 조회만 가능하고 에이전트로는 동작하지 않는다.
> - **설치**(`설치` 버튼 = `POST /api/marketplace/install/{asset_key}`, admin/supervisor): 트랜잭션으로 ① 기존 활성 설치 비활성화(단일 활성 버전) ② `tbl_agent_config` upsert(`nav_group='marketplace'`, `is_enabled=1`) — **내장 에이전트 탭 카드덱과 Orchestrator 인텐트 라우팅에 즉시 편입** ③ `marketplace_installs` 설치 이력 기록 ④ ZIP 블롭이 있으면 addon upload 파이프라인 in-proc 재사용으로 **무중단 hot-deploy**(`/api/addon/{key}/...` 라이브 마운트, 실패해도 설치 기록은 유지되고 `deployed=false` 로 표시).
> - **설치 후 이용**: AI 어시스턴트 질의 시 Orchestrator 가 설치된 에이전트로 자동 라우팅하고, 전용 화면이 있는 에이전트는 좌측 메뉴에 노출된다. 에이전트 카드에서 활성/비활성 토글·MCP 노출 설정 가능.
> - **해제**(`DELETE /api/marketplace/install/{asset_key}`, §7.6.5): 설치 이력 비활성화 + `tbl_agent_config.is_enabled=0` 에 더해 **hot-deploy 산출물을 완전 정리**한다 — addon 이 만든 테이블 DROP, `addon-agents/deployed/{key}/` 삭제, 배포 화면(tsx) 삭제, MCP 중지/설정 삭제, `tbl_addon_agents` 행 삭제(→ 좌측 네비 메뉴 즉시 제거), 화면이 있었으면 web 재빌드. config 행은 유지되어 재설치 시 다시 활성화된다. 라이브 라우터의 완전 제거는 앱 재시작 필요. 과거 잔재 일괄 정리: `make cleanup-addons`(미설치 자산 잔재 + 고아 deployed 디렉터리, 멱등).
>
> **가드레일 도메인 필터(impl/20 §7.8.7)**: wise-Guardrails 규칙 **24개 도메인 전체를 에이전트 내부 데이터(`app/data/guardrails/`)로 관리**한다. `global`(PII/신용정보)은 무조건 필수, 업종 도메인(금융·의료·제조·공공행정 등)은 classifier 규칙에 **regex 를 생성**해 결정적 판정에 사용하며, 도메인 카탈로그의 **`필터적용` 토글**로 테스트 시 적용 여부를 반영(다도메인 동시 판정). 데이터 재빌드: `make guardrails-data` (`scripts/build_guardrails_data.py`).
>
> **워크플로우 컴포넌트 팔레트(impl/25·물리 `test/impl/23`, §7.2.3)**: `GET /api/workflow/components` 가 내장(7종)/시스템/Addon 에이전트의 OpenAPI 엔드포인트를 스캔해 `{에이전트명}-{기능}` 형태 컴포넌트로 실시간 노출한다(신규 테이블 없음, Orchestrator 의 기존 동적 탐지 재사용). 워크플로우 화면에서 팔레트 항목 클릭 시 사전설정된 `agent` 노드(agent_key/method/path)가 삽입되고, 실행 시 실제 API를 호출한다(actor 의 Bearer 토큰 그대로 전달 — 워크플로우가 실행자 권한 이상으로 동작 불가). 신규 `http` 노드(8번째 타입)로 외부 URL 직접 호출도 지원. `agent` 노드는 `config.path` 미지정 시 기존 v1 스텁 동작 그대로 유지(하위호환).
>
> **webhook 수신 트리거(impl/26·물리 `test/impl/24`, §7.2.4)**: `trigger_type="webhook"` 워크플로우 생성 시 서버가 시크릿을 생성해 **응답에 1회만 노출**. 외부 시스템은 `POST /api/workflows/{id}/trigger/webhook` 을 `X-Webhook-Secret` 헤더로 호출 — **JWT 불필요**. 워크플로우 **생성자의 현재 역할**을 조회해 스코프된 임시 토큰을 발급, `agent`/`http` 노드가 그 권한으로 동작(§7.2.3 actor-scoped 원칙 계승 — 생성자를 못 찾으면 무토큰 실행, 해당 노드만 안전하게 실패).
>
> **webhook 보안 강화(impl/29·물리 `test/impl/27`, §7.2.4.1)**: 시크릿 저장을 **bcrypt(단방향) → Fernet 대칭암호**로 전환(로테이션·HMAC 검증에 평문 복원 필요, 키는 `JWT_SECRET_KEY` 파생·신규 env 불요). `POST .../trigger/webhook/rotate`(admin/supervisor) 로 재발급(구 시크릿 즉시 무효). `X-Webhook-Signature: sha256=<hmac>` 헤더 지원(GitHub 컨벤션, 시크릿 자체를 매 호출 전송 안 해도 됨) — 기존 `X-Webhook-Secret` 과 **둘 중 하나만 유효하면 통과**(하위호환). 워크플로우별 인메모리 rate limit(기본 분당 30회, `WORKFLOW_WEBHOOK_RATE_LIMIT_PER_MIN`) — **단일 프로세스 한정**, 강한 보장은 리버스프록시 레벨 병행 권장.
>
> **편집형(드래그) 캔버스(impl/27·물리 `test/impl/25`, §7.2.5)**: `WorkflowCanvas`(React Flow)를 읽기전용 시각화에서 편집형으로 승격 — **노드 드래그 이동·핸들 연결·Backspace/Delete 삭제**. 좌표는 `definition_json.nodes[].position`(스키마 없는 JSON 컬럼이라 **백엔드 변경 없음**)에 저장, 좌표 없는 노드는 기존 BFS 자동배치 폴백. **KWCAG 2.2**: 캔버스는 마우스 중심이라 접근성 대상이 아니며, 기존 a11y 폼 편집기(`DefinitionEditor`)가 캔버스와 **동일한 nodes/edges 상태를 공유하는 대체편집기**로 계속 병행되어 키보드 전용 사용자도 전체 기능(노드/엣지 추가·삭제·컴포넌트 삽입)을 완결할 수 있다.
>
> **풀스크린 워크플로우 빌더(impl/32·물리 `test/impl/30`, §7.2.8)**: impl/27 미니 캔버스(생성 패널 내 320px)가 실사용 불가 판정됨에 따라, Flowise/Dify/n8n 공통의 **팔레트 → 캔버스 drag&drop → 인스펙터** 3분할 빌더로 재구현. `/workflow/builder`(신규)·`/workflow/builder/:id`(기존 편집) 라우트의 `WorkflowBuilderPage` — **좌측 팔레트**(8종 노드 타입 + §7.2.3 컴포넌트 검색, HTML5 드래그·클릭 삽입 병행), **중앙 풀높이 캔버스**(타입별 색상 헤더·config 요약 커스텀 노드, `screenToFlowPosition` 드롭 배치, 연결·이동·삭제), **우측 인스펙터**(agent/llm/condition/http/notify 타입별 구조화 폼 + JSON 폴백 + **엣지 `when` 직접 편집** — §7.2.5 유보 해소, 노드 ID 변경 시 엣지 자동 리매핑). 백엔드는 `PATCH /api/workflows/{id}` 를 **부분 편집으로 확장**(`name`/`description`/`definition_json`, definition 변경 시 `version` +1, `{"enabled"}` 단독 하위호환). **라이선스**: Flowise(Apache-2.0)/Dify UX 패턴만 참조, 코드 복제 없음 — React Flow(MIT) 자체 구현. KWCAG 2.2 는 기존 a11y 폼 편집기 병행 + 팔레트 클릭 삽입 + 인스펙터 표준 폼으로 유지.
>
> **Dify DSL Import 어댑터(impl/28·물리 `test/impl/26`, §7.2.6, 모드 A)**: `POST /api/workflows/import/dify-dsl` 가 Dify Studio export YAML을 §7.2.2 매핑표(`start→trigger`·`llm→llm`·`if-else→condition`·`knowledge-retrieval→agent(rag)`·`http-request→http`·`tool→agent`·`answer/end→notify`)대로 SeCMP `definition_json`으로 변환한다. **관용적 파싱** — `code`·미인식 타입은 크래시 대신 `transform` 플레이스홀더로 대체하고 `warnings[]`로 보고, 댕글링 엣지도 크래시 없이 skip. 가져온 워크플로우는 **항상 `enabled=false`**(사람 검토 강제). 원본 YAML/DSL 버전은 `dify_dsl_source`/`dify_dsl_version` 컬럼에 보관(round-trip 대비). 실행은 SeCMP 자체 엔진(모드 B 위임 실행·모드 C 는 로드맵).
>
> **pgvector 실측 벤치마크(impl/31·물리 `test/impl/29`, §7.5.1)**: `docker-compose.yml` postgres 이미지를 **`pgvector/pgvector:pg17` 로 영구 교체**(구 `postgres:17-alpine` 은 `vector` 확장이 없어 조용히 local 폴백하던 잠재 결함 수정). 실 컨테이너에서 `CREATE EXTENSION vector` 확인 후 `VECTOR_BACKEND=pgvector` 실경로로 식별자 질의 세트(N=40) 실측 — **Recall@10=1.000, p95=20.8ms**(PRD §5 목표 0.89/250ms 대비 초과 달성). 파라프레이즈형 dense 단독 성능은 임베딩 모델 교체(로드맵) 후 별도 재평가 필요.
>
> **완전판정 2단 구조(impl/23 §7.8.7)**: (1) **regex**(결정적) — 규칙별 `mode` 로 **실판정(원본 regex)+휴리스틱(생성 regex) 공존**(카탈로그에 `실판정 N · 휴리스틱 M` 분리 표시). (2) **LLM classifier**(옵션 `GUARDRAILS_CLASSIFIER_ENABLED=true`, 기본 off·비결정적) — regex 후 규칙 메뉴를 LLM 에 제시해 패러프레이즈/문맥 위반까지 판정, 미구성·장애 시 regex 로 degrade. 생성 regex 과탐은 **2개 키워드 공기(AND)+교차도메인 DF 필터**로 완화(단일 흔한 키워드 오탐 제거). 도메인 카탈로그에 **전체 선택/해제 토글**(`필터적용 N/M 도메인` 우측). guardrails ADDON 패키지에 룰셋 데이터 동봉.
>
> **화면 정렬 표준(impl/24)**: 모든 에이전트 화면 루트를 **`.page` 클래스**(`front/src/index.css` = `w-full max-w-6xl p-4 sm:p-6`)로 **좌측정렬·반응형·최대폭 제한** 통일(`mx-auto` 금지). 신규 에이전트(내장·Addon) 개발 기준. **예외**: 전체높이 인터랙티브 레이아웃(AI 어시스턴트 등 채팅·터미널).
>
> **내장 에이전트 MCP 개방(impl/20)**: REQUIRED 내장 5종의 MCP 설정 잠금을 해제 — 7종 내장 에이전트 모두 MCP 서버로 노출 가능.
>
> **자산 디렉터리(impl/38 §7.6.1-7)**: 모든 자산 소스를 `marketplace-assets/<카테고리>/` 로 일원화 — security(13)·builtin(5: marketplace·workflow·rag·playground·guardrails)·addon(5: 스캐폴드 템플릿)·utilities(6: UserManager·server-shell·순수 ADDON 4). `addon-agents/{zip,_templates}` 폐지(deployed/ 만 잔존), 템플릿 조회 경로 = `marketplace-assets/addon`.
>
> **에이전트 표시명 다국어(impl/35·물리 `test/impl/33`, §7.11.2-4 — SeCuardian impl/56 복제 싱크)**: `tbl_agent_config.agent_names` JSON(`{"ko":..,"en":..}`) 신설 — 내장 7종 시드에 en 표시명 병기(마켓플레이스→Marketplace, 워크플로우→Workflow 등)로 en UI 에서 한국어 표시명이 남던 부분 해소. 기동 시 `{"ko": agent_name}` 멱등 백필, meta.json `display_name` dict 형 허용(업로드 시 정규화·동기). 에이전트 카드·좌측 메뉴·헤더 타이틀·가드레일 에이전트 셀렉트에 descriptions 와 동일 fallback 체인 적용.
>
> **내장 에이전트 화면 i18n 전면 적용 + 중복 타이틀 제거(impl/34·물리 `test/impl/32`, §7.11.3)**: UI 언어 English 전환 시 Workflow(목록·풀스크린 빌더·캔버스)·RAG·Playground·Guardrails·Marketplace·Dashboard 화면이 한국어로 남던 결함 수정 — 하드코딩 문자열 137개를 `t()` locale 키(`locales/{ko,en}.json` wf/wfb/rag/pg/mp/dash/grd 섹션)로 치환, ko/en 키 패리티 유지. 본문 h1(5화면)은 상단 헤더(AppLayout) 타이틀과 중복이라 제거하고 **페이지 설명만 표시**(SeCuardian R18 표준 준용). 에이전트 카드의 `nav_group` 칩(DB 한국어 값)도 locale 매핑(en: Basic Agent·Built-in Agent).
>
> **다국어 설명 + Local LLM 다양화(impl/33·물리 `test/impl/31`, §7.11.2 — SeCuardian R18-7·R19 복제 싱크)**: ① 에이전트 설명을 `tbl_agent_config.descriptions` JSON(`{"ko":..,"en":..}`, 타 언어 키 추가만으로 확장)으로 관리 — 기동 시 레거시(`description`/`description_en`) 멱등 백필, meta.json 은 dict 형/레거시 형 모두 허용(업로드 시 정규화). 마이페이지 **선호언어**(`tbl_users.preferred_lang`) 신설 — 표시 fallback `UI언어 → 선호언어 → ko → 첫 언어`, 로그인 시 UI locale 동기화. ② 로컬 LLM 을 **Ollama·llama.cpp·vLLM** 3개 백엔드로 추상화(`app/services/llm_providers.py`, `LOCAL_LLM_PROVIDER` 로 선택, compose profile `llamacpp`/`vllm`) + **작업별 LLM Route**(`llm_routes`: classify/tools/synthesize/domain/chat) + **호출 단위 Metering**(`tbl_llm_usage` 원장, `GET /api/llm/usage` 집계, 시스템 설정 사용량 요약) + **Token 압축**(`LLM_CONTEXT_BUDGET` 초과 시 오래된 히스토리 head/tail 축약). AI 어시스턴트 모델 목록은 `GET /api/llm/models` 동적 조회.
>
> **다국어 설명 authoring 소스 전환 + jp 확장(impl/39·물리 `test/impl/37`, §7.11.2-5)**: impl/33 은 구조·프론트 fallback·선호언어 UI 를 갖췄으나 **authoring 소스가 여전히 split 컬럼**(`02_seed` 이 `description`/`description_en` 기록, `descriptions` 는 boot backfill 파생)이라 타 언어 추가 경로가 없어 미적용이었음. 정정: `02_seed.sql`(내장 7종)·install·`seed_security` 가 `descriptions`/`agent_names` 를 **JSON 직접 저자**(`{"ko","en","jp"}`), split authoring 폐지(레거시 읽기 폴백만). orchestrator `_active_agents_block` 이 descriptions JSON 조회. 마이페이지 선호언어에 **jp 추가**(`locale.jp`) — UI 언어 키 없을 때 선호언어 표출. db.py 중복 `backfill_descriptions` 제거.
>
> **AI 어시스턴트 tool-call 루프 설정화 + 동일 오류 조기 종료(impl/40·물리 `test/impl/38`, §7.11.2-6)**: AI 어시스턴트의 API 오류 자가수정 루프 횟수를 **`llm_tool_max_rounds`**(기본 6, 최소 1)로 시스템 관리 — 우선순위 `os.environ` > **`.env.*`**(`LLM_TOOL_MAX_ROUNDS`) > 시스템 설정 UI(`tbl_settings`) > 기본값, Anthropic/Ollama tool-call 루프 양쪽 적용. **효율 개선**: Ollama 루프에서 동일 `(method, path, status)` 오류가 반복되면(예: 미지원 `PUT` → 405 × 6회) 남은 라운드를 소진하지 않고 **2회 만에 조기 종료** 후 사용자 친화 오류 반환(재시도 1회는 허용 — 자가수정 기회 보존).

---

## 2. 아키텍처 / 디렉터리

```
app/
  main.py                FastAPI 엔트리 (lifespan: migration→seed→addon 로더→ollama warmup)
  agents/orchestrator.py Orchestrator (classify→gather→synthesize, in-proc call_api)
  addon_agent_loader.py  Addon 핫디플로이 (importlib spec → include_router)
  routers/               auth·users·agent·chat_history·suggestions·addon_agent·settings·
                         setup·agent_config·agent_registry·a2a·mcp·mcp_config·
                         marketplace(F-MP)·workflow(F-WF)·rag(F-RAG)·playground(F-PG)·guardrails(F-GRD)
  services/              llm_fallback·ollama_warmup·mcp_proxy_server·openapi_to_mcp·
                         workflow_engine(F-WF DAG)·embeddings+rag_pipeline(F-RAG)·
                         guardrails_detector+guardrails_rules(F-GRD 다도메인 룰스토어)
  data/guardrails/       도메인 규칙(생성 regex 포함) 컴파일 데이터 24 (scripts/build_guardrails_data.py)
  core/                  config(settings)·deps(JWT/RBAC)·security
  rules/                 keyword_matcher (Orchestrator 룰)
  db.py                  raw-SQL 헬퍼 (fetch_one/all·execute_write/insert·_PH·migrations)
sql/{sqlite,pg}/         01_init.sql(멱등 DDL: 코어 + marketplace/workflow/rag/playground/guardrails)
                         02_seed.sql(에이전트/설정/도메인카탈로그 시드)
front/src/
  pages/                 chat·users·settings·profile·addon·setup +
                         marketplace(=agents 통합 허브: 카탈로그/설치됨/Addon 3탭, §7.6.4)·
                         workflow·rag·playground·guardrails (내장 에이전트 5종)
  api/                   백엔드 계약별 axios 클라이언트(1:1 대응)
addon-agents/            Addon ZIP 자산 (deployed/ 는 런타임 bind-mount)
test/impl/<Nth>/         구현 차수별 시험 시나리오·결과
test/dev-env/            개발환경 표준 검증(최초 1회)
```

**서비스(컨테이너)**: `postgres:17` · `redis:7.4` · `ollama` · `api`(profile `app`) · `web`(profile `web`).

---

## 3. 사전 요구사항

| 도구 | 버전 | 비고 |
|---|---|---|
| Python | 3.11+ (검증: 3.13) | `uv` 로 관리 |
| uv | 최신 | 백엔드 패키지·실행 |
| Node | **22+ 권장** (현재 20 동작하나 CI 는 22) | 프론트 |
| pnpm | 9+ (검증: 10) | `corepack enable` |
| Docker Compose | v2+ | dev/staging/prod |

---

## 4. 환경 설정

`.env.example` 를 복사해 사용. **실시크릿 커밋 금지** (`.gitignore` 가 `.env.*` 차단, `.env.example` 만 추적).

| 파일 | 용도 | DB | 비고 |
|---|---|---|---|
| `.env.local` | 개발자 로컬 | SQLite | pm2/직접 실행, dev용 값 허용 |
| `.env.dev` | docker compose | PostgreSQL+Redis | 컨테이너 내부주소는 compose 가 오버라이드 |
| `.env.staging` | prod 동등 | PostgreSQL | 시크릿 `CHANGE_ME` → Vault 주입 |
| `.env.prod` | 운영 | 주입 | **키 목록만** (값 없음, Vault/Secret Manager 주입) |

```bash
cp .env.example .env.local     # 로컬 시작점
# 우선순위: os.environ > .env.<ENV> > tbl_settings > config defaults
```

주요 키: `DATABASE_URL`·`JWT_SECRET_KEY`·`ANTHROPIC_API_KEY`·`OLLAMA_*` · 내장 에이전트 `VECTOR_BACKEND`·`MARKETPLACE_*`·`TENANT_*`·`GUARDRAILS_*`.

---

## 5. 실행 방법

### A) 로컬 (SQLite, 컨테이너 최소)
```bash
make local-all      # Ollama(docker) + BE/FE 를 pm2 로 백그라운드 기동 (SQLite 자동)
make local-stop     # 중단
make local-logs     # 로그
# 또는 개별:
make dev-be         # 백엔드만 (uv run uvicorn --reload)
make dev-fe         # 프론트만 (pnpm dev, :4100)
```

### B) docker compose (dev/staging/prod)
```bash
make up             # 인프라만 (postgres+redis+ollama)
make dev-all        # .env.dev 로 전체 기동 (api profile=app + web)
make dev-down
make staging-all / make prod-all    # 각 .env.<env> 사용
```
- 프로파일: 기본(`up`)=인프라, `app`=api, `web`=프론트 prod 이미지.
- GPU: `OLLAMA_RUNTIME=gpu` 시 `docker-compose.gpu.yml` 자동 병합. macOS Apple Silicon=`mlx`(네이티브 Ollama).

### DB 초기화
```bash
make db-reset       # 스키마 재생성 (FORCE=1 확인 생략)
make seed           # 기반 시드만 — 기본 설정 + 테스트 계정
make seed-security  # 보안 에이전트 13종 자산 카탈로그 등록 (§7.6.1 — 필요 시 명시 실행)
make seed-assets    # marketplace-assets/{security,utilities} 스캔 자산 등록 (§7.6.2 — 미등록만 INSERT)
make db-fresh       # reset + seed(기반) + seed-security + seed-assets — 초기화 직후 security·utilities 등록 상태 (§7.6.3)
make cleanup-addons # 미설치 자산 hot-deploy 잔재 + 고아 deployed 디렉터리 일괄 정리 (§7.6.5, 멱등)
```

---

## 6. 접속 / 포트

| 서비스 | URL | 호스트 포트 | 비고 |
|---|---|---|---|
| Backend API | http://localhost:8100 | `BACKEND_PORT` 8100 → 컨테이너 8000 | |
| API 문서 | http://localhost:8100/docs | | FastAPI Swagger |
| Frontend | http://localhost:4100 | `FRONTEND_PORT` 4100 | Vite. 루트(`/`) 접근 시 `/dashboard` 로 리다이렉트 |
| PostgreSQL | localhost:5432 | `POSTGRES_PORT` | dev+ |
| Redis | localhost:6379 | `REDIS_PORT` | |
| Ollama | localhost:11434 | `OLLAMA_PORT` | 로컬 LLM 폴백 |
| MCP proxy | 20000–20019 | `MCP_PORT_RANGE` | per-agent MCP |

---

## 7. 구현된 API 예시

```bash
# 헬스체크
curl http://localhost:8100/health
# → {"status":"ok","env":"local","mode":"embedded"}

# Setup 상태
curl http://localhost:8100/api/setup/status
# → {"has_supervisor":false,"completed":false}

# 로그인 → JWT
curl -X POST http://localhost:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"secmp","password":"Secu1234!"}'
# → {"access_token":"<JWT>","token_type":"bearer", ...}

# ── Marketplace (F-MP) — Bearer 필요, 등록/설치는 admin/supervisor ──
TOKEN=<JWT>
# 자산 등록 — asset_key 생략 시 name 슬러그로 자동부여 (§7.6.2, 예: "CVE Scanner" → cve-scanner)
curl -X POST http://localhost:8100/api/marketplace/catalog \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"version":"1.0.0","kind":"agent","name":"CVE Scanner"}'
# → {"asset_key":"cve-scanner","installed":false, ...}  (충돌 시 cve-scanner-2)
# ZIP 다중 등록 — 각 ZIP 의 {key}-meta.json 기반 자산 등록 + 블롭 저장 (§7.6.2, 멱등)
curl -X POST http://localhost:8100/api/marketplace/catalog/zip \
  -H "Authorization: Bearer $TOKEN" \
  -F 'files=@agent-a.zip' -F 'files=@agent-b.zip'
# → {"assets":[{"asset_key":"agent-a",...},{"asset_key":"agent-b",...}]}
# 카탈로그 조회
curl http://localhost:8100/api/marketplace/catalog -H "Authorization: Bearer $TOKEN"
# → {"assets":[{"asset_key":"cve-scanner","installed":false,"active_version":null, ...}]}
# 설치 (hot-deploy seam: tbl_agent_config upsert)
curl -X POST http://localhost:8100/api/marketplace/install/cve-scanner \
  -H "Authorization: Bearer $TOKEN"
# → {"id":1,"asset_key":"cve-scanner","version":"1.0.0","status":"installed","active":true,"agent_config_key":"cve-scanner"}
# 해제
curl -X DELETE http://localhost:8100/api/marketplace/install/cve-scanner -H "Authorization: Bearer $TOKEN"

# ── Marketplace-host 공개 카탈로그 API (§7.3.5) — 외부 SeCuardian 소비용, 설치유무 무관 전량 ──
# 인증: MARKETPLACE_HOST_API_KEY 설정 시 `-H "Authorization: Bearer <키>"` 필수(불일치 401), 미설정 시 개방
curl http://localhost:8100/api/marketplace-host/ping
# → {"ok":true,"service":"SeCuardian-Marketplace","categories":["addon","builtin","security","utilities"],"total":29}
curl "http://localhost:8100/api/marketplace-host/catalog?category=security"   # 카테고리별 groups+assets
curl http://localhost:8100/api/marketplace-host/catalog/Board                 # 상세(version·checksum·download_path)
curl -O http://localhost:8100/api/marketplace-host/download/Board             # ZIP 다운로드 (SHA256=checksum)
# 소스 = marketplace-assets/{category}/{Name}.zip 파일시스템 — DB(installs) 미참조 = 설치유무 무관

# ── Marketplace 원격 레지스트리 (F-MP E1.5) — MARKETPLACE_REMOTE_ENABLED=true 필요 ──
curl http://localhost:8100/api/marketplace-remote/ping -H "Authorization: Bearer $TOKEN"
curl http://localhost:8100/api/marketplace-remote/catalog -H "Authorization: Bearer $TOKEN"   # 캐시(sync_interval TTL)
# 원격 자산 다운로드→SHA256 검증→(유효 addon ZIP 이면)실 무중단 hot-deploy→로컬 카탈로그 편입
curl -X POST http://localhost:8100/api/marketplace-remote/install/remote-scanner \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"hot_deploy":true}'
# → {"registered":true,"deployed":true,"checksum":"<sha256>","asset":{...,"source":"remote"}}
#   deployed=true → /api/addon/{key}/... 가 재시작 없이 즉시 라이브(§7.6, upload 파이프라인 in-proc 재사용)

# ── Workflow (F-WF) — DAG 생성·실행·HITL ──
# 워크플로우 생성 (trigger→transform→notify)
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"demo","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"x","type":"transform","config":{"output":{"msg":"$t.input.name"}}},
               {"id":"n","type":"notify","config":{"message":"hi {{x.msg}}"}}],
      "edges":[{"source":"t","target":"x"},{"source":"x","target":"n"}]}}'
# 실행 → completed
curl -X POST http://localhost:8100/api/workflows/1/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"input":{"name":"world"}}'
# → {"id":1,"status":"completed","output_json":"{...\"n\":{\"message\":\"hi world\"}}"}
# HITL 승인 (waiting_hitl 상태 run)
curl -X POST http://localhost:8100/api/workflow-runs/1/hitl -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"approved":true}'

# 컴포넌트 팔레트(impl/25 §7.2.3) — 내장/시스템/Addon 에이전트의 API를 컴포넌트로 조회
curl http://localhost:8100/api/workflow/components -H "Authorization: Bearer $TOKEN"
# → {"components":[{"agent_key":"marketplace","agent_name":"마켓플레이스","category":"builtin",
#                    "method":"GET","path":"/api/marketplace/catalog","capability_key":"카탈로그 조회",
#                    "label":"마켓플레이스-카탈로그 조회"}, ...]}
# agent 노드가 컴포넌트를 실제로 호출(config.path 지정 시 실행) — actor 토큰 그대로 전달, 미지정 시 v1 스텁 하위호환
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"catalog-check","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"a","type":"agent","config":{"agent_key":"marketplace","method":"GET","path":"/api/marketplace/catalog"}}],
      "edges":[{"source":"t","target":"a"}]}}'
curl -X POST http://localhost:8100/api/workflows/2/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"input":{}}'
# → {"status":"completed","output_json":"{...\"a\":{\"agent_key\":\"marketplace\",\"invoked\":true,\"status\":200,\"body\":{...}}}"}
# http 노드(§7.2.3) — 외부 URL 직접 호출(admin-trust 경계, SSRF 는 §6 리스크로 관리)
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"notify-hook","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"h","type":"http","config":{"url":"https://example.com/hook","method":"POST","body":{"msg":"$t.input.msg"}}}],
      "edges":[{"source":"t","target":"h"}]}}'

# webhook 수신 트리거(impl/26 §7.2.4) — trigger_type="webhook" 생성 시 시크릿 1회 노출
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"wh-demo","trigger_type":"webhook","definition_json":{"nodes":[{"id":"t","type":"trigger"}],"edges":[]}}'
# → {"id":3,...,"trigger_type":"webhook","webhook_secret":"<평문, 이 응답에서만 노출>"}
# 외부 시스템은 JWT 없이 시크릿만으로 트리거
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook -H "X-Webhook-Secret: <위 secret>" \
  -H 'Content-Type: application/json' -d '{"event":"deploy-finished"}'
# → {"id":5,"status":"completed","trigger_source":"webhook",...}  (agent/http 노드는 생성자 역할로 실행)
# HMAC 서명 방식(impl/29 §7.2.4.1) — 시크릿 자체를 매 호출 전송 안 함
BODY='{"event":"deploy-finished"}'
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "<위 secret>" | cut -d' ' -f2)"
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook -H "X-Webhook-Signature: $SIG" \
  -H 'Content-Type: application/json' -d "$BODY"
# 시크릿 재발급(로테이션) — 구 시크릿 즉시 무효
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook/rotate -H "Authorization: Bearer $TOKEN"
# → {"id":3,...,"webhook_secret":"<신규 평문, 이 응답에서만 노출>"}

# enabled 토글(impl/30 §7.2.7) — Dify 가져오기(항상 비활성)를 검토 후 활성화하는 흐름 등
curl -X PATCH http://localhost:8100/api/workflows/4 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
# → {"id":4,"enabled":true,...}

# 부분 편집(impl/32 §7.2.8) — 빌더 저장 경로. definition_json 변경 시 version +1
curl -X PATCH http://localhost:8100/api/workflows/4 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"renamed","definition_json":{"nodes":[{"id":"t","type":"trigger","position":{"x":40,"y":120}}],"edges":[]}}'
# → {"id":4,"name":"renamed","version":2,...}  (미전달 필드 보존, 빈 바디 {} 는 422)

# Dify DSL Import(impl/28 §7.2.6, 모드 A) — YAML 붙여넣기 → SeCMP 워크플로우(항상 비활성 생성)
curl -X POST http://localhost:8100/api/workflows/import/dify-dsl -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"dsl":"app:\n  name: demo\nworkflow:\n  graph:\n    nodes:\n      - id: n1\n        data: {type: start}\n    edges: []\n"}'
# → {"id":4,"name":"demo","enabled":false,"dify_dsl_version":"unknown",
#    "definition_json":{"nodes":[{"id":"n1","type":"trigger"}],"edges":[]},"warnings":[]}

# ── RAG (F-RAG) — 컬렉션·수집·하이브리드 검색 ──
curl -X POST http://localhost:8100/api/rag/collections -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"docs","sensitivity":"general"}'
curl -X POST http://localhost:8100/api/rag/collections/1/documents -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"title":"doc-a","text":"SKU-12345 identifies this product."}'
curl -X POST http://localhost:8100/api/rag/collections/1/search -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"query":"SKU-12345"}'
# → {"hits":[{"chunk_id":1,"text":"SKU-12345 identifies...","dense_rank":1,"bm25_rank":1,"rrf_score":0.0328,...}]}

# ── Playground (F-PG) — 프롬프트/모델/RAG 실험 (RBAC 없음, 인증 사용자 누구나) ──
curl -X POST http://localhost:8100/api/playground/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"prompt":"hello world","rag_collection_id":1}'
# → {"id":1,"response_text":"...","provider":"ollama|degraded","latency_ms":42,"citations_json":"[...]"}

# ── Guardrails (F-GRD) — 도메인 카탈로그 + 다도메인 판정 (§7.8.7) ──
curl http://localhost:8100/api/guardrails/domains -H "Authorization: Bearer $TOKEN"
# → {"domains":[{"domain_key":"global","status":"functional","is_required":1,"filter_enabled":1,"regex_rule_count":247,...},
#               {"domain_key":"finance-banking","status":"functional","filter_enabled":0,...}, ...]}
# 도메인 '필터적용' 토글 (admin) — 필수(global)는 해제 불가(409)
curl -X PUT http://localhost:8100/api/guardrails/domains/finance-banking/filter -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
# 판정 시험 — 미지정 시 global(필수)+필터적용 도메인 동시 평가, domains 로 명시도 가능
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"고객확인 KYC 없이 계좌 개설 방법","domains":["global","finance-banking"]}'
# → {"decision":"block","evaluatedDomains":["global","finance-banking"],
#    "perDomain":[{"domain":"finance-banking","decision":"block","matchedCount":13,...}], ...}
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"email me at secret@corp.com"}'
# → {"decision":"redact",...}  저위험 PII(이메일/전화/IP) = 마스킹
# 승격(impl/11): 고위험 1종(시크릿/신용정보/국가식별번호) → block, 2종+ → escalate
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"key sk-abcdefghijklmnopqrstuvwx","domain":"global"}'
# → {"decision":"block","riskScore":0.7,"matchedRules":["secret.api_key"],...}
#   에이전트 토글 ON 상태에서 Orchestrator 가 해당 에이전트 호출 시, block/escalate 입력은 게이트가 HTTP 403 [BLOCKED] 로 차단
# 에이전트별 도메인 토글 (admin/supervisor) — 아래는 Orchestrator 게이트가 실제로 강제하는 설정
curl -X PUT http://localhost:8100/api/guardrails/agents/marketplace/config -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"domain_key":"global","enabled":true,"io_scope":"both"}'
# 이후 Orchestrator 가 call_api 로 marketplace 를 호출하면(예: 자산 등록 description 에 PII 포함)
# guardrails_gate.py 가 orchestrator._exec_api_call 을 가로채 자동으로 마스킹 후 전달 + guardrails_decision_log 기록.
```

---

## 8. 테스트

```bash
make test                                   # pytest 전체
python test/impl/1/test_marketplace.py      # F-MP  (fresh sqlite, 20 assert)
python test/impl/2/test_workflow.py         # F-WF  (fresh sqlite, 21 assert)
python test/impl/4/test_rag.py              # F-RAG (fresh sqlite, 15 assert)
python test/impl/5/test_playground.py       # F-PG  (fresh sqlite, 13 assert)
python test/impl/6/test_guardrails.py       # F-GRD (fresh sqlite, 20 assert — 13종 판정기 전수 검증)
python test/impl/7/test_guardrails_gate.py  # F-GRD Orchestrator 게이트 (fresh sqlite, 15 assert)
python test/impl/9/test_marketplace_remote.py  # F-MP 원격 레지스트리 (fresh sqlite, 14 assert)
python test/impl/10/test_remote_hotdeploy.py   # F-MP 실 ZIP hot-deploy §7.6 (fresh sqlite, 8 assert)
python test/impl/11/test_guardrails_escalation.py  # F-GRD block/escalate 승격 (fresh sqlite, 14 assert)
python test/impl/13/test_guardrails_mcp.py     # F-GRD MCP Server 프록시 (6 assert)
python test/impl/14/test_local_zip_deploy.py   # F-MP 로컬 실 ZIP 배포 (10 assert)
python test/impl/15/test_pgvector_adapter.py   # F-RAG pgvector 어댑터 (6 assert)
python test/impl/16/test_gpg_mtls.py           # F-MP GPG 서명+mTLS (10 assert, gpg 바이너리 필요)
python test/impl/17/test_dashboard_summary.py  # 대시보드 실시간 위젯 (10 assert)
python test/impl/19/test_playground_tokens.py  # F-PG 토큰 사용량 추적 (6 assert)
python test/impl/23/test_workflow_components.py  # F-WF 컴포넌트 팔레트+실호출+http 노드 (18 assert)
python test/impl/24/test_workflow_webhook.py     # F-WF webhook 수신 트리거 (15 assert)
python test/impl/26/test_dify_dsl_import.py      # F-WF Dify DSL Import 어댑터 모드 A (30 assert)
python test/impl/27/test_webhook_security.py     # F-WF webhook 보안 강화(로테이션/HMAC/rate limit) (12 assert)
python test/impl/28/test_workflow_enabled_toggle.py  # F-WF enabled 토글 PATCH (11 assert)
python test/impl/29/test_pgvector_benchmark.py     # F-RAG pgvector 실측 (7 assert, 실 PostgreSQL 필요: docker compose up -d postgres)
python test/impl/30/test_workflow_builder_patch.py # F-WF 풀스크린 빌더 PATCH 부분 편집 (17 assert)
python test/impl/45/test_marketplace_host.py       # §7.3.5 Marketplace-host 공개 카탈로그 API (34 assert)
make lint                                   # ruff
cd front && pnpm exec tsc --noEmit && pnpm exec vite build   # 프론트 타입체크+빌드
```
차수별 시나리오·결과: `test/impl/<Nth>/{scenario,result}.md`. impl/3(F-WF Designer+F-MP 프론트)·impl/8(대시보드)·impl/12(nav '사용자' 하단 재배치)·impl/25(F-WF 편집형 캔버스, 논리 impl/27)는 백엔드 변경 없어 정적 검증(tsc/build)만. impl/26(F-WF Dify DSL Import, 논리 impl/28)은 백엔드+프론트 전종류 시험.

---

## 9. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `ruff` E402 (`main.py` import) | 라우터 import 가 헬퍼 정의 뒤에 위치(원본 SeCuardian 부터 존재) | 기능 영향 없음. 정리 시 import 상단 이동 |
| Node 20 경고 | 스펙 22+ 권장 | `nvm install 22` (pnpm 10 은 20 에서도 동작) |
| ENV=prod 부팅 시 파싱 오류 | `.env.prod` 는 키 목록만(빈 bool/int 주석) | Vault/Secret 로 실제 env 주입 후 기동 |
| Makefile 에 `keycloak-*`/`vault-*`/`harbor-*` 타겟 | 원본 SeCuardian 보안 스택 잔재(SeCMP 범위 밖) | 후속 정리 예정 |
| Playground `pnpm dev` 크래시루프(`ERR_PNPM_IGNORED_BUILDS`) | pnpm 11 `verifyDepsBeforeRun` 가 esbuild ignored-build 로 사전검사 실패 | `front/pnpm-workspace.yaml` `verifyDepsBeforeRun: false` |
| Guardrails 카드번호 오탐 | 임의 13~19자리 숫자열이 모두 매치될 수 있음 | Luhn 체크섬 통과분만 인정(구현됨) — 오탐 잔존 시 규칙 정교화 필요 |
| 워크플로우 캔버스에 노드가 안 보임(`visibility: hidden`) | React Flow v12 는 노드 측정값(`measured`)이 컨트롤드 상태에 반영돼야 표시 — rfNodes 를 매 렌더 재생성하면 measured 소실 | **수정됨(impl/32)** — RF Node[] 를 state 로 보유하고 `applyNodeChanges` 로 dimensions 변경 흡수(`WorkflowBuilderPage`/`WorkflowCanvas`). 동일 패턴 재발 주의 |

---

## 10. 다음 단계 (PRD 잔여)

§9.5 잔여 6항목(F-WF 캔버스·F-RAG pgvector·F-GRD MCP·로컬 실ZIP·대시보드 위젯·GPG/mTLS)은 **impl/13~18 로 전부 완료**.
**impl/25(물리 `test/impl/23`) — F-WF 컴포넌트 팔레트+agent 노드 실호출+http 노드 완료**(§7.2.3).
**impl/26(물리 `test/impl/24`) — F-WF webhook 수신 트리거 완료**(§7.2.4).
**impl/27(물리 `test/impl/25`) — F-WF 편집형 캔버스 완료**(§7.2.5).
**impl/28(물리 `test/impl/26`) — F-WF Dify DSL Import 모드 A 완료**(§7.2.6).
**impl/29(물리 `test/impl/27`) — F-WF webhook 보안 강화 완료**(§7.2.4.1, 로테이션+HMAC+rate limit).
**impl/30(물리 `test/impl/28`) — F-WF `enabled` 토글 PATCH 완료**(§7.2.7).
**impl/31(물리 `test/impl/29`) — F-RAG pgvector 실측 벤치마크 완료**(§7.5.1, Recall@10=1.000·p95=20.8ms).
**impl/32(물리 `test/impl/30`) — F-WF 풀스크린 워크플로우 빌더 완료**(§7.2.8, Flowise/Dify 준용 재구현 + PATCH 부분 편집).
사용자 순차 지정 4항목 + 후속 3항목 **전부 완료**. 남은 것은 외부 인프라 실측·로드맵:

- **실 인프라 실측(잔여)**: mTLS 핸드셰이크(사설 CA), 실 wise-Guardrails MCP 통합(코드·폴백 완료). pgvector 벤치마크는 완료(impl/31).
- **임베딩 모델 교체**: 로컬 해싱 → sentence-transformers/OpenAI(embedding_version 고정).
- **멀티테넌시 namespace/physical, Qdrant** — 로드맵(P5).
- **code 노드**: 샌드박스 보안 검토 선행(§3 하지 않을 것).
- **webhook rate limit 분산화**(단일 프로세스→멀티 인스턴스 공유), `JWT_SECRET_KEY` 로테이션 시 webhook 재발급 운영절차 문서화 — impl/29 1차 유보(§7.2.4.1).
- ~~워크플로우 이름/정의 편집 PATCH~~ — **완료(impl/32, §7.2.8)**. 트리거 타입 변경은 여전히 생성 시에만.
- ~~캔버스 엣지 `when` 직접 편집~~ — **완료(impl/32 인스펙터, §7.2.8)**. **노드 그룹핑/undo-redo/복사붙여넣기/자동 레이아웃/실행 오버레이** — impl/32 1차 유보(§7.2.8).
- **Dify 모드 B(Delegate)/모드 C(Round-trip), 파일 업로드, 실 Dify 인스턴스 검증** — impl/28 1차 유보(§7.2.6).
- **F-PG cost 추적**(Claude 연동 시), eval 실행.
- **운영 문서**: GPG 키 로테이션·mTLS 인증서 발급 절차.

> ~~Orchestrator 게이트 배선~~ — **완료(impl/7)**. `app/agents/guardrails_gate.py` 참조.
> ~~대시보드 화면~~ — **완료(impl/8)**. `front/src/pages/dashboard/DashboardPage.tsx`, 루트 랜딩 페이지.
