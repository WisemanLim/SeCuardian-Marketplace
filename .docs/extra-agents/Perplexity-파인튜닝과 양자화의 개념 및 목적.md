<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## 파인튜닝과 양자화의 개념 및 목적

파인튜닝(Fine-Tuning)은 사전학습된 대규모 언어모델(LLM)을 특정 도메인이나 작업에 최적화하기 위해 추가 학습을 수행하는 기법입니다. 반면 양자화(Quantization)는 모델의 가중치와 활성화 값을 더 낮은 비트 수(예: 32비트→8비트 또는 4비트)로 표현하여 모델 크기와 메모리 사용량을 줄이고 연산 속도를 향상시키는 최적화 기법입니다.[^1_1][^1_2][^1_3]

두 기술의 근본적인 차이는 목적에 있습니다. 파인튜닝은 모델의 **성능과 정확도 향상**에 초점을 맞추는 반면, 양자화는 **효율성과 배포 용이성**을 목표로 합니다. 최근 연구에서는 이 두 기술을 결합하여 제한된 자원 환경에서도 고성능 LLM을 활용할 수 있는 방법론이 활발히 연구되고 있습니다.[^1_4][^1_5][^1_6][^1_7]

## 주요 양자화 기법 비교

### PTQ와 QAT의 기술적 차이

양자화는 수행 시점에 따라 크게 두 가지로 구분됩니다. **PTQ(Post-Training Quantization)**는 학습이 완료된 모델을 캘리브레이션 데이터를 사용하여 양자화하는 방식으로, 추가 학습이 필요하지 않아 빠르고 간편합니다. **QAT(Quantization-Aware Training)**는 학습 과정에 가짜 양자화(fake quantization) 노드를 삽입하여 양자화 효과를 모델이 학습하도록 하는 방식으로, PTQ보다 정확도 손실이 적지만 추가 학습 리소스가 필요합니다.[^1_5][^1_8][^1_9]


| 구분 | PTQ | QAT |
| :-- | :-- | :-- |
| 수행 시점 | 학습 완료 후 | 학습 중 |
| 데이터 요구사항 | 소량의 캘리브레이션 데이터 | 전체 학습 데이터셋 필요 |
| 리소스 요구량 | 낮음 (재학습 불필요) | 높음 (추가 학습 필요) |
| 정확도 | 일반적으로 약간의 손실 | FP32 근접 유지 가능 |
| 적용 난이도 | 쉬움 | 복잡함 |
| 활용 시나리오 | 엣지/모바일 배포, 빠른 프로토타입 | 프로덕션 환경의 고정확도 요구 시 |

[^1_9][^1_10]

### QLoRA의 혁신적 접근

QLoRA(Quantized Low-Rank Adaptation)는 파인튜닝과 양자화를 효과적으로 결합한 대표적 기법입니다. 이 방법은 4비트 NormalFloat(NF4) 데이터 타입, 이중 양자화(double quantization), 그리고 페이지드 옵티마이저(paged optimizer)라는 세 가지 핵심 기술을 도입했습니다. QLoRA는 65B 파라미터 모델을 단일 48GB GPU에서 파인튜닝할 수 있게 하면서도 16비트 전체 파인튜닝과 동등한 성능을 유지합니다.[^1_3][^1_7][^1_11]

NF4는 정규분포를 따르는 가중치에 대해 정보이론적으로 최적화된 데이터 타입으로, 일반 4비트 양자화보다 우수한 성능을 보입니다. 이중 양자화는 양자화 상수 자체를 다시 양자화하여 메모리 사용량을 추가로 절감하며, 페이지드 옵티마이저는 메모리 스파이크를 효과적으로 관리합니다.[^1_11][^1_3]

## 학술 연구 동향 및 주요 논문

### QEFT: 통합 최적화 프레임워크

Lee et al. (2024)이 EMNLP 2024 Findings에 발표한 "QEFT: Quantization for Efficient Fine-Tuning of LLMs" 논문은 추론 속도, 파인튜닝 속도, 메모리 소비, 모델 품질이라는 네 가지 측면을 동시에 개선하는 경량 기법을 제안합니다. 기존 연구들이 이 네 가지를 모두 향상시키는 데 실패한 반면, QEFT는 이론적 기반과 높은 유연성, 하드웨어 호환성을 갖추고 전정밀도 PEFT와 동등한 품질을 유지하면서도 더 적은 리소스를 사용합니다.[^1_6][^1_1]

**논문 정보:**

- 제목: QEFT: Quantization for Efficient Fine-Tuning of LLMs
- 저자: Changhun Lee, Jun-gyu Jin, Younghyun Cho, Eunhyeok Park
- 출판: EMNLP 2024 Findings
- arXiv: https://arxiv.org/abs/2410.08661
- DOI: https://doi.org/10.48550/arXiv.2410.08661

[^1_1][^1_6]

### 안전성 관점의 분석

Kumar et al. (2024)의 "Fine-Tuning, Quantization, and LLMs: Navigating Unintended Outcomes" 논문은 파인튜닝과 양자화가 LLM의 안전성에 미치는 영향을 체계적으로 분석합니다. Mistral, Llama, Qwen, MosaicML 등의 모델을 평가한 결과, 파인튜닝은 일반적으로 jailbreak 공격 성공률을 증가시키는 반면, 양자화는 가변적인 영향을 미친다는 것을 발견했습니다. 특히 2비트 양자화는 취약성을 크게 증가시키지만, 4비트와 8비트 양자화는 안전성을 더 잘 유지하는 경향이 있습니다.[^1_12][^1_13][^1_1]

**논문 정보:**

- 제목: Fine-Tuning, Quantization, and LLMs: Navigating Unintended Outcomes
- 저자: Divyanshu Kumar, Anurakt Kumar, Sahil Agarwal, Prashanth Harshangi
- arXiv: https://arxiv.org/abs/2404.04392
- DOI: https://doi.org/10.48550/arXiv.2404.04392

[^1_13][^1_12][^1_1]

### QLoRA의 이론적 기여

Dettmers et al. (2023)이 NeurIPS 2023에 발표한 QLoRA 논문은 양자화된 LLM의 효율적 파인튜닝 분야에서 획기적인 기여를 했습니다. 이 연구는 1,000개 이상의 모델을 파인튜닝하여 instruction following과 챗봇 성능을 8개의 instruction 데이터셋, 다양한 모델 타입, 그리고 일반 파인튜닝으로는 실행 불가능한 33B 및 65B 규모에서 상세히 분석했습니다. Guanaco라는 최고 성능 모델은 Vicuna 벤치마크에서 모든 이전 오픈소스 모델을 능가하며 ChatGPT 성능의 99.3%에 도달했습니다.[^1_7][^1_11]

**논문 정보:**

- 제목: QLoRA: Efficient Finetuning of Quantized LLMs
- 저자: Tim Dettmers et al.
- 출판: NeurIPS 2023
- GitHub: https://github.com/artidoro/qlora
- Paper: https://proceedings.neurips.cc/paper_files/paper/2023/file/1feb87871436031bdc0f2beaa62a049b-Paper-Conference.pdf

[^1_14][^1_7][^1_11]

## 국내 연구 및 산업 적용 사례

### 도메인 특화 파인튜닝 연구

한국정보처리학회(KIPS)에 발표된 "도메인 전문성 강화를 위한 LLM 파인튜닝" 연구는 도메인 특화 데이터셋을 적용한 파인튜닝이 모델의 정밀도 향상에 미치는 영향을 분석합니다. 이 연구는 데이터 구축, 모델 선정, 파인튜닝 실행의 전체 절차를 체계적으로 다루며, 실무 적용 가능성을 검증했습니다.[^1_15]

**논문 출처:**

- 제목: 도메인 전문성 강화를 위한 LLM 파인튜닝
- 학회: 한국정보처리학회(KIPS) 2025 학술대회
- 링크: https://www.manuscriptlink.com/society/kips/conference/ack2025/file/downloadSoConfManuscript/abs/KIPS_C2025B0013F

[^1_15]

### 개인 맞춤형 시스템 개발

DBpia에 게재된 "LLM 파인튜닝 및 양자화를 통한 개인 맞춤형 운전자 지원 시스템의 추론 성능 개선" 연구는 자동차 산업 분야에서 LLM 최적화 기법의 실용적 적용을 보여줍니다. 이 연구는 파인튜닝과 양자화를 결합하여 엣지 디바이스에서도 실시간으로 작동 가능한 개인화된 운전자 지원 시스템을 구현했습니다.[^1_16]

**논문 출처:**

- 제목: LLM 파인튜닝 및 양자화를 통한 개인 맞춤형 운전자 지원 시스템의 추론 성능 개선
- 데이터베이스: DBpia (한국학술정보)
- 링크: https://www.dbpia.co.kr/Journal/articleDetail?nodeId=NODE12047123

[^1_16]

### 기업 기술 블로그 분석

삼성전자 Tech Blog의 "파인튜닝으로 LLM 편향 개선하기" 연구는 파인튜닝 전후 모델 응답을 분석하여 LLM이 기술적 근거(FP, TU)를 바탕으로 응답하는 비율이 약 40% 이상 증가함을 보고했습니다. 이는 파인튜닝이 단순히 성능 향상뿐만 아니라 모델의 편향을 개선하는 데에도 효과적임을 입증합니다.[^1_17]

**출처:**

- 제목: 파인튜닝으로 LLM 편향 개선하기
- 발행: Samsung Tech Blog (2025년 12월)
- 링크: https://techblog.samsung.com/blog/article/75

[^1_17]

NVIDIA 개발자 블로그의 "QAT로 정확도와 성능을 높이는 gpt-oss 파인튜닝"은 OpenAI의 gpt-oss 오픈소스 모델에 대한 양자화 인지 학습(QAT) 적용 사례를 다룹니다. 전문가 혼합(MoE) 아키텍처와 128K 컨텍스트 길이를 가진 모델에 QAT를 적용하여 정확도와 추론 성능을 동시에 개선하는 방법론을 제시합니다.[^1_8]

**출처:**

- 제목: QAT로 정확도와 성능을 높이는 gpt-oss 파인튜닝
- 발행: NVIDIA Developer Blog (2025년 8월)
- 링크: https://developer.nvidia.com/ko-kr/blog/fine-tuning-gpt-oss-for-accuracy-and-performance-with-quantization-aware-training/

[^1_8]

## 기술적 구현 및 실무 고려사항

### 메모리 효율성 비교

파인튜닝과 양자화를 결합할 때 메모리 사용량은 크게 감소합니다. 16비트 부동소수점에서 4비트 정수로 양자화하면 메모리 사용량을 40~50% 추가로 줄일 수 있으며, LoRA와 같은 PEFT(Parameter-Efficient Fine-Tuning) 기법을 함께 사용하면 메모리 절감 효과가 더욱 증대됩니다. QLoRA의 경우 옵티마이저 상태(optimizer states)의 메모리 사용량도 크게 줄여 전체 메모리 footprint를 극적으로 감소시킵니다.[^1_18][^1_2][^1_4][^1_7][^1_11]

### 정확도 trade-off 분석

양자화로 인한 정확도 손실은 비트 수와 양자화 방법에 따라 다릅니다. 일반적으로 8비트 양자화는 거의 손실 없이 모델을 압축할 수 있으며, 4비트 양자화에서도 QLoRA의 NF4와 같은 고급 기법을 사용하면 전정밀도와 동등한 성능을 유지할 수 있습니다. 그러나 2비트 이하로 내려가면 성능 저하가 현저해지며 안전성 취약점도 증가합니다.[^1_7][^1_9][^1_11][^1_1]

### 배포 환경별 전략

엣지 디바이스나 모바일 환경에서는 PTQ가 선호되며, 프로덕션 환경에서 고정확도가 요구될 때는 QAT가 적합합니다. Ollama와 같은 플랫폼을 활용하면 양자화된 모델을 GGUF 포맷으로 변환하여 로컬 API 서버로 배포할 수 있으며, RESTful API를 통해 외부에서 접근 가능합니다. Hugging Face의 transformers 라이브러리와 PEFT는 BitsandbytesConfig를 통해 양자화 파라미터를 세밀하게 제어할 수 있는 인터페이스를 제공합니다.[^1_10][^1_18][^1_9][^1_11]

## 향후 연구 방향

현재 연구 커뮤니티는 양자화의 "스위트 스팟(sweet spot)" 기법 개발, 안전성을 고려한 파인튜닝 방법론, 작업별 취약성 조사, 그리고 안전 메트릭과 작업 성능을 통합 평가하는 포괄적 벤치마크 개발에 집중하고 있습니다. 또한 sub-4비트 정수 양자화, 동적 양자화 스케일 조정, 그리고 하드웨어 가속기 최적화를 통한 추가적인 효율성 향상도 활발히 연구되고 있습니다.[^1_19][^1_1][^1_7]
<span style="display:none">[^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30]</span>

<div align="center">⁂</div>

[^1_1]: https://www.themoonlight.io/ko/review/fine-tuning-quantization-and-llms-navigating-unintended-outcomes

[^1_2]: https://velog.io/@boks/730-Today-I-Learned-2

[^1_3]: https://wikidocs.net/251902

[^1_4]: https://blog.mondrian.ai/fine-tuning-lora-qlora-guide

[^1_5]: https://cdn.day1company.io/prod/uploads/202501/122009-1154/-패스트캠퍼스--교육과정소개서-llm-모델-파인튜닝을-위한-quantization.pdf

[^1_6]: https://arxiv.org/abs/2410.08661

[^1_7]: https://www.semanticscholar.org/paper/QLoRA:-Efficient-Finetuning-of-Quantized-LLMs-Dettmers-Pagnoni/32ac52069e562d4f900afee70bdca63f53461481

[^1_8]: https://developer.nvidia.com/ko-kr/blog/fine-tuning-gpt-oss-for-accuracy-and-performance-with-quantization-aware-training/

[^1_9]: https://velog.io/@lyh205/PTQ-QAT

[^1_10]: https://apxml.com/courses/practical-llm-quantization/chapter-4-quantization-aware-training-qat/qat-vs-ptq-comparison

[^1_11]: https://github.com/artidoro/qlora

[^1_12]: https://velog.io/@480/GenAI-기초-2탄-파인튜닝-세부-기술-양자화

[^1_13]: https://arxiv.org/abs/2404.04392

[^1_14]: https://proceedings.neurips.cc/paper_files/paper/2023/file/1feb87871436031bdc0f2beaa62a049b-Paper-Conference.pdf

[^1_15]: https://www.manuscriptlink.com/society/kips/conference/ack2025/file/downloadSoConfManuscript/abs/KIPS_C2025B0013F

[^1_16]: https://www.dbpia.co.kr/Journal/articleDetail?nodeId=NODE12047123

[^1_17]: https://techblog.samsung.com/blog/article/75

[^1_18]: https://projectjo.tistory.com/entry/파인-튜닝Fine-tuning-양자화Quantization-1

[^1_19]: https://dl.acm.org/doi/full/10.1145/3689236.3695383

[^1_20]: https://fastcampus.co.kr/data_online_quantization

[^1_21]: https://www.linkedin.com/posts/donghyeon-han-90b439170_llm%EC%9D%84-%EC%9C%84%ED%95%9C-%EC%9D%B8%EC%8A%A4%ED%8A%B8%EB%9F%AD%EC%85%98%ED%94%84%EB%A1%AC%ED%94%84%ED%8A%B8-%ED%8C%8C%EC%9D%B8%ED%8A%9C%EB%8B%9D-%EC%B5%9C%EC%8B%A0-%EC%97%B0%EA%B5%AC-%EB%8F%99%ED%96%A5-%EB%B0%8F-%EC%8B%9C%EC%82%AC%EC%A0%90-%EB%B6%84%EC%84%9D-activity-7095058579342151681-1GhA

[^1_22]: https://uracle.blog/2025/04/25/llm-파인튜닝-효과적인-활용과-대안-전략/

[^1_23]: https://blog.naver.com/qualcommkr/221687419678

[^1_24]: https://arxiv.org/html/2410.08661v1

[^1_25]: https://github.com/pprp/Awesome-LLM-Quantization

[^1_26]: https://www.sciencedirect.com/science/article/pii/S2949719125000202

[^1_27]: https://openreview.net/pdf/0bb10a37bfdc1bd7e1835ea3728115e6947ec3f5.pdf

[^1_28]: https://medium.com/better-ml/quantization-aware-training-qat-vs-post-training-quantization-ptq-cd3244f43d9a

[^1_29]: https://www.youtube.com/watch?v=sLEuVm9ZdxQ

[^1_30]: https://openreview.net/attachment?id=WvFoJccpo8\&name=pdf


---

## QLoRA와 LoRA의 성능 및 메모리 효율성 상세 비교

QLoRA와 LoRA는 모두 파라미터 효율적 파인튜닝(PEFT) 기법이지만, 메모리 효율성과 학습 속도 측면에서 명확한 차이를 보입니다. LoRA는 사전학습된 가중치를 고정하고 저랭크 행렬(low-rank matrices)의 곱으로 가중치 업데이트를 근사하여 학습 파라미터를 대폭 줄이는 반면, QLoRA는 여기에 4비트 양자화를 추가로 적용하여 메모리 사용량을 더욱 감소시킵니다.[^2_1][^2_2][^2_3]

### 메모리 효율성 비교

QLoRA는 LoRA 대비 최대 GPU 메모리 사용량이 약 75% 더 작습니다. Google Cloud의 벤치마크에 따르면, openLLaMA-7B 모델을 A100 40GB GPU 1개에서 파인튜닝할 때 LoRA는 배치 크기 2를 권장하는 반면, QLoRA는 배치 크기 24까지 가능합니다. L4 GPU 1개에서는 LoRA가 배치 크기 1에서도 OOM(Out of Memory) 오류가 발생하지만, QLoRA는 배치 크기 12를 지원합니다. 70억 파라미터 모델의 경우 LoRA 파인튜닝에 약 28GB가 필요하지만(전체 파인튜닝의 100GB 이상과 비교), QLoRA를 사용하면 단일 A100 80GB로 700억 파라미터 모델도 처리할 수 있습니다.[^2_3][^2_4]

### 학습 속도와 비용 비교

LoRA는 파인튜닝 속도 측면에서 QLoRA보다 약 66% 빠르며, 비용은 최대 40% 더 저렴합니다. 이는 QLoRA가 양자화와 역양자화 과정을 거치면서 추가적인 연산 오버헤드가 발생하기 때문입니다. LoRA가 A100과 같은 고급 GPU 여러 장을 필요로 했다면, QLoRA는 RTX 3090이나 RTX 4090 같은 소비자용 GPU 한 장으로도 충분합니다.[^2_4][^2_5][^2_1][^2_3]

### 정확도 비교

놀라운 점은 QLoRA가 메모리를 대폭 절감하면서도 정확도 손실이 거의 없다는 것입니다. Dettmers et al. (2023)의 NeurIPS 논문에 따르면, QLoRA는 MMLU 벤치마크에서 전체 16비트 파인튜닝이 68.3%의 정확도를 보일 때 67.9%를 기록하여 99% 이상의 성능을 유지했습니다. Google Cloud 데이터도 두 방법 모두 비슷한 정확도 개선사항을 제공한다고 보고합니다.[^2_6][^2_1][^2_3]


| 비교 항목 | LoRA | QLoRA |
| :-- | :-- | :-- |
| GPU 메모리 사용량 | 기준 | LoRA 대비 75% 감소 [^2_3] |
| 학습 속도 | QLoRA 대비 66% 빠름 [^2_3] | 더 느림 (양자화 오버헤드) |
| 비용 효율성 | QLoRA 대비 40% 더 비쌈 [^2_3] | 더 저렴함 |
| 배치 크기 (A100 40GB) | 배치 크기 2 [^2_3] | 배치 크기 24 [^2_3] |
| 최대 시퀀스 길이 | 제한적 | 더 긴 길이 지원 [^2_3] |
| 정확도 | 높음 | LoRA와 동등 (99% 이상) [^2_1][^2_3] |
| 추천 하드웨어 | 24GB 이상 GPU [^2_1] | RTX 3090/4090 (소비자용) [^2_1][^2_4] |
| 학습 가능 파라미터 | 전체의 0.1~1% [^2_7] | LoRA와 동일 |

### QLoRA의 핵심 기술

QLoRA는 세 가지 핵심 기술로 메모리 효율성을 극대화합니다. **NF4(4비트 NormalFloat)**는 정규분포를 따르는 가중치에 대해 정보이론적으로 최적화된 데이터 타입으로, 일반 4비트 양자화보다 우수한 성능을 보입니다. **이중 양자화(Double Quantization)**는 양자화 상수 자체를 다시 양자화하여 메모리 사용량을 추가로 절감하며, **페이지드 옵티마이저(Paged Optimizer)**는 메모리 스파이크 시 옵티마이저 상태를 CPU 메모리로 페이징하여 OOM 충돌을 방지합니다.[^2_8][^2_9][^2_4]

## 온디바이스 AI를 위한 최신 경량화 모델 압축 기술 트렌드

온디바이스 AI는 클라우드가 아닌 엣지 디바이스에서 AI를 구동하기 위해 모델 경량화가 필수적입니다. 2026년 현재 LLM을 스마트폰과 IoT 기기 같은 제한적 환경에서 구동하기 위한 경량화 기술은 크게 네 가지 범주로 발전하고 있습니다.[^2_10][^2_11][^2_12]

### 양자화(Quantization)

양자화는 모델의 가중치와 활성화 함수를 FP32에서 INT8 또는 INT4로 변환하여 모델 크기를 줄이고 연산 속도를 향상시킵니다. QLoRA와 같은 기법은 효율적인 미세 조정을 가능하게 하며, LG경영연구원 보고서에 따르면 파라미터와 시냅스의 수를 변화시키지 않고 용량을 줄일 수 있는 방법으로 온디바이스 AI의 핵심 기술로 부상하고 있습니다.[^2_13][^2_11][^2_10]

### 가지치기(Pruning)

가지치기는 모델의 중요도가 낮은 연결이나 뉴런을 제거하여 희소성을 증가시키고 모델 크기를 줄입니다. 구조적 가지치기(Structured Pruning)는 하드웨어 가속에 유리하며, 특정 블록이나 레이어 전체를 제거하여 실제 추론 속도 향상을 달성합니다. Frontiers in Robotics and AI 저널(2025)에 발표된 서베이 논문은 모델 압축 기술을 모델 가지치기, 모델 증류, 저랭크 분해, 양자화의 네 가지 도메인으로 분류했습니다.[^2_14][^2_15][^2_16][^2_17][^2_10]

### 지식 증류(Knowledge Distillation)

지식 증류는 대규모 Teacher 모델의 지식을 소규모 Student 모델로 전이시켜 작은 모델이 큰 모델의 성능을 모방하도록 훈련합니다. Redis의 2026년 가이드에 따르면, 지식 증류는 양자화 및 가지치기와 결합하여 사용할 때 비용 절감과 속도 향상을 동시에 달성할 수 있습니다. 특히 Stable Diffusion과 같은 생성 모델에서는 U-Net에 구조적 가지치기를 수행한 후 원본 모델을 Teacher로 활용하는 통합 최적화 전략이 효과적입니다.[^2_18][^2_19][^2_16][^2_10]

### 효율적인 아키텍처 및 최적화 프레임워크

Mixtral의 Sparse Mixture-of-Experts(MoE) 구조, 그룹화된 쿼리 어텐션(Grouped-query Attention), 그리고 LoRA 같은 PEFT 기법은 모델의 파라미터 효율성을 극대화합니다. 또한 OpenVINO, ONNX Runtime, TensorRT와 같은 최적화 프레임워크는 특정 하드웨어에 최적화된 추론을 가능하게 합니다. 충북대학교 AEL 연구실의 기술 동향 보고서는 온디바이스 AI 하드웨어 및 소프트웨어 통합 최적화의 중요성을 강조하고 있습니다.[^2_20][^2_10]

