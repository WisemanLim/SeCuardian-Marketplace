<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Multiple AI Agent 플랫폼을 구축하려고 합니다. orchestrator에 의해서 관리는 agent의 형태를 다양하고 제공하고자 하는데요. 예를 들면 게시판과 같은 fe/be를 모두 가지고 있으면서 crud를 제공하는 agent와 단순히 외부의 rest api를 mcp로 변환하는 proxy 기능을 제공하는 agent입니다.

예와 같은 사례 말고 Multi AI Agent architecture를 조사하여 구성할 수 있는 orchestrator와 agent의 종류들을 상세하게 정리 및 비교 그리고 개발 가이드(방법론)까지 포함해 주세요.

여러 형태의 Agent를 하나의 플랫폼에서 제공하려면, 기본 구조는 “중앙 Orchestrator + 표준화된 Agent 계약 + 도구/에이전트 상호운용 프로토콜”로 잡는 것이 가장 안정적입니다. 특히 엔터프라이즈 환경에서는 Orchestrator가 요청 수명주기, 라우팅, 상태, 보안, 관측성, 에이전트 등록·발견을 통합 관리하고, Agent는 역할별로 분리하는 구조가 확장성과 운영성을 동시에 확보하는 방향으로 제시됩니다.[^1_1]

## 핵심 구조

Microsoft의 멀티에이전트 레퍼런스 아키텍처는 중앙 Orchestrator가 요청을 받고, 분류기(Classifier)로 의도를 판별하고, Agent Registry에서 적절한 Agent를 찾고, 필요하면 Supervisor Agent를 통해 여러 전문 Agent를 조합하는 구조를 제시합니다. 또한 지식 계층, 대화 이력, 에이전트 상태 저장소, MCP 서버를 별도 계층으로 분리해 제어 경계를 명확히 하는 것을 권장합니다.[^1_1]

질문에서 예시로 든 “CRUD형 업무 Agent”와 “외부 REST API를 MCP로 변환하는 Proxy Agent”는 모두 이 구조 안에 자연스럽게 들어갑니다. 전자는 도메인 업무를 수행하는 Task/Business Agent에 가깝고, 후자는 Integration Layer 또는 Tool Adapter 성격이 강한 Agent로 분류하는 것이 설계상 더 명확합니다.[^1_2][^1_1]

## Orchestrator 종류

멀티에이전트 오케스트레이션 패턴은 크게 라우터형, 코디네이터형, 슈퍼바이저형, 스웜형, 계층형으로 나눌 수 있습니다. Microsoft는 단일 전문 Agent로 보내는 Router Pattern, 공유 대화 스레드에서 여러 Agent가 발화하는 Group Chat Pattern, 그리고 독립 Agent를 순차·병렬로 호출하고 결과를 합성하는 Coordinator Pattern을 비교한 뒤, 실제 엔터프라이즈 운영에는 Coordinator Pattern이 재사용성과 성능 면에서 더 적합하다고 설명합니다.[^1_1]

Semantic Kernel 문서는 오케스트레이션을 순차형, 병렬형, handoff형, Magentic형으로 구분합니다. 순차형은 파이프라인 작업에 적합하고, 병렬형은 동시 분석·집계에 강하며, handoff형은 맥락에 따라 적절한 Agent로 제어권을 넘기는 데 적합하고, Magentic형은 복잡하고 개방형인 문제를 위해 전담 매니저가 다음 행동 Agent를 계속 선택하는 형태입니다.[^1_3]

LangGraph 계열에서는 supervisor와 swarm의 차이가 뚜렷합니다. supervisor 구조에서는 모든 상호작용이 감독 Agent를 중심으로 이뤄지고, swarm 구조에서는 각 Agent가 사용자와 직접 상호작용하거나 다른 Agent로 직접 handoff할 수 있어 유연하지만 제어와 거버넌스는 더 어려워집니다.[^1_4][^1_5][^1_6]


| Orchestrator 유형 | 구조 | 장점 | 단점 | 적합 사례 |
| :-- | :-- | :-- | :-- | :-- |
| Router | 요청을 한 Agent로 라우팅 [^1_1] | 단순, 빠름, 운영 쉬움 [^1_1] | 다중 Agent 협업·합성 약함 [^1_1] | FAQ, 단순 intent 분기 |
| Coordinator | 여러 Agent를 순차/병렬 호출 후 합성 [^1_1] | 엔터프라이즈 재사용성, 병렬화, 응답 합성 우수 [^1_1] | 설계 복잡도 증가 [^1_1] | 복합 업무 처리, 플랫폼형 Agent 허브 |
| Supervisor | 상위 Agent가 작업 분해·할당·검수 [^1_1][^1_7] | 제어 용이, 책임 명확, HITL 연계 쉬움 [^1_1] | 상위 Agent 병목 가능 [^1_7] | 업무 자동화, 코딩/문서 생성 |
| Hierarchical Supervisor | Supervisor 아래 팀/서브팀 배치 [^1_1][^1_6] | 조직 확장성, 도메인별 캡슐화 [^1_1] | 디버깅 경로 복잡 [^1_6] | 대규모 엔터프라이즈 Agent 플랫폼 |
| Swarm | Agent 간 peer handoff [^1_4][^1_5] | 유연함, 자연스러운 협업 [^1_4] | 거버넌스·추적·보안 난도 높음 [^1_5] | 연구형, 탐색형, 고자율 협업 |
| Group Chat | 공유 스레드에서 다자 협업 [^1_1] | 투명성, 반복 개선 [^1_1] | 컨텍스트 결합도 높고 비용 증가 [^1_1] | 리뷰, 브레인스토밍, 합의 생성 |

당신의 요구사항처럼 Agent 형태가 매우 다양한 플랫폼이라면, 기본값은 **Coordinator + Hierarchical Supervisor**가 가장 현실적입니다. 사용자 요청은 중앙 Coordinator가 받고, 도메인군별 Supervisor가 하위 Agent들을 관리하며, 일부 연구성 워크플로우에만 제한적으로 Swarm을 허용하는 식이 운영상 균형이 좋습니다.[^1_6][^1_1]

## Agent 종류

멀티에이전트 플랫폼에서 Agent는 “업무 역할” 기준과 “실행 형태” 기준으로 나눠 설계하는 것이 좋습니다. Microsoft 레퍼런스는 전문 Domain Agent, Supervisor Agent, MCP Client를 가진 Tool-connected Agent, 로컬/원격 Agent, 지식 접근 Agent를 구분하고 있으며, IBM은 Planner, Doer, Critic, Supervisor 같은 팀 역할 모델을 제시합니다.[^1_8][^1_1]

플랫폼 관점에서 실무적으로 유용한 Agent taxonomy는 아래와 같습니다. 이 분류는 질문에서 언급한 CRUD형 Agent와 Proxy형 Agent를 포함하면서, 향후 확장 가능한 포트폴리오를 만드는 데 적합합니다.[^1_9][^1_8][^1_1]


| Agent 유형 | 역할 | 예시 | 핵심 인터페이스 |
| :-- | :-- | :-- | :-- |
| UI/App Agent | FE/BE를 포함한 완결형 업무 Agent | 게시판, 결재, 고객센터, 문서관리 | 사용자 세션, CRUD API, 이벤트 발행 |
| Domain Task Agent | 특정 비즈니스 기능 수행 | 회계 정산, 특허 초안 검토, SLA 분석 | 태스크 입력/출력, 정책/룰 |
| Planner Agent | 작업 분해와 실행계획 생성 | 요구사항 → 하위 태스크 DAG | task graph, dependency metadata |
| Router/Classifier Agent | 의도 판별과 라우팅 | “이 요청은 어떤 팀이 처리?” | intent, confidence, route |
| Supervisor Agent | 하위 Agent 할당·재시도·취합 | 코드 생성팀, 리서치팀 리드 | subtask assignment, aggregation |
| Critic/Reviewer Agent | 품질 검수·환각 탐지·정책 검토 | 답변 검증, 테스트 생성 | score, issue list, approve/reject |
| Tool Proxy Agent | 외부 API를 MCP 도구로 노출 | REST → MCP 변환 | capability schema, auth, tool call |
| Remote Service Agent | 외부 네트워크 서비스형 Agent | SaaS Agent, 별도 팀 운영 Agent | A2A or HTTP endpoint |
| Knowledge/RAG Agent | 검색·인용·근거 수집 | 사내 문서 QA, 법령 검색 | retrieval query, evidence bundle |
| Execution Agent | 코드 실행·워크플로우 처리 | 배치 실행, Terraform 적용 | job spec, sandbox/runtime |
| Human-in-the-loop Agent | 사람 승인/검토 연결 | 법무 승인, 운영자 확인 | approval state, audit trail |
| Memory/Context Agent | 대화·세션·장기 상태 관리 | 사용자 선호, 작업 이력 | memory read/write, TTL |

특히 Tool Proxy Agent는 “에이전트”라기보다 “도구 적응기”에 가깝습니다. MCP는 외부 도구와 데이터 소스를 AI 애플리케이션에 표준 방식으로 연결하기 위한 프로토콜이므로, REST API를 MCP로 감싸는 경우 독립 Agent라기보다 Integration Layer의 MCP Server/Adapter 컴포넌트로 두는 편이 구조적으로 더 깔끔합니다.[^1_2][^1_1]

반대로 Agent 간 협업은 A2A가 더 적합합니다. Google은 MCP를 도구와 컨텍스트 제공을 위한 표준으로, A2A를 서로 다른 프레임워크·벤더의 Agent 간 협업 표준으로 설명하며, A2A는 capability discovery, task lifecycle, artifact 교환, 장기 실행 상태 업데이트를 지원한다고 설명합니다.[^1_10][^1_4]

## 프로토콜 비교

MCP와 A2A는 경쟁 관계가 아니라 계층이 다릅니다. MCP는 “Agent ↔ Tool/Data” 연결 표준이고, A2A는 “Agent ↔ Agent” 협업 표준이므로 둘을 함께 쓰는 설계가 현재 가장 자연스럽습니다.[^1_4][^1_2]


