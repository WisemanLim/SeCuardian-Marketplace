<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# WAZUH SIEM 무엇인가

Wazuh SIEM은 오픈소스 기반으로 로그·이벤트를 중앙에서 수집·분석해 위협 탐지와 컴플라이언스를 지원하는 통합 보안 관제 플랫폼입니다.[^1_1][^1_2][^1_3]

## Wazuh SIEM 개념

- Wazuh는 XDR과 SIEM 기능을 통합한 무료 오픈소스 보안 플랫폼입니다.[^1_4][^1_5][^1_1]
- SIEM(Security Information and Event Management)은 조직 내 서버, 네트워크 장비, 애플리케이션 등에서 발생하는 보안 로그를 한곳에 모아 실시간 분석·탐지를 수행하는 시스템입니다.[^1_3]
- Wazuh SIEM은 이러한 SIEM 역할을 수행하면서 엔드포인트·클라우드 워크로드까지 포함하는 확장된 위협 탐지·대응(XDR) 기능을 동시에 제공합니다.[^1_2][^1_5][^1_1]


## 주요 기능

- 로그 수집·정규화·분석: 다양한 OS(Windows, Linux, macOS), 네트워크 장비, 클라우드 서비스, 애플리케이션에서 발생하는 이벤트를 중앙에서 수집·파싱·정규화합니다.[^1_2][^1_4][^1_3]
- 규칙 기반 탐지 및 알림: 내장 탐지 규칙과 커스텀 룰을 통해 이상 행위, 침입 시도, 악성 행위 패턴을 탐지하고 경보를 발생합니다.[^1_5][^1_1][^1_4]
- 파일 무결성 모니터링(FIM), 취약점 진단, 구성 평가, 보안 정책·규정 준수(예: PCI-DSS, HIPAA 등) 지원 기능을 포함합니다.[^1_6][^1_4]
- 엔드포인트/XDR 기능: 에이전트 기반으로 실시간 보안 데이터 수집, 행위 기반 분석, 프로세스·파일·레지스트리 감시 등을 수행해 EDR/XDR 수준의 가시성을 제공합니다.[^1_1][^1_5][^1_6]


## 아키텍처

Wazuh 플랫폼은 크게 다음 세 컴포넌트로 구성됩니다.[^1_4][^1_3]

- Wazuh Manager: 중앙 분석 서버로, 에이전트에서 전송된 로그 수집·분석, 규칙 엔진 실행, 에이전트 관리 등을 수행하는 핵심 엔진입니다.[^1_3][^1_4]
- Wazuh Indexer: Elasticsearch/OpenSearch 기반 인덱서로, 이벤트 데이터를 저장·검색·집계하는 역할을 담당합니다.[^1_4][^1_3]
- Wazuh Dashboard: Kibana 기반 웹 UI로, 시각화 대시보드, 탐지 이벤트 조회, 규칙·설정 관리 등을 제공합니다.[^1_3][^1_4]

각 서버·단말에는 Wazuh Agent를 설치해 로컬 로그를 수집하고 Manager로 전송하며, Manager와 Agent는 일반적으로 별도의 서버에 배치해 확장성과 보안성을 확보합니다.[^1_4][^1_3]

### Wazuh와 다른 SIEM 대비 특징

| 항목 | Wazuh SIEM 특징 |
| :-- | :-- |
| 라이선스 | 완전 무료 오픈소스, 커뮤니티 활성도 높음[^1_1][^1_3] |
| 기능 범위 | SIEM + XDR(EDR, FIM, 취약점, 구성 평가 등) 통합 제공[^1_1][^1_4][^1_5] |
| 아키텍처 | 에이전트 기반, ELK(OpenSearch) 스택 통합, 수평 확장 용이[^1_4][^1_3] |
| 문서·생태계 | 공식 문서 및 블로그·튜토리얼이 체계적으로 제공됨[^1_1][^1_3] |
| 사용 사례 | 온프레미스, VM, 컨테이너, 클라우드 등 다양한 환경 보호[^1_4][^1_6] |

## 엔터프라이즈 관점에서의 활용 포인트