### 최신 연구 동향

Promwad(2025)의 연구는 실시간 엣지 디바이스를 위한 가지치기, 양자화, 하이브리드 압축 전략을 탐구하며, 이러한 기법들이 2025년 이후 실시간 디바이스에서 AI 모델을 효율적으로 만드는 방법을 제시합니다. AHHA Labs의 분석에 따르면, 경량 알고리즘 설계와 알고리즘 경량화 기술이 최근 활발히 연구되고 있으며, 두 접근법의 결합이 온디바이스 AI의 핵심 도전 과제를 해결하고 있습니다.[^2_12][^2_21]

## 양자화된 모델의 정확도 손실을 최소화하는 캘리브레이션 기법

양자화 과정에서 정확도 손실을 최소화하기 위해서는 적절한 스케일(Scale)과 영점(Zero-Point) 파라미터를 결정하는 캘리브레이션이 핵심입니다. ApX Machine Learning의 실무 가이드에 따르면, PTQ의 효과는 캘리브레이션 데이터가 실제 추론 시 데이터 분포를 얼마나 잘 대표하는지, 그리고 양자화 파라미터가 원본 부동소수점 범위의 필수 정보를 얼마나 정확하게 포착하는지에 달려 있습니다.[^2_22][^2_13]

### 캘리브레이션 워크플로우

PTQ의 전형적인 캘리브레이션 워크플로우는 다음과 같습니다. 먼저 사전학습된 FP32 모델을 준비하고, 추론 시 마주칠 데이터 유형을 반영하는 소량의 대표 데이터셋(캘리브레이션 데이터셋)을 선택합니다. 이 데이터셋을 원본 FP32 모델로 추론하면서 가중치와 중간 활성화 값의 범위(최소/최대값) 통계를 수집합니다. 수집된 통계를 사용하여 양자화할 각 텐서(가중치 및 활성화)에 대한 적절한 스케일과 영점을 계산하고, 이를 바탕으로 모델 가중치를 FP32에서 목표 저정밀도 형식(예: INT8)으로 변환합니다.[^2_22]

### 대칭 양자화 vs 비대칭 양자화

양자화 스킴은 영점 처리 방식에 따라 구분됩니다. **대칭 양자화(Symmetric Quantization)**는 영점을 0으로 고정하여 계산을 단순화하는 반면, **비대칭 양자화(Asymmetric Quantization)**는 실수 0이 양자화된 정수 범위 내의 값에 정확하게 매핑되도록 보장합니다. 위키독스의 양자화 사전에 따르면, 역양자화(Dequantization) 과정에서 완벽한 복원은 불가능하지만 적절한 스케일과 영점을 사용하면 정확도 손실을 최소화할 수 있습니다.[^2_13][^2_22]

### 대조 학습 기반 캘리브레이션

CVPR 2024에 발표된 "Enhancing Post-training Quantization Calibration through Contrastive Learning" 논문은 정보 이론의 상호 정보(Mutual Information)를 PTQ 캘리브레이션에 도입했습니다. 이 연구는 양자화 전후 활성화 간의 상호 정보를 최대화하여 양자화된 활성화를 캘리브레이션하는 것을 목표로 합니다. 대조 학습(Contrastive Learning) 프레임워크를 통해 동일한 입력 샘플에서 수집된 양자화된 활성화와 FP 활성화의 positive pairs를 끌어당기고, 다른 샘플의 negative pairs를 밀어냅니다. 정교하게 설계된 critic function 덕분에 캘리브레이션 데이터가 제한된 상황에서도 충돌 솔루션(collision solution)을 피할 수 있으며, 이론적으로 설계된 손실을 최소화하는 것이 원하는 상호 정보를 최대화하는 것과 동등함을 보장합니다.[^2_23][^2_1]

**논문 정보:**

- 제목: Enhancing Post-training Quantization Calibration through Contrastive Learning
- 저자: Yuzhang Shang, Gaowen Liu, Ramana Kompella, Yan Yan
- 출판: CVPR 2024
- 링크: https://cvpr.thecvf.com/virtual/2024/poster/30493

[^2_1][^2_23]

### 통계적 사전 캘리브레이션

2025년 1월 arXiv에 공개된 "Rethinking Post-Training Quantization: Introducing a Statistical Pre-Calibration" 논문은 가중치 적응형 PTQ 방법을 제안합니다. 이 방법은 양자화된 가중치와 원래 학습된 가중치 간의 Kullback-Leibler divergence를 최소화하여 가중치 분포를 보존합니다. 이러한 최소화는 양자화된 모델이 원본 모델의 Shannon 정보 내용을 상당 부분 유지하도록 보장하여, 많은 작업에서 강건하고 효율적인 배포를 가능하게 합니다. 연구 결과 이 사전 캘리브레이션 결과가 다양한 LLM에서 일부 기존 캘리브레이션 기반 PTQ 방법과 동일한 정확도를 달성하며, 추가 캘리브레이션 조정을 위한 새로운 사전 캘리브레이션 단계를 확립합니다.[^2_24]

### QAT를 통한 정확도 손실 최소화

양자화 인지 학습(QAT)은 학습 과정에서 양자화를 모사(simulate)하여 정확도 손실을 줄이는 방법입니다. 작은 모델들은 양자화 후에 정확도가 떨어지는 경향이 있으므로, 학습 과정에서 양자화를 고려하는 것이 중요합니다. Dohyeon의 논문 리뷰에 따르면, 다양한 캘리브레이션 기법들을 적용해보고 모델 정확도를 비교하여 자신의 모델에 적합한 방법을 찾아야 하며, QAT가 일반적으로 PTQ보다 우수한 성능을 보입니다.[^2_25][^2_26]

## DoRA: 차세대 PEFT 기법

DoRA(Weight-Decomposed Low-Rank Adaptation)는 LoRA와 QLoRA를 능가하는 최신 PEFT 기법으로, 2024년 ICML에서 발표되어 주목받고 있습니다. Liu et al.의 연구는 가중치를 크기(magnitude)와 방향(direction) 두 가지 구성요소로 분해하여 파인튜닝하는 혁신적 접근법을 제안합니다.[^2_27][^2_28][^2_29]

### DoRA의 성능 우위

DoRA는 LLaMA-7B/13B, LLaMA2-7B, LLaMA3-8B에서 LoRA 및 다른 PEFT 방법들을 일관되게 능가합니다. LLaMA-7B에서 DoRA는 commonsense reasoning 벤치마크에서 LoRA 대비 평균 3.7% 향상된 78.4%의 정확도를 달성했으며, LLaMA3-8B에서는 4.4% 향상되어 85.2%를 기록했습니다. 특히 랭크를 절반으로 줄인 DoRA†도 LoRA보다 우수한 성능을 보여, DoRA가 LoRA의 학습 능력을 향상시켜 더 높은 랭크 없이도 정확도를 개선할 수 있음을 입증했습니다.[^2_28][^2_29][^2_27]

**논문 정보:**

- 제목: DoRA: Weight-Decomposed Low-Rank Adaptation
- 저자: Shih-Yang Liu, Chien-Yi Wang, Hongxu Yin, Pavlo Molchanov, Yu-Chiang Frank Wang, Kwang-Ting Cheng, Min-Hung Chen
- 출판: ICML 2024
- GitHub: https://github.com/NVlabs/DoRA
- arXiv: https://arxiv.org/html/2402.09353v5

[^2_29][^2_27][^2_28]

### 가중치 분해 분석

DoRA의 핵심은 Weight Normalization에서 영감을 받은 가중치 분해 분석입니다. 연구팀은 VL-BART 모델을 네 가지 이미지-텍스트 작업으로 파인튜닝하고 query/value 가중치 행렬을 분석한 결과, LoRA는 방향과 크기 변화 간에 일관된 양의 기울기(positive slope)를 보이는 반면, Full Fine-Tuning(FT)은 음의 기울기(negative slope)를 나타냈습니다. LoRA와 FT 간의 상관계수는 각각 +0.83과 -0.62였으며, DoRA는 -0.31로 FT와 유사한 패턴을 보였습니다. 이는 DoRA가 큰 방향 변화와 작은 크기 변화(또는 그 반대)를 독립적으로 조정할 수 있는 능력을 갖추고 있음을 의미합니다.[^2_29]

### QDoRA: QLoRA의 향상

DoRA는 QLoRA와도 결합 가능하며, QDoRA라는 변형은 QLoRA의 성능을 더욱 향상시킵니다. 또한 DoRA는 VeRA와 같은 다른 LoRA 변형과도 호환되며, DVoRA(DoRA+VeRA)는 LLaMA-7B에서 VeRA 대비 0.7점, LLaMA2-7B에서 0.5점 향상된 성능을 보였습니다. DVoRA는 LoRA의 1/100 파라미터만으로도 LoRA와 동등하거나 더 나은 성능을 달성했습니다.[^2_30][^2_29]

### 실무 적용 가이드

Liner의 리뷰에 따르면, DoRA는 Prefix, Series, Parallel 어댑터를 포함한 모든 PEFT 방법을 일관되게 능가하며 추가 추론 오버헤드가 없습니다. Towards AI의 분석은 "LoRA는 기본, QLoRA는 메모리 해킹, DoRA는 업그레이드"라고 요약하며, DoRA가 학습 능력과 안정성을 모두 향상시키는 차세대 PEFT 솔루션임을 강조합니다.[^2_31][^2_27]
<span style="display:none">[^2_32][^2_33][^2_34][^2_35]</span>

<div align="center">⁂</div>

[^2_1]: https://blog.mondrian.ai/fine-tuning-lora-qlora-guide

[^2_2]: https://hyundoil.tistory.com/400

[^2_3]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/lora-qlora?hl=ko

[^2_4]: https://introl.com/ko/blog/fine-tuning-infrastructure-lora-qlora-peft-scale-guide-2025

[^2_5]: https://velog.io/@lyh205/PTQ-QAT

[^2_6]: https://www.semanticscholar.org/paper/QLoRA:-Efficient-Finetuning-of-Quantized-LLMs-Dettmers-Pagnoni/32ac52069e562d4f900afee70bdca63f53461481

[^2_7]: https://www.youngju.dev/blog/llm/2026-03-11-llm-finetuning-lora-qlora-peft-practical-guide

[^2_8]: https://wikidocs.net/251902

[^2_9]: https://github.com/artidoro/qlora

[^2_10]: https://www.aiazit.com/issue/513?page=2

[^2_11]: https://www.lgbr.co.kr/uploadFiles/ko/pdf/busi/LGBR_Report_240408_20242808162819203.pdf

[^2_12]: https://ahha.ai/2024/08/13/lightweight/

[^2_13]: https://wikidocs.net/120218

[^2_14]: https://dmqa.korea.ac.kr/activity/seminar/382

[^2_15]: https://pub.towardsai.net/the-5-model-compression-techniques-how-to-shrink-ai-10-without-losing-accuracy-d87e889d6a2a

[^2_16]: https://www.meta-intelligence.tech/en/insight-integrated-optimization

[^2_17]: https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1518965/full

[^2_18]: https://www.youngju.dev/tags/model-compression

[^2_19]: https://redis.io/blog/model-distillation-llm-guide/

[^2_20]: http://ael.cbnu.ac.kr/lectures/graduate/ICT융합특론/15/15-이석준.pdf

[^2_21]: https://promwad.com/news/ai-model-compression-real-time-devices-2025

[^2_22]: https://apxml.com/courses/practical-llm-quantization/chapter-2-post-training-quantization-ptq/principles-ptq

[^2_23]: https://cvpr.thecvf.com/virtual/2024/poster/30493

[^2_24]: https://tldr.takara.ai/p/2501.09107

[^2_25]: https://github.com/Pseudo-Lab/EfficientML/discussions/13

[^2_26]: https://dohyeon.tistory.com/99

[^2_27]: https://liner.com/review/dora-weightdecomposed-lowrank-adaptation

[^2_28]: https://arxiv.org/html/2402.09353v5

[^2_29]: https://fastcampus.co.kr/data_online_quantization

[^2_30]: https://turingpost.co.kr/p/dora-qlora-qdora

[^2_31]: https://pub.towardsai.net/lora-qlora-dora-which-fine-tuning-method-should-you-actually-use-296b53ea1aa9

[^2_32]: https://wikidocs.net/338716

[^2_33]: https://www.youtube.com/watch?v=bC9nLbAcoPQ

[^2_34]: https://www.facebook.com/i.amanchadha/photos/️-invited-talk-at-the-𝐔𝐧𝐢𝐯𝐞𝐫𝐬𝐢𝐭𝐲-𝐨𝐟-𝐒𝐨𝐮𝐭𝐡-𝐂𝐚𝐫𝐨𝐥𝐢𝐧𝐚-on-𝐌𝐨𝐝𝐞𝐥-𝐂𝐨𝐦𝐩𝐫𝐞𝐬𝐬𝐢𝐨𝐧-𝐟𝐨𝐫-𝐎𝐧-𝐃/26713710141562858/

[^2_35]: https://docs.pytorch.org/TensorRT/ts/ptq.html


---

## LLM 모델 양자화의 최신 트렌드: GPTQ, AWQ, EXL2 비교

LLM 양자화는 모델의 가중치와 활성화 값을 저정밀도로 변환하여 메모리 사용량과 추론 속도를 개선하는 핵심 기술입니다. 2026년 현재 GPTQ, AWQ, EXL2, GGUF, FP8 등 다양한 양자화 방법이 경쟁하고 있으며, 각 기법은 하드웨어 환경과 성능 요구사항에 따라 차별화된 장점을 제공합니다.[^3_1][^3_2][^3_3][^3_4]

### GPTQ (GPT-Quantization)

GPTQ는 레이어별 양자화를 수행하며 역헤시안(inverse Hessian) 정보를 활용하여 가중치를 업데이트함으로써 정확도 손실을 완화하는 가중치 전용 양자화 기법입니다. Frantar et al. (2022)이 제안한 이 방법은 각 열을 순차적으로 처리하며 매번 오류를 재계산하기 때문에 양자화 속도가 비교적 느립니다. GPTQ는 INT4 양자화의 사실상 표준으로 자리잡았으며, NVIDIA GPU에서 최적화되어 있습니다. AutoGPTQ와 vLLM의 llmcompressor 두 가지 구현체가 있으며, 구현 방식에 따라 정확도 차이가 발생할 수 있습니다.[^3_2][^3_5][^3_3][^3_6][^3_7][^3_8][^3_1]

**논문 정보:**

- 제목: GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers
- 저자: Elias Frantar et al.
- 출판: 2022
- 특징: 그룹 크기 128 권장, 대칭 양자화, activation descent 옵션

[^3_6][^3_8][^3_2]

### AWQ (Activation-Aware Weight Quantization)

AWQ는 활성화 크기가 큰 채널의 중요한 가중치를 보존하는 것이 양자화 오류를 줄이는 핵심이라는 통찰에 기반합니다. Lin et al. (2024)의 연구에 따르면, AWQ는 채널별 스케일링을 사용하여 활성화 크기가 큰 채널에 집중하며, GPTQ보다 약 2배 빠른 추론 속도를 제공합니다. arXiv 논문(2409.11055v1)의 벤치마크 결과에 따르면, AWQ는 다양한 LLM에서 GPTQ를 일관되게 능가하며 전체 벤치마크 점수에서 우수한 성능을 보입니다.[^3_9][^3_7][^3_4][^3_10][^3_8]

**논문 정보:**

- 제목: AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration
- 저자: Ji Lin et al.
- 출판: 2024
- arXiv: https://arxiv.org/abs/2306.00978
- 특징: 비대칭 양자화, 그룹 크기 128, 빠른 추론 속도

[^3_7][^3_11][^3_8]

### EXL2 (ExLlamaV2)

EXL2는 가장 최신의 정교한 양자화 포맷으로, GPU 전용으로 설계되어 가장 빠른 추론 속도를 제공합니다. Reddit의 LocalLLaMA 커뮤니티 상세 비교에 따르면, EXL2는 GPTQ보다 3~4배 빠른 속도를 보이며, 8비트 캐시를 지원하여 컨텍스트에 필요한 메모리를 절반으로 줄입니다. EXL2는 상대 프로베니우스 노름(relative Frobenius norm)을 최소화하여 원본 모델을 가장 정확하게 재현하려 하며, 2~8비트 사이의 임의 양자화(예: 2.5 bpw)를 지원합니다.[^3_12][^3_13][^3_14][^3_9]

그러나 EXL2는 GGUF에 비해 품질이 낮은 양자화를 사용하므로, 동일한 크기의 모델에서 출력 품질이 상당히 낮을 수 있다는 지적도 있습니다. 또한 tabbyAPI와 text-generation-webui 등 제한된 백엔드에서만 지원됩니다.[^3_9][^3_12]

### GGUF (GPT-Generated Unified Format)

GGUF는 GGML의 최신 버전으로, 모델에 대한 추가 정보를 포함하여 다중 아키텍처 지원과 프롬프트 템플릿을 개선했습니다. GGUF는 CPU에서 완전히 실행되거나 GPU로 부분적 또는 완전히 오프로드될 수 있으며, K-quants를 사용하여 2비트에서 8비트까지 압축 가능합니다. GGUF의 핵심 장점은 캘리브레이션 데이터가 필요 없고 빠른 양자화 속도로 여러 모델을 테스트하기에 적합하다는 점입니다.[^3_14][^3_15][^3_2][^3_9]

### 성능 비교 분석

| 비교 항목 | GPTQ | AWQ | EXL2 | GGUF |
| :-- | :-- | :-- | :-- | :-- |
| 추론 속도 | 보통 | 빠름 (GPTQ 대비 2배) [^3_9] | 매우 빠름 (GGUF 대비 3~4배) [^3_9] | CPU 최적화 |
| 양자화 속도 | 느림 (순차 처리) [^3_5] | 보통 | 느림 (리소스 집약적) [^3_12] | 매우 빠름 [^3_14] |
| 정확도 (Perplexity) | 중간 [^3_13] | 높음 (GPTQ보다 우수) [^3_8] | 높음 (최적화된 재현) [^3_13] | 높음 (데이터 독립적) [^3_14] |
| 메모리 효율성 | 기본 | 기본 | 우수 (8비트 캐시) [^3_9] | 우수 |
| 캘리브레이션 필요 | 필요 | 필요 | 필요 | 불필요 [^3_14] |
| 하드웨어 최적화 | NVIDIA GPU [^3_3] | NVIDIA GPU | GPU 전용 [^3_9] | CPU/GPU 범용 [^3_9] |
| 비트 범위 | 4비트 주력 | 4비트 주력 | 2~8비트 (분수 지원) [^3_13] | 2~8비트 (K-quants) |
| LoRA 병합 지원 | 어려움 [^3_14] | 어려움 [^3_14] | 제한적 | 용이 |
| 추천 사용 사례 | 빠른 테스트, 일반 배포 [^3_3] | 프로덕션, 품질 중시 [^3_3] | 최대 성능, 충분한 VRAM [^3_9] | CPU 워크로드, 빠른 실험 [^3_9] |

### 최신 벤치마크 결과

arXiv 논문 2409.11055v1 "A Comprehensive Evaluation of Quantized Instruction-Tuned Large Language Models"의 405B 규모까지의 실험 결과는 다음과 같은 핵심 발견을 제시합니다:[^3_10][^3_8]

1. **AWQ의 우수성**: AWQ는 다양한 LLM에서 전체 벤치마크 점수에서 GPTQ를 일관되게 능가합니다[^3_8][^3_10]
2. **모델 크기별 차이**: Llama-3.1-8B의 경우 8비트가 4비트보다 12개 벤치마크에서 높은 정확도를 보이지만, Llama-3.1-70B에서는 GPTQ 4비트가 8비트보다 평균 0.32%(v1), 1.9%(v2) 더 높은 정확도를 달성합니다[^3_8]
3. **SmoothQuant의 한계**: Llama-3.1-405B에서 SmoothQuant는 FP8 대비 평균 -2.93%(v1), -9.23%(v2)의 정확도 하락을 보여, 초대형 모델의 높은 활성화 범위를 효과적으로 완화하지 못합니다[^3_8]
4. **FP8의 안정성**: FP8는 가중치와 활성화를 모두 8비트로 양자화할 때 SmoothQuant보다 안정적이며, NVIDIA H100과 RTX6000Ada 같은 하드웨어에서 지연시간과 처리량 모두에서 이점을 제공합니다[^3_8]

## 온디바이스 AI를 위한 모델 경량화 기술 스택 구축 가이드

온디바이스 AI 구현을 위해서는 경량화된 AI 모델, 시스템 소프트웨어 스택, AI 하드웨어의 세 가지 요소가 유기적으로 결합되어야 합니다. arXiv 논문 2503.06027v1 "A Comprehensive Survey on On-Device AI Models"는 온디바이스 AI의 전체 파이프라인을 데이터 전처리, 모델 개발, 시스템 통합의 세 단계로 구조화합니다.[^3_16][^3_17][^3_18]

### Phase 1: 데이터 최적화 (Data Optimization)

데이터 전처리는 온디바이스 AI 파이프라인의 첫 단계로, 원시 데이터의 품질과 관련성을 보장합니다. **데이터 필터링(Data Filtering)**은 불일치와 오류를 제거하여 정제된 데이터셋을 생성하고, **특징 추출(Feature Extraction)**은 차원을 줄이면서도 필수 정보를 유지합니다. **데이터 집계(Data Aggregation)**는 여러 소스의 정보를 통합하여 일관성을 향상시키며, **데이터 양자화(Data Quantization)**는 데이터 표현의 정밀도를 낮춰 엣지 디바이스에서의 효율적 처리를 가능하게 합니다.[^3_19][^3_18]

### Phase 2: 모델 압축 (Model Compression)

모델 최적화는 4가지 핵심 기술로 구성됩니다:[^3_20][^3_18]

#### 2.1 양자화 (Quantization)

양자화는 FP32를 INT8 또는 INT4로 변환하여 모델 크기를 줄이고 연산 속도를 향상시킵니다. 온디바이스 미디어 제작을 위한 생성형 인공지능 경량화 기술 현황 보고서에 따르면, 양자화는 파라미터와 시냅스의 수를 변화시키지 않고 용량을 줄일 수 있는 방법으로 온디바이스 AI의 핵심 기술입니다.[^3_18][^3_19]

#### 2.2 가지치기 (Pruning)

가지치기는 중요도가 낮은 가중치나 뉴런을 제거하여 모델의 희소성을 증가시킵니다. **구조적 가지치기(Structured Pruning)**는 특정 블록이나 레이어 전체를 제거하여 하드웨어 가속에 유리하며 실제 추론 속도 향상을 달성합니다. **비구조적 가지치기(Unstructured Pruning)**는 개별 가중치를 제거하여 더 높은 압축률을 달성하지만 특수한 하드웨어 지원이 필요할 수 있습니다.[^3_21][^3_20][^3_18]

#### 2.3 지식 증류 (Knowledge Distillation)

지식 증류는 대규모 Teacher 모델의 지식을 소규모 Student 모델로 전이시켜 작은 모델이 큰 모델의 성능을 모방하도록 훈련합니다. Redis의 2026년 가이드에 따르면, 지식 증류는 양자화 및 가지치기와 결합할 때 비용 절감과 속도 향상을 동시에 달성할 수 있습니다.[^3_22][^3_20][^3_18]

#### 2.4 저랭크 분해 (Low-Rank Factorization)