| 항목 | MCP | A2A |
| :-- | :-- | :-- |
| 주 목적 | 도구·데이터 소스 연결 표준 [^1_2] | Agent 간 상호운용 표준 [^1_10] |
| 기본 관계 | MCP client ↔ MCP server [^1_2] | client agent ↔ remote agent [^1_4] |
| 적합 대상 | REST API, DB, 파일, SaaS 도구 [^1_2][^1_1] | 타 팀/타 벤더/원격 Agent 협업 [^1_10] |
| 핵심 기능 | 표준화된 도구 노출, 컨텍스트 연결 [^1_2] | capability discovery, task lifecycle, artifact 교환 [^1_4] |
| 질문의 예시 적용 | “REST API를 MCP로 변환” [^1_2] | “외부 Agent와 협업” [^1_10] |

따라서 플랫폼 표준 계약은 다음처럼 이원화하는 것이 좋습니다. 내부/외부 비즈니스 기능은 MCP Tool Adapter로 표준화하고, 독립적 의사결정 주체인 Agent 서비스 간에는 A2A를 적용하는 방식입니다.[^1_4][^1_1]

## 추천 참조 아키텍처

당신의 시나리오에는 다음 8계층 구조가 가장 적합합니다. 이는 Microsoft 레퍼런스의 Orchestrator, Classifier, Registry, Knowledge Layer, State, MCP Server를 기반으로 하고, A2A를 외부 Agent federation에 추가한 형태입니다.[^1_1][^1_4]

1. Experience Layer: Web, API, Chat, Slack, CLI 등 사용자 진입점.[^1_1]
2. Central Orchestrator: 세션, 컨텍스트, 실행계획, 정책 집행, 응답 합성.[^1_1]
3. Intent/Policy Layer: 분류기, 정책 엔진, 비용·모델 선택기.[^1_1]
4. Agent Registry: Agent 메타데이터, capability, 버전, endpoint, SLA 저장.[^1_1]
5. Supervisor Layer: 도메인 그룹별 상위 관리자 Agent.[^1_1]
6. Worker Agent Layer: CRUD Agent, RAG Agent, Reviewer, Proxy, Execution Agent 등.[^1_8][^1_1]
7. Tool \& Interop Layer: MCP Server/Client, A2A Gateway, event bus, API gateway.[^1_4][^1_1]
8. State \& Observability Layer: conversation history, agent state, tracing, audit, metrics.[^1_1]

이 구조의 핵심은 “Agent를 애플리케이션처럼 등록하고, 오케스트레이터는 실행만 담당”하게 만드는 것입니다. 즉, Orchestrator는 비즈니스 구현을 품지 않고, Registry에서 capability를 보고 적절한 Agent를 선택하며, 각 Agent는 독립 배포·독립 버전업이 가능해야 플랫폼이 커져도 유지됩니다.[^1_1]

## 개발 가이드

멀티에이전트 플랫폼 개발은 처음부터 “자율성”을 크게 주기보다, 결정 가능한 부분은 결정적으로 만들고 LLM 판단은 제한된 지점에만 두는 방법이 실패 확률이 낮습니다. Microsoft도 분류기에서 NLU → SLM → LLM 순으로 비용을 올리며 확신도에 따라 라우팅하는 방식을 제안하고, 비슷한 Agent를 너무 많이 분리하지 말고 Supervisor로 그룹화하라고 권장합니다.[^1_1]

개발 방법론은 아래 순서가 적합합니다. 이 순서는 아키텍처 안정성, 운영성, 테스트 가능성을 우선하는 엔터프라이즈형 접근입니다.[^1_11][^1_3][^1_1]

1. Capability-first 설계: Agent 이름보다 “무엇을 할 수 있는가”를 먼저 정의합니다. Agent Card 또는 Registry 메타데이터에 입력 스키마, 출력 스키마, 인증 요구사항, 비용, 지연시간, 신뢰도, side effect 여부를 기록합니다. A2A는 capability discovery를 핵심으로 삼고 있으므로 이 방식이 상호운용에도 유리합니다.[^1_4][^1_1]
2. Contract-first 인터페이스: 모든 Agent에 대해 `invoke`, `plan`, `status`, `cancel`, `health`, `artifacts` 같은 공통 계약을 둡니다. 장기 실행 태스크가 있다면 A2A의 task lifecycle 개념처럼 상태 조회와 artifact 반환을 표준화하는 편이 좋습니다.[^1_4]
3. Agent 분류 기준 확정: “비즈니스 Agent”, “Tool Proxy”, “Reviewer”, “Planner”, “Supervisor”를 명확히 구분합니다. IBM이 제시한 Planner, Doer, Critic, Supervisor 역할 모델은 팀 설계 기준으로 바로 적용하기 좋습니다.[^1_8]
4. Registry 중심 운영: Agent endpoint를 코드에 하드코딩하지 말고 Registry에서 검색하게 만듭니다. Microsoft 레퍼런스는 Agent Registry를 capability lookup과 lifecycle 관리의 핵심으로 둡니다.[^1_1]
5. Workflow 패턴 표준화: 단순 요청은 Router, 복합 요청은 Coordinator, 대규모 도메인 조직은 Hierarchical Supervisor, 연구성 탐색은 제한적 Swarm으로 규칙화합니다. 패턴을 혼용하되, 어떤 요청이 어느 패턴을 타는지 운영 규칙을 명확히 해야 합니다.[^1_3][^1_6][^1_1]
6. MCP/A2A 분리 원칙: 사내 시스템·외부 SaaS·REST API는 MCP Adapter로 표준화하고, 독립 Agent 서비스끼리는 A2A로 연결합니다. 이 원칙을 지키면 “도구”와 “에이전트”의 책임이 섞이지 않습니다.[^1_2][^1_4]
7. 상태 관리 분리: 대화 이력, 사용자 컨텍스트, 에이전트 런타임 상태를 별도 저장소로 둡니다. Microsoft는 conversation history와 agent state를 별도로 유지하는 구조를 제안합니다.[^1_1]
8. 관측성과 감사 추적 내장: 각 오케스트레이션 단계에 trace id, parent task id, child task id, selected agent, cost, latency, evidence를 남깁니다. A2A와 장기 실행 태스크를 쓰면 상태 추적이 더 중요해집니다.[^1_4]
9. 품질 게이트 추가: 생성 결과는 Critic/Reviewer Agent 또는 규칙 기반 validator를 한 번 더 통과시킵니다. IBM이 Critic 역할을 환각 점검, 테스트 실행, 품질 평가에 사용한다고 설명한 점이 실무적으로 중요합니다.[^1_8]
10. Human-in-the-loop 삽입: 결재, 삭제, 배포, 고객 통신처럼 리스크 있는 행동은 승인 단계를 둡니다. Group Chat이나 Supervisor 패턴은 사람 개입 지점을 설계하기 쉽습니다.[^1_1]

## 구현 패턴 제안

당신의 플랫폼 요구를 기준으로 보면, 아래처럼 “Agent Product Line”을 정의하는 것이 좋습니다. 이렇게 하면 새로운 Agent를 추가할 때 프레임워크와 운영 정책을 재사용할 수 있습니다.[^1_9][^1_1]

- App Agent: 자체 FE/BE와 DB를 가진 완결형 업무 앱, 예: 게시판/문서관리/결재. 이 Agent는 사용자-facing product이면서 동시에 Orchestrator에 기능을 제공하는 서비스입니다.[^1_1]
- Service Agent: 특정 비즈니스 로직만 수행하는 백엔드형 Agent, 예: 요약, 비교, 분류, 규정 점검.[^1_1]
- Tool Proxy Agent: 외부 REST/GraphQL/gRPC를 MCP Server로 감싸는 적응기입니다. 엄밀히는 Tool Adapter 계층으로 두는 편이 좋습니다.[^1_2][^1_1]
- Federation Agent: 외부 조직이나 타 플랫폼의 원격 Agent와 A2A로 협업하는 게이트웨이입니다.[^1_10][^1_4]
- Governance Agent: 정책 검사, PII 마스킹, 보안 룰 검증, 응답 검수 담당입니다.[^1_1]
- Runtime Agent: 코드 실행, 워크플로우 실행, 배치 잡, DevOps 액션 수행 담당입니다.[^1_1]

이 중 게시판 같은 CRUD Agent는 단순 Worker가 아니라 “App Agent”로 취급하는 것이 좋습니다. 반면 외부 REST를 MCP로 바꾸는 기능은 “Agent”라고 부르더라도 플랫폼 내부 구현체는 사실상 “MCP Adapter + Capability Metadata”로 설계하는 편이 재사용성이 높습니다.[^1_2][^1_1]

## 프레임워크 선택 기준

LangGraph는 supervisor, swarm, handoff 같은 제어 흐름 실험과 계층형 Agent 구성이 강점입니다. AutoGen/미분류 Microsoft 계열 패턴은 MagenticOne 계열의 동적 협업과 mixture-of-agents 같은 실험적 패턴을 포함해 복합 협업 시나리오에 적합하며, Semantic Kernel은 엔터프라이즈 통합, 플러그인, 메모리, 계획 수립, 다중 언어 지원 관점에서 강점을 가집니다.[^1_12][^1_3][^1_1]

플랫폼 지향이라면 오케스트레이션 핵심은 프레임워크 종속 API가 아니라 **플랫폼 공통 계약** 위에 놓는 것이 중요합니다. 즉, 내부적으로 LangGraph든 Semantic Kernel이든 사용하더라도 Registry, Agent Card, MCP/A2A Gateway, Trace Schema는 프레임워크 중립적으로 설계해야 장기적으로 교체 비용이 낮습니다.[^1_4][^1_1]

## 권장 설계 원칙

- Agent는 “모델”이 아니라 “능력(capability)과 책임(boundary)”로 정의합니다.[^1_1]
- Orchestrator는 업무 로직을 많이 가지면 안 되고, 선택·조정·기록에 집중해야 합니다.[^1_1]
- 유사한 Agent를 과도하게 분리하면 분류와 라우팅 성능이 떨어질 수 있으므로 그룹화를 고려해야 합니다.[^1_1]
- Tool 연결은 MCP, Agent 협업은 A2A라는 원칙을 유지하면 구조가 단순해집니다.[^1_2][^1_4]
- 기본 패턴은 Coordinator/Supervisor, 예외적으로만 Swarm을 허용하는 것이 운영상 안전합니다.[^1_4][^1_1]
- 품질, 비용, 지연시간, 보안을 Agent 메타데이터에 포함해야 오케스트레이션이 실질적 의사결정을 할 수 있습니다.[^1_1]

