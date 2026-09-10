# SeCuardian Agent Master Catalog — Implementation Status + Expansion Roadmap

> Scope: all agents **already implemented** across SeCuardian (the product) and SeCuardian-Marketplace
> (asset distribution), combined with the **candidates to implement** derived from
> `.docs/extra-agents/ADDON-AGENTS.en.md`.
> The classification mirrors [extra-agents/ADDON-AGENTS.en.md](../.docs/extra-agents/ADDON-AGENTS.en.md)
> (inventory → classification/coverage → implementation guidance).
> Distributed assets live under `marketplace-assets/{security,addon,builtin,utilities}/`.

---

## 0. Architecture Background

SeCuardian is a multi-agent security platform that wires a **6-layer security model** to AI agents. The
orchestrator classifies user intent and routes to the right agent. Agents come in 3 forms:

| Form | Definition | Delivery | Location |
|---|---|---|---|
| **Embedded** | `app/routers/router_*.py` compiled into the app; seeded into `tbl_agent_config` via `make seed-security` | in the app build | SeCuardian `app/routers/` |
| **ADDON** | ZIP upload → dynamic loader hot-deploys, no restart | ZIP package | `marketplace-assets/security|utilities/` |
| **Template** | Scaffolding base for new agents (Board/Rag/Service/Shell/ToolProxy/UserManager) | ZIP package | `marketplace-assets/addon/` |

> Several embedded routers are also packaged as ADDON editions (`router_vasca`→`vasca-cve`,
> `router_isms`→`isms-p-evidence`, `router_ai_eval`→`ai-eval-gate`). Embedded = always loaded, ADDON =
> optional install.

Layer definitions: **L1** Identity & access · **L2** Endpoint · **L3** Network · **L4** Data ·
**L5** Detection/Response · **L6** AI Security · **Cross** cross-cutting.

---

## 1. Implementation Inventory (agents already built)

### 1.1 L1 — Identity & Access

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `keycloak-monitor` (`router_keycloak`) | E01 | Embedded | Keycloak SSO/IAM monitor (realm/client/user/session) |
| `logto-monitor` (`router_logto`) | E01 | Embedded | Logto IAM monitor (alternative IdP) |
| `vault-monitor` (`router_vault`) | E02 | Embedded | HashiCorp Vault dynamic secrets / encryption monitor |
| `teleport-pam` | E17 | ADDON(`security/`) | Teleport privileged-access (PAM) session audit / active-session query |

### 1.2 L2 — Endpoint

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `falco-receiver` (`router_falco`) | E03 | Embedded | Falco runtime event receiver |
| `harbor-scanner` (`router_harbor`) | E03 | Embedded | Harbor registry image-scan monitor |
| `hardening-auditor` (`router_hardening`) | E05 | Embedded | Linux server hardening audit receiver |
| `vasca-cve` (`router_vasca` + ADDON) | E07 | Embedded+ADDON | Host/container CVE scanning (worker: **VASCA_worker**, Go, bundled) |
| `behavior-noti` | E16 | ADDON(`security/`) | Host anomalous-behavior event webhook receiver (worker: **BehaviorNotiService_worker**, C++, bundled) |

### 1.3 L3 — Network

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `caddy` (`router_caddy`) + `caddy-proxy` | E04 | Embedded+ADDON(util) | Caddy reverse-proxy admin-API monitor / config reload |
| `crowdsec-monitor` (`router_crowdsec`) | E04 | Embedded | CrowdSec threat detection/blocking monitor |
| `cilium-netpol` (`router_cilium`) | E09 | Embedded+ADDON | Cilium eBPF network policy + Hubble flows (microsegmentation) |
| `istio-mtls` (`router_istio`) | E10 | Embedded | Istio service-mesh mTLS monitor |
| `teler-ids` (`router_teler`) | E11 | Embedded+ADDON | teler HTTP intrusion detection (IDS) alert receiver / stats |
| `wireproxy-ztna` (`router_wireproxy`) | E12 | Embedded | WireProxy-based ZTNA |

