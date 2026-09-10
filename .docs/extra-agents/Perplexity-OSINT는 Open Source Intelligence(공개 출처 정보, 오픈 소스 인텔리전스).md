<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# OSINT란 무엇인가

OSINT는 **Open Source Intelligence**(공개 출처 정보, 오픈 소스 인텔리전스)의 약자로, **누구나 합법적으로 접근할 수 있는 공개 출처에서 정보를 수집·분석해 인사이트를 추출하는 과정**을 말합니다.[^1_1][^1_2][^1_3]

### 기본 정의

- 군사·정보기관 용어에서 유래했으며, 공개된 신문·방송, 정부 보고서, 웹사이트, 소셜 미디어, 포럼, 학술지 등 공개 데이터를 인텔리전스(정보·통찰)로 바꾸는 활동을 의미합니다.[^1_4][^1_2][^1_5]
- 정보 기관에서는 HUMINT(인간), SIGINT(신호)와 같은 비공개 정보수집과 병행해 사용되며, 오늘날에는 사이버 보안·비즈니스 인텔리전스 영역에서도 널리 쓰입니다.[^1_6][^1_5]


### 주요 활용 분야

- **사이버 보안**: 공격자 입장에서는 표적 회사의 디지털 풋프린트(도메인, IP, 포트, 직원 정보 등)를 파악하고, 방어자는 동일한 공개 정보를 이용해 취약점과 노출 자산을 점검합니다.[^1_3][^1_1][^1_6]
- **법집행·수사**: 범죄 조직, 극단주의 세력, 금융사기 등 사건 관련 공개 정보(소셜 미디어, 블로그, 공공 기록)를 수집해 사건 전개 경로와 연관 관계를 분석합니다.[^1_4][^1_3]
- **비즈니스/리서치**: 경쟁사 활동, 시장 동향, 브랜드 평판을 모니터링하거나, 투자·리서치 기반 데이터를 수집하는 데 활용됩니다.[^1_7][^1_8][^1_9]


### OSINT의 핵심 특징

- **“공개” = “합법적 접근 가능”**: 유료 데이터베이스나 공개적으로 접근 가능한 정보이지만, 비밀 유지·개인정보 보호·저작권 등 법적·윤리적 기준을 따르는 것이 중요합니다.[^1_10][^1_8][^1_3]
- **단순 수집이 아니라 분석**: 단순히 데이터를 긁어오는 것뿐 아니라, 여러 출처의 정보를 연관·정제·시각화해 **의사 결정에 활용 가능한 인텔리전스**로 변환하는 것이 핵심입니다.[^1_9][^1_6][^1_4]

