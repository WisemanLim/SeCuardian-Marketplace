# PRD: SeCuardian-Marketplace (SeCMP)

- 문서 버전: v0.3 (개정 / revised)
- 작성일: 2026-07-08 (v0.1) / 2026-07-08 (v0.2, v0.3 개정)
- 작성자: Wiseman.Lim
- 상태: **개정 초안** — Guardrails Agent 상세 스펙 반영 완료(wise-Guardrails 최종 분석 기반). 단, 원본 시스템 자체의 **구현 갭(§7.8 Critical Finding)** 을 그대로 승계하므로 반드시 §7.8을 먼저 읽을 것.
- 근거 자료:
  - SeCuardian 코드 분석 (`/Users/wise/Developer/wise-project/SeCuardian`)
  - `.docs/Perplexity-Workflow/` 리서치 14종 (Workflow 플랫폼 · Vector DB · Hybrid RAG · OWASP LLM)
  - Flow-Template (`/Users/wise/Developer/wise-project/Flow-Template`) — NAC-Flow PRD·ARCHITECTURE
  - wise-Guardrails (`/Users/wise/Developer/wise-Guardrails`) — 7개 서비스 전수 코드 분석 완료 (§7.8)
  - Dify 공식 문서(`docs.dify.ai/api-reference/workflows/run-workflow`) — Workflow API 실측 확인 (§7.2.2)
  - `domains/govtech.yaml` (wise-dev-standard) — 규제 오버레이 근거 (§7.9)

> **본 PRD의 성격**: `--full` 풀스펙. 섹션 1~6은 비기술 언어(제품 관점), 섹션 7~9는 기술 리더 밀도(아키텍처·NFR·로드맵·일정/리소스). 부록 A~C는 오픈소스 비교표(구현 시 참고용).
> 추측값은 `가정:` 으로 표기. 수치는 근거 문서 기준이며 실측이 아닌 경우 명시.

---

## 1. 개요

- **한 줄 요약**: SeCuardian의 Orchestrator + AI Assistant + Addon Agent(핫디플로이) 아키텍처를 **그대로 준용**하면서, 그 위에 **Marketplace · Workflow · Playground · RAG · Guardrails** 5종의 내장(built-in) 에이전트를 얹어, AI 에이전트·워크플로우·지식베이스(RAG 파이프라인)를 **배포·설치·버전관리·거버넌스**하는 엔터프라이즈 온프렘 지향 플랫폼.
- **배경 / 왜 지금**: SeCuardian은 에이전트를 ZIP으로 업로드하면 무중단으로 라이브 마운트되는 강력한 핫디플로이 기반을 이미 갖췄다. 그러나 (1) 배포 가능한 에이전트를 **탐색·설치·버전관리**하는 시장(Marketplace) 화면이 없고, (2) 에이전트를 **조합해 자동화**하는 Workflow 레이어가 없으며, (3) 프롬프트·RAG·에이전트를 **실험**하는 Playground와 (4) 표준화된 **RAG/Vector** 파이프라인이 없고, (5) 도메인별 **Guardrails(가드레일) 규칙셋을 요청/응답에 강제**하는 거버넌스 에이전트가 없다. Flow-Template(NAC-Flow)이 워크플로우 엔진의 참조 설계를, Perplexity 리서치가 Workflow/Vector/RAG/보안 선택지를, wise-Guardrails가 거버넌스 규칙 엔진의 참조 설계를 이미 제공한다 — 지금이 이를 하나의 제품으로 통합할 시점.
- **제품 코드명**: SeCMP (SeCuardian-Marketplace)

---

## 2. 문제와 대상 (Why & Who)

### 해결하려는 핵심 문제
1. **배포 자산의 시장 부재** — 조직 내 에이전트/워크플로우/RAG 파이프라인이 만들어져도 **찾고·설치하고·버전관리**할 카탈로그가 없다. (영향: 재사용 저하, 중복 개발) (근거: SeCuardian은 `/api/addon-agents/upload`·`export-standalone`은 있으나 카탈로그·설치 경험이 없음)
2. **조합·자동화 레이어 부재** — 개별 에이전트를 이벤트/조건/승인으로 엮는 워크플로우가 없어, 다단계 보안·운영 업무가 수동. (영향: 운영 시간 낭비, 사람 실수) (근거: Flow-Template이 지목한 동일 공백)
3. **실험·검증 표면 부재** — 프롬프트/에이전트/RAG를 안전하게 시험할 Playground가 없어 프로덕션에 직접 실험. (영향: 리스크·품질 저하)
4. **RAG/지식베이스 표준 부재** — 온프렘 규제 환경에서 벡터DB·하이브리드 검색·보안 경계가 표준화되지 않음. (영향: 검색 품질 편차, 규제 위반 리스크) (근거: `.docs/Perplexity-Workflow/` 전반)
5. **거버넌스 규칙 강제 지점 부재** — LLM 요청/응답에 도메인별(보안/금융/의료 등) 규칙셋을 **일관되게 강제**할 표준 에이전트가 없어, 규칙이 있어도(wise-Guardrails 자산) 개별 서비스마다 재구현된다. (영향: 통제 누락, 감사 불가) (근거: wise-Guardrails 멀티서비스 구조 — §7.8)

### 비즈니스 관점 중요성
- **재사용 자산화**: 에이전트/워크플로우/RAG를 마켓 자산으로 관리 → 개발·운영 리드타임 단축.
- **엔터프라이즈 표준 준용**: Marketplace는 SeCuardian 호환을 유지하되 **표준 엔터프라이즈 프레임워크(Dify 계열)** 를 준용해 대외 신뢰성·확장성 확보.
- **규제 대응**: 온프렘/폐쇄망 + OWASP LLM Top 10 통제 + Guardrails 도메인 규칙 내장 → 공공·금융·의료 도입 장벽 완화.

### 타깃 사용자 / 페르소나
| 페르소나 | 역할 | 대표 상황 |
|---|---|---|
| **플랫폼 관리자 (admin/supervisor)** | 에이전트/워크플로우 배포·승인·거버넌스 | Marketplace에서 신규 에이전트 심사·설치, 워크플로우 승인 게이트 관리, Guardrails 도메인 규칙셋 활성화 |
| **워크플로우 빌더 (파워유저)** | 노드 조합으로 자동화 설계 | Workflow Designer에서 이벤트→에이전트→LLM→HITL 승인 플로우 구성 |
| **RAG/지식 담당자** | 문서 수집·인덱싱·검색 튜닝 | RAG 파이프라인에 문서 업로드, 하이브리드 검색 품질 튜닝 |
| **컴플라이언스/보안 담당자** | Guardrails 규칙셋 관리·감사 | 도메인별(보안/공공) 규칙셋 on/off, 위반 로그 검토 |
| **일반 사용자 (user)** | AI Assistant로 질의·실행 | 채팅으로 설치된 에이전트·워크플로우를 자연어로 호출 |
| **에이전트 개발자** | Addon ZIP 제작·게시 | Playground에서 시험 후 Marketplace에 게시 |

### 대표 사용 상황
- 관리자가 마켓에서 "취약점 스캐너" 에이전트를 설치 → **무중단 핫디플로이**로 즉시 AI Assistant 카탈로그에 등장.
- 빌더가 "비인가 단말 차단" 워크플로우를 노드로 설계 → NAC 이벤트 트리거 → 정책 제안(LLM) → 관리자 승인(HITL) → 적용.
- 컴플라이언스 담당자가 "govtech-security" Guardrails 규칙셋을 특정 에이전트에 활성화 → 해당 에이전트의 모든 요청/응답이 규칙 검사를 통과해야 실행.

---

## 3. 범위 (What — In / Out)

### 이번 제품 핵심 기능 (P0/P1)

| # | 기능 | 우선순위 | 설명 |
|---|---|---|---|
| **F-MP** | **Marketplace 내장 에이전트** | P0 | 에이전트/워크플로우/RAG 파이프라인의 카탈로그·상세·설치·버전·심사. 로컬 업로드 + **원격 레지스트리(사내/SaaS)** 접속 지원(§7.3) |
| **F-WF** | **Workflow 내장 에이전트** | P0 | DAG 워크플로우 엔진 + Designer(React Flow). 7노드(trigger/agent/llm/condition/hitl/transform/notify), 실행 상태머신, SSE, retry. **자체 DAG 기본 + Dify DSL/API 호환 어댑터**(§7.2) |
| **F-RAG** | **RAG/지식베이스 내장 에이전트** | P0 | 문서 수집→임베딩→벡터DB→하이브리드 검색(BM25+dense+RRF)→리랭크. pgvector 기본, Qdrant 확장 |
| **F-PG** | **Playground 내장 에이전트** | P1 | 프롬프트/에이전트/RAG/워크플로우 대화형 실험·비교·평가(eval) 표면 |
| **F-GRD** | **Guardrails 내장 에이전트** | P0 | wise-Guardrails(MCP Server, `/mcp/tools/validate_input\|validate_output`) 연동 거버넌스 에이전트. **1차는 `global`(PII/신용정보) 도메인 판정만 실기능**, 25종 업종 규칙셋은 카탈로그 조회만 가능(판정 미지원 — §7.8 Critical Finding). 에이전트별 도메인 활성화는 **SeCMP 자체 DB에서 소유·강제**(업스트림 미강제) |
| **F-GOV** | **거버넌스·보안 공통** | P0 | OWASP LLM Top10 통제, HITL 게이트, 감사로그(tenant/user/prompt·model version), 시크릿 매니저 연동 |
| **F-ENV** | **환경 분리 + 멀티테넌시 설정** | P0 | `.env.local`/dev/staging/prod. SaaS(LLM/Vector) 설정 포함 가능한 `.env.example`(하이브리드). 멀티테넌시 격리 수준 `.env` 확장(§7.4) |
| **F-AI** | **AI Assistant / Orchestrator (필수 내장)** | P0 | SeCuardian Orchestrator(classify→gather→synthesize, in-proc `call_api`) + AI Assistant 를 **기본 필수 내장**(`tbl_agent_config.agent_key='assistant'`, `is_required=true`). Orchestrator 모델은 `orchestrator_model`/`domain_agent_model`(tbl_settings/env). **마켓플레이스·RAG·워크플로우가 공유 LLM(`app/services/llm.py`)·Assistant 를 차후 사용**(워크플로우 `llm` 노드 실동작이 1차 소비처). Claude 주 / Ollama 폴백 / degrade. (§7.11.1) |
| **F-WEB** | **웹 포털(관리자/사용자 UI)** | P0 | React 19 + Vite 7 + RR7 + TanStack Query + Tailwind 4 SPA. 좌측 nav(대시보드/마켓플레이스/워크플로우/RAG + P1 플레이스홀더), 역할 스위처, 백엔드 헤더 인증 연동. KWCAG 2.2(키보드 전용 워크플로우 폼 편집기). (§7.11) |
| **F-SETUP** | **최초 설치 Setup Wizard** | P0 | 웹 포털 최초 접속 시 미완료면 Setup 으로 유도(SeCuardian F6 준용). 단계: status→supervisor 계정 생성→LLM Provider 설정→(선택) admin/user→complete. 전 엔드포인트 인증불요(setup 완료 전), 완료는 `tbl_settings.setup_completed`. (§7.11) |
| **F-OPS** | **운영 명령(Makefile) + DB 초기화** | P0 | 환경별 ops 표준화(SeCuardian 준용): `{local,dev,staging,prod}-{all,stop,logs,status}`. DB: `db-reset`(스키마 재생성, FORCE 확인)·`seed`(기본 설정+테스트 계정)·`db-fresh`(reset+seed). 프론트 타겟(`dev-fe`/`dev-be`). (§7.12) |

### SeCuardian에서 **그대로 준용(무변경 유지)** — 계약(Contract)
- **Orchestrator**: `classify(1~3 intents) → asyncio.gather() → synthesize`, 인프로세스 `call_api`(httpx ASGITransport) 자기호출, OpenAPI 캐시버스트 기반 에이전트 자동 노출. (`app/agents/orchestrator.py`)
- **AI Assistant**: 별도 클래스 없음 — Orchestrator의 tool-calling 경로 + 계층화 시스템 프롬프트. Claude 주(主) / Ollama 폴백.
- **Agent 관리**: DB 주도(4테이블: `tbl_agent_config`·`tbl_addon_agents`·`tbl_addon_agent_capabilities`·`tbl_agent_registry`).
- **Addon Agent 핫디플로이**: `importlib.spec_from_file_location → include_router()` 무중단 마운트, ZIP 매니페스트(`{Name}-app.py`/`-meta.json`/`-front.tsx`/`-sql.sql`), OpenAPI 캐시버스트로 즉시 노출. **→ 기본 유지가 필수 요구사항.**

