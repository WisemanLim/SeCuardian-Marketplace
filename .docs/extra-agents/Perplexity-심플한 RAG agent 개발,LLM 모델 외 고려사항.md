<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 심플한 RAG agent를 개발하고자 합니다. LLM 모델외에 고려해야 하는 사항과 구현방향을 알려주세요

심플한 RAG agent를 만들 때도 핵심은 “LLM + 벡터DB”가 아니라, **검색 품질·문서 처리·근거 제시·운영 평가**까지 포함한 전체 파이프라인을 설계하는 것입니다. 특히 단순 벡터 검색만으로 끝내기보다, 질의 라우팅·하이브리드 검색·재정렬·메타데이터 필터링을 최소 단위로 고려해야 실제 정확도가 안정됩니다.[^1_1][^1_2]

## 구성요소

LLM 외에 꼭 봐야 할 구성요소는 대략 8가지입니다. 1) 문서 수집/정제, 2) chunking 전략, 3) embedding 모델, 4) 검색기(vector + keyword), 5) reranker, 6) prompt/context 조립기, 7) agent/tool router, 8) 평가·모니터링입니다.[^1_2][^1_1]

특히 RAG의 품질은 생성모델보다 검색 전처리에서 먼저 무너지는 경우가 많습니다. OpenAI Cookbook 예제도 질문과 답을 합쳐 임베딩하고, 메타데이터를 별도로 저장한 뒤, 검색 결과 metadata를 근거 문맥으로 조합해 최종 응답을 생성하는 구조를 보여줍니다.[^1_1]

## 우선순위

심플한 구현이라면 아래 순서로 우선순위를 두는 것이 효율적입니다. 단순 agent를 바로 붙이기보다, 먼저 “retrieval quality가 보장된 RAG”를 만든 뒤 agent화를 얹는 편이 실패 확률이 낮습니다.[^1_2]

1. 문서 정제: PDF/HTML/사내 문서를 원문 단위로 정리하고, 제목·섹션·버전·작성일 같은 metadata를 붙입니다. OpenAI Cookbook에서도 원문 외에 Question/Answer를 metadata로 분리 저장해 후속 검색과 응답 조합에 활용합니다.[^1_1]
2. Chunking: 고정 길이만 쓰지 말고 제목/절/문단 기준의 semantic chunk를 우선 고려합니다. chunk가 너무 크면 잡음이 늘고, 너무 작으면 문맥이 끊겨 검색 정확도가 떨어집니다.[^1_2][^1_1]
3. Retrieval: 처음부터 벡터 검색만 쓰기보다 hybrid search를 고려하는 편이 안전합니다. Agno 문서도 hybrid search가 semantic match와 exact term match를 함께 잡아준다고 설명합니다.[^1_2]
4. Reranking: 1차 검색 후보를 그대로 쓰지 말고 reranker로 상위 문서를 다시 정렬합니다. Agno는 cross-encoder 기반 reranking이 초기 검색 결과를 relevance 중심으로 재배열해 품질을 높인다고 설명합니다.[^1_2]
5. Metadata filtering: 문서 타입, 버전, 조직, 제품, 날짜 같은 필터를 설계해야 오답 범위를 줄일 수 있습니다. OpenAI Cookbook은 검색 시 metadata를 함께 저장·반환해 후속 컨텍스트 제어에 활용합니다.[^1_1]
6. Answer policy: 검색 결과가 약하면 “모른다” 또는 “근거 부족”으로 답하게 해야 합니다. 그렇지 않으면 hallucination이 retrieval failure를 가립니다.[^1_1][^1_2]

## 구현방향

가장 현실적인 방향은 **2단계 구조**입니다. 먼저 “Naive RAG+”를 만들고, 그 다음에 “Light Agentic RAG”로 확장하는 방식입니다.[^1_1][^1_2]

### 1단계: Naive RAG+

가장 단순한 운영형 구조는 아래와 같습니다. 이 단계만 잘 만들어도 내부 지식검색, 기술문서 QA, 사내 위키 응답의 상당수를 커버할 수 있습니다.[^1_2][^1_1]

- Ingestion: 문서 수집, 정제, metadata 부여.[^1_1]
- Chunking: 500~1000 token 내외의 섹션 기반 chunk, 10~20% overlap. 이 수치는 일반적 가이드이며 실제 최적값은 데이터셋별 평가가 필요합니다.[^1_2]
- Embedding: 범용 text embedding 모델 사용. OpenAI Cookbook 예제는 `text-embedding-3-small`로 임베딩 차원을 확인하고 인덱스를 생성합니다.[^1_1]
- Retrieval: top-k 20~50 정도의 1차 검색.[^1_2]
- Reranking: 상위 3~8개만 최종 context 후보로 축소. Agno는 reranker가 초기 후보를 relevance 순으로 다시 정렬한다고 설명합니다.[^1_2]
- Prompt assembly: “질문 + 인용 가능한 근거 chunk + 답변 형식 제약”으로 컨텍스트 조립.[^1_1]
- Answering: 답변과 함께 출처 문서명/섹션/링크 반환.[^1_1][^1_2]


### 2단계: Light Agentic RAG

그 다음 agent를 얹을 때는 복잡한 multi-agent보다 **router 1개 + retrieval tool 1~2개** 정도가 적절합니다. OpenAI Cookbook은 질의에 따라 웹 검색 또는 벡터DB 검색 도구를 선택하는 multi-tool orchestration 예시를 제공합니다.[^1_1]

추천 라우팅은 아래처럼 단순하게 두면 됩니다.

- 사내 문서형 질문: internal RAG만 사용.[^1_1]
- 최신성 필요한 질문: 웹 검색 + internal RAG 병행.[^1_1]
- 키워드가 강한 질문: hybrid search 우선.[^1_2]
- 결과 불확실: 재질의(query rewrite) 1회 후 실패 시 근거 부족 응답. Agno는 agentic RAG가 필요 시 검색하고 질의를 reformulate할 수 있다고 설명합니다.[^1_2]


## 기술선택

초기 MVP 기준으로는 아래 조합이 단순합니다. 특정 벤더 종속보다 “교체 가능성”을 우선 두는 편이 좋습니다.[^1_2][^1_1]


| 영역 | 심플한 선택지 | 이유 |
| :-- | :-- | :-- |
| 문서 파이프라인 | Python + unstructured/직접 파서 | 수집·정제·metadata 통제가 쉬움 |
| 벡터 저장소 | Pinecone, LanceDB, pgvector | Cookbook은 Pinecone 예시, Agno는 LanceDB 예시를 제시합니다. [^1_1][^1_2] |
| 검색 방식 | Hybrid search | exact match + semantic match를 함께 확보합니다. [^1_2] |
| 재정렬 | Cohere류 reranker 또는 동급 cross-encoder | 최종 문맥 품질 개선 효과가 큽니다. [^1_2] |
| 오케스트레이션 | LangGraph/LangChain 또는 직접 구현 | 초기엔 직접 구현이 더 단순할 수 있음 |
| 응답 생성 | 범용 LLM + 강한 답변 정책 | 생성보다 근거 통제가 중요합니다. [^1_1] |

당장 가장 단순한 코드 구조는 `ingest.py`, `index.py`, `retrieve.py`, `rerank.py`, `answer.py`, `router.py` 정도로 나누는 방식입니다. 나중에 agent 프레임워크를 붙이더라도 retrieval core를 독립 모듈로 유지해야 교체와 평가가 쉽습니다.[^1_2][^1_1]

## 운영기준

실서비스로 가려면 품질 평가와 운영 지표를 반드시 넣어야 합니다. OpenAI Cookbook 계열 자료는 RAG를 단순 생성이 아니라 retrieval과 response generation을 따로 평가하는 접근을 강조합니다.[^1_3]

최소한 아래 지표는 보셔야 합니다.

- Retrieval hit rate: 정답 근거 문서가 top-k 안에 들어오는지.[^1_3]
- Rerank gain: reranking 전후 top-3 정확도 차이.[^1_2]
- Groundedness: 답변 문장이 실제 chunk에 의해 뒷받침되는지.[^1_3][^1_1]
- Abstention rate: 근거 부족 시 답변 거절이 적절했는지.[^1_1]
- Latency/cost: embedding, retrieval, rerank, generation 각각의 지연과 비용.[^1_1][^1_2]

