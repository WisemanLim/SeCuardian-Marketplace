# SeCuardian Agent 종합 카탈로그 — 구현 현황 + 확장 로드맵

> 대상: SeCuardian(본 제품) 및 SeCuardian-Marketplace(자산 배포)에 **기 구현된 에이전트** 전체와,
> `.docs/extra-agents/ADDON-AGENTS.md` 에서 도출한 **구현 필요 후보** 를 종합 정리한 문서.
> 분류 체계는 [extra-agents/ADDON-AGENTS.md](../.docs/extra-agents/ADDON-AGENTS.md) 와 동일한 구조
> (인벤토리 → 분류/커버리지 → 구현 가이드)를 따른다.
> 배포 자산 실체: `marketplace-assets/{security,addon,builtin,utilities}/`.

---

## 0. 아키텍처 배경

SeCuardian 은 **6계층 보안 모델**을 AI 에이전트로 연계하는 멀티에이전트 보안 플랫폼이다.
Orchestrator 가 사용자 인텐트를 분류해 적합한 에이전트로 라우팅한다. 에이전트는 형태에 따라 3종으로 나뉜다.

| 형태 | 정의 | 배포 방식 | 위치 |
|---|---|---|---|
| **Embedded (내장)** | `app/routers/router_*.py` 로 앱에 컴파일된 보안 라우터. `make seed-security` 로 `tbl_agent_config` 시드 | 앱 빌드에 포함 | SeCuardian `app/routers/` |
| **ADDON** | ZIP 업로드 → 동적 로더가 핫 디플로이. 재시작 불필요 | ZIP 패키지 | `marketplace-assets/security|utilities/` |
| **Template (개발 템플릿)** | 신규 에이전트 스캐폴딩 기반 (Board/Rag/Service/Shell/ToolProxy/UserManager) | ZIP 패키지 | `marketplace-assets/addon/` |

> 여러 내장 라우터는 ADDON 판(`router_vasca`→`vasca-cve`, `router_isms`→`isms-p-evidence`,
> `router_ai_eval`→`ai-eval-gate`)으로도 패키징돼 있다. 내장 = 항상 로드, ADDON = 선택 설치.

계층 정의: **L1** 신원·접근(Identity) · **L2** 엔드포인트(Endpoint) · **L3** 네트워크(Network) ·
**L4** 데이터(Data) · **L5** 탐지·대응(Detection/Response) · **L6** AI 보안(AI Security) · **Cross** 횡단.

---

## 1. 구현 현황 인벤토리 (기 구현 에이전트)

### 1.1 L1 — 신원·접근 제어 (Identity)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `keycloak-monitor` (`router_keycloak`) | E01 | 내장 | Keycloak SSO/IAM 모니터 (realm·client·user·세션) |
| `logto-monitor` (`router_logto`) | E01 | 내장 | Logto IAM 모니터 (대안 IdP) |
| `vault-monitor` (`router_vault`) | E02 | 내장 | HashiCorp Vault 시크릿 동적 발급·암호화 모니터 |
| `teleport-pam` | E17 | ADDON(`security/`) | Teleport 특권 접근(PAM) 세션 감사·활성 세션 조회 |

### 1.2 L2 — 엔드포인트 (Endpoint)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `falco-receiver` (`router_falco`) | E03 | 내장 | Falco 런타임 이벤트 수신 |
| `harbor-scanner` (`router_harbor`) | E03 | 내장 | Harbor 레지스트리 이미지 스캔 모니터 |
| `hardening-auditor` (`router_hardening`) | E05 | 내장 | Linux 서버 하드닝 감사 결과 수신 |
| `vasca-cve` (`router_vasca` + ADDON) | E07 | 내장+ADDON | 호스트·컨테이너 CVE 스캔 (worker: **VASCA_worker**, Go, bundled) |
| `behavior-noti` | E16 | ADDON(`security/`) | 호스트 이상행위 이벤트 웹훅 수신 (worker: **BehaviorNotiService_worker**, C++, bundled) |

