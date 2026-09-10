# Addon Agent 후보 조사 — extra-agents 자료 개요

> 대상 디렉터리: `.docs/extra-agents/`
> 목적: SeCuardian(Security for Guardian)에서 제공할 **차기 Addon Agent** 후보를 찾기 위해 수집한
> GitHub 오픈소스·기사·PDF·리서치 자료를 조사·분류하고, 실제 구현 시 참고 방법을 정리한다.
> 이 문서는 소스 자료 목록이며, 실제 구현은 [addon-agents/README.md](../../addon-agents/README.md)의
> 절차(스캐폴딩 Wizard → meta.json/app.py/sql/front → 시험 → 배포)를 따른다.

---

## 1. 자료 인벤토리

`extra-agents/`에는 `.webloc`(GitHub 등 링크), `.md`(Perplexity 리서치 결과), `.pdf`/`.jpeg`(가이드·인포그래픽),
`.txt`(분류 체계), 그리고 이미 PRD까지 작성된 하위 폴더(`ai-traffic-monitor/`)가 섞여 있다. 총 90여 건을 아래
9개 카테고리로 분류했다.

> **디렉터리 재구성(2026-08-29) + 재검증(2026-09-10)**: 루트 `.webloc` 링크를 SeCuardian 3대 워크스트림
> 하위 폴더로 물리 분류했다. 배경 리서치 문서(`.md`/`.pdf`/`.txt`)는 참조 편의상 루트에 유지한다.
> **9-10 재검증**: `orchestrator/`에 오분류돼 있던 보안툴 17건을 `ai-soc/`로, 네트워크툴 3건과 `ai-soc/`의
> `NETworkManager`를 `ai-traffic-monitor/`로, 에이전트 관측(`agentops`)을 `orchestrator/`로 재배치하고
> 중복 2건(`strix`·`reverse-skill`)을 제거했다. 3분류로 충분해 추가 카테고리는 만들지 않았다(분류 기준:
> **보안 도구/에이전트→ai-soc**, **네트워크·트래픽 관측→ai-traffic-monitor**, **에이전트 런타임·LLM 인프라→orchestrator**).
>
> | 하위 폴더 | 건수 | 담는 것 | 대응 §1 카테고리 |
> |---|---|---|---|
> | `ai-soc/` | 95 | 보안 에이전트·도구(OSINT·펜테스트·취약점·악성코드·SOC/DFIR·에이전틱 AI 보안·MCP/스킬 보안·CI/CD·인증서·컴플라이언스·훈련) | §1.1~1.8, 1.11~1.15(보안분) |
> | `orchestrator/` | 53 | 에이전트 런타임·오케스트레이션·LLM 인프라(라우팅·RAG·메모리·지식그래프·파인튜닝·엣지·에이전트 IDE·평가·관측) | §1.9, 1.10, 1.13~1.15(인프라분) |
> | `ai-traffic-monitor/` | 6 | 네트워크·트래픽 관측(sniffnet·L0p4Map·netwatch·tailcat·nport·NETworkManager + 기존 PRD·리서치) | §1.4 트래픽 관측분 |

### 1.1 OSINT / 공격표면 정찰 (Recon)

외부에 노출된 자산(도메인·서브도메인·IP·계정·이메일)을 공개 정보로 찾아내는 도구. SeCuardian이 "우리 조직이
공격자 시점에서 어떻게 보이는가"를 답하려면 이 계열이 필요하다.

| 소스 | 링크 | 요약 |
|---|---|---|
| smicallef/spiderfoot | github.com/smicallef/spiderfoot | OSINT 자동화 표준 도구. 위협 인텔·공격표면 매핑, 200+ 모듈 |
| six2dez/reconftw | github.com/six2dez/reconftw | 도메인 대상 recon 파이프라인 자동화(서브도메인→취약점까지 일괄) |
| thewhiteh4t/FinalRecon | github.com/thewhiteh4t/FinalRecon | 웹 정찰 올인원(헤더·WHOIS·DNS·서브도메인·포트) |
| edoardottt/cariddi | github.com/edoardottt/cariddi | 도메인 크롤링 → 엔드포인트/시크릿/API 키/토큰 탐지 |
| khashashin/ogi | github.com/khashashin/ogi | 링크 분석 기반 OSINT 프레임워크 |
| XD-MHLOO/Osintgraph | github.com/XD-MHLOO/Osintgraph | OSINT 그래프 시각화 |
| karim852/KUMO-Domain-Recon-Tool | github.com/karim852/KUMO-Domain-Recon-Tool | 도메인 정찰 도구 |
| DevCop95/shodan_reconsx | github.com/DevCop95/shodan_reconsx | Shodan 기반 수동적(passive) 호스트네임 정찰 |
| Alfredredbird/tookie-osint | github.com/alfredredbird/tookie-osint | 소셜미디어 계정 OSINT |
| p1ngul1n0/blackbird | github.com/p1ngul1n0/blackbird | 사용자명/이메일 기반 SNS 계정 탐색 |
| KatrielMoses/MailAccess | github.com/KatrielMoses/MailAccess | 이메일 OSINT — 2500+ 플랫폼, 유출 탐지, API 키 불필요 |
| kaifcodec/user-scanner | github.com/kaifcodec/user-scanner | 사용자명 스캐너 |
| tuanngocptn/nport | github.com/tuanngocptn/nport | 포트 스캔 도구 |
| Perplexity — OSINT 개념 조사 | `Perplexity-OSINT는 Open Source Intelligence...md` | OSINT 정의·활용분야·공격자/방어자 양측 관점 정리(배경 지식) |

### 1.2 AI 기반 침투테스트 자동화 (Offensive AI / AI Pentest)

LLM 에이전트가 정찰→취약점 탐지→익스플로잇 시도까지 자동 수행하는 최신 계열. **승인된(authorized) 대상에만
사용 가능해야 하는 이중용도(dual-use) 도구**이므로 구현 시 거버넌스가 필수.

