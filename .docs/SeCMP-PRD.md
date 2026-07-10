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
| **F-WF** | **Workflow 내장 에이전트** | P0 | DAG 워크플로우 엔진 + Designer(React Flow). 8노드(trigger/agent/llm/condition/hitl/transform/notify/**http**), 실행 상태머신, SSE, retry. **자체 DAG 기본 + Dify DSL/API 호환 어댑터**(§7.2). **impl/25(물리 test/impl/23): 컴포넌트 팔레트**(§7.2.3) — 내장/시스템/Addon 에이전트의 개별 API를 "{에이전트명}-{기능}" 컴포넌트로 노출, `agent` 노드가 실제 API를 호출(기존 스텁 대체, 하위호환 유지) |
| **F-RAG** | **RAG/지식베이스 내장 에이전트** | P0 | 문서 수집→임베딩→벡터DB→하이브리드 검색(BM25+dense+RRF)→리랭크. pgvector 기본, Qdrant 확장 |
| **F-PG** | **Playground 내장 에이전트** | P1 | 프롬프트/에이전트/RAG/워크플로우 대화형 실험·비교·평가(eval) 표면 |
| **F-GRD** | **Guardrails 내장 에이전트** | P0 | wise-Guardrails(MCP Server, `/mcp/tools/validate_input\|validate_output`) 연동 거버넌스 에이전트. **`global`(PII/신용정보) 은 무조건 필수 판정**. **impl/21: 업종 도메인(금융·의료·제조·공공행정 등 24종) 규칙셋 전체를 에이전트 내부 데이터(`app/data/guardrails/`)로 관리**하고, classifier 규칙에는 **regex 를 생성**해 결정적 부분판정 + examplesPositive 휴리스틱으로 적용. 도메인 카탈로그에서 **필수(global) 외 도메인은 `필터적용` 토글**로 테스트 시 적용 유무를 반영(다도메인 동시 판정). 전체 ML classifier(패러프레이즈)까지의 판정은 여전히 로드맵. 에이전트별 도메인 활성화는 **SeCMP 자체 DB에서 소유·강제**(업스트림 미강제) |
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
- **Guardrails 업종별 규칙셋의 완전 ML classifier(패러프레이즈·문맥) 판정** — impl/21 에서 규칙 데이터 전체를 에이전트에 내재화하고 classifier 규칙에 **생성 regex + examplesPositive 휴리스틱**으로 결정적 부분판정까지는 제공하나, 학습형 분류기(임의 표현 탐지)는 여전히 로드맵(LLM classifier 옵션 §7.8.7).
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
| RAG 검색 품질 (하이브리드) | pure vector Recall@10 ≈ 0.55~0.80 (리서치 추정) | RRF 하이브리드 Recall@10 ≥ **0.89** | eval 세트 Recall@10/NDCG@10. **실측(impl/31, §7.5.1, 2026-07-09)**: 식별자 질의 세트 N=40, pgvector 실경로, Recall@10=**1.000** — 목표 초과 달성(단, 파라프레이즈형 dense 단독 성능은 임베딩 모델 교체 후 별도 재평가 필요) |
| RAG 검색 지연 | 신규 | p95 ≤ **250ms**(중규모 온프렘) | 검색 경로 p95 지연. **실측(impl/31)**: p95=**20.8ms**(약 12배 여유), p50=18.3ms |
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
| **워크플로우 `http` 노드(SSRF)**(impl/25, §7.2.3) — 임의 외부 URL 을 워크플로우 정의로 호출 | 내부망 스캔·메타데이터 엔드포인트 접근 등 SSRF 벡터 | 1차는 admin/supervisor 만 워크플로우 생성 가능(RBAC 기존 유지)한 admin-trust 경계로 완화. URL allow-list·사설대역 차단은 로드맵(P5 하드닝) |
| **워크플로우 `agent` 노드 실호출 전환**(impl/25) — 스텁에서 실제 내부 API 호출로 전환 | 워크플로우가 실행자 권한을 넘어서는 API를 호출할 가능성 | actor(실행 요청자) Bearer 토큰을 그대로 전달(actor-scoped) — 워크플로우는 호출자 본인 권한 이상으로 동작 불가. 서비스 계정·권한 상승 경로 없음 |
| **webhook 수신 트리거**(impl/26, §7.2.4) — 미인증 외부 엔드포인트가 워크플로우 실행을 유발 | 시크릿 유출/무차별대입 시 임의 트리거 남용, DoS | **impl/29(§7.2.4.1) 완화**: 로테이션 엔드포인트, HMAC 페이로드 서명(선택, 시크릿 미전송), 인메모리 rate limit(분당 30회, 워크플로우별) 추가. 인메모리 한계(단일 프로세스)는 아래 별도 행 참조 |
| **webhook rate limit 이 인메모리·단일 프로세스 한정**(impl/29, §7.2.4.1) | 멀티 워커/인스턴스 배포 시 워커별 독립 카운트 — 실효 한도가 설정값의 N배(N=워커 수)로 완화됨 | 강한 보장 필요 시 리버스프록시/API 게이트웨이 레벨 rate limit 병행 권장(운영 통제, 코드 레벨 해결 아님) |
| **webhook 시크릿 암호화 키가 `JWT_SECRET_KEY` 파생**(impl/29, §7.2.4.1) | `JWT_SECRET_KEY` 로테이션 시 기존 발급된 모든 webhook 시크릿이 함께 무효화(복호화 실패) | 운영 절차에 "JWT_SECRET_KEY 교체 시 webhook 재발급(rotate) 필요" 명시(§9.5), 코드 레벨 자동 마이그레이션 없음 |

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

### 7.2.3 컴포넌트 팔레트 + 실 실행(F-WF 확장, impl/25 · 물리 test/impl/23) — 사용자 요구(2026-07-09)

> **요구 배경**: "내장/시스템/Addon 에이전트가 제공하는 세부 기능(API)을 워크플로우 컴포넌트로 그대로 사용 가능해야 한다 — 예: A에이전트에 조회 API가 있으면 `A에이전트-조회` 컴포넌트로 제공." No-code/Low-code 플랫폼(Flowise/n8n/Dify) 의 "커넥터/노드 라이브러리" 패턴을 준용.

- **결정**: 별도 컴포넌트 레지스트리 테이블을 신설하지 않고, Orchestrator 가 이미 보유한 **OpenAPI 기반 동적 엔드포인트 탐지**(`_probe_prefix`·`_openapi_paths`, `app/agents/orchestrator.py`)를 재사용해 `GET /api/workflow/components` 에서 실시간 컴포넌트 목록을 생성한다(추가 테이블/동기화 불필요 — 에이전트가 뜨면 즉시 컴포넌트로 노출).
- **분류**: `tbl_agent_config` 의 7개 필수 키(§F-WEB impl/20 `BUILTIN_KEYS`) = `builtin`, 그 외 `tbl_agent_config` 행 = `system`, `tbl_addon_agents` = `addon`. 각 엔드포인트(METHOD+path)를 `{agent_name}-{OpenAPI summary}` 라벨의 컴포넌트 1건으로 매핑.
- **agent 노드 실행 갱신**: 기존 `agent` 노드는 `agent_key` 존재/활성 여부만 확인하는 **스텁**이었다(§9.1 기존 갭). `config.path` 가 지정되면(컴포넌트 선택 시 자동 채움) Orchestrator 의 `_exec_api_call`(in-proc ASGITransport 자기호출, add-only 재사용)로 **실제 API를 호출**하고 `{status, body}` 를 노드 출력에 담는다. `config.path` 가 없으면(v1 하위호환) 기존 스텁 동작 그대로 유지 — **기존 시험(test/impl/2, 21/21) 회귀 없음**.
- **인증**: 워크플로우 실행 호출자(run/hitl-approve 요청의 Bearer 토큰)를 그대로 내부 API 호출에 전달(actor-scoped, 별도 서비스 계정 없음) — 워크플로우가 실행자의 권한 이상으로 동작할 수 없음(권한 상승 방지).
- **신규 `http` 노드**: Dify DSL 매핑표(§7.2.2)의 `http-request` 대응. 외부 URL(agent-registry 밖)을 직접 호출 — admin-trust 경계 내 기능(§6 리스크에 SSRF 항목 추가).
- **1차 구현 범위**: 컴포넌트 팔레트 조회 + agent 노드 실호출 + http 노드. **1차 유보**(다음 반복 대상, 사용자 요구 접수·PRD 기록만 완료):
  - **편집형(드래그) 캔버스**: 현재 React Flow 캔버스는 읽기전용 시각화, a11y 폼이 1차 편집 수단(§9.5). 드래그 편집 승격 시 KWCAG 2.2 대체편집기 병행 필요 — 별도 반복.
  - **Dify DSL Import 어댑터(모드 A)**: §7.2.2 기 설계, 로드맵 P5(§8.2) 그대로 유지.
  - **webhook 수신 트리거·code 노드**: PRD §3 "하지 않을 것"에 code 노드는 보안 리스크로 명시 유보. webhook 인입(외부 HTTP → 워크플로우 트리거)은 `trigger_type` 필드가 이미 값만 보유(§7.2.1 데이터모델)하고 실제 수신 엔드포인트는 미구현 — 별도 반복(→ §7.2.4 impl/26 로 착수).

### 7.2.4 webhook 수신 트리거(F-WF 확장, impl/26 · 물리 test/impl/24) — 사용자 요구(2026-07-09, 순차 진행 1번째)

- **결정**: `workflows.trigger_config_json`(기존 컬럼, 신규 테이블/컬럼 없음)에 시크릿을 저장. `trigger_type="webhook"` 워크플로우 생성 시 서버가 `secrets.token_urlsafe(32)` 로 평문 시크릿을 생성해 **생성 응답에만 1회 노출**(이후 재조회 불가 — API 키 발급 UX 준용).
- **수신 엔드포인트**: `POST /api/workflows/{workflow_id}/trigger/webhook` — **JWT 불필요**(외부 시스템 호출 전제). 헤더 `X-Webhook-Secret` 을 저장된 시크릿과 검증, 불일치/미지정 시 401. `trigger_type != "webhook"` 이거나 `enabled=false` 면 404/409.
- **actor 신원(§7.2.3 원칙 계승)**: webhook 은 로그인 세션이 없으므로, 워크플로우 **생성자(`created_by`)의 현재 역할**을 `tbl_users` 에서 조회해 그 역할로 스코프된 임시 토큰을 발급해 `agent`/`http` 노드 실행에 전달한다(런타임 한정, DB 미영속). 생성자를 찾지 못하면 토큰 없이 실행 — 이 경우 `agent` 노드의 실제 API 호출은 인증 실패로 해당 노드만 실패(권한 상승 없음, §7.2.3 리스크 완화와 동일 원칙).
- **리스크**: 수신 엔드포인트가 미인증 네트워크 노출 표면 — §6 리스크 테이블에 항목 추가(시크릿 무차별대입/유출 시 트리거 남용).

#### 7.2.4.1 webhook 보안 강화(impl/29 · 물리 test/impl/27) — 사용자 요구(2026-07-09, 후속 진행 1번째)

- **저장 방식 전환(bcrypt → Fernet 대칭암호)**: impl/26 의 `webhook_secret_hash`(bcrypt, 단방향)는 로테이션·HMAC 서명 검증에 필요한 **평문 복원이 불가능**해 전환 필요. `webhook_secret_enc`(Fernet, `cryptography` — 이미 `python-jose[cryptography]` 의존성으로 설치되어 있어 신규 설치 없음)로 교체. Fernet 키는 `hashlib.sha256(settings.jwt_secret_key).digest()` 파생(신규 env 불요, add-only) — **주의**: `JWT_SECRET_KEY` 로테이션 시 기존 webhook 시크릿도 함께 무효화됨(§6 운영 리스크로 기록).
- **로테이션 엔드포인트**: `POST /api/workflows/{workflow_id}/trigger/webhook/rotate`(admin/supervisor) — 신규 시크릿 생성·재암호화, 응답에 평문 1회 노출(구 시크릿 즉시 무효). `trigger_type != "webhook"` 이면 409.
- **HMAC 페이로드 서명(선택)**: `X-Webhook-Signature: sha256=<hex hmac-sha256(secret, raw_body)>` 헤더 지원(GitHub 웹훅 컨벤션 준용) — 원문 요청 바디 기준 서명이라 **시크릿 자체를 매 호출마다 전송하지 않아도 됨**(프록시/접근로그 노출 축소). `X-Webhook-Secret`(기존, 직접비교) 과 `X-Webhook-Signature`(신규, HMAC) 중 **하나만 유효하면 통과** — 하위호환 유지(impl/26 기존 연동 무변경 동작).
- **rate limiting**: 워크플로우별 **인메모리 고정윈도우**(기본 분당 30회, `settings.workflow_webhook_rate_limit_per_min`) 제한, 초과 시 429. **단일 프로세스 한정**(멀티 워커/인스턴스 배포 시 워커별 독립 카운트 — 분산 rate limit 아님, §6 리스크로 명시). 강한 보장이 필요하면 리버스프록시/API 게이트웨이 레벨 rate limit 병행 권장(기존 §6 권고 유지).
- **하위호환**: impl/26 에서 이미 발급된 workflow 는 `webhook_secret_hash`(구 필드)만 있고 `webhook_secret_enc`(신규 필드)가 없어 검증 실패(401)한다 — **재발급(rotate) 1회 필요**. 이 프로젝트는 아직 프로덕션 배포 전(로컬/개발 단계)이라 실사용 영향 없음, 운영 마이그레이션 필요 시 문서화(§9.5).

### 7.2.5 편집형(드래그) 워크플로우 캔버스(F-WF 확장, impl/27 · 물리 test/impl/25) — 사용자 요구(2026-07-09, 순차 진행 2번째)

- **결정**: `WorkflowCanvas`(React Flow, impl/18 부터 존재)를 **읽기전용 시각화 → 편집형**으로 승격. 노드 드래그 이동, 핸들 드래그로 엣지 연결(`onConnect`), 노드/엣지 선택 후 삭제(Backspace/Delete)를 지원. 노드 좌표는 `definition_json.nodes[].position`(신규 **선택적** 필드)에 저장 — `definition_json` 은 스키마 없는 JSON 컬럼이라 **백엔드 변경 없음**(`_validate_definition` 은 `id`/`type`/edge 참조만 검사, 추가 키는 통과).
- **KWCAG 2.2 준수 방식**: 캔버스 자체를 키보드 접근 가능하게 만들지 않는다(React Flow 드래그는 마우스 중심). 대신 **기존 a11y 폼 편집기(`DefinitionEditor`, impl/3)를 캔버스와 동일한 상위 상태(`nodes`/`edges`)를 공유하는 대체 편집기로 계속 병행**한다 — 두 편집기 중 어느 쪽으로 편집해도 동일한 워크플로우 정의에 즉시 반영되며, 키보드 전용 사용자는 폼만으로 전체 기능(노드/엣지 추가·수정·삭제·컴포넌트 삽입)을 완결할 수 있다. §4/§7.11 의 "캔버스 대신 키보드 전용 폼을 1차 제공" 요구를 폼 유지로 충족.
- **좌표 미지정 노드**: `position` 이 없는 노드(구 워크플로우, 폼으로 신규 추가된 노드)는 기존 BFS 깊이 기반 자동배치로 폴백 — 드래그하면 그 순간부터 좌표가 저장된다.
- **미포함(1차 유보)**: 조건 분기(`when`)는 캔버스 연결로는 값 미지정 상태로 생성되고, 값 설정은 여전히 폼에서(캔버스 엣지 라벨 직접 편집 UI는 로드맵). 노드 리사이즈·그룹핑·undo/redo 는 로드맵.

### 7.2.6 Dify DSL Import 어댑터 — 모드 A(F-WF 확장, impl/28 · 물리 test/impl/26) — 사용자 요구(2026-07-09, 순차 진행 3번째)

> **가정/전제**: 실제 도입 전 대상 Dify 버전 고정·DSL 스키마 재검증 필요(§7.2.2 전제 조건 그대로 승계).
> 본 구현은 §7.2.2 에 문서화된 **2026-07-08 실측 노드 매핑표**를 근거로 하되, Dify DSL 자체가
> 버전마다 필드가 달라질 수 있어 **관용적(lenient) 파싱**을 채택 — 알 수 없는 필드는 무시,
> 매핑 불가 노드 타입은 크래시 대신 `transform` 플레이스홀더 + `warnings[]` 로 명시한다.

- **결정**: §7.2.2 모드 A(Import, design-time)를 구현. `POST /api/workflows/import/dify-dsl`(admin/supervisor)
  가 Dify DSL YAML 텍스트를 받아 §7.2.2 노드 매핑표대로 내부 `definition_json`(nodes/edges) 으로 변환 후
  워크플로우를 생성한다. **실행은 여전히 SeCMP 자체 엔진**(모드 B 위임 실행은 로드맵 유지, §7.2.2 그대로).
- **노드 매핑**(§7.2.2 표 재사용): `start→trigger` · `llm→llm`(prompt_template/prompt 최선노력 추출) ·
  `if-else→condition`(comparison_operator 를 SeCMP `op` 서브셋[`truthy/==/!=/>/</contains`]로 매핑,
  미지원 연산자는 `truthy` 폴백) · `knowledge-retrieval→agent`(agent_key=`rag`, 실 컬렉션 재바인딩은
  수동, `config.note` 로 표시) · `http-request→http`(§7.2.3 신규 노드 재사용) ·
  `tool→agent`(agent_key 공란, 컴포넌트 팔레트로 수동 지정 필요 — §7.2.3 재사용) ·
  `answer`/`end→notify` · **`code`, 미인식 타입 → `transform` 플레이스홀더**(§3 하지 않을 것 유지) +
  각각 `warnings[]` 항목 기록. **엣지**: `sourceHandle` 이 `true`/`false` 면 SeCMP `when` 으로 이식,
  그 외는 무조건(unconditional) 엣지로 이식. **id 는 Dify 원본 노드 id 를 그대로 보존**(SeCMP 는 id
  형식 제약이 없어 재매핑 불필요, edge source/target 정합성이 자동 유지됨).
- **데이터 모델 확장**(§7.2.2 예고 반영): `workflows` 에 `dify_dsl_source TEXT NULL`(원본 YAML 보관,
  round-trip 대비) · `dify_dsl_version VARCHAR(32) NULL`(DSL 최상위 `version:` 필드, 없으면 `unknown`)
  컬럼 추가 — sqlite/pg 양쪽 `01_init.sql`(신규 설치) + `app/db.py` 컬럼 마이그레이션(기존 설치, 멱등)
  양쪽에 반영.
- **미포함(1차 유보, §3·§7.2.2 그대로)**: 모드 B(Delegate 실행)·모드 C(Round-trip), `code` 노드 실행,
  Dify 플러그인 ↔ Addon Agent 자동 1:1 매핑(수동 필요), 파일 업로드(ZIP/멀티파트) — 1차는 YAML **텍스트**
  입력만(웹 콘솔에서 export 한 YAML 을 붙여넣기).
- **리스크**: DSL 스키마가 실제 Dify 버전과 달라 매핑이 부정확할 수 있음(§6 리스크 테이블 기존 항목
  "Dify DSL/API 버전 드리프트"에 이미 반영됨) — 가져오기 결과는 **항상 사람 검토 후 활성화** 권장
  (`enabled=false` 로 생성, §7.2.6 구현에서 강제).

### 7.2.7 워크플로우 `enabled` 토글 PATCH 엔드포인트(F-WF 확장, impl/30 · 물리 test/impl/28) — 사용자 요구(2026-07-09, 후속 진행 2번째)

- **배경**: 활성/비활성 전환 API 부재가 §9.5 에 반복 기록된 기존 갭 — impl/24 시험은 DB 직접조작으로
  우회했고, impl/28(Dify 가져오기)이 **항상 `enabled=false`** 로 생성하는 설계라 검토 후 활성화하는
  실사용 흐름에도 필요.
- **결정**: `PATCH /api/workflows/{workflow_id}`(admin/supervisor) — 요청 바디 `{"enabled": bool}`.
  **1차 범위는 `enabled` 토글만**(이름·정의 등 전체 편집 PATCH 는 범위 밖 — 정의 편집은 기존
  a11y 폼/캔버스가 신규 워크플로우 생성 흐름으로 담당, §7.2.5). 워크플로우 미존재 시 404.
  → **impl/32(§7.2.8)에서 `name`/`description`/`definition_json` 부분 편집으로 확장됨(하위호환 유지).**
- **부수 효과 없음**: 토글은 `enabled` 컬럼만 변경 — 실행 중인 run 에는 영향 없음(신규 트리거만
  차단/허용됨, 기존 §7.2.1 상태머신 무변경).

### 7.2.8 풀스크린 워크플로우 빌더(Flowise/Dify 준용, F-WF 확장, impl/32 · 물리 test/impl/30) — 사용자 요구(2026-07-09, workflow 재구현)

> **배경**: impl/27(§7.2.5) 편집형 캔버스는 "새 워크플로우" 생성 패널 안의 **320px 보조 위젯**에
> 그쳐 실사용 불가 판정(사용자 피드백 2026-07-09 — "현재 구현 코드로는 사용할 수가 없습니다").
> `.docs/Perplexity-Workflow/`·`Perplexity-No-code or Low-code ~`·`Perplexity-Marketplace 조사 ~`
> 리서치가 제시한 **노드 라이브러리(팔레트) → 캔버스 drag & drop → 인스펙터(속성 편집)** 3분할
> 빌더 패턴(Flowise·Dify·n8n 공통 UX)을 준용해 재구현한다.
> **라이선스 경계**: Flowise(Apache-2.0)·Dify(Apache-2.0 계열 + 추가 조건) **코드를 복사하지 않는다** —
> UX 패턴만 참조하고, 구현은 기보유 React Flow(MIT, `@xyflow/react` 12)로 자체 작성.
> Dify 프론트엔드 등 상용/추가조건 라이선스 구성요소는 도입 제외(§6 라이선스 리스크 기존 원칙 유지).

- **결정(프론트)**: 신규 라우트 **`/workflow/builder`**(신규 생성)·**`/workflow/builder/:id`**(기존 편집),
  `WorkflowBuilderPage` — 전용 풀스크린 3분할 레이아웃:
  1. **좌측 팔레트** — 8종 노드 타입 + §7.2.3 컴포넌트(내장/시스템/Addon 그룹, 검색 필터).
     HTML5 `dataTransfer` 드래그로 캔버스 임의 좌표에 드롭(`screenToFlowPosition`) — Flowise/Dify
     의 "노드 라이브러리 → 캔버스" 패턴. 클릭 삽입도 병행(키보드/보조기기 폴백).
  2. **중앙 캔버스** — React Flow 풀높이. 타입별 색상 헤더·아이콘·config 요약을 가진 **커스텀 노드**,
     핸들 연결·이동·삭제(§7.2.5 기능 승계), Background/Controls/MiniMap.
  3. **우측 인스펙터** — 선택 노드의 타입별 **구조화 설정 폼**(agent: agent_key/method/path·컴포넌트
     재선택, llm: prompt, condition: op/left/right, http: method/url, notify/transform/hitl/trigger 등)
     + raw JSON 폴백 편집. 선택 엣지의 `when`(true/false/값) 직접 편집 — §7.2.5 유보 항목 해소.
  - 상단 툴바: 이름·설명·트리거 타입·저장(신규 POST / 기존 PATCH)·목록 복귀.
- **결정(백엔드)**: `PATCH /api/workflows/{workflow_id}`(§7.2.7)를 **부분 편집으로 확장** —
  `enabled` 외에 `name`/`description`/`definition_json`(전달 시 `_validate_definition` 재검증)을
  선택적으로 수용, `definition_json` 변경 시 `version` +1. 기존 `{"enabled": bool}` 단독 호출은
  하위호환(스키마 전 필드 optional). 신규 테이블/컬럼 없음.
- **KWCAG 2.2**: 빌더 캔버스는 §7.2.5 원칙 그대로 마우스 중심 — **기존 `WorkflowPage` a11y 폼
  편집기(생성 패널)를 계속 병행 유지**하고, 빌더에도 팔레트 클릭 삽입 + 인스펙터 폼(전부 label 있는
  표준 입력)을 제공해 캔버스 없이도 정의 편집이 가능하게 한다.
- **미포함(로드맵)**: undo/redo·노드 그룹핑·복사/붙여넣기·자동 레이아웃 버튼·실행 결과의 캔버스
  노드 상태 오버레이(Flowise 실행 추적 UX)·워크플로우 버전 diff.

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

#### 7.5.1 pgvector 실측 벤치마크(impl/31 · 물리 test/impl/29) — 사용자 요구(2026-07-09, 후속 진행 3번째, 승인 후 진행)

- **배경**: §9.5 잔여 "실 인프라 실측" 항목. `app/services/vector_backend.py`(impl/15) 는 이미
  pgvector 경로(`ensure_pg_schema`/`write_embedding`/`dense_scores`)를 구현·시험 완료했으나,
  이 프로젝트 sqlite 세션에서는 `resolve()="local"` 폴백만 검증됐다 — **실제 PostgreSQL+pgvector
  확장 환경에서의 실측이 없었음**.
- **발견/수정**: `docker-compose.yml` `postgres` 서비스가 plain `postgres:17-alpine` 이미지를 써서
  `vector` 확장이 없었다(`CREATE EXTENSION vector` 실패 시 `ensure_pg_schema` 는 예외를 삼키고
  조용히 local 폴백 — §7.5 pgvector "1차 기본" 설계와 불일치하는 잠재 결함). **`pgvector/pgvector:pg17`
  이미지로 교체**(표준 PostgreSQL 17 + vector 확장 사전 빌드, 나머지 설정 동일) — 임시 우회가 아닌
  영구 수정(add-only, 컨테이너만 재기동하면 반영).
- **실측 방법**: 사용자 승인(네트워크 이미지 pull + 컨테이너 기동) 후 `docker compose up -d postgres`
  로 실 PostgreSQL 기동 → `ENV=dev DATABASE_URL=postgresql://... VECTOR_BACKEND=pgvector` 로 앱 부팅해
  `resolve()="pgvector"` 실경로 활성화 → 문서 인입·질의 세트로 `rag_pipeline.hybrid_search` 를
  **실제 pgvector ANN 경로**(`dense_scores` SQL `<=>`)로 호출해 Recall@10·p95 측정.
- **실측 결과**: `test/impl/29/result.md` 에 실제 수치 기록(추정 아님, `가정:` 태그 제거 대상).
  로컬 해싱 임베더(§7.5, 의미 기반 아님) 한계로 **파라프레이즈형 질의의 Recall 은 목표(0.89) 미달이
  예상되며, 이는 인프라 문제가 아니라 별도 로드맵인 "임베딩 모델 교체"(§9.5) 의 영역** — 벤치마크는
  ① pgvector 경로 자체가 정상 동작하는지(인프라 검증, 이번 목표) 와 ② 임베딩 품질(별도 로드맵)을
  분리해 보고한다.
- **정리**: 벤치마크 후 postgres 컨테이너는 로컬 개발 리소스 절약을 위해 `docker compose stop postgres`
  로 정지(데이터 볼륨은 보존, 재기동 시 재사용 가능). 상시 postgres 개발 환경 전환은 별도 결정 사항.

### 7.6 Marketplace (F-MP)

- 기존 자산 재사용: `router_addon_agent.py`의 `upload`/`scaffold`/`toggle`/`delete`/`export`/`export-standalone`, `agent-registry`(A2A/MCP), `capabilities` 인덱스.
- 신규: **카탈로그**(자산 메타·버전·카테고리·거버넌스·필요 env·리뷰), **설치 트랜잭션**(upload 파이프라인 래핑 + 롤백), **버전관리**(meta.version + min_platform_version, 1차 단일 활성), **원격 레지스트리**(§7.3). 자산 유형: `agent` / `workflow` / `rag-pipeline` / `tool-proxy connector`.
- 설치 = 기존 hot-deploy 파이프라인(SQL→`load_router()`→config upsert→OpenAPI 캐시버스트) — 로컬/원격 공통.

### 7.6.1 에이전트 통합 관리 — 탭 통합 + 보안 에이전트 자산 카탈로그 이관 (F-MP 확장, impl/36 · 물리 test/impl/34) — 사용자 요구(2026-07-09)

**목표**: 모든 에이전트를 SeCuardian-Marketplace 에서 일원 관리한다(SeCuardian PRD §20 연동).

1. **탭 통합**: 에이전트 관리 허브의 `내장 에이전트`/`시스템 에이전트` 2개 탭(impl/20, v0.16)을
   **`내장 에이전트` 단일 탭으로 통합** — `tbl_agent_config` 전체(사용자 Addon 제외)를 한 그리드로
   표시하고, 자산 카탈로그(로컬+원격)와 `자산 등록` 버튼을 통합 탭으로 이동.
   `Addon 에이전트` 탭·기능은 무변경 유지. `BUILTIN_KEYS` 분류 셋·`system` 탭 제거.
2. **보안 에이전트 자산 카탈로그 이관**: 종전 '시스템 에이전트'로 표출되던 SeCuardian 내장
   보안 13종(vasca-cve·cilium-netpol·teler-ids·shuffle-soar·neosync-dlp·otel-collector·
   teleport-pam·velociraptor-dfir·ai-redteam·isms-p-evidence·behavior-noti·agentic-soc·
   ai-eval-gate — Orchestrator `general`·AI 어시스턴트 `chat` 제외)을
   **marketplace_assets(kind=agent, category=security) 자산으로 등록**해 카탈로그 설치 방식으로 제공.
   - emb_ 패키지 13종은 `addon-agents/zip`·`_templates` 에서 제거하고
     **`marketplace-assets/security/`** 로 이동(소스 디렉터리+zip) — zip 블롭은 설치 시 hot-deploy 에 사용.
   - `scripts/seed.py`(=`make seed`)에서 보안 13종 `tbl_agent_config` 시드를 제거(기반 시드만),
     **`scripts/seed_security.py`(=`make seed-security`)** 가 카탈로그 등록(자산 메타 ko/en +
     `marketplace_asset_blobs` zip 블롭 + sha256 checksum)을 멱등 수행.
   - 설치(`POST /api/marketplace/install/{key}`) 시 기존 계약 그대로 `tbl_agent_config` upsert
     (`nav_group='marketplace'`) + zip 블롭 hot-deploy — 통합 '내장 에이전트' 탭에 편입.
3. **zip 스캐폴드 등록 UI**: `자산 등록` 모달에서 카탈로그 메타 등록과 함께 **addon ZIP
   (스캐폴드 형식: `{key}-app.py`+`{key}-meta.json`[+front/sql]) 첨부 업로드**를 지원 —
   기존 `POST /api/marketplace/catalog/{asset_key}/zip`(impl/14) 재사용, 백엔드 무변경.
4. **템플릿 정리(SeCuardian §20.1 동일 적용)**: `_templates/` 는 Board 만 잔류, 나머지 5종
   (RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent·UserManager)은 `addon-agents/zip/` 으로 이동.
   템플릿 목록/다운로드/스캐폴더 API 는 `_templates/`→`zip/` fallback 으로 기능 무변경.
5. **중복 제거 결과(2026-07-09 전수 비교)**: SeCuardian ↔ SeCMP `addon-agents/zip` 공유 18종 동일,
   `_templates` 는 SeCMP 측이 최신(`.page` 리팩터) — **최신 버전 관리 주체 = SeCuardian-Marketplace**.
6. **오류 수정(2026-07-09, impl/37 · 물리 test/impl/35) — emb_ 규약 폐지 + SeCuardian zip 최종 정리**
   (SeCuardian PRD §20.4 연동):
   - 모든 패키지에서 `emb_` prefix 제거 — 디렉터리·zip·내부 파일명·meta `key`
     (`addon-agents/zip/`: marketplace·workflow·rag·playground·guardrails·server-shell,
     `marketplace-assets/security/`: 보안 13종). `scripts/seed_security.py` 블롭 경로 동기
     (`{key}.zip`).
   - prefix 없는 zip 업로드/hot-deploy 는 config 키 선재 시 `is_builtin=1` 등록(기존 호환 경로) —
     내장 탭과 ADDON 탭 간 중복 없음.
   - SeCuardian `addon-agents/zip/` 은 보안 내장 13종만 잔류 — 템플릿 5종·server-shell·
     순수 ADDON 4종은 SeCMP 이전(동일본 확인) 후 SeCuardian 에서 삭제.
7. **자산 디렉터리 재구성(2026-07-09, impl/38 · 물리 test/impl/36) — `addon-agents/zip` 폐지 + 카테고리별 이관**
   (사용자 요구): SeCMP 의 모든 자산 소스를 **`marketplace-assets/<카테고리>/`** 로 일원화한다.
   `addon-agents/zip/` 은 폐지하고, `addon-agents/` 에는 런타임 산출물 `deployed/` 만 남긴다.
   - **`marketplace-assets/security/`** (13, 유지): vasca-cve·cilium-netpol·teler-ids·shuffle-soar·
     neosync-dlp·otel-collector·teleport-pam·velociraptor-dfir·ai-redteam·isms-p-evidence·
     behavior-noti·agentic-soc·ai-eval-gate. zip/ 에 잔존하는 security 는 여기로 이관하되
     **이미 존재하면 zip/ 사본을 삭제**(중복 제거).
   - **`marketplace-assets/builtin/`** (5, 신규): SeCMP 내장 에이전트 ADDON 판 —
     marketplace·workflow·rag·playground·guardrails.
   - **`marketplace-assets/addon/`** (5, 신규): addon 관리 zip 업로드/스캐폴더 **템플릿 경로**
     대상 — Board·RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent (`_TYPE_TEMPLATE` 매핑 대상)
     + `_templates/Board` 이관. `addon-agents/_templates/` 도 폐지.
   - **`marketplace-assets/utilities/`** (6, 신규): 그 외 유틸리티/순수 ADDON —
     UserManager·server-shell·ai-traffic-monitor·caddy-proxy·grafana-dashboard·truffle-scan.
   - **코드 영향**: `router_addon_agent.py` 의 템플릿 조회 기준 경로를
     `addon-agents/{_templates,zip}` → **`marketplace-assets/addon`** 로 전환
     (`_TYPE_TEMPLATE` 값 dir 그대로, 목록/다운로드/스캐폴더 기능 무변경). `_ZIP_CATALOG`/
     `_ZIP_TEMPLATE_NAMES` fallback 제거. `deployed/`(bind mount)·seed_security(security 경로)는 무변경.
   - **이미지 포함**: `marketplace-assets/` 는 `.dockerignore` 미제외(`COPY . .`) → 컨테이너에 포함.

### 7.6.2 자산 등록 UX 개선 + 카테고리 카탈로그 (F-MP 확장, impl/41 · 물리 test/impl/39) — 사용자 요구(2026-07-10)

**목표**: 자산 등록 → 카탈로그 생성 → 에이전트 자동 표시의 전 과정을 매끄럽게 한다.

1. **asset_key 자동부여**: `자산 등록` 모달에서 `asset_key` 입력을 제거하고 사용자는 `name`
   (예: `security`)만 입력 — 서버(`POST /api/marketplace/catalog`)가 name 을 슬러그화해
   asset_key 를 자동 생성(소문자·영숫자·하이픈, 충돌 시 `-2`,`-3` … 접미). `asset_key` 를
   명시하면 기존 동작 유지(하위호환).
2. **Addon ZIP 다중 첨부**: `새 Agent 만들기`의 ZIP 업로드 등록과 동일하게 **여러 ZIP 동시
   선택**을 지원. 신규 `POST /api/marketplace/catalog/zip`(multipart, files[]) — 각 ZIP 의
   `{key}-meta.json` 을 파싱해 asset_key(meta key)·name·description(ko/en)·version 을 추출,
   `marketplace_assets`(kind=agent) 등록 + `marketplace_asset_blobs` 블롭 저장(sha256)을
   ZIP 별로 멱등 수행(동일 key@version 존재 시 메타·블롭 갱신). 설치 시 기존 hot-deploy 계약 그대로.
3. **카테고리별 카탈로그 표시**: 자산 카탈로그를 `category`(security·utilities·general …) 별
   섹션으로 그룹 표시 — 설명 하단에 등록된 보안(security) 에이전트가 용도별로 보이도록 한다.
4. **utilities 시드**: `scripts/seed_assets.py`(=`make seed-assets`) 신설 —
   `marketplace-assets/{security,utilities}/` 를 스캔해 `{key}-meta.json` 기반으로 미등록
   자산만 INSERT(기존 등록분 무변경) + zip 블롭 checksum upsert. utilities 6종
   (UserManager·server-shell·ai-traffic-monitor·caddy-proxy·grafana-dashboard·truffle-scan)이
   카탈로그(category=utilities)에 표시된다. builtin(코어)·addon(스캐폴드 템플릿)은 시드 제외.
5. **등록 즉시 반영**: 자산 등록/ZIP 등록 완료 시 `marketplaceChanged` 이벤트로 카탈로그를
   재조회 — 페이지 새로고침 없이 등록 자산이 즉시 표시된다.
6. **README 상세화**: 설치/미설치 배지의 의미와 설치 시 내부 동작(installs 기록 →
   `tbl_agent_config` upsert → zip 블롭 hot-deploy → 내장 탭·Orchestrator 편입), 설치 후
   이용 방법을 README.md/README.en.md 에 상세 기술.

### 7.6.3 카탈로그 기본 등록 + 카테고리별 추가 등록 (F-MP 확장, impl/42 · 물리 test/impl/40) — 사용자 요구(2026-07-10)

**목표**: security·utilities 자산은 DB 에 기본 등록된 상태로 제공하고, 카탈로그(카테고리)별로
에이전트를 추가 등록할 수 있게 한다.

1. **기본 등록 범위**: `marketplace-assets/` 4분류 중 **security·utilities 만** 자산 카탈로그
   대상 — addon(스캐폴드 템플릿)·builtin(코어 내장)은 카탈로그 등록에서 제외한다.
   결과적으로 마켓플레이스 화면 자산 카탈로그에 security(13)·utilities(6) 섹션이 기본 표시된다.
2. **DB 기본 등록**: `make db-fresh` 가 seed(기반) → seed-security(보안 curated) →
   seed-assets(스캔) 를 순차 수행해 **초기화 직후에도 security·utilities 가 등록 상태**가 되도록
   체인을 확장한다. 기존 dev DB 에는 `make seed-assets` 1회 실행으로 utilities 를 편입(완료).
3. **카테고리별 추가 등록 버튼**: 자산 카탈로그의 각 카테고리 섹션 헤더에 `+ 추가` 버튼(admin) —
   해당 category 가 프리셋된 자산 등록 모달을 열어 에이전트(메타 또는 ZIP 다중)를 그 카탈로그에
   바로 추가한다. 상단 `자산 등록` 버튼은 **카탈로그(신규 category 자유 입력) 생성 + 자산 등록**
   역할 — category 입력(기본 general)을 노출한다.
4. **구현 형태**: `AssetRegisterModal` 을 독립 컴포넌트로 분리(`category` prop 프리셋 지원),
   `registerAsset`(body.category)·`registerAssetZips`(query category) 로 백엔드 기존 계약 재사용
   (백엔드 무변경).

### 7.6.4 마켓플레이스 3탭 재구성 — 카탈로그/설치됨/Addon 분리 (F-MP 확장, impl/43 · 물리 test/impl/41) — 사용자 요구(2026-07-10)

**배경**: §7.6.1 탭 통합 후 '내장 에이전트' 탭에 builtin 에이전트와 카탈로그·설치 자산이 한 화면에
섞여 표시(스크린샷 접수) — 카탈로그와 설치본을 분리한다.

1. **탭 구성 변경**: 마켓플레이스 진입 시 3탭 — **`자산 카탈로그` / `에이전트(설치됨)` /
   `Addon 에이전트`** (기본 탭 = 자산 카탈로그). 종전 `내장 에이전트` 단일 탭을 분해.
2. **자산 카탈로그 탭**: 현행 유지 — 카테고리(security·utilities·general …)별 자산 목록 +
   카테고리별 `+ 추가`(§7.6.3) + 상단 `자산 등록` 버튼 + 원격 레지스트리 섹션.
3. **에이전트(설치됨) 탭**: builtin(기본·내장 7종 등 카탈로그 외 config) + **활성 설치된**
   카탈로그 에이전트만 표시. 카탈로그에서 설치하면 나타나고 해제하면 숨는다 —
   판정 기준은 `tbl_agent_config` 존재 여부가 아니라 **카탈로그 자산의 활성 설치 여부**
   (`installed=true`). 설치/해제 시 `marketplaceChanged` 이벤트로 두 탭 즉시 동기화.
4. **좌측 네비게이션**: 화면(front) 있는 에이전트는 설치(hot-deploy) 시 좌측 메뉴에 노출 —
   기존 hot-deploy 경로 그대로(무변경).
5. **분류·정렬(보완 2026-07-10, impl/45 · 물리 test/impl/43)**: 설치됨 탭도 자산 카탈로그와
   동일하게 **카테고리 섹션으로 그룹 표시** — `builtin`(기본·내장 등 카탈로그 외 config) 섹션을
   먼저, 이어서 `security`·`utilities`·`general` … 순(카탈로그 카테고리 순서와 동일).
   섹션 내 정렬은 builtin=config 기존 순서, 카탈로그 그룹=카탈로그 표시 순서.
   (최초 구현의 단일 그리드+우선순위 정렬을 카테고리 그룹핑으로 정정 — 사용자 재확인)
6. **해제 잔존 결함 수정(impl/45)**: 설치됨 탭 판정·그룹핑의 카탈로그 매칭을 **대소문자 무시**로
   수행 — addon upload 파이프라인이 config 키를 소문자화(예: `usermanager`)해 자산 키
   (`UserManager`)와 불일치, 해제 후에도 builtin 으로 오분류되어 잔존하던 결함 해소.

### 7.6.5 해제 시 hot-deploy 잔재 완전 정리 + 상단 설명 (F-MP 확장, impl/44 · 물리 test/impl/42) — 사용자 요구(2026-07-10)

**배경(결함)**: 카탈로그 설치 시 zip 블롭이 addon upload 파이프라인으로 hot-deploy 되지만,
**해제는 installs 비활성화 + config disable 만** 수행 — `tbl_addon_agents` 행,
`addon-agents/deployed/{key}/` 디렉터리, `front/src/pages/addon/deployed/{key}.tsx` 가 잔존해
좌측 네비게이션(= `tbl_addon_agents.is_active && has_front`) 메뉴가 남는다.
설치본은 `is_builtin=1` 로 등록되어 addon 삭제 API(403 가드)로도 정리 불가.

1. **상단 설명 수정**: 마켓플레이스 페이지 설명(`agent.pageDesc`)에 자산 카탈로그(탐색·설치·
   버전관리) 설명을 포함해 3탭 구성을 반영한다(ko/en).
2. **해제 = 완전 undeploy**: `DELETE /api/marketplace/install/{key}` 가 기존 처리
   (installs 비활성 + config disable)에 더해 hot-deploy 산출물을 정리한다 —
   addon 테이블 DROP·`deployed/{key}` 삭제·front tsx 삭제·MCP 중지/설정 삭제·
   `tbl_addon_agents` 행 삭제·front 존재 시 web 재빌드. `delete_addon` 본문을 공용 헬퍼로
   분리해 재사용(중복 구현 금지). addon 키는 **대소문자 무시 매칭**(upload 파이프라인 소문자화 대응).
   라이브 라우터 완전 제거는 기존 계약대로 앱 재시작 필요(메뉴·목록은 즉시 반영).
3. **네비 즉시 동기화**: 프론트 설치/해제 시 `agentConfigChanged` 이벤트도 발행 —
   AppLayout 네비가 즉시 갱신된다.
4. **잔재 정리 스크립트**: `scripts/cleanup_addon_remnants.py`(=`make cleanup-addons`) —
   ① 활성 설치가 없는 카탈로그 자산의 addon 행+deployed 디렉터리+front tsx 제거(대소문자 무시)
   ② addon 행이 없는 고아 deployed 디렉터리 제거. 과거 결함·시험으로 누적된 잔재의 일괄 정리용(멱등).
5. **addon-agents/ 디렉터리 정책**: `deployed/`(런타임 bind-mount·loader·compose 참조)와
   README 만 유지 — 디렉터리 자체는 런타임 필수라 삭제하지 않는다(§7.6.1-7 재확인).

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

### 7.8.7 도메인별 필터 확장 (impl/21) — 규칙 데이터 내재화 + regex 생성 + 필터적용 토글

**요구(사용자, 2026-07-08)**: `global`(PII/신용정보, **무조건 필수**) 외에도 wise-Guardrails 규칙 데이터를 참고해 **도메인별로 모두 적용**한다. 도메인 카탈로그에서 **필수 도메인 외에는 `필터적용` 토글**로 테스트 시 해당 필터의 적용 유무를 반영한다. 결과적으로 **모든 도메인 규칙 JSON 을 가드레일 에이전트가 내부 데이터로 관리**한다.

**설계 결정(사용자 확정)**: "Regex subset + examplesPositive 휴리스틱"을 기본으로 하되, classifier 전용 산업 도메인 규칙에도 **regex 를 생성**해 에이전트 내부 데이터로 관리.

- **데이터 내재화**: `scripts/build_guardrails_data.py` 가 wise-Guardrails `Guardrails-Service/scripts/*.kr.json`(+en) 을 읽어 `app/data/guardrails/<domain>.json` + `_manifest.json` 으로 컴파일(재실행 가능·멱등). 소스 경로는 `GUARDRAILS_SCRIPTS_DIR`(기본값 = wise-Guardrails scripts). 런타임은 wise-Guardrails 원본에 의존하지 않고 **컴파일된 내부 데이터만** 로드.
- **regex 생성**: `patternType=regex|regex+classifier` 는 원본 `patterns.regex` 를 그대로 사용. `patternType=classifier`(regex 없음) 는 `examplesPositive`(+subCategory) 에서 한국어 키워드를 추출해 **보수적 키워드-공기(AND-of-lookahead) regex 를 생성**(`generated:true` 표기). 키워드 도출 실패 시 해당 규칙은 regex 없이 유지(오탐 억제).
- **판정 경로**: `app/services/guardrails_rules.py`(컴파일 데이터 로드·regex 컴파일·캐시) → `guardrails_detector.detect_domain/decide_multi`(다도메인 동시 판정, 도메인별 breakdown + 통합 결정=최고 severity). 기존 `global` 13종 하드코딩은 컴파일 데이터 부재 시 폴백으로 유지(무데이터 CI 안전).
- **필터적용 토글**: `guardrails_domain_catalog.filter_enabled`(신규 컬럼). `global` 은 `required`(항상 1, 토글 잠금). `PUT /api/guardrails/domains/{domain_key}/filter {enabled}` (admin). `/api/guardrails/test` 는 **global(필수) + filter_enabled=1 도메인**(또는 요청 `domains[]`)을 동시 평가.
- **카탈로그 상태**: `functional`(regex 실판정, global) / `heuristic`(regex 생성·휴리스틱 적용) / `catalog_only`(규칙 없음). `regex_rule_count` 컬럼으로 실판정 가능 규칙 수 노출(허위 기능 표기 방지 — §7.8.0 원칙 유지).

**impl/23 — 완전판정(LLM classifier) + 휴리스틱 과탐 완화**:
- **LLM classifier(완전판정)**: `guardrails_classifier_enabled=true`(기본 off·비결정적·LLM 구성 필요) 시, `/test`(및 확장 시 게이트)가 regex 판정 후 **규칙 데이터를 LLM 메뉴로 제시해 패러프레이즈/문맥 위반을 판정**한다. 도메인당 `guardrails_classifier_max_rules`(기본 40) 규칙을 우선순위(priority)순으로 제시, regex 기매치 규칙은 제외. 공유 LLM(`call_ollama`, Claude/Ollama 폴백) JSON 응답 파싱 → 위반 rule_id 를 매치로 병합. LLM 미구성/장애/파싱실패 시 regex 결과로 **무중단 degrade**(결정적 폴백 유지). 결과 `source="rules+llm"`.
- **휴리스틱 과탐 완화**: 생성 regex 의 오탐(단일 흔한 키워드, 예 "수수료")을 줄이기 위해 (1) **교차도메인 문서빈도(DF) 필터** — 여러 도메인 예시에 두루 등장하는 저정보 토큰 제외, (2) **단일 키워드 게이트** — 규칙당 키워드 2개 공기(AND) 우선, 단일 키워드는 저빈도(DF≤2)+길이≥3 일 때만 허용(그 외는 regex 미생성 → classifier 로 이관). 컴파일 데이터에 `description`·`priority` 추가(LLM 메뉴·정렬용).
- **완전판정 요약**: regex(결정적, 무LLM) + LLM classifier(패러프레이즈, 옵션)의 2단으로 도메인 규칙을 **완전 판정**한다. classifier off 환경에서도 regex 로 결정적 부분판정은 항상 동작.
- **룰셋 정제 — 실판정+휴리스틱 공존(impl/23)**: 각 규칙에 **detection mode 태그**(`mode`: `regex`=원본 실판정 / `heuristic`=생성 regex / `classifier`=LLM 전용)를 부여해 한 도메인 안에서 **실판정 규칙과 휴리스틱 규칙이 함께 적용**된다. 카탈로그는 `regex_rule_count`(실판정) + `heuristic_rule_count`(휴리스틱)를 분리 노출. 컴파일 시 rule_id·정규식 **중복 제거**로 룰셋을 정제.
- **필터적용 토글 견고화(impl/23)**: 프론트 토글을 **낙관적 업데이트 + 오류 표면화**로 개선(무음 실패 제거). 백엔드 `PUT /domains/{key}/filter` 정상 확인. **전체 선택/해제 토글**을 도메인 체크박스와 동일 형태로 `필터적용 N/M 도메인` 우측에 배치(필수 도메인 제외 일괄 적용).
- **emb_guardrails 룰셋 번들(impl/23)**: `addon-agents/zip/emb_guardrails/` ADDON 패키지에 컴파일 룰셋 데이터(`data/guardrails/`)를 **동봉**해 자기완결 배포되도록 함.

### 7.8.8 내장 에이전트 ADDON 패키징 (impl/22) — 누락된 emb_ 패키지 생성

추가 개발된 내장 에이전트(`marketplace`·`workflow`·`rag`·`playground`·`guardrails`)는 네이티브 라우터(Path A)로만 존재하고 `addon-agents/zip/` 에 **`emb_*` ADDON 패키지가 누락**돼 있었다(13종 보안 시스템 에이전트는 이미 존재). emb_ 규약(addon-agents/README §emb_ prefix)에 따라 `addon-agents/zip/emb_{marketplace,workflow,rag,playground,guardrails}/`(`-app.py`+`-meta.json`) + `.zip` 을 생성한다. `meta.json.base_agent` 는 원본 네이티브 라우터(`app/routers/router_{key}.py`, platform SeCuardian-Marketplace)를 가리키고, `-app.py` 는 로더 `/api/addon/emb_{key}` 마운트용 ADDON 판(대표 엔드포인트 이식, `from __future__ import annotations` 금지 — README 경고). 내장 에이전트 자체 key·표출명에는 emb_ 를 붙이지 않는다(패키징에만 적용).

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

- **레이아웃**: 좌측 nav — 상단 스크롤 그룹(대시보드 / AI 어시스턴트 / 내장 에이전트: 마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일) + **하단 고정: 사용자 관리(admin/supervisor) → 로그인 사용자 블록**(impl/12). 헤더 역할 스위처(dev: `X-User`/`X-Role`/`X-Tenant-Id` 헤더 주입, 실 JWT/IAM 은 F-GOV 대체). **impl/20: 별도 `에이전트 관리` 메뉴 제거 — 마켓플레이스 메뉴로 통합**.
- **화면**: 대시보드(`/api/agents` 카탈로그+헬스), **마켓플레이스 = 통합 에이전트 허브**(상단탭 `내장`(한정 7종: Orchestrator·AI 어시스턴트·마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일)/`시스템`(그 외)/`Addon`; 시스템 탭에 `자산 등록`+자산 카탈로그[로컬·원격 설치/해제]), 워크플로우(목록·**폼 기반 노드/엣지 편집기**·실행), 워크플로우 상세(상태·노드 타임라인·HITL 승인/거부·SSE), RAG(컬렉션·수집·하이브리드 검색). **내장 5종(마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일)은 `is_required=1`(REQUIRED) — 비활성 불가**(impl/20).
- **접근성(KWCAG 2.2, govtech 하드 요구)**: 워크플로우 캔버스 대신 **키보드 전용 폼/리스트 편집기**를 1차 제공(React Flow 캔버스는 E3 확장). 포커스 가시성, `aria-label`, 스킵 링크, `role="alert"` 오류.
- **화면 정렬 표준(impl/24)**: 모든 에이전트 화면 루트는 **`.page` 클래스**(`front/src/index.css`, `@apply w-full max-w-6xl p-4 sm:p-6`)로 **좌측정렬·반응형·최대폭 제한**을 통일한다. `mx-auto`(가운데 정렬) 금지. 신규 에이전트(내장·Addon) 개발 시 화면 최상위 컨테이너에 `.page` 를 적용하는 것을 기준으로 한다(addon-agents 가이드 반영). **예외: AI 어시스턴트(ChatPage)** 는 전체높이 채팅 레이아웃으로 현행 유지.

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

### 7.11.2 에이전트 설명 다국어 확장 + Local LLM 다양화 (SeCuardian R18-7·R19 준용, impl/33 · 물리 test/impl/31) — 사용자 요구(2026-07-09)

SeCuardian 구현(test/impl/55)을 **코드 복제**로 싱크 (§3 준용 계약 연장):

1. **다국어 설명 구조(R18-7)**: `tbl_agent_config.descriptions`(JSON `{"ko":..,"en":..}`, 타 언어
   키 추가만으로 확장) + 기동 시 레거시(`description`/`description_en`) 멱등 백필.
   meta.json `description` dict 형/레거시 형 모두 허용(업로드 시 정규화).
   `tbl_users.preferred_lang` + 마이페이지 선호언어 UI — 표시 fallback:
   `UI언어 → 선호언어 → ko → 첫 언어`(`pickDescription`). 로그인 시 UI locale 동기화.
2. **Local LLM 다양화(R19)**: `llm_providers`(ollama/llamacpp/vllm 공통 `chat`, OpenAI 호환) ·
   `llm_router`(작업별 라우팅 `llm_routes`: classify/tools/synthesize/domain/chat) ·
   `llm_metering`(`tbl_llm_usage` 원장 + `GET /api/llm/usage` 집계) ·
   `token_compress`(`llm_context_budget` 초과 시 head/tail 축약) ·
   `router_llm`(`/api/llm/providers·models·routes·usage`) — orchestrator/base_agent 전 경로 통합.
   compose profile `llamacpp`/`vllm`(기본 미기동 — 기존 Ollama 동작 무변경).
3. **비고**: SeCMP 자체 `services/llm.py`(공유 generate) 는 무변경 — 차후 `llm_providers` 경유
   통합은 로드맵.
4. **에이전트 표시명 다국어 (impl/35 · 물리 test/impl/33, 2026-07-09 추가)**:
   `tbl_agent_config.agent_names` JSON(`{"ko":..,"en":..}`) — SeCuardian impl/56 복제 싱크.
   내장 7종 시드에 en 표시명 병기(Marketplace/Workflow/RAG/Playground/Guardrails/AI Assistant/
   Orchestrator), 기동 시 `{"ko": agent_name}` 멱등 백필, meta.json `display_name` dict 형 허용.
   표시: AgentsPage 카드·AppLayout nav/헤더·Guardrails 에이전트 셀렉트 — descriptions 와 동일
   fallback 체인. `agent_name` 컬럼은 내부 참조용 유지.
5. **다국어 authoring 소스 전환 + jp 확장 (impl/39 · 물리 test/impl/37, 2026-07-09 오류 수정)**:
   impl/33 은 구조·프론트 fallback 을 갖췄으나 **authoring 소스가 여전히 split 컬럼**
   (`02_seed.sql` 이 `description`/`description_en` 기록, `descriptions` 는 boot backfill 파생)
   이라 **타 언어를 추가할 경로가 없어 사실상 미적용**이었다. 이를 다음과 같이 정정한다:
   - **`descriptions`/`agent_names` JSON = authoring 소스**: `02_seed.sql`(sqlite/pg) 이 내장 7종의
     `descriptions`·`agent_names` 를 **JSON 으로 직접 기록**(ko/en/**jp** 3언어)하고, split
     `description`/`description_en` authoring 은 제거(레거시 컬럼은 읽기 폴백용으로 스키마만 유지).
   - **orchestrator `_active_agents_block`**: 프롬프트용 설명을 split `description` 대신
     `descriptions`(ko→en→첫 언어)에서 읽는다.
   - **선호언어 확장**: 마이페이지 `PREFERRED_LANGS` 에 `jp` 추가(`locale.jp` 라벨 ko/en). UI 언어에
     해당 키가 없으면 `pickDescription` 이 선호언어(예: jp)로 표출 — 사용자 요구 명시.
   - **install 경로**: `router_marketplace` 설치 시 `tbl_agent_config` upsert 에 `descriptions`
     JSON 을 함께 기록(자산 ko 설명 + name/name_en → agent_names).
   - **정리**: `db.py` 중복 `backfill_descriptions` 정의 제거(완전판 1개 유지).
   - addon 경로(`_norm_descriptions` + upload `descriptions` 기록)는 이미 임의 언어 확장형 — 무변경.
6. **AI 어시스턴트 tool-call 루프 설정화 + 동일 오류 조기 종료 (impl/40 · 물리 test/impl/38, 2026-07-09)**:
   AI 어시스턴트가 API 오류 시 내부 자가수정 루프(하드코딩 6라운드)를 도는데, 존재하지 않는
   메서드 반복 호출(예: `PUT /api/agent-config/ai-assistant` → 405 × 6회) 시 LLM 호출이 낭비됨.
   - **`llm_tool_max_rounds`**(기본 6, 최소 1 클램프): tool-call 최대 루프 횟수를 시스템에서 관리.
     우선순위는 기존 LLM 설정과 동일 — `os.environ`(compose 주입) > **`.env.*` 파일**(pydantic
     `LLM_TOOL_MAX_ROUNDS`) > `tbl_settings`(시스템 설정 UI) > `config.py` 기본값.
     Anthropic tool-call 루프·Ollama `_ollama_tool_rounds` 양쪽 적용. seed(sqlite/pg) +
     SettingsPage `EDITABLE_KEYS` + `.env.example`·`.env.{local,dev,staging,prod}` 키 등재.
   - **동일 오류 조기 종료**: Ollama 루프에서 직전 실패와 `(method, path, status)` 시그니처가
     동일하면 자가수정 실패로 판단, 남은 라운드를 소진하지 않고 즉시 사용자 친화 오류 반환
     (재시도 1회는 허용 — 모델의 PUT→POST 등 자가수정 기회 보존).

### 7.11.3 내장 에이전트 화면 i18n 전면 적용 + 중복 타이틀 제거 (impl/34 · 물리 test/impl/32) — 사용자 요구(2026-07-09)

UI 언어 English 전환 시 내장 에이전트 화면들이 한국어로 남는 결함 + 본문 타이틀 중복 결함 수정.

1. **i18n 미적용 해소**: Workflow(목록·풀스크린 빌더·캔버스)·RAG·Playground·Guardrails·
   Marketplace·Dashboard 화면의 하드코딩 한국어 문자열 전부를 `useLocale` `t()` 키로 치환 —
   `locales/{ko,en}.json` 에 화면별 섹션(`workflow.*`/`rag.*`/`playground.*`/`guardrails.*`/
   `marketplace.*`/`dashboard.*`) 추가. ko/en 키 패리티 유지.
2. **에이전트 카드 라벨**: 마켓플레이스 허브 카드의 `nav_group`(DB 한국어 값: `기본 Agent`·
   `내장 에이전트` 등) 을 locale 매핑으로 표시(en: Basic Agent·Built-in Agent, 미등록 값은
   원문 유지). 에이전트 표시명(`agent_name`)은 DB 데이터로 유지(범위 밖).
3. **중복 타이틀 제거**: 상단 헤더(AppLayout)가 메뉴 타이틀을 표시하므로, 본문 h1
   (Workflow/RAG/Playground/Guardrails/Dashboard) 을 제거하고 **페이지 설명(`*.pageDesc`)만
   표시** — SeCuardian R18 '본문 중복 타이틀 제거' 표준 준용.

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
| **F-WEB** 웹 포털 | 🟡 | SPA: Login·Chat·Users·Settings·Profile·Addon(+modals) **+ Marketplace·Workflow·RAG·Playground·Guardrails(impl/3~6) + Dashboard(impl/8)**, nav/헤더타이틀/i18n(ko/en). 대시보드 요약+빠른링크. **impl/17: 실시간 위젯**. **impl/18: 워크플로우 React Flow 캔버스**. **impl/20: 에이전트 관리↔마켓플레이스 통합** — `에이전트 관리` nav 제거, `/marketplace` 가 통합 허브(`내장`/`시스템`/`Addon` 3탭)를 렌더(`/agents`→`/marketplace` 리다이렉트), 시스템 탭에 `자산 등록`+자산 카탈로그 편입. (tsc/build 0오류) | 편집형 캔버스·SSE 푸시·시계열 차트 로드맵 |
| **F-OPS** Makefile/DB 초기화 | 🟡 | 코어 타겟 `up/down/local-all/local-stop/dev-be/dev-fe/db-reset/seed/db-fresh/test/lint` + `ecosystem.config.js` + `scripts/{db_reset,seed,seed_local}.py` | ⚠ 삭제된 모니터 타겟(`keycloak-*`/`vault-*`/`harbor-*`/`wazuh-*`/`caddy-*`/`crowdsec-*` 등) 다수 잔존 → 정리 필요 |
| **F-ENV** 환경 분리 | 🟡 | `.env.{local,dev,staging,prod}` + `.env.example`(코어 **+ MARKETPLACE_*/TENANT_*/GUARDRAILS_*/VECTOR_BACKEND, impl/1**), `config.py`(동일 필드), `docker-compose*.yml`. 신규 marketplace 테이블 `tenant_id` 선반영 | dev/staging/prod `.env.*` 파일에 신규키 반영 확인, 그 외 신규 테이블 `tenant_id` 지속 적용 |
| **F-GOV** 거버넌스·보안 | 🟡 | `tbl_audit_log` 존재 | HITL 게이트/`tbl_hitl_approvals` 없음, OWASP 스코어카드·시크릿 매니저·SBOM 미구현 |
| **F-MP** Marketplace | 🟡 | **impl/1+3+9**: `router_marketplace.py`(catalog·install·uninstall·installs)+`router_marketplace_remote.py`(**원격 레지스트리 E1.5**: ping·catalog[캐시]·detail·install[다운로드→SHA256검증→로컬편입]), 2테이블(tenant_id), 단일 활성 버전+hot-deploy seam, **프론트**(로컬+원격 카탈로그). impl/10 원격 실 hot-deploy. **impl/14: 로컬 자산 실 ZIP 배포**(`marketplace_asset_blobs`+`deploy_zip` 공용). **impl/16: GPG 서명검증+mTLS**. 시험 20/20+14/14+8/8+10/10+10/10 PASS | 실 mTLS 핸드셰이크·GPG 키 로테이션 운영 절차(코드 완료) |
| **F-WF** Workflow | 🟡 | **impl/2+impl/3**: `workflow_engine.py`(async DAG: topo fire/prune·retry·HITL·템플릿), `router_workflow.py`(CRUD·run·nodes·hitl·cancel·SSE), 3테이블(tenant_id), **프론트**(`pages/workflow/`, a11y 폼 노드/엣지 편집기·실행·HITL 승인/거부·취소). 7노드·시험 21/21 PASS. **impl/18: React Flow 캔버스**(`WorkflowCanvas`, 읽기전용 DAG 시각화, a11y 폼 병존). **impl/25(물리 test/impl/23): 컴포넌트 팔레트**(§7.2.3) — `GET /api/workflow/components`(내장/시스템/Addon 에이전트별 OpenAPI 엔드포인트를 `{에이전트명}-{기능}` 컴포넌트로 노출, DB 신규테이블 없이 동적 탐지), `agent` 노드가 `config.path` 지정 시 `_exec_api_call` 재사용해 **실제 API 호출**(actor 토큰 전달, path 없으면 기존 스텁 하위호환), 신규 `http` 노드(외부 URL 호출). 8노드·시험 test/impl/23 PASS + 기존 21/21 회귀 무영향. **impl/26(물리 test/impl/24): webhook 수신 트리거**(§7.2.4) — `POST /workflows/{id}/trigger/webhook`(무인증, `X-Webhook-Secret` 검증), 생성자 역할 기반 임시 actor 토큰. **impl/27(물리 test/impl/25): 편집형 캔버스**(§7.2.5) — 노드 드래그 이동·핸들 연결·삭제, 좌표는 `definition_json.nodes[].position`(백엔드 무변경), a11y 폼과 상태 공유로 KWCAG 2.2 대체편집기 유지. **impl/28(물리 test/impl/26): Dify DSL Import 어댑터**(§7.2.6, 모드 A) — `POST /workflows/import/dify-dsl`, §7.2.2 노드 매핑표 구현, 미매핑 타입은 `transform` 플레이스홀더+`warnings[]`, `dify_dsl_source`/`dify_dsl_version` 컬럼 추가, 가져온 워크플로우는 `enabled=false` 로 생성(사람 검토 강제). **impl/29(물리 test/impl/27): webhook 보안 강화**(§7.2.4.1) — 시크릿 저장을 bcrypt→Fernet(재사용 가능한 대칭암호, 신규 의존성 없음)로 전환, `POST .../trigger/webhook/rotate`(재발급), `X-Webhook-Signature` HMAC-SHA256 서명 검증(선택, 하위호환), 워크플로우별 인메모리 rate limit(분당 30회 기본값, 단일 프로세스 한정). **impl/30(물리 test/impl/28): `enabled` 토글**(§7.2.7) — `PATCH /workflows/{id}` — Dify 가져오기(항상 비활성)를 검토 후 활성화하는 흐름, impl/24 시험이 DB 직접조작으로 우회했던 기존 갭 해소. **impl/32(물리 test/impl/30): 풀스크린 빌더**(§7.2.8) — `/workflow/builder(/:id)` 라우트, Flowise/Dify 준용 3분할(팔레트 drag&drop → React Flow 캔버스 커스텀 노드 → 타입별 인스펙터+엣지 `when` 편집), `PATCH /workflows/{id}` 를 name/description/definition_json 부분 편집으로 확장(definition 변경 시 version+1, enabled 단독 호출 하위호환). | code 노드·loop/sub-flow/cron·모드 B/C 유보(§7.2.3·7.2.4·7.2.5·7.2.6), llm 노드는 Ollama 폴백만(Claude 미연동), 빌더 undo/redo·실행 오버레이 유보(§7.2.8) |
| **F-RAG** RAG/지식베이스 | 🟡 | **impl/4**: `embeddings.py`(로컬 해싱 임베더)+`rag_pipeline.py`(청킹·BM25·RRF k=60)+`router_rag.py`(컬렉션·수집·하이브리드검색), 3테이블(tenant_id), **프론트**(`pages/rag/`). 식별자 질의 BM25 최상위 랭크 실증. **impl/15: pgvector 어댑터**(`vector_backend` resolve·pg DDL·`<=>` ANN, sqlite 폴백 유지). **impl/31(물리 test/impl/29): pgvector 실측 완료**(§7.5.1) — `docker-compose.yml` postgres 이미지를 `pgvector/pgvector:pg17` 로 영구 교체(구 이미지에 확장 없어 조용히 local 폴백하던 결함 수정), 실 컨테이너에서 Recall@10=1.000·p95=20.8ms 측정(목표 초과 달성). 시험 15/15+6/6+7/7 PASS | Qdrant·임베딩모델 교체(파라프레이즈 재평가 필요)는 로드맵 |
| **F-PG** Playground | 🟡 | **impl/5**: `router_playground.py`(공유 LLM 폴백 실호출 + RAG 컨텍스트 주입 + citations + degrade 무중단), `playground_runs` 테이블(tenant_id), **프론트**(`pages/playground/`, A/B 2-variant 동시실행+이력). 시험 13/13 PASS + tsc 0오류 | 비용(cost) 추적 없음(Claude 미연동), eval 실행 로드맵 |
| **F-GRD** Guardrails | 🟡 | **impl/6+impl/7**: `guardrails_detector.py`(**global 도메인 PII/신용정보 13종 정규식 판정 — 로컬 재구현**, Luhn 카드검증·마스킹), `router_guardrails.py`(도메인 카탈로그·에이전트 토글·test·decision log), **`guardrails_gate.py`(Orchestrator 실시간 게이트 — `_exec_api_call` 모듈 속성 재바인딩으로 orchestrator.py 무변경 유지하며 6개 내부 호출지점 가로챔, 입력/출력 양방향 판정+치환+이중감사)**, 3테이블, 프론트. 13종 전수 실판정 + 게이트 실동작 검증. **impl/11: block/escalate 승격**(고위험 시크릿/신용정보/국가식별번호 1종→block, 2종+→escalate; 게이트 실차단 HTTP 403 [BLOCKED] 검증, 저위험은 redact 하위호환). **impl/13: MCP Server 프록시**(`guardrails_mcp.validate`, MCP 우선·실패시 로컬 폴백, `/test`·게이트 통일). 시험 20/20+15/15+14/14+6/6 PASS | 실 wise-Guardrails MCP 통합시험은 서버 가동 필요(계약·폴백 완료). 25종 업종 판정기는 SeCMP 책임 밖 |