### 하지 않을 것 (Out of Scope)
- SeCuardian의 F1~F25 기존 코드·테이블·API **변경** (add-only 원칙 준수 — Flow-Template 철학 준용).
- 실장비/외부 연동의 **live 검증**(1차는 mock/simulator 우선; Flow-Template F28 패턴 준용).
- 멀티버전 동시 실행(에이전트 버전 coexistence) — 1차는 단일 활성 버전 + `force` 재업로드.
- 인프로세스 Addon의 **강한 샌드박스(컨테이너 격리)** — 1차는 admin-trust 경계 + Standalone export로 대응(§7 리스크 참조).
- 대규모 분산 벡터DB(Milvus, 20M+) — 로드맵 후반(§8).
- 워크플로우 **loop/sub-flow, cron 스케줄** — 1차 DAG(순차/분기/병렬)만. (Flow-Template와 동일 유보, 단 로드맵 명시)
- **Guardrails 업종별(25종) 규칙셋의 실제 판정기 구현** — wise-Guardrails 자체에 판정 백엔드가 없음(§7.8.0). SeCMP는 카탈로그 노출까지만 담당하고, 판정기 개발은 wise-Guardrails 프로젝트의 별도 로드맵.
- Dify **런타임 이관**(엔진 교체) — 1차는 자체 DAG 유지. Dify는 §7.2.2의 향후 적용 방안으로만 설계(즉시 구현 아님).

---

## 4. 사용자 경험 (How — User Flow)

### 시나리오 1 — Marketplace에서 에이전트 설치 (관리자)
1. 관리자가 **Marketplace** 화면에서 카테고리(에이전트/워크플로우/RAG)로 자산을 탐색 — **로컬 카탈로그 + (설정 시) 원격 레지스트리**(§7.3) 통합 뷰.
2. 자산 상세(설명·버전·capability·거버넌스·필요 env)를 확인 → **설치**.
3. 백엔드가 기존 `upload`/hot-deploy 파이프라인 호출 → SQL 적용 → `load_router()` 무중단 마운트 → `tbl_agent_config` 등록.
4. OpenAPI 캐시버스트로 **AI Assistant가 즉시 신규 에이전트를 인지** → 채팅에서 자연어 호출 가능.
5. 관리자가 필요 시 **비활성/삭제/standalone export**.

### 시나리오 2 — Workflow 설계·실행 (빌더 + 관리자)
1. 빌더가 **Workflow Designer**(React Flow 캔버스)에서 노드를 배치: `trigger(webhook) → agent(레지스트리 검색) → llm(정책 제안) → hitl(승인) → notify`.
2. 저장 시 `definition_json`(nodes+edges)로 `workflows` 테이블에 영속화. (선택) **Dify DSL로 export/import** 가능(§7.2.2).
3. 이벤트/수동 트리거로 **run** 생성 → Flow Engine이 DAG 실행 → 노드별 `input/output/error` 기록.
4. `hitl` 노드에서 관리자 승인 대기(`waiting_hitl`) → 승인 시 후속 노드 진행.
5. **SSE**로 실행 진행을 실시간 표시(run 히스토리 · 노드 타임라인).

### 시나리오 3 — RAG 지식베이스 구축·검색 (RAG 담당자)
1. 담당자가 **RAG** 화면에서 컬렉션 생성(민감/일반 분리) → 문서 업로드.
2. 임베딩 파이프라인 → 벡터DB(pgvector) 인덱싱 + BM25 인덱스 동시 구축.
3. 질의 시 **하이브리드 검색**(BM25 + dense, RRF k=60) → 리랭크 → 인용·신뢰도와 함께 응답.
4. eval 세트로 Recall@10/NDCG@10/p95 지연 추적, 청킹·top-k 튜닝.

### 시나리오 4 — Playground 실험 (개발자)
1. 개발자가 **Playground**에서 프롬프트/모델/RAG 컬렉션/에이전트를 조합해 시험.
2. 응답·비용·지연·인용을 나란히 비교(A/B) → 만족 시 워크플로우 노드 또는 Marketplace 게시로 승격.

### 시나리오 5 — Guardrails 규칙셋 적용 (컴플라이언스 담당자) — 상세 §7.8
1. 담당자가 **Guardrails** 화면에서 도메인 목록을 확인 — `global`(**실판정 가능**, PII 13종)과 25종 업종 규칙셋(**카탈로그만, 판정 로드맵**, §7.8.0)이 구분 표시됨.
2. 특정 에이전트에 `global` 도메인을 **활성/비활성 토글**(`PUT /api/guardrails/agents/{agent_key}/config`).
3. 활성화된 에이전트의 모든 요청/응답이 Guardrails MCP Server(`validate_input`/`validate_output`)를 거쳐 처리(차단/마스킹/경고).
4. 위반 이벤트는 Guardrails 자체 감사(Audit Service) + SeCMP `guardrails_decision_log` 이중 기록.

### 디자인 방향 (프론트 감지됨 — ui-design 후속 가능)
- SeCuardian 프론트 스택(**React 19 + Vite 7 + React-Router 7 + TanStack Query + Tailwind 4**) 준용.
- 신규 화면은 좌측 nav 그룹에 추가(`AppLayout.tsx` nav 블록 + `App.tsx` route). Workflow Designer는 **React Flow(MIT)**.
- 접근성: 워크플로우 캔버스에 **키보드 전용 리스트-폼 대체 편집기**(KWCAG 2.2 — Flow-Template 준용, govtech 확정에 따라 필수).
- `가정:` 상세 디자인 시스템은 `/wise-dev-standard:ui-design --prd`로 후속 보강.

---

## 5. 성공 지표 (Success)

| KPI | 기준선(Baseline) | 목표(Target) | 측정 방법 |
|---|---|---|---|
| 에이전트 설치 무중단성 | 현행 hot-deploy 존재 | 설치 후 재시작 0회, AI Assistant 인지 **≤5초** | 설치→OpenAPI 재노출 시간 로그 |
| Marketplace 설치 성공률(로컬+원격) | 가정: N/A | ≥ **98%** (실패 시 롤백) | 설치 트랜잭션 성공/실패 카운트 |
| 원격 레지스트리 연결성 | 신규 | ping/헬스체크 성공률 ≥ **99.5%**(온프렘), SaaS는 SLA 별도 | `/api/marketplace-remote/ping` 모니터링 |
| 워크플로우 실행 신뢰성 | 신규 | 노드 실행 성공률 ≥ **99%**, retry≤3로 복구율 ≥ 90% | `workflow_node_runs` 상태 집계 |
| RAG 검색 품질 (하이브리드) | pure vector Recall@10 ≈ 0.55~0.80 (리서치 추정) | RRF 하이브리드 Recall@10 ≥ **0.89** | eval 세트 Recall@10/NDCG@10 |
| RAG 검색 지연 | 신규 | p95 ≤ **250ms**(중규모 온프렘) | 검색 경로 p95 지연 |
| OWASP LLM 통제 성숙도 | 취약영역 점수 2(LLM05/08/09) | 전 항목 ≥ **4/5**, write/delete/external 100% HITL | OWALP 스코어카드(부록 C) 재평가 |
| 거버넌스 감사 커버리지 | 부분 | 모든 도구실행·정책적용 **100% 감사로그** (tenant/user/prompt·model version) | 감사로그 완전성 점검 |
| Guardrails PII 탐지율(global 도메인) | 신규 | 13종 탐지기 각 100% 재현(자체 unit fixture 기준) | Detection Engine 응답 `matches[]` 검증 |
| Guardrails 검사 지연 부가분 | 신규 | `global` 도메인 <100ms(p95), Orchestrator 전체 응답시간에 가산 | 게이트 전/후 타임스탬프 diff |
| 에이전트별 도메인 토글 정합성 | 신규 | `agent_guardrail_config` 설정과 실제 호출 도메인 100% 일치 | 토글 변경 후 즉시 호출 로그 대조 |

> **검증 가능한 수용 기준(Given-When-Then, ict-saas 베이스라인 + govtech-security 오버레이)**
> - Given 관리자가 마켓에서 에이전트 설치, When 설치 완료, Then 서버 재시작 없이 `/api/{key}` 라이브 + AI Assistant 카탈로그 노출.
> - Given `.env.*`에 `MARKETPLACE_HOST_URL`/`MODE`가 설정, When Marketplace 화면 진입, Then 원격 카탈로그가 로컬 카탈로그와 병합되어 표시.
> - Given `agent` 노드가 write/delete/external-send 액션, When 실행 도달, Then `hitl` 승인 없이는 진행 불가(LLM08 통제).
> - Given 식별자성 질의(코드/SKU/약어), When 하이브리드 검색, Then BM25 경로 포함으로 Recall@10 ≥ 0.89.
> - Given 민감 컬렉션 검색, When 결과 반환, Then 테넌트/네임스페이스 필터 + 민감필드 마스킹 적용(LLM06).
> - Given `TENANT_ISOLATION_LEVEL=namespace`, When 신규 테넌트 등록, Then 물리 DB 변경 없이 네임스페이스 격리로 데이터 분리.

---

## 6. 리스크 및 메모

### 주요 리스크
| 리스크 | 영향 | 완화 |
|---|---|---|
| **Addon 인프로세스 무샌드박스** (전 권한 실행) | 악성 ZIP = RCE 급 | admin-trust 업로드 경계 유지 + Standalone export 격리 옵션 + (로드맵) 서명·SBOM·이미지 스캔(LLM05) |
| **Excessive Agency (LLM08)** — 자율 실행 과다 | 무단 외부 부작용 | write/delete/external 전면 HITL 게이트(기존 F25-3 재사용) |
| **Overreliance (LLM09)** | 잘못된 자동판단 | 인용+신뢰도 노출, 고영향 결정 강제 검토 |
| **n8n "fair-code" 라이선스** | 마켓 재판매/호스팅 제약 | 오케스트레이션 계층은 라이선스 검증 후 채택; 기본은 자체 DAG (부록 A 경고) |
| **Dify DSL/API 버전 드리프트** | 향후 Dify 어댑터 적용 시 호환 깨짐 | DSL 스키마 버전 핀 + 어댑터 계약 테스트(§7.2.2) |
| **원격 레지스트리 신뢰 경계** | 원격 ZIP 변조/중간자 공격 | SHA256 체크섬 + (선택) GPG 서명 검증, mTLS(온프렘)/HTTPS+API키(SaaS) 강제(§7.3) |
| **리서치 수치는 추정치** | 계획 오차 | Recall/지연/ROI는 Perplexity 추정 — 실측 벤치마크로 재검증(§8 Phase 3) |
| **벡터DB 진화 마이그레이션** | 재인덱싱 비용 | 불변 doc/chunk ID, 임베딩 버전 고정, dual-write/shadow-query 검증 |
| **Guardrails 업종 규칙 = 데이터만 존재, 판정기 없음**(9,371개 규칙 중 98.6%가 `patternType:classifier`인데 런타임 분류기 미구현 — `bootstrap.py`의 `register_manufacturing_food()` 등은 `ImportError` 시 조용히 skip하는 스텁) | 업종별(govtech-security 포함) 컴플라이언스 규칙이 **실제로 차단/경고하지 않음** — "적용됨"으로 오인 시 규제 위반 리스크 | **1차 실기능 범위를 `global`(PII 13종 regex) 도메인으로 명확히 한정 표기**, 업종 규칙셋은 UI에 "카탈로그(로드맵)"로 별도 표시. 실제 판정기 구현은 wise-Guardrails 쪽 별도 로드맵(SeCMP 책임 밖) |
| **Guardrails 도메인 선택이 클라이언트 자기신고 + 미인증** — `api_keys.allowed_domains` 컬럼 존재하나 코드 어디서도 참조 안 됨(grep 확인) | 손상된/악성 에이전트가 자신에게 할당되지 않은 도메인으로 위장 요청 가능 | **SeCMP가 도메인 스코프를 자체 DB(`agent_guardrail_config`)에서 소유**하고, Guardrails 호출 시 사용자 입력이 아닌 이 설정값으로 `domain` 필드를 채움(§7.8.4). 강한 격리가 필요하면 업스트림 `ApiKeyGuard` 확장이 필요함을 리스크로 기록 |
| **Guardrails 감사로그 보존기간 미구현**(Audit Service에 TTL/retention 코드 없음, DB 장애 시 메모리 링버퍼 1000건 캡으로 유실) | 장기 감사 추적성 부족, 규제(§7.9 PIPA) 요구와 불일치 가능 | SeCMP 자체 감사로그(F-GOV)에 `decisionId`+요약을 **이중 기록**해 Audit Service 장애/유실에도 자체 추적성 확보 |
| **Guardrails API 키가 단일 공유 정적 키**(`MCP_HTTP_AUTH=required` 시에도 테넌트별 키/스코프/만료 없음) | 키 유출 시 전체 테넌트 영향 | SeCMP↔Guardrails 간 키는 시크릿 매니저 보관 + 정기 로테이션 운영절차로 완화(코드 레벨 해결 아님, 운영 통제) |