원하시면, OSINT를 당신의 **사이버 보안 아키텍처·위협 인텔리전스 파이프라인 설계**에 어떻게 접목할 수 있는지(예: 자동화 수집, IoC 관리, 그래프 기반 연관 분석 등) 구체적으로 설계안도 같이 정리해 드릴까요?
<span style="display:none">[^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://www.ibm.com/kr-ko/think/topics/osint

[^1_2]: https://www.kisec.com/rsrh_rpt_det.do?id=163

[^1_3]: https://www.criminalip.io/knowledge-hub/blog/24024

[^1_4]: https://www.sentinelone.com/ko/cybersecurity-101/threat-intelligence/open-source-intelligence-osint/

[^1_5]: https://jennana.tistory.com/113

[^1_6]: https://www.trendmicro.com/ko_kr/what-is/threat-detection/open-source-intelligence-osint.html

[^1_7]: https://goong.com/ko/word/open_source_intelligence_%ED%95%9C%EA%B5%AD%EC%96%B4/

[^1_8]: https://blog.criminalip.io/ko/2024/12/19/osint/

[^1_9]: https://www.opentext.com/kr/what-is/open-source-intelligence-osint

[^1_10]: https://www.criminalip.io/ko/knowledge-hub/blog/24024

[^1_11]: https://myeverythingdocument.tistory.com/43

[^1_12]: https://namu.wiki/w/공개출처정보

[^1_13]: https://www.youtube.com/watch?v=LWwbr1Ub-SY

[^1_14]: https://blog.naver.com/happymaru11/222154733970

[^1_15]: http://terms.tta.or.kr/dictionary/dictionaryView.do?subject=Open+Source+Intelligence


---

# OSINT 주요 도구는 무엇인가

OSINT(Open Source Intelligence)의 **주요 도구**는 공개 정보를 수집·정리·그래프화하는 데 특화된 툴들로, 사이버 보안·위협 인텔리전스·수사·리서치 용도로 널리 쓰입니다.[^2_1][^2_4][^2_5]

### 대표적인 OSINT 도구

| 도구 이름 | 주요 용도 |
| :-- | :-- |
| **Maltego** | 도메인, IP, 이메일, 소셜 계정 등 간의 관계를 그래프로 시각화해 연결망(네트워크) 분석을 수행하는 링크 분석 도구. [^2_2][^2_4][^2_5] |
| **theHarvester** | 구글, 빙, 야후, 트위터 등에서 이메일, 서브도메인, 가상 호스트 정보를 수집해 초기 정찰(Recon)에 활용하는 CLI 기반 도구. [^2_2][^2_4] |
| **SpiderFoot** | IP, 도메인, 이메일, 사용자명 등을 기반으로 수백 개의 OSINT 소스를 자동으로 조회해 정보를 수집·상관·시각화하는 자동화 정찰 프레임워크. [^2_4][^2_5] |
| **Shodan** | 인터넷에 연결된 서버·IoT 장비·라우터·웹 서버 등을 검색해 개방 포트·서비스·취약 시스템을 파악하는 “IoT/네트워크 검색 엔진”. [^2_2][^2_4] |
| **Recon‑ng** | 웹 기반 OSINT 정찰 프레임워크로, 모듈을 이용해 서브도메인 열거, 이메일 패턴 추출, 소셜 미디어 정보 수집 등을 자동화. [^2_4][^2_6] |
| **FOCA** | 웹에서 다운로드한 MS 문서·PDF·Excel·PPT 등에서 메타데이터·숨겨진 정보를 추출해 조직 내부 구조·기술 스택을 파악하는 도구. [^2_4][^2_5] |
| **OSINT Framework** | 다양한 OSINT 도구·웹 서비스를 카테고리별로 모아둔 “OSINT 도구 포털”로, 특정 작업(예: SNS 탐색, IP 도메인 조사)에 맞는 툴을 빠르게 찾을 수 있음. [^2_4] |
| **Social Mapper / Tinfoleak / Datasploit** | 소셜 미디어 계정 매핑, 트위터 사용자 분석, 도메인·IP 기반 계정·취약점 자동 수집 등 SNS·소셜 정보 추적에 특화된 도구. [^2_4] |
| **Babel X, Intelligence X, DarkSearch** | 다국어·SNS·다크웹·딥웹에서 OSINT를 수집·분석하는 고급 상업 플랫폼(API + AI/NLP 기반). [^2_5] |

### 간단한 활용 패턴(보안 아키텍처 관점)

- **내부 공격 표면 분석**: SpiderFoot + Recon‑ng + Shodan 조합으로 IP·도메인·서브도메인과 연관된 SNS·파일·취약점 정보를 자동 수집.[^2_4][^2_5]
- **외부 위협 인텔리전스**: Maltego에서 IoC(해시, 도메인, IP, 이메일)를 그래프로 연결해 리스크·공격자 네트워크를 시각화.[^2_5][^2_4]

보안 아키텍처 관점에서 “OSINT 도구들을 자동화 플랫폼(Mcp, Airflow, OpenCTI 등)에 엮어 위협 인텔리전스 파이프라인으로 재구성”하는 요구가 있다면, 구체적인 도메인(예: 금융·헬스케어)을 알려주시면 아키텍처 설계안을 함께 잡아 드리겠습니다.
<span style="display:none">[^2_10][^2_3][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.ibm.com/kr-ko/think/topics/osint

[^2_2]: https://blog.naver.com/happymaru11/222154733970

[^2_3]: https://www.sentinelone.com/ko/cybersecurity-101/threat-intelligence/open-source-intelligence-osint/

[^2_4]: https://suji-log.tistory.com/entry/OSINTOpen-Source-Intelligence-도구-10가지

[^2_5]: https://www.wiz.io/ko-kr/academy/threat-intel/osint-tools

[^2_6]: https://sh112-kr.tistory.com/30

[^2_7]: https://www.criminalip.io/ko/knowledge-hub/blog/24024

[^2_8]: https://www.criminalip.io/knowledge-hub/blog/24024

[^2_9]: https://www.kisec.com/rsrh_rpt_det.do?id=163

[^2_10]: https://blog.naver.com/happymaru11/222283492161


---

# OSINT를 활용해 기업 정보의 Ontology 구축 방법에 대해서 상세하게 알려줘

OSINT를 활용해 **기업 정보의 Ontology(온톨로지)**를 구축한다는 것은,
👉 공개 데이터(OSINT)에서 추출한 정보를 바탕으로 **기업·인물·기술·공급망·리스크** 등을 **클래스–속성–관계로 정형화한 지식 그래프 구조**로 만드는 과정이라고 볼 수 있습니다.[^3_1][^3_2][^3_3][^3_4]

아래는 **실무 수준에서 적용 가능한 상세한 프로세스 + 도구 레시피**를 정리한 것입니다.

***

### 1. 단계 1: 범위 정의 및 요구사항 분석 (Domain Analysis)

OSINT에서 어떤 정보를 엔티티로 보고, 어떤 관계를 잡을지 사전에 정의해야 합니다.[^3_5][^3_1]

- **핵심 도메인(스코프)** 예시:
    - `기업(Company)`, `임원/주주(Person)`, `사업 부문(IndustrySegment)`, `제품/서비스`, `기술 스택`, `공급체인(공급·고객)`, `위협·리스크(위협 인텔리전스 IoC 등)`
- **목표 정의**:
    - 예: “금융·헬스케어 공급망의 리스크를 파악할 수 있는 기업 정보 온톨로지”
    - 질문: 어떤 분석을 할 것인지? (예: 공급망 집중도, 제3자 리스크, 공격 표면 분석 등)[^3_6][^3_7]

도구 활용 포인트:

- **OSINT 기획 단계**: `OSINT Framework` 또는 `SpiderFoot`/`Wiz`의 템플릿을 참고해 정보 요구사항(ICR, Information Collection Requirements)을 정의.[^3_7][^3_2]

***

### 2. 단계 2: 핵심 개념 계층 구조 정의 (Conceptualization)

OnTop of Ontology Development 101·Middle‑out 방법론을 따라,
“기업 도메인”에 대한 **클래스‑하위 클래스 계층**을 정의합니다.[^3_8][^3_9][^3_1]

대략적인 **클래스 구조 예시**:

```text
Thing
├─ Organization
│  ├─ Corporation           # 상장·비상장 기업
│  ├─ Startup
│  ├─ PublicInstitution     # 공공기관
├─ Person
│  ├─ Executive
│  ├─ Shareholder
├─ TechnologyStack
│  ├─ FrontendFramework
│  ├─ BackendFramework
│  ├─ CloudProvider
├─ RiskIndicator
│  ├─ CVE
│  ├─ DNSLeak
│  ├─ ExposedService
```

이렇게 정의하면 이후에 OSINT에서 뽑은 도메인·IP·기술·IoC를 적절한 클래스로 매핑할 수 있습니다.[^3_10][^3_2]

***

### 3. 단계 3: 속성·관계·제약 정의 (Properties \& Relations)

OSINT에서 추출된 정보는 대부분 **엔티티–속성–관계** 형태로 와야 지식 그래프로 쓸 수 있습니다.[^3_4][^3_1][^3_8]

#### 3‑1. 속성 예시

- `Organization`:
    - `name`, `homepage`, `ticker`, `country`, `foundedYear`, `industry`, `legalform`, `legaladdress`
- `Person`:
    - `name`, `role`, `affiliation`, `email`, `phone`, `linkedinUrl`
- `TechnologyStack`:
    - `framework`, `version`, `detectedBy`, `detectedAt`


#### 3‑2. 관계 예시 (RDF/OWL 관점)

- `Organization hasExecutive Person`
- `Organization usesTechnologyStack TechnologyStack`
- `Organization isPartOfSupplyChain Organization`
- `Organization hasDomain String`
- `Organization associatedWith RiskIndicator`

이렇게 관계를 정의해 두면, **Maltego**·**Neo4j**·**OpenCTI** 같은 **그래프/온톨로지 스토어**에 직접 매핑 가능합니다.[^3_2][^3_4]

***

### 4. 단계 4: OSINT 기반 데이터 수집 및 전처리

여기서 OSINT 도구를 **자동 수집 Agent**로 쓰면서, 출력을 **RDF/OWL 트리플 또는 지식 그래프 노드** 형식으로 정규화합니다.[^3_3][^3_10][^3_2]

#### 4‑1. 주요 도구와 수집 타입

| OSINT 도구 | 수집하는 것 | Ontology에 매핑 예시 |
| :-- | :-- | :-- |
| **SpiderFoot** | 도메인, 서브도메인, IP, 이메일, TLS, 위협 인텔리전스 피드 | `Organization → hasDomain`, `hasIp`, `associatedWith RiskIndicator` |
| **Maltego** | IP ↔ 도메인 ↔ 조직 ↔ 소셜 계정 관계 그래프 | `Organization → hasProfileOn Person`, `Person → worksAt Organization` |
| **Shodan / BuiltWith / Censys** | 서비스, 포트, 기술 스택, 웹 프레임워크, CMS | `Organization → hasExposedService`, `usesTechnologyStack` |
| **Babel X / Intelligence X / DarkSearch** | 뉴스, SNS, 다크웹, 딥웹에서 기업 언급 | `Organization → involvedIn Event`, `hasRiskIndicator` |
| **기업/공공 DB 크롤링** | 공시·특허·상표·정부 DB 등 | `Organization → registers Trademark`, `Organization → files Patent` |

#### 4‑2. 데이터 전처리 패턴 (Pipeline 설계)

1. **RAW OSINT → JSON → 트리플(Graph) 변환**
    - 각 도구의 출력(JSON/CSV)을 ETL 파이프라인으로 통합.
    - 예시: SpiderFoot JSON → `subject`–`predicate`–`object` 형식으로 변환.
2. **엔티티 링크/정규화**
    - 동일 기업의 다양한 표기(한글/영문/약어)를 하나의 `Organization` 노드로 합침.
    - 규칙: `homepage`, `주소`, `Business ID`, `Ticker`, `상호 정확도 필터` 등.[^3_1][^3_4]

위 과정은 **Python + Apache Spark + Kafka** 또는 **Airflow + Flink** 기반 파이프라인으로 설계하는 것이 일반적입니다.[^3_6][^3_8]

***

### 5. 단계 5: Ontology 자동/반자동 구축 (Ontology Learning)

OSINT에서 나오는 웹 문서·뉴스·공개 PDF를 활용해, **온톨로지 학습** 기법을 적용할 수 있습니다.[^3_9][^3_8]

#### 5‑1. 텍스트 기반 온톨로지 자동 구축

- **공개 웹 문서/보도자료/공시**에서 형태소 분석 + 개체명 인식(NER)을 수행.
    - 예: “A사는 TypeScript를 사용합니다” →
        - `Organization: A사`, `TechnologyStack: TypeScript`
        - 관계: `A사 → usesTechnologyStack → TypeScript`
- 관련 기술:
    - **NER + Relation Extraction** (예: spaCy, BERT‑NER, KoBERT 등)
    - **Korean Ontology 구축 관련 연구**에서 제안하는 클래스·관계 유사도 기반 트리플 생성 방식.[^3_8][^3_9]


#### 5‑2. 반자동 보정 (Human‑in‑the‑loop)

- 자동 생성된 트리플을 **OWL 편집기(Protege 등)** 또는 **지식 그래프 UI**에서 검수·보정.
- 예: “TensorFlow”와 “TensorFlow.js”를 같은 클래스로 합칠지, 별도 클래스로 둘지 규칙 정의.[^3_5][^3_1]

***

### 6. 단계 6: Ontology 저장 및 지식 그래프 구현

정리된 Ontology는 **RDF/OWL 저장소** 또는 **그래프 DB**에 적재하여, 분석·검색·AI 학습에 활용할 수 있습니다.[^3_4][^3_8]

#### 6‑1. 후보 저장소/플랫폼

- **RDF/OWL 스토어**:
    - Apache Jena, GraphDB, Ontotext GraphDB, Stardog
- **그래프 DB**:
    - Neo4j, JanusGraph, NebulaGraph
- **통합 인텔리전스 플랫폼**:
    - OpenCTI, MISP (위협 인텔리전스 쪽)[^3_7][^3_4]


#### 6‑2. 쿼리 예시 (OWL/RDF‑SPARQL)

```sparql
SELECT ?company ?domain
WHERE {
  ?company a :Organization .
  ?company :hasDomain ?domain .
  FILTER(CONTAINS(?domain, ".kr"))
}
```

이런 쿼리를 통해 특정 국가·산업·기술 스택을 가진 기업을 필터링할 수 있습니다.[^3_8][^3_4]

***

### 7. 단계 7: Governance·Privacy·合规 (규제 준수)

OSINT 자체는 공개 데이터지만, 기업 정보 Ontology는 **GDPR·개인정보·데이터 주권** 등을 고려해야 합니다.[^3_6][^3_7]

- **디자인 고려사항**:
    - 쿼리 로그, 접근 권한, 데이터 생애주기(keep until…), 감사 로그를 기록하는 **데이터 거버넌스 플랫폼**과 연계.
        - 예: Solix 통합 데이터 플랫폼처럼, OSINT 데이터셋에 대한 **계보(traceability)**와 **정책 적용**을 제공.[^3_6]
- **윤리적/합법적 한계**:
    - 이메일, 전화번호, 내부 구조 정보는 OSINT 기준이지만, **목적·범위·보관**에 따라 법적 책임이 생길 수 있음.[^3_11][^3_6]

***

### 8. 실무 아키텍처 레시피 (요약)

1. **도메인·Ontology 설계**
    - `Organization` 중심 클래스 계층 + 속성·관계 정의 (Top‑down + Middle‑out).[^3_1][^3_5]
2. **OSINT 수집 파이프라인**
    - `SpiderFoot` + `Maltego` + `Shodan/BuiltWith` + `Babel X` 등의 Output을 JSON으로 통합.[^3_10][^3_2]
3. **ETL/정규화**
    - 엔티티 링크, 중복 합치기, 트리플 변환(예: `org→domain`, `org→techstack`).[^3_4][^3_8]
4. **Ontology 자동 학습**
    - 웹 문서/뉴스에서 NER + Relation Extraction으로 트리플 생성 후 보정.[^3_9][^3_8]
5. **지식 그래프 저장/쿼리**
    - Jena/GraphDB 또는 Neo4j/OpenCTI에 저장·SPARQL/GraphQL 쿼리.[^3_8][^3_4]
6. **Governance·감사**
    - 데이터 거버넌스 플랫폼과 연계해 계보·정책·접근 권한 관리.[^3_6]

***

구체적으로 **“금융기관의 공급망 리스크” 또는 “헬스케어 장비/제약사 공급망”**를 대상으로 하는 Ontology를 설계하고 싶으신가요?
그렇다면,

- 도메인 스키마(클래스/관계) 예시
- OSINT 수집 룰셋(예: 어떤 기업/산업을 타겟으로 잡을지, 어떤 IoC/도메인/기술을 추적할지)
- 이후 **OpenCTI/Neo4j + Kafka/Spark 기반 파이프라인 설계**를 한 번에 같이 잡아 드릴 수 있습니다.

원하시는 도메인(예: 금융 vs 헬스케어 vs 제조/공급망)을 한 가지만 말씀해 주시겠어요?
<span style="display:none">[^3_12][^3_13][^3_14][^3_15]</span>

<div align="center">⁂</div>

[^3_1]: https://brunch.co.kr/@writerjeong/290

[^3_2]: https://www.wiz.io/ko-kr/academy/threat-intel/osint-tools

[^3_3]: https://www.sentinelone.com/ko/cybersecurity-101/threat-intelligence/open-source-intelligence-osint/

[^3_4]: https://joyhong.tistory.com/187

[^3_5]: https://contents.premium.naver.com/itransformlabs/aisolocontents/contents/250523085631561tf

[^3_6]: https://www.solix.com/ko/blog/open-source-intelligence-osint-how-enterprises-turn-public-data-into-governed-ai-and-risk-intelligence/

[^3_7]: https://kr.linkedin.com/pulse/how-apply-osint-enterprise-threat-intelligence-defronix-cnlef?tl=ko

[^3_8]: https://oak.chosun.ac.kr/bitstream/2020.oak/6901/2/의미적 정보검색을 위한 온톨로지 자동 구축 및 효율적 질의 처리 방법.pdf

[^3_9]: https://patents.google.com/patent/KR20110070343A/ko

[^3_10]: http://apjcriweb.org/content/vol10no5/1.pdf

[^3_11]: https://github.com/OffcierCia/non-typical-OSINT-guide/blob/main/Korea.md

[^3_12]: https://www.youtube.com/watch?v=Sb4VVSycwWU

[^3_13]: https://ai-work-flow.com/ko/2025/12/22/한국-정부와-기업이-배워야-할-미군의-ai-보안-전략/

[^3_14]: https://www.kigam.re.kr/boardDownload.es?bid=0060\&list_no=31104\&seq=1

[^3_15]: https://kr.linkedin.com/pulse/getting-nosey-osint-hr-ta-professionals-alesya-raskuratova-tmkge?tl=ko


---

# OSINT 온톨로지 구축 추천 무료 도구

기업 온톨로지 Top-down vs Bottom-up 비교
OSINT 기반 온톨로지 실전 사례 연구

---
## 1. OSINT 온톨로지 구축 추천 무료 도구

### 1.1 OSINT 데이터 수집 도구

- **Maltego Community Edition**
    - 그래프 기반 링크 분석으로, 기업–IP–도메인–소셜 계정 관계를 시각화해 온톨로지 관계(triples)를 손쉽게 추출 가능.
    - 리포트 export: CSV, GEXF, OWL 포맷으로 저장 가능.[^4_1][^4_2]
- **SpiderFoot**
    - 오픈소스 OSINT 재connaissance 툴로, 200+ 모듈을 통해 도메인·IP·이메일·ASN·BTC 주소 등을 수집.
    - JSON/CSV로 출력 → 이후 ETL을 통해 RDF/OWL 트리플로 변환 가능.[^4_2][^4_3][^4_1]
- **Recon‑ng**
    - 웹 기반 정찰 프레임워크로, 서브도메인, 이메일, 사용자명, SNS 정보를 자동 수집.[^4_4][^4_3]
- **OSINT Framework**
    - 수백 개 OSINT 도구를 프록시·SNS·도메인·IP 등 카테고리별로 정리해, 온톨로지 구축에 필요한 도구를 빠르게 찾는 “포털” 역할.[^4_5][^4_2]


### 1.2 온톨로지/지식 그래프 구축 도구

- **Protégé (OWL Editor)**
    - Stanford에서 제공하는 무료 온톨로지 편집기. OWL–RDF 기반 클래스–속성–관계 설계 및 추론 지원. OSINT 데이터에서 추출한 트리플을 Ontology로 매핑할 때 필수.[^4_6][^4_7]
- **Apache Jena / Fuseki**
    - 오픈소스 RDF/OWL 스토어 + SPARQL 서버. OSINT에서 나온 트리플을 로드하고, 온톨로지·쿼리 기반 서칭을 제공.[^4_7][^4_6]
- **Neo4j Community Edition**
    - 자유형 그래프 DB로, 기업–인물–기술–위협 관계를 노드–엣지로 저장. 온톨로지 출력을 JSON/CSV로 변환 후 매핑 가능.[^4_7]

***
## 2. 기업 온톨로지 Top‑down vs Bottom‑up 비교

### 2.1 Top‑down 방식

- **정의**: 도메인 전문가가 먼저 비즈니스 개념 사전 정의 → 이후 데이터를 이 틀에 맞게 매핑.
- **장점**
    - 체계적이고 일관성 높음: 기업·공급망·리스크 등 미리 정의한 개념 구조에 따라 설계.[^4_8][^4_6]
    - 규제·거버넌스 친화적: GDPR·개인정보·데이터 거버넌스 정책과 맞춰 설계 가능.
- **단점**
    - 초기 설계 시간이 길고, 데이터 변동 시 유연성이 낮음.[^4_9][^4_6]


### 2.2 Bottom‑up 방식

- **정의**: 실제 데이터(예: OSINT 수집 결과)에서 NER·관계 추출을 통해 온톨로지 구조를 자동 추출.
- **장점**
    - 데이터 현실에 밀접: OSINT에서 나온 기업·기술·위협·SNS 정보를 직접 반영.[^4_6][^4_7]
    - 빠른 프로토타이핑 가능: NLP 기반 자동 추출 + 반복적 보정.
- **단점**
    - 일관성·중복 개념 문제가 발생 가능. 사람이 보정하는 과정이 필수.


### 2.3 활용 방식 비교 표

| 항목 | Top‑down | Bottom‑up |
| :-- | :-- | :-- |
| 주요 특징 | 도메인 전문가 설계 | 데이터 기반 자동 생성 |
| 설계 시간 | 길음 | 짧음 |
| 일관성 | 높음 | 보정 필요 |
| 유연성 | 낮음 | 높음 |
| 적합 도메인 | 안정적 도메인(예: 금융·공공) | 변화 빠른 도메인(예: E‑commerce·FinTech) |

**실무 권장**: Top‑down으로 초기 온톨로지 구조를 설계한 후, Bottom‑up으로 OSINT 데이터를 수집·추출하여 반복적으로 보정하는 하이브리드 방식이 가장 효과적.[^4_6][^4_7]

***
## 3. OSINT 기반 온톨로주 실전 사례 연구

### 3.1 범죄 수사 기록 온톨로지 구축

- **개요**: 한국의 KISTI 연구에서, 범죄 수사 기록 문서에서 정보를 추출해 온톨로지를 구축하고, 검색 서비스와 범행 장소 추천 서비스를 제공.[^4_7]
- **OSINT 역할**: 비정형 수사 기록(텍스트, 보고서)에서 개체명 인식(NER)을 통해 사건·장소·인물 정보를 추출.[^4_7]
- **온톨로지 구조**:
    - `Event(사건) → occursAt Location(장소)`
    - `Person → perpetratorOf Event`
    - `Location → similarTo Location`
- **효과**: 수사관이 자연어 검색으로 범행 장소를 빠르게 추천받는 서비스 구현.[^4_7]


### 3.2 사이버 위협 인텔리전스(Threat Intelligence)

- **개요**: OSINT 기반 위협 인텔리전스 플랫폼에서, OSINT 수집 도구(예: Maltego, SpiderFoot, Shodan)를 활용해 공격자·도메인·IP·CVE 정보를 수집.[^4_10][^4_1]
- **온톨로지 구조**:
    - `Attacker → targets Organization`
    - `Organization → usesTechnologyStack TechnologyStack`
    - `CVE → affects Organization`
- **효과**: 공격 패턴을 온톨로지 기반으로 분석·추론하여, 조직의 공격 표면을 시각화하고 취약점 관리에 활용.[^4_1][^4_10]


### 3.3 실무 적용 팁

- **Top‑down 설계**: 기업 정보 온톨로지(예: 기업–공급자–고객–위협)를 먼저 설계.[^4_6]
- **Bottom‑up 구축**: OSINT 도구(예: Maltego, SpiderFoot, Shodan)에서 데이터를 수집 → Protégé/Jena로 Ontology를 구축.[^4_1][^4_7]
- **실제 적용 도메인:**
    - 금융 공급망 리스크 분석
    - 헬스케어 공급망(의료 기기·제약사) 위협 인텔리전스
    - 제조업 공급망 집중 리스크

***
이상으로 OSINT 온톨로지 구축을 위한 **무료 도구**, **기업 온톨로지 설계 방식 비교**, **실전 사례**를 정리했습니다.
원하시면, **헬스케어 공급망** 또는 **금융 공급망**을 대상으로 구체적인 온톨로지 설계(예: 기업–공급자–고객–위협 관계)를 만들어 드리겠습니다.
어느 도메인에 적용하시고 싶으신가요?
<span style="display:none">[^4_11][^4_12][^4_13][^4_14][^4_15]</span>

<div align="center">⁂</div>

[^4_1]: https://www.wiz.io/ko-kr/academy/threat-intel/osint-tools

[^4_2]: https://www.unite.ai/ko/best-open-source-intelligence-osint-tools/

[^4_3]: https://www.reddit.com/r/Hacking_Tutorials/comments/1omnjq4/5_free_osint_tools_every_ethical_hacker_must_know/

[^4_4]: https://sh112-kr.tistory.com/30

[^4_5]: https://kr.linkedin.com/pulse/top-10-free-osint-resources-budding-soc-analysts-edward-kiledjian?tl=ko

[^4_6]: https://www.quryon.com/post/현대적-온톨로지의-3단계-과정

[^4_7]: https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201910537995953

[^4_8]: https://www.valley.town/space/@bspark/articles/69847bc5123b73346660b162

[^4_9]: https://blog.naver.com/ktnetblog/223945154281

[^4_10]: https://www.etnews.com/20251216000045

[^4_11]: https://www.reddit.com/r/cybersecurity/comments/1ooiz0g/top_15_web_based_osint_tools_free_enjoy/

[^4_12]: https://eset.estc.co.kr/bbs/board.php?bo_table=notice\&wr_id=16

[^4_13]: https://github.com/OffcierCia/non-typical-OSINT-guide/blob/main/Korea.md

[^4_14]: https://lifeis-picnic.com/palantir-vs-anthropic-autonomous-strategy/

[^4_15]: https://www.kisec.com/rnd_sts_det.do?id=211


---

# 기업 온톨로지 무료 OSINT 도구 비교 가이드 — Top-down vs Bottom-up 적용 예시

OSINT 기업 온톨로지 실제 성공 사례 10개 분석 — 범죄기록 사례와 비교
OSINT 온톨로지 구축을 위한 Protégé 튜토리얼
Top-down 온톨로지 기업 적용 사례
Bottom-up 온톨로지 OSINT 데이터 처리 워크플로우

아래 답변은 요청하신 다섯 가지를 한 번에 볼 수 있게 **섹션별로 정리**해 드립니다.

***

## 1. 기업 온톨로지용 무료 OSINT 도구 비교 가이드

(Top‑down vs Bottom‑up 관점)

기업 온톨로지는 “클래스 구조 설계(Top‑down)”와 “실제 데이터 수집·추출(Bottom‑up)”이 함께 돌아가야 합니다.[^5_1][^5_2]

### 1.1 추천 무료 OSINT 도구 목록

| 구분 | 도구 | 특징 | Top‑down에서의 역할 | Bottom‑up에서의 역할 |
| :-- | :-- | :-- | :-- | :-- |
| 링크 분석 | Maltego CE | 그래프 기반 엔티티·관계 시각화 툴 (Community Edition 무료) | 설계한 Ontology에 맞게 엔티티 타입·관계를 시각적으로 검증 | 수집된 OSINT로부터 실제 관계 패턴을 탐색해 새로운 관계 후보 발굴[^5_3] |
| 자동 정찰 | SpiderFoot OSS | 도메인·IP·이메일·DNS·위협 피드 자동 수집 | 어떤 속성과 관계가 많이 나오는지 보고 Ontology 속성 목록 보완 | 다수 도메인/조직에 대해 OSINT를 크롤링해 원천 데이터 생성[^5_4][^5_3] |
| 웹 정찰 | Recon‑ng | 모듈형 웹 기반 정찰 프레임워크 | 설계한 엔티티(기업, 직원, 도메인 등)별로 어떤 필드를 실제로 뽑을지 확인 | OSINT 기반 이메일, 호스트, SNS 계정 등 자동 수집[^5_5] |
| 노출 서비스 검색 | Shodan / Censys 무료 tier | 인터넷에 노출된 서비스·포트·배너 탐지 | “ExposedService”, “TechnologyStack” 같은 클래스·관계 필요성을 확인 | 기업별 공격 표면 데이터(포트, 배너, SW 버전)를 대량 수집[^5_6] |
| 검색/수집 가이드 | OSINT Framework | OSINT 도구를 카테고리별로 모아둔 포털 | 도메인 분석 범위를 설계할 때, 어떤 소스를 Ontology에 반영할지 카탈로그로 활용 | 각 카테고리별 도구를 골라 실제 데이터 수집에 사용[^5_3] |

- **Top‑down 관점**: 어떤 “개념·속성·관계”가 필요한지 정의한 뒤, 위 도구들을 써서 “실제 데이터가 그 구조를 얼마나 뒷받침하는지” 검증합니다.[^5_2][^5_1]
- **Bottom‑up 관점**: 먼저 SpiderFoot·Shodan·Recon‑ng로 데이터를 긁은 뒤, 그 안에서 반복적으로 등장하는 패턴을 관찰하며 Ontology의 클래스와 관계를 늘려 갑니다.[^5_6][^5_4][^5_5]

***

## 2. 기업 온톨로지 Top‑down vs Bottom‑up 적용 예시

### 2.1 Top‑down 적용 예시 (기업 도메인)

- 참고 개념: Top‑down은 **가장 일반적인 개념 → 구체적인 개념**으로 내려가는 방식입니다.[^5_1][^5_2]
- 기업 도메인 예시 스케치:

```text
Thing
 ├─ Organization
 │   ├─ Corporation
 │   ├─ Startup
 │   ├─ PublicInstitution
 ├─ Person
 │   ├─ Executive
 │   ├─ Employee
 ├─ TechnologyStack
 ├─ RiskIndicator
 ├─ SupplyChainRelation
```

- 적용 과정 예시:

1. 도메인 전문가가 기업의 의사결정·리스크 분석에 필요한 개념(Organization, Person, TechnologyStack, RiskIndicator 등)을 정의.[^5_1]
2. 각 클래스에 필수 속성(예: Organization.name, Organization.country, Organization.industry)을 결정.
3. “Organization usesTechnologyStack TechnologyStack”, “Organization hasSupplier Organization” 같은 핵심 관계를 정의.[^5_2][^5_1]
4. 이후 OSINT 도구에서 나온 데이터는 이 스키마에 맞춰 매핑/필터링.


### 2.2 Bottom‑up 적용 예시 (OSINT 주도)

- Bottom‑up은 **데이터에서 출발하여 반복적으로 개념 구조를 끌어올리는 방식**입니다.[^5_2][^5_1]
- 적용 과정 예시:

1. SpiderFoot과 Shodan으로 여러 기업의 도메인·IP·서비스·배너·기술 스택 데이터를 수집.[^5_4][^5_6]
2. 수집 데이터에서 빈출 필드(예: port, product, version, org, city)를 보고 자연스럽게 “ExposedService”, “TechnologyStack”, “Location” 같은 클래스를 추출.
3. Maltego CE에 데이터를 넣어 조직–IP–DNS–SSL 인증서–이메일 간 관계 그래프를 시각화하고, 자주 등장하는 관계 패턴을 Ontology의 object property로 승격.[^5_3]
4. Protégé로 올라가 “아, Organization와 ExposedService가 이렇게 다대일 구조로 연결되는구나”를 보고 클래스·관계를 정리.
- 실무적으로는 Top‑down으로 최소 뼈대를 만든 뒤, Bottom‑up으로 계속 보정하는 **하이브리드 방식**이 제일 많이 추천됩니다.[^5_7][^5_1][^5_2]

***

## 3. OSINT 기반 기업 온톨로지 성공 사례 10개 개요

(범죄기록 온톨로지와 비교)

논문·보고서·칼럼 수준에서 공개된 케이스를 기준으로, **“OSINT + Ontology/지식 그래프” 패턴**을 기업 활용에 가까운 사례 중심으로 정리하면 다음과 같은 유형들이 반복됩니다.[^5_8][^5_9][^5_10][^5_11][^5_12]

1. **범죄 수사기록 온톨로지 (침입 절도 도메인)**
    - 비정형 수사기록에서 사건·장소·피의자 정보를 추출해 온톨로지와 검색·추천 서비스를 구현.[^5_13][^5_10]
    - 패턴: `Event–Person–Location` 구조가 기업의 `Incident–Organization–Location` 구조와 매우 유사.
2. **사이버 위협 인텔리전스 온톨로지**
    - OSINT 위협 피드·도메인·IP·CVE 정보를 통합하여 기업별 공격 표면·위협 관계를 Ontology로 표현.[^5_11]
3. **금융기관 위협 인텔리전스**
    - 금융기관과 서드파티 공급사 관계를 위협 Ontology로 모델링해 OSINT 기반 피싱·멀웨어 캠페인 추적.[^5_11]
4. **제조/스마트팩토리 노출 자산 온톨로지**
    - Shodan/Censys OSINT로 수집한 공장·IoT/SCADA 장비 노출 정보를 Ontology 형태로 구조화해 리스크 평가.[^5_14][^5_6]
5. **해운/물류 기업 Ontology (국내 사례)**
    - 국내 웨비나/영상에서, 해운사 업무 개념(선박, 항로, 화물, 계약)과 데이터 자산을 Ontology로 통합해 AI‑ready 데이터로 만든 사례 소개.[^5_9]
6. **데이터 거버넌스·AI‑ready Ontology**
    - 엔코아·국내 SI들이 기업 데이터거버넌스 프로젝트에서 업무 용어 사전+Ontology를 구축해 LLM·RAG 성능을 높인 사례.[^5_12][^5_9]
7. **팔란티어 Foundry 기업 Ontology (Top‑down)**
    - Palantir Foundry는 기업 데이터를 통합하고, **비즈니스 Ontology(“디지털 트윈”)를 Top‑down으로 설계한 뒤** 그 위에서 에이전트를 돌리는 구조를 사용.[^5_8]
8. **자율기업(AI Agentic) Ontology 기반 워크플로**
    - Anthropic vs Palantir 글에서, Palantir 쪽이 구조화된 Ontology를 전제로 한 자율기업 전략을 탑다운 방식으로 전개하는 사례가 소개.[^5_8]
9. **의미 기반 정보검색 Ontology**
    - 한국 논문에서, 온톨로지를 자동 구축해 의미 검색·추천을 제공하는 구조를 제안 (도메인 일반론이지만 기업 문서에도 동일 패턴 적용 가능).[^5_15]
10. **AI 시대 온톨로지 비즈니스 적용 사례 모음**
    - 온톨로지 개념·Top‑down vs Bottom‑up·다양한 산업 적용 사례(물류, 유통, 공공)를 요약한 보고서.[^5_2]

### 범죄기록 온톨로지와 기업 온톨로지의 공통점·차이점

- **공통점**
    - 비정형 텍스트(보고서, 기록, 뉴스)에서 개체와 관계를 추출해 트리플로 표현.
    - 온톨로지 기반 검색·추천(범죄에서는 장소·유형 추천, 기업에서는 공급망·리스크/사건 탐색).[^5_10][^5_15]
- **차이점**
    - 범죄 온톨로지는 사건·인물·장소 중심의 “케이스 관리”.
    - 기업 온톨로지는 조직·제품·공급망·위협·계약 등 더 넓은 비즈니스 개념과 재무·운영 데이터까지 포괄.[^5_9][^5_10][^5_8]

***

## 4. OSINT 온톨로지 구축을 위한 Protégé 튜토리얼 (실무 흐름)

Protégé는 무료 OWL 온톨로지 편집기로, **클래스/속성/인스턴스 정의 + 추론**까지 한 번에 처리할 수 있습니다.[^5_16][^5_17][^5_18]

### 4.1 설치·기본 개념

- Protégé 특징
    - OWL/RDF Ontology를 GUI로 만들고, 클래스(Class), 속성(Property), 개별(Individual)을 쉽게 관리.[^5_17]
    - 플러그인(예: OWLViz, Reasoner)을 통해 계층 구조 시각화, 일관성 검사 가능.[^5_18]
- 설치 튜토리얼 요약

1. 공식 사이트(protege.stanford.edu)에서 설치 파일 다운로드.[^5_16][^5_17]
2. 기본 옵션으로 설치. 필요 시 OWLViz, Reasoner(JFact/HermiT) 플러그인 추가 설치.[^5_18][^5_16]


### 4.2 기업 + OSINT용 기본 작업 순서

1. **새 Ontology 생성**
    - File → New Ontology → Ontology IRI 설정 (예: `http://example.com/company-osint-ontology`).[^5_19]
2. **클래스 계층 정의 (TBox 설계)**
    - “Classes” 탭에서 Organization, Person, TechnologyStack, RiskIndicator, Incident 등 상위 클래스를 생성.[^5_19][^5_1]
    - 필요한 경우 중간 노드(예: `EmploymentRelation`)를 만들어 복잡한 관계를 모델링.[^5_19]
3. **Object/Data Property 정의**
    - “Object properties” 탭에서 `hasExecutive`, `usesTechnologyStack`, `hasSupplier`, `associatedWithRisk` 등 관계 정의.[^5_19]
    - “Data properties” 탭에서 `hasName`, `hasDomain`, `hasTicker`, `hasCountry` 등 속성 정의.[^5_17][^5_1]
4. **제약조건·도메인/레인지 설정**
    - 각 object property에 domain/range 설정 (예: `hasExecutive` domain=Organization, range=Person).[^5_1][^5_19]
    - 필요하면 cardinality 제약 (예: `hasTicker` max 1).
5. **OSINT 결과를 개별(Individual)로 입력**
    - SpiderFoot/Recon‑ng/CSV에서 나온 기업·도메인·IP 정보를 Protégé의 Individuals 탭에서 실제 인스턴스로 등록.[^5_17]
    - 나중에는 ETL 스크립트가 RDF/XML 또는 Turtle로 자동 생성한 트리플을 Protégé/Jena에 로드하는 방식으로 자동화.
6. **Reasoner 실행 및 검증**
    - Reasoner(Ul, HermiT 등)를 돌려 클래스 일관성과 관계 정의 오류를 검사.[^5_19]

Protégé 전용 튜토리얼(설치부터 기본 TBox 설계까지)은 국내 블로그 글과 영상 강좌로 꽤 정리되어 있으니, 먼저 위 단계 정도를 실습해 보고, 이후 자동 변환 스크립트로 OSINT 데이터를 RDF로 쏟아 넣는 방향을 추천합니다.[^5_16][^5_17][^5_19]

***

## 5. Top‑down 온톨로지 기업 적용 사례

### 5.1 Palantir Foundry식 Top‑down 사례

- Foundry는 먼저 조직 전체 데이터를 통합하고, 그 위에 **비즈니스 Ontology(“디지털 트윈”)를 Top‑down으로 정의**한 뒤, 역할별 에이전트를 배포하는 전략을 씁니다.[^5_8]
- 흐름:

1. 도메인 전문가가 “실제 직원이 머릿속에서 쓰는 언어”를 Ontology로 정리 (주문, 고객, 계약, 생산 등).[^5_8][^5_1]
2. 이 Ontology를 기준으로 데이터셋을 매핑·정규화.
3. 이후 분석·대시보드·AI 에이전트는 모두 이 Ontology를 의존.


### 5.2 국내 엔터프라이즈 적용 예시

- 국내 AI‑ready 데이터 웨비나에서, 해운·제조 등 산업에서 **Top‑down 기업 Ontology**를 정의하고 이를 기반으로 데이터 거버넌스와 AI 프로젝트를 진행한 사례들이 소개됩니다.[^5_12][^5_9]
- 특징:
    - “업무 용어사전 + Ontology”를 먼저 만들고, 그 위에 RAG/LLM/분석을 얹는 구조.
    - 규제·감사·데이터 품질 요구가 강한 도메인(금융·공공·제조)에 특히 잘 맞음.[^5_9][^5_2]

***

## 6. Bottom‑up 온톨로지 OSINT 데이터 처리 워크플로우

Bottom‑up+OSINT 관점에서의 **실무형 파이프라인**을 요약하면 다음과 같습니다.[^5_15][^5_6][^5_10][^5_11]

1. **수집(Collect)**
    - SpiderFoot/Recon‑ng/Shodan/Censys로 기업 관련 도메인·IP·서비스·SNS·뉴스를 크롤링.[^5_5][^5_6][^5_4]
    - 결과는 JSON/CSV 등 구조화 포맷으로 저장.
2. **정규화(Normalize)**
    - 파이프라인(Python, Spark 등)에서 공통 스키마로 맵핑:
        - 예: `organizationName`, `domain`, `ip`, `port`, `product`, `version`, `country`.
    - 이름 정규화/엔티티 중복 제거 (동일 기업의 다양한 표기를 하나로).[^5_15]
3. **개체·관계 추출 (NER/RE)**
    - 뉴스·보고서·웹 텍스트에서 NER/관계 추출 모델로 `Organization`, `Person`, `Product`, `Attack`, `Location` 등을 탐지.[^5_10][^5_15]
4. **트리플화(Triple generation)**
    - `(subject, predicate, object)` 형태로 변환:
        - `AcmeCorp – hasDomain – acme.co.kr`
        - `AcmeCorp – usesTechnologyStack – Apache_HTTP_Server`
        - `AttackX – targets – AcmeCorp`[^5_10][^5_15]
5. **Ontology 후보 자동 생성**
    - 자주 등장하는 엔티티 유형과 관계 패턴을 기반으로 클래스/속성 후보를 자동 추출.[^5_15]
    - 예: `Organization`와 `Domain` 사이의 `hasDomain` 관계가 수십만 번 등장하면 이를 Ontology의 공식 object property로 승격.
6. **Human‑in‑the‑loop 보정**
    - Protégé 등에서 자동 생성된 클래스/관계/트리플을 사람이 검토·정제.[^5_1][^5_19]
7. **저장 및 서비스**
    - Apache Jena/Neo4j에 적재 → SPARQL/Graph 쿼리 서비스 + 검색/추천 서비스 제공.[^5_10][^5_15]

이 워크플로우는 범죄 수사기록 온톨로지 논문에서 제안된 “비정형 기록 → NER/트리플 → Ontology → 검색·추천 서비스” 구조와 상당히 유사하고, 도메인만 기업/공급망/위협으로 바꿔서 그대로 재사용할 수 있습니다.[^5_15][^5_10]

***

여기까지가 전체 그림입니다.
지금 단계에서 가장 도움이 될 것은, 실제로 **“한 도메인(예: 금융 공급망/헬스케어/제조)”을 하나 선택해서 Protégé 클래스 구조 초안을 같이 설계**해 보는 것입니다.

어느 도메인(금융, 헬스케어, 제조, 기타)부터 Ontology 스키마를 같이 잡아볼까요?
<span style="display:none">[^5_20]</span>

<div align="center">⁂</div>

[^5_1]: https://brunch.co.kr/@writerjeong/290

[^5_2]: https://seo.goover.ai/report/202512/go-public-report-ko-41bd26d3-6f3f-4abb-b262-d8a590b820f9-0-0.html

[^5_3]: https://www.unite.ai/ko/best-open-source-intelligence-osint-tools/

[^5_4]: https://www.wiz.io/ko-kr/academy/threat-intel/osint-tools

[^5_5]: https://sh112-kr.tistory.com/30

[^5_6]: https://rninche01.tistory.com/entry/OSINT-정보-수집-도구

[^5_7]: https://www.quryon.com/post/현대적-온톨로지의-3단계-과정

[^5_8]: https://www.valley.town/space/@bspark/articles/69847bc5123b73346660b162

[^5_9]: https://www.youtube.com/watch?v=jpdgUFgnNeE

[^5_10]: https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201910537995953

[^5_11]: https://www.trendmicro.com/ko_kr/what-is/threat-detection/open-source-intelligence-osint.html

[^5_12]: https://www.youtube.com/watch?v=9kldcOTOx7g

[^5_13]: https://koreascience.kr/article/CFKO201832073078879.pdf

[^5_14]: https://www.etnews.com/20251216000045

[^5_15]: https://oak.chosun.ac.kr/bitstream/2020.oak/6901/2/의미적 정보검색을 위한 온톨로지 자동 구축 및 효율적 질의 처리 방법.pdf

[^5_16]: https://wiblee.tistory.com/entry/Protege-튜토리얼-01-프로테제-개요-설치

[^5_17]: https://blog.naver.com/javafile/220938815734

[^5_18]: http://cfs10.blog.daum.net/upload_control/download.blog?fhandle=MEp1SkFAZnMxMC5ibG9nLmRhdW0ubmV0Oi9JTUFHRS8wLzUucGRm\&filename=3.+%EC%98%A8%ED%86%A8%EB%A1%9C%EC%A7%80+%EA%B5%AC%EC%B6%95+%EB%8F%84%EA%B5%AC+-+%EC%9D%B4%EC%9D%B8%EA%B7%BC+2007-11-10.pdf%3Fdownload

[^5_19]: https://www.youtube.com/watch?v=y2oCck1i-FA

[^5_20]: https://www.ibm.com/kr-ko/think/topics/osint


---

# 기업 온톨로지 구축 템플릿: Top-down vs Bottom-up 적용 전략 비교표 및 도구 자동화 로드맵

OSINT 데이터 온톨로지 설계서: 범죄 수사 및 기업 리스크 모델링을 위한 10단계 프로토콜 구축 보고서
금융기관과 공급망 리스크 도메인
헬스케어 장비와 병원 공급망 도메인
제조업 공장과 스마트팩토리 도메인

요청하신 내용을 정리해서, **전략·도메인별로 바로 가져다 쓸 수 있는 설계 가이드** 형태로 답변드립니다.

***

## 1. 기업 온톨로지 구축 템플릿

### Top‑down vs Bottom‑up 전략 비교표 + 자동화 로드맵

### 1.1 전략 비교 템플릿

온톨로지 방법론을 그대로 기업·OSINT 도메인에 옮겨온 비교 템플릿입니다.[^6_1][^6_2]


| 항목 | Top‑down 기업 온톨로지 | Bottom‑up OSINT 주도 온톨로지 |
| :-- | :-- | :-- |
| 출발점 | 비즈니스 개념·업무 모델 | 실제 데이터(OSINT 로그, 크롤링 결과) |
| 설계 방식 | 도메인에서 일반→구체 개념으로 계층 정의(Class → Subclass) | 구체 개념(leaf)·관계 패턴을 먼저 뽑아 상위 개념으로 묶음[^6_1] |
| 장점 | 일관성, 규제·거버넌스 친화, 의사결정 설명 용이[^6_1][^6_2] | 현실 데이터 반영, 빠른 프로토타입, 새로운 패턴 발견에 유리[^6_3] |
| 단점 | 초기 설계 비용 크고 변화 대응 느림 | 중복 개념/관계, 품질·일관성 확보에 사람 개입 필요[^6_1][^6_4] |
| 적합 도메인 | 금융, 공공, 규제 산업, 대형 엔터프라이즈[^6_2][^6_5] | 신생 서비스, 위협 인텔리전스, E‑commerce, 공격 표면 분석[^6_6] |
| 핵심 도구 | 비즈니스 모델링 툴, Protégé, Palantir‑식 Ontology Foundry[^6_1][^6_2] | SpiderFoot, Shodan, Recon‑ng, NER/RE 파이프라인[^6_7][^6_8] |


***

### 1.2 도구 자동화 로드맵 (엔드‑투‑엔드)

**목표**: “기업 온톨로지 + OSINT 수집·분석”을 자동화하는 파이프라인을 단계별로 배치하는 로드맵입니다.[^6_6][^6_2][^6_1]

1. **도메인·개념 설계 (Top‑down 뼈대)**
    - 작업: 금융/헬스케어/제조 각각에 대해 핵심 개체(조직, 계약, 자산, 공급자, 위협)를 명사/동사로 분해 → Ontology의 클래스/관계 정의.[^6_2][^6_1]
    - 도구: Miro/Whimsical + Protégé.[^6_9][^6_10]
2. **OSINT 수집 레이어 (Bottom‑up 데이터)**
    - 작업: SpiderFoot, Shodan/Censys, Recon‑ng 등으로 기업·도메인·IP·서비스·SNS·뉴스 등 수집.[^6_7][^6_8][^6_11]
    - 결과: JSON/CSV 로그.
3. **ETL + 정규화**
    - 작업: 수집 로그를 공통 스키마로 변환 (`organizationName`, `domain`, `ip`, `port`, `product`, `version`, `country` 등).[^6_3][^6_6]
    - 도구: Python/Spark/Beam, Airflow 등.
4. **개체·관계 추출 (NER/Relation Extraction)**
    - 작업: 뉴스·보고서·수사기록·규제문서에서 `Organization`, `Person`, `Device`, `Incident`, `Location` 등을 추출.[^6_4][^6_3]
5. **트리플 생성**
    - 작업: `(subject, predicate, object)` 형태로 그래프화:
        - `BankA – hasSupplier – VendorX`
        - `HospitalY – usesDevice – MRI_123`
        - `FactoryZ – hasExposedService – Modbus_TCP_502`[^6_12][^6_4]
6. **Ontology 매핑**
    - 작업: 생성된 트리플을 Protégé/Apache Jena에서 정의한 클래스/관계에 맞춰 매핑·검증.[^6_13][^6_9][^6_12]
7. **지식그래프 적재**
    - 도구: Apache Jena/Fuseki, Neo4j 등.[^6_2][^6_12]
8. **분석·알림 서비스**
    - 작업: SPARQL/그래프 쿼리로 공급망 리스크, 위협 전파 경로, 장비 의존도 등을 분석.[^6_14][^6_6][^6_2]
9. **거버넌스·보안 계층**
    - 작업: Palantir Foundry 스타일로 Ontology와 데이터 흐름을 세포 단위까지 추적, 권한·감사를 연결.[^6_5][^6_2]
10. **피드백 루프**
    - 작업: 분석 결과/사용자 피드백으로 Ontology 구조와 OSINT 룰셋을 지속적으로 개선.[^6_6][^6_1]

***

## 2. OSINT 데이터 온톨로지 설계서

### 범죄 수사 + 기업 리스크 10단계 프로토콜

범죄 수사기록 온톨로지 논문에서 제시된 “비정형 기록 → 온톨로지 → 검색·추천” 패턴을, 기업 리스크/OSINT 도메인에 일반화한 10단계 프로토콜입니다.[^6_4][^6_12][^6_6]

1. **도메인 경계 정의**
    - 범죄 수사: 침입 절도, 사건, 장소, 피의자.[^6_12][^6_4]
    - 기업: 금융/헬스케어/제조 공급망, 사건(사이버 공격, 장애), 자산, 공급자.[^6_14][^6_6]
2. **시나리오·질문 정의**
    - 예: “어떤 공급자 장애가 어떤 금융상품에 리스크를 주는가?”, “어떤 의료기기 부품 부족이 어떤 병원의 수술에 영향?”[^6_14][^6_2]
3. **개체·관계 목록화 (개념 추출)**
    - 범죄: `Case`, `Suspect`, `Location`, `M.O.`.[^6_12]
    - 기업: `Organization`, `Supplier`, `Contract`, `Device`, `Incident`, `RiskIndicator`.[^6_1][^6_2]
4. **초기 Ontology 구조(TBox) 설계**
    - 클래스, 하위 클래스, Object/Data property 정의.[^6_1][^6_2]
5. **OSINT·내부 로그·문서 수집**
    - OSINT: 도메인·IP·뉴스·SNS·공개 리포트.[^6_8][^6_6]
    - 범죄: 수사기록 텍스트.[^6_4][^6_12]
    - 내부: 금융 트랜잭션, 의료 장비 로그, 생산·장비 유지보수 이력 등.[^6_15][^6_14]
6. **텍스트 처리·NER/RE**
    - 범죄 논문처럼, 개체명 인식·관계 추출로 “문장 → 삼중(triple)” 변환.[^6_3][^6_4][^6_12]
7. **트리플·그래프 생성**
    - 사건/기업/위협 간 관계를 그래프로 구성.[^6_6][^6_4][^6_12]
8. **Reasoner 기반 검증·정제**
    - 일관성 검사, 중복 노드/관계 정리, 규칙 기반 정제.[^6_1][^6_12]
9. **검색·추천·리스크 평가 서비스 연동**
    - 범죄: “비슷한 패턴의 범행 장소 추천” 서비스 구현.[^6_4][^6_12]
    - 기업: “공급망 단절 시 영향 받는 금융상품/병동/라인 추천”, “위협 경로 시뮬레이션”.[^6_2][^6_14]
10. **지속 운영·피드백 사이클**

- OSINT 인텔리전스 사이클처럼, 계획–수집–처리–분석–공유–피드백 루프.[^6_6]

***

## 3. 금융기관 + 공급망 리스크 도메인 스키마 스케치

금융 규제·리스크 도메인에 맞춘 Top‑down 스키마입니다.[^6_5][^6_2][^6_1]

### 3.1 핵심 클래스

- `FinancialInstitution` (은행, 증권, 보험)
- `Service` (결제, 대출, 수탁, 파생상품 등)
- `ThirdPartySupplier` (IT, 통신, 데이터, 클라우드)[^6_5][^6_2]
- `Contract` (SLA, 아웃소싱 계약)
- `Asset` (시스템, 애플리케이션, 데이터셋)
- `Incident` (장애, 사이버 공격, 규제 위반)
- `RiskIndicator` (OSINT 위협, 규제 경고, 평판 리스크)[^6_5][^6_6]


### 3.2 대표 관계

- `FinancialInstitution offers Service`
- `Service dependsOn Asset`
- `Asset providedBy ThirdPartySupplier`
- `Incident impacts Service`
- `Incident hasRootCause Asset`
- `RiskIndicator associatedWith ThirdPartySupplier`

여기에 OSINT로 수집한 `위협 피드(CVE, IOC)`, `뉴스·보고서`를 연결하면,
“특정 클라우드 벤더 장애가 어떤 금융 서비스·상품에 영향을 미치는지”를 지식 그래프로 질의할 수 있습니다.[^6_16][^6_2][^6_6][^6_5]

***

## 4. 헬스케어 장비 + 병원 공급망 도메인 스키마

의료기기 공급망 위기 예방 논의와 헬스케어 온톨로지 연구를 합친 구조입니다.[^6_15][^6_14]

### 4.1 핵심 클래스

- `Hospital`
- `MedicalDevice` (MRI, CT, 모니터, 인공호흡기 등)[^6_14]
- `DeviceComponent` (센서, 칩, 소모품)
- `Supplier` (제조사, 유통사, 원부자재 공급사)
- `ClinicalDepartment` (외과, 내과, 중환자실 등)
- `Procedure` (수술, 검사, 처치)
- `Incident` (장비 고장, 리콜, 공급 중단)
- `RiskIndicator` (OSINT 리콜 정보, 규제 경고, 품질 이슈)[^6_15][^6_14]


### 4.2 대표 관계

- `Hospital owns MedicalDevice`
- `MedicalDevice composedOf DeviceComponent`
- `DeviceComponent suppliedBy Supplier`
- `MedicalDevice usedIn Procedure`
- `Procedure performedAt ClinicalDepartment`
- `Incident affects MedicalDevice`
- `RiskIndicator associatedWith Supplier or MedicalDevice`[^6_15][^6_14]

OSINT에서는 **공개 리콜 공지, 규제기관 발표, 뉴스**를 수집해 `Incident`·`RiskIndicator`로 매핑하고,
“특정 부품 공급 중단이 어떤 병원의 어떤 시술에 영향을 줄지”를 Ontology 기반으로 추론합니다.[^6_6][^6_14]

***

## 5. 제조업 공장 + 스마트팩토리 도메인 스키마

제조·스마트팩토리에서 온톨로지는 설비·라인·공정을 디지털 트윈으로 표현할 때 핵심입니다.[^6_17][^6_2][^6_14]

### 5.1 핵심 클래스

- `Factory`
- `ProductionLine`
- `Machine` (설비, 로봇, PLC, SCADA 노드)
- `Component` (부품, 모듈)
- `Supplier` (부품/장비 공급사)
- `Product`
- `ProcessStep` (가공, 조립, 검사 등)
- `Incident` (고장, 품질 불량, 사이버 공격)
- `RiskIndicator` (OSINT 기반 취약 설비, 부품 수급 이슈)[^6_17][^6_2][^6_14]


### 5.2 대표 관계

- `Factory hasProductionLine ProductionLine`
- `ProductionLine hasMachine Machine`
- `Machine performs ProcessStep`
- `Product producedBy ProductionLine`
- `Component usedIn Machine`
- `Component suppliedBy Supplier`
- `Incident affects Machine or ProductionLine`
- `RiskIndicator associatedWith Supplier or Machine`

Shodan/Censys 같은 OSINT를 활용하면 공장 설비의 노출 서비스·취약 버전 정보를 `RiskIndicator`로 연결해,
“어떤 설비가 노출돼 있고, 그 설비가 어느 라인·어떤 제품에 영향을 주는지”를 지식 그래프로 분석할 수 있습니다.[^6_8][^6_17][^6_2]

***

## 6. 이걸 어떻게 시작할까? (실행 제안)

1. 위 세 도메인 중 **한 도메인**을 먼저 선택해, Protégé에서 TBox(클래스/관계)만 정의.[^6_18][^6_9][^6_1]
2. 선택한 도메인에 맞춰 **SpiderFoot + Shodan + 뉴스 크롤러** 조합으로 OSINT 샘플 1~2개 기업을 수집.[^6_7][^6_8][^6_6]
3. 간단한 Python 스크립트로 **CSV → Turtle(RDF)** 트리플 변환 후 Protégé/Jena에 로드해서 “작은 지식 그래프”를 띄워 보는 것을 1차 목표로 두는 것을 추천합니다.[^6_13][^6_12][^6_4]

지금 세 도메인(금융·헬스케어·제조) 중에서, 실제로 **PoC를 먼저 해 보고 싶은 도메인 하나**를 골라 주시면,
그 도메인에 맞춰 “Protégé에 그대로 찍어 넣을 수 있는 클래스/속성 리스트 + 예시 트리플 세트”까지 구체적으로 작성해 드리겠습니다.
<span style="display:none">[^6_19][^6_20][^6_21][^6_22][^6_23][^6_24]</span>

<div align="center">⁂</div>

[^6_1]: https://brunch.co.kr/@writerjeong/290

[^6_2]: https://www.cncf.co.kr/ebook/graphdb/part2-graph-db-usecases-ecosystem/4-ontology-and-knowledge-graph/4-1-palantir-ontology/

[^6_3]: https://oak.chosun.ac.kr/bitstream/2020.oak/6901/2/의미적 정보검색을 위한 온톨로지 자동 구축 및 효율적 질의 처리 방법.pdf

[^6_4]: https://accesson.kr/kslis/assets/pdf/9550/journal-53-1-57.pdf

[^6_5]: https://goldenrabbit.co.kr/articles/Zbi2HBg3Pcu0RVWzxIxK

[^6_6]: https://www.trendmicro.com/ko_kr/what-is/threat-detection/open-source-intelligence-osint.html

[^6_7]: https://www.wiz.io/ko-kr/academy/threat-intel/osint-tools

[^6_8]: https://rninche01.tistory.com/entry/OSINT-정보-수집-도구

[^6_9]: https://wiblee.tistory.com/entry/Protege-튜토리얼-01-프로테제-개요-설치

[^6_10]: https://blog.naver.com/javafile/220938815734

[^6_11]: https://sh112-kr.tistory.com/30

[^6_12]: https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201910537995953

[^6_13]: http://cfs10.blog.daum.net/upload_control/download.blog?fhandle=MEp1SkFAZnMxMC5ibG9nLmRhdW0ubmV0Oi9JTUFHRS8wLzUucGRm\&filename=3.+%EC%98%A8%ED%86%A8%EB%A1%9C%EC%A7%80+%EA%B5%AC%EC%B6%95+%EB%8F%84%EA%B5%AC+-+%EC%9D%B4%EC%9D%B8%EA%B7%BC+2007-11-10.pdf%3Fdownload

[^6_14]: https://www.hankyung.com/article/2026060501461

[^6_15]: https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201206735658279

[^6_16]: https://talkit.tv/Talk/73838?TAG=\&SearchText=\&CurrentPage=10

[^6_17]: https://www.youtube.com/watch?v=NMSZuS4wW6Q

[^6_18]: https://www.youtube.com/watch?v=y2oCck1i-FA

[^6_19]: https://seulkom.tistory.com/64

[^6_20]: https://swimlane.com/ko/블로그/ai를-활용한-수사-조율/

[^6_21]: https://s2w.inc/ko/resource/detail/972

[^6_22]: https://blog.naver.com/simula/224077550337

[^6_23]: https://swimmingindev.tistory.com/63

[^6_24]: http://www.prism.go.kr/homepage/researchCommon/downloadResearchAttachFile.do;jsessionid=F4D558C72936296347BBC6724ED2AACC.node02?work_key=000\&file_type=USR\&seq_no=001\&pdf_conv_yn=N\&research_id=1290000-201800075\&usg=AOvVaw2MpFMq_-u9CLwKyZhd-RCP


---

# 실제 대규모 데이터 도메인에서 Top-down 및 Bottom-up 온톨로지 하이브리드 설계 시 발생하는 현실적인 기술적 상충 관계와 해결 전략

기업 공급망 리스크 분석을 위한 지식 그래프 시각화 도구 추천
비정형 텍스트 데이터에서 관계 추출을 위한 NLP 라이브러리 비교
지식 그래프 기반의 위협 인텔리전스 플랫폼 구축 아키텍처

대규모 도메인에서 온톨로지를 하이브리드로 설계할 때의 핵심 문제는, **Top-down의 통제력**과 **Bottom-up의 적응성**이 서로 충돌한다는 점입니다. 실제로는 스키마를 먼저 고정하면 현장 데이터의 변화 속도를 못 따라가고, 반대로 데이터에서만 출발하면 스키마 표류와 품질 저하가 생기므로, “상위 개념은 안정화하고 하위 관계와 인스턴스는 점진적으로 진화시키는 이중 운영 모델”이 가장 현실적입니다.[^7_1][^7_2][^7_3]

## 하이브리드 상충

가장 흔한 기술적 상충 관계는 4가지입니다. 첫째, **스키마 안정성 vs 확장성**으로, 기업은 규제·거버넌스 때문에 안정된 개념 체계를 원하지만 대규모 OSINT와 비정형 데이터는 새 엔티티와 관계를 계속 만들어 냅니다. 둘째, **정밀도 vs 커버리지**로, 엄격한 온톨로지 제약은 정확도를 높이지만 실제 텍스트에서 나오는 변형 표현·은유·불완전 문장을 많이 버리게 되고, 완화하면 노이즈가 급증합니다.[^7_2][^7_4][^7_3][^7_1]

셋째, **추론 가능성 vs 처리 비용**입니다. RDF/OWL 기반의 정교한 모델은 제약 검증과 추론에 강점이 있지만, 대규모 문서·이벤트·OSINT 피드를 실시간에 가깝게 적재하고 질의할 때는 비용과 지연이 커집니다. 넷째, **전문가 주도 설계 vs 자동 추출 파이프라인**의 충돌로, 범죄 수사기록 온톨로지 사례에서도 주제전문가·형사·기술연구자가 반복 회의를 통해 클래스 트리와 제약조건을 정의했고, 구축에 약 9개월이 들었습니다.[^7_3][^7_5]

## 해결 전략

실무적으로는 **3계층 모델**이 효과적입니다. 상위 계층은 `Organization`, `Incident`, `Supplier`, `Asset`, `RiskIndicator` 같은 안정 클래스만 Top-down으로 고정하고, 중간 계층은 도메인별 속성·관계를 버전 관리하며, 하위 계층은 Bottom-up으로 추출된 관계 후보를 샌드박스 영역에서 검증한 뒤 승격하는 방식입니다.[^7_6][^7_1][^7_2]

데이터 파이프라인은 `추출 → 정의 → 정규화 → 검증 → 승격` 구조로 짜는 편이 안전합니다. LLM 기반 KG 구축 조사에서도 스키마 없는 추출 뒤 의미 정의와 정규화(canonicalization)를 거쳐 기존 온톨로지와 정렬하거나 새 온톨로지를 생성하는 접근이 중요하다고 설명하며, 스키마 표류 대응과 실시간 스키마 진화를 핵심 과제로 봅니다. 따라서 운영 정책도 “자동 생성=즉시 반영”이 아니라, 관계 후보를 점수화하고 증거 문장과 출처를 남긴 뒤 승인 임계치를 통과한 것만 본 스키마에 반영하는 방식이 바람직합니다.[^7_7][^7_2]

## 시각화 도구

기업 공급망 리스크 분석용 지식 그래프 시각화 도구는 용도별로 나눠 고르는 것이 좋습니다. **Neo4j Bloom**은 비개발자도 탐색하기 쉬운 비즈니스 친화형 시각화에 적합하고, **Graphistry**는 대규모 엣지 렌더링과 GPU 기반 탐색에 강하며, **Linkurious Enterprise**는 조사·수사형 탐색 UX에 강점이 있어 공급망 리스크와 위협 전파 경로 분석에 잘 맞습니다.[^7_8][^7_9]

LLM·검색 결합형이라면 **Amazon Neptune + GraphRAG Toolkit** 조합도 유력합니다. AWS는 공급망, 조직 구조, 규제처럼 여러 문서에 걸친 복잡한 관계를 다룰 때 GraphRAG가 필요하다고 설명하고, Neptune 그래프와 OpenSearch 벡터 스토어를 함께 써서 구조적 연결과 의미 검색을 결합하는 아키텍처를 제시합니다. 특히 엔티티 네트워크 시각화를 통해 질문과 직접 단어가 닿지 않는 리스크도 구조적으로 드러낼 수 있어, 공급망 차질·서드파티 리스크 분석에 적합합니다.[^7_5]

## NLP 라이브러리

비정형 텍스트에서 관계 추출을 위한 라이브러리는 목적에 따라 선택해야 합니다. **spaCy**는 속도와 실서비스 적용성이 강점이라 대량 전처리·NER·파이프라인 운영에 유리하고, **NLTK**는 교육용·기초 처리엔 폭넓지만 대규모 실무 처리 속도는 상대적으로 아쉽다는 평가가 있습니다. **Transformer 계열 라이브러리**는 문맥과 토큰 간 관계를 계산하는 데 강해 관계 추출 품질 측면에서 유리하며, IBM도 비정형 데이터에서 의미와 메타데이터를 추출하는 방향으로 NLP 라이브러리를 설명합니다.[^7_10][^7_11][^7_4][^7_12]

실무 조합으로는 보통 이렇게 갑니다.

- 대량 전처리: spaCy, 빠른 문장 분리·토큰화·기초 NER.[^7_10]
- 도메인 적응형 추출: Hugging Face Transformers/BERT 계열, instruction tuning 또는 few-shot RE.[^7_4][^7_2]
- 규칙 보강: 정규식·사전·ontology snippet, 고정 패턴 관계 보정.[^7_2]
- 토픽 보조: Gensim, 주제 클러스터링과 문서 묶음 탐색.[^7_10]


## 플랫폼 아키텍처

지식 그래프 기반 위협 인텔리전스 플랫폼은 보통 **수집층, 추출층, 그래프층, 검색층, 분석층**으로 나뉩니다. 수집층은 OSINT·내부 로그·보고서·뉴스를 받고, 추출층은 엔티티/관계/속성 추출과 엔터티 정렬을 수행하며, 그래프층은 Neptune·Neo4j·RDF 스토어에 적재하고, 검색층은 벡터 검색과 그래프 탐색을 결합하며, 분석층은 리스크 탐지·케이스 관리·설명 가능한 질의를 제공합니다.[^7_13][^7_7][^7_5]

AWS의 GraphRAG 예시 아키텍처는 이 구조를 잘 보여 줍니다. 문서가 들어오면 LLM이 엔티티와 관계를 추출해 Neptune에 저장하고, 텍스트 청크 임베딩은 OpenSearch에 저장하며, 질의 시에는 top-k 유사도 검색으로 진입점을 찾은 뒤 그래프 탐색으로 구조적 맥락을 확장해 최종 답변을 생성합니다. 이 방식은 “영국 판매 전망” 질문에서 물류 파트너와 운하 막힘 같은 구조적 리스크를 찾아내는 예로 설명되며, 단순 벡터 검색보다 공급망·위협 인텔리전스에 적합하다고 제시됩니다.[^7_5]

원하시면 다음 단계로 **금융기관 공급망 리스크용 참조 아키텍처** 또는 **헬스케어/제조용 엔티티-관계 스키마 초안**을 바로 그려드릴 수 있습니다.
<span style="display:none">[^7_14][^7_15][^7_16][^7_17][^7_18]</span>

<div align="center">⁂</div>

[^7_1]: https://brunch.co.kr/@writerjeong/290

[^7_2]: https://www.themoonlight.io/ko/review/llm-empowered-knowledge-graph-construction-a-survey

[^7_3]: https://www.ibm.com/kr-ko/think/topics/osint

[^7_4]: https://www.ibm.com/kr-ko/think/topics/natural-language-processing

[^7_5]: https://myeverythingdocument.tistory.com/43

[^7_6]: https://www.oreilly.com/library/view/simaentig-deiteo-mohyeonghwa/9791162245361/chapter-56.html

[^7_7]: https://www.themoonlight.io/ko/review/enhancing-supply-chain-transparency-in-emerging-economies-using-online-contents-and-llms

[^7_8]: https://skywork.ai/skypage/ko/AI 엔지니어를 위한 MCP 지식 그래프 서버 심층 분석: 개념부터 실제 구현까지/1972115402030022656

[^7_9]: https://www.cas.org/ko/solutions/cas-scifinder-discovery-platform/knowledge-graph

[^7_10]: https://jaayy.tistory.com/101

[^7_11]: https://www.ibm.com/kr-ko/products/natural-language-processing

[^7_12]: https://dsbook.tistory.com/329

[^7_13]: https://www.trendmicro.com/ko_kr/what-is/threat-detection/open-source-intelligence-osint.html

[^7_14]: https://velog.io/@joongwon00/번역Construction-and-Application-of-a-Knowledge-Graph

[^7_15]: https://aws.amazon.com/ko/blogs/tech/introducing-the-graphrag-toolkit-03/

[^7_16]: https://www.sailpoint.com/ko/identity-library/structured-unstructured-data

[^7_17]: https://www.databricks.com/kr/blog/2022/06/17/using-a-knowledge-graph-to-power-a-semantic-data-layer-for-databricks.html

[^7_18]: https://publish.obsidian.md/datawave/데이터+클래스/데이터+클래스+Chapter+1


---

# 위협 인텔리전스 그래프 모델링을 위한 STIX/TAXII 활용법

STIX/TAXII는 위협 인텔리전스를 **표준 스키마(STIX)와 전송 프로토콜(TAXII)**로 통합해 주기 때문에, 그래프 모델링에서 “노드·엣지 타입을 거의 그대로 가져다 쓰는 표준 온톨로지 + 배치/스트리밍 수집 채널”로 활용하는 것이 핵심입니다.[^8_1][^8_2]

***

## 1. STIX/TAXII 개념을 그래프 모델에 옮기기

### 1.1 역할 정리

- **STIX (Structured Threat Information eXpression)**
    - 사이버 위협 인텔리전스를 표현하는 JSON 기반 언어로, IOC·위협 행위자·캠페인·공격 기법·관계 등을 객체와 링크로 구조화합니다.[^8_1][^8_2]
    - “위협 지표, 사고, 데이터 유출을 설명하기 위한 공통 언어”를 제공하고, 권장 데이터 모델·어휘 세트를 포함합니다.[^8_1]
- **TAXII (Trusted Automated eXchange of Indicator Information)**
    - HTTPS를 통해 STIX 객체를 교환하기 위한 API/프로토콜입니다.[^8_3][^8_2]
    - TAXII 서버는 STIX 컬렉션을 호스팅하고, 클라이언트는 컬렉션을 주기적으로 폴링해 위협 지표를 자동 수집합니다.[^8_4][^8_3]

즉, **STIX = 그래프 스키마 + 데이터 모델, TAXII = 수집 파이프라인 프로토콜**이라고 보면 됩니다.[^8_2][^8_1]

***

## 2. STIX 기반 그래프 스키마 설계

### 2.1 STIX 객체 → 노드/엣지 매핑

STIX 2.x는 `type` 필드로 객체 유형을 정의합니다. 위협 인텔리전스 그래프에서는 보통 다음처럼 매핑합니다.[^8_1][^8_2]

- **노드(Node)로 모델링할 STIX 객체 예시**
    - `indicator` (IOC: IP, 도메인, 해시 등)
    - `malware`, `tool`, `vulnerability`
    - `threat-actor`, `intrusion-set`, `campaign`, `attack-pattern`
    - `identity` (조직/국가/피해자)
    - `infrastructure`, `observed-data`, `incident/event` 등[^8_2][^8_5]
- **엣지(관계)로 모델링할 STIX 객체**
    - `relationship` (ex: *threat-actor uses malware*, *malware targets identity*)
    - `sighting` (ex: *indicator observed-in organization*)
    - 이들은 보통 `source_ref`, `target_ref`, `relationship_type`로 표현되므로, 그래프에서 **유형이 있는 에지**로 구현합니다.[^8_2]

그래프 DB 기준 예시:

- Node labels: `ThreatActor`, `Indicator`, `Malware`, `Campaign`, `Vulnerability`, `Identity`, `Infrastructure` …
- Edge types:
    - `USES`, `TARGETS`, `ATTRIBUTED_TO`, `DELIVERS`, `EXPLOITS`, `HAS_SIGHTING`, `RELATED_TO` 등
    - STIX `relationship_type`를 그대로 edge label 또는 property로 넣습니다.[^8_6][^8_2]


### 2.2 속성과 메타데이터

각 노드는 STIX 필드를 속성으로 가집니다.

- 공통: `id`, `created`, `modified`, `labels`, `confidence`, `created_by_ref`[^8_1]
- IOC: `pattern` (예: `[ipv4-addr:value = '1.2.3.4']`), `valid_from`, `valid_until`.
- Threat Actor: `name`, `aliases`, `roles`, `goals`, `sophistication`, `resource_level`, `primary_motivation` 등.[^8_2]

이 메타데이터는 **그래프 상에서 필터·스코어·시각화 스타일**에 활용합니다 (예: confidence에 따라 edge 굵기/색상 차등).[^8_1][^8_2]

***

## 3. TAXII로 그래프에 데이터 흘려 넣기

### 3.1 TAXII 수집 파이프라인

- TAXII 서버는 STIX 컬렉션을 REST API로 제공합니다 (API Root, Collection ID 필요).[^8_4]
- 클라이언트(예: TIP, SIEM, 자체 파이프라인)는 폴링 빈도·필터를 설정해 STIX 번들을 주기적으로 가져옵니다.[^8_7][^8_4]
- Microsoft Sentinel 등의 SIEM은 기본 TAXII 클라이언트를 제공하고, API Root URL·컬렉션 ID·자격 증명을 입력하면 STIX 위협 지표를 자동 수집하도록 지원합니다.[^8_4]

일반적인 워크플로:

1. TAXII 서버에서 컬렉션/엔드포인트 정보(API Root, Collection ID) 확보.[^8_4]
2. TAXII 클라이언트(직접 구현 또는 플랫폼 내 커넥터)로 STIX 번들을 폴링/구독.[^8_3][^8_4]
3. 수집된 STIX JSON을 **ETL 계층에서 파싱 → 그래프 변환**.[^8_3]

***

## 4. 그래프 모델링 활용 전략

### 4.1 위협 헌팅/탐색을 위한 시각 그래프

- 노드: 위협 행위자, 캠페인, 악성코드, IOC, 취약점, 피해 조직.
- 에지: `USES`, `DELIVERS`, `TARGETS`, `COMPROMISES`, `ASSOCIATED_WITH`.
- 간단한 질문:
    - “이 IOC와 연관된 공격 캠페인과 행위자는 누구인가?”
    - “최근 7일 내 우리 자산에서 관측된 IOC가 속한 행위자 세트는?”
- 시각화 도구: Neo4j Bloom, Linkurious, Graphistry, 혹은 TIP 제품 내 위협 그래프 뷰어.[^8_7][^8_8][^8_9]


### 4.2 SIEM/SOAR와의 연계

- STIX/TAXII 피드를 통해 **지표를 중앙 TIP 또는 SIEM으로 수집** 후,
    - 방화벽·메일 게이트웨이·EDR에 자동 전파 (차단·경고 룰 동기화).[^8_10][^8_11]
    - SOC 플레이북(SOAR)에서 STIX 객체 ID를 기반으로 enrichment (예: 알람 IOC에 연결된 캠페인, 행위자, CVE 인출).[^8_12][^8_11]
- 국내 연구에서도 STIX/TAXII 기반 지표를 내부 자산 정보와 연계해 TTP 대응 자동화 시스템을 설계한 사례가 있습니다.[^8_12]

***

## 5. STIX를 그래프 온톨로지와 정렬할 때의 팁

1. **STIX를 그대로 상위 온톨로지로 본다**
    - 위협 인텔리전스 영역에서는 STIX의 객체 타입이 사실상 업계 표준 상위 온톨로지 역할을 합니다.[^8_1][^8_5]
    - 도메인 별로 확장이 필요하면, STIX 타입을 상속하거나 별도 네임스페이스를 둡니다 (예: `FinancialInstitution`, `MedicalDevice`, `Factory` 등).
2. **관계 중심 모델링**
    - STIX 관계·sighting 객체를 그래프 엣지에 충실히 매핑하면, “누가 무엇을 누구에게 사용했는지”를 자연스럽게 나타낼 수 있습니다.[^8_2][^8_6]
    - 위협 인텔리전스 그래프는 주로 경로 길이, 연결 컴포넌트, 중심성 분석에 많이 쓰이므로, 관계 정의가 가장 중요합니다.
3. **시간·버전 관리**
    - STIX 객체는 `created`, `modified`, `valid_from/valid_until` 등 시간 정보를 가지고 있어, 시계열 그래프 분석이나 히스토리 뷰(과거 캠페인 vs 현재)를 구현할 수 있습니다.[^8_1]

***

## 6. 실무용 설계 예시(요약)

위협 인텔리전스 그래프를 설계한다고 할 때, 실무 모델은 대략 다음과 같이 가져갈 수 있습니다.

- 노드 타입
    - `ThreatActor`, `Campaign`, `Malware`, `Tool`, `TTP(AttackPattern)`, `Indicator`, `Vulnerability`, `Identity(Org, Country)`, `Infrastructure`, `Incident`.
- 엣지 타입 (STIX relationship_type 기반)
    - `USES`, `TARGETS`, `DELIVERS`, `EXPLOITS`, `ATTRIBUTED_TO`, `COMPROMISES`, `HAS_SIGHTING`, `RELATED_TO`.
- 데이터 플로우
    - TAXII→STIX 번들 수집→파서→그래프 적재→SIEM/TIP/대시보드에서 활용.[^8_1][^8_3][^8_4][^8_7]

이렇게 설계하면, STIX/TAXII의 장점인 표준화된 CTI 표현/전송을 최대한 활용하면서, 지식 그래프 상에서 **공격 캠페인–행위자–IOC–취약점–피해 자산**의 전체 맥락을 탐색·분석할 수 있습니다.[^8_2][^8_11][^8_1]

지금 고민하시는 환경이 어떤 쪽에 더 가까운지(예: “Neo4j 기반 자체 TIP” vs “Sentinel/Elastic 기반 SIEM 확장”) 알려주시면, 해당 스택 기준으로 **스키마 예시와 TAXII 수집 파이프라인 설계**를 구체적인 필드 이름까지 맞춰서 정리해 드리겠습니다.

<div align="center">⁂</div>

[^8_1]: https://www.cloudflare.com/ko-kr/learning/security/what-is-stix-and-taxii/

[^8_2]: https://www.servicenow.com/docs/r/ko-KR/xanadu/security-management/threat-intelligence-security-center/threat-intelligence-security-center-feeds.html

[^8_3]: https://ipsj.ixsq.nii.ac.jp/ej/index.php?action=pages_view_main\&active_action=repository_action_common_download\&item_id=192110\&item_no=1\&attribute_id=1\&file_no=1\&page_id=13\&block_id=8

[^8_4]: https://learn.microsoft.com/ko-kr/azure/sentinel/connect-threat-intelligence-taxii

[^8_5]: https://www.servicenow.com/docs/r/e8KCYd_XhQq4ntf0n2C3CQ/G5IIr7Cg4xkDx7ykQ1RfYg

[^8_6]: https://velog.io/@crowndaisy/STIXTAXII

[^8_7]: https://stellarcyber.ai/ko/platform/platform-threat-intelligence/

[^8_8]: https://skywork.ai/skypage/ko/AI 엔지니어를 위한 MCP 지식 그래프 서버 심층 분석: 개념부터 실제 구현까지/1972115402030022656

[^8_9]: https://www.cas.org/ko/solutions/cas-scifinder-discovery-platform/knowledge-graph

[^8_10]: https://www.reddit.com/r/cybersecurity/comments/u1czmk/stix_taxii/

[^8_11]: https://blog.alyac.co.kr/2372

[^8_12]: https://scholar.kyobobook.co.kr/article/detail/4040070410697


---

# STIX 기반의 커스텀 위협 인텔리전스 모델링 예시가 필요

STIX를 그대로 쓰지 않고 **도메인·내부 자산에 맞게 확장한 커스텀 위협 인텔리전스 모델**을 만들려면,

1) STIX의 객체·관계 구조를 “코어 온톨로지”로 삼고,
2) 거기에 기업 맥락(자산, 공급망, 비즈니스 영향)을 붙이는 식으로 설계하는 게 가장 안전합니다.[^9_1][^9_2]