원하시면 다음 단계로 이어서, 이 내용을 바탕으로 **Kubernetes 기반 배포 아키텍처**, **Agent Registry 스키마**, **MCP/A2A 계약 예시(JSON)**, 그리고 **Spring Boot 또는 FastAPI 기준의 실제 프로젝트 골격**까지 한국어로 설계해 드리겠습니다.
<span style="display:none">[^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30]</span>

<div align="center">⁂</div>

[^1_1]: https://devblogs.microsoft.com/ise/coordinator-patterns-multi-agent-systems/

[^1_2]: https://www.anthropic.com/news/model-context-protocol

[^1_3]: https://devblogs.microsoft.com/agent-framework/semantic-kernel-multi-agent-orchestration/

[^1_4]: https://www.youtube.com/watch?v=JeyDrn1dSUQ

[^1_5]: https://www.youtube.com/watch?v=4oC1ZKa9-Hs

[^1_6]: https://www.youtube.com/watch?v=B_0TNuYi56w

[^1_7]: https://productschool.com/blog/artificial-intelligence/multi-agent-systems

[^1_8]: https://gln75.com/en/blog/ibm-building-team-ai-agents

[^1_9]: https://www.ibm.com/new/announcements/productivity-revolution-with-ai-agents-that-work-across-stack

[^1_10]: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

[^1_11]: https://medium.com/@akankshasinha247/building-multi-agent-architectures-orchestrating-intelligent-agent-systems-46700e50250b

[^1_12]: https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/mixture-of-agents.html

[^1_13]: https://arxiv.org/html/2601.13671v1

[^1_14]: https://www.youtube.com/watch?v=cFEGlFdhDaw

[^1_15]: https://medium.com/@senol.isci/exploring-multi-agent-conversation-patterns-with-the-autogen-framework-29946f199ca5

[^1_16]: https://dev.to/futhgar/multi-agent-ai-systems-architecture-patterns-that-actually-work-107b

[^1_17]: https://medium.com/mindful-engineering/the-art-of-multi-agent-management-when-to-use-create-swarm-and-when-to-use-create-supervisor-91604232fb05

[^1_18]: https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/intro.html

[^1_19]: https://microsoft.github.io/multi-agent-reference-architecture/docs/reference-architecture/Reference-Architecture.html

[^1_20]: https://medium.com/@annie_7775/simplify-multi-agent-ai-orchestration-with-microsoft-autogen-be126e284273

[^1_21]: https://codelabs.developers.google.com/intro-a2a-purchasing-concierge

[^1_22]: https://medium.com/@vinjamurimihira/understanding-model-context-protocol-mcp-by-anthropic-a-step-towards-model-interoperability-c3ea10a82457

[^1_23]: https://docs.cloud.google.com/agent-builder/agent-engine/develop/a2a

[^1_24]: https://en.wikipedia.org/wiki/Model_Context_Protocol

[^1_25]: https://ruslanmv.com/blog/universal-a2a-agent-tutorial

[^1_26]: https://developers.googleblog.com/ko/a2a-a-new-era-of-agent-interoperability/

[^1_27]: https://humanloop.com/blog/mcp

[^1_28]: https://newsletter.systemdesign.one/p/multi-agent-system

[^1_29]: https://www.ibm.com/think/topics/agent2agent-protocol

[^1_30]: https://www.youtube.com/watch?v=Bm7dRZJ3uBc


---

# Architecture Map: 8 essential Multi-Agent roles (beyond CRUD/API proxy) and how they scale within hierarchical supervisor systems

멀티에이전트 플랫폼을 위한 Kubernetes 배포 전략
Agent Registry 구현을 위한 데이터 모델 설계

아래 3가지는 서로 분리해서 설계해야 합니다: **역할 모델**, **Kubernetes 런타임 모델**, **Registry 데이터 모델**입니다. 계층형 Supervisor 시스템에서는 Agent를 많이 만드는 것보다 “어떤 책임 단위로 묶고, 어떻게 등록·발견·스케일링할지”가 더 중요하며, Microsoft 레퍼런스도 Orchestrator가 중앙 조정자 역할을 맡고 Specialized Agent는 의미 있는 응집된 capability 단위로 구성하며, Registry는 identity·capability·status·version·metadata의 소스 오브 트루스가 되어야 한다고 설명합니다.[^2_1][^2_2]

## Architecture Map

CRUD Agent와 API Proxy를 제외하고도, 멀티에이전트 플랫폼에 거의 항상 필요한 8개 핵심 역할은 Planner, Router, Supervisor, Worker, Reviewer, Knowledge, Execution, Governance입니다. Microsoft는 Orchestrator가 상위 계획과 작업 위임을 담당하고, Specialized Agent는 단순 API 호출 같은 미세 작업이 아니라 의미 있는 capability 중심으로 구성해야 한다고 권장합니다.[^2_1]

계층형 Supervisor 구조에서는 상위 Orchestrator 아래에 Domain Supervisor를 두고, 그 아래에 역할별 Worker 군을 배치하는 방식이 가장 운영 친화적입니다. 또한 직접적인 agent-to-agent 통신은 가급적 피하고, 필요한 경우에도 결합도가 높은 Agent들은 별도 Composite Agent로 묶어 Orchestrator에 하나의 단위로 노출하는 접근이 권장됩니다.[^2_1]


| 역할 | 핵심 책임 | 상위/하위 관계 | 스케일 방식 |
| :-- | :-- | :-- | :-- |
| Planner Agent | 사용자 목표를 실행 가능한 task graph로 분해 [^2_1] | Orchestrator 또는 Domain Supervisor의 참모 역할 | CPU보다 토큰/지연시간 기준 오토스케일 |
| Router/Classifier Agent | intent 분류, route 결정, fallback 선택 [^2_3] | Orchestrator 바로 아래 | stateless Deployment로 수평 확장 |
| Supervisor Agent | 하위 Agent 선택, 재시도, 취합, 종료 판단 [^2_1][^2_4] | 계층의 관리자 | low replica 고가용성, 리더리스 API형 권장 |
| Worker/Task Agent | 실제 도메인 작업 수행 [^2_1] | Supervisor 하위 | 기능별 개별 Deployment/HPA |
| Reviewer/Critic Agent | 출력 검증, 정책/품질 평가 [^2_4] | Worker 후단의 품질 게이트 | 비동기 검수 큐 기반 확장 |
| Knowledge Agent | RAG, 벡터/그래프 검색, 근거 수집 [^2_3] | Worker 또는 Supervisor가 호출 | 캐시+retrieval pool 확장 |
| Execution Agent | 코드 실행, 배치, workflow, sandbox 액션 | Worker 특수형 | 잡 큐/Job/Argo 기반 분리 확장 |
| Governance/Security Agent | PII, 정책, 권한, 안전성 검사 [^2_5] | 전 계층 횡단 | inline admission + async audit 병행 |

이 8개 역할은 모두 독립 Agent일 필요는 없습니다. Microsoft는 지나치게 작은 단위를 Agent로 쪼개면 불필요한 복잡성이 생긴다고 설명하므로, 예를 들어 Router와 Planner를 하나의 Control Agent로 묶거나, Reviewer와 Governance를 하나의 Quality Gate Agent로 통합하는 식의 응집도 중심 설계가 더 바람직합니다.[^2_1]

## Hierarchical scaling

계층형 Supervisor 시스템에서는 “모든 Agent가 같은 방식으로 확장되지 않는다”는 점이 중요합니다. Orchestrator와 Supervisor는 상태 판단과 조정이 중요하므로 과도한 fan-out보다 안정성과 추적성이 우선이고, 반대로 Worker·Knowledge·Execution 계층은 요청량에 따라 독립적으로 수평 확장하는 구조가 적합합니다.[^2_6][^2_1]

실전에서 권장되는 계층별 확장 규칙은 다음과 같습니다. Imagine Learning 사례에서는 Orchestrator가 앞단에서 요청 유형별로 서브에이전트를 API 도구처럼 호출하고, 서브에이전트들은 각자 Kubernetes Deployment로 실행되며, 직접 서로 통신하지 않고 Orchestrator가 응답을 합성하는 구조를 사용한다고 설명합니다.[^2_6]

- Tier 0, Edge/API Layer: Ingress, API Gateway, Auth, Rate Limit을 담당하며 요청량 기준으로 확장합니다.[^2_5]
- Tier 1, Orchestrator/Supervisor: 적은 replica 수로 고가용성을 구성하고, sticky state는 외부 상태 저장소로 분리합니다.[^2_1]
- Tier 2, Domain Worker Pools: Agent 유형별 Deployment와 HPA를 둬서 개별 확장합니다.[^2_6]
- Tier 3, Heavy Runtime Pools: Execution, Retrieval, Embedding, Crawler 같은 고비용 작업은 별도 node pool이나 queue consumer로 분리합니다.[^2_5]
- Tier 4, Shared Control Plane: Registry, Observability, Policy, Memory, Event Bus는 플랫폼 공용 서비스로 둡니다.[^2_2][^2_5]

이 구조를 쓰면 상위 계층은 **coordination bottleneck**을 피하면서도 통제력을 유지하고, 하위 계층은 task 특성에 맞게 독립 확장이 가능합니다. 특히 Worker끼리 자유롭게 mesh를 만들기보다 Supervisor를 통해 흐르게 하면 trace, cost attribution, retry, approval 지점이 훨씬 명확해집니다.[^2_1][^2_6]

## Kubernetes 배포 전략

멀티에이전트 플랫폼의 Kubernetes 배포는 “에이전트를 모두 Pod에 올린다” 수준이 아니라, Control Plane과 Execution Plane을 분리하는 방향이 좋습니다. Kubernetes 상에서는 stateless Agent는 Deployment, 안정적인 ID나 저장소가 필요한 컴포넌트는 StatefulSet, 장시간 실행 태스크는 Job 또는 Workflow 계열 CRD로 분리하는 접근이 일반적입니다.[^2_7][^2_8]

권장 배치 전략은 아래와 같습니다. Kubernetes 보안 프레임워크 예시에서도 각 Agent를 개별 Deployment와 개별 ServiceAccount로 두고, 필요한 최소 권한만 부여하며, 공용 intelligence plane 접근은 mTLS와 워크로드 아이덴티티로 제어하는 방식을 제시합니다.[^2_5]