### 9.2 SeCuardian 준용 계약(§3) 상태

| 계약 | 상태 | 비고 |
|---|---|---|
| Orchestrator | ✅ | `app/agents/orchestrator.py` 클론 부팅 검증 |
| AI Assistant | ✅ | Orchestrator tool-calling 경로 |
| Agent 관리(4테이블) | ✅ | `tbl_agent_config`·`tbl_addon_agents`·`tbl_addon_agent_capabilities`·`tbl_agent_registry` 잔존 |
| **Addon Agent 핫디플로이** | ✅ **복원(impl/1)** | 사용자 결정(A): `router_addon_agent.py`·`app/addon_agent_loader.py`·`addon-agents/` 원본 복원, `main.py` `addon_init`/`addon_guard` 재배선, `router_mcp`/`router_agent_config` addon 연동 원복. Marketplace/Playground/Workflow 가 차후 소비 |
| **다국어 설명 + Local LLM 다양화** | ✅ **싱크(impl/33)** | SeCuardian R18-7·R19(test/impl/55) 코드 복제 — `descriptions` JSON·`preferred_lang`·`llm_providers/router/metering/token_compress`·`router_llm`·compose profile llamacpp/vllm (§7.11.2) |

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
| E1.5 원격 레지스트리 | ✅ | impl/9+10: `router_marketplace_remote.py`(ping·catalog[캐시]·detail·install)+프론트. **impl/10: 다운로드 ZIP→SHA256→`/api/addon-agents/upload` in-proc 재사용→실 무중단 hot-deploy**(시험 14/14+8/8). 잔여(범위 밖): 로컬자산 ZIP 저장, GPG 서명, mTLS CA 번들 |
| E2 Workflow 엔진 | 🟡 | impl/2+3: DAG 실행기·상태머신·retry·HITL·SSE+3테이블+a11y 폼 프론트(시험 21/21+tsc/build) |
| E3 Workflow Designer | 🟡 | a11y 폼 노드/엣지 편집기 완료(impl/3, PRD §7.11 1차 요구사항 충족). **impl/25: 컴포넌트 팔레트**(에이전트별 API를 클릭 삽입), **impl/26: webhook 수신 트리거**(§7.2.4), **impl/27: 편집형 캔버스**(§7.2.5, 폼과 상태 공유), **impl/32: 풀스크린 빌더**(§7.2.8, 팔레트 drag&drop·인스펙터·기존 워크플로우 편집) 추가. code 노드는 로드맵 확장(§7.2.3·7.2.4) |
| E3.5 Dify Import(P5) | 🟡 | **impl/28(물리 test/impl/26): 모드 A 착지**(§7.2.6) — 애초 P5 로드맵이었으나 사용자 요구로 조기 구현. 모드 B(Delegate)/C(Round-trip)는 여전히 로드맵 |
| E4 RAG | 🟡 | impl/4: 청킹·해싱임베더·BM25·RRF+3테이블+프론트(시험 15/15+tsc). **impl/31: pgvector 실측 완료**(Recall@10=1.000·p95=20.8ms, §7.5.1). Qdrant·임베딩모델 교체(파라프레이즈 재평가)는 로드맵 |
| E5 Playground | 🟡 | impl/5: LLM 폴백 실행+RAG 컨텍스트 주입+A/B 프론트(시험 13/13+tsc). cost 추적·eval 로드맵 |
| E6 거버넌스 | 🟡 | `tbl_audit_log` + Guardrails 이중감사(`guardrails_decision_log`, impl/6). HITL 게이트(F-WF 내)는 있으나 별도 `tbl_hitl_approvals`·OWASP 스코어카드 없음 |
| E7 하드닝 | ⬜ | — |
| E8 Guardrails | 🟡 | impl/6+7+11: **global 13종 로컬 판정기**+3테이블+토글+decision log+프론트+**Orchestrator 게이트 실동작**+**block/escalate 승격**(시험 20/20+15/15+14/14). 잔여: MCP 프록시 연동, 25종 판정기(SeCMP 책임 밖) |