저랭크 분해는 큰 가중치 행렬을 두 개의 작은 행렬로 분해하여 파라미터 수를 줄입니다. LoRA(Low-Rank Adaptation)와 같은 기법은 사전학습된 가중치를 고정하고 저랭크 어댑터만 학습하여 메모리 효율성을 극대화합니다.[^3_23][^3_18]

### Phase 3: 시스템 최적화 (System Optimization)

시스템 통합은 소프트웨어와 하드웨어 최적화를 모두 포함합니다.[^3_20][^3_18]

#### 3.1 소프트웨어 최적화

| 최적화 프레임워크 | 전문 분야 | 지원 하드웨어 |
| :-- | :-- | :-- |
| TensorFlow Lite | 모바일/엣지 디바이스 | ARM, GPU, DSP |
| PyTorch Mobile | 크로스 플랫폼 | iOS, Android |
| ONNX Runtime | 범용 최적화 | CPU, GPU, NPU |
| TensorRT | NVIDIA GPU 최적화 | NVIDIA GPU |
| OpenVINO | 인텔 하드웨어 | Intel CPU, GPU, VPU |
| Core ML Tools | Apple 생태계 | Apple Silicon, Neural Engine |

[^3_23][^3_18][^3_20]

#### 3.2 하드웨어 최적화

전용 하드웨어 가속기 설계는 AI 모델의 계산 효율성을 크게 향상시킵니다. **TPU (Tensor Processing Units)**와 **FPGA (Field Programmable Gate Arrays)**는 AI 작업에 일반적으로 사용되는 특정 유형의 계산에 최적화되어 범용 프로세서보다 빠른 처리와 낮은 전력 소비를 가능하게 합니다.[^3_24][^3_18]

arXiv 서베이에 따르면, 온디바이스 AI를 위한 주요 엣지 디바이스는 다음과 같습니다:[^3_18]


| 디바이스 | 주요 사양 | 활용 사례 |
| :-- | :-- | :-- |
| NVIDIA Jetson Xavier NX | 6-core ARM CPU, 384-core GPU, 21 TOPS | 로봇공학, 컴퓨터 비전 |
| Google Coral Dev Board | Edge TPU, 4 TOPS, 저전력(2-4W) | 이미지 인식, 객체 감지 |
| Raspberry Pi 4 | Quad-core ARM CPU, 최대 8GB RAM | IoT, 홈 오토메이션 |
| Intel NUC | 최대 i7 프로세서 지원 | 디지털 사이니지, 산업 자동화 |

[^3_18]

### Phase 4: 배포 및 모니터링

모델 배포 후에는 지속적인 성능 검증과 모니터링이 필수입니다. 압축 메트릭으로는 크기 축소(2-10배), 속도 향상(2-5배), 정확도 유지(95% 이상), 메모리 감소(2-8배)를 목표로 합니다.[^3_20]

### 통합 최적화 전략

Samsung의 온디바이스 AI 기술 인터뷰에 따르면, 각 디바이스 모델은 고유한 메모리 아키텍처와 컴퓨팅 프로필을 가지므로 일반적인 접근 방식으로는 클라우드 수준의 AI 성능을 제공할 수 없습니다. 따라서 하드웨어-소프트웨어 공동 설계(hardware-software co-design) 접근법이 에너지 효율성을 위해 두 구성요소를 모두 최적화하여 전체 시스템 성능을 향상시킵니다.[^3_17][^3_24][^3_18]

## PTQ와 QAT의 장단점 및 캘리브레이션 정밀도 차이 분석

양자화는 수행 시점에 따라 PTQ(Post-Training Quantization)와 QAT(Quantization-Aware Training)로 구분되며, 각각의 접근법은 정확도, 리소스 요구량, 구현 복잡도에서 명확한 trade-off를 보입니다.[^3_25][^3_26]

### PTQ (Post-Training Quantization)

PTQ는 학습이 완료된 FP32 모델을 TFLite Converter, TensorRT 등의 변환기에서 캘리브레이션을 통해 스케일(Scale)과 제로포인트(Zero-Point)를 추정해 INT8/FP16으로 변환하는 방식입니다. PTQ의 핵심 아이디어는 재학습 없이 정적 또는 동적 보정으로 모델을 변환하는 것이며, "대체로 적은" 정확도 손실로 모델 크기와 지연시간을 줄이는 것이 목표입니다.[^3_26][^3_27][^3_25]

**PTQ의 장점:**

- 소량의 캘리브레이션 데이터만 필요하며 재학습이 불필요하여 빠른 배포 가능[^3_28][^3_25]
- 구현이 쉽고 시간이 적게 소요되어 배포 전 마지막 최적화에 적합[^3_25][^3_26]
- 대부분의 런타임과 가속기(TFLite, TensorRT, OpenVINO)에서 지원[^3_25]

**PTQ의 단점:**

- QAT 대비 정확도 손실이 상대적으로 큼[^3_28][^3_25]
- 4비트 이하로 내려가면 1% 이상의 정확도 손실 발생 가능[^3_27]
- 캘리브레이션 데이터가 실제 추론 데이터 분포를 얼마나 잘 대표하는지에 따라 효과가 크게 달라짐[^3_29]


### QAT (Quantization-Aware Training)

QAT는 학습 단계에 가짜양자화(fake quantization) 노드를 삽입하여 순전파에서 양자화 효과를 모사하고, 역전파로 양자화 민감도를 학습시켜 저정밀 연산에 강인한 파라미터를 얻는 방식입니다. NVIDIA 개발자 블로그의 분석에 따르면, QAT는 모델이 사전학습 후 추가 학습 단계에서 저정밀도 연산을 처리하는 법을 학습하는 기법입니다.[^3_30][^3_26][^3_25]

**QAT의 장점:**

- 학습 과정에서 양자화의 영향을 반영하여 정확도 손실을 크게 회복[^3_28][^3_25]
- PTQ보다 정확도 손실이 현저히 적으며, INT8 속도와 FP32 근접 정확도가 필수일 때 유리[^3_30][^3_25]
- 1-bit/2-bit 초저비트 양자화에서도 성능 유지 가능[^3_27]
- 동일한 하드웨어 지원(TensorRT/torch-tensorrt가 QAT 산출물을 잘 최적화)[^3_25]

**QAT의 단점:**

- 추가 학습 필요(수~수십 epoch의 미세튜닝)로 리소스 요구량 높음[^3_26][^3_25]
- 설정과 훈련 비용이 높아 난이도가 상승[^3_28][^3_25]
- 대규모 LLM의 경우 막대한 재학습 비용으로 인해 PTQ가 더 선호됨[^3_31][^3_8]


### 장단점 종합 비교

| 구분 | PTQ | QAT |
| :-- | :-- | :-- |
| 핵심 아이디어 | 학습 후 FP32 모델을 정적/동적 보정으로 변환 | 학습 중 가짜양자화로 저정밀 연산 모사하며 재학습 |
| 데이터/리소스 | 소량 캘리브레이션 데이터, 재학습 불필요 → 빠른 배포 | 추가 학습 필요(수~수십 epoch), 리소스 더 필요 |
| 정확도 | 대체로 약간 손실 (작업/모델에 따라 편차) | PTQ 대비 정확도 손실 크게 회복 |
| 난이도/시간 | 쉬움·빠름, 배포 전 마지막 최적화 적합 | 설정·훈련 비용 증가, 정확도 요구치 높을 때 유리 |
| 하드웨어 지원 | 대부분 런타임/가속기 지원 | 동일하게 지원, TensorRT 최적화 우수 |
| 대표 유즈케이스 | 엣지·모바일, PoC, 재학습 여건 없을 때 | 프로덕션에서 INT8 속도 + FP32 근접 정확도 필수 |
| LLM 적용성 | 선호됨 (재학습 비용 부담) [^3_8] | 제한적 (막대한 재학습 비용) [^3_8] |

[^3_26][^3_27][^3_25]

### 캘리브레이션 정밀도 차이

PTQ의 캘리브레이션은 양자화 파라미터(스케일과 영점)가 원본 부동소수점 범위의 필수 정보를 얼마나 정확하게 포착하는지에 달려 있습니다. **대칭 양자화(Symmetric Quantization)**는 영점을 0으로 고정하여 계산을 단순화하는 반면, **비대칭 양자화(Asymmetric Quantization)**는 실수 0이 양자화된 정수 범위 내의 값에 정확하게 매핑되도록 보장합니다.[^3_29][^3_26]

QAT의 경우 학습 과정에서 클리핑 레벨(clipping level)을 자동으로 튜닝하여 전정밀도 정확도와 양자화 정확도 사이의 적절한 trade-off를 조절합니다. 예를 들어 ReLU의 경우 양수 값에 제한이 없어 양자화 시 큰 값들이 모두 줄어들면서 양자화 오류가 커지는데, Clip ReLU를 사용하고 학습 과정에서 적절한 클리핑 레벨을 찾음으로써 이를 보완합니다.[^3_27]

### 정밀도 손실 최소화 기법

Monday9pm의 딥러닝 양자화 분석에 따르면, QAT의 경우 **Loss Scaling**을 통해 gradient 소실 문제를 해결합니다. loss에 스케일을 한 번만 주면 backprop 하면서 gradient도 모두 스케일되며, 스케일이 너무 커지면 양수 값이 날아갈 수 있기 때문에 adaptive하게 정합니다.[^3_26][^3_27]

MyungHak의 양자화 방법론 분석은 QAT가 정밀도 유지, 효율적 배포, 메모리 사용량과 계산 비용 절감을 동시에 달성할 수 있다고 강조합니다. 특히 8비트까지 줄이면 accumulation 시에 문제가 생기므로, floating point quantization에서 bias를 adaptive하게 정하는 것이 중요합니다.[^3_27][^3_28]

arXiv 논문 2509.21173v3 "Can Less Precise Be More Reliable?"는 대규모 모델 양자화가 데이터 프리 PTQ와 더 정확하지만 비용이 많이 드는 QAT 사이의 trade-off를 포함한다고 지적합니다. 실무에서는 대부분의 LLM이 재학습 비용 때문에 PTQ를 채택하지만, 정확도가 중요한 프로덕션 환경에서는 QAT가 여전히 필수적입니다.[^3_31][^3_25][^3_8]
<span style="display:none">[^3_32][^3_33][^3_34][^3_35]</span>

<div align="center">⁂</div>

[^3_1]: https://www.youngju.dev/blog/llm/2026-03-14-llm-quantization-gptq-awq-gguf-guide

[^3_2]: https://peterica.tistory.com/1001

[^3_3]: https://www.youtube.com/watch?v=F4mGvf-65x4

[^3_4]: https://ai.rs/ai-developer/quantization-methods-compared

[^3_5]: https://wikidocs.net/338712

[^3_6]: https://asidefine.tistory.com/318

[^3_7]: https://drfirst.tistory.com/entry/LLM모델의-양자화Quantization-GPTQ-및-AWQ-방식-알아보

[^3_8]: https://projectjo.tistory.com/entry/파인-튜닝Fine-tuning-양자화Quantization-1

[^3_9]: https://www.reddit.com/r/LocalLLaMA/comments/1ayd4xr/for_those_who_dont_know_what_different_model/

[^3_10]: https://arxiv.org/html/2409.11055v1

[^3_11]: https://www.newline.co/@zaoyang/gptq-vs-awq-quantization--d792476e

[^3_12]: https://arca.live/b/alpaca/118956660

[^3_13]: https://www.reddit.com/r/LocalLLaMA/comments/17fuqr7/a_detailed_comparison_between_gptq_awq_exl2_q4_k/

[^3_14]: https://github.com/ml-explore/mlx/issues/135

[^3_15]: https://oobabooga.github.io/blog/posts/gptq-awq-exl2-llamacpp/

[^3_16]: https://www.efactorynews.com/sub_view.asp?ch=1\&t=0\&idx=21106

[^3_17]: https://news.samsung.com/global/interview-the-technologies-bringing-cloud-level-intelligence-to-on-device-ai

[^3_18]: https://velog.io/@boks/730-Today-I-Learned-2

[^3_19]: https://www.kibme.org/resources/journal/20250508095331015.pdf

[^3_20]: https://kodkodkod.studio/blog/ai-model-compression/

[^3_21]: https://www.meta-intelligence.tech/en/insight-integrated-optimization

[^3_22]: https://redis.io/blog/model-distillation-llm-guide/

[^3_23]: https://www.facebook.com/groups/DeepNetGroup/posts/2721202618272603/

[^3_24]: http://ael.cbnu.ac.kr/lectures/graduate/ICT융합특론/15/15-이석준.pdf

[^3_25]: https://velog.io/@lyh205/PTQ-QAT

[^3_26]: https://monday9pm.com/deep-learning-quantization-딥-러닝-양자화-6fb30c642cf7

[^3_27]: https://u-b-h.tistory.com/13

[^3_28]: https://myunghaklee.github.io/quantization/quantization_method/

[^3_29]: https://apxml.com/courses/practical-llm-quantization/chapter-2-post-training-quantization-ptq/principles-ptq

[^3_30]: https://developer.nvidia.com/blog/how-quantization-aware-training-enables-low-precision-accuracy-recovery/

[^3_31]: https://arxiv.org/html/2509.21173v3

[^3_32]: https://wikidocs.net/book/19058

[^3_33]: https://blog.gopenai.com/exploring-bits-and-bytes-awq-gptq-exl2-and-gguf-quantization-techniques-with-practical-examples-74d590063d34

[^3_34]: https://www.youngju.dev/blog/llm/2026-03-06-llm-quantization-gptq-awq-gguf-comparison.en

[^3_35]: https://arxiv.org/html/2503.06027v1


---

## FP8 양자화가 추론 성능과 호환성에 미치는 영향 분석

FP8(8비트 부동소수점) 양자화는 NVIDIA H100 및 Intel Gaudi 2와 같은 최신 AI 가속기에서 네이티브로 지원되어 LLM 추론 성능을 획기적으로 향상시키는 기술입니다. arXiv 논문 2502.01070v1 "An Investigation of FP8 Across Accelerators for LLM Inference"는 FP8 연산과 가속이 두 가지 주요 AI 가속기인 NVIDIA H100과 Intel Gaudi 2에서 어떻게 작동하는지 최초로 종합적으로 분석합니다.[^4_1][^4_2][^4_3][^4_4]

### FP8의 성능 향상

NVIDIA H100에서 FP8는 FP16 대비 2배의 성능 향상과 2배의 메모리 요구량 감소를 제공합니다. TensorRT-LLM 평가 결과 H100 FP8는 A100 대비 최대 4.6배의 최대 처리량과 4.4배 빠른 첫 토큰 지연시간을 달성합니다. GPT-J 6B 모델에서 H100은 64개의 동시 요청에서 10,000 출력 토큰/초 이상의 피크 처리량을 달성하면서도 첫 토큰 지연시간을 100ms로 유지합니다. 최소 지연시간 애플리케이션의 경우 TRT-LLM H100은 10ms 미만의 첫 토큰 지연시간을 달성할 수 있습니다.[^4_5][^4_6][^4_7]

**성능 벤치마크 (H100 FP8 vs A100):**


| 모델 | 배치 크기 | 처리량 (tok/s) | 첫 토큰 지연시간 | 속도 향상 |
| :-- | :-- | :-- | :-- | :-- |
| GPT-J 6B | 64 | 10,907 (H100) vs 3,679 (A100) | 102ms vs 481ms | 3.0x 처리량, 4.7x 지연시간 |
| GPT-J 6B | 1 | 185 (H100) vs 111 (A100) | 7.1ms vs 12.5ms | 2.4x 처리량, 1.7x 지연시간 |

[^4_7]

### FP8 데이터 타입: E4M3 vs E5M2

FP8 포맷은 지수와 가수에 할당된 비트 수에 따라 두 가지 변형으로 나뉩니다. **E4M3 포맷**은 4비트 지수와 3비트 가수로 구성되어 더 높은 정밀도를 제공하며, **E5M2 포맷**은 5비트 지수와 2비트 가수로 구성되어 더 넓은 동적 범위를 제공합니다. arXiv 논문의 실험 결과에 따르면, E4M3는 언어 작업에서 E5M2보다 일관되게 우수한 정확도를 달성합니다.[^4_8][^4_4]

**E4M3 vs E5M2 정확도 비교 (MMLU CoT 5-shot):**


| 모델 | BF16 | E4M3 | E5M2 | 정확도 차이 |
| :-- | :-- | :-- | :-- | :-- |
| Llama v3.2 1B Instruct | 46.3% | 45.5% | 44.5% | E4M3가 1.0%p 우수 |
| Llama v3.2 3B Instruct | 61.8% | 61.6% | 60.7% | E4M3가 0.9%p 우수 |
| Llama v3.1 8B Instruct | 68.8% | 68.3% | 67.5% | E4M3가 0.8%p 우수 |
| Llama v3.3 70B Instruct | 82.0% | 82.0% | 82.2% | E5M2가 0.2%p 우수 |

[^4_4]

### 동적 스케일링 vs 정적 스케일링

FP8 양자화에서 스케일링 팩터 계산 방법은 추론 품질에 큰 영향을 미칩니다. **정적 스케일링(Static Scaling)**은 캘리브레이션 데이터셋을 사용하여 사전에 스케일링 팩터를 계산하는 반면, **동적 스케일링(Dynamic Scaling)**은 각 입력에 대해 런타임에 스케일링 팩터를 계산합니다. arXiv 논문의 비교 분석 결과, 동적 양자화는 원본 BF16 모델과 유사한 결과를 얻는 반면, 정적 양자화는 눈에 띄는 정확도 저하를 초래합니다.[^4_4]

**동적 vs 정적 스케일링 정확도 비교 (Llama v3.1 8B Instruct):**


| 벤치마크 | BF16 | FP8 정적 | FP8 동적 | 정확도 차이 |
| :-- | :-- | :-- | :-- | :-- |
| MMLU CoT 5-shot | 68.8% | 66.3% | 68.3% | 동적이 2.0%p 우수 |
| GSM8K CoT 5-shot | 83.1% | 70.4% | 84.5% | 동적이 14.1%p 우수 |
| Winogrande | 73.8% | 77.6% | 73.8% | 동일 |

[^4_4]

### 하드웨어별 FP8 구현 차이

NVIDIA GPU와 Intel Gaudi HPU는 모두 FP8 사양을 준수하지만 구현에서 주요 차이점이 있습니다:[^4_4]

1. **누산 정밀도**: Hopper GPU는 FP8 GEMM에 14비트 누산기를 사용하여 더 높은 정밀도를 위해 CUDA 코어로 캐스팅이 필요한 반면, Gaudi HPU는 항상 FP32로 누산하여 더 높은 수치 정밀도를 보장합니다[^4_4]
2. **E4M3 범위**: Gaudi 2는 IEEE 사양을 따르며 NVIDIA GPU와 달리 E4M3의 최대값이 240입니다(NVIDIA는 448)[^4_4]
3. **하드웨어 가속 스케일링**: Gaudi HPU는 부동소수점 지수 바이어스 수정을 허용하여 스케일링 팩터 적용을 가속화하며, Gaudi 2는 E4M3에 대해 2^{-8}, 2^{-4}, 2^{0}, 2^{4}의 고정 하드웨어 가속 스케일링 팩터를 지원합니다[^4_4]

### Prefill vs Decode 단계에서의 FP8 성능

arXiv 논문의 핵심 발견은 FP8의 효과가 추론 단계에 따라 크게 다르다는 것입니다. **Prefill 단계**에서는 H100의 처리량이 Gaudi 2보다 50% 높지만, **Decode 단계**는 전체 추론 시간을 지배하며 가속기 활용도가 더 중요해져 Gaudi 2가 이 단계에서 50% 더 높은 처리량을 달성합니다. Gaudi 2는 특히 작은 행렬에서 H100보다 높은 활용도를 달성하며, 행렬 크기 1K에서 더 높은 TFLOPS를 제공합니다.[^4_4]

**Thin GEMM 처리량 비교 (TFLOPS):**


| GEMM 형태 (M,K,N) | Gaudi 2 BF16 | Gaudi 2 FP8 | H100 BF16 | H100 FP8 |
| :-- | :-- | :-- | :-- | :-- |
| (8, 1024, 1024) | 3.3 | 3.8 | 1.7 | 1.7 |
| (16, 1024, 1024) | 6.5 | 11.4 | 3.4 | 3.9 |
| (64, 1024, 1024) | 26.7 | 54.0 | 12.6 | 14.9 |
| (64, 4096, 4096) | 144.5 | 253.4 | 133.3 | 133.9 |

[^4_4]

### FP8 호환성 및 실무 고려사항

Reddit의 LocalLLaMA 커뮤니티 논의에 따르면, FP8는 Hopper 및 Blackwell과 같은 아키텍처에서 하드웨어 최적화가 되어 있을 때 더 효과적으로 작동합니다. FP8와 INT8의 주요 차이점은 부동소수점과 정수 표현 사이에 있으며, FP8는 8비트 정수에 비해 더 큰 동적 범위를 제공합니다. Neural Magic의 벤치마크에 따르면, FP8 모델의 성능 메트릭은 원본 BF16 모델과 밀접하게 일치하며 Q8 GGUF와도 비슷합니다.[^4_9]

AWS Inferentia의 경우, 양자화는 weight 텐서에 대해 int8, fp8을 지원하며 KVcache의 경우 fp8 형태를 지원합니다. fp8의 경우 fp8e4m3, fp8e5m2 두 가지 형태가 있으며, 각각의 특성에 따라 선택적으로 사용할 수 있습니다.[^4_10]

## 최신 NPU 하드웨어 가속기에서의 LLM 추론 최적화 전략

NPU(Neural Processing Unit)는 CPU 및 GPU에 비해 지연 시간이 짧고 처리량이 높으며 전력 소비가 적어 온디바이스 AI에 점점 더 중요해지고 있습니다. Qualcomm, Intel, AMD와 같은 벤더들은 AI 워크로드를 가속화하기 위해 NPU를 설계하고 통합했습니다.[^4_11][^4_12][^4_13][^4_14]

### NPU 아키텍처 및 성능 특성

대부분의 모바일 NPU는 "벡터 + 매트릭스" 조합 아키텍처를 채택하며, 매트릭스 유닛은 행렬 곱셈과 컨볼루션 같은 연산을 가속화하고, 벡터 유닛은 정규화 및 복잡한 활성화 함수와 같은 범용 계산을 처리합니다. Qualcomm의 Hexagon NPU, Huawei의 Ascend NPU, AMD의 XDNA NPU, Intel NPU, Intel의 Gaudi HPU가 모두 이러한 아키텍처를 활용합니다.[^4_14]

**2026년 NPU 성능 비교:**


| NPU | TOPS (INT8) | 특징 |
| :-- | :-- | :-- |
| Qualcomm Snapdragon X Elite (Hexagon) | 45 TOPS [^4_14] | HVX + HMX 유닛, FP16/INT4/INT8 지원 |
| Intel Lunar Lake | 48 TOPS [^4_15] | 통합 NPU, 저전력 |
| Qualcomm Snapdragon X2 | 85 TOPS [^4_15] | 차세대 Hexagon, 향상된 처리량 |
| AMD XDNA | 60 TOPS [^4_15] | 3.1배 세대간 성능 향상 |
| Apple M4 Neural Engine | 38 TOPS [^4_15] | Apple Silicon 통합 |

[^4_15][^4_14]

### Qualcomm Hexagon NPU 최적화 전략

arXiv 논문 2509.23324v1 "Scaling LLM Test-Time Compute with Mobile NPU on Smartphones"는 모바일 NPU를 활용한 LLM 추론 최적화의 포괄적인 프레임워크를 제시합니다. Hexagon NPU의 핵심 특징은 다음과 같습니다:[^4_14]

