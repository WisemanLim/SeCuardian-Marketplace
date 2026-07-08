# SeCuardian-Marketplace (SeCMP)

> **[한국어 →](README.md)** · wise-dev-standard / **python-fastapi × ict-saas (govtech·security overlay)**
> An enterprise on-prem platform that inherits SeCuardian's Orchestrator + AI Assistant + Addon hot-deploy
> architecture and adds **Marketplace · Workflow · RAG · Playground · Guardrails** built-in agents.
>
> Docs: [PRD](.docs/SeCMP-PRD.md) · [COMPLIANCE.md](COMPLIANCE.md) · [AGENTS.md](AGENTS.md)

---

## 1. Overview

SeCMP builds on the SeCuardian core (central Orchestrator + AI Assistant + zero-downtime ZIP hot-deploy +
4-table agent management) to **discover, install, version, and govern** AI agents, workflows, and knowledge
bases (RAG).

**Implementation status** (details: [PRD §9](.docs/SeCMP-PRD.md)):

| Area | Status |
|---|---|
| Orchestrator + AI Assistant (F-AI), Setup Wizard (F-SETUP) | ✅ Done |
| Addon hot-deploy (ZIP upload · live mount) | ✅ Restored |
| Marketplace (F-MP: catalog · install · single active version) — backend+frontend | 🟡 |
| Workflow (F-WF: DAG engine · 7 nodes · retry · HITL · SSE) — backend+a11y form frontend | 🟡 |
| RAG (F-RAG: chunking · BM25+dense · RRF hybrid search) — backend+frontend | 🟡 |
| Playground (F-PG: prompt/model/RAG experimentation · A/B) — backend+frontend | 🟡 |
| Guardrails (F-GRD: PII/financial 13-type real detection · agent toggle) — backend+frontend | 🟡 |
| Env separation/keys (F-ENV), Web portal (F-WEB), Governance (F-GOV) | 🟡 Partial |

