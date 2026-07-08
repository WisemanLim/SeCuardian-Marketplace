# Vector DB 마이그레이션 및 확장 전략 가이드

## 1. 마이그레이션 트리거
- PostgreSQL 재사용에서 시작했지만 벡터 수와 동시성 증가로 검색 지연이 커질 때
- 메타데이터 필터링, 하이브리드 검색, 멀티테넌시 요구가 늘어날 때
- 운영팀이 별도 벡터 검색 계층을 감당할 수 있게 되었을 때

## 2. 권장 진화 경로
- 1단계: pgvector로 PoC 및 초기 운영
- 2단계: Qdrant 또는 Weaviate로 전환하여 하이브리드 검색과 필터링 강화
- 3단계: 대규모 분산이 필요하면 Milvus 또는 managed 서비스 검토

## 3. 마이그레이션 체크리스트
- 문서 ID와 chunk ID의 불변 키 유지
- embedding model 버전과 차원 수 고정 또는 재색인 계획 수립
- relevance baseline(Recall@10, NDCG@10, latency p95) 확보
- dual write 및 shadow query로 새 인덱스 검증
- 컷오버 전후 재현 가능한 평가셋 유지

## 4. LLM 거버넌스 자동화 구현 사례 패턴
- 프롬프트 템플릿 변경 시 승인 워크플로우
- 고위험 응답은 confidence + citation + human review
- 검색 결과에 민감 필드가 포함되면 자동 마스킹
- 툴 실행 전 정책 엔진(allow/deny/approve) 적용
- 감사로그를 tenant, user, prompt version, model version 기준으로 저장

## 5. 인덱싱 및 검색 최적화
- 문서 유형별 chunking 정책 분리 (정책문서, 코드, FAQ, 표 형식 문서)
- BM25와 dense index를 동시 구축
- 기본 fusion은 RRF(k=60), latency 예산이 작으면 top-k와 rerank depth 축소
- exact identifier(코드/SKU/약어)가 많은 도메인은 sparse 가중치 강화
