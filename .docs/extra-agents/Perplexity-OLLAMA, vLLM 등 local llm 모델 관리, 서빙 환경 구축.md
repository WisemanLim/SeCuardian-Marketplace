<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# OLLAMA, vLLM 등 즉, local llm 모델 관리 및 서빙을 위한 환경을 구축하고자 합니다.

1. 최초 질의를 제외한 사용자의 질의에 응답이 최소 1초, 최대 30초 정도로 응답이 되어야 합니다. 예를 들면, hi를 질문하면 100ms정도 소요가 되어야 하며 추론이 필요한 내용은 최초 응답이 최대 30초 내에는 응답이 스트리밍되어야 합니다.
2. 미니피씨(DGX 등), 서버급(H100, or H200 등)의 폐쇄망(air-gap) 환경에서 제공하는 하드웨어 사양을 조사 및 비교, 추천합니다.
3. AWS, GCP, Azure 등의 컴퓨터자원을 조사 및 비교, 추천합니다.

요구사항은 단순히 “모델이 동작하는 환경”보다, **TTFT(Time To First Token)와 동시성 SLO를 보장하는 추론 플랫폼**으로 설계해야 합니다. 권장 방향은 폐쇄망 운영계에는 NVIDIA GPU 기반 vLLM을 주 서빙 엔진으로 두고, Ollama는 개발·검증·GGUF 기반 경량 모델 운영에 한정하는 하이브리드 구조입니다.

vLLM은 요청 도착부터 첫 토큰까지의 TTFT를 `vllm:time_to_first_token_seconds` 히스토그램으로 내보내므로, 목표치를 운영 SLO로 직접 관리할 수 있습니다.[^1_1][^1_2]

## 1. 지연시간 목표와 설계

“hi는 약 100 ms, 복잡한 질의도 30초 이내 스트리밍 시작”은 모델 크기·컨텍스트 길이·동시성에 따라 별도 SLO로 분리해야 현실적으로 보장됩니다.


| 트래픽 유형 | 권장 모델군 | 목표 TTFT | 권장 경로 | 비고 |
| :-- | --: | --: | :-- | :-- |
| 인사, 간단 Q\&A, 라우팅 | 3B–8B | p95 0.2–1초 | 소형 모델 전용 vLLM 풀 | 100 ms는 토크나이저·네트워크·게이트웨이까지 포함하면 매우 공격적 |
| 일반 업무 Q\&A, 요약 | 8B–32B | p95 1–5초 | 중형 vLLM 풀 | RAG 포함 시 검색 시간을 별도 분리 |
| 추론, 복잡 문서 분석 | 32B–70B | p95 3–15초 | 대형 vLLM 풀 | 첫 토큰을 먼저 스트리밍하고 생성은 지속 |
| 매우 긴 입력·에이전트 | 70B+ 또는 MoE | p95 10–30초 | 고메모리 GPU/멀티 GPU | 긴 prefill이 TTFT의 주된 원인 |

### 100 ms를 위한 조건

짧은 인사 질의에서 100 ms 수준은 가능하지만, “대형 모델”의 기본 경로로는 보장하기 어렵습니다. 다음처럼 경로를 분리해야 합니다.

- `hi`, 상태 확인, 자주 묻는 고정 문구는 API gateway 또는 Redis 캐시에서 즉시 응답합니다.
- 의도 분류에는 1B–4B급 소형 모델 또는 규칙 기반 fast-path를 둡니다.
- 8B 이상 모델 호출은 통상 수백 ms~수 초의 TTFT 목표로 측정합니다.
- 스트리밍은 반드시 SSE 또는 WebSocket으로 제공하여 “완성 응답 시간”이 아니라 “첫 토큰 도착 시간”을 UX 기준으로 관리합니다.
- RAG는 임베딩·벡터 검색·rerank·LLM prefill을 각각 계측해야 합니다. 특히 긴 문서 원문을 무제한으로 프롬프트에 넣으면 GPU가 충분해도 TTFT가 악화됩니다.


### 운영 아키텍처

```text
Client
  └─ API Gateway / Auth / Rate limit
       └─ Router
            ├─ Fast path: cache / canned response / tiny model
            ├─ vLLM small pool: 3B~8B
            ├─ vLLM medium pool: 14B~32B
            ├─ vLLM large pool: 70B / MoE
            └─ Ollama: 개발·개인 실험·GGUF 검증
                 └─ Observability: Prometheus + Grafana + tracing
```

핵심 지표는 다음 네 가지입니다.

- TTFT p50/p95/p99
- ITL(Inter-Token Latency) 또는 생성 토큰/초
- queue wait time 및 요청 거절률
- GPU 메모리/KV cache 사용률, prefix-cache hit rate

vLLM의 TTFT는 프런트엔드가 요청을 수신한 시점부터 산정되어 입력 처리 시간도 포함합니다. 즉, 서비스 레벨의 체감 지연을 감시하는 데 적합합니다.[^1_2]

## 2. 폐쇄망 하드웨어 권장

폐쇄망에서는 사양보다도 모델·컨테이너·드라이버·패키지·취약점 DB를 반입하는 **오프라인 공급망**이 성공의 핵심입니다. 운영계는 x86 Linux + NVIDIA CUDA 생태계를 기준으로 설계하고, DGX Spark류는 개발·PoC·소형/양자화 모델 검증 장비로 보는 것이 안전합니다.


| 등급 | 권장 구성 | 적합한 모델/업무 | 장점 | 주의점 |
| :-- | :-- | :-- | :-- | :-- |
| 개발·PoC | DGX Spark 128GB | 7B–32B, 양자화 70B 실험 | 작고 전력 효율적, 128GB 통합 메모리 | LPDDR5x 273GB/s라 HBM GPU 서버 대비 고동시성·긴 생성 성능은 제한적 |
| 부서 단위 운영 | 1–2× H100 80/94GB 또는 H200 141GB | 8B–32B 고동시성, 70B 양자화 | 단순한 운영, 낮은 초기 복잡도 | 70B BF16·긴 컨텍스트·동시성에는 VRAM 부족 가능 |
| 기업 운영 표준 | 4× H200 141GB 또는 8× H100 80GB | 32B/70B, 다중 모델 풀 | vLLM tensor parallelism, 높은 병렬 처리량 | PCIe만으로 구성 시 GPU 간 통신 병목 검토 필요 |
| 대규모·고가용성 | DGX H200 8-GPU 또는 HGX H200 | 70B BF16, 대형 MoE, 긴 컨텍스트, 다수 사용자 | 1,128GB HBM3e, NVSwitch | CAPEX·전력·냉각·랙 설계 필요 |

### DGX Spark

DGX Spark는 20코어 Arm CPU, 128GB LPDDR5x 통합 메모리, 10GbE 및 ConnectX-7을 제공하는 초소형 시스템입니다. 공식 하드웨어 문서상 메모리 대역폭은 273GB/s입니다.[^1_3]

따라서 다음 용도가 적합합니다.

- 오프라인 반입 모델의 기능 검증과 양자화 품질 비교
- Ollama/GGUF 기반 개발자 로컬 환경
- 7B–32B 모델의 단일 사용자 또는 낮은 동시성 서빙
- 운영 vLLM 설정값, 프롬프트, RAG 파이프라인 사전 검증

다만 128GB라는 **용량**만 보고 서버급 H100/H200과 동등하게 기대하면 안 됩니다. LLM 생성은 메모리 대역폭 의존성이 크므로 273GB/s 통합 메모리는 H100/H200 HBM 대비 고동시성 decode에서 불리합니다.

### H100과 H200

H100 SXM은 GPU당 80GB HBM3와 약 3.35TB/s 대역폭을, H200은 GPU당 141GB HBM3e와 4.8TB/s를 제공합니다. 두 GPU는 900GB/s급 NVLink 구성을 지원합니다.[^1_4][^1_5]

- **H100**: 8B–32B 중심, 70B 양자화, 비용을 고려한 운영 풀에 적합합니다.
- **H200**: 70B BF16, 더 큰 KV cache, 긴 컨텍스트, 높은 동시성에서 권장합니다.
- **H200 우선 사유**: 모델 웨이트 외에 KV cache가 크게 필요합니다. 141GB VRAM은 80GB 대비 더 많은 동시 요청 또는 긴 프롬프트를 수용하기 쉬워 TTFT 안정성에 유리합니다.

DGX H100/H200은 각각 8 GPU 구성을 제공하며, 총 GPU 메모리는 H100 640GB, H200 1,128GB입니다. 시스템 내부는 NVSwitch/NVLink로 연결됩니다.[^1_6]

### 폐쇄망 최종 추천

**가장 균형적인 선택: 4× H200 141GB 또는 8× H100 80GB의 Linux 서버 2대**를 권장합니다.

- 서버 A: 8B–32B low-latency 모델, RAG 답변, 일반 사용자 트래픽
- 서버 B: 32B–70B, 추론형 모델, 문서 분석·배치 처리, 장애 시 failover
- 각 서버: 듀얼 AMD EPYC 또는 Intel Xeon, RAM 512GB–1TB, 로컬 NVMe 15TB 이상, 100/200GbE, 이중 PSU
- GPU가 4장 이상이면 NVLink/NVSwitch 토폴로지를 반드시 조달 단계에서 명시합니다.
- 70B를 정밀도 저하 없이 안정적으로 서비스하고 긴 컨텍스트·다중 사용자를 동시에 다룰 경우, H200 쪽이 더 안전합니다.
- 비용을 통제하고 8B–32B가 주력이라면 H100 기반으로 시작한 뒤 모델 라우팅과 수평 확장을 권장합니다.


## 3. AWS·GCP·Azure 비교

퍼블릭 클라우드는 초기 수요가 불확실하거나 GPU 용량 검증, DR, 단기 대규모 배치, 성능 벤치마크에 유리합니다. 반면 엄격한 air-gap은 본질적으로 퍼블릭 클라우드와 양립하기 어려우므로, 민감 데이터가 외부 반출 불가라면 온프레미스가 기본입니다.


| 클라우드 | H100/H200 주요 선택지 | 강점 | 권장 경우 |
| :-- | :-- | :-- | :-- |
| AWS | P5: H100, P5e/P5en: H200, P6: B200 | 대규모 EFA, 강한 생태계, 장기 약정/예약 옵션 | AWS 기반 조직, 대규모 배치·분산 추론 |
| GCP | A3 High/Mega: H100, A3 Ultra: H200, A4: B200 | AI Hypercomputer, 고속 GPU 네트워크, Vertex AI 연계 | GKE·Vertex·BigQuery 기반 데이터/ML 환경 |
| Azure | ND H100 v5, ND H200 v5 | Azure AI·Entra ID·기업 보안·Microsoft 생태계 | Microsoft 중심 기업, 규제·ID 통합 요구 |

### AWS

AWS P5는 H100 기반이며, `p5.48xlarge`는 H100 8장, 총 640GB HBM3, 3.2Tbps EFA, 900GB/s NVSwitch를 제공합니다. P5e/P5en은 H200 8장과 총 1,128GB HBM3e를 제공하며 역시 최대 3.2Tbps EFA를 지원합니다.[^1_7]

최신 고성능 선택지는 P6-B200입니다. `p6-b200.48xlarge`는 B200 GPU 8장, 1,432GiB GPU 메모리, 2TiB 시스템 메모리, 최대 3.2Tbps 네트워크를 제공합니다.[^1_8][^1_9]

**추천:** 운영의 기본 GPU는 P5e/P5en(H200)으로 잡고, 피크 처리·대규모 benchmark 또는 최신 모델 실험에 P6-B200을 제한적으로 쓰는 방식이 합리적입니다.

### GCP

GCP A3 High는 H100 80GB 기반이고, A3 Ultra는 H200 141GB와 GPU 간 900GB/s NVLink full mesh를 제공합니다. A3 Ultra는 총 네트워크 3,600Gbps 및 GPUDirect RDMA를 제공합니다.[^1_10][^1_11]

또한 A4는 B200을 사용하며, `a4-highgpu-8g`는 GPU 8장, 1,440GB HBM3e, 3,600Gbps 네트워크 사양입니다.[^1_12]

**추천:** GKE 중심으로 vLLM을 Kubernetes에 운영하고, 고성능 네트워크 기반 멀티 노드 추론이나 데이터 파이프라인과의 통합이 중요하면 A3 Ultra(H200)를 우선 검토하십시오.

### Azure

Azure ND H100 v5는 H100 80GB GPU 8장, 96 vCPU, 약 1.9TB 시스템 메모리 구성을 제공합니다.[^1_13]

ND H200 v5는 H200 141GB GPU 8장, 96 vCPU, 약 1.85TB 시스템 메모리이며, VM 내부 H200 GPU 간 900GB/s NVLink와 VM당 3.2Tbps급 확장 네트워크를 명시합니다.[^1_14]

**추천:** Entra ID, Azure Policy, Private Link, Azure AI 계열과의 통합, 기업의 Microsoft 계약 체계가 중요한 경우 ND H200 v5가 가장 자연스러운 H200 선택지입니다.

## 4. 구축 우선순위

### 1단계: 성능 기준선 만들기

동일 모델·동일 프롬프트 세트로 Ollama와 vLLM을 비교하되, 모델 파일 형식과 양자화 수준을 혼동하지 않아야 합니다.

- Ollama: GGUF, 개발 편의성, 개인/소규모 워크로드
- vLLM: Hugging Face/Safetensors 계열, continuous batching, tensor parallelism, OpenAI 호환 API, 다중 사용자 운영
- 테스트 모델: 8B, 32B, 70B 각 1종
- 입력 길이: 128, 1K, 8K, 32K 토큰
- 동시성: 1, 4, 16, 64, 128
- 측정: p50/p95/p99 TTFT, output tok/s, total latency, GPU memory, queue delay


### 2단계: 모델 풀 분리

한 개의 대형 모델만 운영하면 짧은 질의도 긴 문서 질의와 같은 큐를 공유해 SLO가 무너집니다.

- Small pool: 간단 응답과 라우팅, 낮은 TTFT 최우선
- Medium pool: 일반 RAG/요약
- Large pool: 복잡 추론, 분석, agent 작업
- Batch pool: 임베딩, 인덱싱, 문서 대량 처리


### 3단계: 폐쇄망 운영 체계

- 승인된 모델의 hash, 라이선스, SBOM, 악성코드 검사 결과를 모델 레지스트리에 기록
- CUDA 드라이버, NVIDIA Container Toolkit, vLLM wheel, PyPI wheelhouse, Docker/OCI image를 오프라인 반입 패키지로 버전 고정
- 내부 Harbor/Artifactory와 Hugging Face 모델 mirror 운영
- API gateway에서 SSO, RBAC, tenant별 rate limit, 감사 로그 적용
- Prometheus/Grafana를 폐쇄망에 자체 구축하고 TTFT p95/p99, queue time, GPU utilization, KV cache pressure를 경보화
- 모델별 최대 컨텍스트와 `max_num_seqs`, GPU memory utilization, tensor parallel size를 별도 프로파일로 관리


## 권장 결론

현재 조건에서는 다음 조합을 권장합니다.

1. **개발/검증:** DGX Spark 또는 동급 단일 GPU 장비 + Ollama + vLLM 병행.
2. **폐쇄망 운영:** Linux 기반 4× H200 서버부터 시작하고, 서비스 분리와 HA를 위해 가능하면 동일 서버 2대로 확장.
3. **비용 우선 대안:** 8× H100 또는 2–4× H100으로 8B–32B 중심 서비스를 먼저 구축하고, 70B·장문·고동시성 수요가 확인되면 H200 풀을 추가.
4. **클라우드:** AWS P5e/P5en, GCP A3 Ultra, Azure ND H200 v5 가운데 기존 기업 계약과 데이터 플랫폼에 맞춰 선택. 순수 GPU 서빙 관점에서 모두 H200 8-GPU급 옵션을 제공하므로, 리전 가용성·할인·예약 가능 용량·네트워크 비용을 실제 견적으로 비교해야 합니다.[^1_7][^1_10][^1_14]

원하시면 다음 단계로, 목표 모델(예: Qwen3 32B/235B, Llama 70B 등), 예상 동시 사용자, 평균·최대 입력 토큰, 월간 요청량을 기준으로 **GPU 수량·vLLM 파라미터·CAPEX/OPEX·SLO 검증용 벤치마크 시나리오**까지 산정해드릴 수 있습니다.

<span style="display:none">[^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49]</span>

<div align="center">⁂</div>

[^1_1]: https://docs.vllm.ai/en/latest/design/metrics/

[^1_2]: https://docs.vllm.ai/en/stable/design/metrics/

[^1_3]: https://docs.nvidia.com/dgx/dgx-spark/hardware.html

[^1_4]: https://northflank.com/blog/h100-vs-h200

[^1_5]: https://ai-infrastructure.net/gpu-hopper/

[^1_6]: https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html

[^1_7]: https://aws.amazon.com/ec2/instance-types/p5/?tag=bestbrands0a9-20

[^1_8]: https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html

[^1_9]: https://aws.amazon.com/it/ec2/instance-types/p6/

[^1_10]: https://docs.cloud.google.com/compute/docs/gpus

[^1_11]: https://docs.cloud.google.com/compute/docs/gpus/gpu-network-bandwidth

[^1_12]: https://docs.cloud.google.com/ai-hypercomputer/docs/gpu

[^1_13]: https://learn.microsoft.com/fil-ph/azure/virtual-machines/sizes/gpu-accelerated/ndh100v5-series?tabs=sizebasic

[^1_14]: https://learn.microsoft.com/he-il/azure/virtual-machines/sizes/gpu-accelerated/nd-h200-v5-series

[^1_15]: https://www.thundercompute.com/blog/nvidia-h100-specs-full-guide

[^1_16]: https://gpusmith.com/hardware/systems/nvidia-dgx-spark

[^1_17]: https://petronellatech.com/hardware/h100-h200-nvlink-cluster-scaling/

[^1_18]: https://slyd.com/hardware/nvidia-hopper

[^1_19]: https://gpusmith.com/articles/en/nvidia-dgx-spark-review-specs-performance

[^1_20]: https://ifactoryapp.com/sap-integration/on-prem-ai/nvidia-dgx-spark-review-enterprise

[^1_21]: https://flopper.io/desktop/nvidia-dgx-spark

[^1_22]: https://blog.kubesimplify.com/day-3-the-dgx-spark-unpacked-gb10-unified-memory-sm-121-and-the-one-reason-this-hardware-exists

[^1_23]: https://toolhalla.ai/blog/nvidia-dgx-spark-complete-guide-2026

[^1_24]: https://ai-infrastructure.net/dgx-spark/

[^1_25]: https://www.spheron.network/blog/nvidia-h100-vs-h200/

[^1_26]: https://aws.amazon.com/ec2/instance-types/accelerated-computing/

[^1_27]: https://docs.cloud.google.com/compute/docs/machine-resource

[^1_28]: https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-ec2-p6-b200-aws-govcloud/

[^1_29]: https://docs.cloud.google.com/ai-hypercomputer/docs/understand-gpus

[^1_30]: https://docs.cloud.google.com/compute/docs/gpus/about-gpus

[^1_31]: https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-ec2-p6-b200-aws-govcloud/

[^1_32]: https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/overview

[^1_33]: https://learn.microsoft.com/en-us/azure/virtual-machines/accelerator-technologies/cuda-overview

[^1_34]: https://learn.microsoft.com/bg-bg/azure/virtual-machines/azure-hpc-vm-images

[^1_35]: https://learn.microsoft.com/th-th/azure/virtual-machines/sizes/gpu-accelerated/ndh100v5-series

[^1_36]: https://learn.microsoft.com/uk-ua/azure/virtual-machines/sizes/gpu-accelerated/nd-h200-v5-series?tabs=sizebasic

[^1_37]: https://learn.microsoft.com/fi-fi/Azure/virtual-machines/sizes/gpu-accelerated/ndh100v5-series

[^1_38]: https://learn.microsoft.com/ms-my/azure/virtual-machines/sizes/gpu-accelerated/ncadsh100v5-series

[^1_39]: https://docs.vllm.ai/en/v0.14.1/design/metrics/

[^1_40]: https://learn.microsoft.com/en-us/answers/questions/5619401/gpu-vram-information-is-not-available-for-vms-with