1. **HVX (Hexagon Vector eXtension)**: 1024비트 폭의 32개 벡터 레지스터, 4~6개 유닛
2. **HMX (Hexagon Matrix eXtension)**: FP16 기준 32×32 타일, 1~2개 유닛, 최대 12 TFLOPS 성능
3. **메모리 서브시스템**: 1 MiB L2 캐시 + 8 MiB TCM (Tightly Coupled Memory)

Hexagon V75 NPU에서 FP16 GEMM 처리량을 측정한 결과, HMX의 처리량은 12 TFLOPS에 달하는 반면 HVX 단일 스레드는 32.93 GFLOPS에 불과하여 300배 이상의 차이를 보입니다. 이는 전용 매트릭스 유닛과 범용 벡터 유닛 간의 성능 격차를 명확히 보여줍니다.[^4_14]

### 하드웨어 인식 타일 양자화 기법

모바일 NPU의 주요 과제는 세밀한 그룹 양자화에 대한 네이티브 하드웨어 지원 부족입니다. 기존 QNN(Qualcomm AI Engine Direct)은 per-tensor 또는 per-channel 양자화만 지원하며, Llama 3.2 1B-Instruct 모델에서 QNN의 per-channel 양자화는 MATH500에서 2.1% 정확도를 기록한 반면, AWQ의 per-group 4비트 양자화는 15.9%를 달성했습니다.[^4_14]

arXiv 논문은 이를 해결하기 위해 **하드웨어 인식 타일 양자화 스킴(Hardware-aware Tile Quantization Scheme)**을 제안합니다. 이 방법은 매트릭스 유닛이 기대하는 데이터 레이아웃에 맞춰 타일 기반 양자화 전략을 적용하고, 벡터 유닛의 처리 능력을 최대화하기 위한 양자화 후 가중치 순열 방법을 사용합니다. 그룹 크기 32에 대해 2×16 타일 단위로 그룹 양자화를 수행하며, 8개의 양자화 그룹을 하나의 슈퍼 그룹으로 통합하여 128바이트 폭의 벡터 레지스터를 효율적으로 활용합니다.[^4_14]

### LUT 기반 계산 최적화

벡터 유닛의 제한된 범용 컴퓨팅 성능을 보완하기 위해, LUT(Look-Up Table) 명령어를 사용하여 복잡한 연산을 대체합니다. 주요 최적화는 다음과 같습니다:[^4_14]

1. **빠른 Softmax**: FP16 입력을 사용하여 65536개 항목의 LUT를 32768개 항목(64 KiB)으로 축소하고, vgather 명령어로 지수 계산을 가속화하여 2.2배 속도 향상 달성[^4_14]
2. **효율적 역양자화**: vlut16 명령어를 사용하여 INT4 양자화 값을 FP16로 직접 변환하고, 4개 그룹의 스케일을 하나의 vlut16 명령어로 브로드캐스트하여 최대 19.0배 혼합 정밀도 GEMM 속도 향상[^4_14]

### Qualcomm NPU 벤치마크 결과

LiteRT를 사용한 Qualcomm NPU 성능 측정 결과는 다음과 같습니다:[^4_12]

**MobileNetv2 추론 지연시간 (ms):**


| 디바이스 | NPU (HTP용 QNN) | GPU (GPUv2) | CPU (XNNPACK) | NPU 속도 향상 |
| :-- | :-- | :-- | :-- | :-- |
| 삼성 S25 | **0.3ms** | 1.8ms | 2.8ms | GPU 대비 6.0배 |
| Samsung S24 | **0.4ms** | 2.3ms | 3.6ms | GPU 대비 5.8배 |
| Samsung S23 | **0.6ms** | 2.7ms | 4.1ms | GPU 대비 4.5배 |

**Phi-3 Mini (3.8B) 추론 지연시간 (ms):**


| 디바이스 | NPU (HTP용 QNN) | GPU (GPUv2) | CPU (XNNPACK) | NPU 속도 향상 |
| :-- | :-- | :-- | :-- | :-- |
| 삼성 S25 | **24.9ms** | 43ms | 481.7ms | GPU 대비 1.7배 |
| Samsung S24 | **29.8ms** | 52.6ms | 621.4ms | GPU 대비 1.8배 |
| Samsung S23 | **43.7ms** | 68.2ms | 871.1ms | GPU 대비 1.6배 |

[^4_12]

### 리벨리온 NPU 기반 LLM 서빙

국내 AI 반도체 기업 리벨리온은 NPU 기반 LLM 서빙 최적화를 위한 vLLM RBLN 플러그인을 제공합니다. vLLM RBLN 플러그인을 사용하면 최적화를 vLLM 워크플로우 내에서 그대로 활용하면서 기존 코드 수정 없이 NPU 기반의 성능과 효율을 그대로 누릴 수 있습니다. 이는 NPU가 데이터센터 환경에서도 GPU의 대안으로 자리잡고 있음을 보여줍니다.[^4_16][^4_17][^4_11]

### Groq LPU의 혁신적 성능

Groq의 LPU(Language Processing Unit)는 LLM 추론에 특화된 가속기로, LLM 벤치마크에서 GPU 대비 18배 가량 빠른 성능을 보여줍니다. Llama2 70B 모델에서 Groq LPU는 비교할 수 없는 성능을 보여주며, AI 작업이 얼마나 빠르고 효율적으로 실행될 수 있는지에 대한 가능성을 제시합니다. LPU는 최소한의 전력 소모, 낮은 지연 시간, 높은 성능으로 작동하여 추론 작업에 최적화되어 있습니다.[^4_11][^4_16]

## 온디바이스 LLM 배포를 위한 프레임워크별 런타임 성능 비교

온디바이스 LLM 배포를 위한 프레임워크는 하드웨어 최적화, 양자화 지원, 크로스 플랫폼 호환성에 따라 차별화됩니다. 2026년 현재 주요 프레임워크의 성능과 특징은 다음과 같습니다.[^4_18][^4_19]

### 주요 온디바이스 LLM 프레임워크

| 프레임워크 | 개발사 | 주요 플랫폼 | 핵심 강점 |
| :-- | :-- | :-- | :-- |
| **llama.cpp** | 오픈소스 | CPU, 모바일, 엣지 | C++ 엔진, 양자화 모델 지원, 다양한 백엔드 [^4_19] |
| **Ollama** | 오픈소스 | 데스크톱 (macOS, Linux, Windows) | 직관적 UI, 모델 관리 플랫폼 [^4_19] |
| **ONNX Runtime** | Microsoft | 크로스 플랫폼 | 하드웨어 가속 추론, 엔터프라이즈 지원 [^4_19] |
| **LiteRT (구 TFLite)** | Google | 모바일, 엣지, IoT | NPU 최적화, CompiledModel API [^4_18][^4_20] |
| **MediaPipe** | Google | Android | Android 디바이스 최적화 [^4_19] |
| **Core ML** | Apple | iOS, macOS | Apple Silicon, Neural Engine 활용 [^4_19] |
| **MLC LLM** | 오픈소스 | iOS, Android, Web | 컴파일러 기반, 고도 커스터마이징 [^4_19] |
| **Nexa AI SDK** | Nexa AI | 크로스 플랫폼 모바일 | 모바일 앱 통합 SDK [^4_19] |
| **Qualcomm AI Hub** | Qualcomm | Snapdragon | Snapdragon 칩 사전 최적화 [^4_19] |

[^4_19]

### LiteRT 2.x의 성능 향상

Google의 LiteRT는 TensorFlow Lite의 후속으로, 효율적인 변환, 런타임, 최적화를 사용하여 엣지 플랫폼에서 고성능 ML 및 생성형 AI를 배포하기 위한 온디바이스 프레임워크입니다. 최신 LiteRT 2.x 릴리스에서는 하드웨어 가속을 극대화하도록 설계된 최신 런타임 인터페이스인 **CompiledModel API**가 도입되었습니다. 기존 Interpreter API(이전 TensorFlow Lite)는 이전 버전과의 호환성을 위해 계속 사용할 수 있지만, CompiledModel API는 기기 내 AI 애플리케이션에서 최첨단 성능을 원하는 개발자에게 권장되는 선택입니다.[^4_20][^4_18]

LiteRT는 PyTorch, TensorFlow, JAX 프레임워크에서 `.tflite` 또는 `.litertlm` 형식으로의 간소화된 변환을 지원하며, Android, iOS, 웹, 데스크톱, IoT 플랫폼에서 고성능으로 ML 모델을 완전히 온디바이스로 실행할 수 있습니다.[^4_18][^4_20]

### llama.cpp NPU 백엔드 성능

arXiv 논문 2509.23324v1의 평가 결과는 llama.cpp의 NPU 백엔드가 GPU 백엔드(OpenCL)보다 우수한 성능을 보여줍니다. Qwen 2.5 1.5B 모델을 Snapdragon 8 Elite (V79 NPU) 기기에서 실행할 때, NPU 백엔드는 디코딩 단계에서 평균 2.2배 빠른 속도를 달성했습니다. 또한 전력 소비는 GPU 대비 약 40% 감소하여 에너지 효율성이 크게 향상되었습니다.[^4_14]

### 모바일 LLM의 제약조건 및 최적화 전략

모바일 LLM 배포 시 고려해야 할 주요 제약조건은 다음과 같습니다:[^4_21]

1. **메모리 제약**: 모델 가중치 + KV Cache + 런타임 오버헤드를 모두 고려해야 함
2. **속도 제약**: 사용자 경험을 위해 최소 10 tokens/sec 이상 권장
3. **발열 제약**: 지속적인 추론 시 열 관리 필수
4. **전력 효율**: 배터리 수명 고려 시 NPU 활용이 유리

[^4_21][^4_14]

### 프레임워크별 권장 사용 사례

| 프레임워크 | 권장 사용 사례 | 성능 특징 |
| :-- | :-- | :-- |
| llama.cpp + NPU | Snapdragon 디바이스, 고성능 필요 시 | 최고 추론 속도, 낮은 전력 소비 [^4_14] |
| LiteRT + Qualcomm Delegate | Android 프로덕션 앱 | NPU 네이티브 지원, 6배 GPU 대비 속도 향상 [^4_12] |
| Core ML | iOS/macOS 앱 | Apple Neural Engine 최적화 |
| ONNX Runtime | 크로스 플랫폼 엔터프라이즈 | 범용 최적화, 안정성 |
| MLC LLM | 고도 커스터마이징 필요 시 | 컴파일러 기반, 최대 유연성 |

[^4_19][^4_12][^4_14]

온디바이스 LLM 추론을 위한 LSM-트리 컴팩션 성능 특성화 연구에 따르면, 대규모 클라우드 기반 LLM은 우수한 추론 능력을 제공하지만 실시간 애플리케이션에 대한 엄청난 지연 시간을 초래하는 반면, 소규모 온디바이스 LLM은 낮은 지연 시간으로 실시간 반응성을 제공합니다. 따라서 애플리케이션의 지연시간 요구사항, 하드웨어 플랫폼, 모델 크기에 따라 적절한 프레임워크를 선택하는 것이 중요합니다.[^4_22]
<span style="display:none">[^4_23][^4_24][^4_25][^4_26][^4_27][^4_28][^4_29][^4_30][^4_31][^4_32]</span>

<div align="center">⁂</div>

[^4_1]: https://developer.nvidia.com/ko-kr/blog/nvidia-quantization-technology-and-tensorrt-llmbased-service-optimization/

[^4_2]: https://www.facebook.com/NVIDIA.KR/posts/️-fp8은-23배-향상된-처리량으로-fp16을-능가하는-tensorrt-llm입니다-초고속-추론-속도를-위해-지원되는-양자화-기법을-tenso/796193082548410/

[^4_3]: https://arxiv.org/html/2502.01070v1

[^4_4]: https://www.dbpia.co.kr/Journal/articleDetail?nodeId=NODE12047123

[^4_5]: https://lambda.ai/blog/nvidia-hopper-h100-and-fp8-support

[^4_6]: https://developer.nvidia.com/ko-kr/blog/nvidia-hopper-architecture-in-depth/

[^4_7]: https://nvidia.github.io/TensorRT-LLM/blogs/H100vsA100.html

[^4_8]: http://hc34.hotchips.org/assets/program/conference/day1/GPU HPC/HC2022.NVIDIA.Choquette.vfinal01.pdf

[^4_9]: https://www.reddit.com/r/LocalLLaMA/comments/1o3r6et/quality_degradation_of_fp8_quantization/

[^4_10]: https://aws.amazon.com/ko/blogs/tech/llm-model-quantization-techniques-for-aws-inferentia-by-nota-ai/

[^4_11]: https://discuss.pytorch.kr/t/groq-18-llm-lpu-language-processing-unit/3553

[^4_12]: https://ai.google.dev/edge/litert/android/npu/qualcomm?hl=ko

[^4_13]: https://arxiv.org/html/2509.23324v1

[^4_14]: https://wikidocs.net/251902

[^4_15]: https://localaimaster.com/blog/npu-comparison-2026

[^4_16]: https://kr.linkedin.com/pulse/gpu-vs-lpu-npu-which-ai-accelerator-should-you-host-server-mania-3iqsc?tl=ko

[^4_17]: https://kr.rebellions.ai/llm-serving-with-npu/

[^4_18]: https://ai.google.dev/edge/litert/overview?hl=ko

[^4_19]: https://www.linkedin.com/posts/shelbyheinecke_skip-the-cloud-these-9-frameworks-run-llms-activity-7359265484057296896-e86n

[^4_20]: https://github.com/google-ai-edge/litert

[^4_21]: https://wikidocs.net/336153

[^4_22]: https://alphaxiv.org/ko/overview/2602.12669v1

[^4_23]: https://introl.com/ko/blog/model-serving-optimization-quantization-pruning-distillation-inference

[^4_24]: https://www.youngju.dev/blog/llm/2026-03-14-llm-quantization-gptq-awq-gguf-guide

[^4_25]: https://www.reddit.com/r/LocalLLaMA/comments/1q9htxp/npu_support_for_distributed_inference_is_the_next/

[^4_26]: https://blog.naver.com/simula/224092182335

[^4_27]: https://tristanchoi.tistory.com/662

[^4_28]: https://discuss.pytorch.kr/t/flashattention-3-nvidia-hopper/4857

[^4_29]: https://ai.google.dev/edge/litert

[^4_30]: https://developer.nvidia.com/blog/achieving-high-mixtral-8x7b-performance-with-nvidia-h100-tensor-core-gpus-and-tensorrt-llm/

[^4_31]: https://www.horizoniq.com/blog/nvidia-h100-specs/

[^4_32]: https://www.computer.org/csdl/proceedings-article/coins/2025/11125797/29o5RcoLZw4


---

# 온디바이스 LLM 배포를 위한 프레임워크별 런타임 비교 보고서

TensorRT-LLM 기반 FP8 추론 파이프라인 구현 절차
FP8 양자화 적용 시 모델 정확도 손실 완화 캘리브레이션 기법
Intel Gaudi 3에서의 FP8 학습 및 추론 가속 성능 분석

이제 상세한 보고서를 작성하겠습니다.

## 온디바이스 LLM 배포를 위한 프레임워크별 런타임 성능 비교

온디바이스 LLM 배포는 클라우드가 아닌 로컬 디바이스에서 AI를 구동하기 위해 프레임워크 선택, 하드웨어 최적화, 모델 경량화를 종합적으로 고려해야 합니다. 2026년 현재 온디바이스 AI는 개인정보 보호, 지연시간 감소, 오프라인 사용 가능성이라는 핵심 가치를 실현하며 기업 AI 전략의 중심으로 자리잡고 있습니다.[^5_1][^5_2]

### 주요 프레임워크 특징 및 성능

| 프레임워크 | 플랫폼 지원 | 하드웨어 최적화 | 추론 속도 | 메모리 효율성 | 통합 난이도 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **LiteRT (구 TFLite)** | Android, iOS, 웹, 임베디드 | NPU, GPU, CPU 델리게이트 | 매우 빠름 | 우수 | 쉬움 |
| **Core ML** | iOS, macOS | Apple Neural Engine | 매우 빠름 | 우수 | 쉬움 (Apple 생태계) |
| **ONNX Runtime** | 크로스 플랫폼 | 다양한 EP 지원 | 빠름 | 양호 | 보통 |
| **llama.cpp** | 데스크톱, 모바일 | CPU, Metal, CUDA, OpenCL, NPU | 빠름 | 우수 | 보통 |
| **MediaPipe** | Android | Android GPU | 빠름 | 양호 | 쉬움 |
| **MLC LLM** | iOS, Android, 웹 | 컴파일러 기반 최적화 | 매우 빠름 | 우수 | 어려움 |
| **Qualcomm AI Hub** | Snapdragon | Hexagon NPU | 매우 빠름 | 우수 | 보통 |
| **Windows ML** | Windows 11 | DirectML, NPU | 빠름 | 양호 | 쉬움 |

[^5_3][^5_4][^5_5]

### LiteRT의 성능 우위

Google의 LiteRT 2.x는 최신 **CompiledModel API**를 도입하여 하드웨어 가속을 극대화했습니다. Qualcomm NPU 벤치마크에서 LiteRT는 MobileNetv2 추론 시 Samsung S25에서 0.3ms의 지연시간을 달성하여 GPU 대비 6배, CPU 대비 9배 빠른 성능을 보여줍니다. Phi-3 Mini (3.8B) 모델에서도 NPU가 24.9ms로 GPU의 43ms 대비 1.7배 빠른 추론 속도를 제공합니다.[^5_6][^5_7][^5_3]

**LiteRT의 핵심 강점:**

- PyTorch, TensorFlow, JAX에서 `.tflite` 또는 `.litertlm` 형식으로 간소화된 변환[^5_3]
- Android, iOS, 웹, 데스크톱, IoT 플랫폼 모두 지원[^5_6][^5_3]
- Qualcomm HTP, GPU, CPU 델리게이트를 통한 유연한 하드웨어 활용[^5_7]


### Windows ML의 온디바이스 AI 표준화

Windows ML은 Windows 11에 내장된 온디바이스 AI 추론 런타임으로, ONNX 모델을 기반으로 다양한 Execution Provider(EP)를 자동 감지·설치하여 수십~수백 MB 규모의 앱 용량 절감 효과를 제공합니다. DirectML EP를 통해 Intel, AMD, NVIDIA, Qualcomm의 NPU와 GPU를 지원하며, 인증·적합성 프로세스로 빌드 간 정확도 유지를 보장합니다.[^5_4]

### 모바일 LLM 성능 벤치마크

위키독스의 안드로이드 온디바이스 AI 실전 가이드는 Pixel 8 (Tensor G3) 기준 모바일 LLM 성능을 다음과 같이 측정했습니다:[^5_8]


| 모델 | 크기 (INT4) | 추론 속도 (GPU) | RAM 사용량 | 응답 품질 |
| :-- | :-- | :-- | :-- | :-- |
| Llama 3.2 1B INT4 | ~0.8GB | 25-35 tok/s | ~2.5GB | 보통 |
| Gemma 2 2B INT4 | ~1.5GB | 15-25 tok/s | ~3.5GB | 양호 |
| Phi-3-mini 3.8B INT4 | ~2.3GB | 10-18 tok/s | ~4.5GB | 우수 |
| Llama 3.2 3B INT4 | ~2.0GB | 12-20 tok/s | ~4.0GB | 양호 |
| Gemma 7B INT4 | ~3.8GB | 5-10 tok/s | ~7.5GB | 매우 우수 |

[^5_8]

### 제약조건 및 최적화 전략

모바일 LLM 배포 시 고려해야 할 핵심 제약조건은 다음과 같습니다:[^5_1][^5_8]

1. **메모리 제약**: 일반 앱은 시스템 RAM의 40~50%까지 사용 가능하며, 모델 가중치 + KV Cache + 런타임 오버헤드를 모두 고려해야 함
2. **속도 제약**: 사용자 경험을 위해 최소 10 tokens/sec 이상 권장 (NPU 추론: 20~60 tok/s, GPU: 10~30 tok/s)
3. **발열 제약**: 지속적인 LLM 추론은 심한 발열을 유발하며, 온도 상승 시 성능 스로틀링 발생
4. **저장공간 제약**: Play Store 150MB 제한으로 앱 설치 시 모델 번들 불가, 첫 실행 시 다운로드 또는 Play Asset Delivery 필요

[^5_8][^5_1]

### 프레임워크별 권장 사용 사례

| 프레임워크 | 최적 사용 사례 | 성능 특징 |
| :-- | :-- | :-- |
| LiteRT + Qualcomm Delegate | Android 프로덕션 앱 | NPU 네이티브 지원, GPU 대비 6배 속도 향상[^5_7] |
| Core ML | iOS/macOS 프로덕션 앱 | Apple Neural Engine 최적화, 낮은 전력 소비 |
| llama.cpp + NPU 백엔드 | Snapdragon 디바이스 고성능 필요 시 | GPU 대비 2.2배 빠른 디코딩, 40% 전력 절감[^5_9] |
| ONNX Runtime | 크로스 플랫폼 엔터프라이즈 | 범용 최적화, DirectML/TensorRT 지원 |
| MLC LLM | 고도 커스터마이징 필요 시 | 컴파일러 기반 최적화, 최대 유연성 |
| Windows ML | Windows 앱 | DirectML 자동 최적화, NPU/GPU 통합 지원[^5_4] |

[^5_5][^5_9][^5_4][^5_7]

## TensorRT-LLM 기반 FP8 추론 파이프라인 구현 절차

TensorRT-LLM은 NVIDIA GPU에서 LLM 추론을 최적화하기 위한 통합 프레임워크로, FP8 양자화를 통해 H100에서 FP16 대비 2.3배의 추론 속도 향상을 제공합니다. 다음은 FP8 추론 파이프라인의 단계별 구현 절차입니다.[^5_10][^5_11]

### Step 1: 사전 양자화된 모델 로드 (가장 간단한 방법)

NVIDIA Model Optimizer 컬렉션에서 사전 양자화된 FP8 모델을 직접 로드하는 방법이 가장 빠릅니다:[^5_12][^5_13]

```python
from tensorrt_llm import LLM

# FP8 양자화된 모델 직접 로드
llm = LLM(model='nvidia/Llama-3.1-8B-Instruct-FP8')
outputs = llm.generate("Hello, my name is")
```

TensorRT-LLM은 체크포인트에서 양자화 설정을 자동으로 감지하여 추가 설정 없이 실행 가능합니다.[^5_13][^5_12]

### Step 2: FP8 KV Cache 수동 활성화

체크포인트가 FP8 KV Cache를 기본적으로 활성화하지 않은 경우, 수동으로 설정할 수 있습니다:[^5_12][^5_13]

```python
from tensorrt_llm import LLM
from tensorrt_llm.llmapi import KvCacheConfig

llm = LLM(
    model='/path/to/model',
    kv_cache_config=KvCacheConfig(dtype='fp8')
)
outputs = llm.generate("Hello, my name is")
```

TensorRT-LLM 공식 문서에 따르면, FP8 KV Cache는 Hopper 및 Ada GPU에서 INT8보다 정확도 저하가 적어 권장되며, FP16에서 FP8 KV Cache로 전환 시 2배의 메모리 절감 효과가 있습니다.[^5_14]

### Step 3: NVIDIA Model Optimizer를 사용한 오프라인 양자화

HuggingFace에 사전 양자화된 모델이 없는 경우, NVIDIA Model Optimizer를 사용하여 직접 양자화할 수 있습니다:[^5_15][^5_13][^5_12]

