-- secuardian — 기본 시드 데이터 (idempotent, PostgreSQL)

INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('general', 'Orchestrator', 1, 1, '기본 Agent', 0, '사용자 요청의 의도를 분류하고 적합한 에이전트로 라우팅·합성하는 중앙 오케스트레이터입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'Orchestrator', is_required = 1,
  description = '사용자 요청의 의도를 분류하고 적합한 에이전트로 라우팅·합성하는 중앙 오케스트레이터입니다.',
  description_en = 'Central orchestrator that classifies user intent and routes/synthesizes responses across the appropriate agents.' WHERE agent_key = 'general';

INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('chat', 'AI 어시스턴트', 1, 1, '기본 Agent', 1, '플랫폼 전반의 질의응답과 데이터 조회·생성·수정·삭제를 수행하는 AI 어시스턴트입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'AI 어시스턴트', is_required = 1,
  description = '플랫폼 전반의 질의응답과 데이터 조회·생성·수정·삭제를 수행하는 AI 어시스턴트입니다.',
  description_en = 'AI assistant that handles platform-wide Q&A and performs data lookup, creation, update, and deletion.' WHERE agent_key = 'chat';

-- 내장 에이전트: Marketplace (F-MP)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('marketplace', '마켓플레이스', 1, 0, '내장 에이전트', 2, '에이전트·워크플로우·RAG 파이프라인 자산을 탐색·설치·버전관리하는 마켓플레이스입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '마켓플레이스', nav_group = '내장 에이전트',
  description = '에이전트·워크플로우·RAG 파이프라인 자산을 탐색·설치·버전관리하는 마켓플레이스입니다.',
  description_en = 'Marketplace to browse, install, and version agent/workflow/RAG-pipeline assets.' WHERE agent_key = 'marketplace';

-- 내장 에이전트: Workflow (F-WF)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('workflow', '워크플로우', 1, 0, '내장 에이전트', 3, '에이전트·LLM·조건·HITL 노드를 DAG로 조합해 자동화하는 워크플로우 엔진입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '워크플로우', nav_group = '내장 에이전트',
  description = '에이전트·LLM·조건·HITL 노드를 DAG로 조합해 자동화하는 워크플로우 엔진입니다.',
  description_en = 'Workflow engine that composes agent/LLM/condition/HITL nodes into automated DAGs.' WHERE agent_key = 'workflow';

-- 내장 에이전트: RAG (F-RAG)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('rag', 'RAG', 1, 0, '내장 에이전트', 4, '문서 수집→임베딩→하이브리드(BM25+dense+RRF) 검색을 제공하는 지식베이스 파이프라인입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'RAG', nav_group = '내장 에이전트',
  description = '문서 수집→임베딩→하이브리드(BM25+dense+RRF) 검색을 제공하는 지식베이스 파이프라인입니다.',
  description_en = 'Knowledge base pipeline: document ingest → embedding → hybrid (BM25+dense+RRF) search.' WHERE agent_key = 'rag';

-- 내장 에이전트: Playground (F-PG)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('playground', '플레이그라운드', 1, 0, '내장 에이전트', 5, '프롬프트·모델·RAG 컬렉션을 조합해 대화형으로 실험하는 도구입니다.')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '플레이그라운드', nav_group = '내장 에이전트',
  description = '프롬프트·모델·RAG 컬렉션을 조합해 대화형으로 실험하는 도구입니다.',
  description_en = 'Interactive tool to experiment by combining prompt, model, and RAG collections.' WHERE agent_key = 'playground';

-- 내장 에이전트: Guardrails (F-GRD)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order, description)
VALUES ('guardrails', '가드레일', 1, 0, '내장 에이전트', 6, 'PII/신용정보 등 도메인 규칙셋을 요청/응답에 강제하는 거버넌스 에이전트입니다(1차: global 도메인 실판정).')
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '가드레일', nav_group = '내장 에이전트',
  description = 'PII/신용정보 등 도메인 규칙셋을 요청/응답에 강제하는 거버넌스 에이전트입니다(1차: global 도메인 실판정).',
  description_en = 'Governance agent enforcing domain rule sets (PII/financial) on requests/responses (phase 1: global domain only).' WHERE agent_key = 'guardrails';

INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('global', 'Global PII/신용정보', 'functional', 13) ON CONFLICT (domain_key) DO NOTHING;
INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('manufacturing-food', '제조업(식품)', 'catalog_only', 0) ON CONFLICT (domain_key) DO NOTHING;
INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('public-administration', '공공행정', 'catalog_only', 0) ON CONFLICT (domain_key) DO NOTHING;

DELETE FROM tbl_agent_config WHERE agent_key IN ('example', 'board');
DELETE FROM tbl_addon_agents WHERE agent_key = 'board';

INSERT INTO tbl_settings (key, value, description) VALUES
  ('orchestrator_model',  'claude-sonnet-4-6',       'Orchestrator LLM 모델'),
  ('domain_agent_model',  'claude-haiku-4-5-20251001','Domain Agent LLM 모델'),
  ('ollama_base_url',     'http://localhost:11434',    'Ollama 서버 주소'),
  ('ollama_model',        'mistral',                  'Ollama 기본 모델'),
  ('fallback_enabled',    'true',                      'LLM Fallback 활성화'),
  ('setup_completed',     'false',                     'Setup Wizard 완료'),
  ('system_custom_instructions', '',                  '시스템 전체 맞춤지침 (모든 사용자에게 적용)'),
  ('user_custom_instructions',   '',                  '사용자 공통 맞춤지침 (Supervisor가 정의하는 사용자 공통 제약·지침)')
ON CONFLICT (key) DO NOTHING;