### 네임스페이스 분리

- `agent-system`: orchestrator, registry, policy, gateway 같은 제어면.[^2_5]
- `agent-domain-*`: 업무별 Agent 묶음, 예: `agent-domain-collab`, `agent-domain-devops`.
- `agent-runtime`: execution, sandbox, batch, queue consumer.
- `agent-observability`: tracing, metrics, logs, audit pipeline.


### 워크로드 타입 선택

| 컴포넌트 | Kubernetes 리소스 | 이유 |
| :-- | :-- | :-- |
| Orchestrator / Router / Supervisor | Deployment [^2_6] | stateless API 형태, 빠른 롤링업데이트 |
| Registry API | Deployment [^2_2] | DB 외부화 시 stateless 운용 가능 |
| Registry DB / graph / vector store | StatefulSet 또는 managed service [^2_7] | 안정적 저장소 필요 |
| Execution sandbox | Job / Kueue / Argo Workflow [^2_7] | 장기 실행·재시도·DAG 제어 적합 |
| Knowledge indexing | CronJob + Worker Deployment | 주기성/비동기성 |
| Event bus / queue | managed Kafka, NATS 등 | decoupling 및 backpressure [^2_5] |

### 스케일링 정책

- HPA 기준을 CPU만 쓰지 말고, QPS, queue length, 토큰 사용량, external API latency를 함께 봐야 합니다. Worker와 Retrieval Agent는 queue depth 기반 scaling이 더 적합합니다.[^2_7]
- Supervisor는 replica를 크게 늘리기보다 request state를 Redis나 DB에 두고, 여러 replica가 동일 계약으로 요청을 이어받을 수 있게 해야 합니다. Microsoft는 Orchestrator가 중앙에서 작업을 계획·위임·합성한다고 설명하므로, 로컬 메모리에 상태를 묶어두는 설계는 피하는 편이 좋습니다.[^2_1]
- GPU/NPU 의존 Agent는 taint/toleration과 node affinity로 전용 node pool에 배치하는 것이 안전합니다. Kubernetes는 pod를 Deployment 또는 StatefulSet으로 운영할 수 있고, 권한은 RBAC로 제어해야 한다는 점도 강조됩니다.[^2_8]


### 운영 권장사항

- Agent별 ServiceAccount를 분리하고 least privilege RBAC를 적용합니다.[^2_5][^2_9]
- PodDisruptionBudget으로 Orchestrator/Supervisor의 최소 가용 replica를 보장합니다.
- NetworkPolicy로 Domain Agent 간 직접 통신을 제한하고, Orchestrator 또는 Gateway 경유만 허용합니다. 이는 Microsoft가 specialized agent 간 직접 통신을 가급적 피하라고 한 권고와 일치합니다.[^2_1]
- OpenTelemetry trace id를 모든 orchestration step에 전달합니다.
- Canary 또는 blue-green 배포는 Worker부터 적용하고, Supervisor는 하위 Agent 버전 호환성을 확인한 뒤 전환합니다.

실무적으로는 “한 Agent = 한 Deployment”를 기본으로 하되, 아주 작은 기능성 Agent를 무분별하게 늘리지 않는 것이 중요합니다. 의미 있는 capability 중심으로 Agent를 묶고, 배포 단위는 런타임 격리와 확장 요구를 기준으로 나누는 편이 더 유지보수에 유리합니다.[^2_1]

## Registry 데이터 모델

Agent Registry는 단순 목록이 아니라 Orchestrator가 “누구를 왜 호출할지” 판단하는 기준 데이터 서비스여야 합니다. Microsoft는 Registry가 identity, capabilities, operational status, version, metadata tags를 중앙에서 관리하고, Orchestrator가 immediate task에 가장 적합한 Agent를 질의할 수 있게 해야 한다고 설명합니다.[^2_10][^2_2]

또한 Registry는 discovery 방식도 고려해야 합니다. Microsoft는 registry-initiated discovery와 agent-initiated self-registration 두 방식을 모두 제시하며, enterprise 환경에서는 등록 시 validation과 주기적 monitoring을 통해 정보 최신성과 uptime을 확인해야 한다고 권장합니다.[^2_2]

### 핵심 엔터티

다음 7개 엔터티를 기본으로 두는 설계를 추천합니다.

1. `agent` — Agent의 정체성과 현재 배포 표현.[^2_2]
2. `agent_version` — 계약/모델/프롬프트/런타임 버전.[^2_10]
3. `capability` — Agent가 수행 가능한 업무 단위.[^2_2]
4. `endpoint` — 호출 주소, 프로토콜, 인증 방식.[^2_2]
5. `policy_profile` — 데이터 등급, 승인 요구, 비용 한도, 지역 제한.
6. `health_status` — 가용성, 지연시간, 오류율, 최근 heartbeat.[^2_2]
7. `ownership` — 팀, 운영자, SLA, 연락 채널.[^2_2]

### 권장 논리 스키마

| 엔터티 | 주요 필드 | 설명 |
| :-- | :-- | :-- |
| agent | agent_id, name, type, role, lifecycle_state, owner_team | Registry의 기본 식별자 [^2_2] |
| agent_version | version_id, agent_id, semver, model_ref, prompt_ref, image_digest, schema_version | 실행 버전 추적 |
| capability | capability_id, agent_id, verb, domain, description, input_schema, output_schema | Orchestrator의 매칭 핵심 [^2_2] |
| endpoint | endpoint_id, agent_id, protocol, url, auth_type, auth_ref, timeout_ms | A2A/MCP/HTTP 호출 정의 [^2_2] |
| policy_profile | data_class, pii_access, action_risk, human_approval_required, region_scope, cost_budget | 거버넌스 기준 |
| health_status | serving_status, last_heartbeat_at, p95_latency_ms, error_rate, saturation, readiness | 런타임 선택 기준 [^2_2] |
| ownership | team, maintainer, oncall, docs_url, runbook_url, sla_tier | 운영 정보 |

### 추천 JSON 예시

```json
{
  "agent_id": "agent-devops-argocd",
  "name": "ArgoCDAgent",
  "type": "specialized",
  "role": ["worker", "knowledge"],
  "lifecycle_state": "active",
  "owner_team": "platform-ai",
  "tags": ["devops", "kubernetes", "argocd"],
  "capabilities": [
    {
      "capability_id": "cap-query-app-sync",
      "verb": "query",
      "domain": "argocd.application",
      "description": "Query Argo CD application sync and health status",
      "input_schema_ref": "schema://argocd/query-status-input/v1",
      "output_schema_ref": "schema://argocd/query-status-output/v1",
      "confidence_hint": 0.89
    }
  ],
  "endpoints": [
    {
      "protocol": "https",
      "url": "https://argocd-agent.agent-domain-devops.svc.cluster.local/invoke",
      "auth_type": "workload-identity",
      "timeout_ms": 12000
    }
  ],
  "policy_profile": {
    "data_class": "internal",
    "pii_access": false,
    "action_risk": "read-only",
    "human_approval_required": false,
    "region_scope": ["kr-seoul-1"]
  },
  "health_status": {
    "serving_status": "ready",
    "last_heartbeat_at": "2026-06-24T14:30:00+09:00",
    "p95_latency_ms": 850,
    "error_rate": 0.01
  },
  "ownership": {
    "team": "platform-ai",
    "maintainer": "devops-ml@company.example",
    "sla_tier": "gold"
  }
}
```

이 모델은 사람이 보는 카탈로그와 Orchestrator가 읽는 선택 데이터 둘 다 충족해야 합니다. Microsoft도 human consumption을 위해 tags, owners 같은 메타데이터가 필요하고, agent consumption을 위해 최소한 name, description, 그리고 통신 방법을 위한 url, authentication 정보가 필요하다고 설명합니다.[^2_2]

## Registry 구현 방법

Registry 구현은 중앙집중형으로 시작하고, 규모가 커지면 계층형 또는 분산형으로 확장하는 것이 안전합니다. Microsoft는 monolithic/distributed 아키텍처에 따라 Registry를 중앙형 또는 agent group별 분산형으로 둘 수 있다고 설명합니다.[^2_2]

초기 구현은 아래 방식이 가장 실용적입니다.

- 저장소: PostgreSQL + JSONB, 필요하면 OpenSearch 인덱스 보조.
- API: `POST /agents/register`, `PUT /agents/{id}/heartbeat`, `GET /agents/search`, `GET /agents/{id}`, `POST /agents/{id}/validate`.
- 등록 방식: self-register 우선, controller/observer에 의한 registry-initiated discovery 보완.[^2_2]
- 질의 방식: exact tag filter + semantic capability search 혼합.
- 검증 단계: schema validation, auth reachability, health probe, policy approval. Microsoft도 등록 시 validation step이 필요하다고 명시합니다.[^2_2]
- 모니터링: registry monitor가 주기적으로 uptime과 metadata freshness를 점검합니다.[^2_2]

규모가 커지면 Agent Card와 Capability Schema를 OCI artifact처럼 버전 관리하는 접근도 고려할 수 있습니다. AGNTCY Agent Directory Service 논문은 capability metadata와 provenance를 분리 가능한 구조, 계층적 taxonomy, 서명 기반 검증을 강조합니다.[^2_11]

## 설계 원칙

- Agent는 capability 중심으로 등록하고, “API 하나 호출” 수준의 미세 기능은 Tool로 남깁니다. Microsoft도 tiny granular task를 standalone agent로 만들지 말라고 권고합니다.[^2_1]
- Registry는 단순 주소록이 아니라 런타임 선택 엔진의 데이터 원본이어야 합니다.[^2_10][^2_2]
- Kubernetes에서는 Control Plane과 Worker Plane을 분리하고, Agent별 권한을 최소화해야 합니다.[^2_5]
- Hierarchical Supervisor 구조에서는 직접 mesh보다 Orchestrator 경유 흐름이 추적성과 통제에 유리합니다.[^2_1]
- 스케일링은 Agent 종류별로 달라야 하며, Supervisor와 Worker를 같은 HPA 정책으로 묶으면 안 됩니다.[^2_7][^2_6]

