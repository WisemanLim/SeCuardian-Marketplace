# Addon Agent Candidates — Overview of `extra-agents` Research Material

> Target directory: `.docs/extra-agents/`
> Purpose: survey and classify the GitHub open-source projects, articles, PDFs, and research notes
> collected as candidates for SeCuardian's (Security for Guardian) **next Addon Agents**, and document
> how to turn them into real implementations.
> This is a source inventory; actual implementation follows the procedure in
> [addon-agents/README.en.md](../../addon-agents/README.en.md) (scaffolding wizard → meta.json/app.py/sql/front
> → testing → deployment).

---

## 1. Material Inventory

`extra-agents/` mixes `.webloc` links (mostly GitHub), `.md` Perplexity research write-ups, `.pdf`/`.jpeg`
guides and infographics, a `.txt` taxonomy file, and one subfolder that already has a full PRD
(`ai-traffic-monitor/`). Roughly 90 items are grouped below into 9 categories.

> **Directory reorg (2026-08-29) + re-verification (2026-09-10)**: the root `.webloc` links were physically
> sorted into subfolders matching SeCuardian's three workstreams. Background research docs (`.md`/`.pdf`/`.txt`)
> stay at the root. **09-10 re-verify**: moved 17 security tools misfiled under `orchestrator/` back to
> `ai-soc/`, 3 network tools + `NETworkManager` (from `ai-soc/`) to `ai-traffic-monitor/`, agent observability
> (`agentops`) to `orchestrator/`, and removed 2 duplicates (`strix`, `reverse-skill`). Three buckets suffice —
> no extra category added (rule: **security tool/agent → ai-soc**, **network/traffic observation →
> ai-traffic-monitor**, **agent runtime/LLM infra → orchestrator**).
>
> | Subfolder | Count | Holds | Maps to §1 categories |
> |---|---|---|---|
> | `ai-soc/` | 95 | Security agents/tools (OSINT, pentest, vuln, malware, SOC/DFIR, agentic-AI & MCP/skill security, CI/CD, certificates, compliance, training) | §1.1–1.8, 1.11–1.15 (security) |
> | `orchestrator/` | 53 | Agent runtime/orchestration/LLM infra (routing, RAG, memory, knowledge-graph, fine-tuning, edge, agent IDE, eval, observability) | §1.9, 1.10, 1.13–1.15 (infra) |
> | `ai-traffic-monitor/` | 6 | Network / traffic observation (sniffnet, L0p4Map, netwatch, tailcat, nport, NETworkManager + existing PRD/research) | §1.4 traffic-observation |

### 1.1 OSINT / Attack-Surface Recon

Tools that discover externally exposed assets (domains, subdomains, IPs, accounts, emails) from public
information. SeCuardian needs this family to answer "how does our organization look from an attacker's
vantage point."

| Source | Link | Summary |
|---|---|---|
| smicallef/spiderfoot | github.com/smicallef/spiderfoot | The standard OSINT automation tool — threat intel & attack-surface mapping, 200+ modules |
| six2dez/reconftw | github.com/six2dez/reconftw | Automated domain recon pipeline (subdomains through vulnerabilities) |
| thewhiteh4t/FinalRecon | github.com/thewhiteh4t/FinalRecon | All-in-one web recon (headers, WHOIS, DNS, subdomains, ports) |
| edoardottt/cariddi | github.com/edoardottt/cariddi | Crawl a domain list → detect endpoints/secrets/API keys/tokens |
| khashashin/ogi | github.com/khashashin/ogi | Link-analysis-based OSINT framework |
| XD-MHLOO/Osintgraph | github.com/XD-MHLOO/Osintgraph | OSINT graph visualization |
| karim852/KUMO-Domain-Recon-Tool | github.com/karim852/KUMO-Domain-Recon-Tool | Domain recon tool |
| DevCop95/shodan_reconsx | github.com/DevCop95/shodan_reconsx | Shodan-based passive hostname recon |
| Alfredredbird/tookie-osint | github.com/alfredredbird/tookie-osint | Social-media account OSINT |
| p1ngul1n0/blackbird | github.com/p1ngul1n0/blackbird | Find social accounts by username/email |
| KatrielMoses/MailAccess | github.com/KatrielMoses/MailAccess | Email OSINT — 2,500+ platforms, breach detection, no API keys needed |
| kaifcodec/user-scanner | github.com/kaifcodec/user-scanner | Username scanner |
| tuanngocptn/nport | github.com/tuanngocptn/nport | Port scanning tool |
| Perplexity — What is OSINT | `Perplexity-OSINT는 Open Source Intelligence...md` | Definition and use-cases of OSINT from both attacker and defender perspectives (background) |

### 1.2 AI-Driven Penetration Testing Automation (Offensive AI)

The newest family: LLM agents that autonomously recon, find vulnerabilities, and attempt exploitation.
**Dual-use tooling that must be restricted to authorized targets.**

