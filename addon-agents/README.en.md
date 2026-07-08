# Addon Agent Guide

> The extension module system for **SeCuardian**.  
> Administrators can create custom Agents (bulletin board, survey, inventory, etc.) as zip files and upload them — the API and DB are deployed immediately (hot-deploy) without restarting the app.  
> If a frontend component (`-front.tsx`) is included, it appears in the sidebar automatically after a frontend rebuild.

---

## Creating Agents

Two methods available:

| Method | Description | Entry |
|--------|-------------|-------|
| **Scaffolding Wizard** | Choose from 9 agent types → enter name/description/domain → ZIP auto-generated | Agent Management → New Agent → **Scaffolding** tab |
| **ZIP Upload** | Upload a ZIP you built yourself | Agent Management → New Agent → **ZIP Upload** tab |

The Scaffolding Wizard calls `/api/addon-agents/scaffold` to generate the ZIP server-side. A "Deploy Now" button lets you register it immediately.

---

## Directory Structure

```
addon-agents/
├── _templates/              Developer templates (includes ready-to-use zip)
│   ├── Board/               App Agent — bulletin board + comments
│   │   ├── Board-app.py
│   │   ├── Board-front.tsx
│   │   ├── Board-sql.sql
│   │   └── Board-meta.json
│   ├── RagAgent/            RAG Agent — document embedding + vector search Q&A
│   │   ├── RagAgent-app.py
│   │   ├── RagAgent-sql.sql
│   │   └── RagAgent-meta.json
│   ├── ServiceAgent/        Service Agent — backend business logic
│   │   ├── ServiceAgent-app.py
│   │   └── ServiceAgent-meta.json
│   ├── ToolProxyAgent/      Tool Proxy Agent — external API → MCP adapter
│   │   ├── ToolProxyAgent-app.py
│   │   └── ToolProxyAgent-meta.json
│   ├── Board.zip            ↗ Ready-to-upload packages
│   ├── RagAgent.zip
│   ├── ServiceAgent.zip
│   └── ToolProxyAgent.zip
└── deployed/                Auto-created after upload (builtin agents excluded — do not edit manually)
    └── {agent_key}/
        ├── {AgentName}-app.py
        ├── {AgentName}-front.tsx   (optional)
        ├── {AgentName}-sql.sql     (optional)
        └── {AgentName}-meta.json
```

> **Builtin agents** (`deployed/board/`) are tracked in git and loaded automatically on app start.

---

## File Naming Convention

| Component | File pattern | Role |
|-----------|-------------|------|
| Metadata | `{AgentName}-meta.json` | Agent type, capability, and governance definition (recommended) |
| API router | `{AgentName}-app.py` | Exports a FastAPI `router` object (optional) |
| Frontend component | `{AgentName}-front.tsx` | React component — self-contained i18n + dark mode (optional) |
| DB schema | `{AgentName}-sql.sql` | Table creation DDL, auto-applied (optional) |
| Package | `{AgentName}.zip` | Flat zip of the above files |

> **AgentName**: PascalCase recommended (e.g. `Board`, `SurveyForm`, `Inventory`)  
> At least one of `-app.py` or `-front.tsx` is required.  
> The zip must contain files at the root level — no subdirectories.

### emb_ prefix — naming convention for embedded-origin agents

- **`emb_` prefix** marks the ADDON packaging of a platform built-in (embedded) agent
  (e.g. `emb_vasca-cve`, `emb_cilium-netpol`). Pure user-authored ADDONs are named without the prefix.
- When converting or newly porting a built-in agent to an ADDON, always use the `emb_` prefix,
  keep the source in `addon-agents/zip/emb_{key}/`, and package it as `addon-agents/zip/emb_{key}.zip`.
- The meta.json `key` (or `agent_key`) field must also carry the `emb_` prefix,
  and a `base_agent` field should record the original built-in router provenance.
- ⚠️ Never use `from __future__ import annotations` in an addon `-app.py` —
  the dynamic loader (`spec_from_file_location`) does not register the module in `sys.modules`,
  so pydantic cannot resolve postponed annotations on request-body models (500 error).

### Screen alignment standard (`-front.tsx`, PRD §7.11 impl/24)