[^1_41]: https://learn.microsoft.com/pt-pt/azure/virtual-machines/sizes/gpu-accelerated/nd-h200-v5-series

[^1_42]: https://learn.microsoft.com/sk-sk/azure/virtual-machines/sizes/gpu-accelerated/nccadsh100v5-series

[^1_43]: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter

[^1_44]: https://akrisanov.com/vllm-metrics/

[^1_45]: https://dev.to/pilgrim2go/vllm-request-lifecycle-where-ttft-is-measured-5cca

[^1_46]: projects.local_llm.launcher_comparison

[^1_47]: projects.local_llm.on_prem_vllm_deployment

[^1_48]: projects.local_llm.vllm_tuning

[^1_49]: projects.local_llm.gguf_automation


---

# 각 운영체제 즉, MacOS, Linux, Windows 별로 Local LLM 환경을 표로 정리해 주세요. 즉, ollama, llama.cpp, vllm 외 추가적으로 조사하여 성능 및 지원하는 환경을 상세하게 정리합니다.

로컬 LLM 환경은 OS별 GPU 가속 경로가 달라서, **개발자용 데스크톱**, **폐쇄망 PoC**, **다중 사용자 서빙**을 분리해 선택하는 것이 좋습니다.\
실무적으로는 **macOS는 MLX/llama.cpp**, **Linux는 vLLM 중심**, **Windows는 Ollama·LM Studio·llama.cpp 또는 WSL2 vLLM**이 가장 안정적인 조합입니다.

## 도구별 핵심 비교

| 도구 | 성격 | 모델 형식·생태계 | 서빙/API | 성능 특성 | 권장 용도 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **Ollama** | 설치·모델 관리가 쉬운 로컬 런타임 | GGUF 중심, Ollama registry | OpenAI 호환 일부 및 자체 REST API, 스트리밍 | 단일 사용자·소규모 동시성에 편리. 고동시성 최적화는 vLLM 대비 제한적 | 개발자 PC, 폐쇄망 PoC, 모델 배포 자동화 |
| **llama.cpp** | C/C++ 기반 경량 추론 엔진 | GGUF 중심, 광범위한 양자화 | `llama-server`로 OpenAI 호환 서버 구성 가능 | CPU·Metal·CUDA·Vulkan 등 이식성이 가장 좋음. 저사양·엣지에 강함 | 다양한 OS/GPU, CPU-only, 경량·엣지 환경 |
| **vLLM** | 고성능 LLM 서빙 엔진 | Hugging Face Safetensors, AWQ/GPTQ/FP8 등 | OpenAI 호환 API, streaming, metrics | PagedAttention, continuous batching, prefix caching 기반으로 다중 사용자 처리량에 유리 | Linux GPU 서버, 사내 API, 운영 환경 |
| **MLX / MLX-LM** | Apple Silicon 특화 프레임워크 | MLX 변환 모델, MLX Community 생태계 | `mlx_lm.server` OpenAI 호환 HTTP API | Apple 통합 메모리·Metal에 최적화. Mac에서 매우 효율적 | Mac 개발·PoC, macOS 폐쇄망 개발 환경 |
| **LM Studio** | GUI 중심 로컬 앱/서버 | GGUF 및 지원 런타임 모델 | OpenAI 호환 로컬 서버 | 설치/모델 탐색/실험이 매우 쉬움. 운영 자동화에는 한계 | 비개발자 PoC, 데모, 모델 품질 비교 |
| **Jan** | 오픈소스 GUI + 로컬 서버 | GGUF 및 런타임별 지원 모델 | 로컬 API, GUI 중심 | 하드웨어 자동 감지·백엔드 선택, 개인 개발 환경에 편리 | 크로스플랫폼 데스크톱 개발 |
| **LocalAI** | 다중 백엔드 통합 API 서버 | GGUF, Safetensors 등 백엔드별 상이 | OpenAI 호환 API, Docker/OCI 배포 | llama.cpp·vLLM·MLX·Transformers 등을 한 API로 통합 | 폐쇄망 플랫폼, 멀티모달·STT·임베딩 통합 |
| **GPT4All** | 오프라인 우선 GUI | 소형·양자화 모델 중심 | 로컬 서버 옵션 | CPU에서도 간단하게 실행 가능하나 고성능 서빙 도구는 아님 | 개인용 오프라인 챗봇, 비기술 사용자 |

LocalAI는 llama.cpp, vLLM, MLX, Transformers 등 여러 백엔드를 선택적으로 설치할 수 있으며 CUDA, ROCm, Intel SYCL, Vulkan, Metal, Jetson L4T 등의 가속 변형을 제공합니다.[^2_1][^2_2]

## macOS 환경

Apple Silicon Mac은 별도 VRAM이 아닌 **통합 메모리(unified memory)** 를 사용합니다. 따라서 64GB/128GB/192GB 이상 메모리 구성은 큰 양자화 모델을 올리는 데 유리하지만, 장시간 다중 사용자 서빙의 처리량은 H100/H200급 CUDA 서버보다 제한됩니다.


| 도구 | Apple Silicon | Intel Mac | 가속 방식 | 운영 적합성 | 비고 |
| :-- | --: | --: | :-- | :-- | :-- |
| Ollama | 매우 적합 | 지원 | Metal | 개발·소규모 팀 | Apple Silicon에서 Metal 자동 사용 |
| llama.cpp | 매우 적합 | 지원 | Metal, CPU | 개발·엣지·경량 API | macOS에서 Metal backend가 기본 활성화 가능 |
| MLX-LM | 최적 | 미지원 | Metal / Apple unified memory | Mac 전용 개발·PoC | Apple Silicon 전용 |
| LM Studio | 적합 | 최근 버전은 사실상 비권장/미지원 | MLX, Metal 계열 | GUI 실험 | 최신 계열은 Apple Silicon 중심 |
| Jan | 적합 | 지원 가능 | Metal, MLX 계열 | 개인 개발 | Apple Silicon에서 Metal 자동 사용 |
| LocalAI | 가능 | 가능 | Metal, MLX, llama.cpp | Docker 기반 통합 API | 서버급 운영보다 Mac PoC 용도 |
| vLLM | 제한적 | 비권장 | Metal 실험 지원 | 개발 검증 | Linux 운영 대체재로는 비권장 |

MLX-LM은 모델 로드·추론·양자화·fine-tuning을 제공하며, `mlx_lm.server`로 OpenAI 호환 로컬 HTTP API를 제공합니다. Apple은 MLX-LM을 기반으로 Apple Silicon에서 로컬 agent workflow를 구성하는 방식을 공식 예시로 제시하고 있습니다.[^2_3]

llama.cpp는 macOS에서 Metal을 기본 backend로 사용할 수 있고, Apple Silicon GPU 가속에 적합합니다.[^2_4][^2_5]

### macOS 권장 조합

| 목적 | 추천 조합 | 이유 |
| :-- | :-- | :-- |
| 개인 개발·CLI 자동화 | Ollama + Open WebUI 또는 자체 FastAPI | 설치가 쉽고 API 자동화가 간단 |
| Apple Silicon 성능 우선 | MLX-LM + MLX 모델 | Apple 메모리 구조와 Metal에 최적화 |
| GGUF·양자화 비교 | llama.cpp + `llama-server` | quantization, context, GPU offload 세부 제어 가능 |
| GUI 기반 모델 비교 | LM Studio 또는 Jan | 모델 다운로드·대화·로컬 서버 구성이 편리 |
| 폐쇄망 사전 검증 | LocalAI 또는 Ollama + 내부 모델 registry | 컨테이너·모델 반입 절차 검증에 적합 |

**Mac 운영 권장:** M5 Max와 64GB 이상 메모리는 7B–32B급 모델 실험과 양자화 70B 검증에 적합합니다. 다만 다중 테넌트, 높은 동시성, 엄격한 TTFT p99를 요구하는 운영 서비스는 Linux GPU 서버로 분리하는 편이 좋습니다.

## Linux 환경

Linux는 NVIDIA CUDA, AMD ROCm, Intel SYCL, Vulkan 및 컨테이너/Kubernetes 생태계가 가장 성숙하여, **사내 Local LLM 운영의 표준 플랫폼**으로 권장됩니다.


| 도구 | NVIDIA CUDA | AMD ROCm | Intel GPU/SYCL | Vulkan | CPU-only | 운영 적합성 |
| :-- | --: | --: | --: | --: | --: | :-- |
| Ollama | 지원 | 지원 | 제한적 | 지원 | 지원 | 중간 |
| llama.cpp | 지원 | 지원 | 지원 가능 | 지원 | 지원 | 높음 |
| vLLM | 최적 | 지원 | 지원 | 제한적/구성별 상이 | 제한적 | 매우 높음 |
| LocalAI | 지원 | 지원 | 지원 | 지원 | 지원 | 높음 |
| LM Studio | 지원 | 지원 | 제한적 | 환경별 상이 | 지원 | 낮음~중간 |
| Jan | 지원 | Vulkan 중심 | 환경별 상이 | 지원 | 지원 | 중간 |
| GPT4All | 환경별 지원 | 제한적 | 제한적 | 환경별 상이 | 지원 | 낮음 |

vLLM은 NVIDIA CUDA를 주력으로 지원하며, 공식 지원 GPU에는 T4, RTX 20xx, A100, L4, H100, B200 등이 포함됩니다. AMD는 MI200/MI300/MI350 및 일부 Radeon·Ryzen AI 계열을 지원합니다.[^2_6][^2_7]

### Linux 권장 조합

| 운영 규모 | 기본 구성 | 모델 형식 | 핵심 설정 |
| :-- | :-- | :-- | :-- |
| 개발·단일 GPU | Ollama 또는 llama.cpp | GGUF | GPU offload, context 제한, 모델별 preset |
| 팀 단위 API | vLLM + FastAPI gateway + Redis | Safetensors | continuous batching, prefix cache, Prometheus |
| 대규모 사내 서비스 | vLLM + Kubernetes + KServe/Ray Serve | Safetensors, AWQ/GPTQ/FP8 | tensor parallelism, autoscaling, multi-node 분리 |
| 멀티모달 통합 | LocalAI + 선택 backend | backend별 | LLM·embedding·reranker·STT·TTS 통합 API |
| CPU/저전력 엣지 | llama.cpp | GGUF Q4/Q5 | SIMD, NUMA pinning, 적정 thread 수 |

### Linux 서버에서 vLLM을 권장하는 이유

- PagedAttention 기반 KV cache 관리로 메모리 효율을 높입니다.
- continuous batching으로 동시 요청 처리량을 높입니다.
- OpenAI 호환 API라 애플리케이션 전환 비용이 낮습니다.
- tensor parallelism으로 H100/H200 다중 GPU를 활용할 수 있습니다.
- Prometheus metric으로 TTFT를 직접 수집·알림 처리할 수 있습니다. vLLM은 `vllm:time_to_first_token_seconds` 지표를 제공합니다.[^2_8]
- Ollama보다 “모델 실행”보다 “고동시성 API 서빙”에 초점을 둔 구조입니다.

**폐쇄망 Linux 운영 추천:** Ubuntu LTS 또는 RHEL 계열 + NVIDIA driver/CUDA/container toolkit + 내부 OCI registry + 내부 PyPI wheelhouse + Hugging Face model mirror + vLLM 컨테이너 이미지 고정 조합입니다.

## Windows 환경

Windows는 데스크톱 개발자 친화성 측면에서는 좋지만, H100/H200 기반의 본격 운영 서버에는 일반적으로 Linux를 권장합니다. Windows에서 vLLM을 써야 한다면 **WSL2 Ubuntu + NVIDIA CUDA** 경로가 현실적입니다.


| 도구 | 네이티브 Windows | WSL2 권장도 | NVIDIA CUDA | AMD | Intel Arc | 권장 목적 |
| :-- | --: | --: | --: | --: | --: | :-- |
| Ollama | 지원 | 선택 | 지원 | 지원 범위 확인 필요 | Vulkan 경로 | 가장 쉬운 로컬 실행 |
| llama.cpp | 지원 | 불필요 | 지원 | HIP/Vulkan | SYCL/Vulkan | 성능·백엔드 세부 제어 |
| vLLM | 네이티브 미지원 | 강력 권장 | 지원 | Linux/WSL 경로 권장 | 구성별 | 개발·검증 |
| LM Studio | 지원 | 불필요 | 지원 | 환경별 | 지원 | GUI 및 OpenAI API |
| Jan | 지원 | 불필요 | 지원 | 지원 | 지원 | GUI 기반 모델 테스트 |
| LocalAI | Docker/WSL2 권장 | 권장 | 지원 | 지원 | 지원 | 컨테이너 기반 통합 API |
| GPT4All | 지원 | 불필요 | 환경별 | 환경별 | 환경별 | CPU 중심 오프라인 챗 |

vLLM은 Windows를 네이티브로 지원하지 않으며, Windows에서는 호환 Linux 배포판을 사용하는 WSL 환경을 권장합니다.[^2_7]

llama.cpp는 Windows에서 CPU, CUDA 12/13, Vulkan, SYCL, HIP 등 여러 사전 빌드 backend를 제공하므로, NVIDIA·AMD·Intel GPU를 폭넓게 시험하기 좋습니다.[^2_9][^2_10]

### Windows 권장 조합

| 상황 | 추천 | 비고 |
| :-- | :-- | :-- |
| 빠른 개인용 Local LLM | Ollama 또는 LM Studio | 설치 편의성과 GUI가 중요할 때 |
| NVIDIA RTX 개발 PC | llama.cpp CUDA 또는 Ollama | GGUF 모델 테스트와 GPU offload |
| AMD/Intel Arc PC | llama.cpp Vulkan/SYCL 또는 Jan | CUDA 종속성을 피해야 할 때 |
| Python·vLLM 개발 | WSL2 Ubuntu + Docker + vLLM | Linux 운영 환경과 최대한 일치 |
| 폐쇄망 Windows PC | Ollama/llama.cpp + 내부 파일 저장소 | 설치 파일, 모델, checksum 사전 반입 |

## OS별 최종 추천

| OS | 개발자 개인 환경 | 팀 API/사내 서비스 | 최우선 선택 | 피해야 할 선택 |
| :-- | :-- | :-- | :-- | :-- |
| macOS Apple Silicon | MLX-LM, Ollama, llama.cpp | 소규모 API·PoC | MLX-LM 또는 llama.cpp | vLLM을 핵심 운영 플랫폼으로 사용하는 것 |
| macOS Intel | llama.cpp, Ollama | 제한적 | llama.cpp CPU 중심 | 대형 모델·높은 동시성 기대 |
| Linux + NVIDIA | Ollama, llama.cpp, vLLM | vLLM, LocalAI | vLLM | GUI 도구만으로 운영 시스템 구성 |
| Linux + AMD | llama.cpp, Ollama, LocalAI | vLLM ROCm 또는 LocalAI | 사전 호환성 benchmark 후 vLLM | 모델별 ROCm 지원 검증 없이 표준화 |
| Windows + NVIDIA | Ollama, LM Studio, llama.cpp | WSL2 + vLLM | Ollama/LM Studio 또는 WSL2 vLLM | Native Windows vLLM 운영 |
| Windows + AMD/Intel | llama.cpp, Jan, LM Studio | WSL2 또는 Linux 전환 검토 | llama.cpp Vulkan/SYCL | CUDA 전용 운영 구조 |

## 귀하의 환경에 대한 제안

M5 Max에서 개발하고 Linux GPU 서버로 운영하는 방식이라면 다음의 3계층 구성이 가장 실용적입니다.

1. **Mac 개발 계층:** MLX-LM으로 Apple Silicon 네이티브 모델 성능을 검증하고, Ollama로 API·모델 배포 UX를 확인합니다.
2. **호환성 계층:** llama.cpp를 기준으로 GGUF 양자화(Q4_K_M, Q5_K_M, Q8_0 등)와 context length, 품질·메모리·토큰 속도를 측정합니다.
3. **운영 계층:** Linux H100/H200 서버에는 vLLM을 기본 엔진으로 배치하고, OpenAI 호환 gateway·Redis 기반 라우팅·Prometheus/Grafana를 결합합니다.
4. **통합 계층:** 텍스트 생성 외에 embedding, reranking, OCR 후처리, 음성, 멀티모달까지 하나의 폐쇄망 API 플랫폼에 묶어야 한다면 LocalAI를 검토할 가치가 있습니다. LocalAI는 llama.cpp, vLLM, MLX 등 backend를 모델별로 선택하는 구조입니다.[^2_2]

LM Studio는 macOS, Windows, Linux를 지원하며 Apple Silicon Mac, x64/ARM64 Windows, x64 Linux를 일반 지원 범위로 명시합니다. Jan은 macOS·Windows·Linux에서 동작하며, Apple Silicon에서는 Metal 가속을 자동으로 사용합니다.[^2_11][^2_12][^2_13]

<span style="display:none">[^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32][^2_33][^2_34][^2_35][^2_36][^2_37][^2_38][^2_39][^2_40][^2_41][^2_42][^2_43][^2_44][^2_45][^2_46]</span>

<div align="center">⁂</div>

[^2_1]: https://localai.io/docs/backends/index.html

[^2_2]: https://localai.io/docs/model-compatibility/

[^2_3]: https://developer.apple.com/videos/play/wwdc2026/232/

[^2_4]: https://factory.ai/open-source-wikis/llama-cpp?page=backends/index.md

[^2_5]: https://github.com/TheTom/llama-cpp-turboquant/blob/feature/turboquant-kv-cache/docs/build.md

[^2_6]: https://docs.vllm.ai/en/stable/getting_started/installation/gpu/

[^2_7]: https://docs.vllm.ai/en/v0.12.0/getting_started/installation/gpu/

[^2_8]: https://docs.vllm.ai/en/latest/design/metrics/

[^2_9]: https://gist.github.com/ilyar/b61bab36b68338ceef6c049868164ae7

[^2_10]: https://newreleases.io/project/github/ggml-org/llama.cpp/release/b8712

[^2_11]: https://beta.lmstudio.ai/docs/app

[^2_12]: https://www.jan.ai/docs/desktop/troubleshooting

[^2_13]: https://janhq-jan-19.mintlify.app/help/faq

[^2_14]: https://docs.vllm.ai/en/v0.11.1/getting_started/installation/gpu/

[^2_15]: https://docs.vllm.ai/en/v0.14.0/getting_started/installation/

[^2_16]: https://github.com/ggml-org/llama.cpp/releases/

[^2_17]: https://github.com/tc-mb/llama.cpp-omni/blob/master/README_llama.cpp.md

[^2_18]: https://www.sitepoint.com/ollama-setup-guide-2026/

[^2_19]: https://markaicode.com/compile-llama-cpp-cpu-cuda-metal/

[^2_20]: https://deepwiki.com/ollama/ollama/6-gpu-and-hardware-support

[^2_21]: https://wiki.linux-server-admin.com/web-apps/genai/vllm/setup

[^2_22]: https://eastondev.com/blog/en/posts/ai/20260425-ollama-gpu-acceleration/

[^2_23]: https://huggingface.co/AbdulElahGwaith/LocalAI/blob/0f07ba75cab0f9402be98934df5e4d582228e070/README.md

[^2_24]: https://www.promptquorum.com/power-local-llm/easiest-local-ai-app-windows-mac-linux

[^2_25]: https://deepwiki.com/mudler/LocalAI/2-installation-and-deployment

[^2_26]: https://www.aimadetools.com/blog/jan-ai-complete-guide/

[^2_27]: https://codersera.com/blog/lm-studio-complete-guide-2026/

[^2_28]: https://convly.ai/lm-studio-complete-guide-2026/

[^2_29]: https://deepwiki.com/mudler/LocalAI/2.4-gpu-acceleration-setup

[^2_30]: https://dev.to/jovan_chan_9500711396d4e6/jan-ai-review-2026-13ei

[^2_31]: https://deepwiki.com/mudler/LocalAI/4.2-backend-registry

[^2_32]: https://deepwiki.com/lmstudio-ai/docs/1.1-system-requirements-and-installation

[^2_33]: https://developer.apple.com/documentation/foundationmodels/supporting-languages-and-locales-with-foundation-models

[^2_34]: https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window

[^2_35]: https://developer.apple.com/videos/play/wwdc2026/241/

[^2_36]: https://developer.apple.com/videos/play/wwdc2026/339/