아래에 **STIX 기반 커스텀 모델링 예시 3개**를 단계별로 정리합니다.

***

## 1. 기본 아이디어: STIX를 상위 스키마로, 기업 맥락을 하위 스키마로

STIX 2.x는 위협 인텔리전스용 객체(Threat Actor, Campaign, Indicator, Malware, Vulnerability 등)와 관계(relationship, sighting)를 표준화된 JSON 구조로 제공합니다.[^9_3][^9_1]

- **장점**
    - 위협 인텔리전스 도메인의 공통 언어를 제공 (표준 타입·필드·관계).[^9_1]
    - OASIS STIX 예시에는 실제 위협 리포트를 STIX 2.1로 변환한 JSON이 포함돼 있어, “현실적인 모델링 패턴”을 그대로 참고할 수 있습니다.[^9_3]
- **커스텀 모델링 방향**
    - STIX 객체는 **위협·IOC·행위자·캠페인 등 “외부 세계”**를 모델링.
    - 별도의 커스텀 클래스는 **자산·서비스·비즈니스·규제·위험도 등 “내부 세계”**를 모델링.
    - 둘 사이를 “연계 관계”로 묶어서, STIX 데이터가 단순 IOC 목록이 아니라 **비즈니스 리스크 그래프**의 일부가 되게 합니다.[^9_4]