권장 아키텍처는 아래처럼 정리할 수 있습니다.

- **MVP**: Ingestion → chunking → embedding → hybrid retrieval → reranking → grounded answer.[^1_2][^1_1]
- **확장형**: MVP + query rewrite + metadata filter + web/internal router.[^1_1][^1_2]
- **주의점**: 처음부터 multi-agent, graph RAG, 복잡한 memory를 넣기보다 검색 정확도와 근거 추적성을 먼저 고정하는 것이 좋습니다.[^1_2][^1_1]

실무적으로는 귀하처럼 엔터프라이즈 AI/RAG를 염두에 두신다면, 첫 버전은 “사내 기술문서 QA용 hybrid+rereank RAG”로 시작하고, 이후 “정책/최신 정보 질의만 웹 검색을 허용하는 router agent”로 확장하는 방향이 가장 안정적입니다.[^1_1][^1_2]

원하시면 다음 답변에서 바로 이어서 **Python 기준 폴더 구조, 컴포넌트 인터페이스, FastAPI + pgvector/Pinecone 기반 샘플 설계안**까지 구체적으로 드리겠습니다.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.youtube.com/watch?v=xWhX61651H8\&vl=ko

[^1_2]: https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration

[^1_3]: https://medium.com/llamaindex-blog/openai-cookbook-evaluating-rag-systems-fe393c61fb93

[^1_4]: https://arxiv.org/html/2511.18177v1

[^1_5]: https://cookbook.openai.com/examples/multimodal/image_understanding_with_rag

[^1_6]: https://docs.agno.com/knowledge/concepts/search-and-retrieval/agentic-rag

[^1_7]: https://developers.openai.com/cookbook/examples/vector_databases/pinecone/using_vision_modality_for_rag_with_pinecone

[^1_8]: https://www.youtube.com/watch?v=d_5cGCzZJN4

[^1_9]: https://medium.com/@xzw0005/ai-agent-tutorial-2-retrieval-augmented-generation-rag-0a24b7d5f0de

[^1_10]: https://abvijaykumar.medium.com/hands-on-agentic-rag-2-3-agentic-reranking-rag-773b04cf4cdd

[^1_11]: https://www.youtube.com/watch?v=_kpxLkH5vY0

[^1_12]: https://skills.sh/qodex-ai/ai-agent-skills/rag-agent-builder

[^1_13]: https://medium.com/@anixlynch/7-simplified-rag-architecture-diagrams-067fa4bd0a78

[^1_14]: https://todatabeyond.substack.com/p/the-rag-spectrum-exploring-7-distinct

[^1_15]: https://www.youtube.com/watch?v=-L8lFWQJ7fc


---

# RAG 에이전트 성능 최적화: 청킹, 하이브리드 검색, 리뱅킹 전략 비교 분석 가이드

RAG 성능 평가를 위한 지표 및 프레임워크 추천

RAG 에이전트 성능 최적화는 보통 “모델 교체”보다 **청킹, 검색 결합 방식, 재정렬, 평가 체계**를 먼저 다듬는 편이 효과가 큽니다. 특히 운영 환경에서는 classic RAG 기준으로 하이브리드 검색과 semantic/reranking을 기본축으로 두고, 이를 retrieval 지표와 answer 지표로 분리 평가하는 접근이 가장 실용적입니다.[^2_1][^2_2][^2_3][^2_4]

## 최적화 관점

Azure AI Search 문서는 RAG의 핵심 난제로 query understanding, token constraints, response time, security, multi-source access를 제시하고, classic RAG에서는 hybrid query와 semantic ranking을 relevance 향상의 기본 수단으로 설명합니다. 또한 큰 문서는 chunking으로 세분화하고, vectorization과 scoring profile, top-k 제어를 함께 조정해야 한다고 권고합니다.[^2_3]

즉, 성능 최적화의 초점은 단일 파라미터가 아니라 “문서를 어떤 단위로 나누고, 어떤 방식으로 많이 찾고, 어떤 기준으로 다시 줄이느냐”의 3단계입니다. 평가 역시 retrieval과 response generation을 분리해서 봐야 개선 포인트가 정확히 드러납니다.[^2_4][^2_3]

## 청킹 전략

청킹은 검색 recall과 응답 grounding의 출발점입니다. OpenAI의 LlamaIndex 평가 예제는 `chunk_size=512`로 단순 벡터 인덱스를 구성하고, similarity top-k를 조절하면서 retrieval 성능을 측정하는 기본 흐름을 보여줍니다.[^2_4]

실무에서는 다음처럼 비교하는 것이 좋습니다.

- 고정 길이 chunk: 구현이 가장 단순하지만, 문단 경계나 표/코드 블록 의미를 자르기 쉬워 문맥 손실 위험이 있습니다.[^2_3]
- 문단/섹션 기반 chunk: 문서 구조를 보존해 QA 품질이 좋아지는 경우가 많고, 기술문서·정책문서에 특히 유리합니다.[^2_3]
- Parent-child chunking: 작은 child chunk로 정밀 검색하고, 상위 parent section을 LLM에 넘겨 문맥 보존을 강화하는 방식입니다. Azure 기반 고급 RAG 구현 글에서도 child 200 tokens, parent 1000 tokens 예시처럼 “정밀 매칭 + 충분한 컨텍스트”를 함께 확보하는 패턴을 설명합니다.[^2_5]

초기 실험 매트릭스는 아래처럼 잡는 것이 무난합니다.

- 200~300 tokens: 정확한 키워드 매칭과 세밀한 retrieval에 유리하지만 문맥이 끊길 수 있습니다.[^2_6]
- 400~600 tokens: 일반적인 기술문서 QA의 기본 시작점으로 많이 쓰입니다. OpenAI 예제의 512도 이 범주에 해당합니다.[^2_4]
- 800~1200 tokens: 요약형 질문에는 유리할 수 있지만 noisy context가 늘어 contextual relevancy가 떨어질 수 있습니다.[^2_7]

청킹 튜닝 기준은 간단합니다. Contextual relevancy가 낮으면 chunk를 더 작게 하거나 top-k를 줄이고, context recall이 낮으면 chunk를 조금 키우거나 overlap과 hybrid recall을 강화합니다. DeepEval은 contextual relevancy가 retrieval context의 statement 중 실제로 질문과 관련 있는 비율을 본다고 설명하며, noisy context가 많을수록 점수가 낮아진다고 안내합니다.[^2_7]

## 하이브리드 검색

하이브리드 검색은 dense retrieval의 의미 기반 매칭과 BM25의 exact term 매칭을 결합하는 방식입니다. Azure AI Search는 classic RAG에서 hybrid query가 keyword와 vector search를 병렬로 수행해 unified result set을 만들고, semantic ranking으로 다시 relevance를 높인다고 설명합니다.[^2_3]

이 방식이 중요한 이유는 질문 유형이 서로 다르기 때문입니다. 제품명, 버전, 에러코드, 규정 번호처럼 lexical exactness가 중요한 질문은 BM25가 강하고, 개념적 유사도나 paraphrase 매칭은 vector search가 강합니다. Azure 고급 RAG 구현 사례는 hybrid search에서 BM25와 vector 결과를 RRF로 결합한 뒤 semantic reranking을 적용하는 구조를 소개합니다.[^2_5]

실무 비교는 아래처럼 보시면 됩니다.


| 방식 | 장점 | 약점 | 적합한 질의 |
| :-- | :-- | :-- | :-- |
| Vector only | 의미 유사도 검색에 강함 [^2_3] | 숫자, 코드, 제품명 exact match에 취약할 수 있음 [^2_5] | 자연어 설명형 질문 |
| BM25 only | 희귀 토큰, 버전명, 에러코드에 강함 [^2_5] | 동의어·의미 확장에 약함 [^2_3] | 키워드 중심 질의 |
| Hybrid | recall이 가장 안정적이고 production 기본값으로 적합 [^2_3][^2_5] | 구현과 파라미터가 조금 더 복잡함 | 혼합형 기업 문서 QA |