[^2_37]: https://docs.vultr.com/how-to-install-gpt4all-an-opensource-chatbot-application-for-running-large-language-models-llms

[^2_38]: https://tessl.io/registry/dpearson2699/swift-ios-skills/3.6.0/files/skills/apple-on-device-ai/references/foundation-models.md

[^2_39]: https://tessl.io/registry/dpearson2699/swift-ios-skills/3.9.0/files/skills/apple-on-device-ai/references/foundation-models.md

[^2_40]: https://github.com/ml-explore/mlx/discussions/3203

[^2_41]: https://a-git.ru/GPT_Routines/gpt4all/wiki

[^2_42]: https://www.geeksforgeeks.org/blogs/how-to-run-llms-model-locally/

[^2_43]: https://wiki.linux-server-admin.com/web-apps/genai/gpt4all

[^2_44]: https://daleelai.com/en/gpt4all-en/

[^2_45]: https://www.qwe.edu.pl/ai-tools/install-gpt4all-offline-chatgpt/

[^2_46]: https://nerdleveltech.com/apple-foundation-models-framework-claude-gemini


---

# Slang을 포함하여 비교해 주세요.

SGLang을 포함하면, Linux GPU 서버의 고성능 서빙 후보는 **vLLM과 SGLang을 함께 벤치마크**하는 것이 맞습니다. 특히 여러 요청이 동일한 system prompt, RAG 템플릿, few-shot 예시를 공유하는 에이전트 환경에서는 SGLang의 **RadixAttention 기반 prefix cache 재사용**이 큰 장점이 될 수 있습니다.[^3_1][^3_2]

## 도구별 비교

| 도구 | 핵심 목적 | 주 모델 형식 | API/서빙 | 성능 최적화 | 가장 적합한 환경 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Ollama | 간편한 로컬 모델 관리·실행 | GGUF, Ollama 패키지 | 자체 REST API, 스트리밍 | 기본 GPU offload, 모델 lifecycle 관리 | 개인 개발, PoC, 폐쇄망 모델 배포 |
| llama.cpp | 경량·이식성 높은 추론 | GGUF | `llama-server`, OpenAI 호환 API | CPU SIMD, Metal, CUDA, HIP, Vulkan, SYCL | Mac, Windows, CPU-only, 엣지 |
| vLLM | 범용 고처리량 LLM 서빙 | HF Safetensors, AWQ, GPTQ, FP8 등 | OpenAI 호환 API, metrics | PagedAttention, continuous batching, prefix cache, tensor parallelism | Linux + NVIDIA/AMD 기반 운영 서비스 |
| **SGLang** | 고성능·공유 prefix 중심 서빙 | HF Safetensors, AWQ/GPTQ/FP8/INT4 등 | OpenAI 호환 API, structured output | RadixAttention, continuous batching, prefill/decode disaggregation, speculative decoding | Linux + H100/H200/B200, agent/RAG 고동시성 |
| MLX-LM | Apple Silicon 전용 추론 | MLX 모델 | OpenAI 호환 HTTP server | Metal, unified memory 최적화 | macOS Apple Silicon |
| LocalAI | 여러 엔진을 통합하는 API 플랫폼 | backend별 상이 | OpenAI 호환 API | llama.cpp/vLLM/MLX 등 backend 선택 | 폐쇄망 통합 플랫폼 |
| LM Studio | GUI 중심 모델 실행·비교 | GGUF 등 | 로컬 OpenAI 호환 서버 | 런타임별 GPU 가속 | 개인 PC, 데모, 모델 평가 |
| Jan | 오픈소스 GUI·로컬 API | GGUF 등 | 로컬 API | Metal/CUDA/Vulkan 등 | 크로스플랫폼 개발 |
| GPT4All | 오프라인 GUI 챗 | 양자화 모델 | 로컬 서버 옵션 | CPU 중심 실행 | 개인용 오프라인 챗 |

SGLang은 RadixAttention, zero-overhead CPU scheduler, prefill-decode disaggregation, speculative decoding, continuous batching, paged attention, tensor/pipeline/expert/data parallelism, multi-LoRA batching 등을 제공하며 NVIDIA, AMD, Intel CPU/XPU, Google TPU, Ascend NPU 등으로 지원 범위를 넓히고 있습니다.[^3_1]

## macOS 비교

| 도구 | Apple Silicon | Intel Mac | 가속 backend | SGLang 대비 | 권장도 |
| :-- | --: | --: | :-- | :-- | :-- |
| MLX-LM | 매우 높음 | 미지원 | Metal, unified memory | SGLang의 대체재가 아니라 Mac 전용 최적화 런타임 | 최고 |
| llama.cpp | 매우 높음 | 높음 | Metal, CPU | 소형·GGUF에 우수, 운영형 batching 기능은 제한적 | 높음 |
| Ollama | 높음 | 지원 | Metal | 모델 관리가 쉬움, 성능 세부 튜닝은 제한적 | 높음 |
| LM Studio | 높음 | 제한적 | MLX/Metal | GUI 기반 비교·데모에 유리 | 높음 |
| Jan | 높음 | 지원 | Metal | GUI·오프라인 개발 환경 | 중간 |
| LocalAI | 가능 | 가능 | Metal/MLX/llama.cpp | Docker 기반 API 통합이 필요할 때 | 중간 |
| vLLM | 제한적 | 비권장 | 제한적/실험적 | 운영 표준으로 사용하지 않는 편이 안전 | 낮음 |
| **SGLang** | 사실상 비권장 | 비권장 | CUDA/ROCm/XPU 중심 | Apple Metal을 주력 운영 backend로 보지 말 것 | 낮음 |

**macOS 결론:** M 시리즈 Mac에서는 SGLang보다 MLX-LM, llama.cpp 또는 Ollama가 낫습니다. 특히 사용자의 M5 Max 검증 환경에서는 MLX-LM으로 native 모델 성능을 확인하고, llama.cpp로 GGUF 양자화별 품질·메모리·속도를 비교하는 구성이 실용적입니다. Apple은 MLX-LM을 사용해 로컬 추론, 양자화, fine-tuning 및 agent workflow를 구성하는 방식을 안내합니다.[^3_3]

## Linux 비교

Linux는 SGLang과 vLLM 모두 운영 가능한 주력 플랫폼입니다. GPU 서버 기반의 폐쇄망 서비스는 이 두 프레임워크를 같은 모델·같은 부하에서 비교해 선택하는 방식이 가장 안전합니다.


| 도구 | NVIDIA CUDA | AMD ROCm | Intel XPU/CPU | CPU-only | 운영 적합성 | 추천 역할 |
| :-- | --: | --: | --: | --: | --: | :-- |
| Ollama | 지원 | 지원 | 제한적 | 지원 | 중간 | 개발, QA, GGUF 배포 |
| llama.cpp | 지원 | 지원 | 지원 | 지원 | 높음 | 경량 API, 범용 HW, 엣지 |
| vLLM | 최적 | 지원 | 지원 | 제한적 | 매우 높음 | 일반 LLM API 운영 |
| **SGLang** | 최적 | 지원 | 지원 | 가능 | 매우 높음 | agent/RAG, shared prefix, structured output |
| LocalAI | 지원 | 지원 | 지원 | 지원 | 높음 | 멀티 엔진 통합 API |
| LM Studio | 지원 | 환경별 | 제한적 | 지원 | 낮음~중간 | 개발자 GUI |
| Jan | 지원 | 지원 | 환경별 | 지원 | 중간 | 개발 PC |
| GPT4All | 환경별 | 제한적 | 제한적 | 지원 | 낮음 | 개인 오프라인 챗 |

SGLang은 NVIDIA GPU뿐 아니라 AMD MI300/MI355, Intel Xeon CPU와 Intel XPU, Google TPU, Ascend NPU 등을 지원한다고 안내합니다. 단, “지원”이 곧 H100 CUDA와 동일한 성능·기능 완성도를 의미하지는 않으므로, 폐쇄망 표준은 우선 NVIDIA CUDA 또는 검증된 AMD ROCm SKU로 제한하는 것이 좋습니다.[^3_4][^3_1]

### vLLM과 SGLang 선택 기준

| 판단 항목 | vLLM 우선 | SGLang 우선 |
| :-- | :-- | :-- |
| 도입 안정성 | 운영 레퍼런스와 생태계, 관측 체계가 중요할 때 | 최신 기능의 검증 부담을 감수할 수 있을 때 |
| 트래픽 성격 | 프롬프트가 비교적 다양한 일반 채팅·API | 동일 system prompt·RAG 템플릿·few-shot을 반복하는 요청 |
| 주요 병목 | 범용 throughput, KV cache 관리, OpenAI API 호환 | 긴 공통 prefix의 prefill 비용 |
| 에이전트 workload | 요청별 context가 서로 달라 cache reuse가 낮음 | 도구 정의·정책·system prompt가 공통인 multi-agent |
| 출력 요구 | 일반 streaming text 응답 | JSON schema, regex, constrained decoding, structured output |
| 확장 방식 | tensor parallel과 일반적 서빙 풀 | prefill/decode 분리, prefix-aware scheduling, parallelism 조합 |
| 초기 운영 | 검증된 baseline을 신속히 만들고 싶을 때 | vLLM benchmark를 넘어 workload 특화 최적화를 원할 때 |

SGLang의 RadixAttention은 요청들의 공통 토큰 prefix를 radix tree의 KV cache로 보관하고 재사용합니다. 예를 들어 모든 요청에 4K-token system prompt와 2K-token RAG 정책이 반복된다면, 첫 요청의 prefill 결과를 후속 요청이 공유할 수 있습니다. 반대로 매 요청의 문서 컨텍스트가 완전히 다르면 prefix cache hit rate가 낮아져 상대적 이점도 줄어듭니다.[^3_2][^3_5]

### Linux 운영 권장

| 목적 | 추천 엔진 | 이유 |
| :-- | :-- | :-- |
| 일반 사내 챗봇·RAG API | vLLM | 범용성, 성숙도, OpenAI 호환, Prometheus 기반 관측 |
| 에이전트·도구 호출 시스템 | SGLang | 공유되는 system prompt·tool schema·few-shot prefix 재사용 |
| 구조화 JSON 추출·문서 후처리 | SGLang | constrained decoding·structured output 최적화 |
| OCR 후처리·문서 분석 | vLLM + SGLang A/B | 입력 템플릿이 반복되면 SGLang, 문서가 매번 크게 다르면 vLLM |
| GGUF 기반 경량 모델 API | llama.cpp 또는 Ollama | 낮은 운영 복잡도 |
| 다중 모달 API 통합 | LocalAI | LLM, embedding, STT/TTS backend를 하나의 API로 통합 |

## Windows 비교

| 도구 | Native Windows | WSL2 | CUDA | Vulkan | 권장도 | 주 용도 |
| :-- | --: | --: | --: | --: | --: | :-- |
| Ollama | 지원 | 선택 | 지원 | 지원 | 높음 | 빠른 로컬 실행 |
| llama.cpp | 지원 | 불필요 | 지원 | 지원 | 높음 | GPU/CPU 세부 제어 |
| LM Studio | 지원 | 불필요 | 지원 | 환경별 | 높음 | GUI 모델 비교 |
| Jan | 지원 | 불필요 | 지원 | 지원 | 중간 | 오프라인 GUI |
| LocalAI | Docker Desktop/WSL2 권장 | 권장 | 지원 | 지원 | 중간 | 통합 API |
| vLLM | 네이티브 미지원 | 권장 | 지원 | 제한적 | 중간 | Linux 배포 전 개발 |
| **SGLang** | 네이티브 운영 비권장 | 강력 권장 | WSL2 CUDA | 제한적 | 중간 | Linux와 동일한 성능 검증 |
| GPT4All | 지원 | 불필요 | 환경별 | 환경별 | 중간 | 간단한 오프라인 챗 |

vLLM은 네이티브 Windows를 지원하지 않으며 WSL의 Linux 배포판 사용을 권장합니다. SGLang 역시 CUDA 기반 운영 스택을 고려하면 Windows native보다 WSL2 Ubuntu 또는 Linux 서버가 적절합니다.[^3_6][^3_7]

## SGLang 운영 아키텍처

사용자 요구사항처럼 “짧은 질의는 즉각 반응하고, 복잡 질의도 30초 내 스트리밍 시작”을 목표로 한다면 SGLang을 독립 풀로 운영하는 구성이 좋습니다.

```text
Client
  └─ API Gateway
       ├─ Fast path: Redis cache / rule / 1B~4B model
       ├─ vLLM small pool: 일반 Q&A, 3B~14B
       ├─ SGLang agent pool: 공통 system prompt + tool schema
       ├─ SGLang extraction pool: JSON/structured output
       ├─ vLLM large pool: 32B~70B reasoning
       └─ Batch pool: embedding, reranker, OCR 후처리
```

예를 들어 금융 문서 분석 서비스에서 다음과 같이 구성할 수 있습니다.

- 공통 prefix: 보안 정책, 사기 탐지 기준, JSON Schema, 판정 설명 방식, tool 정의
- 가변 suffix: 개별 거래 내역, OCR 추출 텍스트, 이미지 분석 결과
- SGLang은 공통 prefix의 KV cache를 재활용하므로, 같은 판정 템플릿을 반복하는 요청에서 prefill GPU 비용과 TTFT를 낮출 가능성이 큽니다.
- 다만 고객별 입력 문서 원문이 지나치게 길고 공통 prefix보다 가변 컨텍스트가 압도적이면, SGLang의 cache 효과가 제한될 수 있으므로 vLLM과 실제 corpus 기반 A/B benchmark가 필요합니다.


## 귀하의 권장 스택

| 계층 | macOS M5 Max | Linux H100/H200 폐쇄망 | Windows 개발 PC |
| :-- | :-- | :-- | :-- |
| 모델 실험 | MLX-LM, Ollama, llama.cpp | Ollama, llama.cpp | Ollama, LM Studio, llama.cpp |
| GGUF 품질/성능 | llama.cpp | llama.cpp | llama.cpp |
| 범용 API 서빙 | 제한적 | vLLM | WSL2 vLLM |
| Agent·구조화 생성 | 제한적 | **SGLang** | WSL2 SGLang |
| API 통합 | LocalAI | LocalAI 또는 자체 gateway | LocalAI Docker/WSL2 |
| 관측 | 로컬 metric 확인 | Prometheus, Grafana, OpenTelemetry | 개발용 로컬 metric |

**실행 우선순위**는 다음과 같습니다.

1. Linux H100/H200에서 vLLM을 운영 baseline으로 먼저 구축합니다.
2. 동일 모델·동일 quantization·동일 GPU·동일 concurrency 조건에서 SGLang을 A/B benchmark합니다.
3. 지표는 TTFT p50/p95/p99, output token/s, request throughput, prefix-cache hit rate, KV cache 사용량, queue wait time으로 통일합니다.
4. SGLang은 공통 system prompt·RAG 템플릿·툴 정의가 큰 agent 및 문서 구조화 추출 경로에만 우선 배치합니다.
5. 실측상 SGLang의 TTFT/throughput 이득이 유의미한 모델·요청 패턴에 한해 운영 표준으로 승격합니다.

<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^3_2]: https://ai-tldr.dev/learn/local-open-models/inference-and-serving/what-is-sglang/

[^3_3]: https://developer.apple.com/videos/play/wwdc2026/232/

[^3_4]: https://sgl-project.github.io/platforms/xpu.html

[^3_5]: https://prakashkagitha.github.io/llm-stack-book/07-inference-serving/04-sglang-radixattention.html

[^3_6]: https://docs.vllm.ai/en/v0.12.0/getting_started/installation/gpu/

[^3_7]: https://inference.net/content/sglang-complete-guide/

[^3_8]: https://github.com/sgl-project/sgl-cookbook

[^3_9]: https://mcpservers.org/agent-skills/firecrawl/sglang

[^3_10]: https://yobitel.com/knowledge-base/sglang

[^3_11]: https://blog.sugiv.fyi/sglang-deep-dive-inside-sglang

[^3_12]: https://leeroopedia.com/index.php/Principle:Sgl_project_Sglang_Batch_Text_Generation

[^3_13]: https://deepwiki.com/llmInference/dyna-spec/10.3-multi-platform-support

[^3_14]: https://leeroopedia.com/index.php/Environment:Sgl_project_Sglang_Multi_Platform_Accelerators

[^3_15]: https://deepwiki.com/mingfeima/sglang/12-multi-platform-support

[^3_16]: https://deepwiki.com/mingfeima/sglang/12.4-ascend-npus-and-other-platforms

[^3_17]: https://deepwiki.com/mingfeima/sglang/12.1-nvidia-gpus-(cuda)


---

# Linux GPU 서버에서 SGLang 설치 및 실행 가이드

Linux GPU 서버에서는 SGLang을 **컨테이너 또는 Python 가상환경으로 고정 배포**하고, NVIDIA CUDA 환경에서는 먼저 단일 GPU·단일 모델 baseline을 만든 뒤 tensor parallelism과 prefix-cache 최적화를 추가하는 방식이 안전합니다. 운영 목적이라면 Ubuntu LTS/RHEL 계열 + NVIDIA GPU + Docker/NVIDIA Container Toolkit + Prometheus 조합을 권장합니다.

SGLang은 OpenAI 호환 API를 제공하며, RadixAttention 기반 prefix caching, continuous batching, prefill/decode 분리, speculative decoding 등을 지원합니다.[^4_1]

## 1. 사전 조건

### 권장 서버 기준

| 구분 | 개발/PoC | 운영 권장 | 대형 모델/고동시성 |
| :-- | --: | --: | --: |
| OS | Ubuntu 22.04/24.04 LTS | Ubuntu 24.04 LTS 또는 RHEL 9 계열 | 동일 |
| GPU | RTX 4090 24GB, L4 24GB | L40S 48GB, H100 80GB | H200 141GB, H100/H200 4–8 GPU |
| 시스템 RAM | 64GB | 256GB 이상 | 512GB–1TB |
| 로컬 NVMe | 1TB | 4TB 이상 | 8TB 이상 |
| 네트워크 | 10GbE | 25/100GbE | 100/200GbE, RDMA 검토 |
| Python | 3.10–3.12 권장 | 버전 고정 | 버전 고정 |
| 모델 저장소 | 로컬 디스크 | 내부 Hugging Face mirror/모델 registry | 공유 스토리지 또는 node-local NVMe |

운영 기준으로는 GPU와 CUDA 조합을 먼저 고정한 뒤 설치해야 합니다. SGLang은 CUDA뿐 아니라 AMD ROCm, Intel XPU/CPU 등도 지원하지만, H100/H200 기준 운영 완성도와 튜닝 정보는 CUDA 경로가 가장 풍부합니다.[^4_2][^4_1]

### GPU 상태 확인

```bash
nvidia-smi
nvidia-smi topo -m
nvidia-smi -L
```

확인 항목:

- NVIDIA Driver와 CUDA 호환성
- GPU 모델·VRAM·GPU 개수
- 다중 GPU 간 NVLink/NVSwitch 또는 PCIe 토폴로지
- 다른 프로세스의 GPU 메모리 점유 여부
- H100/H200 다중 GPU 서버라면 P2P 통신 가능 여부

```bash
nvidia-smi pmon -s mu -c 1
nvidia-smi nvlink -s
```


## 2. 권장 설치 방식

### 방법 A: Python 가상환경 설치

개발·PoC·내부 Python 서비스와의 빠른 통합에는 `venv` 또는 `uv` 기반 설치가 편합니다.

```bash
sudo apt-get update
sudo apt-get install -y \
  git curl wget build-essential \
  python3 python3-venv python3-pip \
  libnuma1 numactl

mkdir -p ~/sglang && cd ~/sglang

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install "sglang[all]"
```

설치 확인:

```bash
python -c "import sglang; print(sglang.__version__)"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
sglang --help
```

설치 후 `torch.cuda.is_available()`가 `True`여야 합니다. `False`라면 CUDA 런타임과 PyTorch wheel의 호환성, 컨테이너 GPU pass-through, `CUDA_VISIBLE_DEVICES` 설정부터 점검하십시오.

### 방법 B: Docker 컨테이너 설치

폐쇄망 또는 운영 서버에서는 컨테이너 이미지와 모델 artifact를 **검증된 내부 registry**로 반입하여 배포하는 방식을 권장합니다.