### 의존성 (내부/외부)
- 내부: SeCuardian 코어(F1~F25) — **무변경 준용**. `agent-registry`, HITL 게이트, keyword rules, standalone export 재사용. wise-Guardrails(진행 중) — Guardrails Agent 규칙 소스.
- 외부: Anthropic Claude(주), Ollama(폴백), pgvector/Qdrant, (선택/향후) Dify, React Flow.

### 미결정 사항 (Open Questions) — **v0.2에서 4건 확정**
1. ~~Workflow 1차 기본~~ → **확정: 자체 DAG + Dify DSL/API 호환 어댑터**. 향후 Dify 적용 상세 경로는 §7.2.2.
2. ~~Marketplace 원격 레지스트리 범위~~ → **확정: `.env.*` 기반 Marketplace-host 접속(온프렘/SaaS 겸용)**. 상세 가이드 §7.3.
3. ~~멀티테넌시 격리 수준~~ → **확정: `.env.*` 설정으로 namespace/physical 확장 가능하게 설계**. 상세 §7.4.
4. ~~규제 도메인~~ → **확정: 1차 govtech, security 특화**. NFR 오버레이 §7.9.
5. ~~Guardrails 규칙 스키마/검사 시점/성능 영향~~ → **확정(v0.3): wise-Guardrails 전수 분석 완료**. API 계약·데이터 모델·통합 갭 §7.8. **중요 전제**: 업종별(25종) 규칙셋은 데이터로만 존재하고 실제 판정기(detector/classifier)가 없어 1차 실기능은 `global`(PII) 도메인에 한정 — 상세 근거는 §7.8 Critical Finding.

---

## 7. 기술 메모 (Technical Notes) — *예시/초안*

### 7.1 아키텍처 개요 (SeCuardian 준용 + Layer 2.5 추가)

기존 SeCuardian 8계층은 **무변경**. Flow-Template의 add-only 철학을 준용해 **신규는 전부 추가**:

```
[Front] React19/Vite7/RR7/TanStack/Tailwind4
  └ 신규 화면: /marketplace  /workflow(+Designer)  /rag  /playground  /guardrails   (App.tsx route + AppLayout nav)
[API/Router] FastAPI
  ├ (기존) router_agent(chat/stream), agent_config, addon_agent, agent_registry, a2a, mcp ...  ← 무변경
  └ (신규) router_marketplace(/api/marketplace) + router_marketplace_remote(/api/marketplace-remote)
          router_workflow(/api/workflows, /api/workflow-runs) [+ Dify 어댑터]
          router_rag(/api/rag)   router_playground(/api/playground)
          router_guardrails(/api/guardrails)  ← 계약만 정의, 구현 상세는 §7.8 보류
[Agent Core]  Orchestrator ─(classify→gather→synthesize, call_api in-proc)─ AI Assistant  ← 무변경
              Flow Engine (DAG executor + state machine)  ← 신규, Orchestrator와 병렬 경로
              Guardrails Gate (요청/응답 훅) ← 신규, 위치·시점은 §7.8
[Data] SQLite(dev) / PostgreSQL(prod)  +  Vector: pgvector→Qdrant  +  BM25 인덱스
       멀티테넌시: .env 기반 namespace|physical (§7.4)
[Deploy] uv, docker-compose(app/web profiles), standalone export, systemd/k8s/ansible  ← 준용
```

- **핵심 준용 계약 4종은 §3 참조** — Orchestrator/Assistant/Agent관리/Addon 핫디플로이 무변경.
- 신규 내장 에이전트는 **Path A(네이티브 라우터 + 전용 화면)** 로 구현:
  1. `app/routers/router_{marketplace,workflow,rag,playground,guardrails}.py` (`APIRouter(prefix="/api/{key}")`, `Depends(get_current_user)`/`require_role`).
  2. `app/main.py` include 블록에 등록.
  3. `sql/sqlite/01_init.sql` + `sql/pg/01_init.sql` 양쪽에 멱등 DDL.
  4. `sql/{sqlite,pg}/02_seed.sql` 양쪽에 `tbl_agent_config` 시드(`agent_key`, bilingual desc, nav_group) → **AI Assistant 카탈로그 자동 등록, `_builtin_api_specs()` 자동 발견 — Orchestrator 수정 불필요.**
  5. 프론트: `front/src/pages/{key}/`, `App.tsx` route, `AppLayout.tsx` nav.
  6. (선택) 전용 툴 필요 시 `BaseAgent` 서브클래스 + `_AGENT_MAP` 등록. 기본은 `call_api`로 구동.

### 7.2 Workflow 엔진 (F-WF) — 자체 DAG 기본 + Dify 호환

#### 7.2.1 1차 계약 (자체 DAG, Flow-Template 준용)

- **결정**: **자체 경량 DAG 코어를 1차 기본**으로 채택(SeCuardian 인프로세스·on-prem·Ollama 폴백과 정합). Dify는 **런타임 교체가 아닌 상호운용 어댑터**로만 통합(§7.2.2).
- **데이터 모델(Flow-Template 준용, 도메인 일반화)**:
  ```sql
  workflows(id, name, description, definition_json, trigger_type, trigger_config_json, enabled, version, created_by, ...)
  workflow_runs(id, workflow_id, status, trigger_source, input_json, output_json, started_at, finished_at)
  workflow_node_runs(id, run_id, node_id, node_type, status, input_json, output_json, error, ...)
  ```
- **노드 7종**: `trigger / agent / llm / condition / hitl / transform / notify`.
  - `agent` 노드 = **`POST /api/agent-registry/search` capability 검색** → **설치된 Marketplace 에이전트가 곧 워크플로우 노드**(핵심 seam).
  - `hitl` 노드 = 기존 HITL 게이트 + `tbl_hitl_approvals` 재사용.
  - `llm` 노드 = Claude/Ollama(폴백) — 폐쇄망 대응.
- **실행 상태머신**: `pending → running → waiting_hitl → completed | failed | cancelled`, 노드별 I/O 보존, retry ≤3, **SSE** 진행 스트림.
- **API**: `GET/POST /api/workflows`, `.../{id}/run`, `GET /api/workflow-runs/{id}`, `.../stream`(SSE), `.../cancel`.
- **1차 유보**: loop/sub-flow, cron. (로드맵 Phase 5에서 first-class로 재도입 검토)

#### 7.2.2 향후 Dify 적용 방안 (상세) — SeCuardian/SeCMP에 단계적으로 도입

**실측 근거** (2026-07-08 확인, `docs.dify.ai/api-reference/workflows/run-workflow`):
- Dify Workflow 실행: `POST /workflows/run`, 헤더 `Authorization: Bearer {API_KEY}`(앱별 API 키).
- 요청 바디: `inputs`(object, 워크플로우 변수 매핑), `user`(string, 필수), `response_mode`(`streaming`|`blocking`, 기본 blocking), `files`(optional).
- 응답(blocking): `{task_id, workflow_run_id, data:{id, workflow_id, status(succeeded|failed|running|stopped|partial-succeeded|paused), outputs, error, elapsed_time, total_tokens, total_steps, created_at, finished_at}}`. streaming은 `text/event-stream` SSE.
- Dify **DSL**: 워크플로우를 YAML로 export/import — 앱 메타데이터 + dependencies + variables/features + ReactFlow 유사 `graph{nodes, edges}`. Import는 Dify 콘솔의 "Import DSL" 또는 API(버전에 따라 상이 — **가정: 안정적 공개 API로 명시 문서화되지 않은 릴리즈 존재, 도입 시 대상 Dify 버전에서 재검증 필요**).

**단계적 통합 모드 (택1 또는 병행, 로드맵 P5/P6 — §8):**

| 모드 | 설명 | 통합 대상 | 리스크 |
|---|---|---|---|
| **A. Import 모드 (design-time)** | Dify Studio에서 설계한 워크플로우를 **DSL YAML로 export** → SeCMP가 **`dify_dsl_adapter`** 로 파싱해 내부 `definition_json`(nodes/edges)으로 변환·저장. 실행은 SeCMP 자체 엔진이 수행 | 노드 매핑표(아래) | DSL 스키마가 Dify 버전마다 변경 — 버전 핀 필요 |
| **B. Delegate 모드 (execution-time)** | 특정 워크플로우를 **Dify 인스턴스에 위임 실행** — SeCMP `llm`/`agent` 노드 대신 단일 `dify_delegate` 노드가 `POST {DIFY_HOST}/v1/workflows/run`을 호출, `workflow_run_id`를 SeCMP `workflow_node_runs.output_json`에 기록해 감사 연속성 유지 | 신규 노드 타입 `dify_delegate` | 이중 실행엔진 운영 부담, Dify 인스턴스 가용성 의존 |
| **C. Round-trip 모드** | A+B 결합 — Dify에서 설계·SeCMP에서 거버넌스(HITL/감사)를 감싸 실행, 결과를 다시 Dify DSL 버전 태그로 기록 | 위 둘의 조합 | 복잡도 최고, 3차 로드맵(P6+)에서만 고려 |

**노드 매핑표 (Dify DSL 노드 → SeCMP 내부 노드, 모드 A 기준)**:

| Dify DSL 노드 | SeCMP 내부 노드 | 매핑 방식 |
|---|---|---|
| `start` | `trigger`(manual) | 1:1 |
| `llm` | `llm` | provider를 Claude/Ollama로 재매핑, prompt template 이식 |
| `knowledge-retrieval` | `agent`(RAG 에이전트 capability 검색) | F-RAG 컬렉션 ID로 재바인딩 |
| `if-else` | `condition` | 조건식 그대로 이식(표현식 문법 차이 어댑터에서 변환) |
| `http-request` | `agent`(tool-proxy capability) 또는 신규 `http` 노드(§8 P5 확장) | Addon ZIP tool-proxy 패턴(Flow-Template 준용)으로 위임 |
| `tool`(플러그인) | `agent`(Registry capability 검색) | Dify 플러그인 ↔ SeCMP Addon Agent 1:1 대응 불가 시 수동 매핑 필요 — `가정:` 전량 자동화 불가 |
| `code` | 미지원(1차) | **로드맵 P6 검토** — 샌드박스 코드 실행은 보안 리스크로 유보 |
| `answer`/`end` | `notify` | 1:1 |

**데이터 모델 확장 (도입 시)**:
```sql
ALTER TABLE workflows ADD COLUMN dify_dsl_source TEXT NULL;   -- 원본 DSL YAML 보관(round-trip 대비)
ALTER TABLE workflows ADD COLUMN dify_dsl_version TEXT NULL;  -- 임포트 시점 Dify 버전 핀
```
- Dify 연결정보는 `tbl_settings`에 암호화 저장(`dify_host_url`, `dify_api_key` — 앱별 키이므로 워크플로우 단위 매핑 테이블 별도 검토).

**도입 순서 제안**: (1) 모드 A(Import)부터 — 리스크 최저, 설계 자산 재사용 가치가 큼. (2) 사용 패턴을 보고 모드 B(Delegate)는 "Dify에 이미 존재하는 대형 플로우"를 재구현 없이 재사용하려는 조직에 한해 옵션 제공. (3) 모드 C는 로드맵 후반(P6+)에서 수요 확인 후 재검토.

**전제 조건**: 실제 도입 전 (a) 대상 조직이 사용할 Dify 버전 고정 및 DSL 스키마 재검증, (b) Dify 라이선스(코어 OSS + 상용 옵션) 조건 확인, (c) 온프렘/폐쇄망 환경에서 Dify 자체도 self-host 필요(외부 SaaS Dify 사용 시 데이터 경계 정책 위반 가능 — §7.6 참조).