질의가 복잡하거나 대화형이라면 agentic retrieval처럼 subquery decomposition이 강력할 수 있지만, 단순하고 빠른 운영형 RAG는 classic hybrid + reranking이 더 단순하고 실패 지점이 적습니다. Azure 문서도 classic RAG는 single-shot query 기반이라 구조가 더 단순하고 빠르다고 설명합니다.[^2_3]

## 리랭킹 전략

리랭킹은 1차 검색의 상위 후보를 더 정밀한 모델로 다시 정렬하는 단계입니다. Azure 고급 구현 사례는 hybrid search 뒤 semantic reranking이 top 50 후보를 재점수화해 최종 top 5를 고르는 구조를 예시로 제시합니다.[^2_5]

OpenAI의 LlamaIndex 평가 예제에서도 hit rate보다 MRR이 낮을 때, “관련 문서를 찾기는 하지만 상위 순위 배치가 불안정하다”는 해석을 제시하며 reranker 사용이 MRR 개선 방법이라고 설명합니다. 예제 결과에서는 hit rate 0.758621, MRR 0.62069로 나타났습니다.[^2_4]

전략 비교는 다음과 같습니다.

- No rerank: 가장 빠르지만 top-k 노이즈가 그대로 남아 answer quality가 흔들리기 쉽습니다.[^2_4]
- Cross-encoder rerank: 정확도 개선 효과가 크고 MRR/nDCG 향상에 유리하지만 latency가 늘어납니다.[^2_6][^2_5]
- Semantic reranker 내장형: Azure AI Search처럼 검색엔진 레벨에서 통합 제공되면 구현 복잡도를 줄일 수 있습니다.[^2_5][^2_3]

권장 패턴은 `retrieve wide → rerank narrow → answer`입니다. 즉, 1차 검색은 20~50개 정도 넓게 가져오고, rerank 후 3~8개 내외만 최종 context로 넘기는 방식이 일반적으로 안정적입니다.[^2_6][^2_5]

## 평가 지표

RAG 성능 평가는 retrieval과 generation을 분리해야 합니다. OpenAI의 Evaluate RAG with LlamaIndex 예제는 retrieval evaluation과 response evaluation을 별도 단계로 수행하고, retrieval에는 Hit Rate와 MRR, response에는 Faithfulness와 Relevancy를 사용합니다.[^2_4]

추천 지표는 아래처럼 구분하는 것이 좋습니다.


| 평가영역 | 핵심 지표 | 의미 | 권장 용도 |
| :-- | :-- | :-- | :-- |
| Retrieval | Hit Rate [^2_4] | top-k 안에 정답 근거가 들어왔는지 | 기본 recall 점검 |
| Retrieval | MRR [^2_4] | 첫 relevant 문서가 얼마나 상위에 오는지 | reranking 효과 측정 |
| Retrieval | Context Precision [^2_1][^2_8] | 검색 문맥의 관련성 밀도 | noisy context 감지 |
| Retrieval | Context Recall [^2_1][^2_8] | 필요한 근거를 얼마나 빠짐없이 찾는지 | chunk/hybrid 비교 |
| Response | Faithfulness [^2_4][^2_1] | 답변이 검색 문맥에 근거하는지 | hallucination 감시 |
| Response | Answer Relevancy [^2_2][^2_8] | 답변이 질문에 맞는지 | prompt/answer 품질 |
| Response | Groundedness/Source coverage [^2_1][^2_9] | 답변 문장의 근거 추적 가능성 | 엔터프라이즈 QA |

라벨이 없는 운영 로그를 볼 때는 referenceless metric이 유용합니다. DeepEval은 RAG Triad를 Answer Relevancy, Faithfulness, Contextual Relevancy의 3개 축으로 설명하며, 이 세 지표는 `expected_output` 없이도 사용할 수 있다고 안내합니다. 또한 contextual relevancy는 chunk size, top-k, embedding model 쪽 문제를 가리키고, answer relevancy는 prompt template, faithfulness는 generator LLM 또는 grounding 문제를 가리킨다고 설명합니다.[^2_9]

## 프레임워크 추천

평가 프레임워크는 목적에 따라 고르면 됩니다. 정답셋이 있는 오프라인 벤치마크와, 정답셋이 부족한 운영 로그 평가를 분리해서 생각하는 것이 좋습니다.[^2_9][^2_4]

- **LlamaIndex Evaluator**: OpenAI 예제처럼 `generate_question_context_pairs`, `RetrieverEvaluator`, `FaithfulnessEvaluator`, `RelevancyEvaluator`, `BatchEvalRunner`를 활용해 retrieval과 response를 함께 평가할 수 있습니다. 빠르게 PoC를 만들기 좋습니다.[^2_4]
- **RAGAS**: 공식 문서는 RAG와 agentic workflow용 metrics를 제공하며, RAG에 대해 Context Precision, Context Recall, Response Relevancy, Faithfulness, Noise Sensitivity 등을 지원한다고 설명합니다. labeled set이 있거나 semi-automatic eval을 만들 때 적합합니다.[^2_1]
- **DeepEval**: RAG quickstart 문서는 generator-focused로 Answer Relevancy, Faithfulness를, retriever-focused로 Contextual Relevancy, Contextual Precision, Contextual Recall을 제시합니다. 특히 live traffic에서 referenceless triad를 돌리기 좋습니다.[^2_2][^2_9]
- **LangSmith**: 체인/에이전트 실행 추적, dataset 기반 회귀 테스트, fixed-source 평가에 강점이 있어 운영 추적과 실험 관리에 유리합니다.[^2_10]

귀하의 용도처럼 “성능 최적화 비교 분석 가이드”가 목적이라면 아래 조합이 가장 실용적입니다.

1. 오프라인 벤치: LlamaIndex 또는 RAGAS로 정답셋 기반 Recall/MRR/Context Recall 측정.[^2_8][^2_4]
2. 온라인 회귀: DeepEval RAG Triad로 answer relevancy, faithfulness, contextual relevancy 지속 점검.[^2_9]
3. 실험 추적: LangSmith 또는 자체 MLflow/DB 대시보드로 chunk size, top-k, reranker on/off, hybrid on/off 실험 기록.[^2_10]

실험 설계는 `chunk_size × overlap × retrieval mode × reranker × top-k`의 그리드로 구성하면 됩니다. 예를 들어 256/512/1024 chunk, overlap 10/20%, vector vs hybrid, rerank on/off, top-k 5/10/20 조합을 돌리고, 각 조합에 대해 Hit Rate, MRR, Context Precision, Faithfulness를 함께 기록하면 어떤 축이 병목인지 명확해집니다.[^2_8][^2_9][^2_4]

권장 시작점은 다음과 같습니다.

- Chunk: 400~600 tokens, 10~20% overlap.[^2_6][^2_4]
- Retrieval: hybrid 기본값.[^2_5][^2_3]
- First-stage top-k: 20~50.[^2_6][^2_5]
- Final context: rerank 후 3~8 chunks.[^2_5][^2_6]
- Eval baseline: Hit Rate, MRR, Faithfulness, Answer Relevancy, Contextual Relevancy.[^2_2][^2_9][^2_4]

다음 단계로는 귀하가 바로 실험에 투입할 수 있도록 **Python 기준 실험 매트릭스 템플릿, 평가 스크립트 구조, RAGAS/DeepEval/LlamaIndex 비교표**까지 정리해드리는 편이 가장 도움이 됩니다. 어느 스택을 기준으로 정리할까요? `LlamaIndex`, `LangChain`, `Haystack`, 또는 `FastAPI + 직접구현` 중 하나를 지정해 주세요.
<span style="display:none">[^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32]</span>

<div align="center">⁂</div>

[^2_1]: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/

[^2_2]: https://deepeval.com/docs/getting-started-rag

[^2_3]: https://cookbook.openai.com/examples/multimodal/image_understanding_with_rag

