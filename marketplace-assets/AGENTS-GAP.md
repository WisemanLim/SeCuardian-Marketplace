# SeCuardian Agent 구현 갭 분석 — SeCMP-PRD 도출 + marketplace-assets 대비

> 기준일: 2026-09-10.
> 근거: [.docs/SeCMP-PRD.md](../.docs/SeCMP-PRD.md)(플랫폼 PRD), [marketplace-assets/AGENTS.md](./AGENTS.md)(구현 인벤토리),
> [.docs/extra-agents/ADDON-AGENTS.md](../.docs/extra-agents/ADDON-AGENTS.md)(오픈소스 조사·후보 A~G).
> 목적: PRD가 요구하는 에이전트를 도출하고, `marketplace-assets/` 에 **이미 구현된 것**과 대조해
> **추가 구현이 필요한 에이전트**만 추린다.

---

## 1. PRD(SeCMP)가 요구하는 에이전트 — 플랫폼 빌트인 (도출)

SeCMP-PRD 는 **Marketplace 플랫폼** PRD 다. 여기서 "에이전트"로 요구하는 것은 6종 **플랫폼 내장 에이전트**이며,
전부 이미 구현(✅/🟡)돼 있다. **신규 플랫폼 에이전트 요구는 없다** — 잔여는 에이전트가 아닌 기능(feature) 수준.

| PRD 기능 | 내장 에이전트 | 상태(§9) | 잔여(에이전트 아님, 기능) |
|---|---|---|---|
| F-MP | `marketplace` | ✅ | GPG 키 로테이션·mTLS 실핸드셰이크(운영) |
| F-WF | `workflow` | 🟡 | code 노드(샌드박스)·loop/sub-flow/cron·llm 노드 Claude 연동 |
| F-RAG | `rag` | 🟡 | Qdrant 확장·임베딩모델 교체(sentence-transformers) |
| F-PG | `playground` | 🟡 | cost 추적·eval 실행 |
| F-GRD | `guardrails` | 🟡 | 25종 업종 ML classifier(SeCMP 책임 밖)·실 MCP 통합시험 |
| F-AI | `assistant`/orchestrator | ✅ | 공유 `services/llm.py` 분리(리팩터) |

> **결론(파트2)**: PRD에서 도출되는 **신규 에이전트는 없음**. 플랫폼 6종은 모두 존재하며, 남은 것은 기능 보강.
> "구현 필요 에이전트"는 PRD 플랫폼이 아니라 **보안 에이전트 자산(카탈로그)** 라인에서 나온다(§3).

---

## 2. 현재 구현된 marketplace-assets 인벤토리 (2026-09-10)

| 분류 | 수 | 목록 |
|---|---|---|
| **security** (보안 에이전트 자산) | 21 (+worker 2) | agentic-soc, ai-eval-gate, ai-redteam, behavior-noti, cilium-netpol, compliance-isms, crowdsec-monitor, falco-receiver, harbor-scanner, hardening-auditor, isms-p-evidence, keycloak-monitor, neosync-dlp, otel-collector, shuffle-soar, teleport-pam, teler-ids, vasca-cve, vault-monitor, velociraptor-dfir, wazuh-siem (+ VASCA_worker, BehaviorNotiService_worker) |
| **builtin** (플랫폼 내장) | 5 | guardrails, marketplace, playground, rag, workflow |
| **utilities** | 5 | ai-traffic-monitor, caddy-proxy, grafana-dashboard, server-shell, truffle-scan |
| **addon** (개발 템플릿) | 6 | Board, RagAgent, ServiceAgent, ShellAgent, ToolProxyAgent, UserManager |

> 이전 [AGENTS.md](./AGENTS.md) §1 은 security 13종 기준으로 작성됐으나, 이후 본 제품 내장 모니터
> (keycloak·vault·falco·harbor·hardening·crowdsec·wazuh·compliance-isms)까지 자산 패키징되어 **21종으로 확대**됐다.

---

## 3. 추가 구현이 필요한 에이전트 (갭)

### 3.1 신규 보안 에이전트 — extra-agents 후보 A~G (marketplace-assets 미존재)

후보 A~G 중 **marketplace-assets/security 에 존재하는 것은 없음** → 전부 미구현 갭.
근거·재사용은 [ADDON-AGENTS.md §2](../.docs/extra-agents/ADDON-AGENTS.md) + 조사 강화(§1.15).