### 9.5 권장 다음 단계

**§9.5 잔여 6항목(F-WF 캔버스·F-RAG pgvector·F-GRD MCP·로컬 실ZIP·대시보드 위젯·GPG/mTLS) impl/13~18 로 전부 착지.**
**impl/25(물리 test/impl/23) — F-WF 컴포넌트 팔레트(§7.2.3) 착지.**
**impl/26(물리 test/impl/24) — F-WF webhook 수신 트리거(§7.2.4) 착지.**
**impl/27(물리 test/impl/25) — F-WF 편집형 캔버스(§7.2.5) 착지.**
**impl/28(물리 test/impl/26) — F-WF Dify DSL Import 모드 A(§7.2.6) 착지.**
**impl/29(물리 test/impl/27) — F-WF webhook 보안 강화(§7.2.4.1) 착지.**
**impl/30(물리 test/impl/28) — F-WF `enabled` 토글 PATCH(§7.2.7) 착지.**
**impl/31(물리 test/impl/29) — F-RAG pgvector 실측 착지**(§7.5.1, Recall@10=1.000·p95=20.8ms, 사용자
"순차적으로 진행" 지정 3번째·마지막 항목).
**impl/32(물리 test/impl/30) — F-WF 풀스크린 워크플로우 빌더(§7.2.8) 착지**(impl/27 미니 캔버스
실사용 불가 피드백 → Flowise/Dify 준용 재구현, PATCH 부분 편집 확장 포함).
남은 것은 외부 인프라 실측·운영 항목 + 아래 신규 유보 항목:

1. ~~실 인프라 실측(pgvector)~~ — **완료(impl/31, §7.5.1)**. mTLS 핸드셰이크, 실 wise-Guardrails MCP Server 통합은
   여전히 별도 인프라(사설 CA / MCP 서버) 배포 환경에서 검증 필요(코드 경로·폴백은 완료·시험됨).
2. **임베딩 모델 교체** — 로컬 해싱 임베더 → sentence-transformers/OpenAI(embedding_version 고정, dual-write 마이그레이션).
3. ~~편집형 워크플로우 캔버스~~ — **완료(impl/27, §7.2.5)**. a11y 폼이 KWCAG 2.2 대체편집기로 계속 병행.
4. **멀티테넌시 namespace/physical 구현**(P5), Qdrant 확장 — 로드맵. ~~Dify DSL Import(E3.5)~~ — **모드 A 완료(impl/28, §7.2.6)**, 모드 B/C 는 로드맵.
5. **운영 문서화** — GPG 공개키 배포·로테이션, mTLS 인증서 발급 절차(`docs/marketplace-remote.md`). **+ webhook**: `JWT_SECRET_KEY` 교체 시 기존 webhook 시크릿 전부 무효화되므로 재발급(rotate) 절차 문서화 필요(impl/29, §7.2.4.1).
6. **code 노드**(§7.2.3 유보) — 샌드박스 보안 검토 선행 필요(§3 하지 않을 것). ~~webhook 수신 트리거~~ — **완료(impl/26, §7.2.4)**. ~~webhook 로테이션·HMAC·rate limit~~ — **완료(impl/29, §7.2.4.1, rate limit 은 단일 프로세스 인메모리 한정)**.
7. ~~워크플로우 `enabled` 토글 PATCH 엔드포인트~~ — **완료(impl/30, §7.2.7)**.