다음 단계로 바로 이어가려면, 저는 이어서 **1) Kubernetes 배포 다이어그램 수준의 참조 구조**, **2) PostgreSQL DDL 형태의 Agent Registry 스키마**, **3) Spring Boot/FastAPI 기준 Registry API 명세**까지 구체화할 수 있습니다.
<span style="display:none">[^2_12][^2_13][^2_14][^2_15][^2_16][^2_17]</span>

<div align="center">⁂</div>

[^2_1]: https://devblogs.microsoft.com/agent-framework/semantic-kernel-multi-agent-orchestration/

[^2_2]: https://arxiv.org/html/2601.13671v1

[^2_3]: https://www.linkedin.com/posts/shaheda-basha_multi-agent-reference-architecture-activity-7461619005930405888-CRTM

[^2_4]: https://devblogs.microsoft.com/ise/multi-agent-systems-at-scale/

[^2_5]: https://dev.to/gde/building-a-multi-agent-security-framework-for-kubernetes-autonomous-detection-investigation-and-55ng

[^2_6]: https://www.buoyant.io/ai-kubernetes-episode/running-multi-agent-ai-on-kubernetes-lessons-from-imagine-learning

[^2_7]: https://fast.io/resources/multi-agent-kubernetes-orchestration/

[^2_8]: https://www.youtube.com/watch?v=lOYE2w1ykus

[^2_9]: https://collabnix.com/agentic-ai-on-kubernetes-advanced-orchestration-deployment-and-scaling-strategies-for-autonomous-ai-systems/

[^2_10]: https://microsoft.github.io/multi-agent-reference-architecture/docs/building-blocks/Building-Blocks.html

[^2_11]: https://www.arxiv.org/abs/2509.18787

[^2_12]: https://rotascale.com/blog/agent-watchtower-reference-architecture/

[^2_13]: https://microsoft.github.io/multi-agent-reference-architecture/docs/agent-registry/Agent-Registry.html

[^2_14]: https://dev.to/leena_malhotra/the-architecture-of-multi-agent-ai-systems-explained-5440

[^2_15]: https://arxiv.org/html/2508.03095v1

[^2_16]: https://www.thepowerplatformcave.com/agent-architecture-patterns-microsoft-foundry-fabric/amp/

[^2_17]: https://www.langchain.com/blog/choosing-the-right-multi-agent-architecture


---

# Systemic failure patterns and resilience strategies for large-scale multi-agent orchestrations in production

Agent Registry를 위한 확장 가능한 데이터베이스 스키마 설계
멀티에이전트 플랫폼을 위한 동적 서비스 디스커버리 구현 가이드
계층형 에이전트 간 통신 프로토콜과 보안 메커니즘 설계

대규모 멀티에이전트 운영에서 실제 장애는 개별 모델 성능보다도 **오케스트레이션 복잡성, 디스커버리 불일치, 상태 불일치, 보안 경계 붕괴**에서 더 자주 발생합니다. 따라서 운영 설계는 “Agent를 어떻게 똑똑하게 만들까”보다 “어떻게 등록·발견·호출·검증·격리·감사할까”를 중심으로 잡아야 하며, Microsoft 레퍼런스도 동적 Agent Registry, Orchestrator 중심 통제, MCP 통합 계층, 대화/상태 저장, 감독형 협업 패턴을 핵심으로 제시합니다.[^3_1][^3_2]

## 장애 패턴

대규모 멀티에이전트 시스템의 대표 장애는 cascade failure, routing drift, coordination deadlock, context poisoning, registry staleness, cost explosion, partial completion, trust boundary leakage로 정리할 수 있습니다. Microsoft는 확장형 멀티에이전트에서 semantic routing, 동적 registry, local/remote execution, conversation-aware orchestration 같은 패턴을 제시하는데, 이는 반대로 말하면 분류 실패, 잘못된 agent 선택, 원격 agent 비가용, 문맥 누수 같은 문제가 구조적으로 자주 발생함을 시사합니다.[^3_3][^3_1]

특히 생산환경에서는 개별 Agent 실패보다 “상위 Supervisor의 잘못된 위임이 연쇄적으로 하위 Agent 호출을 늘리는 현상”이 더 치명적입니다. 공개 장애 분석과 운영 가이드들은 이를 cascade problem 또는 orchestration amplification으로 설명하며, discovery 실패·재시도 폭주·도구 호출 루프·품질 게이트 부재가 결합되면 작은 오류가 전체 응답 지연과 비용 폭증으로 커질 수 있다고 지적합니다.[^3_4][^3_5][^3_6]


| 장애 패턴 | 전형적 원인 | 운영 증상 | 완화 전략 |
| :-- | :-- | :-- | :-- |
| Cascade failure | 상위 Agent의 과도한 fan-out, 무제한 재시도 [^3_4] | 지연시간 급증, queue 적체, 비용 폭증 [^3_5] | 호출 budget, max depth, circuit breaker |
| Routing drift | intent classifier 성능 저하, registry 메타데이터 부정확 [^3_1][^3_2] | 잘못된 Agent 선택, 품질 저하 | confidence threshold, fallback route, offline eval |
| Registry staleness | heartbeat 누락, 비정상 종료, 느린 갱신 [^3_2] | 죽은 endpoint 호출, 연결 실패 | lease/TTL, active probing, stale quarantine |
| Coordination deadlock | Agent 상호 의존, 승인 대기, 상태 전이 불명확 | 완료 안 되는 long-running task | explicit state machine, timeout, compensation |
| Context poisoning | 이전 결과를 무비판적으로 후속 Agent가 신뢰 | 환각 전파, 잘못된 결정 누적 | evidence tagging, reviewer gate, trust labels |
| Partial completion | 일부 하위 Agent만 성공 | 응답 불완전, 설명 불일치 | quorum, partial artifact model, degraded response |
| Security boundary leakage | 과도한 권한, direct agent mesh, tool misuse [^3_1] | 데이터 노출, 임의 실행 | least privilege, mediated routing, signed claims |
| Cost explosion | 과도한 LLM fallback, 중복 retrieval, reviewer 중복 호출 [^3_1] | 예산 초과 | token budget, cache, adaptive orchestration |

이 중 가장 자주 놓치는 것은 **stale registry**와 **partial completion semantics**입니다. Registry에 살아 있다고 기록된 Agent가 실제로는 죽어 있거나, 여러 하위 Agent 중 2개만 성공했는데도 상위 Agent가 전체 성공으로 처리하면, 장애가 즉시 드러나지 않고 품질 저하 형태로 누적됩니다.[^3_7][^3_2]

## 복원력 전략

복원력은 단순 재시도보다 “통제된 실패”를 설계하는 것이 핵심입니다. Microsoft 패턴 문서는 semantic router with LLM fallback, dynamic registry, orchestrator-mediated communication, MCP governance layer를 제시하는데, 이 패턴들은 곧 비용 제한, fallback 경로, mediated control, 정책 기반 접근 통제가 필수임을 의미합니다.[^3_1]

실전에서 권장되는 복원력 전략은 다음과 같습니다.

- **Bounded orchestration**: 요청당 최대 hop 수, 최대 하위 task 수, 최대 토큰 예산을 둡니다. cascade를 막는 가장 강력한 장치입니다.[^3_5][^3_4]
- **Confidence-gated routing**: 저비용 classifier로 먼저 라우팅하고, 낮은 신뢰도에서만 LLM fallback을 적용합니다. Microsoft가 제시한 semantic router 패턴의 핵심 이점도 비용 절감과 정확도 유지입니다.[^3_1]
- **Lease-based liveness**: registry 엔트리에 TTL과 heartbeat lease를 두고, 만료되면 즉시 후보군에서 제외합니다. Registry monitor가 주기적으로 uptime과 정보 최신성을 확인해야 한다고 Microsoft는 설명합니다.[^3_2]
- **Supervisor isolation**: 상위 Supervisor는 하위 Agent 직접 결과를 그대로 신뢰하지 말고, reviewer 또는 policy gate를 끼워 넣습니다.[^3_1]
- **Degraded mode**: 일부 Agent 실패 시 전체 실패 대신 부분 결과와 신뢰도 표기를 반환합니다. local \& remote execution 패턴에서는 여러 Agent의 부분 응답을 Supervisor가 합성하므로, partial artifact 모델이 중요합니다.[^3_1]
- **Replayable workflow**: long-running orchestration은 이벤트 로그 기반 재생이 가능해야 합니다.
- **Idempotent tasks**: register, invoke, callback, status update는 재시도 가능하게 설계합니다.
- **Policy before tool**: MCP 호출 전 정책 검증을 강제합니다. Microsoft의 MCP integration layer는 policy 평가와 audit logging을 호출 흐름에 포함합니다.[^3_1]

운영상으로는 “성공률”보다 **per-hop latency, routing accuracy, stale lookup rate, retry amplification factor, partial completion ratio**를 보는 것이 더 중요합니다. 이 지표들이 올라가면 장애는 아직 터지지 않았더라도 구조적 취약점이 이미 생긴 것입니다.[^3_3][^3_2]

## Registry 스키마

확장 가능한 Agent Registry 스키마는 단일 테이블보다 **정체성, 버전, capability, endpoint, 보안 프로필, 상태, 디스커버리 인덱스**를 분리하는 정규화 구조가 적합합니다. Microsoft는 Registry가 name, description, url, authentication 같은 기본 통신 정보를 제공해야 하고, tags·owners 같은 human metadata와, Orchestrator가 적합한 agent를 찾기 위한 queriable 저장소 역할을 함께 수행해야 한다고 설명합니다.[^3_2]

권장 기본 엔터티는 아래와 같습니다.


| 테이블 | 목적 | 핵심 필드 |
| :-- | :-- | :-- |
| `agents` | Agent 정체성 | agent_id, name, agent_type, owner_team, lifecycle_state [^3_2] |
| `agent_versions` | 배포/계약 버전 | version_id, agent_id, semver, schema_version, image_digest |
| `agent_capabilities` | capability catalog | capability_id, agent_id, verb, domain, description, input_schema, output_schema [^3_2] |
| `agent_endpoints` | 통신 주소/프로토콜 | endpoint_id, agent_id, protocol, url, auth_mode, timeout_ms [^3_2] |
| `agent_security_profiles` | 권한/데이터 정책 | data_class, pii_scope, allowed_callers, region_scope, approval_required |
| `agent_health` | 최신 상태 스냅샷 | agent_id, serving_status, last_heartbeat_at, p95_latency_ms, error_rate |
| `agent_leases` | TTL 기반 생존성 | lease_id, agent_id, issued_at, expires_at, renewable |
| `agent_tags` | 필터/분류 | tag_key, tag_value |
| `agent_embeddings` | 의미 기반 검색 | agent_id, embedding_vector, embedding_model |
| `agent_relationships` | 계층/소속/호출 제한 | parent_agent_id, child_agent_id, relation_type |

