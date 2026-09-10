# SeCuardian Agent Gap Analysis — Derived from SeCMP-PRD vs. marketplace-assets

> As of 2026-09-10.
> Basis: [.docs/SeCMP-PRD.md](../.docs/SeCMP-PRD.md) (platform PRD), [marketplace-assets/AGENTS.en.md](./AGENTS.en.md)
> (implementation inventory), [.docs/extra-agents/ADDON-AGENTS.en.md](../.docs/extra-agents/ADDON-AGENTS.en.md)
> (open-source survey, candidates A–G).
> Goal: derive the agents the PRD requires, compare against what is **already implemented** in
> `marketplace-assets/`, and distill only the **agents still to implement**.

---

## 1. Agents the PRD (SeCMP) Requires — Platform Built-ins (derivation)

SeCMP-PRD is a **Marketplace platform** PRD. Its "agents" are 6 **platform built-in agents**, all already
implemented (✅/🟡). **No new platform agent is requested** — the remainder is feature-level, not agents.

| PRD feature | Built-in agent | Status (§9) | Remaining (feature, not an agent) |
|---|---|---|---|
| F-MP | `marketplace` | ✅ | GPG key rotation, real mTLS handshake (ops) |
| F-WF | `workflow` | 🟡 | code node (sandbox), loop/sub-flow/cron, llm-node Claude wiring |
| F-RAG | `rag` | 🟡 | ~~Qdrant~~ (✅ impl/57), embedding-model swap (deferred) |
| F-PG | `playground` | 🟡 | cost tracking, eval execution |
| F-GRD | `guardrails` | 🟡 | 25-domain ML classifier (out of SeCMP scope), real MCP integration test |
| F-AI | `assistant`/orchestrator | ✅ | split out shared `services/llm.py` (refactor) |

> **Conclusion (part 2)**: the PRD yields **no new agent**. All 6 platform agents exist; only feature work
> remains. The "agents to implement" come not from the platform PRD but from the **security agent asset**
> (catalog) line (§3).

---

## 2. Current marketplace-assets Inventory (2026-09-10)

| Class | Count | Members |
|---|---|---|
| **security** (security agent assets) | 21 (+2 workers) | agentic-soc, ai-eval-gate, ai-redteam, behavior-noti, cilium-netpol, compliance-isms, crowdsec-monitor, falco-receiver, harbor-scanner, hardening-auditor, isms-p-evidence, keycloak-monitor, neosync-dlp, otel-collector, shuffle-soar, teleport-pam, teler-ids, vasca-cve, vault-monitor, velociraptor-dfir, wazuh-siem (+ VASCA_worker, BehaviorNotiService_worker) |
| **builtin** (platform) | 5 | guardrails, marketplace, playground, rag, workflow |
| **utilities** | 5 | ai-traffic-monitor, caddy-proxy, grafana-dashboard, server-shell, truffle-scan |
| **addon** (dev templates) | 6 | Board, RagAgent, ServiceAgent, ShellAgent, ToolProxyAgent, UserManager |

> The earlier [AGENTS.en.md](./AGENTS.en.md) §1 was written against 13 security agents; since then the
> product's embedded monitors (keycloak·vault·falco·harbor·hardening·crowdsec·wazuh·compliance-isms) were also
> packaged as assets, **expanding it to 21**.

---

## 3. Agents Still To Implement (the gap)

### 3.1 New security agents — extra-agents candidates A–G (absent from marketplace-assets)

Candidates A–G were **all implemented on 2026-09-10 in impl/53 (E9)** as `marketplace-assets/security/`
assets. Rationale/reuse per [ADDON-AGENTS.en.md §2](../.docs/extra-agents/ADDON-AGENTS.en.md) + §1.15. See PRD §7.13.

| Cand. | Agent | Gap it fills | Priority | Reuse base | Status |
|---|---|---|---|---|---|
| **B** | `agentic-threat-model` | Security scan of our own MCP/skills/agent configs + threat model (static+runtime, 2 modes) | **Top (promoted)** | agentseal·hackagent·AgentHound·Agent-Wiz + `ShellAgent`/static analysis | ✅ impl/53 |
| **A** | `attack-surface-recon` | External attack-surface OSINT recon | High | spiderfoot·reconftw·noir·osiris + `ShellAgent` CLI wrapping | ✅ impl/53 |
| **C** | `api-vuln-scan` | Active API/web OWASP Top 10 scan + Shadow-API discovery | High | Nettacker·burp-ai-agent·owasp-noir·owasp-top10-skills·VAmPI (target) | ✅ impl/53 |
| **G** | `cicd-security-scan` | CI/CD (GitHub Actions) static security audit | Medium | gato-x (static mode) + adjacent `truffle-scan`/`harbor` | ✅ impl/53 |
| **F** | `ad-security-scan` | Active Directory misconfig / attack paths | Medium | ADScanPro·NetSPI/AD-PathFinder + adjacent `teleport-pam` | ✅ impl/53 (live collect mock-first) |
| **D** | `malware-hunt` | Supply-chain-disguised malware IOC hunting | Medium | malwoverview·GhidraGPT + adjacent `truffle-scan` | ✅ impl/53 |
| **E** | `soc-intel-fusion` | Unified CVE/EPSS/KEV/ATT&CK lookup | Medium | cve-mcp-server (MCP proxy)·IntelOwl·nmap-vulners | ✅ impl/53 |