| Source | Link | Summary |
|---|---|---|
| 0x4m4/hexstrike-ai | github.com/0x4m4/hexstrike-ai | Offensive-tool orchestration framework for AI agents |
| usestrix/strix | github.com/usestrix/strix | Open-source AI pentesting — finds vulnerabilities and proposes fixes |
| vigolium/vigolium | github.com/vigolium/vigolium | High-fidelity vulnerability scanner combining agentic AI with native speed |
| Kritt-ai/open-kritt | github.com/Kritt-ai/open-kritt | Self-hosted AI vulnerability research — agents find and validate code issues |
| ARCANGEL0/EVA | github.com/ARCANGEL0/EVA | AI-assisted pentest agent with multi-backend AI integration |
| PurpleAILAB/Decepticon | github.com/PurpleAILAB/Decepticon | Autonomous hacking agent for red teams |
| elder-plinius/T3MP3ST | github.com/elder-plinius/T3MP3ST | Autonomous red-teaming platform; multi-agent offensive-security meta-harness |
| nishu2402/HEAVEN | github.com/nishu2402/HEAVEN-Autonomous-Penetration-Testing | Autonomous penetration testing |
| 0xSteph/pentest-ai-agents | github.com/0xSteph/pentest-ai-agents | Collection of pentest AI agents |
| 0xwilliamortiz/claude-red | github.com/0xwilliamortiz/claude-red | Claude-based red-team tooling |
| elementalsouls/Claude-BugHunter | github.com/elementalsouls/Claude-BugHunter | Claude-based bug hunting |
| yee-yore/DorkAgent | github.com/yee-yore/DorkAgent | LLM-powered automated Google Dorking for bug hunting/pentesting |
| AKCodez/hackingtool-plugin | github.com/AKCodez/hackingtool-plugin | Claude Code plugin wrapping 183+ pentest/OSINT tools |

### 1.3 Web / API Vulnerability Scanning

| Source | Link | Summary |
|---|---|---|
| OWASP/Nettacker | github.com/OWASP/Nettacker | OWASP's official automated pentest/vulnerability scanner |
| Teycir/BurpAPISecuritySuite | github.com/Teycir/BurpAPISecuritySuite | Burp Suite extension for API security |
| erev0s/VAmPI | github.com/erev0s/VAmPI | Deliberately vulnerable API implementing the OWASP API Top 10 (a **training target**) |
| hahwul/WebHackersWeapons | github.com/hahwul/WebHackersWeapons | Curated list of web hacker tools |

### 1.4 Network / Wireless / Certificate Infrastructure

| Source | Link | Summary |
|---|---|---|
| D3Ext/WEF | github.com/D3Ext/WEF | Wi-Fi exploitation framework |
| BornToBeRoot/NETworkManager | github.com/BornToBeRoot/NETworkManager | Network management/troubleshooting GUI tool |
| GyulyVGC/sniffnet | github.com/GyulyVGC/sniffnet | Real-time internet traffic monitor (Rust) |
| ADScanPro/adscan | github.com/ADScanPro/adscan | Active Directory security scanner |
| htrgouvea/nipe | github.com/htrgouvea/nipe | Route all traffic through Tor as the default gateway |
| hakwerk/labca | github.com/hakwerk/labca | Private ACME-based CA for internal lab use |

### 1.5 Malware Analysis / Reverse Engineering / Kernel Vulnerability Research

| Source | Link | Summary |
|---|---|---|
| 416rehman/DeepZero | github.com/416rehman/DeepZero | Mass analysis of Windows kernel drivers → automated exploitable-IOCTL discovery |
| alexandreborges/malwoverview | github.com/alexandreborges/malwoverview | Malware first-triage tool integrating multiple threat-intel APIs |
| darama22/Malware-Research-Hub | github.com/darama22/Malware-Research-Hub | Catalog of 80 malware families + 2,764 samples (local Flask app, bilingual) |
| mito753/Kernel-Exploit-Dojo | github.com/mito753/Kernel-Exploit-Dojo | CTF kernel-exploitation notes/PoCs |
| thomasxm/BOAZ_beta | github.com/thomasxm/BOAZ_beta | Multilayered AV/EDR evasion framework (no longer maintained) |
| zhaoxuya520/reverse-skill | github.com/zhaoxuya520/reverse-skill | Reverse-engineering skill collection |
| HackUnderway/CyberLeaks | github.com/HackUnderway/CyberLeaks | Cyber-leak related material |
| "AI 개발도구 위장 악성코드 감염 헌팅가이드" (PDF) | local file | Hunting methodology for malware disguised as AI dev tooling (npm/VSCode extensions, etc.) |

### 1.6 Agentic AI Security (securing the AI agents / MCP stack itself)

**The category SeCuardian should watch most closely.** Defensive tooling for the emerging threat surface
where LLM agents, MCP servers, and A2A communication become the attack target.

| Source | Link | Summary |
|---|---|---|
| adithyan-ak/AgentHound | github.com/adithyan-ak/AgentHound | "BloodHound for the agentic stack" — recon, credential looting, model exfiltration/poisoning, attack-path analysis across MCP/A2A/gateways |
| perplexityai/numbat | github.com/perplexityai/numbat | Visibility into AI agent activity on endpoints — on-device detection, pre-action blocking, forensic reconstruction |
| secureagentics/Adrian | github.com/secureagentics/Adrian | Runtime AI agent security — catches malicious tool use, prompt injection, and policy drift before the agent acts |
| Repello-AI/Agent-Wiz | github.com/Repello-AI/Agent-Wiz | CLI for threat modeling and visualizing AI agents built with LangGraph/AutoGen/CrewAI etc. |
| anthropics/claude-code-security-review | github.com/anthropics/claude-code-security-review | Claude-powered security review GitHub Action for code changes |
| mukul975/cve-mcp-server | github.com/mukul975/cve-mcp-server | MCP server giving Claude 27 tools across 21 APIs (CVE, EPSS, CISA KEV, MITRE ATT&CK, Shodan, VirusTotal) |
| "AI 개발도구 위장 악성코드..." (PDF, cross-listed) | local file | Supply-chain angle on threats disguised as AI dev tooling |

### 1.7 SOC / Threat Intelligence / DFIR