[^2_4]: https://arxiv.org/html/2511.18177v1

[^2_5]: https://stackmindset.com/blog/gen-ai/advanced-rag-azure-implementation/

[^2_6]: https://www.linkedin.com/posts/soyhanonder_rag-vectorsearch-llm-activity-7417174453098532865-bL-i

[^2_7]: https://deepeval.com/docs/metrics-contextual-relevancy

[^2_8]: https://docs.ragas.io/en/v0.1.21/getstarted/evaluation.html

[^2_9]: https://deepeval.com/guides/guides-rag-triad

[^2_10]: https://docs.smith.langchain.com/cookbook/testing-examples/using-fixed-sources

[^2_11]: https://www.stackai.com/insights/retrieval-augmented-generation-(rag)-best-practices-for-enterprise-ai-chunking-embeddings-reranking-and-hybrid-search-optimization

[^2_12]: https://dev.to/suhas_mallesh/azure-ai-search-advanced-rag-with-terraform-hybrid-search-semantic-ranking-and-agentic-retrieval-180k

[^2_13]: https://medium.com/llamaindex-blog/openai-cookbook-evaluating-rag-systems-fe393c61fb93

[^2_14]: https://aiexpert.ee/en/articles/chunking-reranking-hybrid-search

[^2_15]: https://developers.openai.com/cookbook/examples/evaluation/evaluate_rag_with_llamaindex

[^2_16]: https://www.youtube.com/watch?v=kOALKZvhMgQ

[^2_17]: https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/raising-the-bar-for-rag-excellence-query-rewriting-and-new-semantic-ranker/4302729

[^2_18]: https://github.com/openai/openai-cookbook/blob/main/examples/evaluation/Evaluate_RAG_with_LlamaIndex.ipynb/

[^2_19]: https://blog.gopenai.com/how-to-prevent-context-loss-in-azure-ai-search-rag-pipelines-497c346c7077

[^2_20]: https://s-edv.com/anleitungen/rag-produktiv-chunking-reranking-eval

[^2_21]: https://ragnight.com/blog/architecture-rag-production-guide-complet?locale=en

[^2_22]: https://medium.com/@rajuyallappa9056/why-your-rag-sucks-fixing-broken-retrieval-with-hybrid-search-reranking-contextual-chunking-336d47a8e7c0

[^2_23]: https://21510208.fs1.hubspotusercontent-na1.net/hubfs/21510208/Hybrid_Retriever.pdf

[^2_24]: https://docs.ragas.io/en/v0.0.19/references/metrics.html

[^2_25]: https://deepeval.com/docs/metrics-introduction

[^2_26]: https://learnixo.io/blog/adv-rag-ragas

[^2_27]: https://bhavikjikadara.medium.com/evaluating-an-rag-pipeline-using-deepeval-749f641b3186

[^2_28]: https://velog.io/@yoonene/RAGAS-metrics-정리

[^2_29]: https://medium.com/@nidishnrao/ragas-e0bf700a63c6

[^2_30]: https://www.llamaindex.ai/blog/evaluating-rag-with-deepeval-and-llamaindex

[^2_31]: https://deepeval.com/guides/guides-rag-evaluation

[^2_32]: https://qaskills.sh/blog/deepeval-rag-evaluation-metrics-reference-2026


---

# LlamaIndex, LangChain 환경

LlamaIndex와 LangChain 환경이라면, **LlamaIndex는 retrieval/response 평가 엔진으로**, **LangChain은 실행 체인과 LangSmith 관측·회귀평가 계층으로** 나누어 쓰는 구성이 가장 실용적입니다. 두 프레임워크를 경쟁 관계로 보기보다, “LlamaIndex = RAG 내부 평가”, “LangChain/LangSmith = 운영 추적과 실험 관리”로 역할을 분리하면 중복이 줄고 운영성이 좋아집니다.[^3_1][^3_2]

## 권장 구조

LlamaIndex는 `Faithfulness`, `Answer Relevancy`, `Context Relevancy` 같은 evaluator와 `BatchEvalRunner`, `evaluate_response`, `evaluate_queries` 같은 배치 평가 인터페이스를 제공합니다. 특히 `BaseEvaluator`가 query, response, contexts를 공통 입력으로 받기 때문에 청킹·검색·리랭킹 실험에 잘 맞습니다.[^3_2][^3_1]

LangChain 쪽은 LangSmith를 통해 dataset 생성, 실행 추적, correctness/relevance/groundedness/retrieval relevance 평가를 구성할 수 있습니다. 공식 튜토리얼도 RAG 평가를 “dataset 생성 → 애플리케이션 실행 → correctness, relevance, groundedness, retrieval relevance 측정”의 3단계로 설명합니다.[^3_2]

## 역할 분담

가장 추천하는 역할 분담은 아래와 같습니다.


| 계층 | 권장 도구 | 역할 |
| :-- | :-- | :-- |
| RAG 파이프라인 | LlamaIndex 또는 LangChain 둘 중 하나 | 실제 ingestion, indexing, retrieval, reranking |
| 오프라인 평가 | LlamaIndex Evaluators + RAGAS | chunking, top-k, hybrid, rerank 조합 비교 [^3_1][^3_3] |
| 운영 추적 | LangSmith | 실험별 trace, latency, prompt/retrieval step 추적 [^3_2] |
| 회귀 테스트 | LangSmith evaluators | correctness, groundedness, retrieval relevance 지속 점검 [^3_2] |

즉, 개발은 어느 한쪽으로 통일해도 되지만, 평가는 혼합 구성이 오히려 효율적입니다. LangSmith 공식 문서도 평가 방식은 특정 프레임워크에 종속되지 않으며, 다른 프레임워크로 만든 앱에도 적용 가능하다고 명시합니다.[^3_2]

## LlamaIndex 설계

LlamaIndex에서는 우선 query-response-context를 안정적으로 수집하는 것이 중요합니다. `evaluate_response()`는 `Response` 객체에서 `response.response`와 `response.source_nodes`를 자동으로 추출해 evaluator에 넘기므로, source node가 유지되는 query engine 구성이 핵심입니다.[^3_4]

실험용 최소 evaluator 세트는 아래 3개가 적절합니다.

- `FaithfulnessEvaluator`: 응답이 retrieved context에 충실한지, 즉 hallucination 여부를 평가합니다. LlamaIndex 문서는 이를 “response가 source nodes와 일치하는지 측정”한다고 설명합니다.[^3_5][^3_6]
- `AnswerRelevancyEvaluator`: 응답이 질문에 적절한지를 봅니다.[^3_4]
- `ContextRelevancyEvaluator`: retrieved contexts 자체가 질문과 관련 있는지를 평가합니다.[^3_4]

실무적으로는 이 3개만으로도 병목 위치가 잘 드러납니다. `ContextRelevancy`가 낮으면 chunking, top-k, hybrid retrieval 쪽 문제일 가능성이 크고, `Faithfulness`만 낮으면 generator prompt나 context packing, answer policy 문제가 의심됩니다.[^3_1][^3_4]

## LangChain 설계

LangChain 환경에서는 LangSmith를 평가 허브로 두는 편이 좋습니다. 공식 튜토리얼은 정답셋 기반 `correctness`, 질문 대비 응답의 `relevance`, 문서 근거 대비 응답의 `groundedness`, 질문 대비 검색 문서의 `retrieval relevance`를 evaluator 함수로 구성해 `client.evaluate()`로 실행하는 패턴을 제시합니다.[^3_2]

이 구조의 장점은 운영 회귀 테스트에 강하다는 점입니다. 예를 들어 `chunk_size=256`, `hybrid=on`, `rerank=off`와 `chunk_size=512`, `hybrid=on`, `rerank=on` 두 실험을 각각 다른 metadata로 LangSmith에 남기면, 응답 품질뿐 아니라 trace 단위로 retriever 결과와 prompt까지 비교할 수 있습니다.[^3_2]

## 실험 매트릭스

귀하의 목적이 “청킹, 하이브리드 검색, 리랭킹 전략 비교 분석”이라면, 아래처럼 두 프레임워크를 나눠 쓰는 실험 설계가 가장 깔끔합니다.