> All 5 built-in agents have working backend+frontend (tests PASS). 🟡 = extension items remain (remote registry, React Flow canvas, pgvector, MCP proxy, etc). Details: [PRD §9](.docs/SeCMP-PRD.md#9-구현-현황-implementation-status--2026-07-08-기준).

---

## 2. Architecture / Layout

```
app/
  main.py                FastAPI entry (lifespan: migration→seed→addon loader→ollama warmup)
  agents/orchestrator.py Orchestrator (classify→gather→synthesize, in-proc call_api)
  addon_agent_loader.py  Addon hot-deploy (importlib spec → include_router)
  routers/               auth·users·agent·chat_history·suggestions·addon_agent·settings·
                         setup·agent_config·agent_registry·a2a·mcp·mcp_config·
                         marketplace(F-MP)·workflow(F-WF)·rag(F-RAG)·playground(F-PG)·guardrails(F-GRD)
  services/              llm_fallback·ollama_warmup·mcp_proxy_server·openapi_to_mcp·
                         workflow_engine(F-WF DAG)·embeddings+rag_pipeline(F-RAG)·guardrails_detector(F-GRD)
  core/                  config(settings)·deps(JWT/RBAC)·security
  rules/                 keyword_matcher (Orchestrator rules)
  db.py                  raw-SQL helpers (fetch_one/all·execute_write/insert·_PH·migrations)
sql/{sqlite,pg}/         01_init.sql (idempotent DDL: core + marketplace/workflow/rag/playground/guardrails)
                         02_seed.sql (agent/settings/domain-catalog seed)
front/src/
  pages/                 chat·agents·users·settings·profile·addon·setup +
                         marketplace·workflow·rag·playground·guardrails (5 built-in agents)
  api/                   axios client per backend contract (1:1)
addon-agents/            Addon ZIP assets (deployed/ is runtime bind-mount)
test/impl/<Nth>/         per-iteration test scenario·result
test/dev-env/            dev-env standard verification (once)
```

**Services (containers)**: `postgres:17` · `redis:7.4` · `ollama` · `api` (profile `app`) · `web` (profile `web`).

---

## 3. Prerequisites

| Tool | Version | Note |
|---|---|---|
| Python | 3.11+ (verified 3.13) | managed via `uv` |
| uv | latest | backend deps·run |
| Node | **22+ recommended** (20 works; CI uses 22) | frontend |
| pnpm | 9+ (verified 10) | `corepack enable` |
| Docker Compose | v2+ | dev/staging/prod |

---

## 4. Environment Configuration

Copy `.env.example`. **Never commit real secrets** (`.gitignore` blocks `.env.*`, tracks only `.env.example`).

| File | Purpose | DB | Note |
|---|---|---|---|
| `.env.local` | developer local | SQLite | pm2/direct run, dev values allowed |
| `.env.dev` | docker compose | PostgreSQL+Redis | in-container addresses overridden by compose |
| `.env.staging` | prod-equivalent | PostgreSQL | `CHANGE_ME` secrets → Vault injection |
| `.env.prod` | production | injected | **key list only** (no values, Vault/Secret Manager) |

```bash
cp .env.example .env.local     # local starting point
# precedence: os.environ > .env.<ENV> > tbl_settings > config defaults
```

Key settings: `DATABASE_URL`·`JWT_SECRET_KEY`·`ANTHROPIC_API_KEY`·`OLLAMA_*` · built-in agents `VECTOR_BACKEND`·`MARKETPLACE_*`·`TENANT_*`·`GUARDRAILS_*`.

---

## 5. Running

### A) Local (SQLite, minimal containers)
```bash
make local-all      # Ollama(docker) + BE/FE via pm2 in background (SQLite auto)
make local-stop
make local-logs
# or individually:
make dev-be         # backend only (uv run uvicorn --reload)
make dev-fe         # frontend only (pnpm dev, :4100)
```

### B) docker compose (dev/staging/prod)
```bash
make up             # infra only (postgres+redis+ollama)
make dev-all        # full stack with .env.dev (api profile=app + web)
make dev-down
make staging-all / make prod-all    # uses each .env.<env>
```
- Profiles: default (`up`)=infra, `app`=api, `web`=frontend prod image.
- GPU: `OLLAMA_RUNTIME=gpu` auto-merges `docker-compose.gpu.yml`. macOS Apple Silicon=`mlx` (native Ollama).

### DB init
```bash
make db-reset       # recreate schema (FORCE=1 skips confirm)
make seed           # default settings + test accounts
make db-fresh       # reset + seed
```

---

## 6. Endpoints / Ports

| Service | URL | Host port | Note |
|---|---|---|---|
| Backend API | http://localhost:8100 | `BACKEND_PORT` 8100 → container 8000 | |
| API docs | http://localhost:8100/docs | | FastAPI Swagger |
| Frontend | http://localhost:4100 | `FRONTEND_PORT` 4100 | Vite |
| PostgreSQL | localhost:5432 | `POSTGRES_PORT` | dev+ |
| Redis | localhost:6379 | `REDIS_PORT` | |
| Ollama | localhost:11434 | `OLLAMA_PORT` | local LLM fallback |
| MCP proxy | 20000–20019 | `MCP_PORT_RANGE` | per-agent MCP |

---

## 7. Implemented API Examples

```bash
# health
curl http://localhost:8100/health
# → {"status":"ok","env":"local","mode":"embedded"}

# setup status
curl http://localhost:8100/api/setup/status
# → {"has_supervisor":false,"completed":false}

# login → JWT
curl -X POST http://localhost:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"secmp","password":"Secu1234!"}'
# → {"access_token":"<JWT>","token_type":"bearer", ...}

# ── Marketplace (F-MP) — Bearer required; register/install need admin/supervisor ──
TOKEN=<JWT>
# register asset
curl -X POST http://localhost:8100/api/marketplace/catalog \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"asset_key":"cve-scanner","version":"1.0.0","kind":"agent","name":"CVE Scanner"}'
# list catalog
curl http://localhost:8100/api/marketplace/catalog -H "Authorization: Bearer $TOKEN"
# → {"assets":[{"asset_key":"cve-scanner","installed":false,"active_version":null, ...}]}
# install (hot-deploy seam: tbl_agent_config upsert)
curl -X POST http://localhost:8100/api/marketplace/install/cve-scanner \
  -H "Authorization: Bearer $TOKEN"
# → {"id":1,"asset_key":"cve-scanner","version":"1.0.0","status":"installed","active":true,"agent_config_key":"cve-scanner"}
# uninstall
curl -X DELETE http://localhost:8100/api/marketplace/install/cve-scanner -H "Authorization: Bearer $TOKEN"

# ── Workflow (F-WF) — DAG create·run·HITL ──
# create workflow (trigger→transform→notify)
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"demo","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"x","type":"transform","config":{"output":{"msg":"$t.input.name"}}},
               {"id":"n","type":"notify","config":{"message":"hi {{x.msg}}"}}],
      "edges":[{"source":"t","target":"x"},{"source":"x","target":"n"}]}}'
# run → completed
curl -X POST http://localhost:8100/api/workflows/1/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"input":{"name":"world"}}'
# → {"id":1,"status":"completed","output_json":"{...\"n\":{\"message\":\"hi world\"}}"}
# HITL approve (run in waiting_hitl)
curl -X POST http://localhost:8100/api/workflow-runs/1/hitl -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"approved":true}'

# ── RAG (F-RAG) — collection·ingest·hybrid search ──
curl -X POST http://localhost:8100/api/rag/collections -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"docs","sensitivity":"general"}'
curl -X POST http://localhost:8100/api/rag/collections/1/documents -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"title":"doc-a","text":"SKU-12345 identifies this product."}'
curl -X POST http://localhost:8100/api/rag/collections/1/search -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"query":"SKU-12345"}'
# → {"hits":[{"chunk_id":1,"text":"SKU-12345 identifies...","dense_rank":1,"bm25_rank":1,"rrf_score":0.0328,...}]}

# ── Playground (F-PG) — prompt/model/RAG experiment (no RBAC gate, any authenticated user) ──
curl -X POST http://localhost:8100/api/playground/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"prompt":"hello world","rag_collection_id":1}'
# → {"id":1,"response_text":"...","provider":"ollama|degraded","latency_ms":42,"citations_json":"[...]"}

# ── Guardrails (F-GRD) — global PII 13-type detection (Playground integration) ──
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"email me at secret@corp.com","domain":"global"}'
# → {"decision":"redact","riskScore":0.2,"matchedRules":["pii.email"],"redactedText":"email me at ****.com",...}
# per-agent domain toggle (admin/supervisor)
curl -X PUT http://localhost:8100/api/guardrails/agents/chat/config -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"domain_key":"global","enabled":true}'
```

---

## 8. Testing

```bash
make test                                   # full pytest
python test/impl/1/test_marketplace.py      # F-MP  (fresh sqlite, 20 asserts)
python test/impl/2/test_workflow.py         # F-WF  (fresh sqlite, 21 asserts)
python test/impl/4/test_rag.py              # F-RAG (fresh sqlite, 15 asserts)
python test/impl/5/test_playground.py       # F-PG  (fresh sqlite, 13 asserts)
python test/impl/6/test_guardrails.py       # F-GRD (fresh sqlite, 20 asserts — all 13 detectors verified)
make lint                                   # ruff
cd front && pnpm exec tsc --noEmit && pnpm exec vite build   # frontend type-check + build
```
Per-iteration scenario·result: `test/impl/<Nth>/{scenario,result}.md`. impl/3 (F-WF Designer + F-MP frontend) is static verification (tsc/build) only.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ruff` E402 (`main.py` import) | router import placed after helper def (present since original SeCuardian) | no functional impact; move imports to top when cleaning up |
| Node 20 warning | spec recommends 22+ | `nvm install 22` (pnpm 10 works on 20 too) |
| ENV=prod boot parse error | `.env.prod` is key-list only (empty bool/int commented) | boot after injecting real env via Vault/Secret |
| Makefile `keycloak-*`/`vault-*`/`harbor-*` targets | leftover SeCuardian security stack (out of SeCMP scope) | to be cleaned up |
| Playground `pnpm dev` crash-loop (`ERR_PNPM_IGNORED_BUILDS`) | pnpm 11 `verifyDepsBeforeRun` fails pre-check on esbuild's ignored build script | `verifyDepsBeforeRun: false` in `front/pnpm-workspace.yaml` |
| Guardrails card-number false positives | any 13–19 digit run can match | Luhn checksum required (implemented) — residual false positives possible, refine rules if needed |

---

## 10. Next Steps (PRD backlog)

- **Orchestrator gate wiring**: `guardrails_gate.py` — hook F-GRD into the Orchestrator call path (§7.8.4).
- **F-MP**: remote registry (§7.3, E1.5), real addon ZIP pipeline wiring (§7.6).
- **F-WF**: React Flow canvas (currently a11y form editor), loop/sub-flow/cron, llm-node Claude integration.
- **F-RAG**: pgvector/Qdrant migration (§7.5), eval (Recall@10/NDCG@10) benchmarks.
- **F-PG**: cost tracking (once Claude is wired), eval execution.
- **F-GRD**: MCP Server proxy integration, 25 industry-domain detectors (out of SeCMP scope, wise-Guardrails' own roadmap).
- **Dashboard**: `/api/agents` catalog+health summary screen (currently nav entry only).