> 완료 이력: Orchestrator 게이트(impl/7)·대시보드(impl/8)·block/escalate(impl/11)·MCP 프록시(impl/13)·
> 로컬 실ZIP(impl/14)·pgvector 어댑터(impl/15)·GPG+mTLS(impl/16)·대시보드 실시간 위젯(impl/17)·React Flow 캔버스(impl/18).

### 9.6 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-07-10 | v0.39 | **impl/46(물리 `test/impl/44`) — §7.11.2-5 확장: 자산 계층 다국어 dict 일원화 + 설치됨 탭 UserManager 중복 해소**(사용자 결함 보고: "일부만 dict 적용·카탈로그 카드 raw repr 노출·UserManager 2중 표시" + 설계 지침: "split 컬럼(description_en) 금지 — `{'ko','en'}` key:value 데이터 + 공통 파싱 함수로 언어 확장 시 코드 수정 없어야 함"). ① 전 자산 meta.json 29종 `display_name`/`description` = `{"ko","en"}` dict 통일 + zip 재빌드 ② 공통 파서 `app/core/i18n.py`(`norm_descriptions`/`parse_lang_map`/`lang_json`) 신설 — addon 업로드·마켓플레이스 등록(ZIP/API/원격)·시드 전 경로 일원화(종전 `str(dict)` 저장 → 카탈로그 카드 `{'ko': …}` repr 노출 결함 수정) ③ `marketplace_assets.names/descriptions` JSON 컬럼(init+멱등 ALTER) — 카탈로그 카드 프론트 공통함수(`parseLangMap`+`pickDescription`) 언어 전환 반영, 등록 모달 dict 전송 ④ asset_key/config 키 소문자 통일 + `seed-assets` 멱등 정규화(대소문자 키·config 중복 행·빈 nav_group·repr 오염 행 복구) — 설치됨 탭 UserManager/usermanager 2중 카드 해소 ⑤ SeCuardian 복제 싱크(`core/i18n.py`·`locale.ts`·`seed_security` agent_names JSON·`addon-agents/zip` 보안 13종 meta+zip) | app/core/i18n.py 신규, app/db.py, sql/{sqlite,pg}/01_init.sql, app/routers/{router_marketplace,router_marketplace_remote,router_addon_agent,router_agent_config}.py, scripts/{seed_assets,seed_security}.py, marketplace-assets(29종 meta+zip), front(store/locale.ts·api/marketplace.ts·MarketplacePage.tsx·AssetRegisterModal.tsx·locales), SeCuardian(core/i18n.py·routers 2종·seed_security.py·locale.ts·addon-agents/zip 13종), README(.en), test/impl/44 |
| 2026-07-10 | v0.38 | **impl/45(물리 `test/impl/43`) — §7.6.4-5·6 설치됨 탭 카테고리 그룹핑 + 해제 잔존 결함 수정**(사용자 결함 보고: 해제해도 설치됨 탭 잔존 + "카탈로그처럼 builtin·security·utilities 분류·정렬" 재확인). ① 설치됨 탭 카탈로그 매칭을 **대소문자 무시**로 정정 — addon upload 가 config 키를 소문자화(`usermanager`)해 자산 키(`UserManager`)와 불일치 → builtin 오분류 잔존하던 결함 해소 ② 설치됨 탭을 카탈로그와 동일한 **카테고리 섹션 그룹**(builtin 먼저 → security → utilities → general …)으로 표시, 섹션 내 정렬 = builtin 기존 순서·카탈로그 그룹 카탈로그 순서 ③ `mp.cat.builtin` 로케일 키 추가 | front(AgentsPage.tsx·locales), README(.en), test/impl/43 |
| 2026-07-10 | v0.37 | **impl/44(물리 `test/impl/42`) — §7.6.5 해제 시 hot-deploy 잔재 완전 정리 + 상단 설명**(사용자 결함 보고: 해제해도 좌측 네비 메뉴·`addon-agents/deployed` 잔존). ① `agent.pageDesc` 에 자산 카탈로그 설명 포함(ko/en) ② marketplace uninstall = installs 비활성+config disable **+ 완전 undeploy**(addon 테이블 DROP·deployed 디렉터리·front tsx·MCP·`tbl_addon_agents` 행 삭제·web 재빌드) — `delete_addon` 본문을 `_remove_addon_artifacts` 공용 헬퍼로 분리 재사용, addon 키 대소문자 무시 매칭 ③ 설치/해제 시 `agentConfigChanged` 발행 → 네비 즉시 동기화 ④ `scripts/cleanup_addon_remnants.py`(=`make cleanup-addons`) 잔재 일괄 정리(멱등) — dev 환경 잔재(고아 deployed 14→정리) 적용 ⑤ addon-agents/ 는 deployed/ 런타임 필수라 유지 결정 | app/routers/{router_marketplace,router_addon_agent}.py, scripts/cleanup_addon_remnants.py, Makefile, front(MarketplacePage.tsx·locales), README(.en), test/impl/42 |
| 2026-07-10 | v0.36 | **impl/43(물리 `test/impl/41`) — §7.6.4 마켓플레이스 3탭 재구성**(사용자 요구: builtin 과 자산등록 에이전트가 한 탭에 혼재). ① 탭 = `자산 카탈로그`(기본) / `에이전트(설치됨)` / `Addon 에이전트` — 종전 `내장 에이전트` 탭 분해 ② 카탈로그 탭 현행 유지(카테고리별 목록·`+ 추가`·자산 등록) ③ 설치됨 탭 = 카탈로그 외 config(기본·내장) + **활성 설치**(installed=true) 카탈로그 에이전트만 — 설치/해제 시 `marketplaceChanged` 이벤트로 즉시 표시/숨김 ④ 좌측 네비 노출은 기존 hot-deploy 무변경 ⑤ 설치됨 정렬 = 기본·내장 우선 후 카탈로그 표시 순서 동일 | front(AgentsPage.tsx·MarketplacePage.tsx·locales), README(.en), test/impl/41 |
| 2026-07-10 | v0.35 | **impl/42(물리 `test/impl/40`) — §7.6.3 카탈로그 기본 등록 + 카테고리별 추가 등록**(사용자 요구). ① security·utilities 만 카탈로그 기본 등록 대상(addon·builtin 제외) — dev DB 에 `make seed-assets` 실행으로 utilities 6종 편입 완료 ② `make db-fresh` 체인 확장(seed → seed-security → seed-assets)으로 초기화 직후에도 등록 상태 보장 ③ 카탈로그 카테고리 섹션 헤더에 `+ 추가` 버튼(admin) — category 프리셋 자산 등록 모달(에이전트 메타/ZIP 다중 추가) ④ 상단 `자산 등록` = 카탈로그 생성 + 자산 등록(category 자유 입력, 기본 general) ⑤ `AssetRegisterModal` 독립 컴포넌트 분리(category prop), 백엔드 무변경 | .docs/SeCMP-PRD.md, Makefile, front(marketplace/AssetRegisterModal.tsx 신규·MarketplacePage.tsx·AgentsPage.tsx·locales), README(.en), test/impl/40 |
| 2026-07-10 | v0.34 | **impl/41(물리 `test/impl/39`) — §7.6.2 자산 등록 UX 개선 + 카테고리 카탈로그**(사용자 요구). ① `자산 등록` asset_key 자동부여 — 모달 입력 제거, name(예: security) 슬러그화로 서버 자동 생성(충돌 시 `-2` 접미, 명시 시 하위호환) ② Addon ZIP **다중 첨부** — 신규 `POST /api/marketplace/catalog/zip`(files[]) 이 ZIP 별 `{key}-meta.json` 파싱→자산 등록+블롭 저장 멱등 수행 ③ 자산 카탈로그 category(security·utilities…) 별 그룹 표시 ④ `scripts/seed_assets.py`(=`make seed-assets`) — security·utilities 스캔 시드(미등록만 INSERT, utilities 6종 카탈로그 편입) ⑤ 등록 완료 시 `marketplaceChanged` 이벤트로 카탈로그 즉시 갱신 ⑥ README(.en) 설치/미설치 동작 상세화 | app/routers/router_marketplace.py, scripts/seed_assets.py, Makefile, front(api/marketplace.ts·AgentsPage.tsx·MarketplacePage.tsx·locales), README(.en), test/impl/39 |
| 2026-07-09 | v0.33 | **impl/40(물리 `test/impl/38`) — AI 어시스턴트 tool-call 루프 설정화 + `.env.*` 지원**(§7.11.2-6, 사용자 요구: "오류 loop 횟수를 시스템에서 관리 + `.env.*` 로 설정"). ① `llm_tool_max_rounds` 설정 신설(기본 6, 최소 1) — `config.py` 필드 + `_db_llm_settings` 플럼빙(`LLM_TOOL_MAX_ROUNDS` env 맵·DB 키·pydantic 기본값) + seed(sqlite/pg) + SettingsPage `EDITABLE_KEYS`, Anthropic/Ollama tool-call 루프 양쪽 적용 ② `.env.example` 활성 키 + `.env.{local,dev,staging,prod}` 키 등재(pydantic env_file 경로로 설정 가능) ③ 효율 개선 — Ollama 루프 동일 `(method, path, status)` 오류 반복 시 조기 종료(405 × 6회 → 2회, 재시도 1회 허용). 시험 test/impl/38 | app/core/config.py, app/agents/orchestrator.py, sql/{sqlite,pg}/02_seed.sql, front/src/pages/settings/SettingsPage.tsx, .env.example, .env.{local,dev,staging,prod}, test/impl/38 |
| 2026-07-09 | v0.32 | **impl/39(물리 `test/impl/37`) — 다국어 설명 authoring 소스 전환 + jp 확장**(§7.11.2-5, 사용자 오류 보고: "확장 구조 개선됐다 했으나 미적용 — descriptions 를 split 컬럼 아닌 `{"ko","en","jp"}` JSON 으로, 언어셋 없으면 선호언어 표출"). impl/33 은 구조·프론트 fallback·선호언어 UI 를 갖췄으나 **authoring 소스가 여전히 split 컬럼**이라 타 언어 추가 경로가 없었음. 정정: ① `02_seed.sql`(sqlite/pg) 내장 7종 `descriptions`·`agent_names` **JSON 직접 저자(ko/en/jp)**, split `description`/`description_en` authoring 제거(레거시 컬럼은 읽기 폴백용 스키마만 유지) ② orchestrator `_active_agents_block` — `descriptions`(ko→en→첫 언어)에서 프롬프트 설명 읽기 ③ 마이페이지 `PREFERRED_LANGS` 에 `jp` 추가(`locale.jp` 라벨) — UI 언어 키 없을 때 선호언어로 표출 ④ `router_marketplace` install upsert 에 `descriptions` JSON 기록 ⑤ `db.py` 중복 `backfill_descriptions` 제거. addon 경로는 이미 확장형 무변경. 시험 test/impl/37(격리 sqlite: 시드 jp·API·pickDescription jp fallback·orchestrator block·dedupe) | sql/{sqlite,pg}/02_seed.sql, app/db.py, app/agents/orchestrator.py, app/routers/router_marketplace.py, front(store/locale.ts·profile/ProfilePage.tsx·locales), test/impl/37 |
| 2026-07-09 | v0.31 | **impl/35(물리 `test/impl/33`) — 에이전트 표시명 다국어 agent_names 싱크**(§7.11.2-4, 사용자 요구 "agent_name 도 descriptions 방식으로 확장"). SeCuardian impl/56 복제: `tbl_agent_config.agent_names` JSON 컬럼(init+멱등 ALTER+`{"ko": agent_name}` 백필), **내장 7종 시드 en 표시명**(마켓플레이스→Marketplace 등 — en UI 에서 한국어 표시명 노출 해소), meta.json `display_name` dict 형 정규화·배포 동기·addon 목록 노출, `_templates` 6종 dict 화 재패키징. 프론트: AgentsPage `nameOf`(10개소)·AppLayout nav/헤더(names dict 상태 보존, locale 전환 즉시 반영)·GuardrailsPage 에이전트 셀렉트. 시험 test/impl/33 4/4 PASS(격리 sqlite 기동·시드·API + import/tsc) |
| 2026-07-09 | v0.30 | **impl/34(물리 `test/impl/32`) — 내장 에이전트 화면 i18n 전면 적용 + 중복 타이틀 제거**(§7.11.3, 사용자 결함 보고: English 전환 시 미적용 + 본문 타이틀 2중 표시). ① Workflow(목록·풀스크린 빌더·캔버스)·RAG·Playground·Guardrails·Marketplace·Dashboard 8파일의 하드코딩 한국어 137개를 `t()` 키로 치환 — `locales/{ko,en}.json` 에 wf/wfb/rag/pg/mp/dash/grd 섹션 신설(키 패리티 검증 0건 차이). WorkflowBuilderPage `NODE_META` label/desc 를 locale 키로 분리, GuardrailsPage `statusBadge` 키 반환화 ② 본문 h1 5화면 제거 → `pageDesc` 만 표시(SeCuardian R18 '본문 중복 타이틀 제거' 표준 준용, AppLayout 헤더가 타이틀 단독 표시) ③ AgentsPage `nav_group` 칩(DB 한국어 값) locale 매핑(`기본 Agent`→Basic Agent 등) — **SeCuardian 에도 동기 반영** ④ Dashboard 에이전트 설명 `pickDescription`(R18-7 fallback) 적용, `nav.aiAssistant` ko 오타 수정. 시험 test/impl/32 6/6 PASS(tsc·build·패리티·잔존 0건) |
| 2026-07-09 | v0.29 | **impl/33(물리 `test/impl/31`) — SeCuardian R18-7·R19 복제 싱크**(§7.11.2, 사용자 요구 "SeCuardian 구현 후 Marketplace 에 코드 복제 싱크"). ① **다국어 설명 확장 구조**: `tbl_agent_config.descriptions` JSON(init+멱등 ALTER+기동 백필), meta.json dict 형 정규화(레거시 호환), `tbl_users.preferred_lang`+`GET/PATCH /auth/me`+마이페이지 선호언어 UI, `pickDescription` fallback 체인(UI→선호→ko→첫 언어), 로그인 locale 동기화, `_templates` 6종 dict 형 재패키징 ② **Local LLM 다양화**: `llm_providers`(ollama/llamacpp/vllm)·`llm_router`(작업별 라우팅)·`llm_metering`(`tbl_llm_usage`+집계)·`token_compress`·`router_llm`(4 엔드포인트), orchestrator/base_agent 통합, compose profile llamacpp/vllm, 설정 seed 7종, SettingsPage 사용량 요약, ChatPage 동적 모델 목록. 싱크 방법: 동일 13종+신규 6종 복사, 분기 11종 patch, main.py 3개소 수동 병합(SeCMP 고유 guardrails 배선 보존). 시험 test/impl/31 6/6 PASS(격리 sqlite 기동·API 검증 + import/ruff/tsc/compose 정적 검증) |
| 2026-07-09 | v0.28 | **impl/32(물리 `test/impl/30`) — F-WF 풀스크린 워크플로우 빌더**(사용자 요구, §7.2.8). impl/27 편집형 캔버스가 생성 패널 내 320px 보조 위젯에 그쳐 "현재 구현 코드로는 사용할 수 없다"는 사용자 피드백 접수 — `.docs/Perplexity-Workflow/`·No-code/Low-code·Marketplace 리서치의 **팔레트→캔버스 drag&drop→인스펙터** 3분할 빌더 패턴(Flowise/Dify/n8n 공통)을 준용해 재구현. **코드 복제 없이 UX 패턴만 참조**(React Flow MIT 자체 구현, 상용/추가조건 라이선스 구성요소 제외). (1) 프론트 신규 `/workflow/builder(/:id)` + `WorkflowBuilderPage` — 좌측 팔레트(8노드+§7.2.3 컴포넌트, HTML5 드래그+클릭 삽입), 중앙 풀높이 캔버스(타입별 커스텀 노드), 우측 인스펙터(타입별 구조화 폼+JSON 폴백+엣지 `when` 편집 — §7.2.5 유보 해소). (2) 백엔드 `PATCH /workflows/{id}` 부분 편집 확장(name/description/definition_json, definition 변경 시 version+1, `{"enabled"}` 단독 하위호환 — §7.2.7 범위 확장). KWCAG 2.2 는 기존 a11y 폼 병행+인스펙터 표준 폼으로 유지. 시험 test/impl/30. **후속 결함 수정(같은 날)**: 캔버스 노드 미표시 버그 — React Flow v12 는 노드 측정값(`measured`)이 컨트롤드 상태에 반영돼야 `visibility:hidden` 을 해제하는데, 매 렌더 rfNodes 를 도메인 상태에서 재생성해 measured 가 소실(impl/18 부터 잠재, 정적 검증만 수행돼 미발견). 빌더는 RF 상태를 단일 진실로 전환, `WorkflowCanvas` 는 measured 보존 merge-sync 로 수정 — headless Chromium E2E(팔레트 삽입→저장→재로드→폼 동기화)로 실측 검증(test/impl/30 §D). |
| 2026-07-09 | v0.27 | **impl/31(물리 `test/impl/29`) — F-RAG pgvector 실측 벤치마크**(사용자 요구·승인, §7.5.1). 사용자가 "순차적으로 진행" 지정한 후속 3항목의 마지막(webhook 보안 강화→enabled 토글→**pgvector 실측**). 도커 이미지 pull+실 컨테이너 기동이 필요해 별도 승인 후 진행. **발견**: `docker-compose.yml` postgres 서비스가 plain `postgres:17-alpine` 이미지라 `vector` 확장이 없었고, impl/15 `ensure_pg_schema()` 가 예외를 삼키고 조용히 local 폴백하는 설계라 지금까지 드러나지 않았던 잠재 결함 — **`pgvector/pgvector:pg17` 로 영구 교체**(임시 우회 아님). `docker compose up -d postgres` → `CREATE EXTENSION vector`(0.8.4) 확인 → `ENV=dev VECTOR_BACKEND=pgvector` 로 앱 부팅해 `vector_backend.resolve()="pgvector"` 실경로 최초 활성화 → 식별자 질의 세트(N=40, impl/4 방법론)로 실 `/api/rag/*` HTTP 경로 실측: **Recall@10=1.000**(목표 ≥0.89 초과 달성), **p95=20.8ms**(목표 ≤250ms, 약 12배 여유). 인프라 검증(이번 목표)과 임베딩 품질(파라프레이즈 재평가, 별도 로드맵)을 분리 보고 — PRD §5 KPI 표에 실측치 반영(더 이상 전량 `가정:` 아님). 벤치마크 후 `docker compose stop postgres` 로 정리(볼륨 보존). 시험 test/impl/29, 기존 test/impl/4·15(sqlite 경로) 회귀 무영향. |
| 2026-07-09 | v0.26 | **impl/30(물리 `test/impl/28`) — F-WF `enabled` 토글 PATCH 엔드포인트**(사용자 요구, §7.2.7). 사용자가 "순차적으로 진행" 지정한 후속 3항목의 2번째. `PATCH /api/workflows/{id}`(admin/supervisor, `{"enabled": bool}`) 신설 — impl/24 시험이 DB 직접조작으로 우회했던 기존 갭 해소, impl/28(Dify DSL Import, 항상 `enabled=false` 생성) 을 검토 후 활성화하는 실사용 흐름 지원. 1차 범위는 `enabled` 토글만(이름/정의 편집은 범위 밖). 프론트 `WorkflowPage.tsx` 에 활성화/비활성화 토글 버튼 추가. 시험 test/impl/28, 기존 test/impl/2·23·24·26·27 회귀 무영향. |
| 2026-07-09 | v0.28 | **§7.6.1-7 자산 디렉터리 재구성 — `addon-agents/zip` 폐지(impl/38 · 물리 `test/impl/36`)**(사용자 요구). 모든 자산 소스를 `marketplace-assets/<카테고리>/` 로 일원화: security(13, 기존)·builtin(5: marketplace·workflow·rag·playground·guardrails)·addon(5: 스캐폴드 템플릿 Board·RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent)·utilities(6: UserManager·server-shell·ai-traffic-monitor·caddy-proxy·grafana-dashboard·truffle-scan). `addon-agents/{zip,_templates}` 폐지(deployed/ 만 잔존). `router_addon_agent.py` 템플릿 경로 → `marketplace-assets/addon`(`_ZIP_CATALOG`/`_ZIP_TEMPLATE_NAMES` fallback 제거, 목록/다운로드/스캐폴더 무변경). marketplace-assets 는 `.dockerignore` 미제외로 이미지 포함 | addon-agents/*, marketplace-assets/*, router_addon_agent.py, README(.en), addon-agents/README(.en), test/impl/36 |
| 2026-07-09 | v0.27 | **§7.6.1-6 오류 수정 — emb_ 규약 폐지(impl/37 · 물리 `test/impl/35`)**(사용자 요구). ① 전 패키지 `emb_` prefix 제거(emb_rag→rag 등) — `addon-agents/zip/` 6종 + `marketplace-assets/security/` 13종 rename(디렉터리·zip·내부 파일명·meta key), `seed_security.py` 블롭 경로 `{key}.zip` 동기 ② prefix 없는 업로드는 config 키 선재 시 is_builtin=1 등록(기존 호환 경로) ③ SeCuardian `addon-agents/zip/` 은 보안 13종(무prefix)만 잔류 — 템플릿 5종·server-shell·순수 4종은 SeCMP 이전 확인 후 삭제(SeCuardian PRD §20.4) |
| 2026-07-09 | v0.26 | **§7.6.1 신규 요구 등재 — 에이전트 통합 관리(impl/36 · 물리 `test/impl/34`)**(사용자 요구). ① 내장/시스템 탭 → `내장 에이전트` 단일 탭 통합(자산 카탈로그·자산 등록 버튼 편입, Addon 탭 무변경) ② 보안 내장 13종을 `marketplace_assets`(category=security) 자산 카탈로그로 이관 — emb_ 패키지는 `addon-agents/zip` → `marketplace-assets/security/` 이동, `make seed-security`(`scripts/seed_security.py`) 신설, `make seed` 는 기반 시드만 ③ 자산 등록 모달에 addon ZIP(스캐폴드 형식) 첨부 업로드 UI(기존 `/catalog/{key}/zip` 재사용) ④ `_templates` Board 제외 5종 → `zip/` 이동(fallback 으로 기능 유지) ⑤ 전수 비교: 관리 주체 = SeCuardian-Marketplace 확정(SeCuardian PRD §20 연동) |
| 2026-07-09 | v0.25 | **impl/29(물리 `test/impl/27`) — F-WF webhook 보안 강화**(사용자 요구, §7.2.4.1). impl/25~28 순차 4항목 완료 후 사용자가 "순차적으로 진행"으로 지정한 §9.5 잔여 3항목의 1번째. 시크릿 저장을 **bcrypt(단방향, impl/26) → Fernet 대칭암호**(`cryptography`, `python-jose[cryptography]` 통해 이미 설치되어 신규 의존성 없음)로 전환 — 로테이션·HMAC 검증에 평문 복원이 필요했기 때문(키는 `JWT_SECRET_KEY` 파생, 신규 env 불요). (1) `POST /workflows/{id}/trigger/webhook/rotate`(admin/supervisor) 신설 — 재발급, 구 시크릿 즉시 무효. (2) `X-Webhook-Signature: sha256=<hmac>` 헤더 지원(GitHub 컨벤션) — 기존 `X-Webhook-Secret` 과 **둘 중 하나만 유효하면 통과**(하위호환). (3) 워크플로우별 인메모리 고정윈도우 rate limit(기본 분당 30회, `settings.workflow_webhook_rate_limit_per_min`) — 초과 시 429, 단일 프로세스 한정임을 리스크로 명시. impl/26 발급 workflow 는 재발급(rotate) 1회 필요(하위 마이그레이션 없음, 로컬/개발 단계라 실사용 영향 없음). 시험 test/impl/27, 기존 test/impl/2·23·24·26 회귀 무영향. |
| 2026-07-09 | v0.24 | **impl/28(물리 `test/impl/26`) — F-WF Dify DSL Import 어댑터 모드 A**(사용자 요구, §7.2.6). 지난 impl/25~27 순차 진행의 3번째(webhook→편집형 캔버스→Dify DSL Import)이자 마지막 지정 항목. §7.2.2 에 이미 문서화된 노드 매핑표(2026-07-08 Dify 공식문서 실측 근거)를 구현: `POST /api/workflows/import/dify-dsl` 신설, `app/services/dify_dsl_adapter.py`(PyYAML 파싱, 기존 의존성 재사용·신규 설치 없음)가 `start/llm/if-else/knowledge-retrieval/http-request/tool/answer/end` 를 SeCMP 8노드로 매핑, **`code`·미인식 타입은 크래시 대신 `transform` 플레이스홀더 + `warnings[]`** 로 명시(§3 code 노드 유보 원칙 유지). Dify 원본 노드 id 보존으로 엣지 정합성 자동 유지, `sourceHandle` true/false → SeCMP `when`. **가져온 워크플로우는 항상 `enabled=false` 로 생성**(사람 검토 강제). 데이터 모델: `workflows.dify_dsl_source`/`dify_dsl_version` 컬럼 추가(sqlite/pg `01_init.sql` + `app/db.py` 컬럼 마이그레이션 양쪽 반영, 기존 로컬 DB 무중단 확장). 시험 test/impl/26(합성 Dify DSL 픽스처로 매핑 전종류 검증), 기존 test/impl/2·23·24 회귀 무영향. |
| 2026-07-09 | v0.23 | **impl/27(물리 `test/impl/25`) — F-WF 편집형 캔버스**(사용자 요구, §7.2.5). 지난 impl/25·26 완료 후 접수된 유보 항목을 사용자가 지정한 순서(webhook→편집형 캔버스→Dify DSL Import→기타)의 2번째. `WorkflowCanvas.tsx` 를 읽기전용 시각화에서 편집형으로 승격 — React Flow `onNodesChange`/`onEdgesChange`/`onConnect` 로 노드 드래그 이동·핸들 연결·Backspace/Delete 삭제 지원. 좌표는 `definition_json.nodes[].position`(신규 선택적 필드, 스키마 없는 JSON 컬럼이라 백엔드 무변경)에 저장, 좌표 없는 노드는 기존 BFS 자동배치로 폴백. **KWCAG 2.2**: 캔버스 자체는 접근성 대상 아님 — 기존 `DefinitionEditor`(a11y 폼, impl/3)가 캔버스와 동일한 `nodes`/`edges` 상위 상태를 공유하는 대체편집기로 계속 병행되어 키보드 전용 사용자도 전체 기능 사용 가능. 시험 test/impl/25(tsc 0오류 + 좌표 왕복 로직 단위검증), 기존 test/impl/2·23·24 회귀 무영향. |
| 2026-07-09 | v0.22 | **impl/26(물리 `test/impl/24`) — F-WF webhook 수신 트리거**(사용자 요구, §7.2.4). 지난 impl/25 완료 후 접수된 유보 4항목(webhook 트리거·편집형 캔버스·Dify DSL Import·기타)을 사용자가 순차 진행하도록 지정한 1번째. `workflows.trigger_config_json`(기존 컬럼, 신규 스키마 없음)에 `webhook_secret_hash`(bcrypt) 저장 — `trigger_type="webhook"` 생성 시 평문 시크릿을 응답에 1회만 노출. `POST /api/workflows/{id}/trigger/webhook`(JWT 불필요, `X-Webhook-Secret` 헤더 검증) 신설 — 워크플로우 생성자의 현재 역할을 `tbl_users` 에서 조회해 임시 actor 토큰을 발급, agent/http 노드 실행에 전달(§7.2.3 actor-scoped 원칙 계승, 권한 상승 없음, 생성자 미발견 시 무토큰 실행). 프론트 `WorkflowPage.tsx` 에 트리거 타입(manual/webhook) 선택 + 생성 시 시크릿·URL 1회 표시 배너 추가. 시크릿 로테이션·HMAC 페이로드 서명·rate limiting 은 1차 유보(§6 리스크 기록). 시험 test/impl/24, 기존 test/impl/2·23 회귀 무영향. |
| 2026-07-09 | v0.21 | **impl/25(물리 `test/impl/23`) — F-WF 컴포넌트 팔레트 + agent 노드 실호출 + http 노드**(사용자 요구, §7.2.3). `/wise-dev-standard:implement` 세션에서 "워크플로우 생성 시 내장/시스템/Addon 에이전트의 세부 기능이 컴포넌트로 제공되어야 한다(예: A에이전트-조회)" 요구 접수. (1) `GET /api/workflow/components` 신설 — Orchestrator 의 기존 OpenAPI 동적 탐지(`_probe_prefix`/`_openapi_paths`)를 재사용해 내장(7종)/시스템/Addon 에이전트별 API 엔드포인트를 `{에이전트명}-{기능}` 컴포넌트로 실시간 노출(신규 테이블 없음). (2) `workflow_engine.py` `agent` 노드가 `config.path` 지정 시 Orchestrator `_exec_api_call` 재사용으로 **실제 API 호출**(actor Bearer 토큰 전달, 권한 상승 없음) — `path` 미지정 시 기존 스텁 동작 하위호환(test/impl/2 21/21 회귀 무영향). (3) 신규 `http` 노드(8번째 타입) — 외부 URL 직접 호출, admin-trust 경계(§6 SSRF 리스크 기록). (4) 프론트 `WorkflowPage.tsx` 에 컴포넌트 팔레트(내장/시스템/Addon 그룹) 추가 — 클릭 시 사전설정된 `agent` 노드 삽입. 편집형 캔버스·Dify DSL Import·webhook 트리거·code 노드는 동일 요구의 일부로 접수했으나 이번 반복 범위 밖 — PRD §7.2.3·§9.5 에 유보 기록. 시험 test/impl/23. |
| 2026-07-09 | v0.19 | **impl/24 — 화면 정렬 표준화**(사용자 요구, §7.11). 대시보드·워크플로우·RAG·플레이그라운드·가드레일이 `max-w-4xl/5xl mx-auto`(가운데)로 제각각이던 것을 마켓플레이스식 **좌측정렬·반응형**으로 통일. `front/src/index.css` 에 **`.page` 표준 클래스**(`w-full max-w-6xl p-4 sm:p-6`) 정의 후 전 화면 루트에 적용, `mx-auto` 제거. addon-agents front(emb_server-shell + 템플릿 Board/ShellAgent/UserManager)도 동일 적용, addon 가이드에 표준 명시. **AI 어시스턴트(ChatPage)는 사용자 지시로 현행 유지(제외)**. 프론트 tsc/build 0오류. 시험 test/impl/22. |
| 2026-07-09 | v0.18 | **impl/23 — F-GRD 완전판정(LLM classifier) + 생성 regex 과탐 완화**(사용자 요구, §7.8.7). (1) `guardrails_classifier_enabled`(기본 off) 시 `/test` 가 regex 후 규칙 메뉴(도메인당 `guardrails_classifier_max_rules`=40, priority순, 기매치 제외)를 LLM(`call_ollama`)에 제시해 패러프레이즈 위반 판정 → `decide_multi_llm`, `source="rules+llm"`, degrade-safe. (2) 컴파일러 `build_guardrails_data.py` 에 **교차도메인 DF 필터 + 단일 키워드 게이트**(DF≤2·len≥3만 단독 허용) 적용해 흔한 키워드 오탐 축소, 규칙에 `description`·`priority`·`mode` 추가·중복 제거. (3) 룰셋 정제 — 규칙별 **실판정(regex)+휴리스틱 공존**, 카탈로그 `regex_rule_count`+`heuristic_rule_count` 분리. (4) 프론트 `필터적용` 토글 **낙관적 업데이트+오류 표면화**(무음 실패 버그 수정). (5) `emb_guardrails` ADDON 에 룰셋 데이터 동봉. 룰스토어 `classifier_candidates()`, 프론트 판정 소스 표기. 시험 test/impl/21. |
| 2026-07-08 | v0.17 | **impl/21 — F-GRD 도메인별 필터 확장 + impl/22 — 누락 emb_ 내장 패키지 생성**(사용자 추가 요구). **impl/21**(§7.8.7): wise-Guardrails 규칙 데이터 24개 업종 도메인 전체를 `scripts/build_guardrails_data.py` 로 `app/data/guardrails/` 에 컴파일 내재화, classifier 규칙에 **regex 생성**(generated). `guardrails_rules.py` 룰스토어 + `guardrails_detector.decide_multi`(다도메인). `guardrails_domain_catalog.filter_enabled` 컬럼 + `PUT /domains/{key}/filter` 토글(global=필수 잠금), `/test` 다도메인 평가. 프론트 카탈로그 `필터적용` 토글 + 도메인별 결과. **impl/22**(§7.8.8): `emb_{marketplace,workflow,rag,playground,guardrails}` ADDON 패키지 생성(`-app.py`+`-meta.json`+`.zip`, base_agent→네이티브 라우터). |
| 2026-07-08 | v0.16 | **impl/20 — 에이전트 관리·마켓플레이스 통합(UI 재구성)**(사용자 추가 요구). (1) 내장 에이전트 **마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일 5종을 `is_required=1`(REQUIRED)** 로 승격(sqlite/pg `02_seed.sql` + 라이브 DB). (2) 에이전트 관리 상단탭을 **`내장 에이전트`(Orchestrator·AI 어시스턴트·마켓플레이스·워크플로우·RAG·플레이그라운드·가드레일 7종 한정) / `시스템 에이전트`(그 외 보안 도메인 등) / `Addon 에이전트`** 3분류로 재구성(`BUILTIN_KEYS` 셋 기준). (3) 기존 마켓플레이스 화면의 **`자산 등록` 버튼을 시스템 에이전트 탭 상단**(Addon 탭 `새 Agent 만들기`와 동일 위치)으로 이동(`registerAsset` 재사용 모달). (4) **좌측 메뉴를 마켓플레이스로 통합** — `에이전트 관리` nav 제거, `/agents`→`/marketplace` 리다이렉트, `/marketplace` 가 통합 허브(3탭)를 렌더, 마켓플레이스 자산 카탈로그(로컬+원격)는 시스템 에이전트 탭 하단에 편입. 프론트 tsc/build 0오류. 백엔드/SQL 계약 무변경(is_required 값만 조정) |
| 2026-07-08 | v0.15 | **impl/19 — F-PG 토큰 사용량 추적**(관측성 §7.9): `call_ollama` usage_out 연결 → `playground_runs.input_tokens/output_tokens`, 대시보드 토큰 합계·이력 노출(시험 6/6). **+ 브랜딩 통일**: "SeCuardian Platform" → "SeCuardian Marketplace" 전면 변경(orchestrator AI 어시스턴트 정체성 ko/en, AppLayout 헤더타이틀·로고). 잔여 0, boot 26 routes, 회귀 무영향 |
| 2026-07-08 | v0.14 | **impl/13~18 — §9.5 잔여 6항목 전부 완료**(사용자 "잔여작업 진행", 네트워크 설치 승인). 설치: `@xyflow/react`·`pgvector`·`psycopg[binary]`·`python-gnupg`. **impl/13** F-GRD MCP Server 프록시(`guardrails_mcp.validate`, MCP 우선·실패시 로컬 폴백, 6/6). **impl/14** 로컬 자산 실 ZIP 배포(`marketplace_asset_blobs` + `deploy_zip` 공용 서비스, local install→무중단 마운트, 10/10). **impl/15** F-RAG pgvector 어댑터(`vector_backend` resolve·pg DDL·`<=>` ANN, sqlite 폴백 유지, 6/6). **impl/16** GPG detached 서명검증(`signature.py`, python-gnupg)+mTLS(CA번들·클라이언트인증서), 10/10. **impl/17** 대시보드 실시간 위젯(`/api/dashboard/summary`·`/activity`+10초 폴링, 10/10). **impl/18** F-WF React Flow 캔버스(`WorkflowCanvas`, 읽기전용 시각화, a11y 폼 병존). 전체 회귀: boot 26 routes, 백엔드 14차수 ALL PASS, ruff 신규 0오류, 프론트 tsc/build 0오류(2201 modules). **§9.5 잔여 = 외부 인프라 실측·로드맵만** |
| 2026-07-08 | v0.1~v0.3 | 초안·Guardrails 상세 확정(기존 이력) |
| 2026-07-08 | v0.4 | **구현 현황(§9) 신설** — 복제·트리밍 소스 정적 분석 반영. F-AI·F-SETUP ✅, F-WEB·F-OPS·F-ENV·F-GOV 🟡, F-MP·F-WF·F-RAG·F-PG·F-GRD ⬜. Addon 핫디플로이 제거에 따른 F-MP 설계 전제 변경(§9.3 Deviation) 기록 |
| 2026-07-08 | v0.5 | **impl/1** — §9.3 옵션 A 확정: Addon 핫디플로이 **복원**(✅). F-ENV 신규 `.env`/config 키 추가. **F-MP 백엔드 이식**(v0 ORM→raw-SQL): marketplace 2테이블·`router_marketplace`·시드, 시험 20/20 PASS |
| 2026-07-08 | v0.6 | **impl/2** — **F-WF 백엔드 이식**: `workflow_engine.py`(async DAG·retry·HITL·템플릿)+`router_workflow.py`+3테이블+시드. 7노드, 시험 21/21 PASS. dev-env 검증 PASS |
| 2026-07-08 | v0.7 | **impl/3~6 — F-WF Designer 프론트·F-MP 프론트·F-RAG·F-PG·F-GRD 전체 완료**(사용자 요청 "순차적으로 구현" 일괄 수행). impl/3: WorkflowPage(a11y 폼 편집기)+MarketplacePage+라우트/nav/i18n 5종(tsc+build 0오류). impl/4: F-RAG 백엔드(해싱임베더·BM25·RRF)+프론트, 식별자질의 BM25 최상위랭크 실증(시험 15/15). impl/5: F-PG 백엔드(LLM폴백 실행+RAG 컨텍스트+degrade무중단)+A/B 프론트(시험 13/13). impl/6: F-GRD 백엔드(**global PII/신용정보 13종 정규식 판정기 로컬 재구현** — Luhn카드검증·마스킹·에이전트토글·이중감사)+프론트(13종 전수 실증, 시험 20/20). §9.3 Deviation 완전 해결로 정리. 전체 회귀: boot 24 routes, ruff 신규코드 0오류, 프론트 tsc+build 0오류(2036 modules). F-MP·F-WF·F-RAG·F-PG·F-GRD **전부 🟡(백엔드+프론트 동작, 확장 항목만 잔존)** |
| 2026-07-08 | v0.8 | **impl/7 — F-GRD Orchestrator 게이트 배선 완료**(§9.5 1순위 항목). `app/agents/guardrails_gate.py` 신설 — `orchestrator._exec_api_call` 모듈 속성 재바인딩으로 **orchestrator.py 소스 0바이트 변경**하며 6개 내부 호출지점 전부 가로챔(Python 전역 이름조회 특성 활용). 입력/출력 양방향 판정, redact 시 실제 페이로드 치환(로깅뿐 아니라 강제), 에이전트별 토글 정합성, 전역 킬스위치(`GUARDRAILS_ENABLED`), 예외 시 무중단 폴백. 시험 15/15 PASS(orchestrator.py 무변경 검증 포함) + 기존 impl/1,2,4,5,6 전체 회귀 무영향 확인. **F-GRD·E8 완전 동작** — 잔여는 MCP 프록시 연동·block/escalate 승격조건뿐 |
| 2026-07-08 | v0.13 | **impl/12 — 좌측 nav '사용자' 하단 재배치**(사용자 UI 지시, §4.5 신규). `AppLayout.tsx` 에서 '사용자 관리' NavLink 를 상단 스크롤 nav 에서 꺼내 로그인 사용자 블록 바로 위 고정 배치. 워크스페이스 전 프로젝트 적용(SeCuardian + SeCuardian-Marketplace, `*-v0` 제외). admin 게이트·i18n·collapsed 보존. 양 프로젝트 tsc/build 0오류 |
| 2026-07-08 | v0.12 | **impl/11 — F-GRD block/escalate 승격 조건 완료**(§9.5 잔여). `guardrails_detector.decide()` 에 고위험 카테고리(시크릿·신용정보·국가식별번호) 기반 승격 추가: 저위험 PII→redact, 고위험 1종→block, 2종+→escalate(riskScore=1.0). impl/7 게이트의 block 분기가 이제 실발화 — 고위험 입력이 Orchestrator `_exec_api_call` 에서 HTTP 403 [BLOCKED] 로 차단·핸들러 미도달 검증. 저위험 redact 하위호환(impl/6·7 회귀 무영향). 시험 14/14 PASS. 잔여: MCP 프록시 연동 |
| 2026-07-08 | v0.11 | **impl/10 — 실 addon ZIP hot-deploy 연결(§7.6) 완료**. `router_marketplace_remote._hot_deploy` — 다운로드·검증한 ZIP 을 httpx ASGITransport in-process 로 기존 `/api/addon-agents/upload` 에 재사용 배포(별도 재구현 없음, §7.3.3 준용). 원격 install→extract→SQL→`load_router()`→무중단 라이브 마운트 E2E 확인(설치 전 404→후 200). `hot_deploy` 플래그·유효성 흡수. 시험 8/8 PASS + impl/9 회귀 무영향. E1.5 ✅. 잔여: 로컬자산 ZIP 저장(로컬 실배포), GPG 서명, mTLS |
| 2026-07-08 | v0.10 | **impl/9 — F-MP 원격 레지스트리(E1.5) 완료**(§7.3.3 계약). `app/routers/router_marketplace_remote.py` — `/api/marketplace-remote` ping·catalog(캐시 TTL)·detail·install(원격 ZIP 다운로드→SHA256 검증→로컬 `marketplace_assets` source='remote' 편입). 원격 HTTP 를 `_remote_get`/`_remote_download` 로 분리해 monkeypatch 시험(네트워크 불요). 폐쇄망 기본 off(409). 프론트 MarketplacePage 원격 카탈로그 섹션. 시험 14/14 PASS + tsc/build 0오류(2039 modules), boot 25 routes. 잔여: 실 ZIP hot-deploy 연결(§7.6) |
| 2026-07-08 | v0.9 | **impl/8 — 대시보드 화면 완료**(§9.5 잔여 항목). `front/src/pages/dashboard/DashboardPage.tsx`(서버상태·에이전트 카운트·5개 내장에이전트 빠른링크·그룹집계) + `api/health.ts`(신규, `/health` 는 `/api` 프리픽스 밖이라 별도 클라이언트 필요) + `vite.config.ts` `/health` 프록시 추가. `/`·`*` 리다이렉트를 `/chat`→`/dashboard` 로 변경(PRD §7.11 "홈: 대시보드" 레이아웃 요구 충족). 백엔드 변경 없음(기존 API 조합), tsc/build 0오류(2038 modules). Makefile/docker-compose/`.env.example` 잔존 모니터 재검사 결과 **이미 클린**(이전 세션에서 완료) 확인. F-WEB 대시보드 갭 해소 |

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