| 후보 | 에이전트 | 채우는 갭 | 우선순위 | 재사용 기반 | 상태 |
|---|---|---|---|---|---|
| **B** | `agentic-threat-model` | 자사 MCP/스킬/에이전트 설정 보안 스캔·위협모델(정적+런타임 2모드) | **최상(승격)** | agentseal·hackagent·AgentHound·Agent-Wiz + `ShellAgent`/정적분석 | 미구현 |
| **A** | `attack-surface-recon` | 외부 공격표면 OSINT 정찰 | 상 | spiderfoot·reconftw·noir·osiris + `ShellAgent` CLI 래핑 | 미구현 |
| **C** | `api-vuln-scan` | API/웹 OWASP Top10 능동 스캔·Shadow API 발견 | 상 | Nettacker·burp-ai-agent·owasp-noir·owasp-top10-skills·VAmPI(타깃) | 미구현 |
| **G** | `cicd-security-scan` | CI/CD(GitHub Actions) 정적 보안 감사 | 중 | gato-x(정적모드) + `truffle-scan`/`harbor` 인접 | 미구현 |
| **F** | `ad-security-scan` | Active Directory 취약설정·공격경로 | 중 | ADScanPro·NetSPI/AD-PathFinder + `teleport-pam` 인접 | 미구현 |
| **D** | `malware-hunt` | 공급망 위장 악성코드 IOC 헌팅 | 중 | malwoverview·GhidraGPT + `truffle-scan` 인접 | 미구현 |
| **E** | `soc-intel-fusion` | CVE/EPSS/KEV/ATT&CK 통합 조회 | 중 | cve-mcp-server(MCP 프록시)·IntelOwl·nmap-vulners | 미구현 |

> **B를 최우선 승격**: SeCuardian 자신이 MCP/A2A 플랫폼 → 자기 MCP·스킬·에이전트 설정을 스캔하는 B의
> 효용이 가장 직접적. agentseal(라이브 MCP tool-poisoning 감사)·hackagent 로 근거 두터움(§1.15).

### 3.2 자산 패키징 갭 — 본 제품 내장 O, 마켓 자산 X

SeCuardian 본 제품에는 내장 라우터로 존재하나 `marketplace-assets/security` 로 **아직 패키징되지 않은** 4종.
신규 개발이 아니라 **기존 라우터의 ADDON 패키징**(vasca-cve·isms-p-evidence 선례와 동일)이면 된다.

| 에이전트 | 본 제품 라우터 | 계층 | 작업 |
|---|---|---|---|
| `logto-monitor` | `router_logto` | L1 Identity | ADDON 패키징 |
| `istio-mtls` | `router_istio` | L3 Network | ADDON 패키징 |
| `wireproxy-ztna` | `router_wireproxy` | L3 Network | ADDON 패키징 |
| `observability-monitor` | `router_observability` | L5 | ADDON 패키징 |

### 3.3 참고 — 에이전트가 아닌 플랫폼 기능 갭

구현 필요 목록이지만 "에이전트"가 아닌 기능(§1 잔여 재게시): Qdrant 확장·임베딩모델 교체·워크플로우 code
노드/loop/cron·llm 노드 Claude 연동·Playground cost·eval·멀티테넌시 namespace·HITL 테이블·OWASP 스코어카드.

---

## 4. 종합 — "추가 구현 필요 에이전트" 최종 목록

1. **신규 보안 에이전트 7종** (우선순위): **B** `agentic-threat-model`(최상) → **A** `attack-surface-recon` ·
   **C** `api-vuln-scan`(상) → **G** `cicd-security-scan` · **F** `ad-security-scan` · **D** `malware-hunt` ·
   **E** `soc-intel-fusion`(중).
2. **패키징 4종**: `logto-monitor` · `istio-mtls` · `wireproxy-ztna` · `observability-monitor`(기존 라우터 ADDON화).
3. **플랫폼 신규 에이전트**: 없음(PRD 6종 전부 구현, 잔여는 기능 보강).

> 구현 절차·안전 모델·거버넌스는 [ADDON-AGENTS.md §3](../.docs/extra-agents/ADDON-AGENTS.md) 및
> `ai-traffic-monitor/PRD-ai-traffic-monitor.md`(실제 작성 사례) 준용.

---

## 변경 이력
- 최초 작성(2026-09-10): SeCMP-PRD 도출(플랫폼 6종 = 구현완료, 신규 없음) + marketplace-assets 현행 인벤토리
  (security 21·builtin 5·utilities 5·templates 6) 대비 → 추가 구현 필요 = 보안 에이전트 7종(A~G, B 최우선) +
  패키징 4종.
