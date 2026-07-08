# 기업 데이터 보안을 위한 Vector DB 온프레미스 배포 가이드

## 1. 배포 원칙
- 문서 원본 저장소, 임베딩 파이프라인, 벡터 DB, LLM 추론 계층을 분리한다.
- 민감 문서와 일반 문서를 별도 컬렉션/테넌트/네임스페이스로 분리한다.
- 임베딩 생성 구간과 검색 구간 모두에 감사 로그를 남긴다.

## 2. 하이브리드 검색 전략
- 순수 벡터 검색만으로는 코드, SKU, 약어, 조문, 정책 번호 같은 exact match를 놓칠 수 있다.
- BM25 + dense retrieval을 병렬 실행한 뒤 RRF(기본 k=60)로 결합한다.
- 1차 검색은 recall 극대화, 2차 reranker는 precision 향상에 사용한다.

## 3. 비용 최적화 체크리스트
- 임베딩 재생성 주기 최소화
- hot/warm 컬렉션 분리
- chunk size와 overlap 재조정
- 캐시 가능한 질의 분리
- 상위 K와 rerank depth 축소 실험
- GPU가 꼭 필요한 구간과 CPU 충분 구간 분리
- 사용량 기준 모델 라우팅(고가/저가 모델 분기)

## 4. Dify/n8n 연계 권장 구조
- Dify: 사용자-facing AI 앱과 RAG 워크플로우
- n8n: ERP/CRM/메일/승인/배치/재시도 오케스트레이션
- Vector DB: Qdrant 또는 pgvector 중심 검토, managed 환경이면 Pinecone 검토
