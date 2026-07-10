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
| Dashboard (`/dashboard` — server status + agent summary + quick links) | ✅ Done |
| Marketplace (F-MP: catalog · install · single active version, **unified agent-management hub**) — backend+frontend | 🟡 |
| Workflow (F-WF: DAG engine · 8 nodes[+http] · retry · HITL · SSE · **component palette · webhook trigger (rotation+HMAC+rate limit) · full-screen builder (palette drag & drop + inspector) · Dify DSL Import · partial-edit PATCH**) — backend+a11y form frontend | 🟡 |
| RAG (F-RAG: chunking · BM25+dense · RRF hybrid search · **pgvector benchmark done**) — backend+frontend | 🟡 |
| Playground (F-PG: prompt/model/RAG experimentation · A/B) — backend+frontend | 🟡 |
| Guardrails (F-GRD: real+heuristic coexist · **24 domain rulesets vendored · filter toggle · multi-domain · LLM classifier (optional) full judgment** · Orchestrator gate) — backend+frontend | 🟡 |
| Env separation/keys (F-ENV), Web portal (F-WEB), Governance (F-GOV) | 🟡 Partial |
| Extensible multilingual descriptions + Local LLM diversification (SeCuardian R18-7·R19 clone sync, §7.11.2) | ✅ Synced |