| 소스 | 링크 | 요약 |
|---|---|---|
| 0x4m4/hexstrike-ai | github.com/0x4m4/hexstrike-ai | AI 에이전트용 공격 도구 오케스트레이션 프레임워크 |
| usestrix/strix | github.com/usestrix/strix | 오픈소스 AI 침투테스트 — 취약점 발견+수정 제안까지 |
| vigolium/vigolium | github.com/vigolium/vigolium | 에이전틱 AI + 네이티브 속도의 고정밀 취약점 스캐너 |
| Kritt-ai/open-kritt | github.com/Kritt-ai/open-kritt | 자체 호스팅 AI 취약점 리서치 — 에이전트가 코드 내 이슈 탐지·검증 |
| ARCANGEL0/EVA | github.com/ARCANGEL0/EVA | AI 지원 침투테스트 에이전트, 멀티 백엔드 AI 통합 |
| PurpleAILAB/Decepticon | github.com/PurpleAILAB/Decepticon | 자율 해킹 에이전트(레드팀) |
| elder-plinius/T3MP3ST | github.com/elder-plinius/T3MP3ST | 자율 레드티밍 플랫폼, 멀티에이전트 공격 메타-하네스 |
| nishu2402/HEAVEN | github.com/nishu2402/HEAVEN-Autonomous-Penetration-Testing | 자율 침투테스트 |
| 0xSteph/pentest-ai-agents | github.com/0xSteph/pentest-ai-agents | 펜테스트 AI 에이전트 모음 |
| 0xwilliamortiz/claude-red | github.com/0xwilliamortiz/claude-red | Claude 기반 레드팀 도구 |
| elementalsouls/Claude-BugHunter | github.com/elementalsouls/Claude-BugHunter | Claude 기반 버그헌팅 |
| yee-yore/DorkAgent | github.com/yee-yore/DorkAgent | LLM 기반 구글 도킹 자동화(버그바운티/펜테스트) |
| AKCodez/hackingtool-plugin | github.com/AKCodez/hackingtool-plugin | Claude Code 플러그인 — 183+ 펜테스트/OSINT 도구 자동 실행 |

### 1.3 웹/API 취약점 스캐닝

| 소스 | 링크 | 요약 |
|---|---|---|
| OWASP/Nettacker | github.com/OWASP/Nettacker | OWASP 공식 자동 침투테스트/취약점 스캐너 |
| Teycir/BurpAPISecuritySuite | github.com/Teycir/BurpAPISecuritySuite | Burp Suite용 API 보안 확장 |
| erev0s/VAmPI | github.com/erev0s/VAmPI | OWASP API Top 10 취약점을 내장한 **훈련용 취약 API**(테스트베드) |
| hahwul/WebHackersWeapons | github.com/hahwul/WebHackersWeapons | 웹 해커 도구 큐레이션 목록 |

### 1.4 네트워크 / 무선 / 인증서 인프라

| 소스 | 링크 | 요약 |
|---|---|---|
| D3Ext/WEF | github.com/D3Ext/WEF | Wi-Fi 익스플로잇 프레임워크 |
| BornToBeRoot/NETworkManager | github.com/BornToBeRoot/NETworkManager | 네트워크 관리/트러블슈팅 GUI 도구 |
| GyulyVGC/sniffnet | github.com/GyulyVGC/sniffnet | 인터넷 트래픽 실시간 모니터링(러스트) |
| ADScanPro/adscan | github.com/ADScanPro/adscan | Active Directory 보안 스캐너 |
| htrgouvea/nipe | github.com/htrgouvea/nipe | Tor 네트워크를 기본 게이트웨이로 전환 |
| hakwerk/labca | github.com/hakwerk/labca | 내부용 사설 인증기관(ACME 기반) |

### 1.5 악성코드 분석 / 리버싱 / 커널 취약점 연구

| 소스 | 링크 | 요약 |
|---|---|---|
| 416rehman/DeepZero | github.com/416rehman/DeepZero | Windows 커널 드라이버 대량 분석 → IOCTL 제로데이 자동 탐색 |
| alexandreborges/malwoverview | github.com/alexandreborges/malwoverview | 악성코드 초기 triage 도구(다중 위협 인텔 API 연동) |
| darama22/Malware-Research-Hub | github.com/darama22/Malware-Research-Hub | 악성코드 80종 패밀리 + 2,764 샘플 카탈로그(로컬 Flask, 이중언어) |
| mito753/Kernel-Exploit-Dojo | github.com/mito753/Kernel-Exploit-Dojo | CTF 커널 익스플로잇 노트/PoC |
| thomasxm/BOAZ_beta | github.com/thomasxm/BOAZ_beta | 다계층 AV/EDR 우회 프레임워크(유지보수 중단) |
| zhaoxuya520/reverse-skill | github.com/zhaoxuya520/reverse-skill | 리버스 엔지니어링 스킬 모음 |
| HackUnderway/CyberLeaks | github.com/HackUnderway/CyberLeaks | 사이버 유출 정보 관련 |
| "AI 개발도구 위장 악성코드 감염 헌팅가이드" (PDF) | 로컬 파일 | npm/VSCode 확장 등 AI 개발도구로 위장한 악성코드 헌팅 방법론 |

### 1.6 에이전틱 AI 보안 (AI 에이전트/MCP 자체를 지키는 보안)

**SeCuardian이 가장 주목해야 할 신흥 카테고리.** LLM 에이전트·MCP 서버·A2A 통신 자체가 공격 표면이 되는
시대의 방어 도구.

| 소스 | 링크 | 요약 |
|---|---|---|
| adithyan-ak/AgentHound | github.com/adithyan-ak/AgentHound | "에이전틱 스택을 위한 BloodHound" — MCP/A2A/게이트웨이 정찰, 자격증명 탈취, 모델 유출·오염, 공격 경로 분석 |
| perplexityai/numbat | github.com/perplexityai/numbat | 엔드포인트에서 AI 에이전트 활동 가시성 — 온디바이스 탐지, 사전 차단, 포렌식 재구성 |
| secureagentics/Adrian | github.com/secureagentics/Adrian | 런타임 AI 에이전트 보안 — 악성 도구 사용/프롬프트 인젝션/정책 이탈을 행동 전에 탐지 |
| Repello-AI/Agent-Wiz | github.com/Repello-AI/Agent-Wiz | LangGraph/AutoGen/CrewAI 등으로 만든 AI 에이전트 위협 모델링·시각화 CLI |
| anthropics/claude-code-security-review | github.com/anthropics/claude-code-security-review | Claude 기반 코드 변경분 보안 리뷰 GitHub Action |
| mukul975/cve-mcp-server | github.com/mukul975/cve-mcp-server | Claude용 MCP 서버 — CVE/EPSS/CISA KEV/MITRE ATT&CK/Shodan/VirusTotal 등 21개 API 통합 |
| "AI 개발도구 위장 악성코드..." (PDF, 1.5 재인용) | 로컬 파일 | 공급망(서플라이체인) 관점의 AI 개발도구 위장 위협 |

### 1.7 SOC / 위협 인텔리전스 / DFIR