> Remaining (agents complete, only real-environment validation left): installing live external tools
> (nmap, subfinder, bloodhound-python, malwoverview) and validating in an isolated runtime. The first cut
> degrades gracefully with 503/501 when a tool is absent (PRD §3 mock-first).
> **E future extension (reference)**: wire `7onez/cti-expert` (79 MCP tools, ATT&CK, ICD-203 reports) via a
> `ToolProxyAgent` proxy to deepen E from simple CVE fusion into CTI case analysis + structured reports
> (ADDON-AGENTS §1.16).

> **Promote B to top**: SeCuardian itself is an MCP/A2A platform → scanning its own MCP/skills/agent configs
> (B) has the most direct payoff. agentseal (live MCP tool-poisoning audit) and hackagent give it thick
> backing (§1.15).

### 3.2 Packaging gap — in the product, not yet a marketplace asset

Present as embedded routers in the SeCuardian product but **not yet packaged** into
`marketplace-assets/security`. These need **ADDON packaging of the existing router** (same as vasca-cve /
isms-p-evidence precedent), not new development.

| Agent | Product router | Layer | Work | Status |
|---|---|---|---|---|
| `logto-monitor` | `router_logto` | L1 Identity | ADDON packaging | ✅ impl/54 |
| `istio-mtls` | `router_istio` | L3 Network | ADDON packaging | ✅ impl/54 |
| `wireproxy-ztna` | `router_wireproxy` | L3 Network | ADDON packaging | ✅ impl/54 |
| `observability-monitor` | `router_observability` | L5 | ADDON packaging | ✅ impl/54 |

### 3.3 Note — platform feature gaps (not agents)

| Feature | Status |
|---|---|
| HITL approvals table (`tbl_hitl_approvals`) + gate | ✅ impl/55 (E11) |
| OWASP LLM Top 10 scorecard | ✅ impl/55 (E11) |
| Playground cost tracking | ✅ impl/56 (E12) |
| Playground eval | ✅ impl/56 (E12) |
| Qdrant (adapter) | ✅ impl/57 (E13) — vector_backend qdrant path, add-only, local fallback. Only real-server benchmarking needs infra |
| Embedding-model swap (sentence-transformers) | ⬜ deferred — heavy dep + dual-write migration |
| Workflow code node | ⬜ deferred — PRD §3 out-of-scope (sandbox review first) |
| loop/sub-flow/cron · namespace multi-tenancy | ⬜ deferred — P5 roadmap |

---

## 4. Final — "Agents Still To Implement"

1. ~~**7 new security agents** (A–G)~~ — **✅ done (impl/53, 2026-09-10)**: agentic-threat-model,
   attack-surface-recon, api-vuln-scan, cicd-security-scan, ad-security-scan, malware-hunt, soc-intel-fusion
   all implemented as `marketplace-assets/security/` assets (tests 24/24 PASS).
2. ~~**4 packaging items**~~ — **✅ done (impl/54)**: logto-monitor·istio-mtls·wireproxy-ztna·observability-monitor.
3. **New platform agents**: none. Of the platform feature gaps, HITL·OWASP (impl/55), cost·eval (impl/56)
   and the Qdrant adapter (impl/57) are done; only infra-dependent items (embedding swap, code node,
   loop/cron, namespace) remain deferred (§3.3).

> Implementation procedure, safety model, and governance follow
> [ADDON-AGENTS.en.md §3](../.docs/extra-agents/ADDON-AGENTS.en.md) and
> `ai-traffic-monitor/PRD-ai-traffic-monitor.md` (a worked example).

---

## Change Log
- Initial version (2026-09-10): derived SeCMP-PRD platform agents (all 6 implemented, none new) and compared
  against the current marketplace-assets inventory (security 21, builtin 5, utilities 5, templates 6) →
  agents to implement = 7 security agents (A–G, B first) + 4 packaging items.
- Update (2026-09-10, impl/53): **7 security agents (A–G) implemented** as `marketplace-assets/security/`
  assets (security 21→28 agents), tests 24/24 PASS. Remaining = 4 packaging items
  (logto/istio/wireproxy/observability) + platform feature gaps (§3.3).
- Update (2026-09-10, impl/57): **Qdrant vector-backend adapter done (E13/E7 partial)** — vector_backend.py qdrant path, add-only, local fallback, 8/8 PASS. Deferred remainder = embedding swap, code node, loop/cron, namespace (infra/sandbox/P5).
- Update (2026-09-10, impl/54–56): **4 packaging items done (impl/54, security 28→32 agents)** + platform
  features **HITL·OWASP scorecard (impl/55, E11)·Playground cost·eval (impl/56, E12)** done. Only
  infra-dependent items (Qdrant, embedding swap, code node, namespace) remain deferred. cti-expert (§1.16) is
  a reference for E's future extension.