> All 5 built-in agents have working backend+frontend (tests PASS). 🟡 = extension items remain (remote registry, React Flow canvas, pgvector, MCP proxy, etc). Details: [PRD §9](.docs/SeCMP-PRD.md#9-구현-현황-implementation-status--2026-07-08-기준).
>
> **UI layout (impl/20 → impl/36 → impl/43, physical `test/impl/41`, §7.6.4 three-tab split)**: there is no separate `Agent Management` menu — the **Marketplace menu is the unified agent hub**. Three top tabs: **Asset Catalog** (default: category-grouped assets, per-category `+ Add`, `Register Asset`, remote registry) / **Agents (Installed)** (base/built-in configs + only catalog agents with an **active install** — they appear on install and disappear on uninstall; catalog matching is case-insensitive §7.6.4-6. Shown in the same **category sections** as the catalog: builtin → security → utilities → general …) / **Addon Agents** (user-uploaded, `New Agent`). The 5 built-ins (Marketplace/Workflow/RAG/Playground/Guardrails) are **REQUIRED (cannot be disabled)**. Install/uninstall/registration fires a `marketplaceChanged` event that syncs the tabs instantly; the register modal supports **attaching multiple scaffold-format addon ZIPs** — hot-deployed on install (agents with a screen appear in the left menu).
>
> **Security agents moved to the asset catalog (impl/36, §7.6.1)**: the 13 SeCuardian security built-ins formerly shown on the 'System Agents' tab (vasca-cve, cilium-netpol, teler-ids, shuffle-soar, neosync-dlp, otel-collector, teleport-pam, velociraptor-dfir, ai-redteam, isms-p-evidence, behavior-noti, agentic-soc, ai-eval-gate) are now provided as **asset-catalog entries (marketplace_assets, category=security)** — registered by `make seed-security` (with zip blobs) and installed from the catalog. Their 13 packages live under **`marketplace-assets/security/`** (§7.6.1-6 `emb_` abolished, §7.6.1-7 `addon-agents/zip` abolished). `make seed` performs the base seed (settings, accounts) only.
>
> **Asset registration UX + categorized catalog (impl/41, physical `test/impl/39`, §7.6.2)**: ① the `Register Asset` modal no longer asks for `asset_key` — enter only **name (e.g. `security`)** and the server auto-assigns the asset_key from a name slug (suffix `-2` on collision; passing an explicit key via the API keeps the old behavior) ② **multiple addon ZIPs** can be attached at once, like the ZIP upload in `Create Agent` — each ZIP is registered as its own asset from its `{key}-meta.json` (new `POST /api/marketplace/catalog/zip`) with the blob stored for hot-deploy on install ③ the asset catalog is grouped into **category sections (security, utilities, general, …)** ④ `make seed-assets` (`scripts/seed_assets.py`) scans `marketplace-assets/{security,utilities}/` and INSERTs only unregistered assets (bringing the 6 utilities into the catalog) ⑤ the catalog refreshes immediately after registration (`marketplaceChanged` event).
>
> **Default catalog registration + per-category add (impl/42, physical `test/impl/40`, §7.6.3)**: of the four `marketplace-assets/` groups, only **security and utilities are default asset-catalog targets** (addon = scaffold templates and builtin = core built-ins are excluded) — `make db-fresh` now chains seed (base) → seed-security → seed-assets, so security (13) and utilities (6) are registered right after initialization. Each category section header in the asset catalog has an **`+ Add` button** (admin) that opens the registration modal preset to that category (metadata or multiple ZIPs), while the top `Register Asset` button handles **catalog creation (free-form category, default general) + asset registration**.
>
> **Install / Not-installed semantics in detail**: the badge on each catalog card reflects whether the asset has an active install.
> - **Not installed**: only the metadata exists in `marketplace_assets` — the asset can be browsed and inspected, but does not act as an agent.
> - **Install** (`Install` button = `POST /api/marketplace/install/{asset_key}`, admin/supervisor) runs a transaction: ① deactivate any previous active install (single active version) ② upsert `tbl_agent_config` (`nav_group='marketplace'`, `is_enabled=1`) — the agent **immediately joins the Built-in Agents tab card deck and Orchestrator intent routing** ③ record the install in `marketplace_installs` ④ if a ZIP blob exists, reuse the addon upload pipeline in-process for a **zero-downtime hot-deploy** (`/api/addon/{key}/...` goes live; a deploy failure does not invalidate the install record and is reported as `deployed=false`).
> - **After install**: Orchestrator automatically routes AI Assistant queries to the installed agent, and agents with a dedicated screen appear in the left menu. The agent card exposes enable/disable and MCP settings.
> - **Uninstall** (`DELETE /api/marketplace/install/{asset_key}`, §7.6.5): in addition to deactivating the install history and setting `tbl_agent_config.is_enabled=0`, it **fully cleans up the hot-deploy artifacts** — DROPs addon-created tables, removes `addon-agents/deployed/{key}/`, deletes the deployed screen (tsx), stops MCP and deletes its config, and deletes the `tbl_addon_agents` row (→ the left-nav menu entry disappears immediately), rebuilding the web bundle if a screen existed. The config row is kept so reinstalling re-activates it. Fully removing a live-mounted router still requires an app restart. Bulk-clean legacy remnants with `make cleanup-addons` (uninstalled-asset remnants + orphan deployed directories, idempotent).
>
> **Guardrails domain filters (impl/20 §7.8.7)**: all **24 wise-Guardrails domain rulesets are vendored as agent-internal data (`app/data/guardrails/`)**. `global` (PII/financial) is always required; industry domains (finance/healthcare/manufacturing/public-admin, …) get **generated regex** for their classifier rules, and each non-required domain has a **`Filter` toggle** in the catalog to include/exclude it at test time (multi-domain evaluation). Rebuild data: `make guardrails-data` (`scripts/build_guardrails_data.py`).
>
> **Workflow component palette (impl/25 · physical `test/impl/23`, §7.2.3)**: `GET /api/workflow/components` scans built-in (7), system, and addon agents' OpenAPI endpoints and exposes each as a `{agent name}-{capability}` component in real time (no new table — reuses Orchestrator's existing dynamic endpoint discovery). Clicking a palette item on the Workflow screen inserts a preconfigured `agent` node (agent_key/method/path); on run, it actually calls that API, forwarding the actor's own Bearer token (a workflow cannot act beyond the requester's own permissions). A new `http` node (8th type) supports calling arbitrary external URLs directly. When `config.path` is omitted the `agent` node keeps its v1 stub behavior (backward compatible).
>
> **Webhook ingress trigger (impl/26 · physical `test/impl/24`, §7.2.4)**: creating a `trigger_type="webhook"` workflow makes the server generate a secret and **expose it only once, in the create response**. External systems call `POST /api/workflows/{id}/trigger/webhook` with an `X-Webhook-Secret` header — **no JWT required**. The server looks up the workflow **creator's current role** and mints a scoped, ephemeral token so `agent`/`http` nodes run with that identity (inherits the actor-scoped principle from §7.2.3 — if the creator can't be found, the run proceeds without a token and only that node fails safely).
>
> **Webhook security hardening (impl/29 · physical `test/impl/27`, §7.2.4.1)**: secret storage moved from **one-way bcrypt to reversible Fernet encryption** (rotation and HMAC verification both need the plaintext back; the key is derived from `JWT_SECRET_KEY`, no new env var). `POST .../trigger/webhook/rotate` (admin/supervisor) reissues a secret and immediately invalidates the old one. `X-Webhook-Signature: sha256=<hmac>` is now supported (GitHub-style convention — the secret itself never has to travel on every call) — either that header or the existing `X-Webhook-Secret` is enough to pass (backward compatible). Per-workflow in-memory rate limiting (default 30/min, `WORKFLOW_WEBHOOK_RATE_LIMIT_PER_MIN`) is added — **single-process only**; pair it with reverse-proxy/API-gateway rate limiting for a stronger guarantee.
>
> **Editable (drag) canvas (impl/27 · physical `test/impl/25`, §7.2.5)**: `WorkflowCanvas` (React Flow) is promoted from read-only visualization to editable — **drag nodes to move, drag handles to connect, select + Backspace/Delete to remove**. Coordinates are stored in `definition_json.nodes[].position` (a schema-less JSON column, so **no backend change**); nodes without a position fall back to the existing BFS auto-layout. **KWCAG 2.2**: the canvas itself is mouse-centric and not an accessibility target — the existing a11y form editor (`DefinitionEditor`) keeps running in parallel, sharing the exact same nodes/edges state as the canvas, so keyboard-only users can still complete every operation (add/remove nodes & edges, insert components).
>
> **Full-screen workflow builder (impl/32 · physical `test/impl/30`, §7.2.8)**: the impl/27 mini canvas (a 320px widget inside the create panel) was judged unusable in practice, so the workflow editor was rebuilt as the **palette → canvas drag & drop → inspector** three-pane builder pattern shared by Flowise/Dify/n8n. `WorkflowBuilderPage` at `/workflow/builder` (new) and `/workflow/builder/:id` (edit existing) — a **left palette** (8 node types + §7.2.3 components with search; HTML5 drag plus click-to-insert), a **center full-height canvas** (custom nodes with type-colored headers and config summaries, `screenToFlowPosition` drop placement, connect/move/delete), and a **right inspector** (structured per-type forms for agent/llm/condition/http/notify plus a JSON fallback, and **inline edge `when` editing** — closing the §7.2.5 deferral; renaming a node remaps its edges automatically). On the backend, `PATCH /api/workflows/{id}` is **extended to partial editing** (`name`/`description`/`definition_json`; a definition change bumps `version` +1; the bare `{"enabled"}` call stays backward compatible). **Licensing**: only the UX pattern of Flowise (Apache-2.0)/Dify is referenced — no code copied; the implementation is our own on React Flow (MIT). KWCAG 2.2 is preserved via the existing a11y form editor, palette click-insert, and standard labeled inspector forms.
>
> **Dify DSL Import adapter (impl/28 · physical `test/impl/26`, §7.2.6, mode A)**: `POST /api/workflows/import/dify-dsl` converts a Dify Studio export YAML into a SeCMP `definition_json` per the §7.2.2 mapping table (`start→trigger` · `llm→llm` · `if-else→condition` · `knowledge-retrieval→agent(rag)` · `http-request→http` · `tool→agent` · `answer/end→notify`). **Lenient parsing** — `code` and unrecognized node types are replaced with a `transform` placeholder instead of crashing, reported in `warnings[]`; dangling edges are skipped the same way. Imported workflows are **always created with `enabled=false`** (forces human review). The original YAML and DSL version are kept in `dify_dsl_source`/`dify_dsl_version` (round-trip ready). Execution still runs on SeCMP's own engine (mode B delegate execution and mode C remain roadmap).
>
> **pgvector real-infra benchmark (impl/31 · physical `test/impl/29`, §7.5.1)**: `docker-compose.yml`'s postgres image was **permanently switched to `pgvector/pgvector:pg17`** (the old `postgres:17-alpine` had no `vector` extension, so it was silently falling back to the local path — a latent gap now fixed). Against a real container with `CREATE EXTENSION vector` confirmed, the pgvector code path (`VECTOR_BACKEND=pgvector`) was exercised end-to-end with an identifier-query eval set (N=40) — **Recall@10=1.000, p95=20.8ms** (both well past the PRD §5 targets of 0.89/250ms). Paraphrase-style dense-only recall still needs re-evaluation once the embedding model is swapped (roadmap).
>
> **Two-tier full judgment (impl/23 §7.8.7)**: (1) **regex** (deterministic) — each rule tagged with a `mode`, so **real (original regex) + heuristic (generated regex) coexist** (catalog shows `real N · heuristic M`). (2) **LLM classifier** (optional `GUARDRAILS_CLASSIFIER_ENABLED=true`, default off / non-deterministic) — after regex, presents the rule menu to the LLM to judge paraphrase/contextual violations; degrades to regex when unconfigured/unavailable. Generated-regex over-matching is mitigated by **2-keyword co-occurrence (AND) + cross-domain DF filter** (removes single common-keyword false positives). The catalog has a **select-all / deselect-all toggle** (right of `Filter N/M domains`). The guardrails ADDON bundles the ruleset data.
>
> **Screen alignment standard (impl/24)**: every agent screen root uses the **`.page` class** (`front/src/index.css` = `w-full max-w-6xl p-4 sm:p-6`) for **left-aligned, responsive, width-capped** layout (no `mx-auto`). Baseline for all new agents (built-in & addon). **Exception**: full-height interactive layouts (chat/terminal, e.g. AI Assistant).
>
> **Built-in MCP unlock (impl/20)**: the MCP lock on the REQUIRED built-in 5 is removed — all 7 built-in agents can be exposed as MCP servers.
>
> **Asset directory (impl/38 §7.6.1-7)**: all asset sources are unified under `marketplace-assets/<category>/` — security(13)·builtin(5: marketplace·workflow·rag·playground·guardrails)·addon(5: scaffold templates)·utilities(6: UserManager·server-shell·4 pure ADDONs). `addon-agents/{zip,_templates}` abolished (only deployed/ remains); template lookup path = `marketplace-assets/addon`.
>
> **Multilingual agent display names (impl/35 · physical `test/impl/33`, §7.11.2-4 — cloned from SeCuardian impl/56)**: new `tbl_agent_config.agent_names` JSON (`{"ko":..,"en":..}`) — the 7 built-in agents are seeded with English display names (마켓플레이스→Marketplace, 워크플로우→Workflow, …), fixing Korean names remaining in the English UI. Idempotent `{"ko": agent_name}` backfill at startup; meta.json `display_name` accepts the dict form (normalized & synced on upload). Applied with the same fallback chain as descriptions to agent cards, left nav, header title, and the Guardrails agent selector.
>
> **Full i18n for built-in agent screens + duplicate title removal (impl/34 · physical `test/impl/32`, §7.11.3)**: fixed screens (Workflow list/full-screen builder/canvas, RAG, Playground, Guardrails, Marketplace, Dashboard) remaining in Korean when the UI language is English — 137 hardcoded strings replaced with `t()` locale keys (`locales/{ko,en}.json` wf/wfb/rag/pg/mp/dash/grd sections), ko/en key parity enforced. Content h1 titles (5 screens) duplicated the AppLayout header title and were removed — **only the page description remains** (SeCuardian R18 standard). The `nav_group` chip on agent cards (Korean DB values) is also locale-mapped (en: Basic Agent · Built-in Agent).
>
> **Multilingual descriptions + Local LLM diversification (impl/33 · physical `test/impl/31`, §7.11.2 — cloned from SeCuardian R18-7·R19)**: ① Agent descriptions are managed as `tbl_agent_config.descriptions` JSON (`{"ko":..,"en":..}`, extensible to more languages by adding keys) — legacy `description`/`description_en` is idempotently backfilled at startup; meta.json accepts both dict and legacy forms (normalized on upload). New **preferred language** in My Page (`tbl_users.preferred_lang`) — display fallback `UI lang → preferred → ko → first available`, synced to the UI locale at login. ② Local LLM abstracted into **Ollama · llama.cpp · vLLM** backends (`app/services/llm_providers.py`, selected via `LOCAL_LLM_PROVIDER`, compose profiles `llamacpp`/`vllm`) + **per-task LLM routing** (`llm_routes`: classify/tools/synthesize/domain/chat) + **per-call metering** (`tbl_llm_usage` ledger, `GET /api/llm/usage` aggregation, usage summary in System Settings) + **token compression** (head/tail truncation of older history above `LLM_CONTEXT_BUDGET`). The AI Assistant model list is fetched dynamically from `GET /api/llm/models`.
>
> **Multilingual description authoring-source switch + jp (impl/39 · physical `test/impl/37`, §7.11.2-5)**: impl/33 had the structure, frontend fallback, and preferred-language UI, but the **authoring source was still split columns** (`02_seed` wrote `description`/`description_en`; `descriptions` was only a boot backfill), so there was no path to add another language — effectively unapplied. Fix: `02_seed.sql` (7 built-ins), install, and `seed_security` now author `descriptions`/`agent_names` as **JSON directly** (`{"ko","en","jp"}`); split authoring abolished (legacy read fallback only). The orchestrator `_active_agents_block` reads the descriptions JSON. My Page preferred language adds **jp** (`locale.jp`) — surfaces the preferred language when the UI-language key is absent. Removed the duplicate `backfill_descriptions` in db.py.
>
> **AI Assistant tool-call loop made configurable + early exit on repeated errors (impl/40 · physical `test/impl/38`, §7.11.2-6)**: The AI Assistant's self-correction loop on API errors is now system-managed via **`llm_tool_max_rounds`** (default 6, min 1) — priority `os.environ` > **`.env.*`** (`LLM_TOOL_MAX_ROUNDS`) > System Settings UI (`tbl_settings`) > default, applied to both the Anthropic and Ollama tool-call loops. **Efficiency**: when the Ollama loop repeats the identical `(method, path, status)` error (e.g. unsupported `PUT` → 405 × 6), it now **exits early after 2 rounds** instead of exhausting the remaining rounds, returning a user-friendly error (one retry is still allowed to preserve the self-correction chance).

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
                         workflow_engine(F-WF DAG)·embeddings+rag_pipeline(F-RAG)·
                         guardrails_detector+guardrails_rules(F-GRD multi-domain rule store)
  data/guardrails/       compiled domain rulesets (incl. generated regex) 24 (scripts/build_guardrails_data.py)
  core/                  config(settings)·deps(JWT/RBAC)·security
  rules/                 keyword_matcher (Orchestrator rules)
  db.py                  raw-SQL helpers (fetch_one/all·execute_write/insert·_PH·migrations)