- Apply the **`.page` class to the top-level container** of an agent screen (`-front.tsx`)
  (defined in `front/src/index.css` = `w-full max-w-6xl p-4 sm:p-6`): **left-aligned, responsive, width-capped**, unified across all screens.
- No `mx-auto` (centering), no per-page `max-w-4xl/5xl` — standardize via `.page`.
- e.g. `<div className="page space-y-4"> … </div>` (grids: `page grid grid-cols-3 gap-4`).
- **Exception**: full-height interactive layouts (`flex flex-col h-full`, e.g. chat/terminal — AI Assistant, ShellAgent, emb_server-shell) do NOT use `.page`. All other content/form screens follow `.page`.

---

## Development Workflow (Makefile)

The **Makefile** in `addon-agents/` automates initialization, validation, and packaging.

```bash
# Run from the addon-agents/ directory
cd addon-agents/

make init    AGENT=Survey   # scaffold from Board template
make test    AGENT=Survey   # validate structure & syntax
make publish AGENT=Survey   # create zip package
make clean   AGENT=Survey   # remove generated files
```

| Target | Description |
|--------|-------------|
| `make init AGENT=<name>` | Copy Board template + replace `Board` → `<name>` into `_templates/<name>/` |
| `make test AGENT=<name>` | Validate: files, Python syntax, router export, SQL structure, React export |
| `make publish AGENT=<name>` | Create `_templates/<name>.zip` (ready to upload) |
| `make clean AGENT=<name>` | Delete generated directory and zip |

---

## Writing the Files

### `{AgentName}-sql.sql`

- Use SQLite/PostgreSQL compatible syntax (`NOT is_deleted`, `CURRENT_TIMESTAMP`)
- Prefix table names with `tbl_`
- Use `CREATE TABLE IF NOT EXISTS` for idempotency

```sql
CREATE TABLE IF NOT EXISTS tbl_myfeature (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    is_deleted  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

> PostgreSQL-specific syntax (`SERIAL`, `BOOLEAN`, `NOW()`) is auto-converted on upload.

### `{AgentName}-app.py`

**Required rules:**
- Export an `APIRouter` instance as the variable `router`
- Use Wise app modules: `from app.core.deps import get_current_user`, `from app.db import fetch_all, fetch_one, execute_write, execute_insert, _PH`
- Final mount path: `/api/addon/{agent_key}/{prefix}/...`

```python
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.db import _PH, execute_insert, fetch_all

router = APIRouter(prefix="/items", tags=["myfeature"])

@router.get("")
async def list_items(user: dict = Depends(get_current_user)):
    return {"items": await fetch_all("SELECT * FROM tbl_myfeature WHERE NOT is_deleted")}
```

### `{AgentName}-front.tsx`

- API base path: `/addon/{agent_key}/{prefix}/...` (client.baseURL="/api" already included)
- Use `import client from "../../../api/client"` (Wise axios instance)
- **Self-contained i18n**: read `localStorage.getItem("locale")` + subscribe to `localeChanged` events
- **Dark mode**: Tailwind `dark:` classes (auto-synced with app theme)
- **No internal page title**: the top header (AppLayout) already shows the agent name,
  so do NOT render the agent name as an `<h1>` at the top of the component. Show a
  one-line page description with `<p className="text-sm text-gray-500 dark:text-gray-400">`
  instead. (Sub-view headings — e.g. a "New Post" form heading — are fine.)

```tsx
const LOCALE = {
  ko: { desc: "내 기능을 관리합니다." },
  en: { desc: "Manage my feature." },
};

function useLocale() {
  const [locale, setLocale] = useState(() => localStorage.getItem("locale") || "ko");
  useEffect(() => {
    const h = () => setLocale(localStorage.getItem("locale") || "ko");
    window.addEventListener("localeChanged", h);
    return () => window.removeEventListener("localeChanged", h);
  }, []);
  return (k: string) => LOCALE[locale]?.[k] ?? LOCALE.ko[k] ?? k;
}