### 1.4 L4 — Data

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `neosync-dlp` (`router_neosync`) | E14 | Embedded+ADDON | Neosync DLP pipeline monitor / job management |
| `truffle-scan` | E08 | ADDON(util) | TruffleHog secret-scan result webhook receiver / query |

### 1.5 L5 — Detection / Response

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `wazuh-siem` (`router_wazuh`) | E06 | Embedded | Wazuh SIEM/XDR monitor |
| `observability` (`router_observability`) | E06 | Embedded | Observability stack monitor |
| `shuffle-soar` (`router_soar`) | E13 | Embedded+ADDON | Shuffle SOAR workflow trigger / result collection (execution) |
| `velociraptor-dfir` (`router_dfir`) | E18 | Embedded+ADDON | Velociraptor endpoint forensic hunting / artifact collection |
| `agentic-soc` (`router_agentic_soc`) | E20/E21 | Embedded+ADDON | A2A orchestration of security agents, incident triage / playbooks (federation) |

### 1.6 L6 — AI Security

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `ai-eval-gate` (`router_ai_eval`) | E20 | Embedded+ADDON | Pre-deploy PyRIT/SkillSpector/agentshield evaluation + gate verdict (disabled by default, security-team approval required) |
| `ai-redteam` (`router_redteam`) ⚠️ | E19/E21 | Embedded+ADDON | PyRIT/SkillSpector adversarial scan for LLM jailbreak / prompt injection (**isolated network + written approval required**) |

### 1.7 Cross — Compliance / Observability / Adapter

| Agent | Epic | Form | Summary |
|---|---|---|---|
| `compliance-isms` / `isms-p-evidence` (`router_isms`) | E22 | Embedded+ADDON | ISMS-P certification audit-evidence auto-collection / control checks (Wazuh·Keycloak·Vault·Teleport·VASCA·Neosync·SOAR) |
| `otel-collector` (`router_otel`) | E15 | Embedded+ADDON | Exposes OpenTelemetry Collector health/pipelines/metrics as MCP Tools |
| `grafana-dashboard` | — | ADDON(util) | Embeds Grafana dashboard panels, answers via vector search (RAG) |
| `ai-traffic-monitor` | E15 | ADDON(util) | Quantifies traffic volume of browser-auto-connected AI assistants (wraps vnstat/nethogs/tshark) |

### 1.8 Platform Built-in Agents (SeCuardian-Marketplace `builtin/`)