- LlamaIndex: retrieval 품질 비교 실험.[^3_1][^3_4]
- LangSmith: 최종 사용자 응답 품질과 회귀 테스트.[^3_2]

권장 실험 축은 아래와 같습니다.


| 축 | 후보 |
| :-- | :-- |
| Chunk size | 256, 512, 1024 |
| Overlap | 10%, 20% |
| Retrieval | vector only, hybrid |
| Rerank | off, cross-encoder/semantic rerank on |
| Top-k retrieve | 10, 20, 40 |
| Final context count | 3, 5, 8 |

평가 방식은 이렇게 두 층으로 나누면 됩니다.

1. **LlamaIndex 오프라인 평가**: `ContextRelevancy`, `AnswerRelevancy`, `Faithfulness`, 필요 시 retrieval ranking metric.[^3_1][^3_4]
2. **LangSmith 회귀 평가**: `correctness`, `groundedness`, `relevance`, `retrieval relevance`.[^3_2]

## 구현 순서

추천 구현 순서는 다음과 같습니다.

1. LangChain 또는 LlamaIndex 중 하나로 실제 RAG 파이프라인을 먼저 고정합니다. 두 프레임워크를 동시에 retrieval layer에 섞기 시작하면 디버깅 비용이 올라갑니다.[^3_1][^3_2]
2. LlamaIndex evaluator로 오프라인 실험 harness를 만듭니다. `BatchEvalRunner`는 여러 evaluator를 병렬로 돌릴 수 있어 실험 매트릭스 비교에 적합합니다.[^3_4]
3. LangSmith dataset을 만들고 동일 질문셋에 대해 회귀 실험을 누적합니다. LangSmith 문서는 dataset 기반 평가와 experiment metadata를 활용한 비교 방식을 제공합니다.[^3_2]
4. RAGAS는 중간 계층으로 붙입니다. RAGAS는 LlamaIndex와 통합 문서를 제공하므로, LlamaIndex 기반 query engine 결과를 RAGAS metric으로 확장하는 데 유리합니다.[^3_3]

귀하의 환경 기준으로 제가 가장 추천하는 구성은 다음입니다.

- **개발 프레임워크**: LlamaIndex로 retrieval 중심 구현, 또는 이미 LangChain 비중이 높다면 LangChain으로 체인 구현.
- **평가 프레임워크**: LlamaIndex evaluator + LangSmith + RAGAS 병행.[^3_3][^3_1][^3_2]

실전형으로 정리하면 아래 한 줄이 됩니다.

- **LlamaIndex는 품질 실험실**, **LangSmith는 운영 관제실**로 쓰십시오.[^3_1][^3_2]

다음 답변에서는 바로 이어서 **LlamaIndex + LangChain 공용 실험 템플릿 구조, Python 디렉터리 설계, 평가 코드 스켈레톤, chunk/hybrid/rerank 실험표 자동화 예제**를 드리겠습니다. 어느 쪽을 주 구현체로 둘지 정하시면 됩니다: `LlamaIndex 중심` 또는 `LangChain 중심`.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://docs.llamaindex.ai/en/v0.10.20/module_guides/evaluating/root.html

[^3_2]: https://docs.agno.com/knowledge/concepts/search-and-retrieval/agentic-rag

[^3_3]: https://docs.ragas.io/en/v0.0.22/references/integrations/llamaindex.html

[^3_4]: https://developers.openai.com/cookbook/examples/vector_databases/pinecone/using_vision_modality_for_rag_with_pinecone

[^3_5]: https://developers.llamaindex.ai/typescript/framework/modules/evaluation/faithfulness/

[^3_6]: https://developers.llamaindex.ai/python/framework/module_guides/evaluating/usage_pattern/

[^3_7]: https://developers.llamaindex.ai/python/framework-api-reference/evaluation/faithfullness/

[^3_8]: https://docs.langchain.com/langsmith/evaluate-rag-tutorial

[^3_9]: https://docs.llamaindex.ai/en/v0.10.23/examples/evaluation/faithfulness_eval/

[^3_10]: https://docs.langchain.com/langsmith/evaluation-approaches

[^3_11]: https://docs.smith.langchain.com/old/cookbook/testing-examples/ragas

[^3_12]: https://kr.langchain-docs.com/langsmith/evaluate-rag-tutorial

[^3_13]: https://www.llamaindex.ai/blog/evaluating-multi-modal-retrieval-augmented-generation-db3ca824d428

[^3_14]: https://docs.langchain.com/langsmith/evaluate-on-intermediate-steps

[^3_15]: https://www.youtube.com/watch?v=pICPk6OHk7c

[^3_16]: https://www.langchain.com/blog/evaluating-rag-pipelines-with-ragas-langsmith

[^3_17]: https://gist.github.com/rlancemartin/f9332f8ebb3d96141c2781f2cd60e74d


---

# LangChain을 주 구현체로 선택할게요

LangChain을 주 구현체로 선택하셨다면, 가장 좋은 방향은 **LCEL 기반 RAG 파이프라인 + LangSmith 평가/추적 + RAGAS 보조평가** 조합입니다. LangSmith 공식 튜토리얼은 LangChain으로 만든 RAG 앱에 대해 dataset 생성, 실행, correctness·relevance·groundedness·retrieval relevance 평가를 수행하는 구조를 제시하고, RAGAS는 LangChain 체인 결과를 `context_recall`, `faithfulness`, `factual_correctness` 같은 지표로 보완할 수 있게 통합 예제를 제공합니다.[^4_1][^4_2]

## 권장 아키텍처

LangChain 쪽 구현은 너무 많은 체인 추상화를 쓰기보다, **문서 적재 → splitter → retriever → optional reranker → prompt → LLM → parser**의 직선형 LCEL 파이프라인으로 시작하는 편이 좋습니다. LangSmith 예제도 기본 RAG를 이 흐름으로 구성하고, retriever와 ChatModel 호출을 traceable하게 연결해 평가 대상으로 삼습니다.[^4_1]

운영 구성을 나누면 아래처럼 깔끔합니다.


| 계층 | 권장 도구 | 역할 |
| :-- | :-- | :-- |
| 파이프라인 구현 | LangChain LCEL | ingestion, retrieval, generation [^4_1] |
| 관측/회귀평가 | LangSmith | correctness, relevance, groundedness, retrieval relevance [^4_1] |
| 정량 보조평가 | RAGAS | context_recall, faithfulness, factual_correctness [^4_2] |
| 벡터저장소 | pgvector, Qdrant, Pinecone 등 | 운영 인덱스 |
| 리랭킹 | cross-encoder 또는 검색엔진 semantic rerank | 1차 검색 후보 정렬 |

## 구현 원칙

LangSmith 문서는 RAG 평가를 네 종류로 구분합니다. `correctness`는 응답과 정답셋 비교, `relevance`는 응답과 질문 비교, `groundedness`는 응답과 검색 문맥 비교, `retrieval relevance`는 검색 문맥과 질문 비교입니다.[^4_1]

이 분류는 설계에도 그대로 적용할 수 있습니다.

- Retrieval layer는 `retrieval relevance`를 올리는 방향으로 튜닝합니다.[^4_1]
- Generation layer는 `groundedness`와 `correctness`를 올리는 방향으로 튜닝합니다.[^4_1]
- Prompt layer는 `relevance`와 `faithfulness`를 동시에 보도록 설계합니다.[^4_2][^4_1]

즉, LangChain 구현의 핵심은 “문서 검색 결과를 answer와 함께 반환”하도록 인터페이스를 고정하는 것입니다. LangSmith 예제도 `{"answer": ..., "documents": docs}` 형태로 반환해 groundedness와 retrieval relevance evaluator가 작동하도록 구성합니다.[^4_1]

## 디렉터리 구조

실무용으로는 아래 구조를 추천합니다. retrieval 실험과 평가를 분리하기 쉽고, CI에 넣기도 좋습니다. LangSmith와 RAGAS는 둘 다 질문·응답·retrieved contexts를 입력으로 쓰기 때문에, 실행 결과를 공통 스키마로 남기면 재활용성이 높습니다.[^4_2][^4_1]