이 구조는 정확 조회와 의미 기반 capability 검색을 분리할 수 있다는 장점이 있습니다. Registry는 listing과 filtering이 쉬워야 하고, advanced case에서는 queryable storage가 필요하다고 Microsoft가 설명하므로, 관계형 스키마와 벡터 인덱스를 병행하는 구성이 적합합니다.[^3_2]

### 권장 PostgreSQL DDL 방향

- `agents`, `agent_versions`, `agent_capabilities`, `agent_endpoints`는 정규화 테이블로 둡니다.
- `tags`, `owners`, `auth metadata`, `custom annotations`는 JSONB 보조 컬럼으로 두되, 자주 조회하는 필드는 별도 컬럼화합니다.
- capability 검색은 `tsvector`와 `pgvector`를 병행합니다.
- `agent_health`는 최신 상태만 저장하는 hot table과 시계열 이력 테이블을 분리합니다.
- `agent_leases`는 TTL/만료 중심으로 설계해 stale registry를 빠르게 식별합니다.

예시 논리 모델은 다음과 같습니다.

```sql
agents(
  agent_id uuid pk,
  name text unique,
  description text,
  agent_type text,
  lifecycle_state text,
  owner_team text,
  created_at timestamptz,
  updated_at timestamptz
);

agent_versions(
  version_id uuid pk,
  agent_id uuid fk,
  semver text,
  schema_version text,
  image_digest text,
  prompt_ref text,
  model_ref text,
  is_active boolean,
  created_at timestamptz
);

agent_capabilities(
  capability_id uuid pk,
  agent_id uuid fk,
  verb text,
  domain text,
  description text,
  input_schema jsonb,
  output_schema jsonb,
  qos jsonb
);

agent_endpoints(
  endpoint_id uuid pk,
  agent_id uuid fk,
  protocol text,
  url text,
  auth_mode text,
  auth_ref text,
  timeout_ms int,
  priority int,
  is_primary boolean
);

agent_health(
  agent_id uuid pk,
  serving_status text,
  last_heartbeat_at timestamptz,
  lease_expires_at timestamptz,
  p95_latency_ms int,
  error_rate numeric,
  load_score numeric,
  last_probe_status text
);
```

이 스키마의 포인트는 **상태와 정의를 분리**하는 것입니다. Agent의 정의는 비교적 천천히 바뀌고, health/lease는 빠르게 변하므로 같은 테이블에 섞으면 락 경합과 캐시 비효율이 커집니다.[^3_8][^3_2]

## 서비스 디스커버리

동적 서비스 디스커버리는 Kubernetes DNS만으로는 충분하지 않고, **Registry + Health Monitor + Selection Policy + Cache Invalidation**을 함께 가져가야 합니다. Microsoft는 Register, Repository, View, Monitor 네 구성요소를 갖는 Registry 모델을 제시하며, registry-initiated discovery와 self-register 둘 다 가능하다고 설명합니다.[^3_2]

실무 구현은 다음 4단계가 가장 안정적입니다.

1. **Registration**: Agent 시작 시 self-register를 수행하거나, Registry가 agent info endpoint를 probe합니다. Microsoft는 두 메커니즘을 모두 제시합니다.[^3_2]
2. **Validation**: schema compliance, endpoint reachability, auth 요구사항, 정책 준수 여부를 확인합니다. 등록 단계에 validation을 포함하는 것이 권장됩니다.[^3_2][^3_1]
3. **Lease + Health Update**: 30초 또는 60초 주기로 heartbeat를 보내고, monitor가 active probe를 병행합니다.[^3_7][^3_2]
4. **Runtime Discovery**: Orchestrator가 capability, tag, protocol, region, cost, health score로 검색하고 가장 적합한 endpoint를 선택합니다.[^3_7][^3_1]

### 추천 조회 API

- `POST /agents/register`
- `POST /agents/{id}/heartbeat`
- `POST /agents/search`
- `GET /agents/{id}`
- `GET /agents/{id}/card`
- `POST /agents/{id}/validate`
- `POST /agents/{id}/lease/renew`
- `POST /agents/{id}/deregister`


### 검색 조건 예시

```json
{
  "capabilities": ["translate", "summarize"],
  "match_mode": "all",
  "preferred_protocol": "a2a",
  "region": "ap-northeast-2",
  "max_p95_latency_ms": 2000,
  "min_health_score": 0.92,
  "caller_identity": "agent-supervisor-legal",
  "data_class": "internal"
}
```

중요한 점은 discovery 결과가 단순 주소 목록이 아니라 **선택 가능한 후보 집합**이어야 한다는 것입니다. capability 기반 검색, metadata 검색, 버전 필터링, transport 필터링 같은 방식은 A2A Registry 예시에서도 제시되며, health-based selection과 cache TTL 전략이 함께 필요하다고 설명합니다.[^3_7]

## 통신 프로토콜

계층형 에이전트 간 통신은 “무엇을 누구에게 어떻게 넘길지”를 표준화해야 합니다. Microsoft 패턴 문서는 orchestrator mediated, direct scoped protocol, pub/sub 세 가지를 보여주며, Registry는 routing preference와 통신 방식을 알려주는 역할을 해야 한다고 설명합니다.[^3_1][^3_2]

권장 프로토콜 계층은 다음처럼 나누는 것이 좋습니다.


| 계층 | 권장 프로토콜 | 용도 |
| :-- | :-- | :-- |
| Agent-to-Tool | MCP [^3_1] | 도구/API/데이터 연결, 정책 통제 |
| Agent-to-Agent sync | A2A 또는 HTTPS/gRPC + Agent Card [^3_2][^3_9] | 요청/응답형 협업 |
| Agent-to-Agent async | NATS/Kafka/SQS 스타일 pub-sub [^3_1] | 비동기 이벤트, 장기 실행 |
| Status/Control | REST webhook, callback, polling | task lifecycle |
| Identity/Trust | mTLS, JWT, workload identity | 상호 인증 |

설계 원칙은 간단합니다. **도구는 MCP**, **독립적 Agent 협업은 A2A 또는 A2A 유사 계약**, **대용량 비동기는 메시지 버스**로 분리하면 경계가 깨지지 않습니다. MCP integration layer는 정책과 audit을 중앙화하는 데 유리하고, agent-to-agent communication은 기본적으로 orchestrator mediated로 시작하되, 직접 통신은 승인된 scoped protocol에서만 허용하는 편이 안전합니다.[^3_1]

### 추천 메시지 계약

- `invoke`: 요청 실행.
- `status`: 장기 실행 상태 조회.
- `callback`: 작업 완료 통지.
- `artifact`: 결과물 메타데이터 전달.
- `cancel`: 작업 취소.
- `heartbeat`: 연결/가용성 상태 갱신.
- `handoff`: 상위 Agent가 다른 Agent에게 권한 위임.
- `attest`: caller identity와 policy claim 전달.


## 보안 메커니즘

멀티에이전트 보안은 네트워크 보안만으로 해결되지 않고, **신원, 권한, 정책, 입력 검증, 감사 추적**이 동시에 필요합니다. Microsoft의 MCP integration pattern은 tool 호출 전에 policy engine이 접근 규칙과 파라미터를 검증하고, 호출과 응답을 audit log에 남기는 구조를 명시합니다.[^3_1]

권장 보안 메커니즘은 아래와 같습니다.

- **mTLS 기본화**: Agent 간 채널 보안과 상호 인증을 보장합니다.[^3_9]
- **Workload identity + short-lived JWT**: Kubernetes ServiceAccount 또는 SPIFFE/SPIRE 기반 identity를 JWT claim으로 변환해 호출자 신원을 전달합니다.
- **Capability-scoped authorization**: “이 Agent가 누구를 호출할 수 있는가”를 capability 단위로 제한합니다.[^3_9]
- **Policy enforcement point**: Orchestrator, MCP gateway, A2A gateway에 정책 집행 지점을 둡니다.[^3_1]
- **Signed agent card / signed registry metadata**: agent metadata 위변조를 방지합니다. AGNTCY ADS는 provenance와 cryptographic signing을 중요한 속성으로 제시합니다.[^3_8]
- **Lease-based trust decay**: heartbeat가 끊긴 Agent는 자동 격리합니다.[^3_2]
- **Input/output sanitization**: prompt injection, schema poisoning, unsafe tool parameters를 필터링합니다.[^3_10]
- **Audit chain**: 누가 누구를 어떤 capability로 호출했고 어떤 artifact를 반환했는지 체인 형태로 남깁니다.[^3_1]

계층형 구조에서는 특히 **하위 Agent에 상위 권한을 넘기지 않는 것**이 중요합니다. Supervisor가 강한 권한을 갖더라도 Worker에는 최소 범위 토큰만 발급하고, 장기 작업은 위임 토큰의 TTL을 짧게 가져가야 lateral movement를 줄일 수 있습니다.[^3_11][^3_9]

## 구현 순서

가장 현실적인 구현 순서는 다음과 같습니다.

1. 중앙 Registry를 먼저 만들고, self-register + active probe를 둘 다 지원합니다.[^3_2]
2. `agents`, `capabilities`, `endpoints`, `health`, `leases` 5개 핵심 테이블부터 시작합니다.[^3_2]
3. discovery API에 capability/tag/health/region 기반 검색을 넣습니다.[^3_7]
4. Orchestrator는 registry lookup 결과를 짧게 캐시하되, lease expiry나 webhook 이벤트로 캐시를 무효화합니다.[^3_7]
5. 통신은 처음엔 orchestrator mediated HTTPS/gRPC로 시작하고, 이후에만 제한적 A2A direct channel을 엽니다.[^3_1]
6. MCP gateway와 A2A gateway 앞에 policy engine을 둡니다.[^3_9][^3_1]
7. 모든 hop에 trace id, parent task id, caller identity, capability id를 강제합니다.
8. partial completion과 degraded response 규칙을 제품 수준에서 정의합니다.