| 소스 | 링크 | 요약 |
|---|---|---|
| beenuar/AiSOC | github.com/beenuar/AiSOC | 오픈소스 AI SOC — 알림 융합, 퍼플팀 훈련, 에이전트 지원 triage, MITRE ATT&CK 조사, MIT 라이선스 |
| intelowlproject/IntelOwl | github.com/intelowlproject/IntelOwl | 위협 인텔리전스 대규모 관리 플랫폼 |
| "Geni AI vs AI Native SOC" (PDF) | 로컬 파일 | 제너레이티브 AI SOC와 AI-네이티브 SOC의 구조적 차이 설명 |
| "과기정통부·KISA AI 보안 레드티밍 가이드" (PDF, 69p) | discuss.pytorch.kr 링크 | AI 레드팀 구성부터 결과보고까지 국내 공식 가이드 |
| Perplexity — WAZUH SIEM 조사 | `Perplexity-WAZUH SIEM 등.md` | 오픈소스 SIEM/XDR Wazuh 개념·기능 정리 |

### 1.8 자동화·오케스트레이션 / 훈련 환경

| 소스 | 링크 | 요약 |
|---|---|---|
| JoasASantos/n8n-CyberSecurity-Workflows | github.com/JoasASantos/n8n-CyberSecurity-Workflows | n8n 기반 Red/Blue/AppSec 워크플로우 100+종 |
| JoasASantos/n8n-cybersecurity-projects | github.com/JoasASantos/n8n-cybersecurity-projects | n8n 보안 프로젝트 모음 |
| shinjaehyun20/ai-workflow-kits | github.com/shinjaehyun20/ai-workflow-kits | Codex/Claude Code/Gemini/Copilot용 즉시 사용 워크플로우 팩 |
| A-poc/RedTeam-Tools, A-poc/BlueTeam-Tools | github.com/A-poc/{RedTeam,BlueTeam}-Tools | 레드팀/블루팀 도구·기법 큐레이션 |
| yeyintminthuhtut/Awesome-Red-Teaming | github.com/yeyintminthuhtut/Awesome-Red-Teaming | 레드팀 리소스 어썸 리스트 |
| m14r41/PentestingEverything | github.com/m14r41/PentestingEverything | VAPT/AppSec/펜테스트 전 영역 가이드 |
| mandiant/commando-vm | github.com/mandiant/commando-vm | Mandiant 공식 윈도우 공격 VM 배포판 |
| ThePorgs/Exegol | github.com/ThePorgs/Exegol | 커뮤니티 주도 해킹 환경(컨테이너) |
| DevCop95/bugbounty-lab101 | github.com/DevCop95/bugbounty-lab101 | 버그바운티 실습 랩 |

### 1.9 컴플라이언스 / 정책 / 배경 리서치 (직접 구현 대상 아님, 참고자료)

| 소스 | 링크 | 요약 |
|---|---|---|
| EU Cyber Resilience Act 가이드 | cyberresilienceact.eu/ko | EU CRA 전문·가이드·무료 도구 |
| 클라우드플레어 AI 에이전트 결제 기사 | datanet.co.kr | AI 에이전트를 이용한 안전한 온라인 결제 기능 소개 |
| "정보보호 솔루션.txt" | 로컬 파일 | 국내 정보보호 산업 표준 분류 체계(EDR/DLP/SIEM/SOAR 등 78개 카테고리) — **본 문서의 분류 기준으로 활용** |
| Perplexity 리서치 5건 | `Perplexity-*.md` | HuggingFace 보안 특화 모델 비교 / 로컬 LLM(Ollama·llama.cpp) 비교 / 멀티 AI 에이전트 아키텍처·Registry 설계 / RAG 에이전트 개발 고려사항 / 파인튜닝·양자화 개념 — SeCuardian 자체 AI 인프라(오케스트레이터, 로컬 LLM 운용) 의사결정에 참고 |

그 외 직접적 보안 연관성이 낮은 범용 AI 플랫폼/인프라 자료(MetaGPT, BitFun, omg.dev, ToolJet, SmythOS,
ClaraVerse, corsair, deer-workflow, mnemory, Soup, SINQ, tech-stack-datasets, Rosetta-Prompt, hallmark,
leadita)는 "SeCuardian 자체를 만드는 데 필요한 멀티에이전트/LLM 인프라 리서치"로 분류하며 본 문서의
Addon Agent 제안 범위에서는 제외한다.

### 1.10 에이전트 런타임·오케스트레이션·엣지 LLM 인프라 (2차 추가분)

최근 추가된 링크 9건은 모두 **보안 에이전트가 아니라 에이전트 런타임/오케스트레이션/엣지-LLM 인프라**다.
신규 Addon Agent 후보(A~F)를 만들어내진 않지만, SeCuardian 자체(오케스트레이터·로컬 LLM 운용·스캐폴딩)
설계에 참고할 수 있어 별도 정리한다. 대부분 §1.9 범용 인프라 버킷의 연장이다.

| 소스 | 링크 | 요약 | SeCuardian 관련성 |
|---|---|---|---|
| truefoundry/trueforge | github.com/truefoundry/trueforge | LLM을 동작하는 에이전트로 바꾸는 오픈소스 에이전트 하네스(런타임 계층) | orchestrator 런타임 설계 참고 |
| stablyai/orca | github.com/stablyai/orca | 병렬 코딩 에이전트 플릿을 다루는 ADE(데스크톱/모바일/VPS) | 멀티에이전트 운용 UX 참고 |
| getpaseo/paseo | github.com/getpaseo/paseo | 데스크톱·모바일에서 다중 코딩 에이전트 오케스트레이션 | 멀티에이전트 오케스트레이션 참고 |
| falcons-eyes/agent-fabric-dispatch | github.com/falcons-eyes/agent-fabric-dispatch | 로컬 오픈웨이트 모델(Ollama) 우선 라우팅 + 불확실 작업만 Claude 폴백(비용 79%↓) | **LLM 라우팅·비용 최적화** — router_llm 미터링/라우팅 정책에 직접 참고 |
| HKUDS/CLI-Anything | github.com/HKUDS/CLI-Anything | 모든 소프트웨어를 에이전트-네이티브 CLI로 노출 | **CLI 래핑 패턴**(§3.1) 및 ToolProxyAgent 참고 |
| vstorm-co/full-stack-ai-agent-template | github.com/vstorm-co/full-stack-ai-agent-template | FastAPI+Next.js AI 에이전트 풀스택 템플릿(RAG·스트리밍·인증·20+ 연동) | 신규 앱형 Addon 스캐폴딩 참고(스택 일치) |
| CopilotKit/openbot | github.com/CopilotKit/openbot | 각자 컴퓨터(브라우저·파일·도구)를 가진 오픈소스 AI 코워커, AG-UI 연동 | 에이전트 UI(AG-UI) 패턴 참고 |
| RightNow-AI/picolm | github.com/RightNow-AI/picolm | 256MB RAM $10 보드에서 1B LLM 구동(엣지 LLM) | 엣지/온디바이스 LLM 운용 참고 |
| jangles-byte/Pythia | github.com/jangles-byte/Pythia | 40+ 글로벌 피드 융합 로컬 예측 시스템(Ollama, 클라우드 미사용) | 상황인식·위협인텔 융합 아이디어 참고(간접) |