```bash
# Model Optimizer 저장소 클론
git clone https://github.com/NVIDIA/TensorRT-Model-Optimizer.git
cd TensorRT-Model-Optimizer/examples/llm_ptq

# FP8 양자화 실행
scripts/huggingface_example.sh --model <huggingface_model_card> --quant fp8 --export_fmt hf
```


### Step 4: FP8 양자화 + NVFP4 KV Cache 결합

NVFP4 KV Cache를 함께 사용하면 메모리 효율성을 극대화할 수 있습니다:[^5_13]

```bash
scripts/huggingface_example.sh \
  --model <huggingface_model_card> \
  --quant fp8 \
  --kv_cache_quant nvfp4
```

현재 TensorRT-LLM은 NVFP4 KV Cache를 사용할 때 FP8 weight/activation 양자화가 필수적이므로 `--quant fp8`를 반드시 포함해야 합니다.[^5_13]

### Step 5: 양자화 방법 선택 가이드

TensorRT-LLM의 양자화 블로그는 배치 크기와 목표에 따른 최적 양자화 방법을 다음과 같이 제시합니다:[^5_11]

**배치 크기 < 16:**

- 가중치와 활성화를 모두 양자화하는 방법 선택 권장
- FP8 우선 시도 → 결과 불만족 시 INT8 SmoothQuant → AWQ/GPTQ 실험

**배치 크기 ≥ 16:**

- 모델별로 최적 방법이 다를 수 있음
- FP8 최우선 권장 (최고 성능과 정확도)
- 요구사항 미충족 시 INT8 SQ → AWQ/GPTQ 순서로 실험


### Step 6: 분산 추론을 위한 병렬화 설정

대규모 모델의 경우 TensorRT-LLM은 텐서 병렬화(TP), 파이프라인 병렬화(PP), 전문가 병렬화(EP)를 지원합니다:[^5_16]

```bash
# 4-way 텐서 병렬화
trtllm-build \
  --checkpoint_dir ./checkpoint \
  --output_dir ./engine \
  --tp_size 4
```


### Step 7: 성능 검증 및 벤치마크

Llama-v2-7B 모델에서 첫 토큰 지연시간을 500ms 이하로 제한할 때, FP8 양자화와 배치 크기 16은 H100에서 FP16 대비 **2.3배의 추론 속도 향상**을 달성합니다.[^5_11]

**TensorRT-LLM FP8의 핵심 장점:**

- H100에서 FP16 대비 2배의 연산 처리량과 2배의 메모리 절감[^5_17]
- 첫 토큰 지연시간 최소화 (GPT-J 6B에서 7.1ms 달성)[^5_18]
- 자동 양자화 설정 감지로 간편한 배포[^5_12]


## FP8 양자화 적용 시 모델 정확도 손실 완화 캘리브레이션 기법

FP8 양자화의 성공적인 적용을 위해서는 적절한 캘리브레이션 기법을 통해 정확도 손실을 최소화해야 합니다. arXiv 논문 2502.01070v1과 2502.01070v2의 연구 결과는 동적 스케일링, E4M3 포맷, 캘리브레이션 전략이 정확도에 미치는 영향을 상세히 분석합니다.[^5_19][^5_20]

### 동적 스케일링 vs 정적 스케일링

**동적 스케일링(Dynamic Scaling)**은 각 입력에 대해 런타임에 스케일링 팩터를 계산하는 반면, **정적 스케일링(Static Scaling)**은 캘리브레이션 데이터셋을 사용하여 사전에 스케일링 팩터를 계산합니다. arXiv 논문의 실험 결과는 동적 스케일링이 정적 스케일링보다 현저히 우수함을 보여줍니다.[^5_20][^5_19]

**Llama v3.1 8B Instruct 정확도 비교:**


| 벤치마크 | BF16 | FP8 정적 | FP8 동적 | 정확도 차이 |
| :-- | :-- | :-- | :-- | :-- |
| MMLU CoT 5-shot | 68.8% | 66.3% | 68.3% | 동적이 2.0%p 우수 |
| GSM8K CoT 5-shot | 83.1% | 70.4% | 84.5% | 동적이 14.1%p 우수 |
| Winogrande | 73.8% | 77.6% | 73.8% | 동일 |

[^5_19][^5_20]

논문은 "동적 양자화는 원본 BF16 모델과 유사한 결과를 얻는 반면, 정적 양자화는 눈에 띄는 정확도 저하를 초래한다"고 결론짓습니다. 정적 스케일링의 문제는 캘리브레이션 중에 얻은 스케일링 팩터가 보이지 않는 입력에 대해 최적이 아닐 수 있다는 점입니다.[^5_20][^5_19]

### E4M3 vs E5M2 포맷 선택

FP8은 지수와 가수에 할당된 비트 수에 따라 E4M3와 E5M2로 구분됩니다. **E4M3**는 4비트 지수와 3비트 가수로 더 높은 정밀도를 제공하며, **E5M2**는 5비트 지수와 2비트 가수로 더 넓은 동적 범위를 제공합니다.[^5_20]

**E4M3 vs E5M2 정확도 비교 (MMLU CoT 5-shot):**


| 모델 | BF16 | E4M3 | E5M2 | 정확도 차이 |
| :-- | :-- | :-- | :-- | :-- |
| Llama v3.2 1B Instruct | 46.3% | 45.5% | 44.5% | E4M3가 1.0%p 우수 |
| Llama v3.2 3B Instruct | 61.8% | 61.6% | 60.7% | E4M3가 0.9%p 우수 |
| Llama v3.1 8B Instruct | 68.8% | 68.3% | 67.5% | E4M3가 0.8%p 우수 |
| Llama v3.3 70B Instruct | 82.0% | 82.0% | 82.2% | E5M2가 0.2%p 우수 |

[^5_20]

arXiv 논문은 "E4M3는 언어 작업에서 E5M2보다 일관되게 우수한 정확도를 달성한다"고 보고하며, 대부분의 경우 E4M3 사용을 권장합니다.[^5_20]

### 캘리브레이션 전략

위키독스의 Quantization 딥다이브는 다양한 캘리브레이션 전략을 다음과 같이 정리합니다:[^5_21]

**주요 캘리브레이션 방법:**


| 방법 | 특징 | 장점 | 단점 |
| :-- | :-- | :-- | :-- |
| **AbsMax** | 최대 절댓값 기반 | 간단하고 빠름 | 이상치에 취약 |
| **Percentile** | 99.99% 백분위수 사용 | 이상치 제거 효과 | 일부 정보 손실 가능 |
| **MSE 최소화** | 양자화 오차 직접 최소화 | 정확도 높음 | 계산 비용 높음 |
| **KL-Divergence** | 원본/양자화 분포 간 정보 손실 최소화 | 정보 이론적 최적화 | TensorRT에서 사용, 복잡함 |

**캘리브레이션 데이터 권장사항:**

- 샘플 수: 100~500개
- 데이터 분포: 실제 사용 환경을 대표
- 다양성: 다양한 입력 패턴 포함

[^5_21]

### Stochastic Rounding의 효과

Stochastic rounding은 양자화 중 더 많은 원본 수치 정보를 보존할 것으로 기대되지만, arXiv 논문의 실험 결과는 다릅니다. "Stochastic rounding은 양자화 중 모델 정확도를 크게 향상시키지 않으며, 특정 경우에는 정확도 저하를 초래할 수도 있다"는 결과를 보고합니다. 따라서 FP8 추론에서 stochastic rounding의 실질적 이점은 불확실합니다.[^5_19]

### 정확도 손실 최소화 모범 사례

1. **동적 스케일링 우선 사용**: 캘리브레이션 데이터가 필요 없고 BF16 모델과 유사한 정확도 달성[^5_19][^5_20]
2. **E4M3 포맷 선택**: 언어 작업에서 E5M2보다 일관되게 우수한 성능[^5_20]
3. **KL-Divergence 캘리브레이션**: 정적 스케일링 필요 시 TensorRT의 KL-Divergence 방법 사용[^5_21]
4. **First/Last Layer 제외**: lm-head와 embedding 레이어는 정확도에 큰 영향을 미치므로 양자화에서 제외 고려[^5_22]
5. **모델 크기 고려**: 대형 모델(70B+)은 양자화에 더 강인하며 정확도 손실이 적음[^5_22]

## Intel Gaudi 3에서의 FP8 학습 및 추론 가속 성능 분석

Intel Gaudi 3는 2세대 대비 FP8 성능을 2배 향상시키고 TDP를 900W(공랭) 또는 1200W(수랭)까지 높여 LLM 학습과 추론에 최적화된 AI 가속기입니다. arXiv 논문 2503.09975v3 "Faster Inference of LLMs using FP8 on the Intel Gaudi"는 Gaudi 2와 3의 FP8 구현을 상세히 분석합니다.[^5_23][^5_24][^5_25][^5_26][^5_22]

### Gaudi 3 하드웨어 사양

**Intel Gaudi 3 AI Accelerator OAM:**


| 사양 | Gaudi 2 | Gaudi 3 | 세대간 향상 |
| :-- | :-- | :-- | :-- |
| TDP (OAM) | 600W | 900W (공랭) / 1200W (수랭) | 1.5~2배 |
| BF16 Matrix TFLOPS | 432 | 1835 | 4.25배 |
| FP8 Matrix TFLOPS | - | 1835 | 신규 지원 |
| BF16 Vector TFLOPS | - | 28.7 | - |
| HBM 용량 | 96GB | 128GB | 1.33배 |
| HBM 대역폭 | 2.46 TB/s | 3.67 TB/s | 1.49배 |
| 온-다이 SRAM (L2 Cache) | - | 96MB / 12.8 TB/s | - |
| 네트워킹 | 4.8 Tb/s 양방향 | 9.6 Tb/s 양방향 | 2배 |
| MME 유닛 | - | 8 (각 256×256 MAC) | - |
| TPC 유닛 | - | 64 | - |

[^5_25][^5_26]

### Gaudi 3의 FP8 혁신 기능

**Gaudi 3의 FP8 향상:**

1. **확장된 E4M3 범위**: Gaudi 2는 IEEE 표준을 따라 E4M3의 최대값이 ±240이었지만, Gaudi 3는 최대 지수를 일반 숫자에 사용 가능하게 하여 ±448로 확장[^5_22]
2. **하드웨어 가속 스케일링 팩터 확대**: Gaudi 2는 [2^{-8}, 2^{-4}, 2^{0}, 2^{4}]의 제한된 스케일링 팩터만 지원했지만, Gaudi 3는 [2^{-32}, ..., 2^{0}, ..., 2^{31}] 범위의 모든 2의 거듭제곱을 지원[^5_22]
3. **Power-of-Two 스케일링 최적화**: 양쪽 입력 텐서가 per-tensor 스케일링과 2의 거듭제곱 팩터를 사용할 때, 지수 바이어스 조정만으로 스케일링을 효율적으로 구현하여 수% 포인트의 처리량 향상 달성[^5_22]

### FP8 GEMM 처리량 벤치마크

Gaudi 2의 FP8 행렬 곱셈 처리량 측정 결과는 다음과 같습니다:[^5_22]

**Scaled FP8 Matrix Multiplication 처리량 (Gaudi 2):**


| M×K×N | Per-Tensor | HW 가속 | Mean TFLOPS | MFU (%) |
| :-- | :-- | :-- | :-- | :-- |
| 4096×4096×4096 | True | True | 803.8 | 92.9% |
| 4096×4096×4096 | True | False | 771.4 | 89.2% |
| 4096×4096×4096 | False | False | 746.5 | 86.3% |
| 6144×6144×6144 | True | True | 849.1 | 98.2% |
| 8192×8192×8192 | True | True | 851.2 | 98.4% |

arXiv 논문은 "Gaudi 2 가속기는 일관되게 높은 연산 유닛 활용도를 달성하며, 종종 90% MFU를 초과한다"고 보고합니다. 피크 scaled FP8 dense GEMM 처리량은 865 TFLOPS에 달합니다.[^5_22]

### 모델 정확도 평가

arXiv 논문은 Llama2, Llama3, Mistral 패밀리 모델에서 다양한 FP8 양자화 방법을 평가했습니다:[^5_22]

**Llama2-70B FP8 정확도:**


| Configuration | WikiText2 PPL (변화%) | Common Sense (변화%) | MMLU (변화%) |
| :-- | :-- | :-- | :-- |
| BF16 Reference | 7.131 | 74.652% | 67.648% |
| Per Tensor Scaling | 7.279 (+2.08%) | 74.336% (-0.42%) | 67.504% (-0.21%) |
| Per Channel Scaling | 7.279 (+2.07%) | 74.297% (-0.48%) | 67.293% (-0.53%) |

**Llama3-70B FP8 정확도:**


| Configuration | WikiText2 PPL (변화%) | Common Sense (변화%) | MMLU (변화%) |
| :-- | :-- | :-- | :-- |
| BF16 Reference | 5.004 | 75.751% | 78.105% |
| Per Tensor Scaling | 5.176 (+3.43%) | 75.582% (-0.22%) | 78.252% (+0.19%) |
| Per Channel Scaling | 5.180 (+3.52%) | 75.456% (-0.39%) | 77.820% (-0.37%) |

[^5_22]

논문의 핵심 발견은 다음과 같습니다:[^5_22]

- **모델 스케일 효과**: 대형 모델(70B)이 양자화에 더 강인하며 1% 미만의 정확도 저하 달성
- **작업 의존성**: MMLU 같은 지식 검색 작업이 양자화에 더 민감하며, 상식 추론 작업은 1% 미만의 저하로 강인함
- **양자화 방법 비교**: Per-tensor와 per-channel 스케일링이 unit scale보다 정확도 보존에 우수하며, per-channel이 소형 모델에서 약간 유리


### 추론 처리량 성능

**Llama v3.1 70B 추론 처리량 (Gaudi 2 단일 카드):**

**Prefill 단계:**


| 입력 길이 | Mean TFLOPS | MFU (%) |
| :-- | :-- | :-- |
| 1024 | 649.1 | 75.4% |
| 2048 | 671.0 | 77.6% |
| 4096 | 602.8 | 69.7% |
| 8192 | 513.7 | 59.4% |
| 16384 | 390.1 | 45.1% |

**Decode 단계 (TFLOPS):**


| 배치 크기 | 512 길이 | 1024 길이 | 2048 길이 | 4096 길이 |
| :-- | :-- | :-- | :-- | :-- |
| 8 | 32.8 | 32.4 | 30.8 | 30.2 |
| 16 | 63.2 | 61.5 | 55.8 | 51.4 |
| 32 | 120.1 | 112.0 | 94.1 | 79.5 |
| 64 | 224.1 | 198.8 | 152.3 | - |
| 128 | 387.1 | 312.8 | - | - |

[^5_22]

### Gaudi 3 GenAI 추론 벤치마크

Hot Chips 2024에서 발표된 Gaudi 3 FP8 추론 성능은 다음과 같습니다:[^5_26]

**LLM 추론 처리량 (tokens/sec):**


| 모델 | TP | 입력/출력 | Gaudi 2 | Gaudi 3 | 세대간 향상 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| LLAMA2-7B | 1 | 128/2048 | 4,789 | 6,574 | 1.37배 |
| LLAMA3-8B | 1 | 128/2048 | 11,098 | 18,769 | 1.69배 |
| LLAMA3-8B | 1 | 2048/2048 | 5,380 | 6,922 | 1.29배 |
| LLAMA2-70B | 1 | 128/2048 | 1,126 | 3,218 | 2.86배 |
| LLAMA2-70B | 2 | 128/2048 | 3,212 | 6,225 | 1.94배 |

[^5_26]

TechInsights의 분석에 따르면, Gaudi 3는 최대 구성에서 전세대 대비 FP8 성능을 2배 향상시켰으며, MLPerf 예상 벤치마크는 Gaudi 3 OAM 클러스터가 대규모 LLM 사전학습에서 H100보다 25~40% 빠른 학습 시간을 달성한다고 보고합니다.[^5_23]

Intel Gaudi 3는 카드, 노드, 랙, 클러스터 등 모든 규모에서 AI 가속을 제공하도록 설계되었으며, Backend.AI와의 통합을 통해 Llama-3.1-8B-Instruct와 70B-Instruct 모델에서 뛰어난 성능을 입증했습니다.[^5_27][^5_26]
<span style="display:none">[^5_28][^5_29][^5_30][^5_31][^5_32][^5_33][^5_34][^5_35][^5_36][^5_37][^5_38][^5_39][^5_40]</span>

<div align="center">⁂</div>

[^5_1]: https://dalbbom.tistory.com/6

[^5_2]: https://blog.mondrian.ai/on-device-llm-ai-strategies

[^5_3]: https://ai.google.dev/edge/litert/overview?hl=ko

[^5_4]: https://news.hada.io/topic?id=23314

[^5_5]: https://www.linkedin.com/posts/shelbyheinecke_skip-the-cloud-these-9-frameworks-run-llms-activity-7359265484057296896-e86n

[^5_6]: https://github.com/google-ai-edge/litert

[^5_7]: https://ai.google.dev/edge/litert/android/npu/qualcomm?hl=ko

[^5_8]: https://wikidocs.net/336153

[^5_9]: https://wikidocs.net/251902

[^5_10]: https://news.hada.io/topic?id=10852

[^5_11]: https://github.com/NVIDIA/TensorRT-LLM/blob/main/docs/source/blogs/quantization-in-TRT-LLM.md

[^5_12]: https://nvidia.github.io/TensorRT-LLM/1.2.0rc5/features/quantization.html

[^5_13]: https://mintlify.wiki/NVIDIA/TensorRT-LLM/features/quantization

[^5_14]: https://kr.linkedin.com/pulse/great-llm-inference-showdown-tensorrt-llm-vs-vllm-vinay-jayanna-9o9pc?tl=ko

[^5_15]: https://github.com/NVIDIA/TensorRT-Model-Optimizer/blob/main/examples/llm_ptq/README.md

[^5_16]: https://introl.com/ko/blog/tensorrt-llm-optimization-nvidia-inference-stack-guide

[^5_17]: https://lambda.ai/blog/nvidia-hopper-h100-and-fp8-support

[^5_18]: https://nvidia.github.io/TensorRT-LLM/blogs/H100vsA100.html

[^5_19]: https://arxiv.org/html/2502.01070v2

[^5_20]: https://www.dbpia.co.kr/Journal/articleDetail?nodeId=NODE12047123

[^5_21]: https://wikidocs.net/338761

[^5_22]: https://www.manuscriptlink.com/society/kips/conference/ack2025/file/downloadSoConfManuscript/abs/KIPS_C2025B0013F

[^5_23]: https://www.techinsights.com/blog/gaudi-3-competes-inference-efficiency

[^5_24]: https://arxiv.org/html/2503.09975v3

[^5_25]: https://cdn.day1company.io/prod/uploads/202501/122009-1154/-패스트캠퍼스--교육과정소개서-llm-모델-파인튜닝을-위한-quantization.pdf

[^5_26]: https://www.linkedin.com/posts/donghyeon-han-90b439170_llm%EC%9D%84-%EC%9C%84%ED%95%9C-%EC%9D%B8%EC%8A%A4%ED%8A%B8%EB%9F%AD%EC%85%98%ED%94%84%EB%A1%AC%ED%94%84%ED%8A%B8-%ED%8C%8C%EC%9D%B8%ED%8A%9C%EB%8B%9D-%EC%B5%9C%EC%8B%A0-%EC%97%B0%EA%B5%AC-%EB%8F%99%ED%96%A5-%EB%B0%8F-%EC%8B%9C%EC%82%AC%EC%A0%90-%EB%B6%84%EC%84%9D-activity-7095058579342151681-1GhA

[^5_27]: https://www.backend.ai/ko/resources/backend-ai-intel-gaudi3-whitepaper

[^5_28]: https://alphaxiv.org/ko/overview/2602.12669v1

[^5_29]: https://www.gnict.org/게시판/ai연구회/llm을-소비자-하드웨어에서-학습-위한-검토-fp4와-양자화/

[^5_30]: https://x.com/No_Extra_Time/status/1916650156889640993

[^5_31]: https://www.samsungsds.com/kr/insights/cloud-aios.html

[^5_32]: https://www.reddit.com/r/LocalLLaMA/comments/1o3r6et/quality_degradation_of_fp8_quantization/

[^5_33]: https://github.com/NVIDIA/TensorRT-LLM/blob/main/examples/quantization/README.md

[^5_34]: https://nvidia.github.io/TensorRT-LLM/performance/performance-tuning-guide/fp8-quantization.html

[^5_35]: https://nvidia.github.io/TensorRT-LLM/torch/features/quantization.html

[^5_36]: https://hc2024.hotchips.org/assets/program/conference/day1/60_HC2024.Intel.RomanKaplan.Gaudi3-0826.pdf

[^5_37]: https://proceedings.mlsys.org/paper_files/paper/2024/file/dea9b4b6f55ae611c54065d6fc750755-Paper-Conference.pdf

[^5_38]: https://nvidia.github.io/TensorRT-LLM/reference/precision.html

[^5_39]: https://www.intel.com/content/www/us/en/developer/platform/gaudi/model-performance.html

[^5_40]: https://arxiv.org/pdf/2312.05725.pdf


---

## 온디바이스 LLM 배포를 위한 프레임워크 선택 가이드라인

온디바이스 LLM 배포 시 프레임워크 선택은 플랫폼, 하드웨어, 모델 크기, 개발 난이도, 성능 요구사항을 종합적으로 고려해야 합니다. 2026년 현재 안드로이드, iOS, 크로스 플랫폼 환경에서 각기 다른 프레임워크가 최적화되어 있습니다.[^6_1][^6_2][^6_3][^6_4]

### 플랫폼별 프레임워크 선택 기준

#### Android 플랫폼

안드로이드는 Google의 온디바이스 AI 전략에 따라 세 가지 계층의 프레임워크를 제공합니다:[^6_2][^6_4]

**1. 고수준 추상화 (빠른 개발, 제한적 커스터마이징):**

- **ML Kit**: Firebase에 포함된 가장 쉬운 온디바이스 AI API로, 텍스트 인식, 얼굴 탐지, 바코드 스캔, 포즈 탐지 등 사전 구축된 기능 제공[^6_4]
- **MediaPipe Tasks API**: 비전, 텍스트, 오디오 AI를 파이프라인으로 구성하며, 손 랜드마크, 객체 탐지, 이미지 세그멘테이션 등 복잡한 멀티미디어 AI 처리에 최적[^6_4]
- **Google AI Edge SDK**: Gemma, Phi 등 소형 LLM을 앱에 통합하며, Gemini Nano가 사전 다운로드된 기기에서 GenerativeModel API로 접근[^6_2][^6_4]

**2. 중간 수준 (모델 커스터마이징, 하드웨어 최적화):**

- **LiteRT (구 TensorFlow Lite)**: 2024년 브랜드 재편으로 `com.google.ai.edge.litert` 패키지로 전환되었으며, `.tflite` 형식의 커스텀 모델을 NPU, GPU, CPU 델리게이트로 실행[^6_2][^6_4]
- **NNAPI Delegate**: TFLite에서 `addDelegate(NnApiDelegate())`로 활성화하여 Qualcomm, Samsung, MediaTek NPU 등 하드웨어 가속기를 통일된 인터페이스로 접근[^6_4]

**3. 저수준 런타임 (최대 성능, 복잡한 구현):**

- **Qualcomm AI Hub**: Snapdragon Hexagon NPU에 사전 최적화된 모델을 제공하며, QNN (Qualcomm AI Engine Direct)을 통해 최대 45~85 TOPS 성능 달성[^6_5][^6_6]

**안드로이드 프레임워크 선택 결정 트리:**