| Source | Link | Summary |
|---|---|---|
| beenuar/AiSOC | github.com/beenuar/AiSOC | Open-source AI-powered SOC — alert fusion, purple-team drills, agent-assisted triage, MITRE ATT&CK investigation, MIT-licensed |
| intelowlproject/IntelOwl | github.com/intelowlproject/IntelOwl | Threat-intelligence-at-scale management platform |
| "Geni AI vs AI Native SOC" (PDF) | local file | Explains the structural difference between a generative-AI SOC and an AI-native SOC |
| KISA AI red-teaming guide (PDF, 69p) | discuss.pytorch.kr link | Official Korean guide covering AI red-team formation through result reporting |
| Perplexity — Wazuh SIEM research | `Perplexity-WAZUH SIEM 등.md` | Overview of the open-source Wazuh SIEM/XDR platform |

### 1.8 Automation / Orchestration / Training Ranges

| Source | Link | Summary |
|---|---|---|
| JoasASantos/n8n-CyberSecurity-Workflows | github.com/JoasASantos/n8n-CyberSecurity-Workflows | 100+ n8n Red/Blue/AppSec workflow playbooks |
| JoasASantos/n8n-cybersecurity-projects | github.com/JoasASantos/n8n-cybersecurity-projects | Collection of n8n security projects |
| shinjaehyun20/ai-workflow-kits | github.com/shinjaehyun20/ai-workflow-kits | Copy-ready workflow packs for Codex/Claude Code/Gemini/Copilot |
| A-poc/RedTeam-Tools, A-poc/BlueTeam-Tools | github.com/A-poc/{RedTeam,BlueTeam}-Tools | Curated red-team / blue-team tools and techniques |
| yeyintminthuhtut/Awesome-Red-Teaming | github.com/yeyintminthuhtut/Awesome-Red-Teaming | Awesome-list of red-teaming resources |
| m14r41/PentestingEverything | github.com/m14r41/PentestingEverything | Complete VAPT/AppSec/pentest guide across every surface |
| mandiant/commando-vm | github.com/mandiant/commando-vm | Mandiant's official offensive Windows VM distribution |
| ThePorgs/Exegol | github.com/ThePorgs/Exegol | Community-driven, containerized hacking environment |
| DevCop95/bugbounty-lab101 | github.com/DevCop95/bugbounty-lab101 | Bug-bounty practice lab |

### 1.9 Compliance / Policy / Background Research (not direct implementation targets)

| Source | Link | Summary |
|---|---|---|
| EU Cyber Resilience Act guide | cyberresilienceact.eu/ko | CRA full text, guide, and free compliance tools |
| Cloudflare AI-agent payments article | datanet.co.kr | Introduces a safe online-payment capability driven by AI agents |
| "정보보호 솔루션.txt" | local file | Korea's standard information-security industry taxonomy (78 categories: EDR/DLP/SIEM/SOAR, etc.) — **used as the classification basis for this document** |
| 5 Perplexity research notes | `Perplexity-*.md` | Comparison of security-specialized HuggingFace models / local LLM (Ollama vs. llama.cpp) comparison / multi-agent architecture & registry design / RAG agent design considerations / fine-tuning & quantization concepts — background for SeCuardian's own AI infra (orchestrator, local LLM ops) decisions |

Material with low direct security relevance (general-purpose AI platform/infra research: MetaGPT, BitFun,
omg.dev, ToolJet, SmythOS, ClaraVerse, corsair, deer-workflow, mnemory, Soup, SINQ, tech-stack-datasets,
Rosetta-Prompt, hallmark, leadita) is classified as "research toward SeCuardian's own multi-agent/LLM
infrastructure" and excluded from the Addon Agent proposals in §2.

### 1.10 Agent Runtime / Orchestration / Edge-LLM Infrastructure (second batch)

The 9 recently added links are all **agent runtime / orchestration / edge-LLM infrastructure, not security
agents**. They produce no new Addon Agent candidates (A–F), but inform SeCuardian's own design
(orchestrator, local-LLM operation, scaffolding), so they are collected separately here. Mostly an
extension of the §1.9 general-infra bucket.

| Source | Link | Summary | SeCuardian relevance |
|---|---|---|---|
| truefoundry/trueforge | github.com/truefoundry/trueforge | Open-source agent harness (runtime layer) turning an LLM into a working agent | orchestrator runtime design |
| stablyai/orca | github.com/stablyai/orca | ADE for a fleet of parallel coding agents (desktop/mobile/VPS) | multi-agent operation UX |
| getpaseo/paseo | github.com/getpaseo/paseo | Orchestrate multiple coding agents from desktop/mobile | multi-agent orchestration |
| falcons-eyes/agent-fabric-dispatch | github.com/falcons-eyes/agent-fabric-dispatch | Local open-weight (Ollama)-first routing + Claude fallback for uncertain tasks (79% cost cut) | **LLM routing / cost optimization** — directly informs router_llm metering/routing policy |
| HKUDS/CLI-Anything | github.com/HKUDS/CLI-Anything | Expose all software as agent-native CLIs | **CLI-wrapping pattern** (§3.1) and ToolProxyAgent |
| vstorm-co/full-stack-ai-agent-template | github.com/vstorm-co/full-stack-ai-agent-template | FastAPI+Next.js full-stack AI agent template (RAG/streaming/auth/20+ integrations) | scaffolding for new app-type Addons (matching stack) |
| CopilotKit/openbot | github.com/CopilotKit/openbot | Open-source AI coworkers each with their own computer (browser/files/tools), AG-UI | agent UI (AG-UI) pattern |
| RightNow-AI/picolm | github.com/RightNow-AI/picolm | Run a 1B LLM on a $10 / 256MB-RAM board (edge LLM) | edge / on-device LLM operation |
| jangles-byte/Pythia | github.com/jangles-byte/Pythia | Local forecasting fusing 40+ global feeds (Ollama, no cloud) | situational-awareness / threat-intel fusion idea (indirect) |

> Conclusion: none of the 9 **spawn a new security Addon candidate.** The §2 candidate list (A–F) is
> unchanged. agent-fabric-dispatch (local-first LLM routing), CLI-Anything (CLI wrapping), and the vstorm
> full-stack template carry real reference value for §3.1 and SeCuardian's orchestrator/scaffolding design.