### 1.3 L3 — 네트워크 (Network)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `caddy` (`router_caddy`) + `caddy-proxy` | E04 | 내장+ADDON(util) | Caddy 리버스 프록시 admin API 모니터·설정 리로드 |
| `crowdsec-monitor` (`router_crowdsec`) | E04 | 내장 | CrowdSec 위협 탐지·차단 모니터 |
| `cilium-netpol` (`router_cilium`) | E09 | 내장+ADDON | Cilium eBPF 네트워크 정책 + Hubble 플로우 (마이크로세그멘테이션) |
| `istio-mtls` (`router_istio`) | E10 | 내장 | Istio 서비스 메쉬 mTLS 모니터 |
| `teler-ids` (`router_teler`) | E11 | 내장+ADDON | teler HTTP 침입 탐지(IDS) 알림 수신·통계 |
| `wireproxy-ztna` (`router_wireproxy`) | E12 | 내장 | WireProxy 기반 ZTNA |

### 1.4 L4 — 데이터 (Data)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `neosync-dlp` (`router_neosync`) | E14 | 내장+ADDON | Neosync DLP 파이프라인 모니터·Job 관리 |
| `truffle-scan` | E08 | ADDON(util) | TruffleHog 시크릿 스캔 결과 웹훅 수신·조회 |

### 1.5 L5 — 탐지·대응 (Detection / Response)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `wazuh-siem` (`router_wazuh`) | E06 | 내장 | Wazuh SIEM/XDR 모니터 |
| `observability` (`router_observability`) | E06 | 내장 | Observability 스택 모니터 |
| `shuffle-soar` (`router_soar`) | E13 | 내장+ADDON | Shuffle SOAR 워크플로우 트리거·결과 수집 (execution) |
| `velociraptor-dfir` (`router_dfir`) | E18 | 내장+ADDON | Velociraptor 엔드포인트 포렌식 헌팅·아티팩트 수집 |
| `agentic-soc` (`router_agentic_soc`) | E20/E21 | 내장+ADDON | 보안 에이전트를 A2A 오케스트레이션, 인시던트 트리아지·플레이북 (federation) |

### 1.6 L6 — AI 보안 (AI Security)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `ai-eval-gate` (`router_ai_eval`) | E20 | 내장+ADDON | AI 배포 전 PyRIT·SkillSpector·agentshield 평가·게이트 판정 (기본 비활성, 보안팀 승인 필요) |
| `ai-redteam` (`router_redteam`) ⚠️ | E19/E21 | 내장+ADDON | PyRIT·SkillSpector LLM 탈옥·프롬프트 인젝션 적대적 스캔 (**격리망 + 서면 승인 필수**) |

### 1.7 Cross — 횡단 (Compliance / Observability / Adapter)

| 에이전트 | Epic | 형태 | 요약 |
|---|---|---|---|
| `compliance-isms` / `isms-p-evidence` (`router_isms`) | E22 | 내장+ADDON | ISMS-P 인증 감사 증거 자동 수집·통제항목 점검 (Wazuh·Keycloak·Vault·Teleport·VASCA·Neosync·SOAR 연계) |
| `otel-collector` (`router_otel`) | E15 | 내장+ADDON | OpenTelemetry Collector 헬스·파이프라인·메트릭을 MCP Tool 로 노출 |
| `grafana-dashboard` | — | ADDON(util) | Grafana 대시보드 패널을 임베딩·벡터검색으로 질의응답 (RAG) |
| `ai-traffic-monitor` | E15 | ADDON(util) | 브라우저 자동연결 AI 도우미의 트래픽 사용량 정량 측정 (vnstat/nethogs/tshark 래핑) |

### 1.8 플랫폼 내장 에이전트 (SeCuardian-Marketplace `builtin/`)

보안 도메인이 아닌, **플랫폼 운영 자체**를 담당하는 내장 에이전트 (Marketplace 앱의 `router_*` 패키징판).

| 에이전트 | 유형 | 요약 |
|---|---|---|
| `guardrails` | service | PII·신용정보 등 도메인별 콘텐츠 안전 판정. global + 24개 도메인 규칙셋(금융·의료·제조·공공 등) |
| `marketplace` | service | 에이전트·워크플로우·RAG·툴프록시 자산 카탈로그 등록·설치·해제 |
| `playground` | service | 프롬프트·모델 조합 대화형 LLM 실험 (Ollama 연동, degrade 폴백) |
| `rag` | rag | 컬렉션 CRUD·문서 ingest·하이브리드 검색 |
| `workflow` | service | DAG 워크플로우 CRUD + 실행·HITL 승인·취소 |

### 1.9 개발 템플릿 (SeCuardian-Marketplace `addon/`)

신규 에이전트 스캐폴딩의 기준 템플릿. §3 구현 시 출발점.