> 결론: 9건 모두 **신규 보안 Addon 후보를 발생시키지 않는다.** §2 후보 목록(A~F)은 변동 없음.
> agent-fabric-dispatch(로컬 우선 LLM 라우팅)와 CLI-Anything(CLI 래핑), vstorm 풀스택 템플릿은
> 각각 §3.1 구현 패턴과 SeCuardian 오케스트레이터/스캐폴딩 설계에 실질적 참고 가치가 있다.

### 1.11 3차 추가분 (보안 훈련 레퍼런스 + 비보안 유틸)

추가 링크 5건. 1건은 보안 학습/훈련 레퍼런스, 1건은 엣지 LLM 인프라(§1.10 picolm 계열), 나머지 3건은
SeCuardian과 무관한 범용 유틸/BaaS다. **신규 보안 Addon 후보 없음(A~F 유지).**

| 소스 | 링크 | 요약 | 처리 |
|---|---|---|---|
| CarterPerez-dev/Cybersecurity-Projects | github.com/CarterPerez-dev/Cybersecurity-Projects | 초급~고급 보안 학습 프로젝트 70종(게이미피케이션) | §1.8 훈련 레퍼런스 — 신규 Addon의 QA/시험 시나리오·PoC 재료로 활용 가능 |
| drumih/turbo-fieldfare | github.com/drumih/turbo-fieldfare | M-시리즈 맥북에서 Gemma 26B를 ~2GB RAM로 추론(엣지 LLM) | §1.10 엣지/온디바이스 LLM 참고(picolm 계열) |
| SteveTheKiller/KillerPDF | github.com/SteveTheKiller/KillerPDF | 오픈소스 PDF 편집기(Windows, GPLv3) | 범위 외 — 보안 에이전트 무관 |
| Skyh-23/TeleVault | github.com/Skyh-23/TeleVault | Telegram 기반 개인 클라우드 드라이브(제로지식 AES-256) | 범위 외 — 저장/프라이버시 앱, Addon 대상 아님 |
| parse-community/parse-server | github.com/parse-community/parse-server | Node.js/Express BaaS 백엔드 | 범위 외 — 범용 BaaS 인프라 |

> 결론: 5건 모두 **신규 보안 Addon 후보를 발생시키지 않는다.** Cybersecurity-Projects는 훈련/시험 재료,
> turbo-fieldfare는 엣지 LLM 참고. 나머지 3건은 SeCuardian 범위 밖으로 제외.

### 1.12 4차 추가분 (AI SOC 레퍼런스 구현 + 공격형 스웜 + 감사 인프라)

추가 링크 5건. **이번 배치는 보안 관련성이 높다** — 그러나 신규 후보를 만들기보다 **기 구현된 `agentic-soc`
(§AGENTS.md L5)를 강화하는 참조 아키텍처**와 §2.3 공격형 거버넌스 사례다. 신규 A~F 후보 없음.

| 소스 | 링크 | 요약 | 처리 |
|---|---|---|---|
| zhadyz/AI_SOC | github.com/zhadyz/AI_SOC | 배포형 로컬 우선 AI SOC — Wazuh + Ollama LLM(Foundation-Sec-8B) + ML 트리아지(RF/XGBoost) + ChromaDB RAG, Docker Compose, **Apache-2.0** | **`agentic-soc`+`wazuh-siem`+`rag` 레퍼런스 아키텍처.** 스택이 SeCuardian 삼종과 정확히 일치 — agentic-soc 내부 구성 참고 최우선 |
| Sec-Link/Argus-Agentic-SOC-Platform | github.com/Sec-Link/Argus-Agentic-SOC-Platform | 배포형 에이전틱 SOC — 알림 수집·인시던트 조사·티켓 협업·자산 상관·워크플로 오케스트레이션·AI 분석. Next.js/Django/PostgreSQL, Docker/K8s, **Apache-2.0** | **`agentic-soc`+`shuffle-soar` 레퍼런스.** 인시던트 워크플로 UX·자산 상관 설계 참고 |
| semantica-agi/semantica | github.com/semantica-agi/semantica | 설명가능·감사가능 AI 인프라 — 지식그래프·W3C 프로버넌스·결정 추적, 규제 도메인(금융·의료·정부), Python, OSS | **`isms-p-evidence` 관련** — 에이전트 결정 로그/감사 프로버넌스 설계 참고(간접) |
| Armur-Ai/Pentest-Swarm-AI | github.com/Armur-Ai/Pentest-Swarm-AI | AI 멀티에이전트 침투테스트 스웜(공격형) | §1.2/§2.3 계열 — 격리 랩 전용·승인 거버넌스 필수. `ai-redteam` 격리 모델 준용 |
| GenDistrict/AgentDeck | github.com/GenDistrict/AgentDeck | 시큐어 에이전트 워크스페이스(프롬프트 인젝션 탐지·격리 자격증명), **폐쇄 소스(다운로드 전용)** | 범위 외(재사용 불가) — §1.6 에이전틱 AI 보안 시장 레퍼런스로만 기록 |

> 결론: 5건 모두 **신규 보안 Addon 후보를 발생시키지 않는다(A~F 유지).** 다만 AI_SOC·Argus는 기 구현
> `agentic-soc` 를 실제 배포 스택으로 구체화한 **오픈소스 참조 구현**으로, 특히 AI_SOC(Wazuh+RAG+LLM,
> Apache-2.0)는 SeCuardian 자체 스택과 일치해 agentic-soc 내부 강화 시 1순위 참고 대상이다.
> semantica는 ISMS-P 감사 프로버넌스 설계에 간접 참고. Pentest-Swarm-AI는 §2.3 거버넌스 대상, AgentDeck는 범위 외.

### 1.13 5차 추가분 (CI/CD 보안 신규 갭 + AI 인프라 다수)

추가 링크 11건. **1건은 신규 보안 갭(CI/CD 파이프라인 보안)을 드러낸다 → 신규 후보 G 제안(§2.2).**
나머지 10건은 AI/에이전트 인프라(LLM 라우팅·메모리·RAG·LLMOps·엣지 추론)와 Ops·개발툴이다.