### 1.11 Third Batch (security-training reference + non-security utilities)

5 more links. 1 is a security learning/training reference, 1 is edge-LLM infra (§1.10 picolm family), the
other 3 are general utilities/BaaS unrelated to SeCuardian. **No new security Addon candidate (A–F
unchanged).**

| Source | Link | Summary | Disposition |
|---|---|---|---|
| CarterPerez-dev/Cybersecurity-Projects | github.com/CarterPerez-dev/Cybersecurity-Projects | 70 beginner→advanced security learning projects (gamified) | §1.8 training reference — usable as QA/test scenarios / PoC material for new Addons |
| drumih/turbo-fieldfare | github.com/drumih/turbo-fieldfare | Gemma 26B inference in ~2 GB RAM on M-series MacBooks (edge LLM) | §1.10 edge / on-device LLM reference (picolm family) |
| SteveTheKiller/KillerPDF | github.com/SteveTheKiller/KillerPDF | Open-source PDF editor (Windows, GPLv3) | out of scope — unrelated to security agents |
| Skyh-23/TeleVault | github.com/Skyh-23/TeleVault | Telegram-based private cloud drive (zero-knowledge AES-256) | out of scope — storage/privacy app, not an Addon target |
| parse-community/parse-server | github.com/parse-community/parse-server | Node.js/Express BaaS backend | out of scope — general BaaS infra |

> Conclusion: none of the 5 **spawn a new security Addon candidate.** Cybersecurity-Projects is
> training/test material, turbo-fieldfare an edge-LLM reference; the other 3 are out of SeCuardian's scope.

### 1.12 Fourth Batch (AI-SOC reference implementations + offensive swarm + audit infra)

5 more links. **This batch is highly security-relevant** — but rather than spawning new candidates, these are
**reference architectures reinforcing the already-implemented `agentic-soc`** (AGENTS.md L5) plus a §2.3
offensive-governance case. No new A–F candidate.

| Source | Link | Summary | Disposition |
|---|---|---|---|
| zhadyz/AI_SOC | github.com/zhadyz/AI_SOC | Deployable local-first AI SOC — Wazuh + Ollama LLM (Foundation-Sec-8B) + ML triage (RF/XGBoost) + ChromaDB RAG, Docker Compose, **Apache-2.0** | **Reference architecture for `agentic-soc`+`wazuh-siem`+`rag`.** Stack matches SeCuardian's trio exactly — top reference for building out agentic-soc internals |
| Sec-Link/Argus-Agentic-SOC-Platform | github.com/Sec-Link/Argus-Agentic-SOC-Platform | Deployable agentic SOC — alert ingest, incident investigation, ticket collaboration, asset correlation, workflow orchestration, AI analysis. Next.js/Django/PostgreSQL, Docker/K8s, **Apache-2.0** | **Reference for `agentic-soc`+`shuffle-soar`.** Incident-workflow UX / asset-correlation design |
| semantica-agi/semantica | github.com/semantica-agi/semantica | Explainable/auditable AI infra — knowledge graph, W3C provenance, decision tracking, regulated domains (finance/health/gov), Python, OSS | **Related to `isms-p-evidence`** — reference for agent decision logs / audit provenance (indirect) |
| Armur-Ai/Pentest-Swarm-AI | github.com/Armur-Ai/Pentest-Swarm-AI | AI multi-agent penetration-testing swarm (offensive) | §1.2/§2.3 family — isolated-lab-only + approval governance required. Follows the `ai-redteam` isolation model |
| GenDistrict/AgentDeck | github.com/GenDistrict/AgentDeck | Secure agent workspace (prompt-injection detection, isolated credentials), **closed-source (download only)** | Out of scope (not reusable) — recorded only as a §1.6 agentic-AI-security market reference |

> Conclusion: none of the 5 **spawn a new security Addon candidate (A–F unchanged).** But AI_SOC and Argus
> concretize the already-implemented `agentic-soc` as deployable **open-source reference implementations**;
> AI_SOC in particular (Wazuh+RAG+LLM, Apache-2.0) matches SeCuardian's own stack and is the #1 reference
> when hardening agentic-soc internals. semantica informs ISMS-P audit provenance (indirect);
> Pentest-Swarm-AI is a §2.3 governance target; AgentDeck is out of scope.

### 1.13 Fifth Batch (new CI/CD security gap + mostly AI infra)

11 more links. **One reveals a new security gap (CI/CD pipeline security) → new candidate G (§2.2).** The
other 10 are AI/agent infrastructure (LLM routing, memory, RAG, LLMOps, edge inference) plus Ops and dev tools.