```bash
sudo apt-get update
sudo apt-get install -y docker.io

sudo systemctl enable --now docker
docker --version
```

NVIDIA Container Toolkit이 준비된 뒤 GPU 인식 여부를 확인합니다.

```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

이 명령이 GPU 정보를 보여야 합니다. 이후에는 SGLang의 검증된 버전 이미지를 내부 registry에 mirror하고, digest를 고정해 사용하십시오.

```bash
export SGLANG_IMAGE="<내부-registry>/ai/sglang:<검증된-태그>"
export MODEL_DIR="/srv/models/Qwen3-8B"

docker run --rm --gpus all \
  --ipc=host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -p 30000:30000 \
  -v "${MODEL_DIR}:/models/Qwen3-8B:ro" \
  "${SGLANG_IMAGE}" \
  python3 -m sglang.launch_server \
    --model-path /models/Qwen3-8B \
    --host 0.0.0.0 \
    --port 30000
```

모델별 custom code가 필요한 경우에만 `--trust-remote-code`를 추가하십시오. 폐쇄망 환경에서는 모델 코드를 정적 분석·서명 검증 없이 신뢰하지 않는 것이 좋습니다.

## 3. 첫 서버 실행

### 단일 GPU: 7B–14B 모델

첫 검증은 7B 또는 8B급 instruct 모델로 시작하십시오.

```bash
export CUDA_VISIBLE_DEVICES=0
export TOKENIZERS_PARALLELISM=false

python3 -m sglang.launch_server \
  --model-path /srv/models/Qwen3-8B-Instruct \
  --host 0.0.0.0 \
  --port 30000 \
  --mem-fraction-static 0.80 \
  --context-length 8192 \
  --max-running-requests 32
```

파라미터 의미:


| 옵션 | 의미 | 초기 권장값 |
| :-- | :-- | :-- |
| `--model-path` | HF 형식 모델의 로컬 절대경로 | `/srv/models/<model>` |
| `--host` | 바인딩 IP | 내부 API면 `0.0.0.0`, 개발은 `127.0.0.1` |
| `--port` | 서버 포트 | `30000` 등 고정 포트 |
| `--mem-fraction-static` | GPU VRAM 중 모델·KV cache용 정적 예약 비율 | 0.75–0.90부터 시작 |
| `--context-length` | 허용 최대 문맥 길이 | 8K부터 실제 요구에 맞춰 증가 |
| `--max-running-requests` | 동시에 실행할 요청 수 상한 | 16–32부터 부하시험으로 조정 |
| `--tp` 또는 `--tensor-parallel-size` | Tensor Parallel GPU 수 | 단일 GPU는 1, 4 GPU면 4 |
| `--trust-remote-code` | 모델의 커스텀 Python 코드 허용 | 필요할 때만 활성화 |

공식 예시에서도 `--model-path`, `--host`, `--reasoning-parser`, `--mem-fraction-static`, `--context-length`, `--max-running-requests`, `--tensor-parallel-size` 조합으로 서버를 시작합니다.[^4_3]

### API 상태 확인

```bash
curl -s http://127.0.0.1:30000/v1/models | jq
```

Chat Completions 요청:

```bash
curl -N http://127.0.0.1:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/srv/models/Qwen3-8B-Instruct",
    "messages": [
      {
        "role": "system",
        "content": "You are a concise enterprise assistant."
      },
      {
        "role": "user",
        "content": "SGLang을 한 문장으로 설명해줘."
      }
    ],
    "temperature": 0.2,
    "max_tokens": 200,
    "stream": true
  }'
```

Python OpenAI SDK 예시입니다.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:30000/v1",
    api_key="local-not-used",
)

stream = client.chat.completions.create(
    model="/srv/models/Qwen3-8B-Instruct",
    messages=[
        {"role": "system", "content": "You are a concise enterprise assistant."},
        {"role": "user", "content": "SGLang의 장점을 세 가지 알려줘."},
    ],
    temperature=0.2,
    max_tokens=300,
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[^4_0].delta.content
    if delta:
        print(delta, end="", flush=True)
```


## 4. 다중 GPU 실행

### 70B급: 4× H100 또는 H200

70B BF16 모델은 모델 weight만 대략 140GB 이상이 필요하므로, KV cache와 런타임 workspace까지 고려하면 단일 141GB H200에도 여유가 부족할 수 있습니다. 운영에서는 2–4 GPU tensor parallelism을 기준으로 시작하는 편이 안전합니다.

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
export TOKENIZERS_PARALLELISM=false

python3 -m sglang.launch_server \
  --model-path /srv/models/Qwen-70B-Instruct \
  --host 0.0.0.0 \
  --port 30000 \
  --tp 4 \
  --mem-fraction-static 0.88 \
  --context-length 16384 \
  --max-running-requests 64 \
  --enable-p2p-check
```

SGLang의 예시에는 2/4/8 GPU tensor parallel 실행을 위해 `--tp 2`, `--tp 4`, `--tp 8`을 사용하는 명령이 제시됩니다.[^4_4]

### MoE 모델: H200 8 GPU 예시

MoE 모델은 전체 weight, 활성 expert, expert routing, KV cache 및 통신량을 함께 고려해야 합니다. 모델별 공식 cookbook과 권장 parser를 우선 적용하십시오.

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

sglang serve \
  --model-path /srv/models/<moe-model> \
  --tp 8 \
  --host 0.0.0.0 \
  --port 30000 \
  --mem-fraction-static 0.90 \
  --context-length 32768 \
  --max-running-requests 32 \
  --enable-p2p-check
```

예를 들어 Kimi K2.5 모델 가이드는 H200 단일 노드 8 GPU에서 `--tp 8`, `--trust-remote-code`, 모델별 tool-call/reasoning parser를 사용하는 방식을 제시합니다.[^4_5]

## 5. 성능 튜닝

### TTFT 목표별 초기값

| 목표 | 권장 설정 | 이유 |
| :-- | :-- | :-- |
| 짧은 Q\&A의 낮은 TTFT | context 4K–8K, small model pool, request 16–32 | 긴 prefill과 queue wait를 제한 |
| 일반 RAG | context 8K–16K, request 32–64 | 문서 근거와 동시성의 균형 |
| 긴 문서 분석 | context 32K 이상, 별도 long-context pool | 긴 prefill이 일반 Q\&A를 방해하지 않게 분리 |
| agent/tool 호출 | 공통 system prompt 유지, SGLang prefix cache 활용 | RadixAttention cache hit을 높임 |
| batch extraction | request 수 증가, 별도 GPU 풀 | interactive 요청과 격리 |

### 권장 운영 파라미터

```bash
python3 -m sglang.launch_server \
  --model-path /srv/models/Qwen3-32B-Instruct \
  --host 0.0.0.0 \
  --port 30000 \
  --tp 2 \
  --mem-fraction-static 0.85 \
  --context-length 16384 \
  --max-running-requests 48 \
  --chunked-prefill-size 8192 \
  --enable-p2p-check
```

튜닝 원칙:

- `--context-length`는 모델의 최대 지원치가 아니라 **업무상 필요한 최대치**로 제한합니다.
- `--max-running-requests`를 무작정 높이면 throughput은 증가할 수 있지만 queueing, KV cache pressure, TTFT p95/p99가 나빠질 수 있습니다.
- `--mem-fraction-static`은 너무 낮으면 KV cache가 부족하고, 너무 높으면 CUDA graph/workspace 등 런타임 여유가 줄어 OOM이 발생할 수 있습니다.
- 70B와 8B를 한 서버·한 큐에서 같이 운영하지 마십시오. small/medium/large 모델 풀을 분리해야 짧은 요청의 TTFT를 지킬 수 있습니다.
- RAG 또는 agent 서비스에서는 system prompt·tool schema·few-shot 예시의 순서와 내용을 안정적으로 유지해 prefix cache hit을 높입니다.

SGLang의 RadixAttention은 공통 prefix의 KV cache를 재사용하도록 설계되어, 동일한 system prompt 또는 반복되는 agent template이 많은 워크로드에 유리합니다.[^4_6][^4_1]

## 6. systemd 운영 예시

운영 서버에서는 `tmux`나 수동 shell 실행 대신 systemd를 사용하십시오.

`/etc/systemd/system/sglang-qwen.service`:

```ini
[Unit]
Description=SGLang Qwen Inference Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=llm
Group=llm
WorkingDirectory=/opt/sglang
Environment="CUDA_VISIBLE_DEVICES=0,1"
Environment="TOKENIZERS_PARALLELISM=false"
Environment="HF_HUB_OFFLINE=1"
Environment="TRANSFORMERS_OFFLINE=1"
Environment="PATH=/opt/sglang/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=/opt/sglang/.venv/bin/python -m sglang.launch_server \
  --model-path /srv/models/Qwen3-32B-Instruct \
  --host 127.0.0.1 \
  --port 30000 \
  --tp 2 \
  --mem-fraction-static 0.85 \
  --context-length 16384 \
  --max-running-requests 48 \
  --enable-p2p-check
Restart=always
RestartSec=10
LimitNOFILE=1048576
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
```

활성화·로그 확인:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sglang-qwen.service

sudo systemctl status sglang-qwen.service
journalctl -u sglang-qwen.service -f
```

외부 노출은 SGLang이 아닌 내부 reverse proxy/API gateway에 맡기고, SGLang 프로세스는 `127.0.0.1`에만 바인딩하는 방식을 권장합니다.

## 7. 폐쇄망 준비

에어갭 환경에서는 인터넷이 되는 staging 구간에서 다음 artifact를 검증한 뒤 반입해야 합니다.


| 반입 항목 | 관리 원칙 |
| :-- | :-- |
| SGLang wheel/컨테이너 | 버전·SHA256·SBOM 고정 |
| Python 의존성 wheelhouse | `pip download`로 전량 확보 후 hash 검증 |
| NVIDIA driver/CUDA/container toolkit | OS·GPU·PyTorch와 호환 매트릭스 문서화 |
| 모델 파일 | commit hash, SHA256, 라이선스, 출처 기록 |
| tokenizer/config/generation config | 모델 weight와 함께 반입 |
| 모델 custom code | `trust_remote_code` 전에 코드 리뷰·악성 행위 검토 |
| OS 패키지 | 내부 apt/yum mirror 또는 오프라인 repository |
| 컨테이너 이미지 | 내부 Harbor/Artifactory registry와 digest pinning |
| 운영 설정 | Git 기반 IaC, 승인된 parameter profile 사용 |

폐쇄망에서는 아래 환경 변수를 지정하면 실수로 외부 Hugging Face Hub 접속을 시도하는 일을 줄일 수 있습니다.

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/srv/hf-cache
export HF_HUB_CACHE=/srv/hf-cache/hub
```


## 8. 장애 점검

| 증상 | 우선 점검 | 조치 |
| :-- | :-- | :-- |
| GPU를 찾지 못함 | `nvidia-smi`, `torch.cuda.is_available()` | driver/CUDA/PyTorch 및 Docker GPU runtime 점검 |
| 기동 즉시 OOM | 모델 정밀도, context, static memory, 다른 프로세스 | context·동시 요청 축소, TP 증가, GPU 점유 해제 |
| 다중 GPU 시작 실패 | `nvidia-smi topo -m`, P2P/NCCL | `--enable-p2p-check`, NCCL 로그 활성화, NVLink/PCIe 토폴로지 점검 |
| TTFT p95가 높음 | queue time, prompt 길이, cache hit | short/long pool 분리, context 상한 축소, concurrency 조정 |
| output 속도가 낮음 | GPU utilization, TP 통신, quantization | GPU별 역할 분리, NVLink 확인, 모델/quantization benchmark |
| JSON 파싱 실패 | schema, tokenizer, decoding 설정 | SGLang structured output/grammar 기능과 모델별 parser 적용 |
| 외부 접속 시도 | 모델 path 및 HF 환경 변수 | `HF_HUB_OFFLINE=1`, 모델·tokenizer 전량 로컬화 |

## 권장 도입 순서

1. 8B instruct 모델을 단일 GPU에서 구동해 API·streaming·TTFT baseline을 수집합니다.
2. 같은 모델·GPU에서 vLLM과 SGLang을 비교합니다.
3. 공통 system prompt, tool schema, RAG template이 반복되는 실제 요청 세트로 prefix-cache 효과를 검증합니다.
4. 32B/70B 모델에서 2·4·8 GPU의 `--tp`별 TTFT, output token/s, GPU 메모리, P2P 통신을 측정합니다.
5. 모델 크기와 workload에 따라 small·general·agent·long-context 풀을 분리합니다.
6. systemd 또는 Kubernetes로 서비스화하고, gateway·인증·rate limit·Prometheus/Grafana를 붙입니다.
7. 폐쇄망 반입 pipeline과 artifact hash 검증을 CI/CD에 포함합니다.

<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^4_2]: https://sgl-project.github.io/platforms/xpu.html

[^4_3]: https://github.com/NVIDIA-NeMo/ProRL-Agent-Server/blob/stable/examples/calculator/README.md

[^4_4]: https://github.com/sgl-project/sglang/issues/10306

[^4_5]: https://github.com/MoonshotAI/Kimi-K2.5/blob/master/docs/deploy_guidance.md

[^4_6]: https://ai-tldr.dev/learn/local-open-models/inference-and-serving/what-is-sglang/

[^4_7]: https://github.com/sgl-project/sgl-project.github.io

[^4_8]: https://github.com/sgl-project/mini-sglang/blob/main/README.md

[^4_9]: https://docs.sglang.ai/\_sources/advanced_features/structured_outputs_for_reasoning_models.ipynb

[^4_10]: https://github.com/sgl-project/sglang?tab=readme-ov-file

[^4_11]: https://github.com/sgl-project/sgl-docs

[^4_12]: https://github.com/sgl-project/sglang/blob/main/benchmark/hicache/README.md

[^4_13]: https://github.com/sgl-project/sglang?ref=runpod.ghost.io

[^4_14]: https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/mem_cache/storage/mooncake_store/README.md

[^4_15]: https://github.com/sgl-project/sglang-jax

[^4_16]: https://docs.sglang.ai/SpecForge/get_started/install.html

[^4_17]: https://github.com/sgl-project/sglang/issues/15443

[^4_18]: https://github.com/sgl-project/sglang-omni


---

# Linux GPU 서버용 SGLang 구축: 모델별 최적화 설정, 파서 구성, 환경 의존성 해결을 위한 원클릭 설치 및 검증 스크립트 만들기

SGLang 다중 GPU Tensor Parallelism 설정 방법
SGLang과 vLLM 성능 및 메모리 사용량 비교

아래는 Linux NVIDIA GPU 서버에서 SGLang을 일관되게 구축·검증하고, 모델별 실행 프로파일·파서·Tensor Parallelism·vLLM 비교 벤치마크까지 자동화하는 실무형 구성입니다. 핵심은 **한 모델당 하나의 YAML 프로파일**, 공통 bootstrap 스크립트, 동일 부하를 사용하는 SGLang/vLLM benchmark로 분리하는 것입니다.

SGLang은 reasoning output 분리용 `--reasoning-parser`, tool calling용 `--tool-call-parser`, 그리고 multi-GPU용 `--tp`를 제공합니다. 예를 들어 Qwen3 reasoning 모델은 `--reasoning-parser qwen3`, tool 사용 시 `--tool-call-parser qwen25`, 대형 모델은 `--tp 8` 구성을 사용합니다.[^5_1][^5_2]

## 권장 프로젝트 구조

```text
local-llm-serving/
├── install/
│   └── install_sglang_stack.sh
├── profiles/
│   ├── qwen3-8b-instruct.env
│   ├── qwen3-32b-instruct-tp2.env
│   ├── qwen3-235b-thinking-tp8.env
│   ├── deepseek-r1-distill-qwen-32b-tp2.env
│   └── llama-3-70b-instruct-tp4.env
├── scripts/
│   ├── start_sglang.sh
│   ├── start_vllm.sh
│   ├── smoke_test.py
│   ├── benchmark_openai.py
│   ├── gpu_snapshot.sh
│   └── compare_results.py
├── artifacts/
│   ├── models/
│   ├── wheels/
│   ├── logs/
│   └── benchmarks/
└── requirements/
    └── requirements-lock.txt
```

운영 서버에서는 `/opt/local-llm-serving`에 code와 설정을, `/srv/models`에 모델을, `/var/log/local-llm`에 로그를 두는 식으로 분리하는 것이 좋습니다.

## 1. 원클릭 설치 스크립트

다음 스크립트는 Ubuntu 22.04/24.04, NVIDIA GPU, 온라인 또는 내부 PyPI mirror 환경을 전제로 합니다. 폐쇄망에서는 `WHEELHOUSE`에 wheel을 미리 반입하고 `PIP_NO_INDEX=1`로 실행합니다.

`install/install_sglang_stack.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-/opt/local-llm-serving/.venv}"
INSTALL_DIR="${INSTALL_DIR:-/opt/local-llm-serving}"
WHEELHOUSE="${WHEELHOUSE:-}"
SGLANG_SPEC="${SGLANG_SPEC:-sglang[all]}"
VLLM_SPEC="${VLLM_SPEC:-vllm}"
INSTALL_VLLM="${INSTALL_VLLM:-1}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Required command not found: $1" >&2
    exit 1
  }
}

echo "==> Checking host"
require_cmd "${PYTHON_BIN}"
require_cmd nvidia-smi

nvidia-smi
"${PYTHON_BIN}" --version

echo "==> Installing OS dependencies"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential \
  ca-certificates \
  curl \
  git \
  jq \
  libnuma1 \
  numactl \
  python3-venv \
  python3-pip

echo "==> Creating virtual environment"
sudo mkdir -p "${INSTALL_DIR}"
sudo chown -R "${USER}:${USER}" "${INSTALL_DIR}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip setuptools wheel

PIP_ARGS=()
if [[ -n "${WHEELHOUSE}" ]]; then
  PIP_ARGS+=(--no-index --find-links "${WHEELHOUSE}")
fi

echo "==> Installing PyTorch and SGLang"
python -m pip install "${PIP_ARGS[@]}" torch
python -m pip install "${PIP_ARGS[@]}" "${SGLANG_SPEC}"

if [[ "${INSTALL_VLLM}" == "1" ]]; then
  echo "==> Installing vLLM"
  python -m pip install "${PIP_ARGS[@]}" "${VLLM_SPEC}"
fi

echo "==> Validating Python/CUDA/SGLang"
python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA is unavailable in PyTorch"
print("torch:", torch.__version__)
print("cuda:", torch.version.cuda)
print("gpu_count:", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(f"gpu[{i}]: {torch.cuda.get_device_name(i)}")
import sglang
print("sglang:", getattr(sglang, "__version__", "installed"))
try:
    import vllm
    print("vllm:", getattr(vllm, "__version__", "installed"))
except ImportError:
    print("vllm: not installed")
PY

echo "==> Completed"
echo "Activate with: source ${VENV_DIR}/bin/activate"
```

실행 예시:

```bash
chmod +x install/install_sglang_stack.sh

sudo mkdir -p /srv/models /var/log/local-llm
sudo chown -R "$USER:$USER" /srv/models /var/log/local-llm

./install/install_sglang_stack.sh
```


### 폐쇄망 wheelhouse 반입

인터넷 가능 staging 서버에서 GPU/OS/Python 버전을 운영 환경과 맞춘 뒤 준비합니다.

```bash
mkdir -p wheels

python3 -m pip download \
  --dest wheels \
  "sglang[all]" \
  vllm \
  torch
```

운영 폐쇄망 서버에서는 다음처럼 실행합니다.

```bash
export WHEELHOUSE=/mnt/airgap/wheels
export PIP_NO_INDEX=1

./install/install_sglang_stack.sh
```

단, PyTorch·SGLang·vLLM wheel은 Python 버전, CUDA 버전, GPU 아키텍처에 따라 호환성이 달라질 수 있습니다. 따라서 검증 완료된 artifact의 SHA-256, 라이선스, SBOM, 모델 commit hash를 함께 반입해야 합니다.

## 2. 모델별 실행 프로파일

환경 변수 파일은 shell에서 바로 읽을 수 있는 `.env` 형식을 추천합니다. 모델마다 context, VRAM 예약, TP, parser를 분리하면 잘못된 설정을 다른 모델에 적용하는 사고를 줄일 수 있습니다.