| 소스 | 링크 | 요약 | 처리 |
|---|---|---|---|
| AdnaneKhan/gato-x | github.com/AdnaneKhan/gato-x | **GitHub Actions 공격 툴킷** — 워크플로 오설정 정적분석 + 셀프호스트 러너 탈취·시크릿 유출, Python, Apache-2.0 | **신규 보안 갭: CI/CD 파이프라인 보안.** 방어 모드(자사 워크플로 오설정 감사)로 신규 후보 **G** 제안. `truffle-scan`(시크릿)·`harbor`(레지스트리) 인접 |
| ulab-uiuc/LLMRouter | github.com/ulab-uiuc/LLMRouter | 오픈소스 LLM 라우팅 라이브러리 | **`router_llm` 참고**(agent-fabric-dispatch 계열, §1.10) |
| mikehasa/agentacct | github.com/mikehasa/agentacct | 로컬 우선 코딩 에이전트 관측(토큰·비용 추적) | `router_llm` 미터링 참고 |
| jeffhajewski/latticedb | github.com/jeffhajewski/latticedb | 임베디드 단일파일 지식그래프 DB(벡터+FTS, RAG용) | **`rag` 인프라 참고** |
| 0xK3vin/MegaMemory | github.com/0xK3vin/MegaMemory | 코딩 에이전트용 영속 지식그래프 메모리(MCP·시맨틱 검색·임베딩) | `rag`·에이전트 메모리 참고(mnemory 계열) |
| leeryong/NELLA | github.com/leeryong/NELLA | 문서→도메인 LLM 자동 구축 Agentic LLMOps(HITL, 로컬) | LLMOps·파인튜닝 참고(Perplexity 파인튜닝 리서치 연계) |
| FlashML-org/FreeToken | github.com/FlashML-org/FreeToken | 소비자 하드웨어용 엣지 MoE 추론 엔진 | 엣지 LLM 참고(picolm 계열, §1.10) |
| Tracer-Cloud/opensre | github.com/Tracer-Cloud/opensre | AI SRE 에이전트 구축 오픈소스 툴킷 | Ops(관측성) 간접 참고 |
| pixlcore/xyops | github.com/pixlcore/xyops | 워크플로 자동화 + 서버 모니터링 | `server-shell`·observability 간접 참고 |
| bloomberg/memray | github.com/bloomberg/memray | Python 메모리 프로파일러 | 범위 외(개발툴) |
| cathrynlavery/diagram-design | github.com/cathrynlavery/diagram-design | Claude Code용 다이어그램 38종(HTML+SVG) | 범위 외(문서/디자인 툴) |

> 결론: 11건 중 **gato-x 1건만 신규 보안 후보(G)를 발생**시킨다. 나머지는 SeCuardian 자체 인프라
> (LLM 라우팅·RAG·메모리·엣지·LLMOps) 참고 자료거나 범위 외다. LLMRouter/agentacct는 §3.5 자체 인프라
> 참고에 합류, latticedb/MegaMemory는 `rag` 강화, NELLA는 파인튜닝·LLMOps 의사결정 참고.

### 1.14 6차 추가분 (신규 후보 없음 — 기존 카테고리·에이전트 강화)

추가 링크 12건. **신규 보안 후보를 발생시키지 않는다(A~G 유지).** 5건은 ai-soc(기존 보안 카테고리·에이전트
강화), 7건은 orchestrator(에이전트 런타임·평가 인프라)로 분류됐다.

| 소스 | 링크 | 요약 | 버킷 · 처리 |
|---|---|---|---|
| nuver-labs/vps-audit | github.com/nuver-labs/vps-audit | Linux 서버 보안·성능 감사 경량 bash 스크립트 | **ai-soc** — 기 구현 `hardening-auditor`(E05) 강화 참고 |
| weirdmachine64/GhidraGPT | github.com/weirdmachine64/GhidraGPT | Ghidra에 LLM 통합, AI 리버스 엔지니어링 | **ai-soc** — §1.5 리버싱, 후보 D(`malware-hunt`) 인접 |
| ottosulin/awesome-ai-security | github.com/ottosulin/awesome-ai-security | AI 보안 리소스 큐레이션 목록 | **ai-soc** — §1.6 에이전틱 AI 보안 메타 레퍼런스 |
| HackUnderway/cerberus | github.com/HackUnderway/cerberus | Shodan Exploits에서 익스플로잇 추출 | **ai-soc** — §1.1/§2.3 공격형(거버넌스 대상) |
| NotAnyoneMe/ProxyChecker | github.com/NotAnyoneMe/ProxyChecker | HTTP/SOCKS 프록시 검사기(GUI) | **ai-soc** — 정찰/익명화 유틸(§1.1 인접) |
| Untrivial-ai/agent-orchestrator | github.com/Untrivial-ai/agent-orchestrator | 코딩 에이전트 플릿 관리 IDE + 계획·스폰·CI 수정 오케스트레이터 | **orchestrator** — SeCuardian orchestrator 설계 참고 |
| google/sam | github.com/google/sam | SAM Sovereign Agent Mesh | **orchestrator** — A2A/에이전트 메쉬 참고 |
| the-open-engine/zeroshot | github.com/the-open-engine/zeroshot | executor–verifier 오케스트레이션 | **orchestrator** — 실행·검증 분리 패턴 참고 |
| braintrustdata/agentbehavior | github.com/braintrustdata/agentbehavior | 에이전트 행위 정의·평가 표준 | **orchestrator** — 기 구현 `ai-eval-gate`(에이전트 평가) 참고 |
| wlsdks/ontology-atlas | github.com/wlsdks/ontology-atlas | 에이전트-네이티브 온톨로지 워크벤치(MCP, 로컬) | **orchestrator** — `rag`·에이전트 지식그래프 참고(MegaMemory 계열) |
| sandbox-quantum/switch | github.com/sandbox-quantum/switch | AI 에이전트+사람 협업 조직 플랫폼 | **orchestrator** — 에이전트 협업 UX 참고 |
| zenbu-labs/terminal-browser | github.com/zenbu-labs/terminal-browser | 터미널 내 브라우저 | **orchestrator** — 개발툴(간접) |

> 결론: 12건 모두 **신규 후보를 만들지 않는다(A~G 유지).** 다만 vps-audit는 기 구현 `hardening-auditor`,
> agentbehavior는 `ai-eval-gate`, GhidraGPT는 후보 D를 각각 강화한다. sam·agent-orchestrator·zeroshot은
> SeCuardian orchestrator/A2A 설계 참고.

### 1.15 7차 추가분 (기존 후보 A·B·C·F 대폭 강화 — 신규 후보 없음)

추가 링크 28건. **신규 후보를 만들지 않되, 기존 후보 A(공격표면)·B(에이전틱 AI 보안)·C(API 취약점)·
F(AD 보안)를 강하게 강화**한다. 17건 ai-soc, 8건 orchestrator, 3건 ai-traffic-monitor.

**ai-soc (보안, 후보 강화)**