- SOC/관제 환경에서 상용 SIEM 대비 라이선스 비용 없이 PoC·실습·중소 규모 운영에 적합합니다.[^1_7][^1_5][^1_1]
- OSSEC 기반으로 출발해 엔터프라이즈급 기능(규칙 엔진, 중앙 관리, 분산 아키텍처)을 갖추었으며, ELK/OpenSearch와 자연스럽게 통합되는 구조라 로그·보안·운영 데이터의 통합 분석이 가능합니다.[^1_8][^1_3][^1_4]
- 컴플라이언스(PCI-DSS, ISO 27001, HIPAA 등) 대응을 위한 사전 정의된 규칙·대시보드·리포트가 있어 규정 준수 및 내부감사에 활용할 수 있습니다.[^1_6][^1_4]

Wazuh를 실제로 검토하신다면, 클라우드/컨테이너 환경까지 포함한 보안 관제 아키텍처에서 어떤 역할(단독 SIEM/XDR vs 다른 솔루션과의 보조 역할)로 배치할지 고민하시는 게 가장 중요할 것 같습니다. 지금은 어떤 규모(예: 수십·수백·수천 노드) 수준의 환경에서 SIEM을 고려하고 계신가요?
<span style="display:none">[^1_10][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://wazuh.com

[^1_2]: https://wazuh.com/platform/siem/

[^1_3]: https://soy-ul.tistory.com/13

[^1_4]: https://yjshin.tistory.com/1296

[^1_5]: https://velog.io/@hosooinmymind/기타-Wazuh-완전정복-오픈소스-SIEM-XDR-플랫폼이란

[^1_6]: https://betwe.tistory.com/entry/오픈소스-보안-강력한-무료-SIEMXDR-솔루션-Wazuh와주-414-완벽-가이드-및-설치-방법

[^1_7]: https://scorchingnraining.tistory.com/195

[^1_8]: https://cloudindovi.tistory.com/entry/Security-Tools-리뷰룸-Wazuh-–-오픈소스-통합-보안-플랫폼-SIEM-EDR-CSPM을-한-번에-🛡️

[^1_9]: https://blog.naver.com/4glac/223982798970

[^1_10]: https://www.reddit.com/r/Wazuh/comments/1nylj8p/scaling_wazuh_integrations_and_evolving_it_into_a/


---

# API 명세(AST), AST?

질문 맥락상, 여기서 말씀하신 AST는 “추상 구문 트리(Abstract Syntax Tree)”를 의미할 가능성이 가장 높습니다.[^2_1][^2_2]
API 명세와 AST는 보통 “코드/스펙을 파싱해서 구조화된 트리(모델)를 만든다”는 관점에서 함께 논의됩니다.[^2_3][^2_1]

## AST(추상 구문 트리)란?

- AST는 Abstract Syntax Tree의 약자로, 소스 코드나 스펙 문서를 문법에 따라 파싱했을 때 얻어지는 **트리** 형태의 내부 표현입니다.[^2_2][^2_1]
- 문자열인 코드·명세를 파서가 토큰화(tokenize)하고 구문 분석(parse)하여, “함수, 변수, 제어문, 표현식, 타입” 등의 구조를 노드로 가지는 트리를 생성합니다.[^2_1][^2_3]

프론트엔드에서 Babel, ESLint, Prettier 등이 모두 AST를 기반으로 코드 변환·정적 분석·포매팅을 수행한다는 점이 잘 알려져 있습니다.[^2_3][^2_1]

## API 명세와 AST

“API 명세(AST)”라고 부르지는 않지만, API 스펙(예: OpenAPI/Swagger, gRPC proto, JSON Schema 등)을 파싱해서 AST/IR 형태의 구조체로 만든 뒤, 그 위에서 아래와 같은 작업을 수행합니다.[^2_1][^2_3]

- 코드 생성(Code Generation):
    - OpenAPI 스펙을 파싱해 각 엔드포인트, 파라미터, 응답 타입 등을 구조화된 트리/모델로 만든 뒤, 서버/클라이언트 스텁을 생성합니다.[^2_3][^2_1]
- 정적 분석·검증:
    - 스펙 간 일관성 체크, breaking change 탐지, 문서-코드 싱크 검증 등에 AST/IR 레벨 비교를 활용할 수 있습니다.[^2_1][^2_3]
- 리팩터링·변환:
    - 예를 들어 OpenAPI 2.0 → 3.0 변환, JSON Schema → 타입 정의(예: TypeScript, Rust struct) 변환 등에서 “명세의 AST”를 거치는 경우가 많습니다.[^2_2][^2_1]

즉, “API 명세서를 AST로 표현한다”는 개념은 일반적인 컴파일러·정적 분석기의 AST 개념을 API 스펙 도메인에 적용한 것이라 보시면 됩니다.[^2_2][^2_1]

## 컴파일러 관점에서 본 AST

AST는 전통적인 컴파일러 파이프라인에서도 핵심 중간 표현입니다.[^2_2][^2_1]

- 파싱 단계 이후, 소스 코드는 구문 구조를 반영한 AST로 바뀝니다.[^2_1]
- 이후 타입 체크, 최적화, 코드 생성 등 대부분의 컴파일러 패스는 이 AST 또는 그에서 파생된 중간 표현(IR)을 조작합니다.[^2_2][^2_1]
- 언어 서버(LS), 리팩터링 도구, 코드 완성 도구도 AST 기반으로 작동하는 경우가 많습니다.[^2_3][^2_1]

API 명세를 “도메인 특화 언어(DSL)”로 보고, 컴파일러처럼 파싱 → AST → 코드 생성/검증을 하는 구조를 설계하면, 엔터프라이즈 레벨에서 스펙 기반 개발(Contract-first, Spec-first)을 체계화하기 좋습니다.[^2_3][^2_1]

## 정리 및 활용 아이디어

- AST는 “문자열로 된 코드나 명세를 구조화된 트리로 표현한 것”이고, 이것을 기반으로 정적 분석, 코드 생성, 자동 문서화 등을 수행합니다.[^2_1][^2_2]
- API 명세에서도 동일하게, 스펙을 파싱해 AST/IR을 만든 뒤 여러 파이프라인(코드 생성, 검증, diff, 문서)를 자동화하는 아키텍처를 설계할 수 있습니다.[^2_3][^2_1]

지금 고민하시는 “API 명세(AST)”는, 예를 들어 OpenAPI·gRPC·GraphQL 스키마 같은 것을 대상으로 한 자체 AST/IR 설계 쪽에 가까운지, 아니면 프로그래밍 언어 AST와 연계해서 API 구현 코드를 분석하는 쪽에 더 가까운지 어느 쪽을 생각하고 계신가요?
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_4][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://j3sung.tistory.com/1269

[^2_2]: https://techtaek.com/초보자도-쉽게-이해하는-ast/

[^2_3]: https://yceffort.kr/2021/05/ast-for-javascript

[^2_4]: https://medicine.yonsei.ac.kr/health/encyclopedia/treat_board.do?mode=view\&articleNo=66846\&title=아스파테이트아미노전이효소

[^2_5]: https://publish.obsidian.md/lemonaa/Topics/Medical/AST

[^2_6]: https://ko.wikipedia.org/wiki/아스파르트산_%EC%95%84%EB%AF%B8%EB%85%B8%EA%B8%B0%EC%A0%84%EC%9D%B4%ED%9A%A8%EC%86%8C

[^2_7]: https://www.amc.seoul.kr/asan/mobile/healthinfo/management/managementDetail.do?managementId=108

[^2_8]: https://www.youtube.com/watch?v=BhN3VDgNU4E

[^2_9]: https://nurse-link.co.kr/community/nurse_talk/124039284

[^2_10]: https://blog.naver.com/kimge0819/222409186632

[^2_11]: https://namu.wiki/w/AST

[^2_12]: https://www.stcarollo.or.kr/0401/2069

[^2_13]: https://www.youtube.com/watch?v=5TYvzFWD5nA

[^2_14]: https://ko.wikipedia.org/wiki/AST/ALT_%EB%B9%84

[^2_15]: https://www.youtube.com/watch?v=r03ObslCNlo


---

# Keycloak SSO, HashiCorp Vault, Logto, Falco, Harbor, CrowdSec, Caddy, Cilium eBPF, teler IDS, TruffleHog, Neosync DLP, Wazuh SIEM, Shuffle SOAR, Velociraptor DFIR, Agentic SOC, AI Red Team

각 용어에 대하여 상세한 설명과 가능하다면 예제(예시)도 함께 알려주세요.

질문하신 용어들은 “클라우드‑네이티브 보안/SRE/SOC 스택”에서 서로 다른 레이어를 담당하는 핵심 오픈소스·신규 솔루션들입니다.[^3_1][^3_2][^3_3]
아래에서는 각 항목별로 개념·주요 기능·간단한 예시를 최대한 압축해서 설명하겠습니다.

***

## 1. Keycloak SSO

- Keycloak는 Red Hat이 만든 오픈소스 IAM(Identity and Access Management) 및 SSO 솔루션으로, OAuth2/OIDC, SAML 기반 인증·인가, 소셜 로그인, RBAC를 제공합니다.[^3_4][^3_5][^3_6]
- 하나의 중앙 인증 서버에서 “한 번 로그인하면 여러 서비스에 자동 로그인(SSO)”이 되도록 세션·토큰을 관리합니다.[^3_7][^3_8][^3_4]

예시:

- `myrealm`이라는 Realm을 만들고 `service-a`, `service-b`를 클라이언트로 등록한 뒤, Spring Boot 앱을 OAuth2 클라이언트로 설정하면 사용자 입장에서 한 번 Keycloak 로그인 후 두 서비스 모두 자동 접근이 가능합니다.[^3_6]

***

## 2. HashiCorp Vault

- Vault는 API 키, 비밀번호, 인증서, 암호화 키 등 “시크릿”을 중앙에서 안전하게 저장·발급·회전시키는 오픈소스 비밀 관리 솔루션입니다.[^3_9][^3_10][^3_11]
- 동적 비밀(Dynamic Secret) 발급, 정책 기반 접근 제어, 통합 인증(Kubernetes, LDAP, AWS IAM 등), 암호화 서비스(Transit) 등을 제공합니다.[^3_12][^3_2][^3_9]

예시:

- Kubernetes에서 웹앱이 DB 계정이 필요할 때 Vault에 “role=webapp-db-readonly”를 요청하면, Vault가 해당 롤에 맞는 DB 계정을 동적으로 생성해 일정 시간이 지나면 자동 폐기되도록 하는 구조를 만들 수 있습니다.[^3_12][^3_9]

***

## 3. Logto

- Logto는 개발자 친화적인 오픈소스·클라우드 기반 인증/SSO 서비스로, OIDC/OAuth2, 소셜 로그인, 멀티테넌트, B2C/B2B 인증을 제공하는 Auth0 유사 솔루션입니다.[^3_3]
- 프론트엔드·백엔드 SDK를 통해 빠르게 로그인/회원가입/SSO를 붙이고, 관리 콘솔에서 테넌트·사용자·권한을 관리합니다.[^3_3]

예시:

- React SPA와 Node.js API에 Logto SDK를 추가하고, Logto 호스티드 로그인 페이지를 사용하면 별도 인증 서버 없이도 다중 테넌트 B2B SaaS 로그인/SSO를 구현할 수 있습니다.[^3_3]

***

## 4. Falco

- Falco는 CNCF 인큐베이티드 오픈소스 런타임 보안 도구로, 리눅스 커널 시스템 호출이나 eBPF 이벤트를 분석해 컨테이너·Kubernetes·호스트 환경의 이상 행위를 실시간 탐지합니다.[^3_2][^3_13][^3_1]
- “컨테이너 안에서 쉘 실행”, `/etc/shadow` 접근, 권한 상승 패턴 등 런타임 위협 탐지를 규칙 언어로 정의하고, Slack/이메일/SIEM으로 알림을 보냅니다.[^3_13][^3_1]

예시 규칙:

- 컨테이너 내부에서 bash/sh 실행 시 알림

```yaml
- rule: Terminal shell in container
  condition: container and proc.name in (bash, zsh, sh)
```

이 규칙을 적용하면 운영 중인 Pod에서 임의 쉘이 열리면 Falco가 경고 이벤트를 생성합니다.[^3_13]

***

## 5. Harbor

- Harbor는 CNCF 졸업 프로젝트로, RBAC·이미지 서명·취약점 스캐닝·복제·감사 로그 등을 제공하는 엔터프라이즈급 컨테이너 이미지 레지스트리입니다.[^3_14][^3_15][^3_16]
- Docker Registry 위에 UI, 프로젝트 기반 권한, Notary 서명, Clair/Trivy 취약점 스캔, 정책 기반 복제를 얹어 “사설 컨테이너 레지스트리 플랫폼”을 제공합니다.[^3_15][^3_16]

예시:

- Harbor에 `prod` 프로젝트를 만들고, CI 파이프라인이 이미지를 `registry.example.com/prod/app:1.0`으로 푸시하면, 취약점 스캔 결과가 UI에 표시되고, 정책으로 “Critical 취약점 존재 시 배포 차단”을 설정할 수 있습니다.[^3_16]

***

## 6. CrowdSec

- CrowdSec은 “현대형 Fail2ban”을 지향하는 오픈소스 행동 기반 침입 방지 시스템으로, 로그를 분석해 악성 IP를 차단하고 커뮤니티 기반 블록리스트를 공유합니다.[^3_3]
- 다양한 로그 소스(Nginx, SSH, 웹앱)를 파싱하고, 시나리오 기반 탐지 후 방화벽/Bouncer를 통해 차단 액션을 수행합니다.[^3_3]

예시:

- Caddy/Nginx 로그를 CrowdSec에 연결하고 “HTTP 브루트포스 시나리오”를 활성화하면, 반복 로그인 실패 IP를 자동으로 iptables/Cloudflare 방화벽에서 차단하도록 구성할 수 있습니다.[^3_3]

***

## 7. Caddy

- Caddy는 Go로 작성된 오픈소스 웹 서버·리버스 프록시로, Let’s Encrypt 기반 HTTPS 인증서 자동 발급·갱신(자동 HTTPS) 기능으로 유명합니다.[^3_17][^3_18][^3_19]
- Caddyfile 또는 JSON 설정으로 정적 파일 서빙, 리버스 프록시, 로드밸런싱, TLS 설정 등을 간단히 구성합니다.[^3_18][^3_19]

예시 Caddyfile:

```txt
example.com {
  reverse_proxy 127.0.0.1:8080
}
```

이 정도 설정만으로도 Caddy가 `example.com`에 대한 HTTPS 인증서를 자동 발급하고, 443→8080 리버스 프록시를 구성합니다.[^3_19][^3_18]

***

## 8. Cilium eBPF

- Cilium은 eBPF 기반 CNI/네트워크·보안 플랫폼으로, Kubernetes에서 L3/L4/L7 네트워크 정책, 서비스 로드밸런싱(kube‑proxy 대체), DNS·HTTP/gRPC 레벨 필터링, Hubble/Tetragon 관측 기능을 제공합니다.[^3_20][^3_21][^3_3]
- eBPF 프로그램을 커널의 다양한 훅에 주입해 패킷·소켓·프로세스를 고성능·저오버헤드로 제어·관측합니다.[^3_22][^3_20]

예시:

- Cilium을 CNI로 사용하면서 “L7 HTTP 정책”을 설정하여 특정 네임스페이스의 Pod가 `api.example.com`에 대해 `GET /health`만 호출 가능하게 하고, 다른 메서드는 커널 레벨에서 차단할 수 있습니다.[^3_21]

***

## 9. teler IDS

- teler IDS는 Nginx 등 웹 서버 로그를 실시간 분석해 웹 공격 패턴(SQLi/XSS/RFI 등)을 탐지하는 오픈소스 웹 로그 IDS입니다.[^3_3]
- Go로 작성되어 단일 바이너리로 동작하며, 오픈 룰셋을 통해 직접 패턴을 커스터마이즈할 수 있습니다.[^3_3]

예시:

- `access.log`를 teler에 스트리밍하면, `' OR 1=1 --` 같은 SQLi 시도, `<script>` 삽입 XSS 시도 등을 탐지해 Slack으로 알림을 보낼 수 있습니다.[^3_3]

***

## 10. TruffleHog

- TruffleHog는 Git, Docker, S3, 파일시스템, CI 로그 등 전반에서 누출된 시크릿을 탐지·검증하는 오픈소스 시크릿 스캐너입니다.[^3_23][^3_24][^3_25]
- 700~800+ 유형의 자격 증명을 식별하고, 실제로 로그인 인증을 시도해 유효한 시크릿인지 검증하며, Base64·압축파일 등 다양한 인코딩·아카이브 포맷 내부도 자동으로 디코딩해서 스캔합니다.[^3_26][^3_25]

예시:

- `trufflehog git file:///path/to/repo` 명령으로 로컬 Git 리포를 스캔하면, 과거 커밋·브랜치까지 포함해 AWS 키, Slack 토큰, DB 비밀번호 등을 찾아내고, 일부는 실제 AWS API 호출로 유효성을 확인합니다.[^3_25]

***

## 11. Neosync DLP

- Neosync는 개발·테스트용 데이터 동기화/가명화 플랫폼으로, PII/PHI 등 민감 데이터를 인식해 마스킹·가명화·서브샘플링을 수행하는 DLP/데이터 프라이버시 도구에 가깝습니다.[^3_3]
- 프로덕션 DB에서 개발 환경으로 데이터 동기화 시 개인정보를 안전하게 변환하는 워크플로우를 제공합니다.[^3_3]

예시:

- Postgres 프로덕션 DB에서 `users` 테이블을 개발용 DB로 복제하되, 이름·전화번호·이메일을 Neosync가 지정한 정책(랜덤 이름, 도메인 유지한 마스크 이메일 등)으로 변환해 개인정보 없는 테스트 데이터를 자동 생성하도록 할 수 있습니다.[^3_3]

***

## 12. Wazuh SIEM

- Wazuh는 XDR + SIEM 기능을 통합한 무료 오픈소스 보안 플랫폼으로, 서버·VM·컨테이너·클라우드 워크로드 전반의 로그를 중앙 수집·분석해 위협 탐지와 컴플라이언스를 지원합니다.[^3_27][^3_28][^3_29][^3_30]
- OSSEC 기반 HIDS에서 발전해 파일 무결성 모니터링(FIM), 취약점 진단, 구성 평가, 규정 준수 대시보드까지 포함한 통합 보안 관제 환경을 제공합니다.[^3_29][^3_30][^3_31]

예시:

- 각 서버에 Wazuh Agent를 설치하고, Wazuh Manager + Indexer + Dashboard 스택을 구성하면, SSH 로그인 실패, sudo 남용, 웹 서버 에러, 시스템 변경 이벤트 등을 한 대시보드에서 통합 모니터링·알림할 수 있습니다.[^3_31][^3_29]

***

## 13. Shuffle SOAR

- Shuffle는 오픈소스 SOAR(Security Orchestration, Automation and Response) 플랫폼으로, 보안 이벤트에 대한 플레이북 기반 자동화(티켓 생성, 알림, 차단 등)를 제공합니다.[^3_3]
- Drag‑and‑drop 워크플로우로 “SIEM 알림 → Enrichment → Slack 알림 → Jira 티켓 생성 → 방화벽 API 호출” 같은 시나리오를 구성할 수 있습니다.[^3_3]

예시:

- Wazuh에서 “고위험 탐지 이벤트”가 발생하면 Shuffle 플레이북이 이를 받아 WHOIS/IP reputation 조회 후, 결과를 정리해 Slack 알림과 Jira Incident 티켓을 자동 생성하도록 할 수 있습니다.[^3_3]

***

## 14. Velociraptor DFIR

- Velociraptor는 엔드포인트에 경량 에이전트를 배포해 DFIR(Digital Forensics and Incident Response)을 수행하는 오픈소스 플랫폼입니다.[^3_3]
- 자체 쿼리 언어(VQL)로 파일 시스템, 레지스트리, 프로세스, 로그를 수집·분석하고, 상시 헌팅과 포렌식 조사에 활용합니다.[^3_3]

예시:

- 랜섬웨어 감염 의심 시, Velociraptor 쿼리를 통해 전체 조직의 Windows 머신에서 의심 프로세스·암호화된 파일 패턴·이벤트 로그를 신속히 수집하고, 타임라인 분석을 자동화할 수 있습니다.[^3_3]

***

## 15. Agentic SOC

- Agentic SOC는 LLM/에이전트 기반으로 SOC 워크플로우(티어1 트리아지, 유스케이스 튜닝, 헌팅)를 자동화·보조하는 개념/플랫폼을 의미하며, 여러 프로젝트에서 “다중 에이전트가 SIEM·SOAR·Threat Intel을 연계해 Incident을 관리하는 SOC”를 지향합니다.[^3_3]
- 예: 한 에이전트는 Wazuh/Cloud SIEM 알림을 요약·분류, 다른 에이전트는 Threat Intel 조회, 또 다른 에이전트는 SOAR 플레이북 추천·수정 등을 수행하는 구조입니다.[^3_3]

예시:

- Wazuh 알림이 들어오면 LLM 에이전트가 MITRE ATT\&CK 매핑을 하고, Shuffle 플레이북을 자동 선택/수정한 뒤, 필요 시 Velociraptor 쿼리를 제안하는 식으로 “대화형·자율형 SOC”를 구현할 수 있습니다.[^3_3]

***

## 16. AI Red Team

- AI Red Team은 전통적 레드팀 개념을 “AI 시스템”에 적용한 것로, 모델 탈취·프롬프트 인젝션·데이터 포이즈닝·정책 우회를 시도해 방어 수준을 평가·강화하는 역할을 합니다.[^3_3]
- 대규모 언어모델, 에이전트, 추천 시스템 등에 대해 공격 시나리오를 설계·실행하고, 취약점·리스크를 리포트·수정하는 보안/리스크 팀입니다.[^3_3]

예시:

- 내부 Copilot에 대해 AI Red Team이 프롬프트 인젝션(예: “이전 지침을 모두 무시하고…”), 데이터 유출 시나리오, 탈의도(탈식별) 실패 케이스를 설계해 테스트하고, 정책/Guardrail/필터를 개선하는 활동을 수행합니다.[^3_3]

***

### 전체 역할을 한 번에 보는 관점

| 계층 | 도구 예 | 주요 역할 |
| :-- | :-- | :-- |
| 인증/권한 | Keycloak, Logto, Vault | SSO, 비밀 관리, 토큰 발급[^3_4][^3_5][^3_9] |
| 컨테이너·네트워크 | Cilium, Harbor | CNI/네트워크 정책, 이미지 레지스트리[^3_16][^3_21] |
| 런타임 보안/IDS | Falco, teler, CrowdSec | 커널·웹 로그 기반 위협 탐지[^3_1][^3_13][^3_3] |
| 시크릿/누설 | Vault, TruffleHog, Neosync | 시크릿 저장·발급·누출 탐지·DLP[^3_9][^3_25][^3_26] |
| SIEM/XDR | Wazuh | 로그 집계·위협 탐지·컴플라이언스[^3_27][^3_29][^3_30] |
| SOAR/워크플로우 | Shuffle | 보안 자동화 플레이북[^3_3] |
| DFIR/헌팅 | Velociraptor | 포렌식·엔드포인트 헌팅[^3_3] |
| 웹 인프라 | Caddy, Harbor | 웹 서버/Reverse Proxy, 레지스트리[^3_19][^3_16] |
| AI 보안 | Agentic SOC, AI Red Team | LLM 기반 SOC, AI 시스템 공격·평가[^3_3] |

이 스택 전체를 “참고 아키텍처”로 놓고, 어느 레이어부터 PoC를 해보실 계획인지(예: 네트워크/CNI vs SIEM/XDR vs SOAR/Agentic SOC)가 정해지면, 거기부터 구체적으로 설계/실습 플로우를 같이 잡아볼 수 있을 것 같습니다. 지금 가장 먼저 손대고 싶은 도구 또는 레이어는 어느 쪽이신가요?
<span style="display:none">[^3_32][^3_33][^3_34][^3_35][^3_36][^3_37][^3_38][^3_39][^3_40][^3_41][^3_42][^3_43][^3_44][^3_45][^3_46][^3_47][^3_48][^3_49][^3_50]</span>

<div align="center">⁂</div>

[^3_1]: https://wlsdn3004.tistory.com/94

[^3_2]: https://s-core.co.kr/post_cloudnative/%EC%BF%A0%EB%B2%84%EB%84%A4%ED%8B%B0%EC%8A%A4-%EB%B3%B4%EC%95%88-%ED%88%B4-%EB%9F%B0%ED%83%80%EC%9E%84-%EC%9D%B4%EB%AF%B8%EC%A7%80-%EA%B4%80%EB%A6%AC/

[^3_3]: https://www.youngju.dev/blog/cilium/2026-06-13-cilium-ebpf-datapath-architecture-2026

[^3_4]: https://idea9329.tistory.com/1721

[^3_5]: https://velog.io/@yardyard/KeyCloak으로-SSO-구현

[^3_6]: https://moonquery.tistory.com/55

[^3_7]: https://memoryhub.tistory.com/entry/SSOSingle-Sign-On-구축-😋

[^3_8]: https://memoryhub.tistory.com/entry/Keycloak-SSO-연동-방법-😋

[^3_9]: https://itpe.jackerlab.com/entry/HashiCorp-Vault

[^3_10]: https://kschoi728.tistory.com/454

[^3_11]: https://wlsdn3004.tistory.com/11

[^3_12]: https://techietalks.tistory.com/25

[^3_13]: https://velog.io/@gun_123/Monitoring-Logging-and-Runtime-Security-Kubernetes-%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EC%97%90-Falco-%EC%84%A4%EC%B9%98-%EB%B0%8F-%EC%9C%84%ED%98%91-%ED%83%90%EC%A7%80

[^3_14]: https://lab.wallarm.com/what/하버란-무엇인가/?lang=ko

[^3_15]: https://yona.xslab.co.kr/엑세스랩/HOWTO-V-Raptor-SQ-nano/post/26

[^3_16]: https://brightforest.tistory.com/94

[^3_17]: https://feccle.tistory.com/545

[^3_18]: https://blog.jhyeom.com/caddy-server

[^3_19]: https://ko.wikipedia.org/wiki/캐디_(%EC%9B%B9_%EC%84%9C%EB%B2%84)

[^3_20]: https://ygtoken.tistory.com/380

[^3_21]: https://www.youngju.dev/blog/kubernetes/2026-03-03-cilium-ebpf-networking-guide

[^3_22]: https://montkim.com/cilium-overview

[^3_23]: https://appsecsanta.com/trufflehog

[^3_24]: https://trufflesecurity.com/docs/scan-for-secrets

[^3_25]: https://www.helpnetsecurity.com/2024/02/21/trufflehog-open-source-solution-for-scanning-secrets/

[^3_26]: https://trufflesecurity.com/blog/secret-scanning-encoded-and-archived-data

[^3_27]: https://wazuh.com

[^3_28]: https://wazuh.com/platform/siem/

[^3_29]: https://yjshin.tistory.com/1296

[^3_30]: https://betwe.tistory.com/entry/오픈소스-보안-강력한-무료-SIEMXDR-솔루션-Wazuh와주-414-완벽-가이드-및-설치-방법

[^3_31]: https://soy-ul.tistory.com/13

[^3_32]: https://tech.socarcorp.kr/security/2019/07/31/keycloak-sso.html

[^3_33]: https://adjh54.tistory.com/645

[^3_34]: https://docs.cloud.google.com/architecture/identity/keycloak-single-sign-on?hl=ko

[^3_35]: https://www.hashicorp.com/ko/resources/korean-introduction-to-hashicorp-vault

[^3_36]: https://kschoi728.tistory.com/455

[^3_37]: https://www.youtube.com/watch?v=8OPAmqKi8uQ

[^3_38]: https://aws.amazon.com/ko/blogs/tech/kubernetes-runtime-security-using-amazon-eks-add-on-falco/

[^3_39]: https://www.reddit.com/r/kubernetes/comments/1gi00wi/kubernetes_security_how_i_use_falco_to_detect/

[^3_40]: https://velog.io/@yukyung_16/Falco%EB%A5%BC-%ED%99%9C%EC%9A%A9%ED%95%9C-%EC%BF%A0%EB%B2%84%EB%84%A4%ED%8B%B0%EC%8A%A4-%EB%9F%B0%ED%83%80%EC%9E%84-%EB%B3%B4%EC%95%88-%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81

[^3_41]: https://www.youtube.com/watch?v=C8ephsD1_fM

[^3_42]: https://seekerslab.com/ko/resources/blog/ebpf-기반-kubernetes-런타임-보안-모니터링-falco와-cwpp를-활용한-실시간-위협-탐지-1771811417832

[^3_43]: https://pkglog.com/blog/caddy-web-server-guide/

[^3_44]: https://polarcompass.tistory.com/317

[^3_45]: https://blog.naver.com/isc0304/222513152724

[^3_46]: https://koder.ai/ko/blog/nginx-vs-caddy-2025-eoddeon-web-seobeoreul-sayonghaeya-halgga

[^3_47]: https://nginxstore.com/blog/kubernetes/harbor-컨테이너-레지스트리-kubernetes-배포-가이드/

[^3_48]: https://github.com/trufflesecurity

[^3_49]: https://sweetlittlebird.github.io/posts/2024-10-26-KANS-Study-Week8/

[^3_50]: https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/README.md