```text
rag-app/
├── app/
│   ├── ingest.py
│   ├── splitters.py
│   ├── retrievers.py
│   ├── rerankers.py
│   ├── chains.py
│   ├── prompts.py
│   └── config.py
├── eval/
│   ├── dataset.py
│   ├── langsmith_eval.py
│   ├── ragas_eval.py
│   └── experiment_matrix.py
├── tests/
│   └── test_rag_regression.py
├── notebooks/
└── pyproject.toml
```

역할 분리는 다음처럼 두시면 됩니다.

- `retrievers.py`: vector/hybrid 검색 전략 캡슐화.
- `rerankers.py`: rerank on/off 및 모델 교체 포인트.
- `chains.py`: 최종 LCEL 체인 조립.
- `langsmith_eval.py`: correctness, groundedness, retrieval relevance evaluator 실행.[^4_1]
- `ragas_eval.py`: `EvaluationDataset` 생성 후 `LLMContextRecall`, `Faithfulness`, `FactualCorrectness` 실행.[^4_2]


## LCEL 스켈레톤

LangChain에서는 아래처럼 “retriever 결과를 answer와 함께 반환하는” 형태가 중요합니다. RAGAS 예제도 `retrieved_contexts`, `response`, `reference`를 dataset에 넣는 구조를 사용합니다.[^4_2]

```python
from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

prompt = ChatPromptTemplate.from_template(
    """주어진 context만 사용해 질문에 답하세요.
모르면 모른다고 답하세요.

Context:
{context}

Question:
{question}
"""
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def build_rag_chain(retriever, reranker=None):
    def retrieve(question: str):
        docs = retriever.invoke(question)
        if reranker:
            docs = reranker.rerank(question, docs)
        return docs

    retrieve_node = RunnableLambda(retrieve)

    answer_chain = (
        {
            "question": RunnablePassthrough(),
            "docs": retrieve_node,
        }
        | {
            "question": itemgetter("question"),
            "documents": itemgetter("docs"),
            "context": itemgetter("docs") | RunnableLambda(format_docs),
        }
        | RunnableLambda(
            lambda x: {
                "answer": (prompt | llm | StrOutputParser()).invoke(
                    {"context": x["context"], "question": x["question"]}
                ),
                "documents": x["documents"],
            }
        )
    )
    return answer_chain
```

이 구조의 장점은 evaluator 친화적이라는 점입니다. LangSmith groundedness와 retrieval relevance는 `documents`를 직접 사용할 수 있고, RAGAS는 동일 결과를 `retrieved_contexts` 배열로 변환해 재사용할 수 있습니다.[^4_2][^4_1]

## 평가 설계

LangSmith에서는 공식 튜토리얼처럼 evaluator 함수를 4개 두는 방식이 좋습니다. 즉 `correctness`, `relevance`, `groundedness`, `retrieval_relevance`를 각각 evaluator로 등록해 `client.evaluate()`를 실행하는 패턴입니다.[^4_1]

RAGAS는 보조 정량평가로 붙이면 됩니다. 공식 LangChain 통합 예제는 `EvaluationDataset.from_list()`로 dataset을 만들고 `LLMContextRecall`, `Faithfulness`, `FactualCorrectness`를 평가합니다.[^4_2]

실제로는 아래처럼 나누면 됩니다.


| 도구 | 지표 | 목적 |
| :-- | :-- | :-- |
| LangSmith | correctness | 정답셋 기준 응답 정확도 [^4_1] |
| LangSmith | groundedness | hallucination 감시 [^4_1] |
| LangSmith | retrieval relevance | 검색 품질 감시 [^4_1] |
| RAGAS | LLMContextRecall | retrieval recall 추정 [^4_2] |
| RAGAS | Faithfulness | 문맥 충실성 보강 [^4_2] |
| RAGAS | FactualCorrectness | reference 대비 사실 정확성 보강 [^4_2] |

## 실험 매트릭스

LangChain 주 구현체에서 가장 먼저 자동화할 실험은 `chunk_size × overlap × retrieval mode × rerank × top_k`입니다. LangSmith는 dataset 기반 비교에 적합하고, RAGAS는 각 실험 run에서 context recall과 faithfulness를 정량화하는 데 적합합니다.[^4_2][^4_1]

권장 시작 매트릭스는 아래와 같습니다.

- Chunk size: 256, 512, 1024. LangSmith 예제는 250, RAGAS 통합 예제는 작은 in-memory 예시를 사용하므로 실무에서는 256/512를 시작점으로 두는 것이 현실적입니다.[^4_2][^4_1]
- Overlap: 10%, 20%.
- Retrieval: vector only, hybrid.
- Retrieve top-k: 10, 20, 40.
- Final context: rerank 후 3, 5, 8.
- Evaluators: LangSmith 4종 + RAGAS 3종.[^4_1][^4_2]

해석은 이렇게 하시면 됩니다.

- `retrieval relevance` 낮음: chunking 또는 hybrid retrieval 문제 가능성이 큽니다.[^4_1]
- `groundedness` 낮음: context packing, prompt, answer policy 문제 가능성이 큽니다.[^4_1]
- `LLMContextRecall` 낮음: 검색 누락, chunk granularity, top-k 부족 가능성이 큽니다.[^4_2]
- `FactualCorrectness`만 낮음: 생성 단계 요약/추론에서 정보 왜곡이 발생했을 가능성이 큽니다.[^4_2]


## 운영 권장안

초기 운영 baseline은 아래 구성이 무난합니다.

- `RecursiveCharacterTextSplitter` 기반 chunking으로 시작. LangSmith 예제도 이 splitter를 사용합니다.[^4_1]
- 답변은 항상 `documents`를 함께 반환.[^4_1]
- `traceable` 또는 LangSmith tracing 활성화.[^4_1]
- evaluator는 최소 `groundedness + retrieval relevance + correctness`를 유지.[^4_1]
- RAGAS는 nightly batch로 돌려 장기 추세를 봅니다. `context_recall`, `faithfulness`, `factual_correctness` 조합이 적절합니다.[^4_2]

실무적으로는 귀하처럼 엔터프라이즈 RAG를 염두에 둔 경우, **LangChain LCEL로 retrieval core를 심플하게 유지하고, 품질 판단은 LangSmith와 RAGAS로 외부화**하는 전략이 유지보수성이 가장 좋습니다.[^4_2][^4_1]

