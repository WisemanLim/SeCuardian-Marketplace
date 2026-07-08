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
| Marketplace (F-MP: 카탈로그·설치·단일활성버전) — 백엔드+프론트 | 🟡 |
| Workflow (F-WF: DAG 엔진·7노드·retry·HITL·SSE) — 백엔드+a11y 폼 프론트 | 🟡 |
| RAG (F-RAG: 청킹·BM25+dense·RRF 하이브리드검색) — 백엔드+프론트 | 🟡 |
| Playground (F-PG: 프롬프트/모델/RAG 실험·A/B) — 백엔드+프론트 | 🟡 |
| Guardrails (F-GRD: PII/신용정보 13종 실판정·에이전트토글) — 백엔드+프론트 | 🟡 |
| 환경 분리/키(F-ENV), 웹 포털(F-WEB), 거버넌스(F-GOV) | 🟡 부분 |

> 5개 내장 에이전트 모두 백엔드+프론트 동작(시험 PASS). 🟡 = 확장 항목(원격 레지스트리·React Flow 캔버스·pgvector·MCP 프록시 등) 잔존. 상세: [PRD §9](.docs/SeCMP-PRD.md#9-구현-현황-implementation-status--2026-07-08-기준).

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
                         workflow_engine(F-WF DAG)·embeddings+rag_pipeline(F-RAG)·guardrails_detector(F-GRD)
  core/                  config(settings)·deps(JWT/RBAC)·security
  rules/                 keyword_matcher (Orchestrator 룰)
  db.py                  raw-SQL 헬퍼 (fetch_one/all·execute_write/insert·_PH·migrations)
sql/{sqlite,pg}/         01_init.sql(멱등 DDL: 코어 + marketplace/workflow/rag/playground/guardrails)
                         02_seed.sql(에이전트/설정/도메인카탈로그 시드)
front/src/
  pages/                 chat·agents·users·settings·profile·addon·setup +
                         marketplace·workflow·rag·playground·guardrails (내장 에이전트 5종)
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
make seed           # 기본 설정 + 테스트 계정
make db-fresh       # reset + seed
```

---

## 6. 접속 / 포트

| 서비스 | URL | 호스트 포트 | 비고 |
|---|---|---|---|
| Backend API | http://localhost:8100 | `BACKEND_PORT` 8100 → 컨테이너 8000 | |
| API 문서 | http://localhost:8100/docs | | FastAPI Swagger |
| Frontend | http://localhost:4100 | `FRONTEND_PORT` 4100 | Vite |
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
# 자산 등록
curl -X POST http://localhost:8100/api/marketplace/catalog \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"asset_key":"cve-scanner","version":"1.0.0","kind":"agent","name":"CVE 스캐너"}'
# 카탈로그 조회
curl http://localhost:8100/api/marketplace/catalog -H "Authorization: Bearer $TOKEN"
# → {"assets":[{"asset_key":"cve-scanner","installed":false,"active_version":null, ...}]}
# 설치 (hot-deploy seam: tbl_agent_config upsert)
curl -X POST http://localhost:8100/api/marketplace/install/cve-scanner \
  -H "Authorization: Bearer $TOKEN"
# → {"id":1,"asset_key":"cve-scanner","version":"1.0.0","status":"installed","active":true,"agent_config_key":"cve-scanner"}
# 해제
curl -X DELETE http://localhost:8100/api/marketplace/install/cve-scanner -H "Authorization: Bearer $TOKEN"

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

# ── Guardrails (F-GRD) — global PII 13종 판정 (Playground 연계) ──
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"email me at secret@corp.com","domain":"global"}'
# → {"decision":"redact","riskScore":0.2,"matchedRules":["pii.email"],"redactedText":"email me at ****.com",...}
# 에이전트별 도메인 토글 (admin/supervisor)
curl -X PUT http://localhost:8100/api/guardrails/agents/chat/config -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"domain_key":"global","enabled":true}'
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
make lint                                   # ruff
cd front && pnpm exec tsc --noEmit && pnpm exec vite build   # 프론트 타입체크+빌드
```
차수별 시나리오·결과: `test/impl/<Nth>/{scenario,result}.md`. impl/3(F-WF Designer+F-MP 프론트)은 정적 검증(tsc/build)만.

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

---

## 10. 다음 단계 (PRD 잔여)

- **Orchestrator 게이트 배선**: `guardrails_gate.py` — F-GRD 를 Orchestrator 호출 경로에 연결(§7.8.4).
- **F-MP**: 원격 레지스트리(§7.3, E1.5), 실 addon ZIP 파이프라인 연결(§7.6).
- **F-WF**: React Flow 캔버스(현재 a11y 폼 편집기), loop/sub-flow/cron, llm 노드 Claude 통합.
- **F-RAG**: pgvector/Qdrant 전환(§7.5), eval(Recall@10/NDCG@10) 벤치마크.
- **F-PG**: 비용(cost) 추적(Claude 연동 시), eval 실행.
- **F-GRD**: MCP Server 프록시 연동, 25종 업종 판정기(SeCMP 책임 밖, wise-Guardrails 별도 로드맵).
- **대시보드**: `/api/agents` 카탈로그+헬스 요약 화면(현재 nav 만 존재).