| 소스 | 요약 | 강화 대상 |
|---|---|---|
| getagentseal/agentseal | AI 에이전트 보안 툴킷 — 위험 스킬·MCP 설정 스캔, 공급망 공격 감시, 프롬프트 인젝션 저항 테스트, **라이브 MCP 서버 tool-poisoning 감사** | **B**(에이전틱 AI 보안) — 런타임/설정 스캔 관점 추가 |
| AISecurityLab/hackagent | AI 에이전트 취약점 탐지 오픈소스 툴킷 | **B** |
| owasp-noir/noir | 코드에서 엔드포인트 탐지·Shadow API 노출·공격표면 매핑 | **A**+**C**(Shadow API 발견) |
| six2dez/burp-ai-agent | Burp 확장 — MCP 툴링·AI 분석·수동/능동 스캔 | **C**(웹/API 취약점) |
| scholarly360/owasp-top10-web-skills | OWASP Top10 2025 에이전트 스킬 | **C** |
| vulnersCom/nmap-vulners | nmap 서비스스캔→CVE/CVSS/exploit 매핑 | **A**+**E**(CVE) |
| NetSPI/AD-PathFinder | AD·ADCS·SCCM·MSSQL 공격경로 매핑(BloodHound CE) | **F**(AD 보안) |
| Shad0w-ops/H.I.V.E | 통합 OSINT 멀티툴 | **A** |
| simplifaisoul/osiris | 실시간 OSINT 대시보드(Palantir 대안) | **A** |
| danielmiessler/SecLists | 보안 워드리스트 표준 | **A**+**C** 지원 데이터 |
| Awarexone/Agentic-Bug-Hunter | AI 버그바운티 헌팅 툴킷 | **C**/§2.3 |
| Netw0rkNoob/VulnClaw | AI Agent+MCP 침투 전체 자동화 체인 | §2.3 공격형(격리 랩) |
| infosecn1nja/Red-Teaming-Toolkit | 레드팀 OST 모음 | §1.8/§2.3 |
| lgandx/Responder | LLMNR/NBT-NS/MDNS 포이즈너 | §2.3 공격형(네트워크) |
| sunblaze-ucb/cybergym-e2e | 사이버 레인지(E2E 평가) | §1.8 훈련·평가 |
| certimate-go/certimate | 셀프호스트 SSL 인증서 ACME 전주기(발급·배포·갱신·**모니터링**) 자동화 | `vault-monitor`·labca 인접 — 인증서 수명주기 감시 |
| rebugui/KISA-CIIP-2026 | 국내 주요정보통신기반시설(CIIP) 2026 대응 | `isms-p-evidence` 컴플라이언스 인접 |
| mukul975/Anthropic-Cybersecurity-Skills | Claude 보안 스킬 팩 | 레퍼런스 |

**orchestrator (인프라)**: KnockOutEZ/wigolo(로컬 검색·크롤 MCP)·MnemeHQ/mneme(아키텍처 드리프트 가드레일)·
jundot/omlx(Apple Silicon LLM 추론 서버)·kelviq/tare(토큰 감사)·rahulnyk/knowledge_graph(텍스트→KG, RAG)·
AgentOps-AI/agentops(에이전트·LLM 비용 관측)·selfishclub/privacy-build(한국법 약관 생성 스킬)·yjc-web/FlowSuite.
→ SeCuardian orchestrator/RAG/`router_llm` 참고 자료.

**ai-traffic-monitor (네트워크)**: L0p4Map(ARP+nmap 토폴로지 시각화)·netwatch(터미널 네트워크 진단)·
tailcat(Tailscale netcat). → `ai-traffic-monitor` 에이전트 네트워크 관측 참고.

> 결론: 28건 모두 **신규 후보 없음.** 다만 **B(에이전틱 AI 보안)** 는 agentseal·hackagent(+기존 AgentHound·
> Agent-Wiz·numbat·Adrian)로 근거가 매우 두터워져 **우선순위를 상(上)으로 올릴 것을 권고**한다 — SeCuardian이
> MCP/A2A 플랫폼이므로 자기 자신의 MCP·스킬·에이전트 설정을 스캔하는 B의 효용이 가장 직접적이다.
> C(API 취약점)는 owasp-noir(Shadow API)·burp-ai-agent·owasp-top10-skills 로, F(AD 보안)는 AD-PathFinder 로 보강.

**이미 구현 착수됨**: `ai-traffic-monitor/` 폴더는 자체 PRD([PRD-ai-traffic-monitor.md](./ai-traffic-monitor/PRD-ai-traffic-monitor.md))가
작성되어 있으며, 브라우저 자동연결 AI 도우미의 트래픽량을 관측하는 Addon Agent다. §3의 구현 가이드가 그대로
이 PRD의 실제 작성 사례다.

---

## 2. 분류 기반 Addon Agent 제안

기존 SeCuardian-Marketplace에는 이미 다음 13종 보안 에이전트가 있다: `agentic-soc`, `ai-eval-gate`,
`ai-redteam`, `behavior-noti`, `cilium-netpol`, `isms-p-evidence`, `neosync-dlp`, `otel-collector`,
`shuffle-soar`, `teleport-pam`, `teler-ids`, `vasca-cve`, `velociraptor-dfir` (+ 유틸리티 5종:
`ai-traffic-monitor`, `caddy-proxy`, `grafana-dashboard`, `server-shell`, `truffle-scan`).

아래는 위 인벤토리를 근거로, **기존 라인업에 없는 빈틈(gap)**을 채우는 신규 Addon Agent 후보다. 우선순위는
"SeCuardian이 방어자 관점 플랫폼"이라는 정체성과의 정합성, 구현 난이도, 거버넌스 리스크를 함께 고려했다.

### 2.1 우선순위 상(높음)

**A. `attack-surface-recon` — 외부 공격표면 정찰 에이전트**
- 근거: §1.1 OSINT/Recon 전체(spiderfoot, reconftw, FinalRecon, cariddi 등)
- 개념: 자사 도메인/서브도메인/IP를 대상으로 CLI 도구(`subfinder`/`amass`/`nmap`/`whois`/`dig` 등 이미 설치된
  것)를 안전하게 래핑해 "우리 조직이 외부에 어떻게 노출돼 있는가"를 정기 스캔·리포트한다.
- `ai-traffic-monitor`, `vasca-cve`와 유사한 "CLI 래핑 + service 타입 + 화면 없음" 패턴을 그대로 재사용 가능.
- 리스크: **자사 자산 대상으로만** 사용해야 하므로, 스캔 대상 도메인을 사전 등록(allowlist)하는 거버넌스가 필수.

**B. `agentic-threat-model` — AI 에이전트/MCP 위협 모델링 에이전트** ★근거 강화(§1.15)
- 근거: §1.6 AgentHound, Agent-Wiz, numbat, Adrian + §1.15 **agentseal**(라이브 MCP tool-poisoning 감사·
  위험 스킬/설정 스캔·프롬프트 인젝션 테스트), **hackagent**(AI 에이전트 취약점 탐지)