### 7.3 Marketplace 원격 레지스트리 (F-MP 확장) — `.env.*` 기반 온프렘/SaaS 접속 가이드

**목표**: SeCuardian(또는 SeCMP를 설치한 각 인스턴스)이 **클라이언트**로서 별도 운영되는 "Marketplace-host" 서버(사내 공유 레지스트리 또는 SaaS 제공 서버)에 접속해, 로컬 업로드 없이 **원격 카탈로그를 검색·설치**할 수 있게 한다. 기존 로컬 `upload` 파이프라인은 그대로 유지하고, 원격 자산은 다운로드 후 **동일한 hot-deploy 파이프라인**(SQL 적용→`load_router()`→config upsert)에 태운다.

#### 7.3.1 `.env.*` 설정 키 (제안 스키마)

```dotenv
# --- Marketplace Remote Registry ---
MARKETPLACE_REMOTE_ENABLED=false           # true 시 원격 카탈로그 병합 조회
MARKETPLACE_HOST_MODE=onprem               # onprem | saas
MARKETPLACE_HOST_URL=https://marketplace.internal.example.com   # onprem: 사내 URL / saas: 제공사 URL
MARKETPLACE_TENANT_ID=                     # 멀티테넌시 SaaS 사용 시 테넌트 식별자
MARKETPLACE_API_KEY=                       # Bearer 인증 (시크릿 매니저 권장, .env 직접 저장은 dev/local 한정)
MARKETPLACE_TLS_VERIFY=true                # onprem 사설 CA 사용 시 false 또는 CA 번들 경로 지정
MARKETPLACE_TLS_CA_BUNDLE=                 # 사설 CA 사용 시 경로
MARKETPLACE_SYNC_INTERVAL_SEC=3600         # 카탈로그 캐시 갱신 주기
MARKETPLACE_INSTALL_VERIFY_CHECKSUM=true   # 다운로드 ZIP SHA256 검증 강제
MARKETPLACE_INSTALL_REQUIRE_SIGNATURE=false # true 시 GPG 서명 검증 강제(엔터프라이즈 옵션)
```

- **환경별 기본값 원칙(하이브리드)**: `local`/폐쇄망 프로파일 = `MARKETPLACE_REMOTE_ENABLED=false`(기본 오프). `dev`/`staging`/`prod`는 `.env.example`에 SaaS/온프렘 값 예시를 **주석 포함**으로 제공하되 실값은 비워둠 — 배포 담당자가 채움.

#### 7.3.2 접속 모드

| 모드 | 대상 | 인증 | 네트워크 |
|---|---|---|---|
| **온프렘(사내 공유)** | 조직 내부에 별도 배포된 Marketplace-host(예: SeCMP 자체를 "레지스트리 전용" 모드로 한 대 더 운영) | 사설 CA mTLS 또는 사내 API 키 | 폐쇄망 내부 통신, 외부 egress 불필요 |
| **SaaS(제공사 호스팅)** | 외부 SaaS 카탈로그 서버 | HTTPS + `MARKETPLACE_API_KEY`(Bearer) | 외부 egress 필요 — 폐쇄망은 이 모드 비활성 유지 |
| **에어갭(오프라인)** | 완전 격리망 | 해당 없음(원격 비활성) | Marketplace-host에서 ZIP을 수동 다운로드 후 기존 로컬 `upload`로 반입(§3 하지 않을 것: 원격 자동 동기화 없음) |

#### 7.3.3 신규 라우터 계약 (제안)

`app/routers/router_marketplace_remote.py` (`/api/marketplace-remote`):
```
GET  /api/marketplace-remote/ping            # 연결성/인증 확인 (헬스체크)
GET  /api/marketplace-remote/catalog         # 원격 카탈로그 목록(캐시, SYNC_INTERVAL 준수)
GET  /api/marketplace-remote/catalog/{key}   # 원격 자산 상세
POST /api/marketplace-remote/install/{key}   # 다운로드→체크섬/서명 검증→기존 upload 파이프라인 재사용→설치
```
- `install`은 내부적으로 원격 ZIP을 받아 **로컬 `router_addon_agent.py`의 upload 로직을 함수 재사용**(별도 재구현 금지 — 준용 원칙).
- 실패 시 부분 설치 롤백(트랜잭션 경계는 기존 upload와 동일).

#### 7.3.4 운영 가이드 요약 (문서화 대상 — 구현 시 `docs/marketplace-remote.md`로 확장)
1. Marketplace-host 유형 결정(온프렘 자체 운영 vs SaaS 구독).
2. `.env.{dev,staging,prod}`에 `MARKETPLACE_HOST_MODE`/`MARKETPLACE_HOST_URL`/`MARKETPLACE_API_KEY` 설정.
3. `MARKETPLACE_TLS_VERIFY`/`CA_BUNDLE`로 사설 인증서 대응(온프렘 필수 검토).
4. `/api/marketplace-remote/ping`으로 연결 검증 → Marketplace 화면에 원격 카탈로그 노출.
5. 설치 시 체크섬(기본) + 서명(엔터프라이즈 옵션) 검증 통과해야 hot-deploy 진행.
6. 폐쇄망은 `MARKETPLACE_REMOTE_ENABLED=false` 유지, 필요 자산은 수동 반입 절차(에어갭 모드) 사용.

### 7.4 멀티테넌시 격리 (`.env.*` 기반 확장형)

**목표**: 1차 출시는 **단일 테넌트(off)** 를 기본으로 하되, `.env.*` 설정만으로 **네임스페이스 격리 → 물리 격리**까지 재구성 코드 변경 없이 확장 가능하게 설계.

```dotenv
# --- Multi-Tenancy ---
TENANT_ISOLATION_LEVEL=off                 # off | namespace | physical
TENANT_DB_STRATEGY=shared                  # shared(단일 DB, tenant_id 컬럼) | schema-per-tenant | db-per-tenant
TENANT_VECTOR_STRATEGY=shared              # shared(단일 컬렉션+메타필터) | namespace-per-tenant | collection-per-tenant
TENANT_DEFAULT_ID=default                  # off 모드일 때 사용할 고정 테넌트 식별자
```

| `TENANT_ISOLATION_LEVEL` | DB | 벡터DB | 적합 대상 |
|---|---|---|---|
| `off`(기본) | 단일 스키마, 테넌트 개념 없음 | 단일 컬렉션 | 단일 조직 온프렘 배포 |
| `namespace` | 단일 DB, `tenant_id` 컬럼 + (PostgreSQL) Row-Level Security | 벡터 컬렉션 내 `tenant_id` 메타필터 | SaaS 초기, 다부서 공유 |
| `physical` | 스키마 또는 DB 인스턴스 분리(`schema-per-tenant`/`db-per-tenant`) | 테넌트별 컬렉션/인스턴스 분리 | 강한 규제·고객사별 물리 분리 요구 |

- 적용 지점: 모든 신규 테이블(`workflows`, `rag_collections`, `marketplace_*`, `guardrails_*`)에 **처음부터 `tenant_id` 컬럼을 포함**(off 모드에서는 `TENANT_DEFAULT_ID` 고정값) — 이후 namespace/physical 전환 시 스키마 변경 최소화.
- **로드맵**: 1차(P1~P4)는 `off` 검증, `namespace`는 P5에서 구현·검증, `physical`은 엔터프라이즈 옵션으로 P5 이후 요구 시 착수(§8).

### 7.5 RAG/Vector (F-RAG)

- **벡터DB 전략(리서치 근거)**: **pgvector 1차 기본**(온프렘·기존 PostgreSQL 재사용·저운영), **Qdrant 확장**(1M~20M·메타필터·하이브리드), Milvus(20M+·후반). 진화 경로: pgvector → Qdrant/Weaviate → Milvus/managed.
- **하이브리드 검색**: BM25(sparse) ∥ dense 병렬 → **RRF(k=60)** 융합 → 리랭크(2차 정밀). 식별자성 도메인은 sparse 가중↑. 문서유형별 청킹 정책.
- **데이터 경계(온프렘 보안)**: 문서원본 저장소 / 임베딩 파이프라인 / 벡터DB / 추론 계층 분리. 민감 vs 일반 문서 = 별도 컬렉션·네임스페이스·테넌트(§7.4 연계). ingest·query 양경로 감사로그. 외부 LLM에는 요약만 전송, 원본은 내부 검색 계층 유지. 원본 삭제 시 벡터+캐시 동시 파기.
- **eval**: Recall@10 / NDCG@10 / p95 지연 기준선, 임베딩 버전 고정, dual-write/shadow-query 마이그레이션 검증.

### 7.6 Marketplace (F-MP)

- 기존 자산 재사용: `router_addon_agent.py`의 `upload`/`scaffold`/`toggle`/`delete`/`export`/`export-standalone`, `agent-registry`(A2A/MCP), `capabilities` 인덱스.
- 신규: **카탈로그**(자산 메타·버전·카테고리·거버넌스·필요 env·리뷰), **설치 트랜잭션**(upload 파이프라인 래핑 + 롤백), **버전관리**(meta.version + min_platform_version, 1차 단일 활성), **원격 레지스트리**(§7.3). 자산 유형: `agent` / `workflow` / `rag-pipeline` / `tool-proxy connector`.
- 설치 = 기존 hot-deploy 파이프라인(SQL→`load_router()`→config upsert→OpenAPI 캐시버스트) — 로컬/원격 공통.

### 7.7 Playground (F-PG)

- 프롬프트/모델/에이전트/RAG 컬렉션 조합 대화형 실험, A/B 비교(응답·비용·지연·인용), eval 실행. 승격 경로: Playground → Workflow 노드 / Marketplace 게시.

### 7.8 Guardrails 내장 에이전트 (F-GRD) — 상세 확정 (v0.3, wise-Guardrails 전수 분석 기반)

> 근거: `/Users/wise/Developer/wise-Guardrails` 7개 서비스(`Guardrails-Service` 코어+`scripts/`, `Detection-Engine`, `Policy-Engine`, `Audit-Service`, `Admin`, `Admin-Web`, `Server`) 전수 코드 분석. 아래 스펙은 **연구 근거가 아니라 실제 소스코드를 읽고 확정한 계약**이다.

#### 7.8.0 ⚠ Critical Finding — 반드시 먼저 읽을 것

**wise-Guardrails가 시딩한 ~9,371개 규칙 중 98.6%(`patternType: classifier`)는 런타임 판정기가 없다.** `Guardrails-Service-Detection-Engine/src/detectors/bootstrap.py`는 `global` 도메인의 정규식 탐지기 13종(`register_global_privacy()`)만 등록하고, `manufacturing-food` 등 25개 업종 도메인용 `register_manufacturing_food()` 등은 `try/except ImportError: return`으로 조용히 스킵되는 **미구현 스텁**이다. 즉:
- **실제로 동작**: `global` 도메인의 PII/신용정보 정규식 탐지 13종(주민번호, SSN, 마이넘버, 여권, 이메일, 전화(KR/US), 카드번호+Luhn, IBAN, API 키, 운전면허(KR), 사업자등록번호(KR), IPv4).
- **데이터로만 존재, 판정 안 됨**: 25개 업종(`manufacturing-*`, `finance-*`, `healthcare-*`, `public-administration`, `arts-recreation` 등)의 컴플라이언스/안전/사기/IP/환각 규칙 약 9,116개.

**본 PRD의 결정(권고, 사용자 확인 필요 시 재조정 가능)**: **F-GRD 1차 출시 범위를 `global`(PII) 도메인 실판정으로 한정**하고, 25개 업종 규칙셋은 Guardrails 화면에 **"카탈로그 — 판정 로드맵"** 으로 명시 구분해 노출한다. "적용됨"으로 오인되지 않도록 UI/문서에서 실판정 도메인과 카탈로그 전용 도메인을 시각적으로 분리한다. 업종 판정기 자체 구현은 wise-Guardrails 프로젝트의 별도 로드맵이며 SeCMP 책임 범위 밖이다.

#### 7.8.1 아키텍처 — 통합 지점은 MCP Server 1곳