### Qwen3 8B Instruct: 단일 GPU

`profiles/qwen3-8b-instruct.env`:

```bash
MODEL_ID="Qwen/Qwen3-8B"
MODEL_PATH="/srv/models/Qwen3-8B"
SERVED_MODEL_NAME="qwen3-8b"

HOST="127.0.0.1"
PORT="30000"

CUDA_VISIBLE_DEVICES="0"
TP_SIZE="1"

DTYPE="bfloat16"
CONTEXT_LENGTH="8192"
MEM_FRACTION_STATIC="0.82"
MAX_RUNNING_REQUESTS="32"
CHUNKED_PREFILL_SIZE="4096"

REASONING_PARSER=""
TOOL_CALL_PARSER="qwen25"
TRUST_REMOTE_CODE="0"
```

권장 대상:

- 24GB~48GB GPU에서 일반 Q\&A·요약
- 짧은 RAG 응답
- API/streaming 기능 검증
- low-latency 소형 모델 풀


### Qwen3 32B Instruct: 2 GPU TP

`profiles/qwen3-32b-instruct-tp2.env`:

```bash
MODEL_ID="Qwen/Qwen3-32B"
MODEL_PATH="/srv/models/Qwen3-32B"
SERVED_MODEL_NAME="qwen3-32b"

HOST="127.0.0.1"
PORT="30000"

CUDA_VISIBLE_DEVICES="0,1"
TP_SIZE="2"

DTYPE="bfloat16"
CONTEXT_LENGTH="16384"
MEM_FRACTION_STATIC="0.85"
MAX_RUNNING_REQUESTS="48"
CHUNKED_PREFILL_SIZE="8192"

REASONING_PARSER=""
TOOL_CALL_PARSER="qwen25"
TRUST_REMOTE_CODE="0"
```

권장 대상:

- H100 80GB 2장 또는 H200 141GB 2장
- 사내 RAG, 문서 분석, 코드·업무 assistant
- 8K~16K 입력과 중간 규모 동시성


### Qwen3 Thinking: reasoning + tool parser

`profiles/qwen3-235b-thinking-tp8.env`:

```bash
MODEL_ID="Qwen/Qwen3-235B-A22B-Thinking-2507"
MODEL_PATH="/srv/models/Qwen3-235B-A22B-Thinking-2507"
SERVED_MODEL_NAME="qwen3-235b-thinking"

HOST="127.0.0.1"
PORT="30000"

CUDA_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"
TP_SIZE="8"

DTYPE="bfloat16"
CONTEXT_LENGTH="32768"
MEM_FRACTION_STATIC="0.88"
MAX_RUNNING_REQUESTS="24"
CHUNKED_PREFILL_SIZE="8192"

REASONING_PARSER="qwen3"
TOOL_CALL_PARSER="qwen25"
TRUST_REMOTE_CODE="0"
```

Qwen3의 공식 SGLang 예시는 `--reasoning-parser qwen3`, tool calling 시 `--tool-call-parser qwen25`, 대형 모델에서 `--tp 8` 구성을 사용합니다.[^5_2]

### DeepSeek-R1 Distill Qwen: reasoning parser

`profiles/deepseek-r1-distill-qwen-32b-tp2.env`:

```bash
MODEL_ID="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
MODEL_PATH="/srv/models/DeepSeek-R1-Distill-Qwen-32B"
SERVED_MODEL_NAME="deepseek-r1-32b"

HOST="127.0.0.1"
PORT="30000"

CUDA_VISIBLE_DEVICES="0,1"
TP_SIZE="2"

DTYPE="bfloat16"
CONTEXT_LENGTH="16384"
MEM_FRACTION_STATIC="0.85"
MAX_RUNNING_REQUESTS="24"
CHUNKED_PREFILL_SIZE="8192"

REASONING_PARSER="deepseek-r1"
TOOL_CALL_PARSER=""
TRUST_REMOTE_CODE="0"
```

DeepSeek-R1 Distill-Qwen 계열은 SGLang에서 `--reasoning-parser deepseek-r1`를 지정해 reasoning과 최종 답변 content를 분리할 수 있습니다.[^5_1]

### Llama 70B Instruct: 4 GPU TP

`profiles/llama-3-70b-instruct-tp4.env`:

```bash
MODEL_ID="meta-llama/Llama-3.3-70B-Instruct"
MODEL_PATH="/srv/models/Llama-3.3-70B-Instruct"
SERVED_MODEL_NAME="llama-70b"

HOST="127.0.0.1"
PORT="30000"

CUDA_VISIBLE_DEVICES="0,1,2,3"
TP_SIZE="4"

DTYPE="bfloat16"
CONTEXT_LENGTH="16384"
MEM_FRACTION_STATIC="0.88"
MAX_RUNNING_REQUESTS="32"
CHUNKED_PREFILL_SIZE="8192"

REASONING_PARSER=""
TOOL_CALL_PARSER=""
TRUST_REMOTE_CODE="0"
```


## 3. SGLang 원클릭 실행·검증

`scripts/start_sglang.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

PROFILE="${1:?Usage: $0 profiles/<model>.env}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[^5_0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-/opt/local-llm-serving/.venv}"
LOG_DIR="${LOG_DIR:-/var/log/local-llm}"

source "${PROFILE}"
source "${VENV_DIR}/bin/activate"

mkdir -p "${LOG_DIR}"

export CUDA_VISIBLE_DEVICES
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

[[ -d "${MODEL_PATH}" ]] || {
  echo "[ERROR] Missing model directory: ${MODEL_PATH}" >&2
  exit 1
}

nvidia-smi -L
nvidia-smi topo -m || true

ARGS=(
  --model-path "${MODEL_PATH}"
  --host "${HOST}"
  --port "${PORT}"
  --tp "${TP_SIZE}"
  --dtype "${DTYPE}"
  --context-length "${CONTEXT_LENGTH}"
  --mem-fraction-static "${MEM_FRACTION_STATIC}"
  --max-running-requests "${MAX_RUNNING_REQUESTS}"
  --chunked-prefill-size "${CHUNKED_PREFILL_SIZE}"
  --served-model-name "${SERVED_MODEL_NAME}"
)

if [[ -n "${REASONING_PARSER}" ]]; then
  ARGS+=(--reasoning-parser "${REASONING_PARSER}")
fi

if [[ -n "${TOOL_CALL_PARSER}" ]]; then
  ARGS+=(--tool-call-parser "${TOOL_CALL_PARSER}")
fi

if [[ "${TRUST_REMOTE_CODE}" == "1" ]]; then
  ARGS+=(--trust-remote-code)
fi

echo "[INFO] SGLang server starts: ${SERVED_MODEL_NAME}"
echo "[INFO] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}, TP=${TP_SIZE}"

exec python -m sglang.launch_server "${ARGS[@]}" \
  2>&1 | tee -a "${LOG_DIR}/${SERVED_MODEL_NAME}.log"
```

`scripts/smoke_test.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
import time
from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:30000/v1")
parser.add_argument("--model", required=True)
parser.add_argument("--timeout", type=float, default=90)
args = parser.parse_args()

client = OpenAI(base_url=args.base_url, api_key="local")

started = time.perf_counter()
first_token_at = None
text = ""

try:
    stream = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Say hello in Korean in one short sentence."},
        ],
        temperature=0,
        max_tokens=64,
        stream=True,
        timeout=args.timeout,
    )

    for chunk in stream:
        delta = chunk.choices[^5_0].delta.content or ""
        if delta and first_token_at is None:
            first_token_at = time.perf_counter()
        text += delta

except Exception as exc:
    print(f"FAIL: {exc}", file=sys.stderr)
    raise SystemExit(1)

ended = time.perf_counter()
assert text.strip(), "Empty model response"

ttft_ms = (first_token_at - started) * 1000 if first_token_at else None
e2e_ms = (ended - started) * 1000

print({
    "status": "ok",
    "ttft_ms": round(ttft_ms, 2) if ttft_ms else None,
    "e2e_ms": round(e2e_ms, 2),
    "response": text.strip(),
})
```

실행 순서:

```bash
chmod +x scripts/start_sglang.sh scripts/smoke_test.py

scripts/start_sglang.sh profiles/qwen3-32b-instruct-tp2.env

python scripts/smoke_test.py \
  --base-url http://127.0.0.1:30000/v1 \
  --model qwen3-32b
```


## 4. 다중 GPU Tensor Parallelism

Tensor Parallelism은 모델의 layer 내부 weight를 여러 GPU에 분할합니다. 즉, `TP=4`면 4개 GPU가 하나의 모델 요청을 공동 처리합니다. 모델 weight가 분산되므로 GPU당 남는 VRAM이 늘어 KV cache를 더 확보할 수 있지만, 각 token 생성 단계에서 GPU 간 통신이 발생합니다.

vLLM도 Tensor Parallelism에서 모델 파라미터를 여러 GPU의 각 layer에 걸쳐 분할한다고 설명합니다. TP를 늘리면 GPU당 더 많은 KV cache 공간을 확보할 수 있으나, 통신 비용이 발생합니다.[^5_3]

### TP 선택 표

| 모델급 | 정밀도 | 최소 권장 | 실무 시작값 | 비고 |
| :-- | :-- | --: | --: | :-- |
| 7B–14B | BF16 | TP 1 | TP 1 | H100/H200 한 장이면 충분한 경우가 많음 |
| 32B | BF16 | TP 1–2 | TP 2 | 동시성·긴 context를 위해 TP 2 권장 |
| 70B | BF16 | TP 2 | TP 4 | 4× H100 또는 2–4× H200부터 benchmark |
| 70B | INT4/AWQ | TP 1–2 | TP 2 | 단일 H200도 가능할 수 있으나 KV cache 여유 검증 필요 |
| 100B–250B MoE | BF16/FP8 | TP 4–8 | TP 8 | NVLink/NVSwitch, NCCL 필수 검증 |
| 400B+ MoE | FP8/INT4 | TP 8 이상 | TP 8 + EP/DP 검토 | 모델별 공식 recipe를 우선 적용 |

### TP 실행 명령

4 GPU:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3

python -m sglang.launch_server \
  --model-path /srv/models/Llama-3.3-70B-Instruct \
  --tp 4 \
  --host 127.0.0.1 \
  --port 30000 \
  --mem-fraction-static 0.88 \
  --context-length 16384 \
  --max-running-requests 32 \
  --enable-p2p-check
```

8 GPU:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

python -m sglang.launch_server \
  --model-path /srv/models/Qwen3-235B-A22B-Thinking-2507 \
  --tp 8 \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen25 \
  --host 127.0.0.1 \
  --port 30000 \
  --mem-fraction-static 0.88 \
  --context-length 32768 \
  --max-running-requests 24 \
  --enable-p2p-check
```


### NCCL·P2P 의존성 점검

```bash
nvidia-smi topo -m
nvidia-smi nvlink -s

export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,GRAPH
export NCCL_P2P_DISABLE=0
```

검증 원칙:

- `TP_SIZE`는 반드시 노출 GPU 수와 일치시킵니다.
- H100/H200 다중 GPU의 경우 NVLink/NVSwitch 연결을 우선 사용합니다.
- PCIe-only 구성도 동작하지만 decode 단계의 all-reduce 통신으로 token/s와 tail latency가 저하될 수 있습니다.
- 서로 다른 GPU SKU·VRAM을 한 TP 그룹에 섞지 마십시오.
- MIG는 TP와 운영 복잡성이 높아질 수 있으므로 low-latency production path에서는 초기 구성에서 피하는 편이 안전합니다.
- 다중 노드 TP는 InfiniBand/RDMA, NCCL, 노드 간 latency, 장애 복구까지 포함한 별도 설계가 필요합니다.


## 5. 파서 구성 원칙

SGLang의 parser는 “모델이 출력한 특수 토큰/태그”를 reasoning, content, tool call로 해석하는 계층입니다. parser 이름을 임의로 설정하면 안 되며, 해당 모델의 공식 SGLang recipe 또는 지원 목록을 확인해야 합니다.


| 모델 패턴 | Reasoning parser | Tool parser | 사용 시점 |
| :-- | :-- | :-- | :-- |
| 일반 Instruct | 미지정 | 미지정 또는 모델별 parser | 일반 chat/RAG |
| Qwen3 Thinking | `qwen3` | `qwen25` | thinking 분리, function calling |
| DeepSeek-R1 Distill | `deepseek-r1` | 모델별 지원 여부 확인 | `<think>`와 최종 응답 분리 |
| Kimi 계열 | 모델 공식 문서 기준 | 예: `kimi_k2` | reasoning/tool tag 형식 반영 |
| 커스텀 fine-tune | custom parser 필요 가능 | custom parser 필요 가능 | 특수 tag·JSON 문법 사용 |

SGLang의 reasoning parser는 `--reasoning-parser`로 설정하고, DeepSeek-R1 Distill-Qwen-7B에는 `deepseek-r1` parser를 쓰는 공식 예시가 있습니다. Tool parser는 모델이 반환한 function name과 arguments를 구조화해 전달하며, 지원되지 않는 모델 태그에는 parser 확장이 필요할 수 있습니다.[^5_4][^5_1]

## 6. SGLang과 vLLM 공정 비교

두 엔진의 성능 비교에서 가장 많이 발생하는 오류는 **모델, 정밀도, context, 요청 분포, prefix cache 상태, concurrency가 다른 경우**입니다. 반드시 모두 맞춰야 합니다.

### 비교 규칙

| 항목 | 반드시 통일할 값 |
| :-- | :-- |
| 모델 | 같은 Hugging Face revision, 동일 tokenizer |
| 정밀도 | BF16/FP8/AWQ/GPTQ 중 동일 하나 |
| GPU | 같은 GPU, 동일 GPU 수, 동일 TP |
| context | 동일 input token 수와 max context |
| 출력 길이 | 동일 max tokens 및 EOS 처리 기준 |
| 동시성 | 1, 4, 16, 32, 64, 128 등 같은 단계 |
| 요청 도착률 | closed-loop 또는 고정 request rate 중 하나로 통일 |
| warm-up | 최소 3–5분 또는 충분한 요청 수 |
| prefix cache | 둘 다 off 또는 둘 다 warm-cache 상태로 시험 |
| 부하 데이터 | 실제 RAG/agent 로그를 익명화한 동일 JSONL |

vLLM benchmark에서 synthetic dataset을 사용할 경우 일관된 측정을 위해 prefix caching을 비활성화하라고 권장합니다. 또한 vLLM은 prefix repetition dataset을 사용해 공통 prefix 길이, prefix 수, prefix당 요청 수를 직접 제어할 수 있습니다.[^5_5][^5_6]

### SGLang 서버 실행

```bash
python -m sglang.launch_server \
  --model-path /srv/models/Qwen3-32B \
  --tp 2 \
  --host 127.0.0.1 \
  --port 30000 \
  --mem-fraction-static 0.85 \
  --context-length 16384 \
  --max-running-requests 48
```


### vLLM 서버 실행

```bash
vllm serve /srv/models/Qwen3-32B \
  --served-model-name qwen3-32b \
  --tensor-parallel-size 2 \
  --host 127.0.0.1 \
  --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 16384 \
  --max-num-seqs 48 \
  --no-enable-prefix-caching
```

vLLM은 `--gpu-memory-utilization`으로 GPU 메모리 사용 비율을 제어하며, 기본값은 0.9입니다. `--tensor-parallel-size`와 prefix caching enable/disable 옵션을 제공합니다.[^5_7][^5_8]

### 공통 benchmark runner

`scripts/benchmark_openai.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", required=True)
parser.add_argument("--model", required=True)
parser.add_argument("--engine", required=True, choices=["sglang", "vllm"])
parser.add_argument("--concurrency", type=int, default=16)
parser.add_argument("--requests", type=int, default=100)
parser.add_argument("--input-text", default="Explain tensor parallelism in two concise paragraphs.")
parser.add_argument("--max-tokens", type=int, default=256)
parser.add_argument("--output", required=True)
args = parser.parse_args()

async def one_request(client, sem, idx):
    async with sem:
        payload = {
            "model": args.model,
            "messages": [
                {"role": "system", "content": "You are a concise enterprise assistant."},
                {"role": "user", "content": args.input_text},
            ],
            "temperature": 0,
            "max_tokens": args.max_tokens,
            "stream": True,
        }

        started = time.perf_counter()
        first_token = None
        chunks = []
        try:
            async with client.stream(
                "POST",
                f"{args.base_url.rstrip('/')}/chat/completions",
                json=payload,
                timeout=300,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    delta = event["choices"][^5_0].get("delta", {}).get("content") or ""
                    if delta and first_token is None:
                        first_token = time.perf_counter()
                    chunks.append(delta)
        except Exception as exc:
            return {"id": idx, "error": repr(exc)}

        ended = time.perf_counter()
        text = "".join(chunks)
        return {
            "id": idx,
            "ttft_ms": round((first_token - started) * 1000, 2) if first_token else None,
            "e2e_ms": round((ended - started) * 1000, 2),
            "output_chars": len(text),
            "error": None,
        }

def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)

async def main():
    sem = asyncio.Semaphore(args.concurrency)
    limits = httpx.Limits(max_connections=args.concurrency * 2)
    async with httpx.AsyncClient(limits=limits) as client:
        started = time.perf_counter()
        rows = await asyncio.gather(*[
            one_request(client, sem, i) for i in range(args.requests)
        ])
        elapsed = time.perf_counter() - started

    ok = [x for x in rows if not x["error"]]
    ttfts = [x["ttft_ms"] for x in ok if x["ttft_ms"] is not None]
    e2es = [x["e2e_ms"] for x in ok]

    result = {
        "engine": args.engine,
        "model": args.model,
        "concurrency": args.concurrency,
        "requests": args.requests,
        "success": len(ok),
        "failed": len(rows) - len(ok),
        "elapsed_s": round(elapsed, 3),
        "request_throughput_rps": round(len(ok) / elapsed, 3),
        "ttft_ms_p50": round(percentile(ttfts, 0.50), 2) if ttfts else None,
        "ttft_ms_p95": round(percentile(ttfts, 0.95), 2) if ttfts else None,
        "ttft_ms_p99": round(percentile(ttfts, 0.99), 2) if ttfts else None,
        "e2e_ms_p50": round(percentile(e2es, 0.50), 2) if e2es else None,
        "e2e_ms_p95": round(percentile(e2es, 0.95), 2) if e2es else None,
        "rows": rows,
    }

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))

asyncio.run(main())
```

실행 예시:

```bash
# SGLang
python scripts/benchmark_openai.py \
  --engine sglang \
  --base-url http://127.0.0.1:30000/v1 \
  --model qwen3-32b \
  --concurrency 32 \
  --requests 300 \
  --output artifacts/benchmarks/sglang-c32.json

# vLLM
python scripts/benchmark_openai.py \
  --engine vllm \
  --base-url http://127.0.0.1:8000/v1 \
  --model qwen3-32b \
  --concurrency 32 \
  --requests 300 \
  --output artifacts/benchmarks/vllm-c32.json
```


### 메모리 스냅샷

`scripts/gpu_snapshot.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

OUT="${1:-artifacts/benchmarks/gpu-$(date +%Y%m%d-%H%M%S).csv}"
mkdir -p "$(dirname "${OUT}")"

nvidia-smi \
  --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,power.draw,temperature.gpu \
  --format=csv,noheader,nounits \
  > "${OUT}"

cat "${OUT}"
```

부하시험 중 1초 간격으로 수집하려면 다음처럼 사용합니다.

```bash
while true; do
  scripts/gpu_snapshot.sh "artifacts/benchmarks/sglang-gpu-$(date +%s).csv"
  sleep 1
done
```


### 비교해야 할 지표

| 영역 | 측정값 | 해석 |
| :-- | :-- | :-- |
| 최초 응답 | TTFT p50/p95/p99 | interactive UX와 SLO의 핵심 |
| 생성 성능 | output token/s, inter-token latency | 응답이 끊기지 않는 정도 |
| 전체 처리량 | request/s, token/s | GPU 자원당 수용량 |
| 대기 | queue wait time | overload와 scheduler 한계 |
| GPU 메모리 | allocated/reserved VRAM, KV cache 사용량 | 동시성·context 상한 결정 |
| GPU 활용 | compute·memory utilization, power | 병목이 compute인지 memory인지 판단 |
| Cache | prefix cache hit/reuse ratio | SGLang Radix cache 효과 검증 |
| 안정성 | OOM, timeout, error rate, restart | 운영 가능성 판단 |