| Source | Link | Summary | Disposition |
|---|---|---|---|
| AdnaneKhan/gato-x | github.com/AdnaneKhan/gato-x | **GitHub Actions attack toolkit** — static analysis of workflow misconfig + self-hosted runner takeover / secrets exfiltration, Python, Apache-2.0 | **New security gap: CI/CD pipeline security.** In defensive mode (audit our own workflows) → new candidate **G**. Adjacent to `truffle-scan` (secrets) / `harbor` (registry) |
| ulab-uiuc/LLMRouter | github.com/ulab-uiuc/LLMRouter | Open-source LLM routing library | **`router_llm` reference** (agent-fabric-dispatch family, §1.10) |
| mikehasa/agentacct | github.com/mikehasa/agentacct | Local-first coding-agent observability (token/cost tracking) | `router_llm` metering reference |
| jeffhajewski/latticedb | github.com/jeffhajewski/latticedb | Embedded single-file knowledge-graph DB (vector+FTS, for RAG) | **`rag` infra reference** |
| 0xK3vin/MegaMemory | github.com/0xK3vin/MegaMemory | Persistent knowledge-graph memory for coding agents (MCP, semantic search, embeddings) | `rag` / agent-memory reference (mnemory family) |
| leeryong/NELLA | github.com/leeryong/NELLA | Agentic LLMOps that builds domain LLMs from documents (HITL, local) | LLMOps / fine-tuning reference (ties to the Perplexity fine-tuning research) |
| FlashML-org/FreeToken | github.com/FlashML-org/FreeToken | Edge-native MoE inference engine for consumer hardware | edge-LLM reference (picolm family, §1.10) |
| Tracer-Cloud/opensre | github.com/Tracer-Cloud/opensre | Open-source toolkit for building AI SRE agents | Ops (observability) — indirect |
| pixlcore/xyops | github.com/pixlcore/xyops | Workflow automation + server monitoring | `server-shell` / observability — indirect |
| bloomberg/memray | github.com/bloomberg/memray | Python memory profiler | out of scope (dev tool) |
| cathrynlavery/diagram-design | github.com/cathrynlavery/diagram-design | 38 diagram types for Claude Code (HTML+SVG) | out of scope (docs/design tool) |

> Conclusion: of the 11, **only gato-x spawns a new security candidate (G).** The rest are references for
> SeCuardian's own infra (LLM routing, RAG, memory, edge, LLMOps) or out of scope. LLMRouter/agentacct join
> the §3.5 own-infra references, latticedb/MegaMemory reinforce `rag`, NELLA informs fine-tuning/LLMOps.

### 1.14 Sixth Batch (no new candidate — reinforces existing categories/agents)

12 more links. **They spawn no new security candidate (A–G unchanged).** 5 sorted into ai-soc (reinforcing
existing security categories/agents), 7 into orchestrator (agent runtime / eval infra).

| Source | Link | Summary | Bucket · Disposition |
|---|---|---|---|
| nuver-labs/vps-audit | github.com/nuver-labs/vps-audit | Lightweight bash script for Linux server security/perf auditing | **ai-soc** — reinforces the implemented `hardening-auditor` (E05) |
| weirdmachine64/GhidraGPT | github.com/weirdmachine64/GhidraGPT | LLM integrated into Ghidra for AI reverse engineering | **ai-soc** — §1.5 reversing, adjacent to candidate D (`malware-hunt`) |
| ottosulin/awesome-ai-security | github.com/ottosulin/awesome-ai-security | Curated AI-security resource list | **ai-soc** — §1.6 agentic-AI-security meta reference |
| HackUnderway/cerberus | github.com/HackUnderway/cerberus | Extract exploits from Shodan Exploits | **ai-soc** — §1.1/§2.3 offensive (governance target) |
| NotAnyoneMe/ProxyChecker | github.com/NotAnyoneMe/ProxyChecker | HTTP/SOCKS proxy checker (GUI) | **ai-soc** — recon/anonymization util (§1.1 adjacent) |
| Untrivial-ai/agent-orchestrator | github.com/Untrivial-ai/agent-orchestrator | Coding-agent-fleet IDE + planning/spawn/CI-fix orchestrator | **orchestrator** — SeCuardian orchestrator design reference |
| google/sam | github.com/google/sam | SAM Sovereign Agent Mesh | **orchestrator** — A2A / agent-mesh reference |
| the-open-engine/zeroshot | github.com/the-open-engine/zeroshot | Executor–verifier orchestration | **orchestrator** — execute/verify separation pattern |
| braintrustdata/agentbehavior | github.com/braintrustdata/agentbehavior | Standards for defining/evaluating agent behavior | **orchestrator** — reference for the implemented `ai-eval-gate` (agent eval) |
| wlsdks/ontology-atlas | github.com/wlsdks/ontology-atlas | Agent-native ontology workbench (MCP, local) | **orchestrator** — `rag` / agent knowledge-graph reference (MegaMemory family) |
| sandbox-quantum/switch | github.com/sandbox-quantum/switch | Platform for AI-agent + human collaborative orgs | **orchestrator** — agent-collaboration UX reference |
| zenbu-labs/terminal-browser | github.com/zenbu-labs/terminal-browser | A browser inside the terminal | **orchestrator** — dev tool (indirect) |

> Conclusion: none of the 12 **spawn a new candidate (A–G unchanged).** But vps-audit reinforces the
> implemented `hardening-auditor`, agentbehavior the `ai-eval-gate`, and GhidraGPT candidate D.
> sam/agent-orchestrator/zeroshot inform SeCuardian's orchestrator/A2A design.

### 1.15 Seventh Batch (strongly reinforces existing candidates A·B·C·F — no new candidate)

28 more links. **No new candidate, but strongly reinforces A (attack surface), B (agentic-AI security),
C (API vuln), F (AD security).** 17 in ai-soc, 8 in orchestrator, 3 in ai-traffic-monitor.

**ai-soc (security, candidate reinforcement)**

