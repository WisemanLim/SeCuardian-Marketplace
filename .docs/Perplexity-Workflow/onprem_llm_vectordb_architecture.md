# 온프레미스 LLM 워크플로우 및 Vector DB 선정 가이드

## 1. 온프레미스 보안 가이드라인
- 프롬프트, 문서 원본, 임베딩, 추론 로그를 분리 저장한다.
- 외부 API LLM과 내부 로컬 LLM의 사용 경계를 정책으로 구분한다.
- 비밀정보는 워크플로우 변수 대신 비밀관리체계와 연계한다.
- 고위험 자동화는 Human-in-the-Loop 승인 단계를 둔다.
- 모델/프롬프트/임베딩 버전을 추적해 감사 가능성을 확보한다.

## 2. Dify + n8n 엔드투엔드 아키텍처
- Dify: AI 앱, 에이전트, 워크플로우, API, 프롬프트/RAG 계층
- n8n: ERP/CRM/메일/그룹웨어/레거시 연동, 승인, 재시도, 배치/이벤트 오케스트레이션
- Vector DB: Qdrant/Weaviate/pgvector 등 검색 계층
- Local LLM 또는 외부 LLM 게이트웨이: 모델 정책에 따라 분기

## 3. 권장 패턴
- 내부 포털/사내 지식검색: Dify + Qdrant + n8n
- PostgreSQL 중심 조직: Dify + pgvector + n8n
- 대규모 멀티테넌트 검색: Dify + Milvus + n8n
- 빠른 파일럿: Dify + Chroma, 이후 Qdrant 또는 pgvector로 이전 검토