당신처럼 플랫폼 관점에서 설계한다면, 핵심은 “Agent를 늘리는 것”이 아니라 **등록-발견-검증-위임-감사**의 공통 제어면을 먼저 완성하는 것입니다. 이 제어면이 안정적이면 Agent 수가 늘어도 시스템은 커지지만, 제어면이 약하면 Agent 수가 늘수록 장애는 기하급수적으로 증폭됩니다.[^3_2][^3_1]

다음 단계로 이어서 구성할 수 있는 산출물은 3가지가 적합합니다: **PostgreSQL DDL 전체안**, **A2A/MCP 통합 Agent Card JSON 스키마**, **Kubernetes 기반 Registry + Discovery + Gateway 참조 아키텍처**입니다.
<span style="display:none">[^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_18]</span>

<div align="center">⁂</div>

[^3_1]: https://www.youtube.com/watch?v=cFEGlFdhDaw

[^3_2]: https://medium.com/@senol.isci/exploring-multi-agent-conversation-patterns-with-the-autogen-framework-29946f199ca5

[^3_3]: https://devblogs.microsoft.com/ise/multi-agent-systems-at-scale/

[^3_4]: https://dev.to/wilsonhoe/the-cascade-problem-why-your-multi-agent-system-will-break-in-production-and-the-5-patterns-that-3i5i

[^3_5]: https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production

[^3_6]: https://www.techaheadcorp.com/blog/ways-multi-agent-ai-fails-in-production/

[^3_7]: http://a2a-registry.dev/documentation/concepts/agent-discovery/

[^3_8]: https://arxiv.org/html/2509.18787v1

[^3_9]: https://datatracker.ietf.org/doc/html/draft-li-dmsc-macp-03

[^3_10]: https://mariothomas.com/whitepapers/mcp-dns-registry/

[^3_11]: https://dev.to/gde/building-a-multi-agent-security-framework-for-kubernetes-autonomous-detection-investigation-and-55ng

[^3_12]: https://microsoft.github.io/multi-agent-reference-architecture/docs/reference-architecture/Patterns.html

[^3_13]: https://arxiv.org/pdf/2505.10609.pdf

[^3_14]: https://www.linkedin.com/pulse/multi-agent-orchestration-production-playbook-reliable-nick-gupta-azcwe

[^3_15]: https://github.com/chandrakanthm/agentHub

[^3_16]: https://dl.ifip.org/db/conf/npc/npc2008/ZhengLS08.pdf

[^3_17]: https://arxiv.org/html/2503.13657v1

[^3_18]: http://a2a-registry.dev/documentation/examples/advanced/


---

# Multi-Agent Registry Blueprint

대규모 멀티에이전트 플랫폼에서는 Agent Registry를 단순 주소록이 아니라 capability 기반 discovery, schema 검증, 상태 기반 라우팅, 보안 검증의 제어면으로 설계해야 한다. Microsoft의 Multi-agent Reference Architecture는 Registry가 agent identity, metadata, status, version, tags를 중앙에서 관리하고 Orchestrator가 현재 작업에 가장 적합한 Agent를 검색하도록 설계해야 한다고 설명한다. AGNTCY ADS는 capability indexing과 content location을 분리하고, 계층형 taxonomy와 cryptographic signing을 통해 검증 가능한 discovery를 제공하는 구조를 제시한다.[^4_1][^4_2][^4_3]

## Architecture blueprint

확장형 Registry의 권장 구조는 `control API + metadata store + capability index + lease/health plane + policy plane + discovery cache`의 6계층이다. 이 구조는 정의 데이터와 동적 상태 데이터를 분리하여 stale registry, 잘못된 endpoint 선택, schema drift 같은 운영 문제를 줄이는 데 유리하다.[^4_2][^4_4][^4_1]

### Core components

| Component | Responsibility | Resilience role |
| :-- | :-- | :-- |
| Registry API | 등록, 갱신, 검색, 비활성화 처리 [^4_1] | 입력 검증, optimistic concurrency |
| Metadata store | Agent 정의, 버전, 소유자, 정책 저장 [^4_1] | 정규화된 schema, 감사 추적 |
| Capability index | capability/tag/semantic 검색 [^4_2][^4_4] | 의미 기반 fallback discovery |
| Lease \& health plane | heartbeat, TTL, probe, quarantine [^4_1] | stale endpoint 제거 |
| Policy plane | 호출자 권한, 데이터 등급, 지역 정책 [^4_1][^4_5] | 잘못된 호출 차단 |
| Discovery cache | Orchestrator의 단기 캐시 | lookup latency 절감, thundering herd 완화 |

### Schema-driven resilience

Schema-driven resilience의 핵심은 Agent를 자유 형식 JSON으로만 저장하지 않고, `identity schema`, `capability schema`, `endpoint schema`, `security schema`, `health schema`를 분리한 뒤 버전 관리하는 것이다. 이 방식은 새 Agent가 등록될 때 계약 위반을 조기에 검출하고, 런타임에서는 capability mismatch, protocol mismatch, required auth 누락을 차단하는 데 효과적이다.[^4_3][^4_5][^4_1][^4_2]

권장 검증 흐름은 다음과 같다.

1. Agent Card JSON schema 검증.[^4_5][^4_6]
2. 필수 capability와 endpoint 프로토콜 검사.[^4_6][^4_1]
3. 인증 방식과 신원 문서 확인.[^4_3][^4_5]
4. active probe로 health endpoint 및 invoke endpoint 확인.[^4_1]
5. lease 발급 후 일정 주기 heartbeat 요구.[^4_1]
6. 미갱신 또는 probe 실패 시 quarantine 전이.[^4_1]

## Failure simulator

멀티에이전트 장애 시뮬레이터는 단순 부하 테스트보다 cascade scenario를 재현하는 데 초점을 맞춰야 한다. 대표적으로 `misroute cascade`, `registry staleness`, `retry storm`, `partial completion`, `reviewer bottleneck`, `tool timeout amplification` 시나리오를 넣는 것이 좋다.[^4_7][^4_8]

### Simulation scenarios

| Scenario | Injected fault | Expected breaker behavior |
| :-- | :-- | :-- |
| Misroute cascade | Router confidence 저하로 잘못된 Worker 선택 | Supervisor가 fallback route 또는 abort 선택 |
| Registry staleness | dead endpoint가 ready로 남아 있음 | lease expiry 또는 active probe 실패로 candidate 제거 |
| Retry storm | 하위 Agent timeout + 무제한 재시도 | circuit breaker open, retry budget 소진 후 degraded response |
| Partial completion | 5개 중 2개 하위 task 실패 | quorum 정책에 따라 partial artifact 반환 |
| Reviewer bottleneck | reviewer queue 적체 | reviewer bypass 금지, async finalize 또는 SLA timeout 적용 |
| MCP timeout amplification | 느린 tool server 다중 fan-out | per-tool timeout, bulkhead, cancellation propagation |

### Circuit-breaker verification

Circuit-breaker는 Agent 단위, capability 단위, endpoint 단위로 구분해 검증하는 것이 좋다. endpoint breaker는 개별 URL 장애를 격리하고, capability breaker는 특정 종류의 작업 전체를 잠시 제한하며, supervisor breaker는 fan-out 폭주 자체를 차단한다.[^4_8][^4_7]

검증 항목은 다음이 적절하다.

- Open 조건: 최근 N회 중 실패율, p95 latency, timeout 비율 초과.
- Half-open 조건: 제한된 probe 요청만 허용.
- Recovery 조건: 연속 성공 횟수 또는 SLA 회복 확인.
- Fallback 정책: 대체 Agent, degraded response, async completion 중 하나 선택.
- Blast radius 측정: breaker가 상위 orchestration 전체 장애를 얼마나 줄였는지 계산.


## PostgreSQL DDL guide

PostgreSQL 기반 Registry는 정의 테이블과 hot-state 테이블을 분리해야 한다. Microsoft 구조에서 Registry는 metadata와 status를 모두 다루지만, 실제 구현에서는 write pattern이 완전히 다르므로 분리하지 않으면 lock 경합과 vacuum 비용이 커진다.[^4_1]

### DDL principles

- 정의 데이터와 health/lease 데이터를 분리한다.[^4_1]
- JSONB는 확장 필드에만 사용하고, 자주 조회하는 조건은 컬럼으로 승격한다.
- capability 검색은 `GIN(tsvector)`와 `pgvector`를 병행하는 것이 유리하다.[^4_4][^4_2]
- endpoint 우선순위, auth mode, region scope는 별도 컬럼으로 관리한다.
- audit과 health history는 append-only 테이블로 분리한다.


### Recommended DDL

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agents (
  agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  agent_type TEXT NOT NULL CHECK (agent_type IN ('orchestrator','supervisor','worker','reviewer','knowledge','execution','gateway','tool-proxy')),
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('draft','active','quarantined','retired')),
  owner_team TEXT NOT NULL,
  owner_contact TEXT,
  home_region TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_versions (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  semver TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  model_ref TEXT,
  prompt_ref TEXT,
  image_ref TEXT,
  is_active BOOLEAN NOT NULL DEFAULT FALSE,
  manifest JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(agent_id, semver)
);

CREATE TABLE agent_capabilities (
  capability_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  capability_key TEXT NOT NULL,
  verb TEXT NOT NULL,
  domain TEXT NOT NULL,
  description TEXT NOT NULL,
  input_schema JSONB NOT NULL,
  output_schema JSONB NOT NULL,
  qos JSONB,
  embedding VECTOR(1536),
  search_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(capability_key,'') || ' ' || coalesce(domain,'') || ' ' || coalesce(description,''))
  ) STORED,
  UNIQUE(agent_id, capability_key)
);

CREATE INDEX idx_agent_capabilities_tsv ON agent_capabilities USING GIN(search_tsv);

CREATE TABLE agent_endpoints (
  endpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  protocol TEXT NOT NULL CHECK (protocol IN ('https','grpc','a2a','mcp','nats')),
  url TEXT NOT NULL,
  auth_mode TEXT NOT NULL CHECK (auth_mode IN ('mtls','oauth2','jwt','workload-identity','none')),
  auth_ref TEXT,
  region TEXT,
  priority INT NOT NULL DEFAULT 100,
  timeout_ms INT NOT NULL DEFAULT 10000,
  concurrency_limit INT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE(agent_id, protocol, url)
);