| 상황 | 권장 선택 |
| :-- | :-- |
| 빠른 프로토타입, Firebase 이미  사용 중 | ML Kit |
| 얼굴/손/포즈 등 비전 AI, 표준 모델로 충분 | MediaPipe Tasks API |
| 나만의 학습 모델(.tflite)을 앱에 통합 | TensorFlow Lite / LiteRT |
| Gemma, Phi 등 소형 LLM을 앱에 통합 | Google AI Edge SDK |
| TFLite를 쓰되 하드웨어 가속이 필요 | TFLite + NNAPI Delegate |
| Snapdragon 디바이스에서 최대 성능 필요 | Qualcomm AI Hub + LiteRT |

[^6_2][^6_4]

#### iOS/macOS 플랫폼

Apple 생태계는 Foundation Models 프레임워크를 통해 Apple Intelligence를 구동하는 온디바이스 LLM에 접근합니다:[^6_7][^6_1]

**Foundation Models 프레임워크 (iOS 18.2+, macOS 15.2+):**

- **SystemLanguageModel**: 온디바이스 LLM에 대한 시스템 수준 접근 제공[^6_1]
- **LanguageModelSession**: 타입화된 온디바이스 LLM 호출을 네트워크 액세스 없이 수행[^6_1]
- **Tool 프로토콜**: 동적 UI 업데이트를 위한 스트리밍 응답, 데이터 검색 또는 작업 수행을 위한 도구 호출[^6_7]

**Core ML:**

- Apple Neural Engine 최적화로 낮은 전력 소비와 높은 추론 속도 제공[^6_8]
- `.mlmodel` 또는 `.mlpackage` 형식 지원[^6_8]
- Xcode에서 모델 컴파일 및 배포 자동화[^6_3]

**iOS/macOS 선택 기준:**


| 요구사항 | 권장 선택 |
| :-- | :-- |
| Apple Intelligence 기반 텍스트 생성 | Foundation Models 프레임워크 |
| 커스텀 ML 모델 배포 | Core ML |
| 크로스 플랫폼 필요 | ONNX Runtime + Core ML EP |

[^6_3][^6_7][^6_1]

### 크로스 플랫폼 프레임워크

#### ONNX Runtime

Microsoft의 ONNX Runtime은 Android, iOS, Windows, Linux에서 통일된 API를 제공하며, 다양한 Execution Provider(EP)를 통해 하드웨어 최적화를 지원합니다:[^6_9][^6_8]

**지원 Execution Providers:**

- **DirectML EP**: Windows 11에서 Intel, AMD, NVIDIA, Qualcomm NPU 및 GPU 자동 감지[^6_9]
- **TensorRT EP**: NVIDIA GPU 최적화[^6_8]
- **Core ML EP**: Apple Silicon 및 Neural Engine[^6_8]
- **NNAPI EP**: Android NPU/GPU[^6_8]

**ONNX Runtime 장점:**

- 엔터프라이즈급 안정성과 포괄적 하드웨어 지원[^6_8]
- `.onnx` 형식으로 PyTorch, TensorFlow 모델 변환 용이[^6_10]
- Windows ML과의 통합으로 수십~수백 MB 앱 용량 절감[^6_9]


#### llama.cpp

llama.cpp는 C++ 엔진 기반으로 CPU, Metal (Apple), CUDA (NVIDIA), OpenCL, NPU 백엔드를 지원하는 경량 LLM 추론 프레임워크입니다:[^6_11][^6_8]

**llama.cpp 강점:**

- GGUF 포맷으로 양자화 모델 지원 (2~8비트)[^6_12][^6_13]
- Snapdragon 8 Elite NPU에서 GPU 대비 2.2배 빠른 디코딩, 40% 전력 절감[^6_11]
- 로컬 서버 모드로 RESTful API 제공 가능[^6_8]


#### MLC LLM

MLC LLM은 컴파일러 기반 접근법으로 iOS, Android, 웹에서 고도의 커스터마이징을 제공합니다:[^6_8]

**MLC LLM 특징:**

- Apache TVM 컴파일러 스택 활용으로 최대 유연성[^6_8]
- 하드웨어별 최적화 코드 자동 생성[^6_8]
- 구현 난이도가 높지만 최고 성능 달성 가능[^6_8]


### 모델 크기별 프레임워크 권장사항

모바일 디바이스의 메모리와 성능 제약을 고려하여 모델 크기별로 적합한 프레임워크를 선택해야 합니다:[^6_14][^6_15]


| 모델 크기 | Android | iOS/macOS | 크로스 플랫폼 |
| :-- | :-- | :-- | :-- |
| **소형 (<1B)** | MediaPipe Tasks API, ML Kit | Core ML | ONNX Runtime |
| **중형 (1~3B)** | LiteRT + NNAPI, Google AI Edge SDK | Foundation Models, Core ML | llama.cpp, ONNX Runtime |
| **대형 (3~7B)** | LiteRT + Qualcomm Delegate | Foundation Models (A17 Pro+) | llama.cpp + NPU 백엔드 |
| **초대형 (7B+)** | 제한적 (INT4 양자화 필수) | 제한적 (M 시리즈 Mac) | MLC LLM (컴파일 최적화) |

[^6_14][^6_8]

### 하드웨어 최적화 전략

#### NPU 활용 우선순위

NPU는 CPU 및 GPU 대비 지연시간이 짧고 전력 소비가 적어 온디바이스 LLM의 핵심 가속기입니다:[^6_5][^6_11]

**NPU 성능 벤치마크 (MobileNetv2, Samsung S25):**

- NPU (HTP용 QNN): **0.3ms**
- GPU (GPUv2): 1.8ms (NPU 대비 6배 느림)
- CPU (XNNPACK): 2.8ms (NPU 대비 9배 느림)

[^6_5]

**NPU 최적화 프레임워크 선택:**


| 하드웨어 | 최적 프레임워크 | 추론 속도 향상 |
| :-- | :-- | :-- |
| Qualcomm Hexagon NPU | LiteRT + Qualcomm Delegate | GPU 대비 6배 [^6_5] |
| Apple Neural Engine | Core ML, Foundation Models | 높은 에너지 효율 |
| Intel/AMD NPU | ONNX Runtime + DirectML | Windows 통합 최적화 [^6_9] |
| MediaTek NPU | LiteRT + NNAPI | 안드로이드 표준 지원 |

[^6_5][^6_9][^6_8]

#### 메모리 제약 대응

모바일 LLM 배포 시 메모리 관리는 성공의 핵심입니다:[^6_15][^6_14]

**메모리 사용량 공식:**

```
총 메모리 = 모델 가중치 + KV Cache + 런타임 오버헤드
```

**Pixel 8 (Tensor G3) 기준 메모리 사용량:**


| 모델 | 크기 (INT4) | RAM 사용량 | 추론 속도 (GPU) |
| :-- | :-- | :-- | :-- |
| Llama 3.2 1B INT4 | ~0.8GB | ~2.5GB | 25-35 tok/s |
| Gemma 2 2B INT4 | ~1.5GB | ~3.5GB | 15-25 tok/s |
| Phi-3-mini 3.8B INT4 | ~2.3GB | ~4.5GB | 10-18 tok/s |
| Gemma 7B INT4 | ~3.8GB | ~7.5GB | 5-10 tok/s |

[^6_14]

**메모리 최적화 전략:**

1. **INT4 양자화 필수**: 7B 모델도 ~4GB 이하로 압축[^6_14]
2. **KV Cache 크기 제한**: 최대 컨텍스트 길이를 512~1024 토큰으로 제한[^6_14]
3. **Play Asset Delivery 활용**: 150MB Play Store 제한 우회를 위해 첫 실행 시 모델 다운로드[^6_14]

### 배포 전략 결정 트리

```
시작
├─ 플랫폼?
│  ├─ Android
│  │  ├─ 빠른 프로토타입? → ML Kit
│  │  ├─ 비전 AI? → MediaPipe Tasks API
│  │  ├─ 소형 LLM (Gemma)? → Google AI Edge SDK
│  │  ├─ 커스텀 모델 + NPU? → LiteRT + NNAPI/Qualcomm Delegate
│  │  └─ 최대 성능 (Snapdragon)? → Qualcomm AI Hub
│  │
│  ├─ iOS/macOS
│  │  ├─ Apple Intelligence 기반? → Foundation Models
│  │  ├─ 커스텀 ML 모델? → Core ML
│  │  └─ 크로스 플랫폼 필요? → ONNX Runtime
│  │
│  └─ 크로스 플랫폼
│     ├─ 엔터프라이즈급 안정성? → ONNX Runtime
│     ├─ CPU/모바일 최적화? → llama.cpp
│     ├─ 최대 커스터마이징? → MLC LLM
│     └─ 간단한 로컬 배포? → Ollama
│
├─ 모델 크기?
│  ├─ <1B: 모든 프레임워크 가능
│  ├─ 1~3B: NPU 최적화 프레임워크 권장
│  ├─ 3~7B: INT4 양자화 + NPU 필수
│  └─ 7B+: 제한적, 고성능 디바이스만 가능
│
└─ 개발 리소스?
   ├─ 제한적 → 고수준 API (ML Kit, MediaPipe, Foundation Models)
   ├─ 중간 → 중간 수준 (LiteRT, Core ML, ONNX Runtime)
   └─ 충분 → 저수준 (llama.cpp, MLC LLM, Qualcomm AI Hub)
```


### 성능 vs 개발 난이도 매트릭스

| 프레임워크 | 성능 | 개발 난이도 | 하드웨어 최적화 | 크로스 플랫폼 |
| :-- | :-- | :-- | :-- | :-- |
| ML Kit | 중 | 매우 쉬움 | 자동 | Android/iOS |
| MediaPipe Tasks API | 중~높음 | 쉬움 | 자동 | Android/iOS/웹 |
| Foundation Models | 높음 | 쉬움 | 자동 (Apple) | iOS/macOS만 |
| LiteRT + NNAPI | 높음 | 보통 | 수동 설정 | Android 중심 |
| Core ML | 높음 | 보통 | 자동 (Apple) | iOS/macOS만 |
| ONNX Runtime | 중~높음 | 보통 | EP 선택 | 우수 |
| llama.cpp | 높음 | 보통~어려움 | 백엔드 선택 | 우수 |
| MLC LLM | 매우 높음 | 어려움 | 컴파일 최적화 | 우수 |
| Qualcomm AI Hub | 매우 높음 | 어려움 | 최고 (Snapdragon) | Android만 |

[^6_4][^6_2][^6_8]

### 2026년 트렌드 및 권장사항

**주요 트렌드:**

1. **LiteRT의 TFLite 완전 대체**: 신규 프로젝트에서는 `litert` 패키지 사용 권장[^6_4]
2. **멀티모달 온디바이스 AI**: 텍스트, 이미지, 오디오를 동시 처리하는 소형 모델 지원 확대[^6_4]
3. **Android AICore 확대**: Gemini Nano 지원이 Pixel 외 제조사 기기로 확산[^6_4]
4. **Kotlin 우선 API**: 자바 기반 TFLite API에서 Kotlin 친화적 API로 전환[^6_4]
5. **NPU 표준화**: DirectML, NNAPI, QNN 등 NPU 추상화 계층의 성숙[^6_9]

**프로덕션 환경 권장사항:**


| 사용 사례 | 1순위 | 2순위 | 3순위 |
| :-- | :-- | :-- | :-- |
| Android 상용 앱 | LiteRT + NNAPI | Google AI Edge SDK | MediaPipe |
| iOS 상용 앱 | Foundation Models | Core ML | ONNX Runtime |
| 크로스 플랫폼 앱 | ONNX Runtime | llama.cpp | MLC LLM |
| 고성능 Snapdragon | Qualcomm AI Hub | LiteRT + Qualcomm | llama.cpp + NPU |
| Windows 앱 | ONNX Runtime + DirectML | - | - |
| 빠른 PoC | ML Kit (Android) | Foundation Models (iOS) | MediaPipe |

[^6_2][^6_9][^6_4][^6_8]

온디바이스 LLM 배포의 성공은 적절한 프레임워크 선택뿐만 아니라 양자화, 메모리 관리, 하드웨어 최적화를 종합적으로 고려한 전략 수립에 달려 있습니다. 2026년 현재는 특히 NPU 활용과 소형 LLM (1~3B) 배포가 온디바이스 AI의 스위트 스팟으로 자리잡고 있습니다.[^6_16][^6_17][^6_6][^6_5]
<span style="display:none">[^6_18][^6_19]</span>

<div align="center">⁂</div>

[^6_1]: https://blakecrosley.com/ko/blog/foundation-models-on-device-llm

[^6_2]: https://wikidocs.net/336082

[^6_3]: https://developer.apple.com/kr/videos/play/wwdc2025/360/

[^6_4]: https://uracle.blog/2025/04/25/llm-파인튜닝-효과적인-활용과-대안-전략/

[^6_5]: https://ai.google.dev/edge/litert/android/npu/qualcomm?hl=ko

[^6_6]: https://localaimaster.com/blog/npu-comparison-2026

[^6_7]: https://developer.apple.com/kr/hello/october25/

[^6_8]: https://www.linkedin.com/posts/shelbyheinecke_skip-the-cloud-these-9-frameworks-run-llms-activity-7359265484057296896-e86n

[^6_9]: https://news.hada.io/topic?id=23314

[^6_10]: https://developer.android.com/ai/overview?hl=ko

[^6_11]: https://wikidocs.net/251902

[^6_12]: https://www.reddit.com/r/LocalLLaMA/comments/1ayd4xr/for_those_who_dont_know_what_different_model/

[^6_13]: https://oobabooga.github.io/blog/posts/gptq-awq-exl2-llamacpp/

[^6_14]: https://wikidocs.net/336153

[^6_15]: https://dalbbom.tistory.com/6

[^6_16]: https://www.kibme.org/resources/journal/20250508095309624.pdf

[^6_17]: https://blog.mondrian.ai/on-device-llm-ai-strategies

[^6_18]: https://developer.apple.com/kr/videos/play/meet-with-apple/205/

[^6_19]: https://discuss.pytorch.kr/t/llm-a-to-z/6622


---

## 모바일 환경에서의 SLM(Small Language Model) 벤치마크 평가 방법

SLM(Small Language Model)은 파라미터 수가 7B 미만인 경량 언어모델로, 모바일 및 엣지 디바이스에서 효율적으로 작동하도록 설계되었습니다. arXiv 논문 2508.15478v1 "SLM-Bench: A Comprehensive Benchmark of Small Language Models"는 SLM의 정확도, 연산 효율성, 환경적 영향을 종합적으로 평가하는 최초의 벤치마크를 제시합니다.[^7_1][^7_2][^7_3][^7_4]

### SLM-Bench의 핵심 설계 원칙

SLM-Bench는 15개의 SLM을 9가지 NLP 태스크와 14개 도메인에 걸친 23개 데이터셋에서 평가하며, 4가지 하드웨어 구성(NVIDIA L4, A10 GPU 및 NVIDIA Jetson Orin AGX 16GB/64GB)에서 실험을 수행합니다. 기존 벤치마크가 주로 LLM에 집중한 반면, SLM-Bench는 자원 제약 환경에서의 배포 가능성을 중심으로 SLM을 평가합니다.[^7_4][^7_1]

**SLM-Bench의 3가지 특징:**

1. **SLM 집중**: 연산 효율성과 접근성이 높은 7B 미만 모델에 집중[^7_4]
2. **환경 영향 측정**: 에너지 소비와 CO₂ 배출량을 통합 평가하여 지속가능성 평가[^7_4]
3. **다양한 설정 평가**: 9개 태스크, 23개 데이터셋, 14개 도메인, 4개 하드웨어에서 포괄적 분석[^7_4]

### 11가지 평가 메트릭

SLM-Bench는 정확성, 연산, 소비의 세 가지 범주로 나뉜 11가지 메트릭을 사용합니다:[^7_1][^7_4]


| 범주 | 메트릭 | 설명 | 적용 태스크 |
| :-- | :-- | :-- | :-- |
| **정확성 (Correctness)** | Accuracy | 예측 정확도 측정 | QA, 분류, 인식, 추론, 독해 |
|  | F1 Score | 정밀도와 재현율의 조화 평균 | QA, 분류, 인식, 추론, 독해 |
|  | BLEU | 생성 텍스트와 참조 텍스트 간 n-gram 일치도 | 텍스트 생성, 주제 추출 |
|  | ROUGE | 요약 품질 평가 (n-gram 겹침) | 텍스트 생성, 주제 추출 |
|  | METEOR | 동의어 및 의역 고려한 품질 평가 | 텍스트 생성, 주제 추출 |
|  | Perplexity | 언어 모델의 예측 불확실성 | 텍스트 생성, 주제 추출 |
| **연산 (Computation)** | Runtime | 모델 실행 시간 | 모든 태스크 |
|  | FLOPs | 부동소수점 연산 횟수 | 모든 태스크 |
| **소비 (Consumption)** | Cost (USD) | lightning.ai 서버 임대 비용 | 모든 태스크 |
|  | CO₂ Emissions (kg) | ML CO2 패키지로 추정한 탄소 배출량 | 모든 태스크 |
|  | Energy (kWh) | Zeus 패키지로 측정한 에너지 소비 | 모든 태스크 |

[^7_1][^7_4]

### 모바일 환경 평가 방법론

#### 1. 엣지 디바이스 벤치마크 구성

SLM-Bench는 서버급 GPU(NVIDIA L4, A10)와 엣지 디바이스(NVIDIA Jetson Orin AGX 16GB/64GB)에서 동일한 평가를 수행하여 모바일 환경에서의 실제 성능을 측정합니다. Jetson Orin AGX는 온디바이스 AI의 대표적인 플랫폼으로, 실제 모바일 배포 시나리오를 반영합니다.[^7_4]

#### 2. 벤치마킹 파이프라인

SLM-Bench는 7개 모듈로 구성된 통합 파이프라인을 제공합니다:[^7_1][^7_4]

1. **Universal Data Loader**: 다양한 형식의 데이터셋을 통일된 구조로 변환
2. **Preprocessing**: 데이터 정제 (트리밍, 특수 기호 제거, 변환)
3. **Calling**: SLM 및 태스크 실행 관리
4. **Post-processing**: 추론 후 출력 추가 정제
5. **Evaluation**: 적절한 메트릭 적용하여 성능 평가
6. **Report**: 결과 및 시각화 종합
7. **Logging**: 파이프라인 전체 이벤트 기록 (추적성, 디버깅, 투명성)

[^7_1][^7_4]

#### 3. 랭킹 방법론

SLM-Bench는 각 SLM이 다양한 실험 설정에서 1위(gold), 2위(silver), 3위(bronze)를 차지한 횟수를 계산하여 종합 성능을 평가합니다. 점수 기반 평가도 병행하여 gold 3점, silver 2점, bronze 1점을 부여합니다. 이 접근법은 단일 집계 메트릭에 의존하지 않고 다양한 조건에서의 순위를 고려하여 전체 모델 성능을 평가합니다.[^7_1][^7_4]

### SLM-Bench 주요 발견

arXiv 논문의 실험 결과는 다음과 같은 핵심 인사이트를 제공합니다:[^7_4]

**정확성 부문:**

- **Llama-3.2-1B**: 가장 많은 gold 메달 획득, 최고 정확도 모델[^7_4]
- **Mistral-7B**: Llama-3.2-1B에 이어 2위, 일관된 출력 품질[^7_4]
- **Gemma-3-1B, Phi-3-3.8B**: 상위 3위권 빈번 진입[^7_4]

**연산 효율성 부문:**

- **GPT-Neo-1.3B**: gold 메달 최다 획득, 처리 속도와 리소스 사용 우수[^7_4]
- **TinyLlama-1.1B, ShearedLlama-2.7B**: 높은 효율성 시연[^7_4]

**에너지 소비 부문:**

- **Phi-1.5B**: 가장 에너지 효율적인 모델[^7_4]
- **StableLM-3B, GPT-Neo-1.3B**: 2위 공동, 지속가능한 설계[^7_4]

**주요 관찰:**

1. **정확성과 효율성의 비상관성**: Llama-3.2-1B는 작은 크기에도 불구하고 최고 정확도를 달성했지만 연산 및 에너지 소비에서는 저조한 성능을 보임[^7_4]
2. **연산과 소비의 차이**: 일부 모델은 빠른 런타임을 위해 더 많은 에너지를 사용하고, 유사한 연산량에서도 비병렬화 연산과 아키텍처 병목으로 인해 효율성이 다름[^7_4]

### 한국어 SLM 벤치마크

국내 커뮤니티에서도 SLM의 한국어 성능 평가가 활발히 진행되고 있습니다. Arca.live의 SLM 한국어 벤치마크는 1~3B 규모 모델을 대상으로 다음과 같은 평가를 수행했습니다:[^7_5][^7_6]

**평가 벤치마크:**

- 4종 MCQA(Multiple Choice Question Answering) 벤치마크
- Language Confusion 테스트

**평가 모델 예시:**

- Kanana, HyperCLOVA X, Qwen 등 한국어 특화 SLM[^7_5]

**정성 평가:**
모델 벤치마크 외에도 실제 사용자 관점에서 자연스럽고 정확한 응답을 확인하기 위한 정성 평가 진행[^7_5]

### 실무 권장사항

SLM-Bench의 종합 분석 결과, 모바일 환경에서 SLM 선택 시 다음과 같은 권장사항을 제시합니다:[^7_4]


| 우선순위 | 권장 모델 | 특징 |
| :-- | :-- | :-- |
| **정확도 최우선** | Llama-3.2-1B | 최고 정확도, 높은 연산/에너지 비용 |
| **빠른 실행 속도** | GPT-Neo-1.3B | 우수한 런타임 성능, 지연시간 민감 작업 적합 |
| **에너지 효율성** | Phi-1.5B | 최고 에너지 효율, 저전력/엣지 디바이스 이상적 |
| **균형잡힌 성능** | Mistral-7B | 모든 기준에서 안정적, 다목적 선택 |

[^7_4]

### 온디바이스 소형언어모델 기술개발 동향

ETRI의 기술개발 동향 보고서는 MT-Bench(Multitask Benchmark)를 통해 SLM의 일반적인 언어 이해 및 생성 능력을 종합적으로 평가합니다. MT-Bench는 다양한 자연어 처리 태스크를 통해 모델의 범용성을 측정하며, 온디바이스 환경에서의 실용성을 검증하는 핵심 벤치마크입니다.[^7_7]

## 온디바이스 AI용 개인정보 보호 및 데이터 로컬 유지 기술 로드맵

온디바이스 AI의 핵심 가치는 개인정보 보호와 데이터 주권 확보입니다. 모든 연산이 기기 내부에서 수행되고 외부로 전송되는 데이터가 없으므로 데이터 센터에 사용자 입력을 전송해야 하는 클라우드 AI와 비교하면 개인정보 유출 위험이 매우 낮습니다.[^7_8][^7_9]

### 개인정보 보호의 3단계 로드맵

#### Phase 1: 로컬 처리 기반 구축 (2024-2025)

**핵심 기술:**

1. **온디바이스 추론**: 모든 AI 모델이 로컬 디바이스에서 실행되어 원시 데이터가 외부로 전송되지 않음[^7_9]
2. **데이터 격리**: 민감한 개인 정보를 로컬 디바이스 내에서 처리하여 외부 유출 위험 최소화[^7_10]
3. **엣지 AI 데이터**: 클라우드로 대부분의 처리를 이동시키는 데 드는 에너지를 절감하고 데이터 보안 향상[^7_11]

**장점:**

- 개인정보보호: 기기 내부에서 데이터 처리[^7_12]
- 저지연성: 네트워크 왕복 시간 제거[^7_12]
- 안정성: 인터넷 연결 불필요[^7_12]
- 네트워크 트래픽 사용 효율성[^7_12]