| 템플릿 | 유형 | 용도 |
|---|---|---|
| `Board` | app (fe+be) | CRUD 게시판 — 화면 포함 앱 에이전트 기준 예제 |
| `UserManager` | app (fe+be) | 사용자 검색·CRUD·비밀번호 초기화 |
| `RagAgent` | rag | 문서 임베딩 + 벡터검색 RAG 골격 |
| `ServiceAgent` | service | 백엔드 비즈니스 로직 서비스 골격 |
| `ShellAgent` | service | 읽기전용 CLI/셸 진단 (**CLI 래핑 안전 모델의 레퍼런스**, supervisor/admin) |
| `ToolProxyAgent` | tool-proxy | 외부 REST API → MCP Tool 변환 어댑터 |

---

## 2. 커버리지 분석 — 구현됨 vs 구현 필요

`extra-agents/ADDON-AGENTS.md` §2 의 후보(A~G)를 위 6계층 커버리지에 대입하면, SeCuardian 은
**방어자 관점 관측·대응(L1~L6 내부 자산 모니터링)** 은 촘촘하지만, **외부 공격표면 관점**과
**에이전틱 AI 자체 보안** 은 아직 빈틈이 있다.

### 2.1 잘 커버된 영역 (기 구현)

- **내부 자산 모니터링**: IAM(Keycloak/Vault/Teleport) · 엔드포인트(Falco/Harbor/VASCA/Behavior) ·
  네트워크(Cilium/Istio/teler/CrowdSec/WireProxy) · 데이터(Neosync/TruffleHog) · 탐지대응(Wazuh/SOAR/DFIR/SOC).
- **컴플라이언스**: ISMS-P 증거 자동 수집.
- **AI 보안(내부)**: 배포 전 평가 게이트(ai-eval-gate) + 레드팀 스캔(ai-redteam).

### 2.2 빈틈 → 구현 필요 후보 (extra-agents 근거)

| 후보 (extra-agents §2) | 채우는 빈틈 | 계층 | 우선순위 | 재사용 기반 |
|---|---|---|---|---|
| **A. `attack-surface-recon`** | 외부 공격표면(OSINT) 정찰 — 현재 전무 | L3 확장 | 상 | `ai-traffic-monitor`/`ShellAgent` (CLI 래핑) |
| **B. `agentic-threat-model`** | 자사 AI 에이전트/MCP 구성 위협 모델링 — 현재 전무 | L6 확장 | 상 | 정적 분석, 읽기전용 |
| **C. `api-vuln-scan`** | API OWASP Top10 능동 스캔 (teler/vasca 는 수신형) | L2/L4 | 상 | `ShellAgent` + VAmPI 테스트베드 |
| **D. `malware-hunt`** | 공급망 위장 악성코드 IOC 헌팅 | L2 확장 | 중 | `truffle-scan` 인접 |
| **E. `soc-intel-fusion`** | CVE/EPSS/KEV/ATT&CK 통합 조회 | L5 확장 | 중 | `cve-mcp-server` MCP 프록시(`ToolProxyAgent`) |
| **F. `ad-security-scan`** | Active Directory 취약 설정 점검 | L1 확장 | 중 | `ShellAgent` + `teleport-pam` 인접 |
| **G. `cicd-security-scan`** | CI/CD 파이프라인(GitHub Actions) 보안 정적분석 — 현재 전무 | L4 공급망 | 중 | gato-x(정적분석 모드) + `truffle-scan`/`harbor` 인접 |

### 2.3 정책상 보류 (방어자 정체성 상충)

- **자율 공격/익스플로잇 계열** (hexstrike-ai·strix·T3MP3ST·Decepticon 등): 정식 제품 내장은 신중.
  채택 시 **승인된 격리 랩 전용** + 대상 화이트리스트 + 승인 로그 필수. `ai-redteam` 의 격리망 모델 준용.
- **커널 제로데이/AV·EDR 우회**: Addon 화 부적합 — 오프라인 리서치 도구로 유지.

---

## 3. 구현 시 참고 사항

### 3.1 신규 ADDON 개발 절차 (표준 흐름)

`extra-agents/ADDON-AGENTS.md` §3 + `addon-agents/README.md` 절차 동일. 요약:

1. **PRD 작성** — `ai-traffic-monitor/PRD-ai-traffic-monitor.md` 를 실제 템플릿으로 사용. Non-goals 먼저 명시.
2. **템플릿 선택** — 화면 있음 → `Board`/`UserManager`, CLI 래핑 → `ShellAgent`, RAG → `RagAgent`,
   외부 API 프록시 → `ToolProxyAgent`, 순수 백엔드 → `ServiceAgent`.