***

## 2. 예시 1: 금융기관 + 공급망 커스텀 CTI 모델

### 2.1 핵심 개체

- STIX 코어
    - `threat-actor`, `campaign`, `malware`, `indicator`, `vulnerability(CVE)`, `attack-pattern`, `infrastructure`, `identity`.[^9_3][^9_1]
- 커스텀 엔티티 (내부)
    - `FinancialInstitution`, `BusinessService` (인터넷뱅킹, 카드결제 등),
    - `ThirdPartySupplier` (클라우드, 결제대행, 코어뱅킹 벤더),
    - `ITAsset` (시스템, 호스트, 애플리케이션),
    - `Control` (방화벽 정책, EDR 룰, MFA 정책 등),
    - `RiskScore` (자산·서비스별 산출 점수).[^9_4]


### 2.2 관계 설계 예시

- STIX 내부 관계 (표준)
    - `ThreatActor -[USES]-> Malware`
    - `Malware -[DELIVERS]-> AttackPattern`
    - `Campaign -[TARGETS]-> Identity(Bank)`
    - `Indicator -[INDICATES]-> Malware/Vulnerability`
    - `Sighting(Indicator, ITAsset)` → 그래프에선 `Indicator -[SIGHTED_ON]-> ITAsset`.[^9_2][^9_3]