- 확장: 정적 위협 모델링(B) + **런타임 MCP/스킬/에이전트-설정 보안 스캔**(agentseal 계열)을 한 에이전트의
  두 모드로 설계 가능. SeCuardian 자신이 MCP/A2A 플랫폼이라 효용 최상 — **최우선 권고**.
- 개념: SeCuardian 자신을 포함해 사내에서 운용 중인 LangGraph/AutoGen/CrewAI/MCP 서버 구성을 정적으로
  스캔하고, 과도한 권한·시크릿 노출·프롬프트 인젝션 취약 지점을 위협 모델(다이어그램+표)로 출력한다.
- SeCuardian이 "에이전트 플랫폼"이자 "보안 제품"이라는 이중 정체성을 가지므로, 자기 자신의 에이전트
  생태계(orchestrator, addon-agents)를 감사하는 용도로 가장 직접적인 효용이 있다.
- 리스크: 낮음(읽기 전용 정적 분석 위주).

**C. `api-vuln-scan` — API 보안 취약점 스캐너**
- 근거: §1.3 Nettacker, BurpAPISecuritySuite, VAmPI(테스트베드로 활용)
- 개념: OWASP API Top 10 체크리스트 기반으로 등록된 내부 API 엔드포인트(OpenAPI 스펙 입력)를 점검.
  `VAmPI`를 자체 CI/QA 랩에 띄워 이 에이전트의 회귀 테스트 타깃으로 사용할 수 있다.

### 2.2 우선순위 중(보완/확장 가치 있음)

**D. `malware-hunt` — 공급망 위장 악성코드 헌팅 에이전트**
- 근거: §1.5 malwoverview, PDF "AI 개발도구 위장 악성코드 감염 헌팅가이드"
- 개념: npm/PyPI/VSCode 확장 등 개발 도구 생태계에 유포되는 위장 악성코드 지표(IOC)를 조회하고, 사내
  개발자 워크스테이션·CI 파이프라인에서 설치된 패키지를 대조한다. `truffle-scan`(시크릿 스캔)과 인접 영역이라
  같은 계열로 묶어 배포하면 좋다.

**E. `soc-intel-fusion` — 위협 인텔리전스 통합 조회 에이전트**
- 근거: §1.6 cve-mcp-server, §1.7 IntelOwl
- 개념: `vasca-cve`(자산 CVE)와 `agentic-soc`(SOC 알림)를 보완해, CVE/EPSS/CISA KEV/MITRE ATT&CK를 한 번에
  조회하는 질의응답형 에이전트. cve-mcp-server가 이미 MCP 서버 형태로 존재하므로, SeCuardian orchestrator에
  MCP 클라이언트로 연동하는 방식이 자체 개발보다 빠를 수 있다(§3.3 참고).

**F. `ad-security-scan` — Active Directory 보안 점검 에이전트**
- 근거: §1.4 ADScanPro/adscan
- 개념: 사내 AD 환경(있는 조직 한정)의 취약 설정(Kerberoasting 대상 계정, 취약 ACL 등)을 점검. `teleport-pam`과
  함께 배치하면 계정/권한 보안 영역을 완성한다.

**G. `cicd-security-scan` — CI/CD 파이프라인 보안 점검 에이전트** (신규, §1.13)
- 근거: §1.13 gato-x(GitHub Actions 공격 툴킷, Apache-2.0)
- 개념: 자사 GitHub Actions/GitLab CI 워크플로 정의를 **정적 분석**해 오설정(과도한 `pwn-request`,
  신뢰 못 할 입력의 스크립트 주입, 셀프호스트 러너 노출, OIDC 신뢰 범위 과다, 하드코딩 시크릿)을 감사·리포트한다.
- 계층: L4 데이터/공급망 인접. `truffle-scan`(시크릿)·`harbor`(레지스트리 이미지)와 함께 배치하면 **공급망/빌드
  보안** 영역을 완성한다. D(`malware-hunt`, 패키지 악성코드)와 상보적 — D는 설치 패키지, G는 빌드 파이프라인.
- 구현: gato-x의 **정적분석(enumerate) 모드만** 방어 용도로 래핑. 러너 탈취·시크릿 유출 등 공격 모드는 §2.3
  거버넌스(격리 랩·승인) 적용 또는 비활성. `ShellAgent` CLI 래핑 안전 모델 준용.
- 리스크: 중 — 자사 저장소 대상 읽기 정적분석은 낮으나, 공격 모드 포함 시 §3.2 거버넌스 필수.

### 2.3 우선순위 낮음 / 참고만

- **레드팀 자동 익스플로잇 계열**(hexstrike-ai, strix, T3MP3ST, Decepticon 등, §1.2): SeCuardian은 "가디언(방어)"
  정체성이므로, 공격 자동화 에이전트를 정식 제품으로 내장하는 것은 신중해야 한다. 굳이 채택한다면
  **승인된 내부 랩 환경 전용**(`bugbounty-lab101`, `Exegol`, `VAmPI` 같은 격리된 타깃에만 실행)으로 한정하고,
  실행 전 대상 화이트리스트 확인 + 승인 로그를 남기는 거버넌스를 필수로 붙인다.
- **커널 익스플로잇/제로데이 리서치**(DeepZero, Kernel-Exploit-Dojo, §1.5): 매우 특수한 리서치 영역이라
  Addon Agent보다는 별도 오프라인 리서치 도구로 남겨두는 편이 합리적.
- **AV/EDR 우회 프레임워크**(BOAZ_beta): 유지보수 중단 + 방어 제품 정체성과 정면으로 배치되므로 제외 권장.
- **범용 AI 인프라 자료**(MetaGPT, ClaraVerse, ToolJet 등): Addon Agent가 아니라 SeCuardian 자체 아키텍처
  (오케스트레이터/로컬 LLM 운용) 설계 시 참고 문헌으로 남겨둔다.

---

## 3. 구현 시 참고 사항

### 3.1 기존 패턴 재사용 — `ai-traffic-monitor` PRD를 템플릿으로

`ai-traffic-monitor/PRD-ai-traffic-monitor.md`는 "CLI 도구를 안전하게 래핑하는 service형 Addon Agent"를
만드는 실제 성공 사례다. 신규 에이전트(특히 A, D, F)를 만들 때 다음 구조를 그대로 따른다.