3. **파일 구성** — `{AgentName}-meta.json`(필수) + `-app.py`/`-front.tsx`/`-sql.sql`(선택). prefix 없이
   `tbl_agent_config` key 와 동일 명명. 내장 키와 중복 금지(409 `builtin_conflict`).
4. **엔드포인트 순서** — `GET /status`(도구 가용성) → 읽기 조회 → 특권 작업(`POST /scan` 등, `require_role`).
5. **worker 동봉** — 별도 바이너리 필요 시(예: A 후보의 스캐너) `{key}-worker-guide.md` 내장 + meta.json
   `worker` 블록 선언(`kind: bundled|external`). `VASCA_worker`(Go)/`BehaviorNotiService_worker`(C++) 참고.
6. **시험** — `test/impl/<Nth>/{scenario,result}.md` + `ITManually.sh` 배치 추가.
7. **문서화** — `addon-agents/README.md`(한/영) 및 본 카탈로그 갱신.

### 3.2 CLI 래핑 안전 모델 (A·C·D·F 후보 필수)

`ShellAgent`/`ai-traffic-monitor` 의 실행 안전 모델 준용:

- 외부 실행은 항상 **`shell=False` + 내부 조립 argv** (사용자 문자열 셸 직접 주입 금지).
- 바이너리 **allowlist** 고정(예: `nmap dig whois subfinder amass`).
- 입력 검증: 도메인/IP 는 정규식·`ipaddress` 파싱, 정수 파라미터 상한 클램프, 파일경로 전용 디렉터리 봉쇄.
- 특권 작업은 `require_role`(supervisor/admin).
- 도구 미설치/미구성 시 500 아닌 **503 + 안내** 로 우아하게 저하 (orchestrator 가 502 로 오인·중단 방지).
- ⚠️ `from __future__ import annotations` **금지** — 동적 로더가 `sys.modules` 미등록 → pydantic 지연
  어노테이션 해석 실패 → 500.

### 3.3 공격형 도구 거버넌스 (A 후보 + 2.3 계열)

- **대상 화이트리스트**: 스캔 대상은 사전 등록 자산에서만 선택(자유 입력 금지 또는 도메인 소유권 검증).
- **승인 이력**: 실행 전 supervisor/admin 승인 + 실행 로그(누가/언제/무엇).
- **격리 우선**: `VAmPI`·`Exegol`·`bugbounty-lab101` 통제 타깃 선검증 후 실자산 확대.
- **이중용도 고지**: README·UI 에 "승인된 보안 테스트 전용" 경고. `ai-redteam` 의 `redteam-isolated` 모델 준용.

### 3.4 외부 MCP 서버 프록시 (E 후보)

`cve-mcp-server` 처럼 이미 완성된 MCP 서버는 `-app.py` 신작보다 `ToolProxyAgent` 로 프록시하는 편이
개발비 낮음. Addon 역할은 "프록시 설정 + 결과를 SeCuardian UI/대화 흐름에 맞게 가공" 으로 축소.

### 3.5 자체 인프라 참고 (extra-agents 2차 추가분, §1.10)

extra-agents 최근 추가 링크 9건은 신규 보안 에이전트가 아닌 **에이전트 런타임/오케스트레이션/엣지-LLM 인프라**
로, 보안 로드맵(§4)은 불변이다. 다만 구현·플랫폼 설계에 다음 3건이 직접 참고 가치가 있다.

- **`falcons-eyes/agent-fabric-dispatch`** — 로컬(Ollama) 우선 라우팅 + 불확실 작업만 Claude 폴백(비용 79%↓).
  `router_llm` 미터링·라우팅 정책 설계 참고.
- **`HKUDS/CLI-Anything`** — 소프트웨어를 에이전트-네이티브 CLI로 노출. §3.1~3.2 CLI 래핑 패턴·`ToolProxyAgent` 보강.
- **`vstorm-co/full-stack-ai-agent-template`** — FastAPI+Next.js 풀스택 AI 에이전트 템플릿(스택 일치).
  화면형 Addon(`Board`/`UserManager`) 스캐폴딩 참고.

> 상세 근거: [extra-agents/ADDON-AGENTS.md §1.10](../.docs/extra-agents/ADDON-AGENTS.md).

### 3.6 `agentic-soc` 참조 구현 (extra-agents 4차 추가분, §1.12)