CREATE TABLE agent_security_profiles (
  agent_id UUID PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  data_classification TEXT NOT NULL,
  pii_scope TEXT NOT NULL,
  approval_required BOOLEAN NOT NULL DEFAULT FALSE,
  allowed_callers JSONB,
  allowed_regions JSONB,
  secrets_profile JSONB,
  trust_attestation JSONB
);

CREATE TABLE agent_health_current (
  agent_id UUID PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  serving_status TEXT NOT NULL CHECK (serving_status IN ('ready','degraded','down','quarantined')),
  health_score NUMERIC(5,4) NOT NULL DEFAULT 1.0000,
  p95_latency_ms INT,
  error_rate NUMERIC(8,5),
  inflight_requests INT,
  last_heartbeat_at TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,
  last_probe_status TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_health_history (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  serving_status TEXT NOT NULL,
  health_score NUMERIC(5,4) NOT NULL,
  p95_latency_ms INT,
  error_rate NUMERIC(8,5),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_leases (
  lease_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  renewable BOOLEAN NOT NULL DEFAULT TRUE,
  lease_nonce TEXT NOT NULL,
  UNIQUE(agent_id)
);

CREATE TABLE agent_tags (
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  tag_key TEXT NOT NULL,
  tag_value TEXT NOT NULL,
  PRIMARY KEY(agent_id, tag_key, tag_value)
);

CREATE TABLE agent_relationships (
  parent_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  child_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('supervises','reviews','fallback-for','depends-on','owns-tool')),
  PRIMARY KEY(parent_agent_id, child_agent_id, relation_type)
);

CREATE TABLE discovery_audit_log (
  id BIGSERIAL PRIMARY KEY,
  caller_agent_id UUID,
  query JSONB NOT NULL,
  matched_agents JSONB NOT NULL,
  decision_reason JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```


### Scaling notes

파티셔닝이 필요한 첫 후보는 `agent_health_history`와 `discovery_audit_log`이다. 둘은 쓰기량이 크고 기간 기반 보존 정책이 잘 맞기 때문에 월 단위 range partition이 적합하다. capability가 수십만 건 이상으로 늘어나면 `agent_capabilities`를 domain 단위로 샤딩하거나 읽기 전용 검색 인덱스를 별도 서비스로 분리하는 편이 안전하다.[^4_2][^4_4]

## Standard Agent Card JSON schema

표준 Agent Card는 A2A와 MCP 양쪽을 포괄해야 하므로 `identity`, `capabilities`, `endpoints`, `security`, `interaction`, `tools/mcp`, `artifacts`, `governance` 블록으로 나누는 것이 좋다. A2A discovery 문서는 agent card 기반 discovery를 전제로 하며, MCP는 tools, resources, prompts 같은 노출 객체와 인증 메커니즘이 중요하다.[^4_5][^4_6]

### Required sections

| Section | Purpose |
| :-- | :-- |
| `identity` | agent 고유 식별자, 이름, 소유 조직 |
| `version` | card schema와 agent 구현 버전 |
| `capabilities` | 수행 가능한 작업 단위, 입출력 schema |
| `endpoints` | A2A, HTTPS, gRPC, MCP endpoint 목록 |
| `security` | auth 방식, mTLS/OAuth/JWT, trust claims |
| `interaction` | sync/async, callback, streaming 지원 여부 |
| `mcp` | tools/resources/prompts 노출 정보 |
| `governance` | data class, approval, audit, policy labels |
| `observability` | health, metrics, trace propagation 규칙 |

### JSON Schema outline

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/agent-card.schema.json",
  "title": "Agent Card",
  "type": "object",
  "required": ["identity", "version", "capabilities", "endpoints", "security"],
  "properties": {
    "identity": {
      "type": "object",
      "required": ["agent_id", "name", "organization"],
      "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "organization": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}}
      }
    },
    "version": {
      "type": "object",
      "required": ["card_schema_version", "agent_version"],
      "properties": {
        "card_schema_version": {"type": "string"},
        "agent_version": {"type": "string"},
        "model_ref": {"type": "string"}
      }
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["key", "verb", "domain", "input_schema", "output_schema"],
        "properties": {
          "key": {"type": "string"},
          "verb": {"type": "string"},
          "domain": {"type": "string"},
          "description": {"type": "string"},
          "input_schema": {"type": "object"},
          "output_schema": {"type": "object"},
          "qos": {"type": "object"}
        }
      }
    },
    "endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["protocol", "url", "auth_mode"],
        "properties": {
          "protocol": {"enum": ["https", "grpc", "a2a", "mcp"]},
          "url": {"type": "string", "format": "uri"},
          "auth_mode": {"enum": ["mtls", "oauth2", "jwt", "workload-identity", "none"]},
          "timeout_ms": {"type": "integer"},
          "region": {"type": "string"}
        }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "mtls_required": {"type": "boolean"},
        "oauth_scopes": {"type": "array", "items": {"type": "string"}},
        "signed_attestation": {"type": "string"},
        "allowed_callers": {"type": "array", "items": {"type": "string"}}
      }
    },
    "interaction": {
      "type": "object",
      "properties": {
        "supports_sync": {"type": "boolean"},
        "supports_async": {"type": "boolean"},
        "supports_streaming": {"type": "boolean"},
        "callback_url": {"type": "string", "format": "uri"}
      }
    },
    "mcp": {
      "type": "object",
      "properties": {
        "tools": {"type": "array", "items": {"type": "object"}},
        "resources": {"type": "array", "items": {"type": "object"}},
        "prompts": {"type": "array", "items": {"type": "object"}}
      }
    },
    "governance": {
      "type": "object",
      "properties": {
        "data_classification": {"type": "string"},
        "human_approval_required": {"type": "boolean"},
        "audit_level": {"type": "string"}
      }
    }
  }
}
```


### Example Agent Card

```json
{
  "identity": {
    "agent_id": "agent-legal-reviewer-01",
    "name": "LegalReviewSupervisor",
    "organization": "example-corp",
    "description": "Supervises legal analysis, clause extraction, and compliance review tasks",
    "tags": ["legal", "review", "supervisor"]
  },
  "version": {
    "card_schema_version": "1.0.0",
    "agent_version": "2.3.1",
    "model_ref": "gpt-5-class"
  },
  "capabilities": [
    {
      "key": "contract-risk-review",
      "verb": "review",
      "domain": "legal.contract",
      "description": "Assess contractual clauses and produce structured risk findings",
      "input_schema": {"type": "object"},
      "output_schema": {"type": "object"},
      "qos": {"max_latency_ms": 8000, "supports_async": true}
    }
  ],
  "endpoints": [
    {
      "protocol": "a2a",
      "url": "https://legal-review.example.com/a2a",
      "auth_mode": "mtls",
      "timeout_ms": 10000,
      "region": "ap-northeast-2"
    },
    {
      "protocol": "mcp",
      "url": "https://legal-review.example.com/mcp",
      "auth_mode": "oauth2",
      "timeout_ms": 10000,
      "region": "ap-northeast-2"
    }
  ],
  "security": {
    "mtls_required": true,
    "oauth_scopes": ["agent.invoke", "agent.read"],
    "signed_attestation": "sigstore://bundle/example",
    "allowed_callers": ["agent-orchestrator-core", "agent-supervisor-legal"]
  },
  "interaction": {
    "supports_sync": true,
    "supports_async": true,
    "supports_streaming": false,
    "callback_url": "https://legal-review.example.com/callback"
  },
  "mcp": {
    "tools": [
      {"name": "search_clause_library", "description": "Search internal clause library"}
    ],
    "resources": [
      {"name": "policy_manual", "uri": "resource://policy-manual"}
    ],
    "prompts": [
      {"name": "risk_review_system", "description": "Standard legal review prompt"}
    ]
  },
  "governance": {
    "data_classification": "confidential",
    "human_approval_required": true,
    "audit_level": "full"
  }
}
```


## Implementation recommendations

초기 단계에서는 중앙 PostgreSQL Registry로 시작하되, capability 규모와 조직 경계가 커지면 AGNTCY ADS 같은 content-addressed 또는 federation-friendly 모델을 참고해 계층형 디렉터리로 확장하는 것이 현실적이다. 또한 A2A discovery와 MCP metadata를 하나의 Agent Card로 통합하더라도, 런타임 transport와 정책 집행은 gateway 계층에서 분리하는 편이 운영상 안전하다.[^4_9][^4_6][^4_2][^4_3][^4_5]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18]</span>

<div align="center">⁂</div>

[^4_1]: https://microsoft.github.io/multi-agent-reference-architecture/docs/agent-registry/Agent-Registry.html

[^4_2]: https://arxiv.org/abs/2509.18787v1

[^4_3]: https://docs.agntcy.org

[^4_4]: https://arxiv.org/html/2508.03095v3

[^4_5]: https://modelcontextprotocol.io/specification/2025-11-25/basic/index

[^4_6]: https://google-a2a.github.io/A2A/latest/topics/agent-discovery/

[^4_7]: https://devblogs.microsoft.com/ise/multi-agent-systems-at-scale/

[^4_8]: https://microsoft.github.io/multi-agent-reference-architecture/docs/reference-architecture/Patterns.html

[^4_9]: https://datatracker.ietf.org/doc/html/draft-mp-agntcy-ads-00

[^4_10]: https://www.webfuse.com/mcp-cheat-sheet

[^4_11]: https://arxiv.org/html/2509.18787v1

[^4_12]: https://arxiv.org/html/2504.16902v2

[^4_13]: https://www.gradientorbit.com/post/secure-your-mcp-servers-using-oauth-2-1-part-1

[^4_14]: https://www.themoonlight.io/ko/review/the-agntcy-agent-directory-service-architecture-and-implementation

[^4_15]: https://courses.taltech.akaver.com/agentic-software-development/lectures/mcp

[^4_16]: https://huggingface.co/datasets/John6666/knowledge_base_md_for_rag_1/blob/main/hf_mcp_20251201.md

[^4_17]: https://outshift.cisco.com/blog/ai-ml/agntcy-agent-directory-find-and-publish-ai-agents

[^4_18]: https://mcp-best-practice.github.io/mcp-best-practice/best-practice/