```
SeCMP (FastAPI)                         wise-Guardrails
router_guardrails.py  ──HTTP──▶  MCP Server :8080 (ApiKeyGuard, x-api-key)
  (agent_guardrail_config 소유)         │  orchestrates (Promise.all, 3-5s timeout, 장애 시 자동 allow-degrade)
                                          ├─ Policy Engine   :8082(policy)/:8085(redact)  [Postgres/SQLite + Redis 300s 캐시]
                                          ├─ Detection Engine :8081  [Python/FastAPI, stateless, regex 13종]
                                          └─ Audit Service    :8083  [decision_events, textHash만 저장·원문 미저장]
                (별도) Admin API :8084 + Admin-Web :3001 — 규칙 CRUD/CSV 임포트, SeCMP는 호출 안 함(운영자 전용 콘솔)
```
- **SeCMP는 MCP Server(:8080)만 호출한다.** Server가 Policy+Detection을 병렬 호출·병합하고, 다운스트림 장애 시에도 절대 하드 실패하지 않고 `decision:'allow', riskScore:0`으로 **자동 degrade**한다(§7.8.6 리스크로 별도 기재).
- 인증: `MCP_HTTP_AUTH=required` 시 헤더 `x-api-key: <GUARDRAILS_API_KEY>`(단일 공유 정적 키, 테넌트별 키 없음 — §6 리스크).

#### 7.8.2 API 계약 (실측, `POST /mcp/tools/<name>`)

**`validate_input` / `validate_output`** — 요청:
```json
{ "text": "<검사 대상 텍스트>", "domain": "global", "locale": "ko-KR",
  "sessionId": "<secmp-session-id>", "tenantId": "<secmp-tenant-id>" }
```
응답(`ValidateResponse`):
```json
{
  "decision": "allow|warn|redact|sanitize|block|escalate",
  "riskScore": 0.0, "matchedRules": ["PRIV_ID_IN_001"], "categories": ["pii.national_id_kr"],
  "normalizedText": "...", "redactedText": "...", "message": "...",
  "policyVersion": "1.0.0", "decisionId": "uuid", "evaluatedDomains": ["global"],
  "latencyMs": 42
}
```
- `block`/`escalate` → 콘텐츠를 사용자/LLM에 전달하지 않고 리터럴 `"[BLOCKED]"` 대체. `redact`/`sanitize` → `redactedText` 사용.
- 동기 HTTP POST, sub-second(정규식 경로 <50ms 자체 문서 기준). 클라이언트 타임아웃 권장 **3~5초**(Policy+Detection 왕복 커버).

**`explain_decision`** — 요청 `{ "decisionId": "..." }` → Audit Service `decision_events` 1건 반환(원문 없음, `textHash`만).

**규칙 카탈로그 조회** — MCP 전용 도구 없음. `POST /mcp/tools/health_check` → `{ enabledDomains, enabledLocales, transport }`로 **배포 시점에 활성화된 도메인 목록**만 확인 가능(도메인별 규칙 상세는 Policy Engine `GET :8082/policies/bundle?domains=...`을 직접 호출해야 하나, 이는 MCP 표준 경로 밖 — §7.8.3에서 SeCMP 측 카탈로그 캐시로 대체 설계).

#### 7.8.3 데이터 모델 (SeCMP 자체 소유 — 신규 테이블)

wise-Guardrails에는 `agent`/`tenant` 개념이 없고, 도메인 선택은 **호출자가 요청 바디에 넣는 자기신고 값**이며 서버 측 인가 검증이 없다(`api_keys.allowed_domains` 컬럼은 존재하나 코드 어디서도 참조되지 않음 — grep 확인). 따라서 **도메인 스코프 소유권은 SeCMP가 가져야 한다**:

```sql
guardrails_domain_catalog(   -- 배포된 Guardrails Service의 도메인 카탈로그 캐시(주기 동기화)
  domain_key, display_name, status ENUM('functional','catalog_only'),  -- 'functional'=global만, 나머지='catalog_only'
  rule_count, last_synced_at)

agent_guardrail_config(      -- 에이전트(agent_key) 단위 도메인 활성화 — 요구사항 3번의 핵심 구현체
  agent_key REFERENCES tbl_agent_config(agent_key),
  domain_key REFERENCES guardrails_domain_catalog(domain_key),
  enabled BOOLEAN DEFAULT false,
  io_scope ENUM('input','output','both') DEFAULT 'both',
  updated_by, updated_at,
  PRIMARY KEY(agent_key, domain_key))

guardrails_decision_log(     -- SeCMP 측 이중 감사(Audit Service TTL 미구현·메모리 링버퍼 유실 리스크 완화, §6)
  id, agent_key, decision_id,          -- Guardrails decisionId 참조
  domain_key, decision, risk_score, matched_rule_count,
  tenant_id, session_id, created_at)
```
- **원칙**: Orchestrator/`call_api` 호출 시 SeCMP는 사용자·에이전트 입력의 `domain` 필드를 신뢰하지 않고, **`agent_guardrail_config`에서 해당 `agent_key`에 활성화된 도메인만**을 조합해 Guardrails에 요청한다. 이것이 "에이전트별 규칙셋 적용 on/off" 요구사항(사용자 지시 3번)의 실제 구현 지점 — **업스트림이 강제하지 않으므로 SeCMP가 강제한다.**
- `guardrails_domain_catalog.status`는 §7.8.0 결정에 따라 `global`만 `functional`, 나머지 25종은 `catalog_only`로 시딩.

#### 7.8.4 검사 시점(Wiring Point) — Orchestrator 통합

- **위치**: `app/agents/orchestrator.py`의 `_exec_api_call()` 직전(입력) / 직후(출력) 훅으로 삽입 — 기존 `call_api` 인프로세스 자기호출 경로를 가로채는 지점. Orchestrator 코드 자체는 무변경 원칙(§3)을 지키기 위해, 신규 `app/agents/guardrails_gate.py`가 `orchestrator._exec_api_call` 앞뒤를 감싸는 **얇은 래퍼**로 구현(데코레이터 또는 명시적 호출 삽입 — 구현 시 SeCuardian 코어 변경 최소화 방식 선택).
- **워크플로우(F-WF) 연계**: `agent`/`hitl` 노드 진입 전, `agent_guardrail_config`에 해당 노드가 참조하는 `agent_key`의 활성 도메인이 있으면 동일 게이트 통과. `block`/`escalate` 판정 시 워크플로우 노드는 `failed` 처리 후 사유를 `workflow_node_runs.error`에 기록.
- **성능 영향(§5 KPI 연동)**: Guardrails 왕복(<50ms 정규식 경로 + 네트워크)이 §5의 "에이전트 인지 ≤5초"·"노드 성공률 ≥99%" KPI에 **추가 지연으로 가산**됨을 명시. `global` 도메인만 활성화된 1차 범위에서는 무시 가능한 수준(수십 ms)으로 추정하나, 실측은 P4 verify에서 확인(§8.3).

#### 7.8.5 API 라우터 계약 (SeCMP 측, Path A 준용)

`app/routers/router_guardrails.py` (`/api/guardrails`):
```
GET    /api/guardrails/domains                    # guardrails_domain_catalog 목록(functional/catalog_only 구분)
GET    /api/guardrails/agents/{agent_key}/config   # 해당 에이전트의 활성 도메인 목록
PUT    /api/guardrails/agents/{agent_key}/config   # 도메인별 on/off 토글 (require_role admin/supervisor)
POST   /api/guardrails/test                        # Playground 연계 — 임의 텍스트를 즉시 validate_input에 시험
GET    /api/guardrails/decisions/{decision_id}      # explain_decision 프록시
GET    /api/guardrails/decisions?agent_key=&limit=  # guardrails_decision_log 조회(SeCMP 자체 이중기록 — 업스트림 미지원 필터 보완)
```
- `tbl_agent_config` 시드(`agent_key='guardrails'`) 등록은 §7.1 패턴과 동일 — AI Assistant 카탈로그에 자동 노출.

#### 7.8.6 요구사항 대응 매핑 (사용자 지시 3건 최종 확인)
1. **"거버넌스 관점 Guardrails 참고, 내장 에이전트 추가"** → §7.8.1~7.8.5, `router_guardrails.py` + MCP Server 연동으로 충족.
2. **"`Guardrails-Service/scripts/` 도메인별 규칙셋 사용 가능하게"** → `guardrails_domain_catalog`가 카탈로그를 노출하되, **§7.8.0의 실판정 범위 한정을 함께 고지** — 사용 가능 = "조회·선택 가능"이지 25종 전체가 "판정 가능"은 아님을 제품적으로 명확히 함(허위 기능 표기 방지).
3. **"도메인별 적용여부를 에이전트 단위로 토글"** → `agent_guardrail_config` 테이블 + `PUT /api/guardrails/agents/{agent_key}/config`로 정확히 충족. 업스트림이 인가를 강제하지 않으므로 **SeCMP가 유일한 강제 지점**이라는 점이 설계의 핵심.

### 7.9 비기능 요구사항 (NFR)

| 범주 | 요구 |
|---|---|
| **보안(OWASP LLM Top10)** | LLM01(입력 검증·툴 allow-list) · LLM02(출력 sanitize) · LLM06(ABAC·필드 마스킹·검색범위 제한) · LLM07(scoped vault 크리덴셜) · LLM08(write/delete/external HITL) · LLM09(인용·신뢰도·검토) · LLM05(버전 핀·이미지/의존성 스캔·SBOM). 부록 C 스코어카드로 관리 |
| **성능** | RAG p95 ≤250ms(중규모), 에이전트 인지 ≤5초, 워크플로우 노드 성공률 ≥99% |
| **가용성/복원력** | 노드 retry≤3, dead-letter/idempotency, 무중단 배포 |
| **관측성** | Prometheus `/metrics`(준용), 실행 트레이스, 감사로그(tenant/user/prompt·model version) |
| **규제 — 확정: govtech 1차, security 특화** | `domains/govtech.yaml` 오버레이 그대로 준용(근거: wise-dev-standard). 핵심: **N2SF 망분리 등급(C/S/O)** 기반 데이터 분리, **개인정보보호법(PIPA)** — 주민 PII(주민번호/주소) 최소수집·마스킹·접근로그, **전자정부법/eGovFrame v4.3** 정합 검토(직접 이식은 아니나 공공 SI 조달 시 참조), **CSAP(2026 완화, N2SF 등급제 전환)** 인증 공공클라우드 배포 고려, **웹접근성 KWCAG 2.2**(4원칙 33항목) 필수. **Security 특화 연동(v0.3 확정)**: wise-Guardrails에 `public-administration`(공공행정) 규칙셋은 존재하나 전용 `govtech-security` 규칙셋은 없고, **모든 업종 규칙셋이 판정기 없는 데이터 상태**(§7.8.0)이므로 1차는 **PIPA 대응 = Guardrails `global` 도메인의 KR 주민번호(RRN)·사업자등록번호·운전면허 정규식 탐지 3종**으로 실질 커버. N2SF 등급(C/S/O)은 §7.4 멀티테넌시 `physical` 격리 수준과 연계해 향후 매핑(로드맵). |
| **접근성** | KWCAG 2.2 — 워크플로우 캔버스 키보드 대체 편집기 (govtech 확정에 따라 하드 요구사항으로 격상) |
| **인증/인가** | 기존 JWT + role(user/admin/supervisor) + 외부 IAM(Keycloak/Logto/Vault) 준용 |
| **멀티테넌시** | §7.4 `.env.*` 기반 off/namespace/physical |

### 7.10 환경 분리 (F-ENV)

- `.env.local`(개발자 로컬, sqlite) / `.env.dev` / `.env.staging` / `.env.prod`.
- **하이브리드 정책**: 로컬/폐쇄망은 온프렘(self-host LLM + pgvector) 우선, dev/staging/prod는 **SaaS(외부 LLM API·관리형 Vector) 설정 포함 가능**.
- `.env.example` 에 온프렘·SaaS 양쪽 키를 주석과 함께 제공. 시크릿은 시크릿 매니저 주입, 노드 config에 평문 금지(LLM07).
- LLM 설정 우선순위 준용: `os.environ > .env.* > tbl_settings > config defaults`.
- **§7.3(Marketplace 원격)·§7.4(멀티테넌시) 신규 키를 동일 `.env.example`에 통합 관리.**

#### 7.10.1 프론트엔드 바인딩 (F-WEB 연계)