- 커스텀 관계 (기업 맥락)
    - `FinancialInstitution -[OFFERS]-> BusinessService`
    - `BusinessService -[DEPENDS_ON]-> ITAsset`
    - `ITAsset -[RUNS_ON]-> ThirdPartySupplier`
    - `ITAsset -[HAS_CONTROL]-> Control`
    - `Vulnerability(CVE) -[AFFECTS]-> ITAsset`
    - `RiskScore -[ASSIGNED_TO]-> BusinessService/ITAsset`.[^9_4]

이렇게 모델링하면, 예를 들어:

> 특정 TAXII 피드에서 CVE-2025-XXXX 취약점을 악용하는 캠페인이 탐지되었을 때,
> 해당 CVE가 영향을 주는 내부 ITAsset들과 그 자산이 담당하는 BusinessService(예: 외환결제)를 경로 탐색으로 바로 도출.

할 수 있습니다. 연구 사례에서도 **외부 STIX/TAXII 기반 CTI + 내부 자산 정보를 연계**해 위험도를 산출하고 대응 우선순위를 정하는 프레임워크를 제안합니다.[^9_4]

***

## 3. 예시 2: 제조/스마트팩토리 OT 위협 CTI 모델

### 3.1 STIX + OT 커스텀 개체

- STIX
    - `malware`, `tool`, `indicator`, `intrusion-set`, `attack-pattern`, `vulnerability`, `infrastructure`.[^9_1][^9_3]