**단점:**

- 하드웨어 성능에 맞춰 경량화된 모델 필요[^7_8]
- 모델 업데이트 복잡성[^7_12]


#### Phase 2: 연합학습 기반 프라이버시 보존 (2025-2026)

**연합학습 (Federated Learning):**
연합학습은 데이터를 중앙 서버로 전송하지 않고 각 디바이스에서 로컬로 AI 모델을 학습한 후 모델 파라미터만 공유하는 분산 학습 방식입니다. arXiv 논문 2411.01140v1 "Privacy-Preserving Federated Learning with Differentially Private Hyperdimensional Computing"은 FL의 개인정보 보호 강화를 위한 핵심 기법을 제시합니다.[^7_13][^7_14][^7_15]

**FL의 4가지 공격 시나리오:**

1. **도청(Eavesdropping)**: 클라이언트와 서버 간 통신 가로채기[^7_15]
2. **악의적 참가자(Malicious Participant)**: 정당한 클라이언트로 위장하여 글로벌 모델 접근[^7_15]
3. **서버 침해(Server Compromise)**: 중앙 서버 해킹으로 글로벌 모델 노출[^7_15]
4. **신뢰할 수 없는 서버(Untrusted Server)**: 서버 자체가 로컬 모델 분석[^7_15]

**차등 프라이버시 (Differential Privacy):**
DP는 데이터나 모델에 정교하게 보정된 노이즈를 추가하여 개별 레코드가 분석 중에도 개인정보를 유지하도록 보장합니다. Google, Microsoft, Apple 등 주요 기업이 DP를 데이터 수집 관행에 통합하여 사용자 프라이버시를 향상시켰습니다.[^7_16][^7_15]

**DP의 수학적 정의:**


| 개념 | 정의 | 설명 |
| :-- | :-- | :-- |
| **(ε, δ)-DP** | $\mathbb{P}[M(I_1)] \leq \exp(\epsilon) \cdot \mathbb{P}[M(I_2)] + \delta$ | 단일 데이터 포인트의 포함/제외가 결과에 제한된 영향 |
| **가우시안 메커니즘** | $M(I) = f(I) + \mathcal{N}(0, \sigma_{dp}^2)$ | 평균 0, 분산 σ²의 가우시안 노이즈 추가 |
| **민감도 (Sensitivity)** | $\Delta f = \max_{I_1, I_2} \|f(I_1) - f(I_2)\|$ | 단일 데이터 포인트가 출력에 미치는 최대 영향 |
| **노이즈 분산 조건** | $\sigma_{dp}^2 > 2\ln(1.25/\delta) \cdot (\Delta f^2 / \epsilon^2)$ | (ε, δ)-DP 보장을 위한 최소 노이즈 분산 |

[^7_15]

**FedHDPrivacy 프레임워크:**
FedHDPrivacy는 연합학습, 초차원 컴퓨팅(Hyperdimensional Computing), 차등 프라이버시를 결합한 설명 가능한 AI(XAI) 프레임워크입니다. 이 프레임워크는 이전 라운드의 누적 노이즈를 정확하게 추적하고 필요한 증분 노이즈만 추가하여 개인정보와 정확도 사이의 균형을 관리합니다.[^7_13][^7_15]

**FedHDPrivacy의 핵심 기여:**

1. 클라이언트와 중앙 서버 모델을 보호하기 위한 필요 노이즈 정확 결정[^7_15]
2. 이전 라운드의 누적 노이즈를 계산하여 DP 노이즈 과다 추정 방지[^7_15]
3. 반복 학습 과정에서 과도한 노이즈 추가 회피로 개인정보와 정확도 최적 균형[^7_15]
4. FedAvg, FedSGD, FedProx, FedNova, FedAdam 대비 최대 38% 성능 향상[^7_15]

#### Phase 3: 하드웨어 기반 보안 강화 (2026-2027)

**엣지 AI를 위한 로드맵 (Dagstuhl Perspective):**
ACM Digital Library의 "Roadmap for Edge AI: A Dagstuhl Perspective"는 엣지 AI의 개인정보 보호 로드맵을 제시합니다:[^7_17][^7_18]

**핵심 원칙:**

1. **로컬 데이터 처리**: 데이터를 로컬로 유지 및 처리하여 개인정보 향상[^7_18][^7_17]
2. **AI 워크플로우 인터페이스 이동**: 처리 초점을 디바이스로 이동[^7_17][^7_18]
3. **하드웨어-소프트웨어 공동 설계**: 에너지 효율성을 위해 양측 최적화[^7_19]

**기술 스택:**


| 계층 | 기술 | 개인정보 보호 메커니즘 |
| :-- | :-- | :-- |
| **하드웨어** | NPU, TPU, Secure Enclave | Trusted Execution Environment (TEE) |
| **모델** | SLM, 양자화 모델 | 온디바이스 추론, 데이터 로컬 유지 |
| **프레임워크** | FL, DP, HD | 분산 학습, 노이즈 주입, 설명 가능성 |
| **애플리케이션** | 의료, 금융, IoT | 엔드투엔드 암호화, 접근 제어 |

[^7_18][^7_17][^7_15]

### 기술별 성숙도 및 배포 시기

| 기술 | 현재 성숙도 (2026) | 배포 시기 | 주요 과제 |
| :-- | :-- | :-- | :-- |
| **온디바이스 추론** | 상용화 | 현재 | 모델 크기 vs 정확도 trade-off |
| **연합학습 (FL)** | 파일럿 배포 | 2025-2026 | 통신 오버헤드, 클라이언트 이질성 |
| **차등 프라이버시 (DP)** | 연구/개발 | 2026-2027 | 노이즈 vs 정확도 균형 |
| **동형암호 (HE)** | 초기 연구 | 2027+ | 계산 오버헤드 |
| **Secure Multiparty Computation (SMC)** | 초기 연구 | 2027+ | 통신 비용 |
| **하드웨어 TEE** | 상용화 | 현재 | 사이드 채널 공격 방어 |

[^7_14][^7_16][^7_15]

### 산업별 적용 로드맵

#### IoT 제조 환경

arXiv 논문의 실제 케이스 스터디는 제조 머시닝 작업의 인프로세스 모니터링에서 FedHDPrivacy가 개인정보를 보호하면서 FedAvg 대비 38% 향상된 성능을 달성했음을 보고합니다. 이는 IoT 환경에서 연속 학습(continuous learning)과 개인정보 보호를 동시에 달성할 수 있음을 입증합니다.[^7_13][^7_15]

#### 의료 AI

민감한 환자 데이터를 로컬 디바이스에서 처리하고 FL과 DP를 결합하여 병원 간 협업 학습을 가능하게 하면서도 HIPAA 규정 준수를 보장합니다.[^7_14][^7_16]

#### 스마트폰 음성 비서

온디바이스 AI를 적용하여 사용자의 음성 데이터를 클라우드로 전송하지 않고도 로컬에서 응답할 수 있습니다. 개인정보 보호 강화와 함께 신속하고 정확한 서비스를 제공합니다.[^7_20]

### 2026년 이후 기술 전망

**Belt and Braces 접근법:**
CACM의 "Belt and Braces: When Federated Learning Meets Differential Privacy"는 FL과 DP를 결합하여 더 포괄적인 데이터셋으로 머신러닝 모델을 학습하고 개선하는 이중 보안 접근법을 제시합니다. 이 접근법은 두 기술의 상호 보완적 강점을 활용하여 개인정보 보호를 극대화합니다.[^7_16]

**Physical AI 시대 대응:**
온디바이스 AI 반도체 경쟁력 강화를 위한 기술 로드맵은 데이터 기반 지능형 자동화와 AI 시대 인프라 구축을 목표로 합니다. Physical AI는 로봇공학과 자율주행 등 물리적 환경과 상호작용하는 AI로, 실시간성과 개인정보 보호가 동시에 요구되어 온디바이스 AI의 중요성이 더욱 커질 것입니다.[^7_21]

온디바이스 AI의 개인정보 보호 기술은 로컬 처리, 연합학습, 차등 프라이버시, 하드웨어 보안의 다층 방어(defense-in-depth) 전략으로 진화하고 있으며, 2026년 이후에는 이러한 기술들의 통합과 표준화가 가속화될 것으로 전망됩니다.[^7_10][^7_12]
<span style="display:none">[^7_22][^7_23][^7_24][^7_25][^7_26][^7_27][^7_28][^7_29][^7_30][^7_31][^7_32][^7_33]</span>

<div align="center">⁂</div>

[^7_1]: https://www.themoonlight.io/ko/review/slm-bench-a-comprehensive-benchmark-of-small-language-models-on-environmental-impacts-extended-version

[^7_2]: https://www.ibm.com/kr-ko/think/topics/small-language-models

[^7_3]: https://huggingface.co/blog/jjokah/small-language-model

[^7_4]: https://blog.naver.com/qualcommkr/221687419678

[^7_5]: https://ariz1623.tistory.com/374

[^7_6]: https://arca.live/b/alpaca/122619426

[^7_7]: https://ettrends.etri.re.kr/ettrends/209/0905209009/082-092. 김근용_209%ED%98%B8%20%EC%B5%9C%EC%A2%85.pdf

[^7_8]: https://namu.wiki/w/온디바이스 인공지능

[^7_9]: https://www.minew.com/ko/on-device-ai-for-iot/

[^7_10]: https://www.irsglobal.com/bbs/rwdboard/28791

[^7_11]: https://www.seco.com/blog/details/how-edge-ai-data-lets-you-revolutionize-your-business-strategy

[^7_12]: https://www.copyright.or.kr/information-materials/trend/tmis/view.do?brdctsno=53345

[^7_13]: https://www.sciencedirect.com/science/article/abs/pii/S0045790625002046

[^7_14]: https://www.refontelearning.com/blog/federated-learning-for-privacy-preserving-ai-building-trust-in-a-decentralized-world

[^7_15]: https://developer.nvidia.com/ko-kr/blog/fine-tuning-gpt-oss-for-accuracy-and-performance-with-quantization-aware-training/

[^7_16]: https://cacm.acm.org/research/belt-and-braces-when-federated-learning-meets-differential-privacy/

[^7_17]: https://zenodo.org/records/7788524/files/3523230.3523235.pdf?download=1

[^7_18]: https://dl.acm.org/doi/pdf/10.1145/3523230.3523235

[^7_19]: https://velog.io/@boks/730-Today-I-Learned-2

[^7_20]: https://blog.naver.com/withnetworks/223331181330

[^7_21]: https://www.instagram.com/p/DLjuliEvY76/

[^7_22]: https://ncsoft.github.io/ncresearch/b93db425f816a64229e09d2e5777de401fec76ed

[^7_23]: https://news.hada.io/topic?id=17481

[^7_24]: https://discuss.pytorch.kr/t/slm-small-language-models-survey-measurements-and-insights/5292

[^7_25]: https://journal.kace.re.kr/xml/43240/43240.pdf

[^7_26]: https://arxiv.org/html/2411.03350v1

[^7_27]: https://www.sciencedirect.com/science/article/pii/S016412122600049X

[^7_28]: https://www.meta-intelligence.tech/en/insight-llm-evaluation

[^7_29]: https://github.com/swordlidev/Evaluation-Multimodal-LLMs-Survey

[^7_30]: https://www.qualifire.ai/posts/llm-evaluation-frameworks-metrics-methods-explained

[^7_31]: https://arxiv.org/html/2411.01140v1

[^7_32]: https://en.wikipedia.org/wiki/Language_model_benchmark

[^7_33]: https://arxiv.org/html/2508.15478v1


---

## 온디바이스 연합학습(Federated Learning) 최신 알고리즘 및 통신 효율성 최적화

연합학습(Federated Learning, FL)은 분산된 디바이스에서 원시 데이터를 공유하지 않고 로컬로 AI 모델을 학습한 후 모델 파라미터만 중앙 서버에 전송하여 집계하는 분산 학습 방식입니다. 온디바이스 환경에서 FL은 개인정보 보호와 데이터 주권 확보라는 핵심 가치를 실현하지만, 제한된 컴퓨팅 자원, 통신 대역폭, 이질적인 디바이스 성능이라는 근본적인 도전 과제에 직면합니다.[^8_1][^8_2][^8_3][^8_4]

### 최신 연합학습 알고리즘

#### 1. FedAvg (Federated Averaging)

FedAvg는 가장 널리 사용되는 기본 FL 알고리즘으로, 각 클라이언트에서 로컬 SGD(Stochastic Gradient Descent)를 여러 번 수행한 후 모델 파라미터를 서버에서 평균하는 방식입니다. 이는 매 배치마다 그래디언트를 전송하는 것보다 통신 오버헤드를 크게 줄입니다.[^8_5][^8_6]

**FedAvg의 한계:**

- 클라이언트가 유사한 컴퓨팅 자원과 데이터 분포를 가진다고 가정[^8_6]
- Non-IID(비독립 동일 분포) 데이터에서 성능 저하[^8_6]
- 느린 디바이스(stragglers)에 의해 전체 학습이 지연되는 동기식 방식[^8_4]


#### 2. FedProx

FedProx는 로컬 손실 함수에 **근위 항(proximal term)**을 추가하여 로컬 학습 중 글로벌 모델로부터의 큰 편차를 페널티화합니다. 이는 다양한 컴퓨팅 능력을 가진 디바이스가 서로 다른 수의 로컬 에폭을 실행할 때 수렴을 안정화시킵니다.[^8_6]

**FedProx 손실 함수:**

$$
\min_{w} F(w) + \frac{\mu}{2} \|w - w^{global}\|^2
$$

여기서 μ는 근위 정규화 강도를 제어하는 하이퍼파라미터입니다.[^8_6]

#### 3. SCAFFOLD (Stochastic Controlled Averaging for Federated Learning)

SCAFFOLD는 **제어 변수(control variates)**를 도입하여 Non-IID 데이터로 인한 클라이언트 드리프트를 완화하고, 로컬 업데이트가 글로벌 모델과 더 잘 정렬되도록 보장합니다.[^8_6]

#### 4. FedNova (Normalized Averaging)

FedNova는 이질적인 FL에서 **목적 함수 불일치 문제(objective inconsistency problem)**를 해결합니다. 기존 FedAvg는 각 디바이스가 동일한 수의 로컬 스텝을 수행한다고 가정하지만, 실제로는 디바이스 성능 차이로 인해 로컬 스텝 수가 다를 수 있습니다.[^8_7][^8_8]

**FedNova의 핵심:**

- 정규화된 평균화 방법으로 목적 함수 불일치 제거[^8_7]
- 빠른 오류 수렴 유지[^8_7]
- 그래디언트 압축/양자화 및 공정한 집계 기법과 호환 가능[^8_8]


#### 5. FedAdam \& FedYogi (적응형 최적화)

FedAdam과 FedYogi는 Adam의 **적응형 학습률 메커니즘**을 연합 평균화로 확장하여, 과거 그래디언트 통계를 기반으로 파라미터별 학습률을 조정합니다. 이는 불균등한 클라이언트 참여 또는 노이즈가 많은 업데이트 시나리오에서 수렴을 개선합니다.[^8_6]

#### 6. PARS (Performance-driven Adam-based Resilient SCAFFOLD)

PARS는 FedAvg, FedProx, FedNova, FedYogi를 일관되게 능가하는 최신 알고리즘입니다. PARS는 Adam 기반 최적화와 SCAFFOLD의 제어 변수를 결합하여, IID 및 Non-IID 데이터 분할 모두에서 10개 및 100개 클라이언트 설정에서 우수한 성능을 보입니다.[^8_9]

### 통신 효율성 최적화 기법

통신 비용은 연합학습의 주요 병목 지점으로, 특히 모바일 디바이스와 IoT 환경에서 제한된 대역폭과 간헐적 연결이 문제입니다.[^8_10][^8_5]

#### 1. 그래디언트 압축 (Gradient Compression)

**양자화(Quantization):**
모델 업데이트를 저정밀도 형식으로 압축하여 전송 크기를 줄입니다. Google의 FL 구현은 양자화를 사용하여 전송되는 모델 가중치 크기를 최대 90% 감소시킵니다.[^8_5][^8_6]

**희소화(Sparsification):**
업데이트 벡터에서 중요도가 낮은 요소를 제거하여 구조적 희소성을 강제합니다. 희소 그래디언트를 전송하면 통신 페이로드를 크게 줄일 수 있습니다.[^8_11][^8_6]

#### 2. FedSMU (Symbolic Model Updates)

ICML 2025에 발표된 FedSMU는 클라이언트 모델 업데이트를 심볼화(즉, 각 모델 파라미터의 크기를 정규화)하여 데이터 이질성으로 인한 모델 이질성을 완화하고 전체 글로벌 모델의 일반화 성능을 향상시킵니다.[^8_12]

**FedSMU의 핵심 기여:**

- 각 디바이스가 AI 모델의 모든 가중치 변화에 대해 부호("+", "−")만 전송하여 통신 오버헤드를 수 비트로 감소[^8_12]
- Lion 옵티마이저의 분할 버전을 사용하여 일부는 디바이스에서, 일부는 서버에서 실행[^8_12]
- Non-convex 설정에서도 수렴 보장을 이론적으로 증명[^8_12]
- 이미지 및 텍스트 벤치마크에서 대역폭을 최대 10배 감소시키면서 선도적인 압축 기반 또는 최적화 기반 FL 방법을 능가[^8_12]


#### 3. DARF (Dynamic Adjustment of Random Projection)

ACM 2025에 발표된 DARF는 **랜덤 프로젝션(Random Projection)** 차원을 학습 역학에 따라 동적으로 조정하는 전략을 제안합니다. 이는 고정된 trade-off를 완화하여 통신 효율성을 극대화합니다.[^8_13]

#### 4. EF-Feddr (Error Feedback with Douglas-Rachford)

Frontiers in AI 2026에 발표된 EF-Feddr은 **Douglas-Rachford 분할 방법**과 오류 피드백을 결합하여 통신 효율성을 향상시킵니다. 이 방법은 데이터 프라이버시를 보존하고 데이터 사일로를 완화하는 분산 머신러닝 패러다임을 제공합니다.[^8_14]

### 자원 제약 환경을 위한 최적화

#### FTTE (Federated Tiny Training Engine)

arXiv 논문 2510.03165v1 "FTTE: Federated Learning on Resource-Constrained Edge Devices"는 메모리, 에너지, 통신 대역폭이 제한된 엣지 디바이스에서의 FL 배포를 위한 혁신적인 프레임워크를 제시합니다.[^8_15][^8_4]

**FTTE의 3가지 핵심 혁신:**

**1. 파라미터 선택 (Parameter Selection):**
서버는 TEE(Trusted Execution Environment)를 통해 클라이언트별 디바이스 프로파일을 안전하게 수집하고, 모든 클라이언트의 최소 메모리 제약 $M_{min}$을 설정합니다. 다음 제약 최적화 문제를 서버에서 해결합니다:[^8_4]

$$
w^{*} = \arg\max_{w} (\Delta Acc_w) \quad \text{s.t.} \quad Mem.(w) \leq M_{min}
$$

여기서 $w$는 학습 가능한 파라미터의 후보 부분집합이며, $\Delta Acc_w$는 $w$를 업데이트함으로써 예상되는 모델 정확도 향상입니다. 이는 각 클라이언트가 로컬 하드웨어 제한을 초과하지 않고 파라미터를 업데이트할 수 있도록 보장합니다.[^8_4]

**2. 희소 준동기 FL (Sparse Semi-Asynchronous FL):**
FTTE는 고정된 수의 클라이언트 업데이트 $B$를 수신한 후에만 집계하는 준동기 패러다임을 사용합니다. 각 클라이언트는 선택된 파라미터 부분집합 $w^*$만 로컬로 학습하고 희소 파라미터 업데이트만 서버에 전송합니다. 이는 전체 모델 업데이트 대비 통신 및 온디바이스 메모리 요구사항을 크게 줄입니다.[^8_4]

**3. Staleness 함수 (Staleness-Weighted Aggregation):**
FTTE는 각 버퍼링된 업데이트의 **시간적 나이(age)**와 글로벌 모델 대비 **통계적 편차(variance)**를 동시에 고려하는 staleness-aware 집계 함수를 도입합니다:[^8_4]

$$
Staleness(\hat{w}^i) = (1 + Age(\hat{w}^i) \times Var(\hat{w}^i, \hat{w}_g))^{-1}
$$

여기서 $Age(\hat{w}^i)$는 클라이언트 $i$의 업데이트가 수신된 이후 경과한 통신 스텝 수이며, $Var(\hat{w}^i, \hat{w}_g)$는 집계 시점의 글로벌 모델 $w_g$와 로컬 모델 $w_i$ 간의 레이어별 분산 합입니다. 이는 오래되고 높은 편차를 가진 업데이트의 기여도를 억제하여 학습을 안정화시킵니다.[^8_4]

**FTTE의 성능 결과 (CIFAR-10 기준):**


| 메트릭 | FedAvg 대비 개선 |
| :-- | :-- |
| 수렴 속도 | 81% 빠름 |
| 온디바이스 메모리 사용량 | 80% 감소 |
| 통신 페이로드 | 69% 감소 |
| 스케일링 | 500 클라이언트, 90% stragglers 지원 |

[^8_15][^8_4]

**Table 1 분석 (100 클라이언트, 50% stragglers, 30초 지연):**

CIFAR-10에서 MCUNet 모델, IID 데이터 분포(α=10000), 목표 정확도 73.1%:

- FedAvg: 5000 스텝 (FTTE 대비 7.09배 느림)
- AsyncFL: >10000 스텝 (>14.18배 느림)
- FedBuff: 1497 스텝 (2.12배 느림)
- **FTTE: 705 스텝**

Non-IID 데이터(α=0.1)에서는 AsyncFL과 FedBuff가 대부분 불안정한 손실로 실패("Osc.")한 반면, FTTE는 안정적으로 수렴합니다.[^8_4]

#### 자원 최적화 통합 프레임워크

International Journal of AI, Big Data and Cloud Management Systems의 "Federal Learning Optimization for Edge Devices with Limited Resources" 연구는 다층 최적화 접근법을 제안합니다:[^8_11]

**1. 경량 모델 아키텍처:**

- 양자화 및 프루닝 기법 적용[^8_11]

**2. 적응형 클라이언트 선택:**

- 디바이스의 능력 또는 에너지 수준에 기반한 선택[^8_11]

**3. 통신 효율적 집계 프로토콜:**

- 주기적 평균화(periodic averaging)[^8_11]
- 비동기 업데이트(asynchronous updates)[^8_11]
- 희소화된 그래디언트(sparsified gradients)[^8_11]

**4. 실시간 모니터링:**

- 엣지 노드의 부하 인식 스케줄링[^8_11]

**실험 결과 (Raspberry Pi 4 \& NVIDIA Jetson Nano):**

- 통신 비용: 38.7% 감소
- 수렴 속도: 41.3% 빠름
- 에너지 절약: 50.6%

[^8_11]

### 한국 연구 동향: 제한된 자원을 효율적으로 사용하는 On-device 연합학습

KISTI의 과제 보고서는 3년간 수행된 "제한된 자원을 효율적으로 사용하는 on-device 연합학습 기법 연구"의 핵심 성과를 제시합니다:[^8_1]

**주요 연구 내용:**

1. **Binary 경량화 신경망 설계**: 제한된 컴퓨팅 및 네트워크 자원을 효율적으로 사용[^8_1]
2. **실제 네트워크 요구사항 반영 스케줄링 기법**: 통신 스케줄링 최적화[^8_1]
3. **Context-aware 연합학습 기법**: 주어진 기기 간 상황을 고려[^8_1]