- `.env.*` 에 `FRONTEND_HOST`(기본 `0.0.0.0`)·`FRONTEND_PORT`(기본 `5173`) 를 둔다. `front/vite.config.ts` 가 이 값을 읽어 dev 서버 host/port·프록시를 구성(하드코딩 제거).
- **중복 방지 원칙**: dev 프록시 대상은 `APP_PORT` 에서 파생(`http://localhost:${APP_PORT}`)한다. `VITE_API_TARGET` 은 **선택적 오버라이드**로만 사용(교차 호스트/도메인 배포 시). 평상시 `.env` 에 두지 않아 `APP_PORT` 와의 값 중복을 없앤다.
- compose `web`(profiles:[web]) 프로덕션 이미지는 `FRONTEND_PORT` 로 매핑, 빌드 인자 `VITE_API_TARGET` 로 백엔드 주소 주입.

#### 7.10.2 Ollama 추론 런타임 — CPU / GPU / MLX (SeCuardian 준용)

폐쇄망 LLM 폴백(Ollama)의 가속 장치를 `.env.*` `OLLAMA_RUNTIME` 로 선택한다:

| `OLLAMA_RUNTIME` | 대상 | compose 처리 | 비고 |
|---|---|---|---|
| `cpu`(기본) | 전 플랫폼 | `docker-compose.yml` 의 `ollama` 서비스(CPU) | 이식성 최고, 성능 최저 |
| `gpu` | Linux + NVIDIA(+Container Toolkit) | `docker-compose.gpu.yml` 오버레이 병합 → `deploy.resources.reservations.devices`(nvidia, `OLLAMA_GPU_COUNT`), `NVIDIA_VISIBLE_DEVICES` | macOS/Windows Docker Desktop 은 GPU passthrough 미지원 |
| `mlx` | macOS(Apple Silicon) Metal/MLX | **Docker ollama 미기동**(리눅스 VM 은 Metal 접근 불가) — 호스트 네이티브 Ollama/MLX 구동, 앱은 `OLLAMA_BASE_URL=http://host.docker.internal:${OLLAMA_PORT}` 로 접속 | 최고 성능(Apple GPU) |

- 관련 키: `OLLAMA_ENABLED`(기본 true), `OLLAMA_PORT`(11434), `OLLAMA_RUNTIME`(cpu|gpu|mlx), `OLLAMA_GPU_COUNT`(all|정수), `NVIDIA_VISIBLE_DEVICES`(all), `OLLAMA_KEEP_ALIVE`, `OLLAMA_WARMUP_ENABLED`/`OLLAMA_WARMUP_INTERVAL`.
- gpu 오버레이 사용: `COMPOSE_FILE=docker-compose.yml:docker-compose.override.yml:docker-compose.gpu.yml` (staging/prod 는 override 제외). Makefile 이 `OLLAMA_RUNTIME=gpu` 감지 시 자동 병합.
- 컨테이너 내부 앱은 `OLLAMA_BASE_URL` 을 서비스명(`http://ollama:11434`) 또는 mlx 시 `host.docker.internal` 로 구성(§7.10 하이브리드).

### 7.11 웹 포털 + Setup Wizard (F-WEB / F-SETUP) — SeCuardian 프론트·F6 준용

**프론트 스택**(§4 확정): React 19 + Vite 7 + React-Router 7 + TanStack Query 5 + Tailwind 4 SPA(`front/`). dev 프록시(`/api`,`/health` → 백엔드 :8000). `make dev-fe`/`dev-be` 분리 기동.

- **레이아웃**: 좌측 nav 그룹(홈: 대시보드 / 내장 에이전트: 마켓플레이스·워크플로우·RAG + 플레이그라운드·가드레일[P1 disabled 배지]) + 헤더 역할 스위처(dev: `X-User`/`X-Role`/`X-Tenant-Id` 헤더 주입, 실 JWT/IAM 은 F-GOV 대체).
- **화면**: 대시보드(`/api/agents` 카탈로그+헬스), 마켓플레이스(카탈로그·등록·설치/해제), 워크플로우(목록·**폼 기반 노드/엣지 편집기**·실행), 워크플로우 상세(상태·노드 타임라인·HITL 승인/거부·SSE), RAG(컬렉션·수집·하이브리드 검색).
- **접근성(KWCAG 2.2, govtech 하드 요구)**: 워크플로우 캔버스 대신 **키보드 전용 폼/리스트 편집기**를 1차 제공(React Flow 캔버스는 E3 확장). 포커스 가시성, `aria-label`, 스킵 링크, `role="alert"` 오류.

**Setup Wizard(F-SETUP, SeCuardian F6 준용)** — `router_setup.py`(`/api/setup`, **인증 불필요**, setup 완료 전 상태):
```
GET  /api/setup/status        # {has_supervisor, completed}
POST /api/setup/supervisor    # 최초 supervisor 계정(이미 존재 시 409)
PUT  /api/setup/llm-provider   # LLM 모델/Ollama/fallback → tbl_settings 저장
POST /api/setup/admin          # (선택) admin 계정
POST /api/setup/user           # (선택) user/viewer 계정
POST /api/setup/complete       # tbl_settings.setup_completed = true
```
- **게이트**: 프론트 로딩 시 `GET /api/setup/status` → `completed=false` 면 `/setup` 으로 유도, 완료 후 본 포털 진입.
- **신규 테이블(SeCMP 자체 소유)**:
  ```sql
  tbl_users(user_id PK, username, email, password(hash), role, tenant_id, created_at)   -- role: supervisor|admin|user|viewer
  tbl_settings(key PK, value, description, updated_at)                                    -- setup_completed, LLM provider 등
  ```
- 비밀번호는 해시 저장(평문 금지). 최초 supervisor 는 1회만 생성 가능.

### 7.11.1 AI Assistant / Orchestrator (F-AI) — 필수 내장 + 공유 재사용

- **필수 내장**: `tbl_agent_config` 에 `assistant`(is_required=true) 시드 → `/api/agents` 카탈로그·좌측 nav 에 항상 노출. 비활성 불가(필수).
- **Orchestrator**(`app/agents/orchestrator.py`, SeCuardian 준용 클론): `classify→gather→synthesize`, **in-proc `call_api`(httpx ASGITransport 자기호출)** 로 설치/내장 에이전트 REST 를 도구 실행. `router_agent`(`/api/agent/chat`, `/chat/stream` SSE).
- **모델 설정**: `orchestrator_model`·`domain_agent_model`(우선순위 `os.environ > tbl_settings > config`). Setup Wizard/`/api/settings` 로 런타임 변경.
- **공유 LLM(`app/services/llm.py`)**: `generate(prompt, system)` — Claude(anthropic 선택) → Ollama 폴백 → degrade. **마켓플레이스·RAG·워크플로우가 공유 소비**한다:
  - **워크플로우 `llm` 노드**: 스텁 → 공유 LLM 실호출(1차 소비처). LLM 미구성 시 노드는 degrade 텍스트로 완료(무중단).
  - RAG(응답 합성)·Playground(실험) 는 동일 `generate`/Assistant 를 후속 사용(로드맵).
- **오프라인/CI**: Claude·Ollama 모두 불가 시 degrade — 결정적 동작(시험 안전).

### 7.12 운영 명령(F-OPS) — Makefile 환경별 ops + DB 초기화 (SeCuardian 준용)

| 범주 | 타겟 | 설명 |
|---|---|---|
| local | `local-all` / `local-stop` / `local-logs` / `local-status` | **pm2 프로세스 매니저 기반**(SeCuardian 준용) — BE(uvicorn)+FE(vite) 백그라운드 관리, **SQLite 자동**(Postgres 불필요), Ollama 는 옵션. `ecosystem.config.js` 사용 |
| local(대안) | `run` | honcho 포그라운드 통합 실행(web+front, Ctrl-C 종료) — pm2 미설치 환경 대안 |
| dev/staging/prod | `<env>-all` / `<env>-stop` / `<env>-logs` | docker compose 환경별 기동/중단/로그 |
| DB | `db-reset` | 데이터 삭제+스키마 재생성(`FORCE=1` 로 확인 생략) |
| DB | `seed` | 기본 설정 + 테스트 계정 삽입(`ENV=prod` 가드) |
| DB | `db-fresh` | `db-reset` + `seed` 순차 |
| front | `dev-fe` / `dev-be` | 프론트(pnpm)/백엔드(uvicorn) 개별 기동 |

- 파괴적 명령(`db-reset`/`db-fresh`)은 확인 프롬프트(FORCE 로 생략). prod 대상 `seed` 는 명시적 `ENV=prod` 필요.
- 스크립트: `scripts/db_reset.py`(drop_all+create_all+seed 내장 에이전트), `scripts/seed.py`(tbl_settings 기본값 + 비-prod 테스트 계정).
- **local 실행 모델(SeCuardian 준용)**: `ecosystem.config.js`(pm2) 로 `secmp-api`(uvicorn, `APP_PORT`)·`secmp-fe`(vite, `FRONTEND_PORT`) 를 백그라운드 관리. local 은 SQLite 라 Postgres 컨테이너 불필요. Ollama 는 `OLLAMA_RUNTIME` 에 따라 옵션(cpu=docker, mlx=네이티브). pm2 미설치 시 `make run`(honcho) 대안 안내.

---

## 8. 실행 연결 — Epic / 로드맵 / 일정·리소스

### 8.1 Epic 분해

| Epic | 범위 | 기능 |
|---|---|---|
| **E0** | 스캐폴드 · 준용 검증(코어 무변경 회귀) · 환경분리(.env.* + 멀티테넌시/원격 레지스트리 키 포함) · SQL 초기화(tenant_id 컬럼 선반영) | F-ENV |
| **E1** | Marketplace 카탈로그·상세·설치 트랜잭션·버전·심사 (upload/export 래핑) | F-MP |
| **E1.5** | Marketplace 원격 레지스트리 클라이언트(§7.3) — ping/catalog/install, 체크섬/서명 검증 | F-MP |
| **E2** | Workflow Flow Engine 코어(DAG 파서·실행기·상태머신·retry·SSE) | F-WF |
| **E3** | Workflow Designer UI(React Flow 3화면 + a11y 대체) | F-WF |
| **E3.5** | Dify DSL Import 어댑터(모드 A, §7.2.2) — *P5로 이연* | F-WF |
| **E4** | RAG 파이프라인(수집·임베딩·pgvector·BM25·RRF·리랭크·eval) | F-RAG |
| **E5** | Playground(실험·A/B·eval) | F-PG |
| **E6** | 거버넌스·보안(OWASP 통제·HITL 전면·감사로그·시크릿·SBOM) | F-GOV |
| **E7** | 하드닝·엔터프라이즈(Qdrant 확장·`namespace` 멀티테넌시 구현·서명/스캔·loop/cron 검토) | NFR |
| **E8** | **Guardrails Agent 전체 구현**(§7.8) — `router_guardrails.py`, `agent_guardrail_config`/`guardrails_domain_catalog`/`guardrails_decision_log` 3테이블, Orchestrator 훅(`guardrails_gate.py`), Playground `/api/guardrails/test` 연계, `global` 도메인 실판정 + 25종 카탈로그 표시 | F-GRD |

### 8.2 로드맵 (Phase별 · 일정 · 리소스)

> 일정은 **주(week) 단위**, 리소스는 **역할별 투입(FTE)**. `가정:` 표준 5~6인 스쿼드, 병렬 진행 전제. 실제 산정은 스프린트 계획에서 재보정. **v0.2 변경**: 원격 레지스트리(E1.5)를 P1에 흡수, 멀티테넌시 `namespace` 구현을 P5로 이동(1차는 스키마 선반영만), Dify 어댑터(E3.5)·Guardrails 상세(E8 본편)를 P5/v0.3으로 이연.