vLLM은 GPU cache에 사용할 메모리 비율을 조정할 수 있고, 증가시키면 KV cache 용량을 늘릴 수 있습니다. 반대로 `max_num_seqs` 또는 context 길이를 줄여 OOM을 피할 수 있습니다. SGLang도 `--mem-fraction-static`을 통해 모델과 KV cache가 사용할 GPU 메모리 비율을 관리하며, SGLang 예시에서는 TP 8 및 0.85 수준의 메모리 fraction을 사용합니다.[^5_9][^5_10]

## 7. 권장 비교 시나리오

| 시나리오 | 입력/출력 | Prefix 상태 | 동시성 | 목적 |
| :-- | --: | :-- | --: | :-- |
| 짧은 Q\&A | 128 / 128 tokens | off | 1, 4, 16, 64 | baseline TTFT |
| 일반 RAG | 2K / 512 tokens | off | 4, 16, 32, 64 | 일반 업무 질의 |
| 긴 문서 | 16K / 1K tokens | off | 1, 4, 16 | long-prefill 처리 |
| Agent 공통 정책 | 4K shared + 1K variable / 512 | warm cache | 16, 64, 128 | SGLang Radix cache 가치 |
| JSON 추출 | 4K / 256 tokens | warm/off 각각 | 16, 64 | parser·structured generation 안정성 |
| Burst | 1K / 512 tokens | off | 0→128 급증 | queue, TTFT p99, OOM |

공통 prefix scenario는 SGLang이 유리할 가능성이 높은지 검증하는 시험입니다. RadixAttention은 공유 prefix를 radix tree 기반 KV cache에 보관해 재사용하도록 설계되어 있기 때문입니다. 반면 synthetic benchmark에서는 두 엔진의 cache 상태를 맞추거나 모두 끈 상태에서 baseline을 얻어야 공정합니다.[^5_6][^5_11][^5_12][^5_5]

## 운영 적용 결론

- **SGLang 기본 배치:** Qwen3 Thinking, DeepSeek-R1 계열, tool calling, structured output, 공통 system prompt가 긴 agent/RAG.
- **vLLM 기본 배치:** 일반 chat/RAG, 다수 모델의 표준 OpenAI API 서빙, 팀에서 이미 vLLM 관측·운영 체계를 보유한 경우.
- **TP 기본값:** 32B는 TP 2, 70B는 TP 4, 200B+ MoE는 TP 8부터 시작하고 실측으로 축소·확대합니다.
- **메모리 설정:** `SGLang --mem-fraction-static 0.82~0.88`, `vLLM --gpu-memory-utilization 0.82~0.88`에서 시작해 GPU별 KV cache, TTFT p95, OOM 발생 여부로 조정합니다.
- **운영 배포:** 하나의 GPU 풀에 8B·32B·70B·long-context 트래픽을 함께 넣지 말고, 모델 크기와 latency 목표별로 별도 deployment와 queue를 구성합니다.
- **폐쇄망:** 모델·wheel·컨테이너·CUDA driver·parser 설정·model revision을 하나의 승인된 release bundle으로 취급하십시오.

<span style="display:none">[^5_13][^5_14][^5_15][^5_16][^5_17][^5_18][^5_19][^5_20]</span>

<div align="center">⁂</div>

[^5_1]: https://docs.sglang.ai/advanced_features/separate_reasoning.html

[^5_2]: https://docs.sglang.ai/basic_usage/qwen3.html

[^5_3]: https://docs.vllm.ai/en/v0.10.2/configuration/optimization.html

[^5_4]: https://docs.sglang.ai/advanced_features/tool_parser.html

[^5_5]: https://docs.vllm.ai/en/stable/cli/bench/throughput/

[^5_6]: https://docs.vllm.ai/projects/recipes/en/stable/OpenAI/GPT-OSS.html

[^5_7]: https://docs.vllm.ai/en/v0.14.0/cli/bench/throughput/

[^5_8]: https://docs.vllm.ai/en/latest/cli/bench/throughput/

[^5_9]: https://docs.vllm.ai/en/v0.26.0/configuration/optimization/

[^5_10]: https://docs.sglang.ai/SpecForge/basic_usage/data_preparation.html

[^5_11]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^5_12]: https://ai-tldr.dev/learn/local-open-models/inference-and-serving/what-is-sglang/

[^5_13]: https://docs.vllm.ai/projects/recipes/en/stable/GLM/GLM.html

[^5_14]: https://docs.vllm.ai/en/v0.20.0/cli/bench/throughput/

[^5_15]: https://docs.vllm.ai/en/latest/cli/bench/latency/

[^5_16]: https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/ucm_deployment.html

[^5_17]: https://docs.vllm.ai/en/stable/cli/bench/latency/

[^5_18]: https://docs.vllm.ai/projects/recipes/en/latest/GLM/GLM.html

[^5_19]: https://docs.sglang.ai/SpecForge/get_started/install.html

[^5_20]: https://docs.sglang.ai/\_sources/advanced_features/structured_outputs_for_reasoning_models.ipynb


---

# SGLang vLLM 벤치마크 결과 비교 분석 가이드

SGLang 툴 콜 파서 및 리조닝 파서 실전 설정 사례
다중 GPU 환경에서 Tensor Parallelism 성능 튜닝 팁

SGLang과 vLLM의 비교는 “어느 엔진이 더 빠른가”보다 **어떤 요청 분포에서 TTFT·처리량·VRAM 효율이 더 좋은가**를 판정하는 방식으로 해야 합니다. 특히 공통 system prompt·툴 schema·few-shot이 반복되는 agent/RAG에서는 SGLang, 일반적인 다중 사용자 chat/RAG API에서는 vLLM이 각각 유리할 수 있으므로 실제 트래픽에 가까운 부하로 측정해야 합니다.[^6_1][^6_2]

## 1. 벤치마크 결과 해석

### 반드시 통일할 조건

| 항목 | SGLang·vLLM 공통 기준 |
| :-- | :-- |
| 모델 | 동일 Hugging Face revision, 동일 tokenizer |
| 정밀도 | BF16, FP8, AWQ, GPTQ 등 완전히 동일 |
| GPU | 동일 SKU, GPU 수, driver, CUDA, NCCL |
| 병렬화 | 동일 Tensor Parallel 크기 |
| context | 동일 maximum context 및 동일 입력 token 분포 |
| 출력 | 동일 `max_tokens`, temperature, EOS 정책 |
| 동시성 | 1, 4, 16, 32, 64, 128 등 같은 단계 |
| 부하 모델 | closed-loop 또는 일정 request rate 중 하나로 통일 |
| warm-up | 최소 수십~수백 요청 또는 3–5분 이상 |
| cache | cold-cache와 warm-cache를 별도 시험 |
| 데이터셋 | 같은 JSONL, 같은 RAG·agent prompt, 같은 랜덤 시드 |

vLLM benchmark는 TTFT, end-to-end latency, throughput을 제공하며 TTFT를 “요청 전송부터 첫 streamed token 수신까지”로 정의합니다. 합성 데이터 benchmark에서는 prefix cache 영향을 통제하려면 시작 직후 첫 benchmark를 사용하거나 prefix caching을 명시적으로 비활성화해야 합니다.[^6_2][^6_3][^6_4]

### 핵심 지표별 판정

| 지표 | 낮을수록/높을수록 | 의미 | 이상 징후 |
| :-- | :-- | :-- | :-- |
| TTFT p50 | 낮을수록 좋음 | 평상시 첫 응답성 | 모델 prefill 또는 기본 scheduler 병목 |
| TTFT p95/p99 | 낮을수록 좋음 | 사용자 체감·SLO 핵심 | queueing, KV cache 부족, burst 취약 |
| ITL | 낮을수록 좋음 | 스트리밍의 매끄러움 | decode 통신, GPU memory bandwidth 병목 |
| Output token/s | 높을수록 좋음 | 생성 성능 | TP 통신 과다, 낮은 GPU utilization |
| Request/s | 높을수록 좋음 | 전체 요청 처리량 | 긴 요청이 short 요청을 점유 |
| E2E p95 | 낮을수록 좋음 | 완료까지의 시간 | 출력 길이·scheduler·queue 영향 |
| GPU VRAM | 목적에 맞게 안정적 | KV cache 여유 | 95% 이상 고정, OOM, cache eviction |
| GPU utilization | 높은데 안정적일수록 좋음 | GPU 활용도 | 낮으면 CPU/network, 100%+ TTFT 상승은 과부하 |
| Prefix cache hit rate | 높을수록 좋음 | 공통 prefix 재사용 | prompt template 변화, cache eviction |
| Error/timeout rate | 낮을수록 좋음 | 운영 안정성 | OOM, NCCL, parser, overload 문제 |

vLLM은 TTFT histogram과 prefix cache hit counter를 제공하므로, 애플리케이션 클라이언트 측정치와 Prometheus 지표를 함께 봐야 합니다.[^6_5][^6_6]

### 결과 패턴별 분석

| 관측 결과 | 가능성 높은 원인 | 권장 대응 |
| :-- | :-- | :-- |
| SGLang warm-cache TTFT가 크게 낮음 | 공통 prefix가 길고 Radix cache reuse가 높음 | agent/RAG 경로를 SGLang으로 분리 |
| SGLang과 vLLM cold-cache가 유사 | 공통 prefix 재사용이 거의 없음 | 운영 성숙도·관측·모델 호환성을 기준으로 선택 |
| vLLM throughput이 더 높음 | 범용 continuous batching 및 모델별 kernel 최적화 효과 | 일반 chat/RAG pool을 vLLM으로 유지 |
| SGLang structured output 성공률이 높음 | parser·constrained decoding·모델 template 적합 | 추출·tool call 경로에 SGLang 우선 적용 |
| TP 증가 후 token/s 하락 | GPU 간 all-reduce/NCCL 통신 비용 | TP를 낮추거나 NVLink/NVSwitch GPU로 변경 |
| TTFT p50은 낮지만 p99가 높음 | queue burst, context mix, KV eviction | short/long pool 분리, admission control 적용 |
| VRAM은 여유인데 GPU 활용률이 낮음 | CPU tokenization, API parsing, network, 작은 batch | CPU core pinning, batch/concurrency 증가, profiling |
| VRAM이 거의 가득 차고 timeout 증가 | context/concurrency 과다, KV cache pressure | max context·동시성 축소, TP 확대, 모델 양자화 |

### 권장 보고서 형식

동일한 엔진에서 concurrency만 변경한 결과가 아니라, 다음 4개 workload를 함께 표시해야 의사결정이 가능합니다.


| Workload | 입력/출력 | Cache | 목적 |
| :-- | --: | :-- | :-- |
| Short chat | 128 / 128 tokens | cold | 최저 TTFT |
| General RAG | 2K / 512 tokens | cold | 일반 업무성 응답 |
| Long document | 16K / 1K tokens | cold | prefill·KV cache 한계 |
| Agent/RAG template | 4K shared + 1K variable / 512 | warm | prefix reuse 가치 |

예를 들어, 4K-token 공통 system prompt와 도구 정의를 모든 요청이 공유하고 요청별 문서만 1K token씩 추가된다면, SGLang의 RadixAttention은 공통 prefix의 KV cache 재사용으로 TTFT를 크게 줄일 가능성이 있습니다. 반대로 각 요청의 문서와 prompt가 전부 고유하면 cache reuse가 작아 SGLang의 이점도 제한적입니다.[^6_1]

## 2. Tool·Reasoning parser 사례

parser는 모델 출력의 특수 tag를 reasoning, 일반 응답, function call로 해석해 OpenAI 호환 응답 구조로 반환합니다. 이는 “프롬프트만으로 JSON을 요구”하는 방식보다 streaming 및 tool orchestration에 안정적입니다.

### Reasoning parser

| 모델군 | 권장 parser | 목적 | 주의점 |
| :-- | :-- | :-- | :-- |
| DeepSeek-R1 / R1 Distill | `deepseek-r1` | `<think>` 계열 reasoning과 final content 분리 | 모델 세부 revision별 template 확인 |
| Qwen3 일반 계열 | `qwen3` | `enable_thinking`이 반영된 reasoning 처리 | chat template과 parser 일치 필요 |
| Qwen3 Thinking | `qwen3` 또는 `qwen3-thinking` | 항상 reasoning하는 모델의 think/final 분리 | reasoning token이 길어 TTFT/E2E 영향 |
| Kimi reasoning 계열 | 모델 cookbook의 parser | 모델별 special token 파싱 | 임의 parser 사용 금지 |
| 일반 instruct | 생략 | reasoning tag가 없으면 불필요 | parser를 억지로 켜지 않음 |

SGLang은 DeepSeek-R1의 명시적 thinking block과 Qwen3 family의 `enable_thinking` 처리 등을 위한 reasoning parser를 제공합니다. Qwen3 Thinking 모델은 `qwen3` 또는 `qwen3-thinking` parser를 사용할 수 있습니다.[^6_7]

#### 사례 A: Qwen3 Tool Calling + Reasoning

```bash
python -m sglang.launch_server \
  --model-path /srv/models/Qwen3-32B \
  --served-model-name qwen3-32b \
  --host 127.0.0.1 \
  --port 30000 \
  --tp 2 \
  --context-length 16384 \
  --mem-fraction-static 0.85 \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen25
```

이 조합은 다음과 같은 경우에 맞습니다.

- 업무 assistant가 reasoning을 내부 필드로 분리해야 하는 경우
- function calling으로 내부 검색·DB 조회·문서 retrieval을 호출하는 경우
- 사용자 UI에는 최종 답변만 보이고, 감사 로그에는 reasoning 분리 여부·tool argument·tool result를 저장해야 하는 경우

Qwen3는 reasoning parser로 `qwen3`, tool-call parser로 `qwen25` 조합을 사용할 수 있습니다.[^6_8]

#### 사례 B: DeepSeek-R1 Distill 추론 서비스

```bash
python -m sglang.launch_server \
  --model-path /srv/models/DeepSeek-R1-Distill-Qwen-32B \
  --served-model-name deepseek-r1-32b \
  --host 127.0.0.1 \
  --port 30000 \
  --tp 2 \
  --context-length 16384 \
  --mem-fraction-static 0.85 \
  --max-running-requests 24 \
  --reasoning-parser deepseek-r1
```

DeepSeek-R1은 revision에 따라 `<think>` 시작 tag 없이 thinking content부터 생성하거나 시작·종료 tag를 모두 생성할 수 있습니다. `deepseek-r1` parser는 두 형태를 처리하도록 설계되어 있습니다.[^6_7]

### Tool parser 실전 흐름

```text
Client request + tools schema
  └─ SGLang
       ├─ 모델 생성
       ├─ tool-call parser가 특수 출력 tag를 해석
       ├─ tool name / JSON arguments를 streaming event로 전달
       └─ Orchestrator가 내부 도구 호출
            └─ tool result를 모델에 반환
                 └─ 최종 답변 생성
```

도구 호출은 반드시 **모델 출력값을 신뢰하지 않는 입력**으로 취급하십시오.

- tool name은 허용 목록(allowlist)으로 검증합니다.
- JSON Schema/Pydantic으로 argument type·범위·필수 필드를 검증합니다.
- 테넌트/사용자 권한을 tool executor에서 재검증합니다.
- 금전 이동, 파일 삭제, 외부 전송 등 side effect 도구는 사용자 확인 단계를 둡니다.
- reasoning 내용은 민감 정보·내부 프롬프트가 포함될 수 있으므로 사용자 응답에 그대로 노출하지 않습니다.

SGLang의 Model Gateway는 reasoning과 function call parsing을 위한 관리 endpoint를 제공하며, 스트리밍 중 partial token을 처리하면서 reasoning block을 일반 텍스트와 분리합니다.[^6_9]

## 3. Tensor Parallelism 튜닝

TP는 모델 weight를 GPU 여러 장에 분산하므로 단일 GPU에 맞지 않는 모델을 올리거나 GPU당 KV cache 공간을 늘리는 데 필요합니다. 하지만 decode 단계마다 GPU 간 통신이 발생하므로, “가능한 가장 큰 TP”가 항상 최고 성능은 아닙니다.

vLLM은 TP가 model parameter를 GPU 간에 분할하고 GPU별 KV cache 공간을 늘리지만, TP를 높이면 통신 비용도 발생한다고 설명합니다.[^6_10]

### TP 설정 기준

| 모델 | GPU | 권장 시작 TP | 튜닝 방향 |
| :-- | :-- | --: | :-- |
| 7B–14B BF16 | H100/H200 | 1 | TP보다 data parallel replica를 우선 고려 |
| 32B BF16 | H100 80GB | 2 | 1과 2를 비교, context·concurrency가 크면 TP 2 |
| 32B BF16 | H200 141GB | 1–2 | 단일 GPU throughput과 replica 구성을 우선 검토 |
| 70B BF16 | H100 80GB | 4 | TP 2/4/8을 비교, NVLink 여부 확인 |
| 70B BF16 | H200 141GB | 2–4 | 2부터 검증, KV cache 목표에 따라 확대 |
| 200B+ MoE | H100/H200 8 GPU | 8 | 모델 공식 recipe와 expert parallel 옵션 검토 |
| 8B–32B 다중 사용자 | 4–8 GPU | TP 1 replica 다수 | 짧은 Q\&A에서는 replica가 TTFT에 유리 |

### 튜닝 순서

1. **단일 GPU baseline**을 먼저 확보합니다. 모델이 단일 GPU에 들어갈 경우 TP 1의 token/s와 TTFT를 기준으로 삼습니다.
2. `TP=2`, `TP=4`, `TP=8`을 같은 모델·동일 concurrency에서 비교합니다. VRAM 여유, p95 TTFT, output token/s, GPU별 utilization의 변화를 기록합니다.
3. `nvidia-smi topo -m`으로 GPU 간 NVLink/NVSwitch 또는 PCIe 연결을 확인합니다. 4~8 GPU TP에서는 NVLink/NVSwitch가 매우 중요합니다.
4. GPU가 충분하다면 큰 TP 하나보다 **여러 작은 replica**가 short chat에 유리한지 비교합니다. 예: H100 8장으로 32B 모델을 TP2×4 replica로 두면 TP8 한 개보다 동시 사용자와 장애 격리에 유리할 수 있습니다.
5. 긴 context/긴 prefill과 짧은 chat을 한 deployment에서 섞지 마십시오. long-context workload는 KV cache와 scheduler를 점유해 short request의 p99 TTFT를 악화시킵니다.

### TP 토폴로지 예시

| 인프라 | 모델/업무 | 권장 배치 | 이유 |
| :-- | :-- | :-- | :-- |
| 4× H100 NVLink | 70B BF16 | TP4 × 1 | 모델 수용과 통신 균형 |
| 8× H100 NVSwitch | 70B 일반 chat | TP2 × 4 replicas | 동시성·HA·짧은 TTFT |
| 8× H200 NVSwitch | 235B MoE reasoning | TP8 × 1 | 모델 메모리와 expert 통신 |
| 8× H200 NVSwitch | 32B RAG | TP1 × 8 replicas | 높은 동시성, low TTFT |
| 2× H200 PCIe | 70B BF16 | TP2 × 1 | 최소 운영 구성 |
| 4× L40S PCIe | 32B AWQ | TP1/2 benchmark | PCIe 통신 비용을 최소화 |

### 환경 변수와 점검

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,GRAPH
export NCCL_P2P_DISABLE=0
export TOKENIZERS_PARALLELISM=false

nvidia-smi topo -m
nvidia-smi nvlink -s
```

SGLang 서버 기동 예시:

```bash
python -m sglang.launch_server \
  --model-path /srv/models/Llama-3.3-70B-Instruct \
  --tp 4 \
  --host 127.0.0.1 \
  --port 30000 \
  --context-length 16384 \
  --mem-fraction-static 0.88 \
  --max-running-requests 32 \
  --enable-p2p-check
