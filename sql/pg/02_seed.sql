-- secuardian — 기본 시드 데이터 (idempotent, PostgreSQL)

INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('general', 'Orchestrator', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'Orchestrator', is_required = 1,
  agent_names = '{"ko": "Orchestrator", "en": "Orchestrator", "jp": "オーケストレーター"}',
  descriptions = '{"ko": "사용자 요청의 의도를 분류하고 적합한 에이전트로 라우팅·합성하는 중앙 오케스트레이터입니다.", "en": "Central orchestrator that classifies user intent and routes/synthesizes responses across the appropriate agents.", "jp": "ユーザー要求の意図を分類し、適切なエージェントへルーティング・統合する中央オーケストレーターです。"}' WHERE agent_key = 'general';

INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('chat', 'AI 어시스턴트', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'AI 어시스턴트', is_required = 1,
  agent_names = '{"ko": "AI 어시스턴트", "en": "AI Assistant", "jp": "AIアシスタント"}',
  descriptions = '{"ko": "플랫폼 전반의 질의응답과 데이터 조회·생성·수정·삭제를 수행하는 AI 어시스턴트입니다.", "en": "AI assistant that handles platform-wide Q&A and performs data lookup, creation, update, and deletion.", "jp": "プラットフォーム全般の質疑応答とデータの照会・作成・更新・削除を行うAIアシスタントです。"}' WHERE agent_key = 'chat';

-- 내장 에이전트: Marketplace (F-MP)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('marketplace', '마켓플레이스', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '마켓플레이스', nav_group = '내장 에이전트', is_required = 1,
  agent_names = '{"ko": "마켓플레이스", "en": "Marketplace", "jp": "マーケットプレイス"}',
  descriptions = '{"ko": "에이전트·워크플로우·RAG 파이프라인 자산을 탐색·설치·버전관리하는 마켓플레이스입니다.", "en": "Marketplace to browse, install, and version agent/workflow/RAG-pipeline assets.", "jp": "エージェント・ワークフロー・RAGパイプライン資産を検索・インストール・バージョン管理するマーケットプレイスです。"}' WHERE agent_key = 'marketplace';

-- 내장 에이전트: Workflow (F-WF)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('workflow', '워크플로우', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '워크플로우', nav_group = '내장 에이전트', is_required = 1,
  agent_names = '{"ko": "워크플로우", "en": "Workflow", "jp": "ワークフロー"}',
  descriptions = '{"ko": "에이전트·LLM·조건·HITL 노드를 DAG로 조합해 자동화하는 워크플로우 엔진입니다.", "en": "Workflow engine that composes agent/LLM/condition/HITL nodes into automated DAGs.", "jp": "エージェント・LLM・条件・HITLノードをDAGで組み合わせて自動化するワークフローエンジンです。"}' WHERE agent_key = 'workflow';

-- 내장 에이전트: RAG (F-RAG)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('rag', 'RAG', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = 'RAG', nav_group = '내장 에이전트', is_required = 1,
  agent_names = '{"ko": "RAG", "en": "RAG", "jp": "RAG"}',
  descriptions = '{"ko": "문서 수집→임베딩→하이브리드(BM25+dense+RRF) 검색을 제공하는 지식베이스 파이프라인입니다.", "en": "Knowledge base pipeline: document ingest → embedding → hybrid (BM25+dense+RRF) search.", "jp": "文書取り込み→埋め込み→ハイブリッド(BM25+dense+RRF)検索を提供する知識ベースパイプラインです。"}' WHERE agent_key = 'rag';

-- 내장 에이전트: Playground (F-PG)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('playground', '플레이그라운드', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '플레이그라운드', nav_group = '내장 에이전트', is_required = 1,
  agent_names = '{"ko": "플레이그라운드", "en": "Playground", "jp": "プレイグラウンド"}',
  descriptions = '{"ko": "프롬프트·모델·RAG 컬렉션을 조합해 대화형으로 실험하는 도구입니다.", "en": "Interactive tool to experiment by combining prompt, model, and RAG collections.", "jp": "プロンプト・モデル・RAGコレクションを組み合わせて対話的に実験するツールです。"}' WHERE agent_key = 'playground';

-- 내장 에이전트: Guardrails (F-GRD)
INSERT INTO tbl_agent_config (agent_key, agent_name, is_enabled, is_required, nav_group, sort_order)
VALUES ('guardrails', '가드레일', 1, 1)
ON CONFLICT (agent_key) DO NOTHING;
UPDATE tbl_agent_config SET agent_name = '가드레일', nav_group = '내장 에이전트', is_required = 1,
  agent_names = '{"ko": "가드레일", "en": "Guardrails", "jp": "ガードレール"}',
  descriptions = '{"ko": "PII/신용정보 등 도메인 규칙셋을 요청/응답에 강제하는 거버넌스 에이전트입니다(1차: global 도메인 실판정).", "en": "Governance agent enforcing domain rule sets (PII/financial) on requests/responses (phase 1: global domain only).", "jp": "PII/金融情報などのドメインルールセットを要求/応答に強制するガバナンスエージェントです(第1段階: globalドメインのみ実判定)。"}' WHERE agent_key = 'guardrails';

INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('global', 'Global PII/신용정보', 'functional', 13) ON CONFLICT (domain_key) DO NOTHING;
INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('manufacturing-food', '제조업(식품)', 'catalog_only', 0) ON CONFLICT (domain_key) DO NOTHING;
INSERT INTO guardrails_domain_catalog (domain_key, display_name, status, rule_count)
VALUES ('public-administration', '공공행정', 'catalog_only', 0) ON CONFLICT (domain_key) DO NOTHING;

-- (agent_names 는 위 각 에이전트 UPDATE 에서 descriptions 와 함께 JSON 으로 직접 저자 — §7.11.2-5)

DELETE FROM tbl_agent_config WHERE agent_key IN ('example', 'board');
DELETE FROM tbl_addon_agents WHERE agent_key = 'board';

INSERT INTO tbl_settings (key, value, description) VALUES
  ('orchestrator_model',  'claude-sonnet-4-6',       'Orchestrator LLM 모델'),
  ('domain_agent_model',  'claude-haiku-4-5-20251001','Domain Agent LLM 모델'),
  ('ollama_base_url',     'http://localhost:11434',    'Ollama 서버 주소'),
  ('ollama_model',        'mistral',                  'Ollama 기본 모델'),
  ('local_llm_provider',  'ollama',                    'R19-1 기본 로컬 LLM provider (ollama|llamacpp|vllm)'),
  ('llamacpp_base_url',   'http://localhost:8180',     'llama.cpp server 주소 (OpenAI 호환)'),
  ('llamacpp_model',      '',                          'llama.cpp 모델명 (단일 모델 서빙 시 생략 가능)'),
  ('vllm_base_url',       'http://localhost:8100',     'vLLM OpenAI 호환 서버 주소'),
  ('vllm_model',          '',                          'vLLM 모델명'),
  ('llm_routes',          '',                          'R19-2 작업별 LLM 라우팅 (JSON: task→provider/model)'),
  ('llm_context_budget',  '8000',                      'R19-4 히스토리 토큰 예산 (초과 시 압축, 0=무압축)'),
  ('fallback_enabled',    'true',                      'LLM Fallback 활성화'),
  ('setup_completed',     'false',                     'Setup Wizard 완료'),
  ('system_custom_instructions', '',                  '시스템 전체 맞춤지침 (모든 사용자에게 적용)'),
  ('user_custom_instructions',   '',                  '사용자 공통 맞춤지침 (Supervisor가 정의하는 사용자 공통 제약·지침)')
ON CONFLICT (key) DO NOTHING;