다음 단계로는 바로 실전에 쓸 수 있게 **LangChain 중심 Python 프로젝트 템플릿, LangSmith evaluator 코드, RAGAS 배치평가 스크립트, hybrid/rerank 인터페이스 설계**를 코드 수준으로 작성해드릴 수 있습니다. 파일 형태로 받아보시겠습니까, 아니면 대화 안에 바로 전체 예제 코드를 드릴까요?
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_3][^4_4][^4_5][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://www.youtube.com/watch?v=d_5cGCzZJN4

[^4_2]: https://medium.com/llamaindex-blog/openai-cookbook-evaluating-rag-systems-fe393c61fb93

[^4_3]: https://docs.langchain.com/langsmith/evaluate-rag-tutorial

[^4_4]: https://wikidocs.net/318658

[^4_5]: https://docs.ragas.io/en/stable/howtos/integrations/langchain/

[^4_6]: https://www.langchain.com/blog/evaluating-rag-pipelines-with-ragas-langsmith

[^4_7]: https://note.com/pescafe/n/n2652c4c16453

[^4_8]: https://docs.ragas.io/en/v0.3.7/howtos/integrations/langchain/

[^4_9]: https://www.youtube.com/watch?v=lTfhw_9cJqc

[^4_10]: https://docs.ragas.io/en/v0.4.1/howtos/integrations/_langchain/

[^4_11]: https://docs.smith.langchain.com/old/cookbook/testing-examples/ragas

[^4_12]: https://docs.ragas.io/en/stable/references/integrations/

[^4_13]: https://www.youtube.com/watch?v=WC3t4pMKaVQ

[^4_14]: https://www.youtube.com/watch?v=vz0ERvLNbvw

[^4_15]: https://kr.langchain-docs.com/langsmith/evaluate-rag-tutorial

[^4_16]: https://agentry.press/tutorial/rag-pipeline-with-retrieval-tracing-and-eval-harness-using-langsmith/

[^4_17]: https://wikidocs.net/259216


---

# 우선 템플릿 구조와 예제 코드를 같이 부탁해요

좋습니다. LangChain을 주 구현체로 두고, **바로 가져다 쓸 수 있는 템플릿 구조 + 예제 코드**를 함께 드리겠습니다. 핵심은 LangSmith 평가를 위해 체인 결과가 `answer`와 `documents`를 함께 반환하도록 설계하고, RAGAS 평가를 위해 같은 실행 결과를 `retrieved_contexts` 형식으로 쉽게 변환할 수 있게 만드는 것입니다. LangSmith의 RAG 평가 튜토리얼은 correctness, relevance, groundedness, retrieval relevance를 기준으로 평가하는 구조를 제시하고, RAGAS LangChain 통합 문서는 `EvaluationDataset.from_list()`를 사용해 response, reference, retrieved_contexts 기반 평가를 수행하는 흐름을 보여줍니다.[^5_1][^5_2]

## 템플릿 구조

아래 구조는 “심플하지만 실험 가능한” RAG 프로젝트를 목표로 한 것입니다. LangChain은 retrieval 체인 구성을 단순하게 유지하고, 평가 계층은 별도 디렉터리로 분리하는 편이 유지보수와 회귀 테스트에 유리합니다.[^5_3][^5_1]

```text
rag-langchain-template/
├── app/
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   ├── loaders.py
│   ├── splitters.py
│   ├── vectorstore.py
│   ├── retrievers.py
│   ├── rerankers.py
│   ├── chains.py
│   └── schemas.py
├── eval/
│   ├── dataset.py
│   ├── langsmith_eval.py
│   ├── ragas_eval.py
│   └── experiment_runner.py
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   ├── ingest.py
│   ├── ask.py
│   └── run_eval.py
├── tests/
│   └── test_smoke.py
├── .env.example
├── pyproject.toml
└── README.md
```

이 구조의 장점은 역할이 명확하다는 점입니다. `app/`은 실제 서비스 코드, `eval/`은 실험 코드, `scripts/`는 실행 진입점이며, 나중에 FastAPI를 붙여도 core logic을 거의 손대지 않아도 됩니다.[^5_1]

## 핵심 설계

설계 원칙은 3개만 기억하시면 됩니다.

- 체인 출력은 항상 `answer`, `documents`, `question`을 포함합니다. LangSmith의 groundedness와 retrieval relevance 평가는 질문과 검색 문서를 함께 볼 수 있어야 하기 때문입니다.[^5_1]
- retriever와 reranker는 인터페이스로 분리합니다. 그래야 vector only, hybrid, rerank on/off 실험이 쉬워집니다.[^5_2][^5_3]
- 평가 데이터는 `user_input`, `response`, `reference`, `retrieved_contexts` 공통 스키마로 변환합니다. RAGAS의 `EvaluationDataset.from_list()`가 이 패턴을 전제로 하기 때문입니다.[^5_2]


## 예제 코드

아래 코드는 최소 동작형 템플릿입니다. 실제 운영에서는 벡터DB, 하이브리드 검색기, 리랭커만 교체하면 됩니다. LangChain LCEL은 retriever와 question을 prompt 입력으로 조합하는 방식으로 구성할 수 있으며, 기본 retrieval chain 패턴도 LangChain 문서의 Retrieval 가이드와 LCEL 예제 흐름에 부합합니다.[^5_4][^5_3]

### 1) `app/schemas.py`

```python
from __future__ import annotations

from typing import Any, List, TypedDict
from langchain_core.documents import Document


class RAGResult(TypedDict):
    question: str
    answer: str
    documents: List[Document]


class EvalRow(TypedDict):
    user_input: str
    response: str
    reference: str
    retrieved_contexts: List[str]
    retrieved_sources: List[str]
```


### 2) `app/config.py`

```python
from pydantic import BaseModel
import os


class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_tracing: str = os.getenv("LANGSMITH_TRACING", "true")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "rag-langchain-template")

    chat_model: str = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "64"))
    retrieve_k: int = int(os.getenv("RETRIEVE_K", "20"))
    final_k: int = int(os.getenv("FINAL_K", "5"))


settings = Settings()
```


### 3) `app/models.py`

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.config import settings


def get_llm():
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=0,
    )


def get_embeddings():
    return OpenAIEmbeddings(
        model=settings.embedding_model,
    )
```


### 4) `app/prompts.py`

```python
from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template(
    """당신은 근거 기반 질의응답 시스템입니다.
다음 규칙을 반드시 지키세요.
1. 주어진 context만 사용해 답변하세요.
2. context에 근거가 없으면 "주어진 문맥에서 확인되지 않습니다."라고 답하세요.
3. 가능하면 핵심 근거를 간단히 요약해 답변하세요.

Context:
{context}

Question:
{question}
"""
)
```


### 5) `app/loaders.py`

```python
from pathlib import Path
from langchain_core.documents import Document


def load_text_files(data_dir: str) -> list[Document]:
    docs = []
    for path in Path(data_dir).glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": str(path), "filename": path.name}
            )
        )
    return docs
```


### 6) `app/splitters.py`

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


def get_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
```


### 7) `app/vectorstore.py`

```python
from langchain_chroma import Chroma
from app.models import get_embeddings


def build_vectorstore(documents, persist_directory: str = "./data/chroma"):
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    return vectorstore
```


### 8) `app/retrievers.py`

```python
from typing import List
from langchain_core.documents import Document
from app.config import settings


class BaseRetrieverAdapter:
    def invoke(self, question: str) -> List[Document]:
        raise NotImplementedError


class VectorRetrieverAdapter(BaseRetrieverAdapter):
    def __init__(self, vectorstore):
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.retrieve_k},
        )

    def invoke(self, question: str) -> List[Document]:
        return self.retriever.invoke(question)


class HybridRetrieverAdapter(BaseRetrieverAdapter):
    def __init__(self, dense_retriever, sparse_retriever, merge_fn):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.merge_fn = merge_fn

    def invoke(self, question: str) -> List[Document]:
        dense_docs = self.dense_retriever.invoke(question)
        sparse_docs = self.sparse_retriever.invoke(question)
        return self.merge_fn(dense_docs, sparse_docs)
```

여기서 hybrid는 인터페이스만 잡아둔 상태입니다. 실제 BM25, Elasticsearch, OpenSearch, pgvector+BM25, vendor hybrid API로 교체하면 됩니다. hybrid search는 dense와 keyword search를 결합해 unified result set을 만드는 것이 일반적이며, exact token과 semantic match를 동시에 확보하는 데 유리합니다.[^5_5]

### 9) `app/rerankers.py`

```python
from typing import List
from langchain_core.documents import Document
from app.config import settings


class NoOpReranker:
    def rerank(self, question: str, docs: List[Document]) -> List[Document]:
        return docs[: settings.final_k]


class SimpleLengthHeuristicReranker:
    def rerank(self, question: str, docs: List[Document]) -> List[Document]:
        ranked = sorted(docs, key=lambda d: len(d.page_content), reverse=True)
        return ranked[: settings.final_k]
```

실전에서는 여기를 cross-encoder 기반 리랭커로 바꾸시면 됩니다. 중요한 점은 1차 검색을 넓게 가져오고, 2차에서 좁히는 인터페이스를 유지하는 것입니다. 이 구조는 retrieval relevance와 MRR 개선 실험에 적합합니다.[^5_6][^5_1]

### 10) `app/chains.py`