```


### 흔한 문제와 해결

| 문제 | 원인 | 해결 |
| :-- | :-- | :-- |
| TP 4가 TP 2보다 느림 | PCIe 통신·NCCL all-reduce 비용 | TP 축소, NVLink 구성, replica 수 증가 |
| GPU별 VRAM 사용량 불균형 | 모델 architecture, KV cache, 프로세스 잔존 | 프로세스 정리, 모델별 공식 recipe 확인 |
| 시작 시 NCCL hang | P2P/IB/NCCL driver 문제 | topology 확인, NCCL debug 로그, firmware/driver 정합성 검증 |
| 높은 TTFT p99 | queueing, long request 혼입 | short/long pool 분리, admission control |
| OOM | KV cache 과다, context·동시성 과대 | context/max running requests 축소, memory fraction 조정 |
| GPU 1장만 100% | 잘못된 `CUDA_VISIBLE_DEVICES`, TP 값 불일치 | 노출 GPU 수와 `--tp` 일치 확인 |
| 낮은 GPU utilization | 작은 batch, CPU tokenizer 병목 | concurrency 증가, CPU core·NUMA affinity 점검 |

## 4. 실무 의사결정

초기 운영은 다음 순서가 가장 안전합니다.

- **일반 사내 Q\&A/RAG:** vLLM을 baseline으로 운영하고, 8B·32B 모델은 TP를 최소화하거나 replica를 늘립니다.
- **Agent·tool calling·공통 프롬프트가 긴 요청:** SGLang을 별도 pool로 두고 warm-cache TTFT와 prefix reuse를 측정합니다.
- **Reasoning 모델:** parser를 명시하고, reasoning token을 사용자의 완료 응답 지연과 분리해서 측정합니다.
- **70B 이상:** NVLink/NVSwitch 환경에서 TP 2/4/8을 실측하고, decode token/s보다 p95/p99 TTFT와 안정성까지 함께 판단합니다.
- **최종 선정:** cold/warm cache, short/RAG/long-context/agent의 네 가지 workload 결과를 가중 평균하여, 모델별·업무별로 엔진을 분리합니다.

<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18][^6_19][^6_20][^6_21]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^6_2]: https://docs.vllm.ai/en/latest/benchmarking/cli/

[^6_3]: https://docs.vllm.ai/projects/recipes/en/stable/OpenAI/GPT-OSS.html

[^6_4]: https://docs.vllm.ai/projects/recipes/en/latest/Ernie/Ernie4.5-VL.html

[^6_5]: https://docs.vllm.ai/en/v0.27.0/design/metrics/

[^6_6]: https://docs.vllm.ai/en/v0.16.0/design/metrics/

[^6_7]: https://docs.sglang.ai/\_sources/advanced_features/separate_reasoning.ipynb

[^6_8]: https://docs.sglang.ai/basic_usage/qwen3.html

[^6_9]: https://docs.sglang.ai/advanced_features/sgl_model_gateway.html

[^6_10]: https://docs.vllm.ai/en/v0.10.2/configuration/optimization.html

[^6_11]: https://docs.vllm.ai/projects/ascend/en/v0.21.0rc/tutorials/features/long_sequence_context_parallel_multi_node.html

[^6_12]: https://docs.vllm.ai/en/v0.26.0/configuration/optimization/

[^6_13]: https://docs.vllm.ai/en/latest/design/metrics/

[^6_14]: https://docs.vllm.ai/en/stable/design/metrics/

[^6_15]: https://docs.vllm.ai/en/v0.14.1/design/metrics/

[^6_16]: https://docs.vllm.ai/en/stable/cli/bench/throughput/

[^6_17]: https://docs.sglang.ai/advanced_features/separate_reasoning.html

[^6_18]: https://docs.sglang.ai/advanced_features/tool_parser.html

[^6_19]: https://docs.sglang.ai/SpecForge/basic_usage/data_preparation.html

[^6_20]: https://docs.sglang.ai/\_sources/advanced_features/structured_outputs_for_reasoning_models.ipynb

[^6_21]: https://docs.sglang.ai/SpecForge/get_started/install.html


---

# vLLM SGLang KV cache 관리 방식 차이점 비교

SGLang RadixAttention과 vLLM Prefix Caching 비교
LLM 서빙 엔진별 OOM 대응 전략

vLLM과 SGLang 모두 KV cache를 GPU 메모리의 block 단위로 관리해 단편화를 줄이지만, **vLLM은 범용 PagedAttention + hash 기반 Automatic Prefix Caching(APC)** 에, **SGLang은 radix-tree 기반 RadixAttention + cache-aware scheduling**에 더 초점을 둡니다. 따라서 공통 prefix가 길고 반복되는 agent/RAG·멀티턴 환경에서는 SGLang의 cache 재사용 이점을 검증할 가치가 크고, 일반 chat/RAG API의 안정적 운영에는 vLLM이 강한 baseline입니다.[^7_1][^7_2]

## KV cache 관리 방식

### 공통점

두 엔진 모두 모델 weight 외 GPU VRAM을 KV cache에 배정하고, active request의 과거 token K/V를 저장해 autoregressive decode 시 재계산을 피합니다.

- 요청마다 context가 길어질수록 KV cache 사용량이 증가합니다.
- 동시 요청 수가 많아질수록 KV cache가 빠르게 소진됩니다.
- context length, 모델 layer 수, hidden size, KV head 수, dtype가 KV cache 용량에 직접 영향을 줍니다.
- KV cache는 “모델이 GPU에 올라가는가”와 별개로, 실제 운영 동시성과 long-context 수용량을 결정합니다.
- cache가 부족하면 새 요청이 대기하거나, cache eviction, preemption, OOM, TTFT p95/p99 악화로 나타납니다.


### vLLM: PagedAttention 중심

vLLM은 KV cache를 고정 크기 block으로 나누어 필요할 때 물리 GPU block을 논리 token block에 매핑합니다. 이 방식은 운영체제의 virtual memory paging과 유사하게, 연속된 큰 GPU 메모리를 요청마다 직접 확보하지 않아 fragmentation을 줄입니다.


| 항목 | vLLM |
| :-- | :-- |
| 기본 KV cache 방식 | PagedAttention 기반 block 관리 |
| block allocation | 요청 진행에 맞춰 GPU block 동적 할당 |
| 목적 | 높은 batching 효율, 메모리 단편화 완화, 높은 동시성 |
| prefix 재사용 | APC(Automatic Prefix Caching) |
| prefix 식별 | token block hash 기반 |
| 공유 단위 | 일치하는 완전 token block |
| eviction | 재사용 가능 block을 관리하며 필요시 cache 공간 회수 |
| 메모리 제한 | `--gpu-memory-utilization` |
| 관측 | KV cache usage, preemption, prefix cache hit 등 |

vLLM의 APC는 중복되는 prompt prefill 계산을 피하기 위해 KV cache block을 재사용하는 최적화입니다. GPU 사용 비율은 `--gpu-memory-utilization`으로 설정하며 최신 설정 문서의 기본값은 0.92입니다. 이 값은 **해당 vLLM 인스턴스별** 상한이므로 같은 GPU에서 여러 인스턴스를 띄우면 각 인스턴스의 총합을 보수적으로 잡아야 합니다.[^7_3][^7_4][^7_1]

### SGLang: RadixAttention 중심

SGLang도 paged KV cache block을 기반으로 GPU 메모리를 관리하지만, cache를 radix tree로 색인하여 요청 간 공통 prefix를 적극 재사용합니다. 개념적으로는 같은 시스템 프롬프트·tool schema·few-shot·대화 이력이 여러 요청에 중복될 때, 그 prefix의 KV를 하나만 계산하고 트리의 공통 경로로 공유합니다.


| 항목 | SGLang |
| :-- | :-- |
| 기본 KV cache 방식 | Paged KV pool + RadixAttention cache |
| prefix 인덱스 | radix tree / compressed trie |
| 핵심 목적 | 공유 prefix를 높은 비율로 재사용 |
| 요청 배치 | cache locality를 고려한 scheduling |
| 공유 방식 | 같은 prefix 경로의 KV block 공유 |
| eviction | 사용 중인 경로를 보호하면서 오래된 cache부터 회수 |
| 메모리 제한 | `--mem-fraction-static` |
| 확장 | HiCache, prefill/decode disaggregation 등 |

SGLang은 RadixAttention, continuous batching, prefill-decode disaggregation, speculative decoding을 제공하며, 공통 prefix를 radix tree로 관리하는 것이 핵심 차별점입니다. 단, 구현상 실제 KV memory allocation은 여전히 block 단위입니다. “SGLang은 token 단위, vLLM은 block 단위”라고 단순화하는 설명은 정확하지 않습니다. 두 시스템 모두 GPU 메모리 효율을 위해 block을 사용하며, 차이는 주로 **prefix를 어떻게 찾아 공유하고 요청을 스케줄하는가**에 있습니다.[^7_2][^7_5]

## RadixAttention vs Prefix Caching

| 비교 항목 | SGLang RadixAttention | vLLM APC |
| :-- | :-- | :-- |
| 주된 설계 목표 | 공유 prefix를 적극적으로 재사용하는 serving | 범용 block KV cache와 자동 prefix reuse |
| 인덱스 구조 | radix tree / trie | token block hash 기반 lookup |
| cache 공유 | 트리의 공통 prefix path | hash가 일치하는 완전 KV block |
| 다중턴 대화 | 대화 이력이 prefix chain으로 자연스럽게 누적 | 재사용 가능하나 block hash match가 필요 |
| RAG 공통 템플릿 | system prompt·tool 정의·few-shot이 반복되면 강점 | 동일 block prefix면 재사용 가능 |
| partial overlap | 트리 구조로 다양한 prefix 관계를 표현 | block 경계까지의 일치가 중요 |
| scheduler | cache locality를 고려한 요청 배치에 강점 | 범용 continuous batching 중심 |
| cache 효과가 작은 경우 | 요청 prompt가 모두 고유한 경우 | 요청 prompt가 모두 고유한 경우 |
| 운영 판단 | agent, shared template, multi-turn 중심 | 범용 chat/RAG API baseline |

vLLM의 APC는 고정 token block hash를 기반으로 prefix KV를 재사용합니다. SGLang RadixAttention은 radix tree로 요청 prefix 간 관계를 표현해 공통 path를 재사용합니다.[^7_5][^7_6][^7_1]

### 실제 예시

다음 요청이 있다고 가정합니다.

```text
[공통 3,000 tokens]
- 시스템 보안 정책
- 금융 문서 사기 탐지 규칙
- JSON Schema
- 도구 정의 12개
- few-shot 예시

[가변 1,000 tokens]
- 고객별 OCR 텍스트
- 거래 내역
- 사용자 질문
```

- **첫 요청:** 공통 3,000 tokens와 가변 1,000 tokens를 모두 prefill합니다.
- **후속 요청:** 공통 3,000 tokens가 동일하면 해당 KV를 재사용하고, 가변 1,000 tokens 중심으로 추가 prefill합니다.
- 공통 부분이 길고 요청 수가 많을수록 prefill GPU 시간·TTFT·비용 절감 가능성이 커집니다.
- 이 workload에서는 SGLang의 RadixAttention을 warm-cache 조건으로 vLLM APC와 비교해야 합니다.
- 각 고객 문서의 시작 부분부터 완전히 다르고 common prefix가 거의 없다면, RadixAttention의 cache advantage는 크지 않을 수 있습니다.


## OOM 대응 전략

OOM은 단순히 “GPU VRAM이 부족하다”가 아니라, 어느 메모리 영역이 문제인지 구분해야 합니다.


| OOM 유형 | 주 원인 | 우선 조치 |
| :-- | :-- | :-- |
| 모델 load 직후 OOM | weight + runtime workspace가 VRAM 초과 | 더 많은 GPU TP, 더 낮은 dtype/quantization, 더 큰 VRAM GPU |
| 첫 요청 prefill OOM | context가 과도하게 큼 | max context 축소, chunked prefill, long-context pool 분리 |
| 동시성 증가 후 OOM | KV cache 소진 | max running request 축소, max sequence 축소, KV budget 조정 |
| 특정 긴 요청만 OOM | unbounded prompt/RAG 문서 | input token quota, chunking, truncation/rerank |
| 시간이 지나며 OOM | cache pressure, memory leak, 비정상 재시작 | cache metric·VRAM trend 확인, version upgrade/rollback, 재시작 정책 |
| TP 실행에서 OOM | GPU 수/VRAM 불충분, 불균등 분할 | TP 확대, GPU 균질화, model-specific parallel plan 확인 |
| 여러 엔진 공존 OOM | GPU 메모리 예약 총합 과다 | GPU별 engine 격리, memory fraction 합계 축소 |

### vLLM OOM 대응

| 순서 | 조치 | 예시 |
| --: | :-- | :-- |
| 1 | GPU VRAM 예산을 보수적으로 설정 | `--gpu-memory-utilization 0.80` |
| 2 | 최대 context를 업무 기준으로 제한 | `--max-model-len 8192` |
| 3 | 동시 sequence 제한 | `--max-num-seqs 32` |
| 4 | batch token 상한 조정 | `--max-num-batched-tokens 8192` |
| 5 | 모델 weight 축소 | AWQ/GPTQ/FP8/INT4 검증 |
| 6 | TP 증가 또는 replica 재배치 | `--tensor-parallel-size 2` |
| 7 | 긴 문서 전용 deployment 분리 | long-context model pool |
| 8 | 단일 GPU 다중 process 제거 | GPU당 한 엔진 권장 |

```bash
vllm serve /srv/models/Qwen3-32B \
  --served-model-name qwen3-32b \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.82 \
  --max-model-len 16384 \
  --max-num-seqs 32 \
  --max-num-batched-tokens 8192 \
  --enable-prefix-caching
```

`--gpu-memory-utilization`을 올리면 KV cache 공간은 늘지만 runtime workspace와 memory fragmentation에 대한 여유가 줄어듭니다. 높은 동시성을 위해서도 처음부터 0.95 이상을 고정하기보다 0.80~0.88에서 안정성 baseline을 확인한 뒤 올리는 편이 낫습니다. vLLM은 max sequence 수를 줄이거나 GPU cache 비율을 조정하는 방식으로 cache pressure를 완화할 수 있습니다.[^7_7][^7_3]

vLLM은 sleep mode에서 모델 weight를 CPU RAM으로 offload하고 KV cache를 폐기해 GPU memory의 90% 이상을 반환할 수 있습니다. 다만 이는 interactive serving 중 OOM 회피책이 아니라, GPU를 일시적으로 다른 작업에 양보하는 운영 기능으로 보아야 합니다.[^7_8]

### SGLang OOM 대응

| 순서 | 조치 | 예시 |
| --: | :-- | :-- |
| 1 | static VRAM fraction을 보수적으로 낮춤 | `--mem-fraction-static 0.80` |
| 2 | 최대 context 제한 | `--context-length 8192` |
| 3 | 실행 중 요청 수 제한 | `--max-running-requests 24` |
| 4 | chunked prefill 크기 축소 | `--chunked-prefill-size 4096` |
| 5 | 긴 문서·reasoning 모델 풀 분리 | 별도 GPU deployment |
| 6 | TP 확대 | `--tp 2`, `--tp 4` |
| 7 | 모델 dtype/quantization 변경 | BF16 → FP8/AWQ/INT4 검증 |
| 8 | cache warming 범위 제한 | 불필요한 장문 prefix의 상시 유지 방지 |

```bash
python -m sglang.launch_server \
  --model-path /srv/models/Qwen3-32B \
  --served-model-name qwen3-32b \
  --tp 2 \
  --mem-fraction-static 0.82 \
  --context-length 16384 \
  --max-running-requests 32 \
  --chunked-prefill-size 4096 \
  --host 127.0.0.1 \
  --port 30000
```

SGLang에서는 Radix cache가 공통 prefix를 재사용하므로, cache hit은 좋아도 너무 많은 서로 다른 long-prefix를 동시에 warm하게 유지하면 VRAM이 KV cache로 채워질 수 있습니다. 따라서 tenant별로 완전히 다른 장문 문서를 상시 prefix로 고정하는 설계는 피하고, LRU eviction이 정상 작동하도록 cache 용량·동시성·context 상한을 같이 조정해야 합니다.

## 운영 대응 순서

OOM이 발생했을 때 다음 순서로 대응하면 품질 저하와 운영 중단을 최소화할 수 있습니다.

1. **요청을 제한합니다.** API gateway에서 입력 token, 출력 token, 동시 요청 quota를 우선 적용합니다.
2. **긴 요청을 격리합니다.** short chat과 long document/reasoning을 서로 다른 model deployment와 GPU queue로 분리합니다.
3. **KV budget을 조정합니다.** vLLM은 `gpu_memory_utilization`, SGLang은 `mem-fraction-static`을 낮춰 runtime headroom을 확보합니다.
4. **동시성을 낮춥니다.** vLLM은 `max-num-seqs`, SGLang은 `max-running-requests`를 줄입니다.
5. **context를 줄입니다.** 최대 context, RAG chunk 수, chunk 길이, top-k, tool result 상한을 함께 줄입니다.
6. **병렬화 또는 모델 형식을 변경합니다.** TP를 확장하거나 FP8/AWQ/GPTQ/INT4를 적용하되, 동일 품질 평가 세트에서 정확도·JSON 준수·한국어 품질을 재검증합니다.
7. **정상화 지표를 확인합니다.** GPU memory used, KV cache utilization, queue time, TTFT p95/p99, error rate가 안정화되기 전에는 다시 concurrency를 높이지 않습니다.

## 엔진별 권장 위치

| 업무 특성 | 1차 선택 | 이유 |
| :-- | :-- | :-- |
| 일반 사내 chat/RAG API | vLLM | 성숙한 PagedAttention·APC·관측 생태계 |
| 반복 system prompt·tool schema | SGLang | RadixAttention 기반 prefix reuse |
| 멀티턴 agent | SGLang A/B 우선 | 대화 history와 공통 tool definition의 재사용 |
| 긴 문서 1회성 분석 | vLLM 또는 SGLang 실제 측정 | prefix overlap이 작으면 cache advantage 제한 |
| 구조화 추출/tool calling | SGLang | parser·structured generation 경로 |
| low-latency short Q\&A | 작은 모델 vLLM replica 또는 SGLang | TP 확대보다 TP1 replica로 queue를 줄이는 편이 유리 |

최종적으로 SGLang과 vLLM 중 하나만 표준화하기보다, **vLLM을 범용 serving baseline으로 두고 SGLang을 shared-prefix·agent·structured-output 전용 pool로 운영**하는 하이브리드 구성이 가장 현실적입니다.

<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://docs.vllm.ai/en/stable/design/prefix_caching/

[^7_2]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^7_3]: https://docs.vllm.ai/en/stable/api/vllm/config/cache/

[^7_4]: https://docs.vllm.ai/en/v0.19.0/cli/serve/

[^7_5]: https://prakashkagitha.github.io/llm-stack-book/07-inference-serving/07-prefix-caching.html

[^7_6]: https://llm-academy.dev/optimization/prefix-caching/

[^7_7]: https://docs.vllm.ai/en/v0.26.0/configuration/optimization/

[^7_8]: https://docs.vllm.ai/en/v0.19.0/features/sleep_mode/

[^7_9]: https://docs.vllm.ai/en/v0.27.1/api/vllm/config/cache/

[^7_10]: https://docs.vllm.ai/en/latest/api/vllm/config/cache/

[^7_11]: https://docs.vllm.ai/en/v0.10.2/api/vllm/config/cache.html

[^7_12]: https://llm-academy.dev/inference/sglang-radixattention/

[^7_13]: https://deploybase.ai/articles/sglang-vs-vllm

[^7_14]: https://www.spheron.network/blog/vllm-vs-sglang-2026/

[^7_15]: https://docs.vllm.ai/en/stable/cli/bench/throughput/

[^7_16]: https://docs.vllm.ai/en/v0.14.0/cli/bench/throughput/


---

# Compare vLLM and SGLang KV caching: RadixAttention vs. PagedAttention, prefix reuse, and memory fragmentation trade-offs

LLM OOM mitigation audit: Compare vLLM request preemption against SGLang’s Radix-based scheduling strategies
SGLang radix tree 구조와 RadixAttention 원리
LLM 서빙 엔진별 TTFT TPS 성능 벤치마크

vLLM과 SGLang은 모두 paged KV-cache를 이용해 연속 메모리 할당 문제를 줄이지만, **vLLM은 PagedAttention과 block-hash APC를 중심으로 범용적인 처리량·preemption을 최적화**하고, **SGLang은 그 위에 radix tree와 cache-aware scheduling을 얹어 공통 prefix를 더 적극적으로 재사용**합니다. 따라서 shared-prefix가 거의 없는 일반 chat에서는 차이가 작을 수 있지만, agent/RAG처럼 공통 system prompt·tool schema·few-shot이 반복되면 SGLang의 warm-cache TTFT가 크게 유리해질 수 있습니다.[^8_1][^8_2]

## 1. KV cache 구조 비교

### 공통 기반: paged KV cache

전통적인 방식은 요청별 KV cache를 하나의 연속된 tensor로 확보하려 합니다. 이 경우 요청 길이가 다르고 수시로 종료되면 큰 연속 영역을 찾기 어렵고, 미사용 메모리 조각이 남는 **external fragmentation** 문제가 생깁니다.

vLLM과 SGLang은 이를 피하기 위해 KV cache를 일정 토큰 수의 물리 block/page로 쪼갭니다.

```text
논리 token 순서
Request A: [T0 ... T15] [T16 ... T31] [T32 ... T47]