export default function MyFeaturePage() {
  const t = useLocale();
  // Title is shown by the top header — render only the description here
  return <p className="text-sm text-gray-500 dark:text-gray-400">{t("desc")}</p>;
}
```

### `{AgentName}-meta.json`

Used by the Orchestrator for capability-based routing and governance gates.

> **Description i18n**: provide both `description` (Korean — shown when the UI language is ko)
> and `description_en` (English — shown when the UI language is en; falls back to `description`
> if missing). Applied to agent-management cards/tooltips and the Q&A fallback header of
> screen-less addons.

**Supported agent_type values:**

| agent_type | Use case |
|------------|----------|
| `app` | UI + CRUD apps (bulletin board, survey, etc.) |
| `service` | Backend business logic |
| `rag` | Document embedding + vector search Q&A |
| `tool-proxy` | External REST API → MCP adapter |
| `reviewer` | Response quality / risk review gate |
| `execution` | Code / command execution Agent |
| `hitl` | Human-in-the-Loop approval gate |
| `memory` | Long-term memory / context storage |
| `federation` | Bridge to external Agent systems |

**Full schema:**

```json
{
  "agent_type": "service",
  "version": "1.0.0",
  "display_name": "My Agent",
  "description": "Agent description",
  "capabilities": [
    {
      "verb": "process",
      "domain": "service.myfeature",
      "description": "Feature description",
      "input_schema": {
        "type": "object",
        "properties": { "input": { "type": "object" } },
        "required": ["input"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "output": { "type": "object" },
          "status": { "type": "string" }
        }
      },
      "qos": {
        "max_latency_ms": 10000,
        "supports_async": true,
        "supports_streaming": true
      }
    }
  ],
  "governance": {
    "data_classification": "internal",
    "human_approval_required": false,
    "audit_level": "standard"
  },
  "required_env": [],
  "optional_env": ["ANTHROPIC_API_KEY"],
  "min_platform_version": "2.0.0"
}
```

| Field | Description |
|-------|-------------|
| `capabilities[].verb` | Used by Orchestrator for intent routing (`retrieve`, `process`, `proxy`, `manage`, etc.) |
| `capabilities[].domain` | Format: `{category}.{subdomain}` |
| `governance.human_approval_required` | Forces HITL gate when `true` |
| `required_env` | Deployment warning if unset (e.g. `TOOL_PROXY_BASE_URL`) |
| `optional_env` | Optional env vars that enhance functionality |
| `min_platform_version` | Platform version compatibility check |

---

## Packaging and Upload

```bash
# Makefile (recommended)
make publish AGENT=MyFeature
# → _templates/MyFeature.zip

# Manual
zip -j _templates/MyFeature.zip \
    _templates/MyFeature/MyFeature-app.py \
    _templates/MyFeature/MyFeature-front.tsx \
    _templates/MyFeature/MyFeature-sql.sql
```

### Upload steps

1. Go to **Agent Management** → click **New Agent** → **ZIP Upload** tab
2. Select the zip file (or download a template zip and upload it)
3. Automatic processing:
   - `-sql.sql` executed → DB tables created
   - `-app.py` dynamically loaded → API active immediately
   - `-front.tsx` → copied to `front/src/pages/addon/deployed/{key}.tsx`
   - Records inserted into `tbl_addon_agents` + `tbl_agent_config`
4. **Rebuild frontend** → sidebar menu appears automatically:
   ```bash
   cd front && npm run build
   pm2 restart wise-fe
   ```

---

## Hot-Deploy Mechanism

```
zip upload
    │
    ▼
Files saved to addon-agents/deployed/{agent_key}/
    │
    ├─ {Name}-sql.sql executed → DB tables created
    │
    ├─ {Name}-app.py loaded via importlib
    │   → extract module.router
    │   → app.include_router(router, prefix="/api/addon/{agent_key}")
    │
    ├─ {Name}-front.tsx → front/src/pages/addon/deployed/{key}.tsx
    │   → rebuild frontend → /addon/{key} route activates automatically
    │
    └─ INSERT into tbl_addon_agents + tbl_agent_config