1. **배경/근거 문서 → 스코프 정의**: 무엇을 하지 않는지(Non-goals)를 먼저 명시한다.
2. **엔드포인트 표**: `GET /status`(도구 가용성) → 읽기 전용 조회 → `POST /scan` 등 특권 작업 순으로 설계.
3. **보안 모델**(`ShellAgent` 실행 안전 모델 준용):
   - 외부 프로세스 실행은 항상 `shell=False` + 내부 조립 argv. 사용자가 넘긴 문자열을 셸에 바로 넣지 않는다.
   - 실행 바이너리는 allowlist로 고정(`nmap`, `dig`, `whois` 등 명시적으로 나열).
   - 입력 검증: 도메인/인터페이스/IP는 정규식·`ipaddress` 모듈로 파싱, 정수 파라미터는 상한 클램프.
   - 경로 봉쇄: 파일 출력은 전용 디렉터리 하위 + 허용 확장자만.
   - 특권 작업(스캔 실행 등)은 `require_role`로 supervisor/admin 제한.
   - 도구 미설치·미구성 시 500이 아니라 **503 + 설치/구성 안내**로 우아하게 저하시켜, orchestrator가 502로
     오인해 중단하지 않게 한다.
4. **`from __future__ import annotations` 절대 금지** — 동적 로더(`spec_from_file_location`)가 addon
   모듈을 `sys.modules`에 등록하지 않아 pydantic이 지연 어노테이션을 못 풀어 500 오류가 난다.
5. **명명 규칙**: `{AgentName}-app.py`/`-meta.json`/`-sql.sql`(선택)/`-front.tsx`(선택), 전부 prefix 없이
   `tbl_agent_config` key와 동일하게 명명. 내장 에이전트 키와 중복 금지.
6. **worker 동봉이 필요한 경우**(예: Go/Rust로 별도 스캐너 바이너리를 만드는 경우, `VASCA_worker`/
   `BehaviorNotiService_worker` 참고): `{key}-worker-guide.md` 설치 가이드를 패키지에 내장하고 meta.json에
   `worker` 블록(`required`/`kind: bundled|external`/`guide`)을 선언한다.
7. **시험**: `test/impl/<Nth>/{scenario,result}.md`에 시나리오·결과 기록 후, `ITManually.sh`에 배치 추가.
8. **문서화**: `addon-agents/README.md`(한/영) 내장/ADDON 목록 갱신.

### 3.2 거버넌스 — 공격형 도구를 다룰 때

§2.3에서 언급한 공격 자동화 계열(레드팀 AI 에이전트)을 채택할 경우, 다음을 meta.json의 governance 필드와
실제 동작에 모두 반영한다.

- **대상 화이트리스트**: 스캔/공격 대상은 사전 등록된 자산 목록에서만 선택 가능(자유 입력 금지 또는 도메인
  소유권 검증 연동).
- **승인 이력**: 실행 전 supervisor/admin 승인 및 실행 로그(누가/언제/무엇을) 필수 기록.
- **격리 환경 우선**: 가능하면 `VAmPI`, `Exegol`, `bugbounty-lab101` 같은 통제된 랩 타깃에 먼저 적용해
  검증한 뒤 실제 자산으로 확대한다.
- **이중용도 고지**: README·UI에 "승인된 보안 테스트 목적 전용" 경고를 명시한다.

### 3.3 외부 MCP 서버 연동이 자체 구현보다 빠른 경우

`mukul975/cve-mcp-server`처럼 이미 MCP 서버로 완성된 도구는, 처음부터 `-app.py`를 새로 짜기보다
SeCuardian orchestrator의 MCP 클라이언트 기능으로 프록시하는 `ToolProxyAgent` 템플릿
(`addon-agents/zip/` 참고)을 활용하는 편이 개발 비용이 낮다. 이 경우 Addon Agent의 역할은 "프록시 설정 +
결과를 SeCuardian UI/대화 흐름에 맞게 가공"으로 축소된다.

### 3.4 분류 체계 참고

`정보보호 솔루션.txt`의 78개 국내 정보보호 산업 표준 카테고리(EDR/DLP/SIEM/SOAR/CASB 등)는 향후 신규 자료를
extra-agents/에 추가할 때 "이미 다루는 카테고리인가, 새로운 카테고리인가"를 빠르게 판단하는 체크리스트로
활용한다.

---

## 변경 이력

- 최초 작성: extra-agents/ 전체 자료(90여 건) 조사·분류, Addon Agent 후보 6종(A~F) 제안, 구현 가이드 정리.
- 2차 갱신: 신규 링크 9건(trueforge·orca·paseo·agent-fabric-dispatch·CLI-Anything·full-stack-ai-agent-template·
  openbot·picolm·Pythia) 분석. 모두 에이전트 런타임/오케스트레이션/엣지-LLM 인프라로, §1.10 신설·정리.
  신규 보안 Addon 후보는 없음(A~F 유지). agent-fabric-dispatch·CLI-Anything·풀스택 템플릿은 자체 인프라
  참고 자료로 채택.
- 3차 갱신: 신규 링크 5건(Cybersecurity-Projects·turbo-fieldfare·KillerPDF·TeleVault·parse-server) 분석,
  §1.11 신설. Cybersecurity-Projects=보안 훈련 레퍼런스, turbo-fieldfare=엣지 LLM(picolm 계열), 나머지
  3건=범위 외. 신규 보안 Addon 후보 없음(A~F 유지).
- 4차 갱신: 신규 링크 5건(AI_SOC·Argus·semantica·Pentest-Swarm-AI·AgentDeck) 분석, §1.12 신설.
  AI_SOC·Argus=`agentic-soc` 오픈소스 참조 구현(Apache-2.0), semantica=ISMS-P 감사 프로버넌스 참고,
  Pentest-Swarm-AI=§2.3 공격형 거버넌스, AgentDeck=폐쇄 소스 범위 외. 신규 보안 Addon 후보 없음(A~F 유지).
- 5차 갱신: 신규 링크 11건 분석, §1.13 신설. gato-x(GitHub Actions CI/CD 보안)로 **신규 후보 G
  `cicd-security-scan` 제안**(§2.2). 나머지 10건=AI/에이전트 인프라(LLMRouter·agentacct·latticedb·
  MegaMemory·NELLA·FreeToken·opensre·xyops)+개발툴(memray·diagram-design). 후보 목록 A~G로 확장.
- 6차 갱신: 루트 `.webloc` 125건을 `ai-soc/`(78)·`orchestrator/`(46)·`ai-traffic-monitor/`(1) 3개
  하위 폴더로 물리 분류(§1 인트로 표). 신규 링크 12건 분석, §1.14 신설. 신규 후보 없음(A~G 유지) —
  vps-audit→`hardening-auditor`, agentbehavior→`ai-eval-gate`, GhidraGPT→후보 D 강화.
- 7차 갱신(2026-09-10): 분류 **재검증** — orchestrator 오분류 17건→ai-soc, 네트워크 4건→ai-traffic-monitor,
  agentops→orchestrator, 중복 2건 제거. 최종 ai-soc 95·orchestrator 53·ai-traffic-monitor 6.
  신규 링크 28건 분석, §1.15 신설. 신규 후보 없음 — **후보 B(에이전틱 AI 보안)를 agentseal·hackagent로
  최우선 승격 권고**, C·F 보강.