sql/{sqlite,pg}/         01_init.sql (idempotent DDL: core + marketplace/workflow/rag/playground/guardrails)
                         02_seed.sql (agent/settings/domain-catalog seed)
front/src/
  pages/                 chat·users·settings·profile·addon·setup +
                         marketplace(=unified agent hub: Catalog/Installed/Addon 3 tabs, §7.6.4)·
                         workflow·rag·playground·guardrails (5 built-in agents)
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
make seed           # base seed only — default settings + test accounts
make seed-security  # register the 13 security agents in the asset catalog (§7.6.1, explicit)
make seed-assets    # scan marketplace-assets/{security,utilities} and register assets (§7.6.2, INSERT missing only)
make db-fresh       # reset + seed (base) + seed-security + seed-assets — security/utilities registered right after init (§7.6.3)
make cleanup-addons # bulk-clean uninstalled-asset hot-deploy remnants + orphan deployed dirs (§7.6.5, idempotent)
```

---

## 6. Endpoints / Ports

| Service | URL | Host port | Note |
|---|---|---|---|
| Backend API | http://localhost:8100 | `BACKEND_PORT` 8100 → container 8000 | |
| API docs | http://localhost:8100/docs | | FastAPI Swagger |
| Frontend | http://localhost:4100 | `FRONTEND_PORT` 4100 | Vite. Root (`/`) redirects to `/dashboard` |
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
# register asset — omit asset_key to auto-assign from the name slug (§7.6.2, e.g. "CVE Scanner" → cve-scanner)
curl -X POST http://localhost:8100/api/marketplace/catalog \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"version":"1.0.0","kind":"agent","name":"CVE Scanner"}'
# → {"asset_key":"cve-scanner","installed":false, ...}  (cve-scanner-2 on collision)
# register multiple ZIPs — each ZIP registers an asset from its {key}-meta.json + stores the blob (§7.6.2, idempotent)
curl -X POST http://localhost:8100/api/marketplace/catalog/zip \
  -H "Authorization: Bearer $TOKEN" \
  -F 'files=@agent-a.zip' -F 'files=@agent-b.zip'
# → {"assets":[{"asset_key":"agent-a",...},{"asset_key":"agent-b",...}]}
# list catalog
curl http://localhost:8100/api/marketplace/catalog -H "Authorization: Bearer $TOKEN"
# → {"assets":[{"asset_key":"cve-scanner","installed":false,"active_version":null, ...}]}
# install (hot-deploy seam: tbl_agent_config upsert)
curl -X POST http://localhost:8100/api/marketplace/install/cve-scanner \
  -H "Authorization: Bearer $TOKEN"
# → {"id":1,"asset_key":"cve-scanner","version":"1.0.0","status":"installed","active":true,"agent_config_key":"cve-scanner"}
# uninstall
curl -X DELETE http://localhost:8100/api/marketplace/install/cve-scanner -H "Authorization: Bearer $TOKEN"

# ── Marketplace remote registry (F-MP E1.5) — requires MARKETPLACE_REMOTE_ENABLED=true ──
curl http://localhost:8100/api/marketplace-remote/ping -H "Authorization: Bearer $TOKEN"
curl http://localhost:8100/api/marketplace-remote/catalog -H "Authorization: Bearer $TOKEN"   # cached (sync_interval TTL)
# download remote asset → SHA256 verify → (if valid addon ZIP) live hot-deploy → merge into local catalog
curl -X POST http://localhost:8100/api/marketplace-remote/install/remote-scanner \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"hot_deploy":true}'
# → {"registered":true,"deployed":true,"checksum":"<sha256>","asset":{...,"source":"remote"}}
#   deployed=true → /api/addon/{key}/... is live immediately with no restart (§7.6, reuses upload pipeline in-proc)

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

# Component palette (impl/25 §7.2.3) — list built-in/system/addon agent APIs as components
curl http://localhost:8100/api/workflow/components -H "Authorization: Bearer $TOKEN"
# → {"components":[{"agent_key":"marketplace","agent_name":"Marketplace","category":"builtin",
#                    "method":"GET","path":"/api/marketplace/catalog","capability_key":"list catalog",
#                    "label":"Marketplace-list catalog"}, ...]}
# agent node actually invokes the component (executes when config.path is set) — actor token forwarded, v1 stub if omitted
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"catalog-check","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"a","type":"agent","config":{"agent_key":"marketplace","method":"GET","path":"/api/marketplace/catalog"}}],
      "edges":[{"source":"t","target":"a"}]}}'
curl -X POST http://localhost:8100/api/workflows/2/run -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"input":{}}'
# → {"status":"completed","output_json":"{...\"a\":{\"agent_key\":\"marketplace\",\"invoked\":true,\"status\":200,\"body\":{...}}}"}
# http node (§7.2.3) — direct external URL call (admin-trust boundary, SSRF tracked in §6)
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{
    "name":"notify-hook","definition_json":{
      "nodes":[{"id":"t","type":"trigger"},
               {"id":"h","type":"http","config":{"url":"https://example.com/hook","method":"POST","body":{"msg":"$t.input.msg"}}}],
      "edges":[{"source":"t","target":"h"}]}}'

# Webhook ingress trigger (impl/26 §7.2.4) — creating trigger_type="webhook" exposes the secret once
curl -X POST http://localhost:8100/api/workflows -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"wh-demo","trigger_type":"webhook","definition_json":{"nodes":[{"id":"t","type":"trigger"}],"edges":[]}}'
# → {"id":3,...,"trigger_type":"webhook","webhook_secret":"<plaintext, only in this response>"}
# external systems trigger with just the secret — no JWT needed
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook -H "X-Webhook-Secret: <secret above>" \
  -H 'Content-Type: application/json' -d '{"event":"deploy-finished"}'
# → {"id":5,"status":"completed","trigger_source":"webhook",...}  (agent/http nodes run as the creator)
# HMAC signature mode (impl/29 §7.2.4.1) — the secret itself never travels on the wire
BODY='{"event":"deploy-finished"}'
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "<secret above>" | cut -d' ' -f2)"
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook -H "X-Webhook-Signature: $SIG" \
  -H 'Content-Type: application/json' -d "$BODY"
# Rotate the secret — old one is invalidated immediately
curl -X POST http://localhost:8100/api/workflows/3/trigger/webhook/rotate -H "Authorization: Bearer $TOKEN"
# → {"id":3,...,"webhook_secret":"<new plaintext, only in this response>"}

# enabled toggle (impl/30 §7.2.7) — e.g. reviewing a Dify import (always disabled) before enabling it
curl -X PATCH http://localhost:8100/api/workflows/4 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
# → {"id":4,"enabled":true,...}

# Partial edit (impl/32 §7.2.8) — the builder's save path. A definition change bumps version +1
curl -X PATCH http://localhost:8100/api/workflows/4 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"renamed","definition_json":{"nodes":[{"id":"t","type":"trigger","position":{"x":40,"y":120}}],"edges":[]}}'
# → {"id":4,"name":"renamed","version":2,...}  (omitted fields preserved; an empty body {} returns 422)

# Dify DSL Import (impl/28 §7.2.6, mode A) — paste YAML → SeCMP workflow (always created disabled)
curl -X POST http://localhost:8100/api/workflows/import/dify-dsl -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"dsl":"app:\n  name: demo\nworkflow:\n  graph:\n    nodes:\n      - id: n1\n        data: {type: start}\n    edges: []\n"}'
# → {"id":4,"name":"demo","enabled":false,"dify_dsl_version":"unknown",
#    "definition_json":{"nodes":[{"id":"n1","type":"trigger"}],"edges":[]},"warnings":[]}

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

# ── Guardrails (F-GRD) — domain catalog + multi-domain evaluation (§7.8.7) ──
curl http://localhost:8100/api/guardrails/domains -H "Authorization: Bearer $TOKEN"
# → {"domains":[{"domain_key":"global","status":"functional","is_required":1,"filter_enabled":1,...},
#               {"domain_key":"finance-banking","status":"functional","filter_enabled":0,...}, ...]}
# domain 'filter' toggle (admin) — required (global) cannot be disabled (409)
curl -X PUT http://localhost:8100/api/guardrails/domains/finance-banking/filter -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
# test — without domains: evaluates global (required) + filter-enabled domains; or pass domains explicitly
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"open an account without KYC","domains":["global","finance-banking"]}'
# → {"decision":"block","evaluatedDomains":["global","finance-banking"],"perDomain":[...], ...}
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"email me at secret@corp.com"}'
# → {"decision":"redact",...}  low-risk PII (email/phone/IP) = masked
# promotion (impl/11): 1 high-risk category (secret/financial/national-id) → block, 2+ → escalate
curl -X POST http://localhost:8100/api/guardrails/test -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"text":"key sk-abcdefghijklmnopqrstuvwx","domain":"global"}'
# → {"decision":"block","riskScore":0.7,"matchedRules":["secret.api_key"],...}
#   with agent toggle ON, block/escalate inputs are cut off by the gate (HTTP 403 [BLOCKED]) during Orchestrator calls
# per-agent domain toggle (admin/supervisor) — actually enforced by the Orchestrator gate below
curl -X PUT http://localhost:8100/api/guardrails/agents/marketplace/config -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"domain_key":"global","enabled":true,"io_scope":"both"}'
# once enabled, any Orchestrator call_api invocation against marketplace (e.g. registering an asset whose
# description contains PII) is intercepted by guardrails_gate.py, which masks it before forwarding and
# writes a guardrails_decision_log entry.
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
python test/impl/7/test_guardrails_gate.py  # F-GRD Orchestrator gate (fresh sqlite, 15 asserts)
python test/impl/9/test_marketplace_remote.py  # F-MP remote registry (fresh sqlite, 14 asserts)
python test/impl/10/test_remote_hotdeploy.py   # F-MP real ZIP hot-deploy §7.6 (fresh sqlite, 8 asserts)
python test/impl/11/test_guardrails_escalation.py  # F-GRD block/escalate promotion (fresh sqlite, 14 asserts)
python test/impl/13/test_guardrails_mcp.py     # F-GRD MCP Server proxy (6 asserts)
python test/impl/14/test_local_zip_deploy.py   # F-MP local real ZIP deploy (10 asserts)
python test/impl/15/test_pgvector_adapter.py   # F-RAG pgvector adapter (6 asserts)
python test/impl/16/test_gpg_mtls.py           # F-MP GPG signature + mTLS (10 asserts, needs gpg binary)
python test/impl/17/test_dashboard_summary.py  # Dashboard realtime widgets (10 asserts)
python test/impl/19/test_playground_tokens.py  # F-PG token usage tracking (6 asserts)
python test/impl/23/test_workflow_components.py  # F-WF component palette+real invoke+http node (18 asserts)
python test/impl/24/test_workflow_webhook.py     # F-WF webhook ingress trigger (15 asserts)
python test/impl/26/test_dify_dsl_import.py      # F-WF Dify DSL Import adapter mode A (30 asserts)
python test/impl/27/test_webhook_security.py     # F-WF webhook security hardening (rotate/HMAC/rate limit) (12 asserts)
python test/impl/28/test_workflow_enabled_toggle.py  # F-WF enabled toggle PATCH (11 asserts)
python test/impl/29/test_pgvector_benchmark.py     # F-RAG pgvector benchmark (7 asserts, needs real PostgreSQL: docker compose up -d postgres)
python test/impl/30/test_workflow_builder_patch.py # F-WF full-screen builder partial-edit PATCH (17 asserts)
make lint                                   # ruff
cd front && pnpm exec tsc --noEmit && pnpm exec vite build   # frontend type-check + build
```
Per-iteration scenario·result: `test/impl/<Nth>/{scenario,result}.md`. impl/3 (F-WF Designer + F-MP frontend), impl/8 (dashboard), impl/12 (nav 'Users' moved to bottom), impl/25 (F-WF editable canvas, logical impl/27) touch no backend code, so they're static verification (tsc/build) only. impl/26 (F-WF Dify DSL Import, logical impl/28) has full backend+frontend tests across every mapped node type.

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
| Workflow canvas nodes invisible (`visibility: hidden`) | React Flow v12 only shows a node once its measured dimensions land back in the controlled state — rebuilding rfNodes from scratch every render drops `measured` | **Fixed (impl/32)** — keep RF Node[] in React state and absorb dimension changes via `applyNodeChanges` (`WorkflowBuilderPage`/`WorkflowCanvas`). Avoid reintroducing the rebuild-per-render pattern |