| Phase | 기간 | 주요 산출물 | 핵심 리소스(FTE) | 종료 기준(Exit) |
|---|---|---|---|---|
| **P0 기반** | 2주 | 리포 스캐폴드, 코어 무변경 회귀 통과, `.env.*`/`.env.example`(멀티테넌시·원격레지스트리 키 포함), DDL/seed(`tenant_id` 선반영) | TL 1, BE 1 | SeCuardian 코어 회귀 100% 통과 + 신규 라우터 헬스체크 |
| **P1 Marketplace MVP** | 5주(+1주) | 카탈로그·설치 트랜잭션·버전·심사 + **원격 레지스트리 클라이언트**(ping/catalog/install) | BE 2, FE 1, TL 0.5 | 마켓에서 로컬+원격 설치→AI Assistant 인지 ≤5초, 성공률 ≥98%, ping 성공률 ≥99.5% |
| **P2 Workflow + Guardrails** | 7주(+1주, Guardrails 병렬 투입) | Flow Engine 코어(E2) + Designer(E3) **+ Guardrails Agent 전체(E8)**: 라우터·3테이블·Orchestrator 훅·`global` 도메인 실판정·카탈로그 UI | BE 2.5(+0.5), FE 1.5, TL 0.5, Sec 0.5(신규) | 7노드 DAG 실행·HITL·SSE E2E 노드 성공률 ≥99%, **Guardrails `global` 도메인 PII 13종 검사 E2E(≤50ms), 에이전트별 on/off 토글 동작 확인** |
| **P3 RAG/Vector** | 5주 | 수집·임베딩·pgvector·BM25·RRF·리랭크·eval, 데이터 경계 | BE 1.5, RAG/ML 1, FE 1 | 하이브리드 Recall@10 ≥0.89, p95 ≤250ms(실측 재검증) |
| **P4 Playground + 거버넌스** | 4주 | Playground(A/B·eval, `/api/guardrails/test` 연계) + OWASP 통제·HITL 전면·감사로그·시크릿, govtech-security NFR 검증(§7.9) | BE 1.5, FE 1, Sec 0.5 | OWASP 스코어카드 전항목 ≥4, write/delete/external 100% HITL, KWCAG 2.2 자동점검 통과, guardrails_decision_log 이중기록 검증 |
| **P5 하드닝/엔터프라이즈** | 5주(+1주) | Qdrant 확장·`namespace` 멀티테넌시 구현·서명/SBOM/스캔·Dify DSL Import 어댑터(E3.5)·loop/cron 검토·부하시험 | BE 2, Sec 0.5, QA 1 | 부하·보안·마이그레이션(dual-write) 검증 통과, Dify Import 파일럿 1건 성공 |

- **총 기간**: 약 **29주(≈7개월)** — v0.2 대비 Guardrails Agent 전체 구현(E8)이 P2로 편입되며 +2주.
- **팀 구성(권장)**: Tech Lead 1, Backend 2.5, Frontend 1~1.5, RAG/ML 1, Security/Compliance 0.5(P2부터 조기 투입 — Guardrails 규칙셋 검토 담당). 업종별(25종) 규칙 판정기 자체 개발은 SeCMP 범위 밖(wise-Guardrails 별도 로드맵)이므로 팀 규모에 미반영.
- **누적 인월(person-month) 추정**: `가정:` 약 **30~34 PM** (5.5~6.5인 × ~7개월, 병렬·리스크 버퍼 포함).
- **크리티컬 패스**: P0 → P2(Workflow 엔진 + Guardrails) → P4(거버넌스). RAG(P3)는 P2와 부분 병렬 가능. P5의 Dify 어댑터·namespace 멀티테넌시는 P1~P4 완료 후 착수(선행 의존).

### 8.3 마일스톤 검증(각 Phase = verify)
1. P0 → verify: 코어 회귀 스위트 + 신규 라우터 스모크.
2. P1 → verify: 설치 트랜잭션 E2E(로컬 설치/롤백/인지시간) + 원격 레지스트리 ping/catalog/install E2E(온프렘 mock 서버 대상).
3. P2 → verify: 워크플로우 E2E(트리거→노드→HITL→완료) + SSE. **+ Guardrails E2E: `global` PII 13종 각각 실제 탐지 확인, 에이전트 A(도메인 on)·B(off) 동일 입력에 결과 분기 확인, MCP Server 다운 시 SeCMP가 자동 allow-degrade를 리스크로 로깅하는지 확인.**
4. P3 → verify: RAG eval 세트(Recall/NDCG/p95) 실측.
5. P4 → verify: OWASP 스코어카드 재평가 + HITL 커버리지 + KWCAG 2.2 자동 점검 + `guardrails_decision_log` ↔ Audit Service 기록 정합성 대조.
6. P5 → verify: 부하·마이그레이션·보안 스캔 + Dify DSL Import 파일럿(실제 Dify 인스턴스 대상, 버전 고정 후).

---

## 9. 구현 현황 (Implementation Status) — 2026-07-08 기준

> 근거: `SeCuardian-Marketplace/` 복제·트리밍 소스 정적 분석(라우터·SQL·프론트·Makefile·config).
> 범례: ✅ 완료 / 🟡 부분 / ⬜ 미착수. "완료"는 코드가 존재하고 `import app.main` 부팅 검증됨을 의미(런타임 E2E 시험은 별도).

### 9.1 기능(Feature) 상태

| 기능 | 상태 | 구현 근거 (소스) | 갭 / 다음 작업 |
|---|---|---|---|
| **F-AI** AI Assistant/Orchestrator | ✅ | `app/agents/orchestrator.py`·`base_agent.py`, `router_agent.py`, `services/llm_fallback.py`·`ollama_warmup.py`, `rules/keyword_matcher.py`, seed `general`(is_required)+`chat` | 없음(핵심 준용 완료). 공유 `services/llm.py` 는 미분리(orchestrator 내부) |
| **F-SETUP** Setup Wizard | ✅ | `router_setup.py`(`/api/setup/*`), `front/src/pages/setup/SetupWizard.tsx`, `tbl_users`·`tbl_settings` | 없음 |
| **F-WEB** 웹 포털 | 🟡 | SPA: Login·Chat·Agents·Users·Settings·Profile·Addon(+modals) **+ Marketplace·Workflow·RAG·Playground·Guardrails(impl/3~6)**, `App.tsx` route 5종 + nav/헤더타이틀/i18n(ko/en) | 대시보드 화면 없음(nav 항목만). Workflow Designer 는 a11y 폼 편집기(1차)뿐, React Flow 캔버스는 로드맵 |
| **F-OPS** Makefile/DB 초기화 | 🟡 | 코어 타겟 `up/down/local-all/local-stop/dev-be/dev-fe/db-reset/seed/db-fresh/test/lint` + `ecosystem.config.js` + `scripts/{db_reset,seed,seed_local}.py` | ⚠ 삭제된 모니터 타겟(`keycloak-*`/`vault-*`/`harbor-*`/`wazuh-*`/`caddy-*`/`crowdsec-*` 등) 다수 잔존 → 정리 필요 |
| **F-ENV** 환경 분리 | 🟡 | `.env.{local,dev,staging,prod}` + `.env.example`(코어 **+ MARKETPLACE_*/TENANT_*/GUARDRAILS_*/VECTOR_BACKEND, impl/1**), `config.py`(동일 필드), `docker-compose*.yml`. 신규 marketplace 테이블 `tenant_id` 선반영 | dev/staging/prod `.env.*` 파일에 신규키 반영 확인, 그 외 신규 테이블 `tenant_id` 지속 적용 |
| **F-GOV** 거버넌스·보안 | 🟡 | `tbl_audit_log` 존재 | HITL 게이트/`tbl_hitl_approvals` 없음, OWASP 스코어카드·시크릿 매니저·SBOM 미구현 |
| **F-MP** Marketplace | 🟡 | **impl/1+impl/3**: `router_marketplace.py`(raw-SQL: catalog·install·uninstall·installs), `marketplace_assets`/`marketplace_installs` DDL(tenant_id), 단일 활성 버전+hot-deploy seam, **프론트**(`pages/marketplace/`, 카탈로그·등록·설치/해제). 시험 20/20 PASS + tsc/build 0오류 | 원격 레지스트리(§7.3 E1.5), 실 addon ZIP 파이프라인 연결(§7.6) 후속 |
| **F-WF** Workflow | 🟡 | **impl/2+impl/3**: `workflow_engine.py`(async DAG: topo fire/prune·retry·HITL·템플릿), `router_workflow.py`(CRUD·run·nodes·hitl·cancel·SSE), 3테이블(tenant_id), **프론트**(`pages/workflow/`, a11y 폼 노드/엣지 편집기·실행·HITL 승인/거부·취소). 7노드·시험 21/21 PASS + tsc/build 0오류 | React Flow 캔버스(로드맵), loop/sub-flow/cron 유보, llm 노드는 Ollama 폴백만(Claude 미연동) |
| **F-RAG** RAG/지식베이스 | 🟡 | **impl/4**: `embeddings.py`(로컬 해싱 임베더)+`rag_pipeline.py`(청킹·BM25·RRF k=60)+`router_rag.py`(컬렉션·수집·하이브리드검색), 3테이블(tenant_id), **프론트**(`pages/rag/`). 식별자 질의 BM25 최상위 랭크 실증. 시험 15/15 PASS + tsc 0오류 | pgvector/Qdrant 확장(§7.5 로드맵), eval(Recall@10/NDCG@10) 벤치마크 미실시 |
| **F-PG** Playground | 🟡 | **impl/5**: `router_playground.py`(공유 LLM 폴백 실호출 + RAG 컨텍스트 주입 + citations + degrade 무중단), `playground_runs` 테이블(tenant_id), **프론트**(`pages/playground/`, A/B 2-variant 동시실행+이력). 시험 13/13 PASS + tsc 0오류 | 비용(cost) 추적 없음(Claude 미연동), eval 실행 로드맵 |
| **F-GRD** Guardrails | 🟡 | **impl/6**: `guardrails_detector.py`(**global 도메인 PII/신용정보 13종 정규식 판정 — 로컬 재구현**, Luhn 카드검증·마스킹), `router_guardrails.py`(도메인 카탈로그·에이전트 토글·test·decision log), 3테이블(`guardrails_domain_catalog`/`agent_guardrail_config`/`guardrails_decision_log`), **프론트**(`pages/guardrails/`). 13종 전수 실판정 검증. 시험 20/20 PASS + tsc/build 0오류 | Orchestrator 게이트 배선(`guardrails_gate.py`, §7.8.4) 미구현, MCP Server 프록시 연동(로컬 판정이 1차 경로) 미구현. 25종 업종 판정기는 SeCMP 책임 밖 |

### 9.2 SeCuardian 준용 계약(§3) 상태

| 계약 | 상태 | 비고 |
|---|---|---|
| Orchestrator | ✅ | `app/agents/orchestrator.py` 클론 부팅 검증 |
| AI Assistant | ✅ | Orchestrator tool-calling 경로 |
| Agent 관리(4테이블) | ✅ | `tbl_agent_config`·`tbl_addon_agents`·`tbl_addon_agent_capabilities`·`tbl_agent_registry` 잔존 |
| **Addon Agent 핫디플로이** | ✅ **복원(impl/1)** | 사용자 결정(A): `router_addon_agent.py`·`app/addon_agent_loader.py`·`addon-agents/` 원본 복원, `main.py` `addon_init`/`addon_guard` 재배선, `router_mcp`/`router_agent_config` addon 연동 원복. Marketplace/Playground/Workflow 가 차후 소비 |

### 9.3 ⚠ 설계 전제 변경 (Deviation) — **해결됨(2026-07-08): 옵션 A 채택·완료**

PRD §3 은 Addon 핫디플로이를 "기본 유지 필수 요구사항"으로 명시했으나, 초기 트리밍 과정에서 해당 파이프라인이
일시 삭제되어 F-MP(E1) 구현 전제가 흔들린 바 있다. **사용자가 옵션 A(Addon 핫디플로이 복원)를 확정**했고,
impl/1 에서 `addon_agent_loader.py`·`router_addon_agent.py`·`addon-agents/` 원본을 복원, `router_mcp`/`router_agent_config`
연동도 원복해 준용 원칙을 회복했다(§9.2). 이후 방향(옵션 B의 취지 — 내장 에이전트가 addon 로드 기능을 소비)은
impl/1~6 에서 Marketplace 의 hot-deploy seam(`tbl_agent_config` upsert)과 Playground/Workflow 가 공유 에이전트
레지스트리(`tbl_agent_config`)를 조회하는 형태로 실현됐다. **후속 결정 불필요 — 해결 완료.**

### 9.4 Epic 진행 상태(§8.1 대비)