물리 GPU block
Request A:    Block 7       Block 31      Block 2
```

논리적으로 연속된 prompt라도 물리 block은 GPU VRAM의 어느 위치에 있어도 됩니다. 요청이 종료되면 그 block만 free pool로 되돌아가 다른 요청이 즉시 재사용합니다. vLLM의 일반적인 block size는 16 tokens이며, block table이 논리 token 위치와 비연속 물리 block을 매핑합니다.[^8_3][^8_4]

### 엔진별 차이

| 항목 | vLLM | SGLang |
| :-- | :-- | :-- |
| 기본 메모리 모델 | PagedAttention | Paged KV cache pool + RadixAttention |
| GPU block 관리 | block table + free-block pool | block pool + radix cache node/path |
| fragmentation 회피 | 비연속 fixed-size block 할당 | 동일한 paged block allocation 사용 |
| prefix index | hash 기반 APC | radix tree / compressed trie |
| prefix 공유 단위 | 일치하는 complete token block | longest matching prefix path를 tree에서 탐색 |
| cache-aware scheduling | 범용 scheduler 중심 | radix cache locality를 적극 반영 |
| 주력 workload | 일반 chat/RAG, 다양한 prompt | agent, multi-turn, 반복 template |
| memory 정책 | block 재사용·preemption | radix node 참조·reuse·eviction |
| 주된 위험 | cache pressure → request preemption | 많은 unique long prefix → radix cache pressure |

중요한 점은 **SGLang도 fragmentation 회피를 위해 paged block allocation을 사용한다**는 것입니다. RadixAttention은 PagedAttention을 “대체하는 단일 메모리 allocator”가 아니라, paged KV block을 효율적으로 공유·검색·스케줄링하기 위한 상위 cache 구조로 이해하는 것이 정확합니다.[^8_4][^8_5]

## 2. Prefix reuse 비교

### vLLM: block hash 기반 APC

vLLM의 Automatic Prefix Caching(APC)은 complete KV block마다 token ID hash를 계산해 재사용합니다.

```text
Prompt A
[system prompt ... 16 token block] [16 token block] [partial block]

Prompt B
[동일 첫 block] [동일 두 번째 block] [다른 사용자 질의]
```

- 완전히 일치하는 prefix block은 기존 KV block을 공유합니다.
- 공유 block은 reference count로 보호됩니다.
- 새 요청이 동일 block을 참조하면 그 block의 prefill 계산을 건너뜁니다.
- 마지막 partial block은 complete block이 아니므로 대체로 재계산 대상이 됩니다.
- tokenizer, chat template, tool schema의 token sequence가 조금만 달라져도 cache hit가 줄어듭니다.

vLLM APC는 중복 prompt 계산을 피하기 위한 KV block 재사용 기능이며, full block 기준 token hash로 cache hit을 판정합니다.[^8_6][^8_1]

### SGLang: radix tree 기반 RadixAttention

SGLang은 request prefix를 radix tree의 경로로 저장합니다. 각 tree path는 이미 계산된 prefix KV block들과 연결됩니다. 새 요청이 들어오면 root에서 token sequence를 따라가며 **가장 긴 공통 prefix(longest prefix match)** 를 찾고, 일치한 구간은 prefill 없이 재사용하고 남은 suffix만 계산합니다.

```text
Root
 └─ [System prompt + policy + tool schema]
     ├─ [Customer A document]
     │   └─ [Question A]
     ├─ [Customer B document]
     │   └─ [Question B]
     └─ [Customer C document]
         └─ [Question C]
```

이 구조는 다음 조건에서 특히 유리합니다.

- 모든 요청이 동일한 2K~10K system prompt를 공유
- MCP/tool 정의, JSON schema, policy/few-shot이 동일
- agent가 같은 workflow prompt를 반복 사용
- multi-turn session에서 이전 history가 계층적으로 누적
- RAG template은 동일하고 customer data만 suffix로 달라짐

SGLang은 prefix caching용 RadixAttention, cache-aware scheduling, continuous batching을 제공하며, shared prefix가 있는 요청의 prefill 비용을 줄이는 데 초점을 둡니다.[^8_2][^8_7]

### Trade-off

| 상황 | vLLM APC | SGLang RadixAttention | 실무 판단 |
| :-- | :-- | :-- | :-- |
| 모든 prompt가 거의 고유 | cache hit 낮음 | cache hit 낮음 | vLLM을 baseline으로 선택 |
| 동일 system prompt 반복 | full block까지 reuse | longest common prefix reuse | SGLang A/B 우선 |
| 공통 prefix가 길고 요청이 많음 | 유의미한 prefill 절감 | 매우 큰 prefill 절감 가능 | SGLang 우선 검증 |
| 마지막 prefix 경계가 block 중간 | 해당 부분은 재계산 가능 | tree match 후 suffix만 계산 | SGLang이 상대적으로 유리할 수 있음 |
| 다중턴 agent | 일부 history block 재사용 | session prefix path 재사용에 적합 | SGLang A/B 우선 |
| 여러 tenant의 서로 다른 장문 문서 | cache churn 증가 | radix tree node 증가·eviction 증가 | cache isolation/TTL 필요 |
| 순수 short chat | cache 절감 작음 | tree 관리 이득 작음 | 작은 model replica가 더 중요 |

공개 자료에서 제시하는 단일 수치 벤치마크는 모델·GPU·cache warm 상태·prompt 중복률에 강하게 좌우됩니다. 예를 들어 일부 H100 기반 공개 비교는 ShareGPT류 workload에서 SGLang 약 16,200 tok/s, vLLM 약 12,500 tok/s를 보고하지만, 이 수치를 일반적인 운영 성능으로 간주해서는 안 됩니다. 별도 비교는 Llama 3 70B/A100에서 vLLM TTFT 120ms·7,200 tok/s, SGLang TTFT 110ms·7,500 tok/s를 제시합니다. 이 차이는 benchmark 환경과 workload에 따라 결론이 달라질 수 있음을 보여줍니다.[^8_8][^8_9]

## 3. OOM 완화 감사

### OOM이 발생하는 위치

```text
GPU VRAM
├─ Model weights
├─ CUDA graph / kernel workspace
├─ Activations / temporary buffers
└─ KV cache
   ├─ active request blocks
   ├─ shared prefix blocks
   └─ cached-but-idle prefix blocks
```

운영 중 OOM은 대개 “모델 자체가 안 들어감”보다 **KV cache가 장문 입력·높은 동시성·prefix cache·출력 생성 때문에 포화**되어 발생합니다.

### vLLM: request preemption

vLLM은 GPU KV block이 부족하면 scheduler가 실행 중인 요청을 preempt할 수 있습니다. 일반적으로 preempt 대상 요청의 KV block을 회수하고, 해당 요청은 나중에 다시 scheduling 됩니다.

대표 전략은 다음과 같습니다.


| 전략 | 동작 | 장점 | 비용 |
| :-- | :-- | :-- | :-- |
| Recompute | victim request의 GPU KV block을 해제하고 재개 시 prefill 재계산 | CPU RAM 불필요, 단순 | 재실행 시 TTFT·E2E 증가 |
| Swap | victim request KV block을 CPU RAM으로 비동기 이동 후 재개 시 GPU로 복귀 | prefill 재계산 감소 | PCIe/NVLink copy 비용, CPU RAM 필요 |
| Reject/admission control | 새 요청을 대기·거절 | 기존 요청 SLO 보호 | client retry/429 처리 필요 |

vLLM scheduler는 KV cache pool이 임계 상태에 도달하면 실행 중 sequence를 preempt할 수 있으며, sustained cache usage 90% 이상은 preemption 가능성이 커지는 구간으로 볼 수 있습니다. 내부 구현 설명에 따르면 recompute 방식은 victim KV를 해제하고 재개 시 prefill을 다시 수행하며, swap은 KV를 CPU로 옮겨 재사용하지만 CPU 메모리와 전송 대역폭을 사용합니다.[^8_10][^8_6]

### SGLang: Radix-aware scheduling

SGLang은 prefix KV가 radix tree로 공유될 수 있으므로, cache 정책의 목적이 단순히 “가장 오래된 request를 비우는 것”이 아니라 **다음 요청에도 재사용될 가치가 큰 prefix path를 남기는 것**에 있습니다.


| 전략 | SGLang 관점 | 기대 효과 | 위험 |
| :-- | :-- | :-- | :-- |
| longest-prefix reuse | 새 요청의 longest matching path 탐색 | prefill 감소, TTFT 개선 | 고유 prompt에는 효과 제한 |
| cache-aware scheduling | cache hit이 큰 요청을 우선/효율적으로 batch | GPU 계산 재사용률 증가 | 공정성·tail latency 주의 |
| radix eviction | 재사용 가치가 낮은 leaf/old path 회수 | hot common prefix 보호 | unique long prompt churn |
| chunked prefill | 긴 입력을 잘라 prefill | short request starvation 완화 | 설정이 너무 작으면 throughput 저하 |
| prefill/decode 분리 | prefill과 decode resource 분리 | long-input와 streaming 간섭 완화 | 인프라·통신 복잡성 증가 |
| HiCache | GPU 밖 계층으로 KV 확장 | VRAM pressure 완화 | CPU/SSD/RDMA latency, 운영 복잡도 |

SGLang은 RadixAttention 외에 prefill-decode disaggregation 및 HiCache 관련 기능을 제공하며, KV cache를 shared-prefix workload에 맞춰 관리합니다.[^8_11][^8_2]

### OOM 대응 비교

| 상황 | vLLM 우선 대응 | SGLang 우선 대응 |
| :-- | :-- | :-- |
| GPU cache 포화 | `max-num-seqs` 축소, preemption 관찰, `gpu-memory-utilization` 조정 | `max-running-requests` 축소, `mem-fraction-static` 조정 |
| 긴 prompt 1개가 OOM | `max-model-len`, batch tokens 축소 | `context-length`, chunked prefill 축소 |
| shared prefix가 VRAM 점유 | APC hit/eviction·cache 상태 관찰 | radix tree churn·hot prefix 보호/tenant partition |
| 대기열 때문에 p99 TTFT 악화 | admission control, short/long pool | cache-aware batching + short/long pool |
| 모델 weight OOM | TP 증가, FP8/AWQ/GPTQ/INT4 | TP 증가, FP8/AWQ/GPTQ/INT4 |
| 여러 engine이 GPU 공유 | `gpu-memory-utilization` 총합 제한 | `mem-fraction-static` 총합 제한 |
| 유휴 상태에서 GPU 회수 | sleep mode | scale-down/별도 pool 또는 cache offload 설계 |

vLLM의 GPU memory utilization 기본값은 최신 문서 기준 0.92이며, 운영 초기에는 0.80~0.88 정도에서 시작해 workspace 및 CUDA graph 여유를 확보하는 것이 안전합니다. SGLang도 `--mem-fraction-static`으로 GPU VRAM 사용 예산을 제한해야 하며, shared-prefix cache가 과도하게 커지는 tenant 혼합 workload에서는 context와 concurrency 상한을 함께 설정해야 합니다.[^8_12]

## 4. Radix tree와 RadixAttention 원리

### Radix tree 구조

Radix tree는 trie의 압축형입니다. 각 token을 node 하나로 만들지 않고, 공통 경로가 아닌 연속 token 구간을 하나의 edge/node에 압축합니다.

```text
요청 1
[SYS][POLICY][TOOLS][DOC-A][Q-A]

요청 2
[SYS][POLICY][TOOLS][DOC-B][Q-B]

압축 radix tree
root
 └─ [SYS + POLICY + TOOLS] ── shared KV blocks
      ├─ [DOC-A + Q-A] ── request/cache branch A
      └─ [DOC-B + Q-B] ── request/cache branch B
```

각 edge/path에는 해당 token 구간의 KV block reference가 연결됩니다. 새 요청이 들어오면 root에서 토큰을 따라가다가 mismatch 지점에서 멈추고:

1. 이미 존재하는 longest matching path의 KV blocks를 참조합니다.
2. 일치하지 않는 suffix의 KV blocks만 새로 할당·prefill합니다.
3. 새 suffix를 radix tree branch로 추가합니다.
4. 요청이 끝난 뒤에도 정책상 재사용 가치가 있으면 해당 prefix path는 cache에 남습니다.
5. VRAM pressure가 발생하면 재사용 가치가 낮은 branch/leaf부터 eviction 대상이 됩니다.

### RadixAttention의 의미

일반 attention 수식 자체가 바뀌는 것은 아닙니다. 모델은 동일한 causal attention을 수행합니다. **RadixAttention은 이미 계산된 prefix의 K/V state를 radix tree로 찾아 재사용하는 serving-time cache·scheduler 전략**입니다.

즉:

$$
\text{KV}_{0:t} \text{가 cache hit이면, } \text{prefill}(0:t) \text{를 생략하고 } \text{prefill}(t+1:n) \text{만 수행}
$$

새 요청의 전체 prompt를 $P = C \Vert S$로, $C$를 기존 cache와 일치하는 prefix, $S$를 새 suffix라고 하면:

$$
\text{Compute}_{\text{new}} \approx \text{prefill}(S) + \text{decode}
$$

대신 cache miss일 경우:

$$
\text{Compute}_{\text{miss}} \approx \text{prefill}(C \Vert S) + \text{decode}
$$

공통 prefix $C$가 길고 재사용 횟수가 많을수록 TTFT 절감 폭이 커집니다. RadixAttention의 효과는 모델 정확도를 바꾸지 않고, 주로 prefill 계산량·TTFT·GPU 비용을 줄이는 데 있습니다.

## 5. TTFT·TPS 벤치마크 방법

### 수치 비교 시 주의

“엔진 A가 엔진 B보다 TTFT 30% 빠르다”는 주장은 다음이 하나라도 다르면 신뢰할 수 없습니다.

- cache cold vs warm 상태
- system prompt의 token 수
- prefix 중복률과 요청 순서
- model revision, quantization, tokenizer
- GPU 모델, GPU 개수, NVLink/NVSwitch 유무
- TP 크기와 `max_num_seqs`
- 요청 도착률, concurrency, output length
- benchmark가 server-side timestamp인지 client-side streaming timestamp인지

따라서 공개 benchmark는 가설 생성용으로만 쓰고, 도입 결정은 반드시 동일 hardware·실제 익명화 prompt로 해야 합니다.

### 권장 벤치마크 매트릭스

| Scenario | Input / Output | Cache | Concurrency | 주요 판정 |
| :-- | --: | :-- | --: | :-- |
| Short chat | 128 / 128 tokens | cold | 1, 4, 16, 64 | baseline TTFT/ITL |
| General RAG | 2K / 512 tokens | cold | 4, 16, 32, 64 | throughput/VRAM |
| Long document | 16K / 1K tokens | cold | 1, 4, 16 | prefill·OOM 한계 |
| Shared agent | 4K shared + 1K unique / 512 | warm | 16, 64, 128 | Radix/APC reuse 효과 |
| Multi-turn | 1K system + growing history / 256 | warm | 16, 64 | session reuse·tail latency |
| Burst | 1K / 512 tokens | cold | 0→128 burst | preemption/OOM/SLO |

### 지표와 계산

| 지표 | 계산 | 의미 |
| :-- | :-- | :-- |
| TTFT | request send → first non-empty stream token | 첫 응답 체감 |
| ITL | consecutive output tokens 간 시간 | 스트리밍 부드러움 |
| TPS | generated tokens / generation time | 생성 처리 성능 |
| RPS | completed requests / elapsed time | API 수용량 |
| Prefill TPS | input tokens / prefill time | 긴 prompt 처리 성능 |
| E2E latency | request send → stream complete | 최종 응답 시간 |
| p95/p99 TTFT | tail TTFT percentile | 사용자 SLO·burst 안정성 |
| VRAM peak | benchmark 중 최대 GPU memory used | OOM 위험 |
| cache hit rate | hit / lookup | shared-prefix 최적화 실효성 |
| preemption rate | preempted requests / completed requests | KV memory 부족 신호 |

TPS는 입력 처리와 출력 생성을 분리해 보는 편이 좋습니다.

$$
\text{Prefill TPS} =
\frac{\sum \text{input tokens}}{\sum \text{prefill time}}
$$

$$
\text{Decode TPS} =
\frac{\sum \text{generated tokens}}{\sum (\text{end time} - \text{first token time})}
$$

### 의사결정 기준

| 결과 | 권장 선택 |
| :-- | :-- |
| Cold-cache TTFT/TPS 비슷, vLLM 운영 안정성 우세 | vLLM 기본 pool |
| Shared-prefix warm-cache에서 SGLang TTFT p95가 20% 이상 개선 | agent/RAG를 SGLang pool으로 분리 |
| SGLang radix hit가 낮고 VRAM churn 증가 | vLLM 또는 SGLang cache policy/context 축소 |
| vLLM preemption이 자주 발생 | concurrency/context 축소, GPU/TP 증설, request pool 분리 |
| 둘 다 p99 TTFT가 SLO 초과 | 모델 축소, TP보다 replica 확대, input quota·admission control 적용 |
| TP 확대 후 TPS 하락 | GPU 통신 병목; TP 축소하고 replica 구성 재검토 |

사용자 요구처럼 short request는 빠르고 long reasoning도 30초 내 stream이 시작되어야 한다면, “최대 TPS”보다 **TTFT p95/p99, cache hit rate, preemption/OOM rate, queue wait time**을 1순위로 두어야 합니다.

<span style="display:none">[^8_13][^8_14][^8_15][^8_16][^8_17][^8_18][^8_19]</span>

<div align="center">⁂</div>

[^8_1]: https://docs.vllm.ai/en/stable/design/prefix_caching/

[^8_2]: https://github.com/sgl-project/sglang??ref=blog.premai.io

[^8_3]: https://prakashkagitha.github.io/llm-stack-book/07-inference-serving/03-vllm-internals.html

[^8_4]: https://ai-infrastructure.net/kv-cache-management/

[^8_5]: https://factory.ai/open-source-wikis/vllm?page=systems/kv-cache.md

[^8_6]: https://www.varunk.me/blog/how-vllm-works-internals-deep-dive

[^8_7]: https://turion.ai/blog/vllm-vs-sglang-inference-comparison-2026/

[^8_8]: https://llm-academy.dev/inference/vllm-vs-sglang/

[^8_9]: https://graphwiz.ai/vllm-vs-sglang-inference/

[^8_10]: https://www.runpod.io/articles/guides/vllm-pagedattention-continuous-batching

[^8_11]: https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/mem_cache/storage/mooncake_store/README.md

[^8_12]: https://docs.vllm.ai/en/stable/api/vllm/config/cache/

[^8_13]: https://nadhebe.com/comparisons/sglang-vs-vllm-performance/

[^8_14]: https://localaimaster.com/blog/sglang-vs-vllm-comparison

[^8_15]: https://deploybase.ai/articles/best-llm-inference-engine

[^8_16]: https://localaimaster.com/blog/kv-cache-paged-attention-guide

[^8_17]: https://syntexic.com/blog/vllm-vs-sglang-vs-tensorrt-llm-2026/

[^8_18]: https://inference.net/content/sglang-complete-guide/

[^8_19]: https://www.spheron.network/blog/vllm-vs-sglang-2026/