On app restart: addon_agent_loader._load_all_from_disk()
→ query active addons from DB → re-register all routers automatically
```

---

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/addon-agents/` | List registered Addons | Login |
| `POST` | `/api/addon-agents/upload` | Upload zip + hot-deploy | supervisor/admin |
| `POST` | `/api/addon-agents/scaffold` | Scaffolding Wizard → generate zip (or deploy immediately) | supervisor/admin |
| `PATCH` | `/api/addon-agents/{key}/toggle` | Toggle active/inactive | supervisor/admin |
| `DELETE` | `/api/addon-agents/{key}` | Delete Agent | supervisor/admin |
| `GET` | `/api/addon-agents/templates/list` | List developer templates | Login |
| `GET` | `/api/addon-agents/templates/download/{file}` | Download template zip | Login |

---

## Constraints and Notes

| Item | Details |
|------|---------|
| Security | Uploaded Python files are executed on the server — protect with supervisor/admin access |
| Router removal | Fully removing a router requires an **app restart** after deletion |
| Frontend rebuild | If `-front.tsx` is included, run `npm run build` + restart server |
| File size | Zip files should be under 10MB |
| Builtin agents | `deployed/board/` can be edited directly (tracked in git) |

---

## Builtin Agents

| Agent | Description | Path |
|-------|-------------|------|
| **Board** | Bulletin board (create/edit/delete posts, write/delete comments, pagination) | `/addon/board` |

### ADDON packaging of built-in agents (`zip/emb_*`) + pure ADDONs

ADDON packagings of built-in agents (seeded in tbl_agent_config) carry the `emb_` prefix;
pure ADDONs (not in the built-in list) are named without it.
Upload `addon-agents/zip/{key}.zip` via Agent Management to deploy at `/api/addon/{key}`.

**Built-in-origin (`emb_`), 13:**
`emb_agentic-soc` · `emb_ai-eval-gate`(new port) · `emb_ai-redteam` · `emb_behavior-noti` ·
`emb_cilium-netpol` · `emb_isms-p-evidence`(new port) · `emb_neosync-dlp` · `emb_otel-collector` ·
`emb_shuffle-soar` · `emb_teleport-pam` · `emb_teler-ids` · `emb_vasca-cve`(new port) ·
`emb_velociraptor-dfir`

**Pure ADDONs (no prefix), 4:** `caddy-proxy` (reverse-proxy monitor) · `grafana-dashboard` (dashboard RAG + sql) · `truffle-scan` (secret-scan receiver) · `ai-traffic-monitor` (browser AI-assistant traffic-usage monitor — wraps vnstat/nethogs/tcpdump/tshark; ITManually Batch 13)

> `general` (Orchestrator) and `chat` (AI Assistant) are required core agents and excluded from conversion.
> Built-in agents themselves keep their original keys and built-in-tab display names without emb_ —
> the prefix applies only to ADDON packagings (zip / addon key).
> The three new ports use environment-variable configuration (unlike the settings-based built-ins) and
> keep independent in-memory stores from their built-in counterparts.

---

## Available Templates

| Template | agent_type | Description | File |
|----------|------------|-------------|------|
| **Board** | `app` | Bulletin board with comments — same implementation as the builtin Board agent. Includes React UI | `Board.zip` |
| **RagAgent** | `rag` | Document ingestion, chunking, vector search + SSE-streaming Q&A. Embedding function swap point included | `RagAgent.zip` |
| **ServiceAgent** | `service` | Backend business logic skeleton. `process` capability, async/streaming support | `ServiceAgent.zip` |
| **ToolProxyAgent** | `tool-proxy` | Adapts external REST APIs as MCP Tools. Requires `TOOL_PROXY_BASE_URL` | `ToolProxyAgent.zip` |

### RagAgent Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/addon/ragagent/ingest` | Upload document + chunk + embed |
| `GET` | `/api/addon/ragagent/documents` | List uploaded documents |
| `DELETE` | `/api/addon/ragagent/documents/{id}` | Delete document + chunks (supervisor/admin) |
| `POST` | `/api/addon/ragagent/search` | Cosine similarity vector search |
| `POST` | `/api/addon/ragagent/qa` | RAG-based Q&A — SSE streaming response |

> The `_embed()` function is a prototype implementation (hash-based). Replace with Ollama `nomic-embed-text` or OpenAI `text-embedding-3-small` for production use.

---

_SeCuardian · Addon Agent Extension System_