| Epic | 상태 | 근거 |
|---|---|---|
| E0 스캐폴드·환경·SQL | 🟡 | 스캐폴드/코어 + `.env` 원격·테넌시·RAG·Guardrails 키(impl/1) + 신규테이블 전부 `tenant_id` 선반영. 잔여: dev/staging/prod `.env.*` 개별 반영, Makefile 잔존 모니터 타겟 정리 |
| E1 Marketplace | 🟡 | impl/1+3: 카탈로그·설치 API+프론트, 단일활성버전+hot-deploy seam(시험 20/20+tsc/build). 잔여: 원격(E1.5)·실 ZIP 연결 |
| E1.5 원격 레지스트리 | ⬜ | — |
| E2 Workflow 엔진 | 🟡 | impl/2+3: DAG 실행기·상태머신·retry·HITL·SSE+3테이블+a11y 폼 프론트(시험 21/21+tsc/build) |
| E3 Workflow Designer | 🟡 | a11y 폼 노드/엣지 편집기 완료(impl/3, PRD §7.11 1차 요구사항 충족). React Flow 캔버스는 로드맵 확장 |
| E3.5 Dify Import(P5) | ⬜ | 이연 |
| E4 RAG | 🟡 | impl/4: 청킹·해싱임베더·BM25·RRF+3테이블+프론트(시험 15/15+tsc). pgvector 확장·eval 로드맵 |
| E5 Playground | 🟡 | impl/5: LLM 폴백 실행+RAG 컨텍스트 주입+A/B 프론트(시험 13/13+tsc). cost 추적·eval 로드맵 |
| E6 거버넌스 | 🟡 | `tbl_audit_log` + Guardrails 이중감사(`guardrails_decision_log`, impl/6). HITL 게이트(F-WF 내)는 있으나 별도 `tbl_hitl_approvals`·OWASP 스코어카드 없음 |
| E7 하드닝 | ⬜ | — |
| E8 Guardrails | 🟡 | impl/6: **global 13종 로컬 판정기**(실동작)+3테이블+토글+decision log+프론트(시험 20/20+tsc/build). 잔여: Orchestrator 게이트 배선, MCP 프록시 연동, 25종 판정기(SeCMP 책임 밖) |

### 9.5 권장 다음 단계

1. **Orchestrator 게이트 배선**(`guardrails_gate.py`, §7.8.4) — F-GRD 를 Orchestrator `_exec_api_call` 앞뒤로 연결(기존 Orchestrator 무변경 원칙 유지하며 얇은 래퍼로).
2. **F-MP 원격 레지스트리**(E1.5, §7.3) + **실 addon ZIP 파이프라인 연결**(§7.6) — 현재 hot-deploy seam 은 config upsert 까지만.
3. **F-WF React Flow 캔버스**(E3 확장) — 현재 a11y 폼 편집기는 1차 요구사항 충족, 캔버스는 시각적 편의성 확장.
4. **F-RAG pgvector 전환**(§7.5) + eval 벤치마크(Recall@10/NDCG@10, P3).
5. **Makefile/docker-compose 잔존 모니터 타겟 정리**, dev/staging/prod `.env.*` 신규키 전파.
6. **대시보드 화면** — 현재 nav 만 존재, `/api/agents` 카탈로그+헬스 요약 화면(§7.11) 없음.

### 9.6 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-07-08 | v0.1~v0.3 | 초안·Guardrails 상세 확정(기존 이력) |
| 2026-07-08 | v0.4 | **구현 현황(§9) 신설** — 복제·트리밍 소스 정적 분석 반영. F-AI·F-SETUP ✅, F-WEB·F-OPS·F-ENV·F-GOV 🟡, F-MP·F-WF·F-RAG·F-PG·F-GRD ⬜. Addon 핫디플로이 제거에 따른 F-MP 설계 전제 변경(§9.3 Deviation) 기록 |
| 2026-07-08 | v0.5 | **impl/1** — §9.3 옵션 A 확정: Addon 핫디플로이 **복원**(✅). F-ENV 신규 `.env`/config 키 추가. **F-MP 백엔드 이식**(v0 ORM→raw-SQL): marketplace 2테이블·`router_marketplace`·시드, 시험 20/20 PASS |
| 2026-07-08 | v0.6 | **impl/2** — **F-WF 백엔드 이식**: `workflow_engine.py`(async DAG·retry·HITL·템플릿)+`router_workflow.py`+3테이블+시드. 7노드, 시험 21/21 PASS. dev-env 검증 PASS |
| 2026-07-08 | v0.7 | **impl/3~6 — F-WF Designer 프론트·F-MP 프론트·F-RAG·F-PG·F-GRD 전체 완료**(사용자 요청 "순차적으로 구현" 일괄 수행). impl/3: WorkflowPage(a11y 폼 편집기)+MarketplacePage+라우트/nav/i18n 5종(tsc+build 0오류). impl/4: F-RAG 백엔드(해싱임베더·BM25·RRF)+프론트, 식별자질의 BM25 최상위랭크 실증(시험 15/15). impl/5: F-PG 백엔드(LLM폴백 실행+RAG 컨텍스트+degrade무중단)+A/B 프론트(시험 13/13). impl/6: F-GRD 백엔드(**global PII/신용정보 13종 정규식 판정기 로컬 재구현** — Luhn카드검증·마스킹·에이전트토글·이중감사)+프론트(13종 전수 실증, 시험 20/20). §9.3 Deviation 완전 해결로 정리. 전체 회귀: boot 24 routes, ruff 신규코드 0오류, 프론트 tsc+build 0오류(2036 modules). F-MP·F-WF·F-RAG·F-PG·F-GRD **전부 🟡(백엔드+프론트 동작, 확장 항목만 잔존)** |

---

## 부록 A. Workflow 플랫폼 오픈소스 비교 (구현 시 참고)

> 출처: `.docs/Perplexity-Workflow/workflow ...조사.md` 외. **수치는 Perplexity 추정** — 채택 전 실측·라이선스 재검증 필수.

| 항목 | Flowise | LangFlow | Dify | n8n | Sim Studio |
|---|---|---|---|---|---|
| 포지션 | 비주얼 에이전트/챗플로우 빌더 | LangChain LLM 플로우 | AI 앱 플랫폼(agent+workflow+RAG+eval+observability) | 범용 자동화(fair-code) | AI 에이전트 워크플로우 |
| 스택 | LangChain.js + ReactFlow | LangChain(Py/JS) | 웹 + RAG/eval/observability | Node.js, 400+ 커넥터 | Next.js+PG+ReactFlow+Zustand |
| 엔터프라이즈 | 기본 | 팀/프로젝트 | RBAC·버전·관측성 | 확장·온프렘 | 커뮤니티 단계 |
| 온프렘 자가호스트 | Docker | Yes | Docker Compose(문서 우수) | 온프렘/클라우드 | Docker(로컬 LLM 강조) |
| Workflow API | — | — | **`POST /workflows/run`(실측 확인, §7.2.2)** | HTTP 노드 | 성숙 중 |
| DSL export/import | — | — | **YAML DSL(graph nodes/edges), 콘솔 Import(실측 확인)** | — | — |
| 라이선스 유의 | 확인 필요 | OSS | 코어 OSS+상용 옵션 | **fair-code(재판매/호스팅 제약)** | OSS |
| 마켓 적합 | PoC/비주얼 | Python 커스텀 | 프로덕션/포털 | 프로세스 통합 | 자체 캔버스 참고 |

- **리서치 결론(v0.1)**: 프로덕션/마켓 = Dify 준용, 비주얼 설계 = Flowise, Python 커스텀 = LangFlow, 프로세스 통합 = n8n(라이선스 주의). 자체 캔버스 구축 시 Sim Studio 스택 참고.
- **본 PRD 채택(v0.2 확정)**: **자체 DAG 코어(Flow-Template 정합) + Dify DSL/API 상호운용 어댑터**(§7.2.2, 모드 A→B→C 단계적 도입).

## 부록 B. Vector DB 비교 (구현 시 참고)

> 출처: `vector_db_selection_matrix.csv`, `vector_db_evaluation_simulator.csv`, `vector_db_simulator_profiles.csv`. **추정 스코어**.

| 조건 | 1순위 | 근거 |
|---|---|---|
| <1M · 온프렘 · PostgreSQL 기존 | **pgvector** (소규모 4.45) | 기존 DB 재사용·저운영 |
| 1M~20M · 온프렘 · 필터 중요 | **Qdrant** (중규모 4.65) | 자가호스트 성능+메타필터 균형 |
| 외부 서비스 · 관리형 우선 | Pinecone (4.55) | 운영 단순·확장 |
| 하이브리드(키워드+시맨틱) 핵심 | Weaviate | BM25+벡터 융합 |
| 20M+ 분산 | Milvus | 분산 확장 |
| 빠른 로컬 PoC | Chroma | 최단 셋업 |

- **본 PRD 채택**: **pgvector 기본 → Qdrant 확장**(진화 경로). 마이그레이션: 불변 ID·임베딩 버전 고정·baseline·dual-write/shadow-query.

## 부록 C. OWASP LLM Top10 통제 매핑 (엔드포인트 스코어카드)

> 출처: `owasp_llm_rag_checklist.csv`, `owasp_llm_compliance_scorecard.csv`, `owasp_llm_custom_audit_tool.csv`. 취약영역(점수 2)= **LLM05·LLM08·LLM09** 우선 조치.

| 엔드포인트/자산 | 리스크 | 우선 조치 |
|---|---|---|
| `/agent/chat*` (system+user prompt) | LLM01 Prompt Injection | 입력 분류기·검색 격리·툴 allow-list |
| `/rag/search` | LLM06 민감정보 노출 | 컬렉션 ABAC·민감필드 마스킹 |
| `/workflow-runs`(write/delete/external 노드) | LLM08 과잉 자율 | **write/delete/external 100% HITL** |
| `/render`·출력 | LLM02 출력 처리 | HTML/JSON sanitize·직접 실행 차단 |
| `/rag/ingest` | LLM03 데이터 오염 | 소스 신뢰점수·격리 워크플로우 |
| `/model/infer` | LLM04 DoS | 테넌트 토큰 쿼터·캐시 |
| CI/CD 배포(Addon 업로드, Marketplace 원격 설치 포함) | LLM05 공급망 | 버전 핀·이미지/의존성 서명·SBOM·스캔, **원격 ZIP 체크섬/서명(§7.3)** |
| `/audit/export` | LLM10 모델 탈취 | export 제한·식별자 마스킹 |
| 검토 화면(인용/신뢰도) | LLM09 과신 | 고영향 결정 강제 검토 |
| 커넥터 크리덴셜 | LLM07 플러그인 | vault scoped 크리덴셜(정적 시크릿 금지) |
| `/api/guardrails/*` → `validate_input`/`validate_output`(global 도메인) | LLM06 민감정보 노출 | ✅실기능(PII regex 13종). 25종 업종 규칙은 **판정기 미구현**(§7.8.0) — LLM03/LLM08 관점 업종 컴플라이언스 통제는 카탈로그일 뿐 실질 통제 아님, 별도 리스크로 관리(§6) |
| Guardrails 도메인 선택 필드(`domain`) | LLM07 플러그인/도구 오남용 유사 패턴(자기신고 인가 없음) | SeCMP `agent_guardrail_config`로 서버측 강제(§7.8.3), 업스트림 `api_keys.allowed_domains` 미강제는 기록된 리스크(§6) |

---

## 리뷰 체크리스트 (Definition of Ready) — 자가 점검
- [x] 문제 정의가 실제 사용자 문제를 설명 (§2, 5개 공백 — Guardrails 포함)
- [x] MVP In/Out 둘 다 명확 (§3)
- [x] 성공 지표 측정 가능 + 기준선 (§5) — Guardrails 3개 KPI 확정(global 도메인 범위)
- [x] 수용 기준 Given-When-Then (§5)
- [x] 의존성·리스크 노출 (§6) — 무샌드박스·fair-code·Dify 버전드리프트·원격신뢰경계·**Guardrails 판정기 갭·미인증 도메인선택·감사보존 미구현**·추정치
- [x] 규제·데이터등급 NFR 반영 (§7.9) — govtech 확정 + security 특화(Guardrails PII 탐지로 PIPA 실질 커버 범위 명시)
- [x] Open Question 5건 전건 확정 반영 (§6) — Workflow/Dify, 원격 레지스트리, 멀티테넌시, 규제도메인, **Guardrails 스펙**
- [x] Guardrails 상세 스펙 (§7.8) — wise-Guardrails 전수 분석 완료, API 계약·데이터 모델·검사시점·요구사항 대응 확정. **단, "25종 업종 규칙셋 = 실판정 아닌 카탈로그"라는 결정(§7.8.0)은 제품적 판단이므로 이해관계자 확인 권장**