```python
from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.prompts import RAG_PROMPT
from app.models import get_llm


def format_docs(docs):
    return "\n\n".join(
        f"[source={d.metadata.get('filename', 'unknown')}]\n{d.page_content}"
        for d in docs
    )


def build_rag_chain(retriever_adapter, reranker):
    llm = get_llm()

    def retrieve(question: str):
        docs = retriever_adapter.invoke(question)
        docs = reranker.rerank(question, docs)
        return docs

    retrieve_node = RunnableLambda(retrieve)

    answer_node = RAG_PROMPT | llm | StrOutputParser()

    chain = (
        {
            "question": RunnablePassthrough(),
            "documents": retrieve_node,
        }
        | {
            "question": itemgetter("question"),
            "documents": itemgetter("documents"),
            "context": itemgetter("documents") | RunnableLambda(format_docs),
        }
        | RunnableLambda(
            lambda x: {
                "question": x["question"],
                "documents": x["documents"],
                "answer": answer_node.invoke(
                    {"question": x["question"], "context": x["context"]}
                ),
            }
        )
    )
    return chain
```

이 출력 형식은 LangSmith와 RAGAS 둘 다에 적합합니다. LangSmith는 trace와 evaluator에 검색 문서를 함께 넘길 수 있고, RAGAS는 `documents`를 문자열 배열로 바꿔 `retrieved_contexts`로 사용하면 됩니다.[^5_2][^5_1]

### 11) `eval/dataset.py`

```python
from app.schemas import EvalRow


def rag_result_to_eval_row(result: dict, reference: str) -> EvalRow:
    docs = result["documents"]
    return {
        "user_input": result["question"],
        "response": result["answer"],
        "reference": reference,
        "retrieved_contexts": [d.page_content for d in docs],
        "retrieved_sources": [d.metadata.get("source", "") for d in docs],
    }
```


### 12) `eval/ragas_eval.py`

```python
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset
from ragas.metrics import Faithfulness, LLMContextRecall, FactualCorrectness


def run_ragas_eval(eval_rows: list[dict]):
    dataset = EvaluationDataset.from_list(eval_rows)
    result = evaluate(
        dataset=dataset,
        metrics=[
            LLMContextRecall(),
            Faithfulness(),
            FactualCorrectness(),
        ],
    )
    return result
```

RAGAS LangChain 통합 문서는 `EvaluationDataset.from_list()`로 데이터를 만들고, `LLMContextRecall`, `Faithfulness`, `FactualCorrectness` 같은 metric을 evaluate에 전달하는 패턴을 사용합니다.[^5_2]

### 13) `eval/langsmith_eval.py`

```python
from langsmith import Client


def run_langsmith_eval(
    target,
    dataset_name: str,
    experiment_prefix: str = "rag-eval",
):
    client = Client()

    results = client.evaluate(
        target,
        data=dataset_name,
        experiment_prefix=experiment_prefix,
    )
    return results
```

실제 evaluator 함수는 correctness, relevance, groundedness, retrieval relevance를 별도로 정의해 `evaluators=[...]`에 넣는 방식이 좋습니다. LangSmith RAG 평가 튜토리얼은 이 네 가지 축으로 시스템을 점검하는 예시를 제공합니다.[^5_1]

### 14) `scripts/ingest.py`

```python
from app.loaders import load_text_files
from app.splitters import get_splitter
from app.vectorstore import build_vectorstore


def main():
    docs = load_text_files("./data/raw")
    splitter = get_splitter()
    split_docs = splitter.split_documents(docs)
    build_vectorstore(split_docs)
    print(f"Loaded {len(docs)} docs, split into {len(split_docs)} chunks")


if __name__ == "__main__":
    main()
```


### 15) `scripts/ask.py`

```python
from langchain_chroma import Chroma
from app.models import get_embeddings
from app.retrievers import VectorRetrieverAdapter
from app.rerankers import NoOpReranker
from app.chains import build_rag_chain


def main():
    vectorstore = Chroma(
        persist_directory="./data/chroma",
        embedding_function=get_embeddings(),
    )
    retriever = VectorRetrieverAdapter(vectorstore)
    reranker = NoOpReranker()
    chain = build_rag_chain(retriever, reranker)

    question = "RAG 평가에서 groundedness는 무엇을 의미하나요?"
    result = chain.invoke(question)

    print("Q:", result["question"])
    print("A:", result["answer"])
    print("Sources:", [d.metadata.get("filename") for d in result["documents"]])


if __name__ == "__main__":
    main()
```


## 실험 확장 포인트

이 템플릿에서 바로 확장할 부분은 4개입니다.

- `splitters.py`: 256/512/1024 chunk size와 overlap 실험. LangSmith와 RAGAS 지표 변화를 보기 좋습니다.[^5_1][^5_2]
- `retrievers.py`: vector only와 hybrid 비교. retrieval relevance와 context recall 차이를 볼 수 있습니다.[^5_5][^5_1]
- `rerankers.py`: NoOp vs cross-encoder 비교. groundedness와 factual correctness가 개선되는지 확인합니다.[^5_6][^5_2]
- `langsmith_eval.py`: correctness, relevance, groundedness, retrieval relevance evaluator 추가. LangSmith 튜토리얼의 핵심 축입니다.[^5_1]


## 바로 적용 팁

초기에는 너무 많은 기능을 넣지 않는 편이 좋습니다. 먼저 `VectorRetrieverAdapter + NoOpReranker + LangSmith eval`로 baseline을 만들고, 그 다음 순서로 `HybridRetrieverAdapter`, `CrossEncoderReranker`, `RAGAS batch eval`을 얹는 것이 안정적입니다.[^5_2][^5_1]

실무 기준으로는 다음 순서가 가장 효율적입니다.

1. 위 템플릿 그대로 실행 가능한 baseline 구축.
2. 질문 30~50개 규모의 고정 평가셋 작성. LangSmith는 dataset 기반 평가에 적합합니다.[^5_1]
3. chunk size와 top-k만 먼저 튜닝.
4. 그 다음 hybrid search 도입.
5. 마지막으로 reranking 추가. retrieval relevance와 groundedness 개선 여부를 확인합니다.[^5_2][^5_1]

원하시면 다음 답변에서 이어서 바로 **`langsmith_eval.py`에 들어갈 evaluator 함수 4종 전체 코드**, 그리고 **hybrid retriever/BM25 리트리버 예제**, **cross-encoder reranker 인터페이스 구현 예제**까지 붙여드리겠습니다.
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_18][^5_19][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://medium.com/@xzw0005/ai-agent-tutorial-2-retrieval-augmented-generation-rag-0a24b7d5f0de

[^5_2]: https://abvijaykumar.medium.com/hands-on-agentic-rag-2-3-agentic-reranking-rag-773b04cf4cdd

[^5_3]: https://docs.langchain.com/oss/python/langchain/retrieval

[^5_4]: https://rudaks.tistory.com/entry/langchain-LCEL로-RAG를-구현하는-기본-예제

[^5_5]: https://cookbook.openai.com/examples/multimodal/image_understanding_with_rag

[^5_6]: https://arxiv.org/html/2511.18177v1

[^5_7]: https://github.com/langchain-ai/langchain/discussions/22305

[^5_8]: https://docs.smith.langchain.com/old/cookbook/testing-examples/ragas

[^5_9]: https://docs.ragas.io/en/stable/howtos/integrations/langchain/

[^5_10]: https://medium.com/data-science/building-a-rag-chain-using-langchain-expression-language-lcel-3688260cad05

[^5_11]: https://www.youtube.com/watch?v=WC3t4pMKaVQ

[^5_12]: https://leeroopedia.com/index.php/Implementation:Vibrantlabsai_Ragas_EvaluationDataset_From_List

[^5_13]: https://agentfactory.panaversity.org/docs/Building-Custom-Agents/vector-databases-rag-langchain/building-retrieval-chains

[^5_14]: https://www.youtube.com/watch?v=vz0ERvLNbvw

[^5_15]: https://tds.s-anand.net/2026-02/docs/week-4/ragas-evaluation/

[^5_16]: https://docs.langchain.com/langsmith/evaluation-approaches

[^5_17]: https://www.youtube.com/watch?v=rEk_sFQt5Iw

[^5_18]: https://wikidocs.net/293304

[^5_19]: https://campus.datacamp.com/courses/developing-llm-applications-with-langchain/retrieval-augmented-generation-rag?ex=12