| Source | Summary | Reinforces |
|---|---|---|
| getagentseal/agentseal | AI-agent security toolkit — scan dangerous skills/MCP configs, watch supply-chain attacks, test prompt-injection resistance, **audit live MCP servers for tool poisoning** | **B** (agentic-AI security) — adds runtime/config-scan angle |
| AISecurityLab/hackagent | Open-source toolkit to detect AI-agent vulnerabilities | **B** |
| owasp-noir/noir | Endpoint discovery in code, Shadow-API exposure, attack-surface mapping | **A**+**C** (Shadow API discovery) |
| six2dez/burp-ai-agent | Burp extension — MCP tooling, AI analysis, passive/active scanning | **C** (web/API vuln) |
| scholarly360/owasp-top10-web-skills | OWASP Top 10 2025 agent skills | **C** |
| vulnersCom/nmap-vulners | nmap service scan → CVE/CVSS/exploit mapping | **A**+**E** (CVE) |
| NetSPI/AD-PathFinder | AD/ADCS/SCCM/MSSQL attack-path mapping (BloodHound CE) | **F** (AD security) |
| Shad0w-ops/H.I.V.E | Unified OSINT multi-tool | **A** |
| simplifaisoul/osiris | Real-time OSINT dashboard (Palantir alternative) | **A** |
| danielmiessler/SecLists | Standard security wordlists | **A**+**C** support data |
| Awarexone/Agentic-Bug-Hunter | AI bug-bounty hunting toolkit | **C**/§2.3 |
| Netw0rkNoob/VulnClaw | AI-agent+MCP full pentest automation chain | §2.3 offensive (isolated lab) |
| infosecn1nja/Red-Teaming-Toolkit | Red-team OST collection | §1.8/§2.3 |
| lgandx/Responder | LLMNR/NBT-NS/MDNS poisoner | §2.3 offensive (network) |
| sunblaze-ucb/cybergym-e2e | Cyber range (E2E eval) | §1.8 training/eval |
| certimate-go/certimate | Self-hosted SSL certificate ACME full-cycle (issue/deploy/renew/**monitor**) | adjacent to `vault-monitor`/labca — cert-lifecycle monitoring |
| rebugui/KISA-CIIP-2026 | Korean Critical Information Infrastructure Protection 2026 | adjacent to `isms-p-evidence` compliance |
| mukul975/Anthropic-Cybersecurity-Skills | Claude security skill pack | reference |

**orchestrator (infra)**: wigolo (local search/crawl MCP), mneme (architecture-drift guardrails), omlx
(Apple-Silicon LLM inference server), tare (token audit), knowledge_graph (text→KG for RAG), agentops
(agent/LLM cost observability), privacy-build (Korean-law policy generator skill), FlowSuite. → references for
SeCuardian's orchestrator/RAG/`router_llm`.

**ai-traffic-monitor (network)**: L0p4Map (ARP+nmap topology viz), netwatch (terminal network diagnostics),
tailcat (Tailscale netcat). → references for the `ai-traffic-monitor` agent's network observation.

> Conclusion: none of the 28 **spawn a new candidate.** But **B (agentic-AI security)** now has very thick
> backing (agentseal, hackagent + existing AgentHound, Agent-Wiz, numbat, Adrian) — **recommend raising it to
> high priority**: SeCuardian is an MCP/A2A platform, so scanning its own MCP/skills/agent configs (B) has the
> most direct utility. C reinforced by owasp-noir (Shadow API)/burp-ai-agent/owasp-top10-skills; F by AD-PathFinder.

### 1.16 Eighth Batch (CTI depth — reinforces E·A, no new candidate)

| Source | Link | Summary | Reinforces |
|---|---|---|---|
| 7onez/cti-expert | github.com/7onez/cti-expert | CTI/OSINT analysis skill (Claude Code/Codex) — 120+ commands, 57 techniques, **79 typed MCP tools**, deterministic case pipeline, **ICD-203 reports**, no API keys for core | **E** (soc-intel-fusion) CTI depth + **A** (OSINT) |

> Bucket: `ai-soc`. Conclusion: **no new candidate.** It is a **CTI-depth reference implementation** for the
> already-built **E `soc-intel-fusion`** (CVE/EPSS/KEV fusion, impl/53) — cti-expert extends into ATT&CK
> technique mapping, a case pipeline and structured ICD-203 reporting. E already fills the "unified lookup"
> gap, so this is not a re-implementation target; adopt it as the basis for E's **future extension** (ATT&CK
> technique lookup + structured intel reports), where its ready MCP tools make the §3.4 `ToolProxyAgent`
> proxy cheaper than building from scratch. Also assists A (attack-surface OSINT).

**Already in progress**: the `ai-traffic-monitor/` folder has its own PRD
([PRD-ai-traffic-monitor.md](./ai-traffic-monitor/PRD-ai-traffic-monitor.md)) — an Addon Agent that observes
traffic volume from browser-auto-connected AI assistants. It is a working example of the implementation
guide in §3.

---

## 2. Proposed Addon Agents by Category

SeCuardian-Marketplace already ships 13 security agents — `agentic-soc`, `ai-eval-gate`, `ai-redteam`,
`behavior-noti`, `cilium-netpol`, `isms-p-evidence`, `neosync-dlp`, `otel-collector`, `shuffle-soar`,
`teleport-pam`, `teler-ids`, `vasca-cve`, `velociraptor-dfir` (plus 5 utilities: `ai-traffic-monitor`,
`caddy-proxy`, `grafana-dashboard`, `server-shell`, `truffle-scan`).

The candidates below fill **gaps** in that existing lineup, based on the inventory above. Priority weighs
fit with SeCuardian's identity as a defender-side platform, implementation difficulty, and governance risk.

### 2.1 High Priority

**A. `attack-surface-recon` — External attack-surface recon agent**
- Rationale: all of §1.1 OSINT/Recon (spiderfoot, reconftw, FinalRecon, cariddi, etc.)
- Concept: safely wrap CLI tools already installed on the host (`subfinder`/`amass`/`nmap`/`whois`/`dig`) to
  periodically scan and report "how exposed is our organization externally," scoped to our own domains/IPs.
- Reuses the same "CLI-wrapping, `service`-type, no dedicated screen" pattern already proven by
  `ai-traffic-monitor` and `vasca-cve`.
- Risk: must be **restricted to owned assets only**, so a pre-registered domain allowlist is mandatory
  governance, not optional.

**B. `agentic-threat-model` — AI agent/MCP threat-modeling agent** ★ reinforced (§1.15)
- Rationale: §1.6 AgentHound, Agent-Wiz, numbat, Adrian + §1.15 **agentseal** (live MCP tool-poisoning audit,
  dangerous skill/config scan, prompt-injection testing), **hackagent** (AI-agent vulnerability detection)
- Extension: design as two modes of one agent — static threat modeling (B) + **runtime MCP/skill/agent-config
  security scan** (agentseal family). SeCuardian being an MCP/A2A platform makes this the top-utility candidate.
- Concept: statically scan the LangGraph/AutoGen/CrewAI/MCP server configurations running internally —
  including SeCuardian's own orchestrator and addon-agents — and output a threat model (diagram + table)
  flagging over-privileged tools, exposed secrets, and prompt-injection-prone entry points.
- Because SeCuardian is simultaneously an agent platform and a security product, auditing its own agent
  ecosystem gives this the most direct payoff of any candidate here.
- Risk: low (mostly read-only static analysis).

**C. `api-vuln-scan` — API security vulnerability scanner**
- Rationale: §1.3 Nettacker, BurpAPISecuritySuite, VAmPI (usable as a test target)
- Concept: check registered internal API endpoints (fed via OpenAPI spec) against an OWASP API Top 10
  checklist. `VAmPI` can be stood up in an internal CI/QA lab as this agent's regression-test target.

### 2.2 Medium Priority (worthwhile extensions)

**D. `malware-hunt` — Supply-chain-disguised malware hunting agent**
- Rationale: §1.5 malwoverview, the "AI dev-tool-disguised malware hunting guide" PDF
- Concept: look up IOCs for malware distributed through the npm/PyPI/VSCode-extension ecosystem, and
  cross-reference packages installed on developer workstations and CI pipelines. Adjacent to `truffle-scan`
  (secret scanning) — pairing them in the same delivery makes sense.

**E. `soc-intel-fusion` — Unified threat-intelligence lookup agent**
- Rationale: §1.6 cve-mcp-server, §1.7 IntelOwl
- Concept: complement `vasca-cve` (asset CVEs) and `agentic-soc` (SOC alerts) with one Q&A agent that
  queries CVE/EPSS/CISA KEV/MITRE ATT&CK together. Since cve-mcp-server already exists as a ready-made MCP
  server, wiring it in as an MCP client from the SeCuardian orchestrator (see §3.3) may be faster than
  building from scratch.

**F. `ad-security-scan` — Active Directory security assessment agent**
- Rationale: §1.4 ADScanPro/adscan
- Concept: for organizations running AD, check for weak configurations (Kerberoastable accounts, overly
  permissive ACLs). Paired with `teleport-pam`, this rounds out the account/privilege security surface.

**G. `cicd-security-scan` — CI/CD pipeline security assessment agent** (new, §1.13)
- Rationale: §1.13 gato-x (GitHub Actions attack toolkit, Apache-2.0)
- Concept: **statically analyze** our own GitHub Actions / GitLab CI workflow definitions for misconfig
  (overly permissive `pwn-request`, script injection from untrusted input, exposed self-hosted runners,
  over-broad OIDC trust, hardcoded secrets) and audit/report.
- Layer: adjacent to L4 data/supply-chain. Paired with `truffle-scan` (secrets) and `harbor` (registry
  images) it completes the **supply-chain / build security** surface. Complementary to D (`malware-hunt`,
  package malware) — D covers installed packages, G covers the build pipeline.
- Implementation: wrap **only gato-x's static-analysis (enumerate) mode** for defensive use; put runner
  takeover / secrets exfiltration (attack modes) under §2.3 governance (isolated lab + approval) or disable.
  Follows the `ShellAgent` CLI-wrapping safety model.
- Risk: medium — read-only static analysis of our own repos is low, but including attack modes mandates §3.2
  governance.

### 2.3 Low Priority / Reference Only

- **Autonomous offensive-exploit tooling** (hexstrike-ai, strix, T3MP3ST, Decepticon, etc., §1.2): given
  SeCuardian's defender ("Guardian") identity, shipping offense-automation as a first-class product feature
  needs care. If adopted at all, restrict it to **approved internal lab targets only** (isolated targets like
  `bugbounty-lab101`, `Exegol`, `VAmPI`), and require target-allowlist confirmation plus an approval log
  before every run.
- **Kernel exploit / zero-day research** (DeepZero, Kernel-Exploit-Dojo, §1.5): a highly specialized research
  domain better kept as an offline research tool than an Addon Agent.
- **AV/EDR evasion frameworks** (BOAZ_beta): unmaintained and directly at odds with a defensive-product
  identity — recommend excluding.
- **General-purpose AI infra material** (MetaGPT, ClaraVerse, ToolJet, etc.): not Addon Agent candidates —
  keep as reference literature for SeCuardian's own architecture (orchestrator, local LLM operations).

---

## 3. Implementation Guidance

### 3.1 Reuse the existing pattern — `ai-traffic-monitor`'s PRD as a template

`ai-traffic-monitor/PRD-ai-traffic-monitor.md` is a real, working example of a "service-type Addon Agent
that safely wraps CLI tools." When building new agents (especially A, D, F above), follow the same
structure:

1. **Background/rationale → scope**: state the Non-goals explicitly before anything else.
2. **Endpoint table**: order from `GET /status` (tool availability) → read-only queries → `POST /scan` and
   other privileged actions.
3. **Security model** (follows the `ShellAgent` execution-safety model):
   - Every external process call uses `shell=False` with an internally assembled argv — never feed a
     user-supplied string straight to a shell.
   - Executable binaries are fixed by an allowlist (explicitly enumerate `nmap`, `dig`, `whois`, etc.).
   - Input validation: parse domains/interfaces/IPs with regex or the `ipaddress` module; clamp integer
     parameters to an upper bound.
   - Path containment: file output stays under a dedicated directory with an allowed extension only.
   - Privileged actions (triggering a scan, etc.) require `require_role` (supervisor/admin).
   - When a tool is missing or unconfigured, degrade gracefully with **503 + install/config guidance**
     instead of a 500, so the orchestrator doesn't mistake it for a 502 API failure and abort.
4. **Never use `from __future__ import annotations`** — the dynamic loader (`spec_from_file_location`)
   doesn't register the addon module in `sys.modules`, so pydantic can't resolve deferred annotations on
   request-body models, causing 500 errors.
5. **Naming convention**: `{AgentName}-app.py` / `-meta.json` / `-sql.sql` (optional) / `-front.tsx`
   (optional), all without a prefix, matching the `tbl_agent_config` key exactly. Never collide with a
   built-in agent's key.
6. **Bundled workers when needed** (e.g. a separate Go/Rust scanner binary — see `VASCA_worker` /
   `BehaviorNotiService_worker`): bundle a `{key}-worker-guide.md` install guide in the package and declare
   a `worker` block in meta.json (`required` / `kind: bundled|external` / `guide`).
7. **Testing**: record scenario/result under `test/impl/<Nth>/{scenario,result}.md`, then add a batch to
   `ITManually.sh`.
8. **Docs**: update the built-in/ADDON lists in `addon-agents/README.md` (KO/EN).

### 3.2 Governance — when handling offensive tooling

If any of the offense-automation candidates in §2.3 are ever adopted, reflect the following both in
meta.json's governance field and in actual runtime behavior:

- **Target allowlist**: scan/attack targets must be selectable only from a pre-registered asset list (no
  free-form input, or domain-ownership verification is wired in).
- **Approval trail**: require supervisor/admin approval before execution and log every run (who/when/what).
- **Isolated environments first**: validate against controlled lab targets (`VAmPI`, `Exegol`,
  `bugbounty-lab101`) before extending to real assets.
- **Dual-use disclosure**: README and UI must clearly state "for authorized security testing only."

### 3.3 When wiring an external MCP server beats building from scratch

For a tool that's already a complete MCP server, like `mukul975/cve-mcp-server`, it's usually cheaper to
proxy it through SeCuardian orchestrator's MCP-client capability (see the `ToolProxyAgent` template under
`addon-agents/zip/`) than to write a fresh `-app.py`. In that case the Addon Agent's job shrinks to "proxy
configuration + reshaping results to fit SeCuardian's UI/conversation flow."

### 3.4 Reference taxonomy

The 78-category Korean information-security industry taxonomy in `정보보호 솔루션.txt` (EDR, DLP, SIEM, SOAR,
CASB, etc.) is a useful checklist for future additions to `extra-agents/`: quickly decide whether new
material fits an already-covered category or represents a genuinely new one.

---

## Change Log

- Initial version: surveyed and classified ~90 items in `extra-agents/`, proposed 6 Addon Agent candidates
  (A–F), and documented the implementation guide.
- Second update: analyzed 9 new links (trueforge, orca, paseo, agent-fabric-dispatch, CLI-Anything,
  full-stack-ai-agent-template, openbot, picolm, Pythia) — all agent runtime/orchestration/edge-LLM
  infrastructure. Added §1.10. No new security Addon candidate (A–F unchanged); agent-fabric-dispatch,
  CLI-Anything, and the full-stack template adopted as own-infra references.
- Third update: analyzed 5 new links (Cybersecurity-Projects, turbo-fieldfare, KillerPDF, TeleVault,
  parse-server), added §1.11. Cybersecurity-Projects = security-training reference, turbo-fieldfare =
  edge LLM (picolm family), the other 3 out of scope. No new security Addon candidate (A–F unchanged).
- Fourth update: analyzed 5 new links (AI_SOC, Argus, semantica, Pentest-Swarm-AI, AgentDeck), added §1.12.
  AI_SOC & Argus = open-source reference implementations for `agentic-soc` (Apache-2.0), semantica = ISMS-P
  audit-provenance reference, Pentest-Swarm-AI = §2.3 offensive governance, AgentDeck = closed-source, out
  of scope. No new security Addon candidate (A–F unchanged).
- Fifth update: analyzed 11 new links, added §1.13. gato-x (GitHub Actions CI/CD security) → **new candidate
  G `cicd-security-scan`** (§2.2). The other 10 = AI/agent infra (LLMRouter, agentacct, latticedb, MegaMemory,
  NELLA, FreeToken, opensre, xyops) + dev tools (memray, diagram-design). Candidate list expanded to A–G.
- Sixth update: physically sorted the 125 root `.webloc` links into `ai-soc/` (78), `orchestrator/` (46),
  `ai-traffic-monitor/` (1) subfolders (§1 intro table). Analyzed 12 new links, added §1.14. No new
  candidate (A–G unchanged) — vps-audit → `hardening-auditor`, agentbehavior → `ai-eval-gate`, GhidraGPT →
  candidate D.
- Eighth update (2026-09-10): analyzed 1 new link (7onez/cti-expert), added §1.16. Bucket `ai-soc`, **no new
  candidate** — adopted as the CTI-depth reference (ATT&CK/ICD-203) for the built E (soc-intel-fusion), i.e. E's
  future extension via a ToolProxyAgent proxy.
- Seventh update (2026-09-10): **re-verified** classification — 17 misfiled security tools orchestrator→ai-soc,
  4 network tools → ai-traffic-monitor, agentops → orchestrator, removed 2 duplicates. Final: ai-soc 95,
  orchestrator 53, ai-traffic-monitor 6. Analyzed 28 new links, added §1.15. No new candidate — **recommend
  promoting candidate B (agentic-AI security) to top priority via agentseal/hackagent**; C·F reinforced.