- OT 커스텀
    - `Factory`, `ProductionLine`, `OTAsset(PLC, HMI, SCADA node)`,
    - `Component` (펌웨어, 모듈, OS 이미지),
    - `Supplier` (장비/부품 공급사),
    - `SafetyImpact` (안전/품질/생산 영향 카테고리).


### 3.2 모델링 예시 시나리오

- STIX 영역
    - `Malware: OT_Ransom_X` (OT용 랜섬웨어)
    - `AttackPattern: ICS_Command_Abuse`
    - `Vulnerability: CVE-2026-12345` (특정 PLC 펌웨어 취약점)
    - `IntrusionSet: GROUP_ICS_A`
    - `Indicator: 악성 C2 도메인 및 해시`.
- OT 영역 및 연결
    - `OTAsset: PLC_1` (ProductionLine_A에서 사용, 펌웨어 버전 X)
    - `OTAsset: HMI_2` (같은 라인)
    - `ProductionLine_A -[LOCATED_IN]-> Factory_Seoul`
    - `OTAsset -[SUPPLIED_BY]-> Supplier_Y`.
- 관계
    - `Malware OT_Ransom_X -[EXPLOITS]-> CVE-2026-12345`
    - `CVE-2026-12345 -[AFFECTS]-> OTAsset(PLC_1)`
    - `IntrusionSet GROUP_ICS_A -[USES]-> Malware OT_Ransom_X`.