Not security-domain — these run **platform operations** themselves (packaged editions of the Marketplace
app's `router_*`).

| Agent | Type | Summary |
|---|---|---|
| `guardrails` | service | Domain content-safety verdicts (PII, credit info, etc.). global + 24 domain rulesets (finance/medical/manufacturing/public, etc.) |
| `marketplace` | service | Catalog register/install/uninstall of agent/workflow/RAG/tool-proxy assets |
| `playground` | service | Interactive prompt×model LLM experimentation (Ollama integration, degrade fallback) |
| `rag` | rag | Collection CRUD / document ingest / hybrid search |
| `workflow` | service | DAG workflow CRUD + execution / HITL approval / cancel |

### 1.9 Development Templates (SeCuardian-Marketplace `addon/`)

Baseline templates for scaffolding new agents; the starting point for §3.

| Template | Type | Use |
|---|---|---|
| `Board` | app (fe+be) | CRUD board — reference example for a screen-bearing app agent |
| `UserManager` | app (fe+be) | User search / CRUD / password reset |
| `RagAgent` | rag | Document-embedding + vector-search RAG skeleton |
| `ServiceAgent` | service | Backend business-logic service skeleton |
| `ShellAgent` | service | Read-only CLI/shell diagnostics (**reference for the CLI-wrapping safety model**, supervisor/admin) |
| `ToolProxyAgent` | tool-proxy | External REST API → MCP Tool adapter |

---

## 2. Coverage Analysis — Implemented vs. To-Implement

Mapping the candidates (A–G) from `extra-agents/ADDON-AGENTS.en.md` §2 onto the 6-layer coverage:
SeCuardian densely covers the **defender view (internal-asset monitoring across L1–L6)** but still has gaps
in the **external attack-surface view** and **agentic-AI self-security**.

### 2.1 Well-Covered (already implemented)

- **Internal asset monitoring**: IAM (Keycloak/Vault/Teleport) · Endpoint (Falco/Harbor/VASCA/Behavior) ·
  Network (Cilium/Istio/teler/CrowdSec/WireProxy) · Data (Neosync/TruffleHog) · Detection-response
  (Wazuh/SOAR/DFIR/SOC).
- **Compliance**: ISMS-P evidence auto-collection.
- **AI security (internal)**: pre-deploy evaluation gate (ai-eval-gate) + red-team scanning (ai-redteam).

### 2.2 Gaps → Candidates to Implement (basis: extra-agents)

| Candidate (extra-agents §2) | Gap it fills | Layer | Priority | Reuse base |
|---|---|---|---|---|
| **A. `attack-surface-recon`** | External attack-surface (OSINT) recon — currently none | L3 ext | High | `ai-traffic-monitor`/`ShellAgent` (CLI wrapping) |
| **B. `agentic-threat-model`** | Threat-modeling of our own AI agent/MCP config — currently none | L6 ext | High | static analysis, read-only |
| **C. `api-vuln-scan`** | Active API OWASP Top 10 scanning (teler/vasca are receive-type) | L2/L4 | High | `ShellAgent` + VAmPI test target |
| **D. `malware-hunt`** | Supply-chain-disguised malware IOC hunting | L2 ext | Medium | adjacent to `truffle-scan` |
| **E. `soc-intel-fusion`** | Unified CVE/EPSS/KEV/ATT&CK lookup | L5 ext | Medium | `cve-mcp-server` MCP proxy (`ToolProxyAgent`) |
| **F. `ad-security-scan`** | Active Directory misconfiguration checks | L1 ext | Medium | `ShellAgent` + adjacent to `teleport-pam` |
| **G. `cicd-security-scan`** | CI/CD pipeline (GitHub Actions) security static analysis — currently none | L4 supply-chain | Medium | gato-x (static-analysis mode) + adjacent to `truffle-scan`/`harbor` |

### 2.3 Held Back by Policy (conflicts with the defender identity)

- **Autonomous offense/exploit family** (hexstrike-ai / strix / T3MP3ST / Decepticon): embedding as a
  first-class product feature needs care. If adopted, restrict to **approved isolated labs** + target
  allowlist + approval log. Follows `ai-redteam`'s isolated-network model.
- **Kernel zero-day / AV·EDR evasion**: unfit for Addon packaging — keep as offline research tools.

---

## 3. Implementation Guidance

### 3.1 New-ADDON Development Procedure (standard flow)

Same as `extra-agents/ADDON-AGENTS.en.md` §3 + `addon-agents/README.en.md`. Summary:

1. **Write a PRD** — use `ai-traffic-monitor/PRD-ai-traffic-monitor.md` as the concrete template. State
   Non-goals first.
2. **Pick a template** — has a screen → `Board`/`UserManager`; CLI wrapping → `ShellAgent`; RAG →
   `RagAgent`; external-API proxy → `ToolProxyAgent`; pure backend → `ServiceAgent`.
3. **File layout** — `{AgentName}-meta.json` (required) + `-app.py`/`-front.tsx`/`-sql.sql` (optional),
   named without a prefix, matching the `tbl_agent_config` key. Never collide with a built-in key
   (409 `builtin_conflict`).
4. **Endpoint order** — `GET /status` (tool availability) → read-only queries → privileged actions
   (`POST /scan` etc., `require_role`).
5. **Bundled workers** — when a separate binary is needed (e.g. candidate A's scanner), bundle a
   `{key}-worker-guide.md` and declare a `worker` block in meta.json (`kind: bundled|external`). See
   `VASCA_worker` (Go) / `BehaviorNotiService_worker` (C++).
6. **Testing** — `test/impl/<Nth>/{scenario,result}.md` + add a batch to `ITManually.sh`.
7. **Docs** — update `addon-agents/README.md` (KO/EN) and this catalog.

### 3.2 CLI-Wrapping Safety Model (required for A·C·D·F)

Follows the execution-safety model of `ShellAgent` / `ai-traffic-monitor`:

- External calls always use **`shell=False` + internally assembled argv** (never inject a user string into a
  shell).
- Fix executable binaries by **allowlist** (e.g. `nmap dig whois subfinder amass`).
- Input validation: parse domains/IPs via regex or the `ipaddress` module, clamp integer params to an upper
  bound, contain file paths under a dedicated directory.
- Privileged actions require `require_role` (supervisor/admin).
- When a tool is missing/unconfigured, degrade gracefully with **503 + guidance**, not a 500 (so the
  orchestrator doesn't mistake it for a 502 and abort).
- ⚠️ **Never** use `from __future__ import annotations` — the dynamic loader doesn't register the module in
  `sys.modules`, so pydantic can't resolve deferred annotations → 500.

### 3.3 Offensive-Tool Governance (candidate A + the §2.3 family)

- **Target allowlist**: scan targets selectable only from pre-registered assets (no free-form input, or wire
  in domain-ownership verification).
- **Approval trail**: supervisor/admin approval before execution + run log (who/when/what).
- **Isolation first**: validate against controlled targets (`VAmPI`/`Exegol`/`bugbounty-lab101`) before
  extending to real assets.
- **Dual-use disclosure**: "for authorized security testing only" warning in README/UI. Follows the
  `redteam-isolated` model of `ai-redteam`.

### 3.4 External MCP-Server Proxying (candidate E)

For an already-complete MCP server like `cve-mcp-server`, proxying via `ToolProxyAgent` is cheaper than
writing a fresh `-app.py`. The Addon's job shrinks to "proxy config + reshaping results for SeCuardian's
UI/conversation flow."

### 3.5 Own-Infra References (extra-agents second batch, §1.10)

The 9 recently added extra-agents links are **agent runtime/orchestration/edge-LLM infrastructure**, not new
security agents, so the security roadmap (§4) is unchanged. Three carry direct reference value for
implementation/platform design:

- **`falcons-eyes/agent-fabric-dispatch`** — local (Ollama)-first routing + Claude fallback for uncertain
  tasks (79% cost cut). Informs `router_llm` metering/routing policy.
- **`HKUDS/CLI-Anything`** — expose software as agent-native CLIs. Reinforces the §3.1–3.2 CLI-wrapping
  pattern and `ToolProxyAgent`.
- **`vstorm-co/full-stack-ai-agent-template`** — FastAPI+Next.js full-stack AI agent template (matching
  stack). Scaffolding reference for screen-bearing Addons (`Board`/`UserManager`).

> Detailed basis: [extra-agents/ADDON-AGENTS.en.md §1.10](../.docs/extra-agents/ADDON-AGENTS.en.md).

### 3.6 `agentic-soc` Reference Implementations (extra-agents fourth batch, §1.12)

Two **open-source reference implementations** that concretize the already-implemented `agentic-soc` (§1.5 L5)
as a deployable stack. Not new agents — references for hardening agentic-soc internals (triage, correlation,
RAG, workflow).

- **`zhadyz/AI_SOC`** (Apache-2.0) — Wazuh + Ollama LLM (Foundation-Sec-8B) + ML triage (RF/XGBoost) +
  ChromaDB RAG, Docker Compose. **Stack matches SeCuardian's `agentic-soc`+`wazuh-siem`+`rag` trio → #1 reference.**
- **`Sec-Link/Argus-Agentic-SOC-Platform`** (Apache-2.0) — alert ingest, incident investigation, ticketing,
  asset correlation, workflow orchestration. Incident-workflow UX / asset-correlation design (ties to `shuffle-soar`).
- Note: `semantica-agi/semantica` (W3C provenance / audit graph) indirectly informs `isms-p-evidence` audit-log design.

> Detailed basis: [extra-agents/ADDON-AGENTS.en.md §1.12](../.docs/extra-agents/ADDON-AGENTS.en.md).

---

## 4. Roadmap Summary

| Status | Agents | Layer |
|---|---|---|
| ✅ Implemented (embedded) | keycloak/logto/vault, falco/harbor/hardening, crowdsec/istio/wireproxy, wazuh/observability | L1–L5 |
| ✅ Implemented (embedded+ADDON) | vasca-cve, cilium-netpol, teler-ids, neosync-dlp, shuffle-soar, otel-collector, teleport-pam, velociraptor-dfir, agentic-soc, ai-eval-gate, ai-redteam⚠️, isms-p-evidence | L1–L6, Cross |
| ✅ Implemented (ADDON util) | truffle-scan, caddy-proxy, grafana-dashboard, ai-traffic-monitor | L3·L4·Cross |
| ✅ Platform built-in | guardrails, marketplace, playground, rag, workflow | platform |
| 🟡 Candidate (high) | attack-surface-recon(A), agentic-threat-model(B), api-vuln-scan(C) | L3·L6·L2 |
| 🟡 Candidate (medium) | malware-hunt(D), soc-intel-fusion(E), ad-security-scan(F), cicd-security-scan(G) | L2·L5·L1·L4 |
| ⛔ Held by policy | autonomous offense automation, kernel zero-day, AV/EDR evasion | — |

---

## Change Log

- Initial version: classified the implemented agents (24 embedded routers + 13 ADDON + 5 utilities +
  5 platform built-ins + 6 templates) across the 6 layers, mapped the extra-agents candidates (A–G) onto
  coverage, and consolidated the implementation guidance.
- Second update: incorporated 9 new extra-agents links — all agent infrastructure (runtime/orchestration/
  edge-LLM), so the security roadmap is unchanged. Added §3.5 own-infra references (agent-fabric-dispatch,
  CLI-Anything, full-stack template).
- Third update: reviewed 5 new extra-agents links (Cybersecurity-Projects, turbo-fieldfare, KillerPDF,
  TeleVault, parse-server) — 1 security-training reference + 1 edge-LLM + 3 out-of-scope, so no new
  security agent and the roadmap is unchanged. Detail: extra-agents/ADDON-AGENTS.en.md §1.11.
- Fourth update: reviewed 5 new extra-agents links (AI_SOC, Argus, semantica, Pentest-Swarm-AI, AgentDeck).
  AI_SOC & Argus are open-source reference implementations for `agentic-soc` — added §3.6. No new security
  agent, roadmap unchanged. Detail: extra-agents/ADDON-AGENTS.en.md §1.12.
- Fifth update: reviewed 11 new extra-agents links. gato-x (GitHub Actions CI/CD security) → **new candidate
  G `cicd-security-scan`** (§2.2, §4). The other 10 are AI/agent infra + dev tools. Detail: ADDON-AGENTS.en.md §1.13.
- Sixth update: physically sorted the 125 root extra-agents links into `ai-soc/`, `orchestrator/`,
  `ai-traffic-monitor/` folders. Reviewed 12 new links — no new candidate (A–G unchanged); vps-audit
  reinforces `hardening-auditor`, agentbehavior the `ai-eval-gate`. Roadmap unchanged. Detail: ADDON-AGENTS.en.md §1.14.
- Seventh update (2026-09-10): re-verified classification (ai-soc 95, orchestrator 53, ai-traffic-monitor 6)
  + 28 new links (§1.15, recommend promoting candidate B). **Confirmed security assets expanded 13→21.**
  Derived the agents-to-implement vs SeCMP-PRD → new doc **[AGENTS-GAP.en.md](./AGENTS-GAP.en.md)** (7 new
  security agents A–G + 4 packaging items).