---

## 10. Next Steps (PRD backlog)

The 6 §9.5 backlog items (F-WF canvas · F-RAG pgvector · F-GRD MCP · local real-ZIP · dashboard widgets · GPG/mTLS)
are **all done in impl/13~18**. **impl/25 (physical `test/impl/23`) — F-WF component palette + agent-node real
invocation + http node — done** (§7.2.3). **impl/26 (physical `test/impl/24`) — F-WF webhook ingress trigger —
done** (§7.2.4). **impl/27 (physical `test/impl/25`) — F-WF editable canvas — done** (§7.2.5).
**impl/28 (physical `test/impl/26`) — F-WF Dify DSL Import mode A — done** (§7.2.6).
**impl/29 (physical `test/impl/27`) — F-WF webhook security hardening — done** (§7.2.4.1,
rotation+HMAC+rate limit).
**impl/30 (physical `test/impl/28`) — F-WF `enabled` toggle PATCH — done** (§7.2.7).
**impl/31 (physical `test/impl/29`) — F-RAG pgvector real-infra benchmark — done** (§7.5.1,
Recall@10=1.000 · p95=20.8ms).
**impl/32 (physical `test/impl/30`) — F-WF full-screen workflow builder — done** (§7.2.8,
Flowise/Dify-style rebuild + partial-edit PATCH).
All 4 user-specified sequential items plus all 3 follow-up items are now complete. What remains is
external-infra validation & roadmap:

- **Real-infra validation (remaining)**: mTLS handshake (private CA), real wise-Guardrails MCP integration (code & fallback done). pgvector benchmark is done (impl/31).
- **Embedding model swap**: local hashing → sentence-transformers/OpenAI (pin embedding_version).
- **Multi-tenancy namespace/physical, Qdrant** — roadmap (P5).
- **Code node**: needs a sandbox security review first (§3 Out of Scope).
- **Distributed webhook rate limiting** (single-process → shared across instances), documenting the "rotate webhook secrets after JWT_SECRET_KEY rotation" ops procedure — deferred in impl/29 (§7.2.4.1).
- ~~Full workflow edit PATCH~~ — **done (impl/32, §7.2.8)**. Changing the trigger type is still create-time only.
- ~~Canvas edge `when` inline editing~~ — **done (impl/32 inspector, §7.2.8)**. **Node grouping/undo-redo/copy-paste/auto-layout/run-status overlay** — deferred in impl/32 (§7.2.8).
- **Dify mode B (Delegate)/mode C (Round-trip), file upload, real Dify instance validation** — deferred in impl/28 (§7.2.6).
- **F-PG cost tracking** (once Claude is wired), eval execution.
- **Ops docs**: GPG key rotation, mTLS cert issuance procedures.

> Completed: Orchestrator gate (impl/7) · dashboard (impl/8) · block/escalate (impl/11) · MCP proxy (impl/13) · local real-ZIP (impl/14) · pgvector adapter (impl/15) · GPG+mTLS (impl/16) · dashboard widgets (impl/17) · React Flow canvas (impl/18).