이렇게 되면, 새 TAXII 피드에서 `OT_Ransom_X`나 해당 CVE를 언급하는 STIX 객체가 들어왔을 때,
**어떤 라인/공장/제품에 다운타임 리스크가 생기는지**를 그래프 탐색으로 직관적으로 볼 수 있습니다.

***

## 4. 예시 3: 헬스케어 장비·병원 공급망 CTI 모델

### 4.1 엔티티

- STIX
    - `malware`, `indicator`, `vulnerability`, `attack-pattern`, `threat-actor`, `identity(병원/벤더)`, `infrastructure`.[^9_3][^9_1]
- 헬스케어 커스텀
    - `Hospital`, `MedicalDevice` (MRI, CT, infusion pump 등),
    - `DeviceComponent` (보드, OS, 미들웨어),
    - `Vendor` (제조사·유통사),
    - `ClinicalDepartment`, `Procedure` (수술·검사),
    - `PatientSafetyImpact` (치명/중간/경미).


### 4.2 관계 예시

- `MedicalDevice -[HAS_COMPONENT]-> DeviceComponent`
- `DeviceComponent -[HAS_VULNERABILITY]-> Vulnerability(CVE)`
- `Vulnerability -[EXPLOITED_BY]-> Malware`
- `ThreatActor -[TARGETS]-> Hospital`
- `MedicalDevice -[USED_IN]-> Procedure`
- `Procedure -[PERFORMED_AT]-> ClinicalDepartment`.