기 구현 `agentic-soc`(§1.5 L5)를 실제 배포 스택으로 구체화한 **오픈소스 참조 구현 2건**이 확보됐다. 신규
에이전트는 아니며, agentic-soc 내부(트리아지·상관·RAG·워크플로) 강화 시 참고한다.

- **`zhadyz/AI_SOC`** (Apache-2.0) — Wazuh + Ollama LLM(Foundation-Sec-8B) + ML 트리아지(RF/XGBoost) +
  ChromaDB RAG, Docker Compose. **스택이 SeCuardian `agentic-soc`+`wazuh-siem`+`rag` 삼종과 일치 → 1순위 참고.**
- **`Sec-Link/Argus-Agentic-SOC-Platform`** (Apache-2.0) — 알림 수집·인시던트 조사·티켓·자산 상관·워크플로
  오케스트레이션. 인시던트 워크플로 UX·자산 상관 설계 참고(`shuffle-soar` 연계).
- 참고: `semantica-agi/semantica`(W3C 프로버넌스·감사 그래프)는 `isms-p-evidence` 감사 로그 설계에 간접 참고.

> 상세 근거: [extra-agents/ADDON-AGENTS.md §1.12](../.docs/extra-agents/ADDON-AGENTS.md).

---

## 4. 종합 로드맵 요약

| 상태 | 에이전트 | 계층 |
|---|---|---|
| ✅ 구현됨 (내장) | keycloak/logto/vault, falco/harbor/hardening, crowdsec/istio/wireproxy, wazuh/observability | L1~L5 |
| ✅ 구현됨 (내장+ADDON) | vasca-cve, cilium-netpol, teler-ids, neosync-dlp, shuffle-soar, otel-collector, teleport-pam, velociraptor-dfir, agentic-soc, ai-eval-gate, ai-redteam⚠️, isms-p-evidence | L1~L6, Cross |
| ✅ 구현됨 (ADDON util) | truffle-scan, caddy-proxy, grafana-dashboard, ai-traffic-monitor | L3·L4·Cross |
| ✅ 플랫폼 내장 | guardrails, marketplace, playground, rag, workflow | 플랫폼 |
| 🟡 구현 후보 (상) | attack-surface-recon(A), agentic-threat-model(B), api-vuln-scan(C) | L3·L6·L2 |
| 🟡 구현 후보 (중) | malware-hunt(D), soc-intel-fusion(E), ad-security-scan(F), cicd-security-scan(G) | L2·L5·L1·L4 |
| ⛔ 정책 보류 | 자율 공격 자동화, 커널 제로데이, AV/EDR 우회 | — |

---

## 변경 이력

- 최초 작성: SeCuardian/SeCuardian-Marketplace 기 구현 에이전트(내장 24 라우터 + ADDON 13 + 유틸 5 +
  플랫폼 내장 5 + 템플릿 6) 6계층 분류, extra-agents 구현 후보(A~F) 커버리지 매핑, 구현 가이드 종합.
- 2차 갱신: extra-agents 신규 링크 9건 반영. 모두 에이전트 인프라(런타임/오케스트레이션/엣지-LLM)로 보안
  로드맵 불변. §3.5 자체 인프라 참고(agent-fabric-dispatch·CLI-Anything·풀스택 템플릿) 추가.
- 3차 갱신: extra-agents 신규 링크 5건(Cybersecurity-Projects·turbo-fieldfare·KillerPDF·TeleVault·
  parse-server) 검토. 보안 훈련 레퍼런스 1 + 엣지 LLM 1 + 범위 외 3으로, 신규 보안 에이전트 없음.
  로드맵 불변. 상세: extra-agents/ADDON-AGENTS.md §1.11.
- 4차 갱신: extra-agents 신규 링크 5건(AI_SOC·Argus·semantica·Pentest-Swarm-AI·AgentDeck) 검토.
  AI_SOC·Argus=`agentic-soc` 오픈소스 참조 구현으로 §3.6 추가. 신규 보안 에이전트 없음, 로드맵 불변.
  상세: extra-agents/ADDON-AGENTS.md §1.12.
- 5차 갱신: extra-agents 신규 링크 11건 검토. gato-x(GitHub Actions CI/CD 보안)로 **신규 후보 G
  `cicd-security-scan` 추가**(§2.2·§4). 나머지 10건=AI/에이전트 인프라·개발툴. 상세: ADDON-AGENTS.md §1.13.