**키워드:**

- 온디바이스 인공지능 (On-device AI)
- 연합학습 (Federated Learning)
- 자원 최적화 (Resource Optimization)
- 이진 신경망 (Binary Neural Networks)
- 통신 스케줄링 (Communications Scheduling)

[^8_1]

### 산업 적용 사례

#### SAKAK의 초개인화 AI

SAKAK(사각)은 연합 학습 기반 솔루션으로 초개인화(Hyper-Personalized) AI Agent를 구축합니다:[^8_16]

**핵심 기술:**

- 여러 특징모델을 조합하여 고객별 특화 AI 모델 구현[^8_16]
- 개인화 AI 모델 학습 시 고객 디바이스에서의 연산량 최소화[^8_16]
- 고객 성향정보를 개인화 AI 모델에 안전하게 암호화하여 활용[^8_16]
- 서버와 고객 디바이스 간 데이터 전송 소요 최소화[^8_16]

**장점:**

- 민감한 개인정보는 고객 디바이스에서 저장/처리[^8_16]
- 대규모 데이터 보관/처리를 위한 별도 서버/스토리지 불필요[^8_16]
- 기존 연합학습 프레임워크에 쉽게 적용 가능[^8_16]


### 연합학습 프레임워크 비교

| 프레임워크 | 개발사 | 핵심 특징 | 통신 최적화 |
| :-- | :-- | :-- | :-- |
| **TensorFlow Federated** | Google | FL API + Federated Core API, 손실 압축 알고리즘, DP-FedAvg | 양자화로 통신 비용 90% 감소 [^8_5][^8_6] |
| **Flower** | 오픈소스 | 다양한 FL 알고리즘 구현 (FedAvg, FedProx, FedNova) | 모듈식 압축 지원 [^8_7] |
| **IBM FL** | IBM | Decision Trees, 강화학습 포함 | 엔터프라이즈 환경 최적화 [^8_17] |
| **FTTE** | 연구 프로젝트 | 희소 업데이트, staleness-aware 집계 | 69% 페이로드 감소 [^8_4] |

### 향후 연구 방향

**PNAS의 Communication-Efficient FL 연구**는 엣지 디바이스가 효율적으로 모델 파라미터를 학습하고 전송할 수 있는 통신 효율적 FL 프레임워크를 제안합니다. 2026년 이후 FL 연구는 다음 방향으로 진화할 것으로 전망됩니다:[^8_18]

1. **보안 및 공정성**: Byzantine-robust 분산 최적화, 공정한 자원 할당[^8_19]
2. **프라이버시**: 차등 프라이버시와 동형암호의 통합[^8_19]
3. **스케일링**: 수천~수만 디바이스 대규모 FL 시스템[^8_19]
4. **적응형 최적화**: 디바이스 이질성과 데이터 분포 변화에 동적 대응[^8_19]

온디바이스 연합학습은 개인정보 보호, 통신 효율성, 자원 제약을 동시에 해결하는 핵심 기술로, FTTE와 FedSMU 같은 최신 알고리즘은 실제 배포 가능한 수준의 성능을 입증했습니다.[^8_12][^8_4]
<span style="display:none">[^8_20][^8_21][^8_22][^8_23][^8_24][^8_25]</span>

<div align="center">⁂</div>

[^8_1]: https://scienceon.kisti.re.kr/srch/selectPORSrchReport.do?cn=TRKO202400009423

[^8_2]: https://ahha.ai/2023/11/09/fl/

[^8_3]: https://www.couchbase.com/blog/ko/federated-learning/

[^8_4]: https://techblog.samsung.com/blog/article/75

[^8_5]: https://jihyeonryu.github.io/2021-04-21-survey-paper2/

[^8_6]: https://milvus.io/ai-quick-reference/what-optimization-algorithms-are-used-in-federated-learning

[^8_7]: https://flower.ai/docs/baselines/fednova.html

[^8_8]: https://arxiv.org/pdf/2007.07481.pdf

[^8_9]: https://www.sciencedirect.com/science/article/abs/pii/S0020025526003051

[^8_10]: https://www.sciencedirect.com/science/article/abs/pii/S1566253524006122

[^8_11]: https://ijaibdcms.org/index.php/ijaibdcms/article/view/224

[^8_12]: https://icml.cc/virtual/2025/poster/45089

[^8_13]: https://dl.acm.org/doi/full/10.1145/3797234.3797241

[^8_14]: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1699896/full

[^8_15]: https://arxiv.org/html/2510.03165v1

[^8_16]: https://www.sakak.co.kr/tech

[^8_17]: https://www.ibm.com/kr-ko/think/topics/federated-learning

[^8_18]: https://www.pnas.org/doi/10.1073/pnas.2024789118

[^8_19]: https://www.ieeesmc.org/cai-2026/w6-fede/

[^8_20]: https://ksp.etri.re.kr/ksp/plan-report/file/791.pdf

[^8_21]: https://blog.cslee.co.kr/federated-learning/

[^8_22]: https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11433813

[^8_23]: https://www-sop.inria.fr/members/Giovanni.Neglia/federatedlearning/

[^8_24]: https://www.youtube.com/watch?v=GAUEtmDYeC0

[^8_25]: https://events.vtools.ieee.org/m/361144


---

# 온디바이스 FL 기반의 개인화 모델 배포 파이프라인 아키텍처

이제 종합적인 답변을 작성하겠습니다.

## 온디바이스 FL 기반의 개인화 모델 배포 파이프라인 아키텍처

온디바이스 연합학습(Federated Learning) 기반의 개인화 모델 배포는 클라우드 중앙 집중식 학습의 개인정보 문제를 해결하면서도, 각 사용자의 고유한 데이터 분포와 선호도에 맞춤화된 AI 모델을 제공하는 핵심 패러다임입니다. arXiv 논문 2505.06907v2 "A Survey on Foundation Models for Personalized Federated Intelligence"는 개인화 연합 지능(Personalized Federated Intelligence, PFI)이라는 새로운 비전을 제시하며, AGI(인공 일반 지능)를 보완하는 API(인공 개인화 지능) 시대를 전망합니다.[^9_1][^9_2][^9_3]

### PFI의 핵심 개념 및 목적

**Personalized Federated Intelligence (PFI):**
표준 FL이 단일 글로벌 모델을 학습하는 것과 달리, PFI는 K개 참가자의 이질적인 데이터 분포에 맞춤화된 **개인화 모델 집합** $\Omega = \{\omega_1, \dots, \omega_K\}$을 학습합니다. 각 클라이언트 모델은 다음과 같이 분해됩니다:[^9_3]

$$
\omega_k = \Phi(\omega_g, \theta_k)
$$

여기서 $\omega_g$는 공유된 글로벌 파라미터, $\theta_k$는 클라이언트별 특화 파라미터, $\Phi(\cdot)$는 글로벌 및 로컬 컴포넌트를 통합하는 개인화 매핑 함수입니다.[^9_3]

**PFI 목적 함수:**

$$
\min_{\omega_g, \Theta} \sum_{k=1}^{K} p_k F_k(\Phi(\omega_g, \theta_k))
$$

이 공식은 공유 파라미터와 개인화 파라미터를 동시에 학습하여 표준 FL과 명확히 구분됩니다.[^9_3]

### 5단계 개인화 모델 배포 파이프라인

#### Stage 1: 모델 초기화 및 분산

**1.1 Foundation Model 준비:**

- 사전학습된 FM(예: Gemini Nano, Llama-3.2, Phi-3-mini)을 클라우드 서버에서 준비[^9_3]
- 또는 여러 분산 데이터 사일로(병원, 기업 등)에서 협력적으로 처음부터 학습하여 개인정보를 초기부터 보호[^9_3]

**1.2 경량화 전처리:**

- **모델 프루닝(Model Pruning)**: 중요도가 낮은 뉴런, 어텐션 헤드, 레이어를 제거하여 희소 버전 생성[^9_3]
- **양자화(Quantization)**: FP32 → INT8 또는 INT4로 변환하여 모델 크기 80% 감소[^9_3]
- **지식 증류(Knowledge Distillation)**: 대규모 Teacher 모델의 지식을 소형 Student 모델로 전이[^9_3]

**경량화 기법 비교:**


| 기법 | 통신량 감소 | 계산량 감소 | 정확도 유지 | 대표 논문 |
| :-- | :-- | :-- | :-- | :-- |
| 구조적 프루닝 | ~80% | 높음 | 양호 | FedSpaLLM [^9_3] |
| 적응형 프루닝 | ~90% | 매우 높음 | 우수 | PPC-GPT [^9_3] |
| 양자화 (8비트) | ~75% | 보통 | 우수 | FedQLoRA [^9_3] |
| 지식 증류 | ~99.25% | 매우 높음 | 양호 | FedDAT [^9_3] |

[^9_3]

**1.3 클라이언트 프로파일 수집:**

- TEE(Trusted Execution Environment)를 통해 클라이언트별 디바이스 프로파일 안전하게 수집[^9_4]
- 메모리 용량, CPU/NPU 성능, 배터리 상태, 네트워크 대역폭 측정[^9_4]


#### Stage 2: 연합학습 기반 글로벌 모델 학습

**2.1 클라이언트 선택 전략:**

- **자원 기반 선택**: 디바이스 능력 또는 에너지 수준에 기반[^9_5]
- **적응형 선택**: 클라이언트 이질성을 고려한 동적 선택[^9_6]

**2.2 로컬 학습 (각 클라이언트에서):**

```python
# 의사 코드: 온디바이스 로컬 학습
def local_training(global_model, local_data, device_profile):
    # 1. 글로벌 모델 다운로드
    local_model = download_model(global_model)
    
    # 2. 디바이스 제약에 맞춘 파라미터 선택 (FTTE 방식)
    trainable_params = select_parameters(
        model=local_model,
        memory_limit=device_profile.memory,
        target_accuracy=device_profile.target_acc
    )
    
    # 3. 로컬 데이터로 선택된 파라미터만 학습
    for epoch in range(local_epochs):
        for batch in local_data:
            loss = compute_loss(local_model, batch)
            gradients = compute_gradients(loss, trainable_params)
            update_parameters(trainable_params, gradients)
    
    # 4. 희소 업데이트만 서버로 전송
    sparse_update = extract_update(trainable_params)
    return compress(sparse_update)  # 양자화 또는 희소화
```

**2.3 통신 효율적 집계:**

- **주기적 평균화(Periodic Averaging)**: 매 라운드마다 전송하지 않고 여러 에폭 후 전송[^9_5]
- **비동기 업데이트(Asynchronous Updates)**: stragglers 문제 완화[^9_4]
- **희소화된 그래디언트(Sparsified Gradients)**: 중요한 업데이트만 전송하여 통신 페이로드 69% 감소[^9_4]

**2.4 Staleness-Aware 집계 (FTTE 방식):**

$$
Staleness(\hat{w}^i) = (1 + Age(\hat{w}^i) \times Var(\hat{w}^i, \hat{w}_g))^{-1}
$$

여기서:

- $Age(\hat{w}^i)$: 클라이언트 i의 업데이트 수신 후 경과한 통신 스텝 수
- $Var(\hat{w}^i, \hat{w}_g)$: 글로벌 모델과 로컬 모델 간 레이어별 분산 합

[^9_4]

이 접근법은 오래되고 높은 편차를 가진 업데이트의 기여도를 억제하여 학습을 안정화시킵니다.[^9_4]

#### Stage 3: 개인화 레이어 적응

**3.1 개인화 기법:**


| 기법 | 설명 | 적용 사례 |
| :-- | :-- | :-- |
| **로컬 미세조정(Local Fine-Tuning)** | 글로벌 모델을 각 디바이스의 데이터로 추가 학습[^9_1] | 키보드 앱이 사용자 슬랭/오타 학습 |
| **메타 러닝(Meta-Learning)** | MAML로 몇 번의 로컬 스텝만으로 효과적 개인화[^9_1] | 헬스케어 앱의 환자 맞춤 진단 |
| **멀티태스크 학습(Multi-Task Learning)** | 공유 베이스 모델 + 사용자별 파라미터[^9_1] | 병원별 맞춤 예측 레이어 |
| **FedPer (분할 아키텍처)** | 하위 레이어(특징 추출)는 연합, 상위 레이어(분류)는 로컬[^9_1] | 개인정보 유출 없는 개인화 의사결정 |
| **Self-FL (불확실성 기반)** | 클라이언트 간/내 불확실성 정량화로 자동 균형[^9_2][^9_7] | Amazon Alexa의 사용자 맞춤 응답 |

**3.2 Self-FL의 베이지안 계층 모델:**
Amazon Science의 Self-aware Personalized FL 연구는 베이지안 계층 모델에서 영감을 받아, 각 클라이언트가 로컬 개인 모델과 글로벌 모델 학습을 자동으로 균형잡는 방법을 제안합니다:[^9_2][^9_7]

- **클라이언트 간 불확실성(Inter-client Uncertainty)**: 사용자 간 로컬 모델 차이 특성화 → 높을수록 개인화 중요[^9_2]
- **클라이언트 내 불확실성(Intra-client Uncertainty)**: 시간에 따른 로컬 모델 차이 프로파일링 → 높을수록 글로벌 모델 의존[^9_2]

이 방법은 기존 FL 대비 엣지 클라이언트 정확도를 향상시켜 Amazon 고객 디바이스를 더 반응성 있게 만듭니다.[^9_2]

#### Stage 4: 모델 배포 및 버전 관리

**4.1 안드로이드 앱 배포 전략:**

위키독스의 "안드로이드 온디바이스 AI 실전 가이드"는 모델 배포의 실무적 접근법을 제시합니다:[^9_8]

**APK/AAB 빌드와 모델 번들링:**

- **assets 폴더**: 모델 파일을 `app/src/main/assets/`에 저장, 압축 방지를 위해 `aaptOptions`에 `.tflite` 확장자 추가[^9_8]
- **Play Asset Delivery**: 150MB Play Store 제한 우회를 위해 대용량 모델을 분리 배포[^9_9][^9_8]
- **On-Demand Delivery**: 사용자가 특정 기능 활성화 시 모델 다운로드[^9_8]

**4.2 Firebase ML을 활용한 동적 모델 배포:**

```kotlin
// Firebase ML Custom Model 다운로드
val conditions = FirebaseModelDownloadConditions.Builder()
    .requireWifi()  // Wi-Fi 연결 시에만 다운로드
    .build()

FirebaseModelDownloader.getInstance()
    .getModel("personalized_model_v2", 
              DownloadType.LATEST_MODEL, 
              conditions)
    .addOnSuccessListener { model ->
        // 다운로드된 모델로 추론 실행
        val interpreter = Interpreter(model.file)
        // 로컬 폴백 모델 전략: 다운로드 실패 시 번들 모델 사용
    }
```

이 방법은 앱 업데이트 없이 새로운 개인화 모델을 사용자 기기에 배포할 수 있습니다.[^9_8]

**4.3 모델 버전 관리와 A/B 테스트:**

Firebase Remote Config와 A/B Testing을 이용해 사용자 집단을 나누고, 두 버전의 모델 중 어느 것이 더 좋은 성과를 내는지 데이터로 검증합니다:[^9_8]

```kotlin
// Firebase A/B Testing 설정
val remoteConfig = Firebase.remoteConfig
remoteConfig.fetchAndActivate()
    .addOnCompleteListener { task ->
        if (task.isSuccessful) {
            val modelVersion = remoteConfig.getString("model_version")
            loadModel(modelVersion)  // "v1" 또는 "v2"
        }
    }

// 성능 메트릭 기록
Analytics.logEvent("inference_latency", params)
Analytics.logEvent("model_accuracy", params)
```


#### Stage 5: 지속적 개선 및 적응적 정제

**5.1 Retrieval-Augmented Personalization:**
PFI 프레임워크는 RAG(Retrieval-Augmented Generation)를 통해 외부 사용자 관련 지식을 동적으로 통합하여 모델이 개별 사용자 컨텍스트와 지속적으로 진화할 수 있도록 합니다.[^9_3]

**5.2 온디바이스 지속 학습:**

- **Continuous Learning**: 사용자 피드백을 로컬에서 실시간으로 학습[^9_10]
- **Differential Privacy 통합**: DP-FedAvg로 로컬 업데이트에 노이즈 추가하여 개인정보 보호[^9_11]


### 통합 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    클라우드 서버 (Central Server)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. 글로벌 FM 초기화 (Gemini Nano, Llama-3.2, Phi-3)      │   │
│  │ 2. 경량화: 프루닝 + 양자화 + 증류                         │   │
│  │ 3. Staleness-Aware 집계 (FTTE)                          │   │
│  │ 4. 글로벌 모델 업데이트 및 배포                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             ▲ ▼                                  │
│                     통신 효율적 전송 (희소화/양자화)              │
│                             ▲ ▼                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲ ▼
┌─────────────────────────────────────────────────────────────────┐
│                엣지 디바이스 레이어 (Edge Devices)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  디바이스 1   │  │  디바이스 2   │  │  디바이스 K   │         │
│  │──────────────│  │──────────────│  │──────────────│         │
│  │ 1. 로컬 데이터│  │ 1. 로컬 데이터│  │ 1. 로컬 데이터│         │
│  │ 2. 파라미터   │  │ 2. 파라미터   │  │ 2. 파라미터   │         │
│  │    선택 (FTTE)│  │    선택 (FTTE)│  │    선택 (FTTE)│         │
│  │ 3. 로컬 학습  │  │ 3. 로컬 학습  │  │ 3. 로컬 학습  │         │
│  │ 4. 개인화     │  │ 4. 개인화     │  │ 4. 개인화     │         │
│  │    (Self-FL)  │  │    (FedPer)   │  │    (Meta-LR)  │         │
│  │ 5. 희소 업데이트│ │ 5. 희소 업데이트│ │ 5. 희소 업데이트│       │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲ ▼
┌─────────────────────────────────────────────────────────────────┐
│              애플리케이션 레이어 (Application Layer)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Firebase ML: 동적 모델 배포                            │   │
│  │ • Remote Config: A/B 테스트                             │   │
│  │ • Play Asset Delivery: 대용량 모델 분리 배포             │   │
│  │ • LiteRT/Core ML: 온디바이스 추론 런타임                │   │
│  │ • Analytics: 성능 메트릭 수집                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```


### 실무 구현 가이드

**클라우드-엣지 협업 아키텍처:**
Computer Society의 "Cloud-Edge Large-Tiny Model Collaborative (CELTC)" 연구는 딥 강화학습 기반으로 클라우드의 대규모 모델과 엣지의 소형 모델이 협업하여 처리를 최적화하는 아키텍처를 제안합니다.[^9_12]

**Google Privacy Sandbox의 온디바이스 개인화:**
Google의 Privacy Sandbox는 Federated Learning API를 제공하여 개인화 모델을 학습하고 배포할 수 있도록 지원합니다:[^9_13]

```java
// Federated Learning Job 생성
FederatedLearningJobRequest request = 
    new FederatedLearningJobRequest.Builder()
        .setTrainingInterval(Duration.ofDays(1))
        .setMinimumClients(100)
        .setModelId("personalized_keyboard_v2")
        .build();

FederatedLearningManager.getInstance(context)
    .scheduleFederatedLearningJob(request);
```

**Samsung의 온디바이스 최적화 기술:**
삼성리서치 AI 센터는 모델 크기를 줄이고 기기 환경에 맞게 실행 효율을 높이는 온디바이스 AI 최적화 기술을 개발하여, 개인화된 AI 경험을 제공합니다.[^9_14]

### 성능 지표 및 기대 효과

| 메트릭 | 기존 FL | PFI (FTTE) | 개선율 |
| :-- | :-- | :-- | :-- |
| 수렴 속도 (CIFAR-10) | 5000 스텝 | 705 스텝 | **81% 빠름** [^9_4] |
| 온디바이스 메모리 | 기준 | 20% | **80% 감소** [^9_4] |
| 통신 페이로드 | 기준 | 31% | **69% 감소** [^9_4] |
| 에너지 소비 (Raspberry Pi) | 기준 | 49.4% | **50.6% 절약** [^9_5] |
| 개인화 정확도 향상 | - | 1.91배 | **WorldLM 대비** [^9_3] |

온디바이스 FL 기반 개인화 모델 배포 파이프라인은 개인정보 보호, 통신 효율성, 자원 제약, 사용자 맞춤화를 동시에 해결하는 차세대 AI 배포 패러다임입니다. FTTE, Self-FL, FedSMU 같은 최신 알고리즘은 실제 배포 가능한 수준의 성능을 입증했으며, Firebase ML과 Privacy Sandbox 같은 플랫폼은 프로덕션 환경에서의 실용성을 제공합니다.[^9_2][^9_13][^9_4]
<span style="display:none">[^9_15][^9_16][^9_17][^9_18][^9_19][^9_20][^9_21][^9_22][^9_23][^9_24][^9_25][^9_26][^9_27][^9_28][^9_29][^9_30][^9_31]</span>

<div align="center">⁂</div>

[^9_1]: https://milvus.io/ai-quick-reference/how-does-personalization-work-in-federated-learning

[^9_2]: https://www.amazon.science/blog/personalized-federated-learning-for-a-better-customer-experience

[^9_3]: https://arxiv.org/html/2410.08661v1

[^9_4]: https://techblog.samsung.com/blog/article/75

[^9_5]: https://ijaibdcms.org/index.php/ijaibdcms/article/view/224

[^9_6]: https://events.vtools.ieee.org/m/361144

[^9_7]: https://www.amazon.science/publications/self-aware-personalized-federated-learning

[^9_8]: https://github.com/pprp/Awesome-LLM-Quantization

[^9_9]: https://wikidocs.net/336153

[^9_10]: https://milvus.io/ai-quick-reference/how-is-federated-learning-used-in-personalized-recommendations

[^9_11]: https://developer.nvidia.com/ko-kr/blog/fine-tuning-gpt-oss-for-accuracy-and-performance-with-quantization-aware-training/

[^9_12]: https://www.computer.org/csdl/journal/cc/2025/01/10820031/23b0N8zjpUQ

[^9_13]: https://privacysandbox.google.com/protections/on-device-personalization/create-federated-learning-job

[^9_14]: https://news.samsung.com/kr/ai-특집-ai를-손-안에-담다-온디바이스-최적화-기술의-혁

[^9_15]: https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning?hl=ko

[^9_16]: https://hyperconnect.github.io/2026/01/23/On-device-Face-Verification-Pipeline-Optimization.html

[^9_17]: https://introl.com/ko/blog/mlops-infrastructure-cicd-pipelines-model-training-deployment

[^9_18]: https://www.kibme.org/resources/journal/20250508095331015.pdf

[^9_19]: https://wikidocs.net/336147

[^9_20]: https://fastcampus.co.kr/data_online_mlopspj

[^9_21]: https://www.ibm.com/kr-ko/think/topics/machine-learning-pipeline

[^9_22]: https://blog.naver.com/suresofttech/223538409824

[^9_23]: https://cloud.google.com/discover/what-is-federated-learning

[^9_24]: https://www.couchbase.com/blog/federated-learning/

[^9_25]: https://www.computer.org/csdl/journal/oj/2020/01/09090366/1kkFDELch7W

[^9_26]: https://ieeexplore.ieee.org/document/10366825/

[^9_27]: https://www.ibm.com/think/topics/federated-learning

[^9_28]: https://www.meegle.com/en_us/topics/federated-learning/federated-learning-in-machine-learning-pipelines

[^9_29]: https://www.youtube.com/watch?v=gMN0D1rgbaE

[^9_30]: https://arxiv.org/html/2505.06907v2

[^9_31]: https://proceedings.mlr.press/v162/pillutla22a/pillutla22a.pdf