STIX CTI 피드에서 특정 의료기기 취약점이나 헬스케어를 타깃으로 한 랜섬웨어 캠페인이 등장하면,
“어떤 병원, 어떤 장비, 어떤 시술에 안전 리스크가 생기는지”를 한눈에 분석할 수 있습니다.

***

## 5. STIX 객체 레벨에서 커스텀 필드를 붙이는 방법(간단 예시)

STIX는 **Extension** 메커니즘으로 커스텀 필드를 추가할 수 있습니다.[^9_1]

예를 들어, 금융기관용 커스텀 Indicator:

```json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--1234...",
  "created": "2026-06-18T10:00:00Z",
  "modified": "2026-06-18T10:00:00Z",
  "name": "Malicious IP used in card fraud",
  "pattern": "[ipv4-addr:value = '203.0.113.10']",
  "pattern_type": "stix",
  "valid_from": "2026-06-18T09:00:00Z",
  "labels": ["malicious-activity", "fraud"],
  "extensions": {
    "x-org-risk-extension": {
      "extension_type": "property-extension",
      "business_services_at_risk": ["CardAuthorization", "InternetBanking"],
      "risk_score": 85,
      "internal_asset_ids": [
        "it-asset--abcd-efgh..."
      ]
    }
  }
}
```

- 여기서 `x-org-risk-extension`은 STIX 스펙에서 허용하는 **커스텀 확장 네임스페이스**이고,[^9_2][^9_1]
- 내부 그래프에서는 `business_services_at_risk`를 `Indicator -[IMPACTS]-> BusinessService` 관계로 풀어낼 수 있습니다.

***

## 6. 참고용 공식 STIX 예시

OASIS CTI TC가 제공하는 **STIX 2.1 Examples** 페이지에는 실제 위협 리포트를 STIX로 모델링한 JSON 예시가 다수 포함돼 있습니다.[^9_3]

- APT1 리포트 JSON: Campaign, Threat Actor, Indicator, Attack Pattern, Malware, Intrusion Set 등을 어떻게 엮는지 보여줌.[^9_3]
- Poison Ivy 리포트 JSON: 다양한 Malware 버전과 Campaign·Threat Actor·Vulnerability를 연결하는 패턴 예시.[^9_3]

이 예시들을 그대로 **그래프 노드/관계로 시각화**한 뒤, 위에서 제안한 `BusinessService`·`ITAsset`·`RiskScore` 같은 커스텀 노드를 붙여 보면,
STIX 기반 커스텀 위협 인텔리전스 모델이 어떤 모습이 될지 감이 바로 잡힐 것입니다.

***

만약 지금 당장 PoC를 해보신다면, 어떤 도메인(금융/헬스케어/제조)부터 실제 JSON 스키마와 그래프 노드/관계 정의를 “복붙 가능한 수준”으로 받고 싶으신가요?
그 한 도메인을 골라 주시면, STIX 예시 JSON + 커스텀 필드 + 그래프 스키마를 한 세트로 묶어서 설계해 드리겠습니다.
<span style="display:none">[^9_10][^9_5][^9_6][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://www.cloudflare.com/ko-kr/learning/security/what-is-stix-and-taxii/

[^9_2]: https://velog.io/@crowndaisy/STIXTAXII

[^9_3]: https://oasis-open.github.io/cti-documentation/stix/examples.html

[^9_4]: https://koreascience.kr/article/JAKO202404357603499.pub?lang=ko

[^9_5]: https://stellarcyber.ai/ko/platform/platform-threat-intelligence/

[^9_6]: https://dcollection.korea.ac.kr/srch/srchDetail/000000289843

[^9_7]: https://learn.microsoft.com/ko-kr/azure/sentinel/connect-threat-intelligence-taxii

[^9_8]: https://blog.alyac.co.kr/2372

[^9_9]: https://tech.somma.kr/STIX2/

[^9_10]: https://journal.kci.go.kr/kiots/archive/articlePdf?artiId=ART003237107

