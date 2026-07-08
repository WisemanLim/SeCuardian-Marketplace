-- secuardian — DB 스키마 초기화 (idempotent, SQLite)

CREATE TABLE IF NOT EXISTS tbl_users (
    serial       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      VARCHAR(50)  NOT NULL UNIQUE,
    username     VARCHAR(50),
    email        VARCHAR(100),
    password     VARCHAR(200) NOT NULL,
    role         VARCHAR(20)  NOT NULL DEFAULT 'user',
    status       VARCHAR(20)  NOT NULL DEFAULT 'active',
    custom_instructions TEXT,
    totp_secret  TEXT,
    totp_enabled INTEGER      NOT NULL DEFAULT 0,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP
);

-- Agent 활성화 설정 (F8)
CREATE TABLE IF NOT EXISTS tbl_agent_config (
    agent_key    VARCHAR(50)  PRIMARY KEY,
    agent_name   VARCHAR(100) NOT NULL,
    is_enabled   INTEGER      NOT NULL DEFAULT 1,
    is_required  INTEGER      NOT NULL DEFAULT 0,
    model        TEXT,
    system_prompt TEXT,
    description  TEXT,
    description_en TEXT,
    disabled_reason TEXT,
    disabled_reason_en TEXT,
    nav_group    VARCHAR(50),
    sort_order   INTEGER      NOT NULL DEFAULT 0,
    updated_at   TIMESTAMP
);

-- Addon Agent 등록 (F4 + F22)
CREATE TABLE IF NOT EXISTS tbl_addon_agents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_key    VARCHAR(50)  NOT NULL UNIQUE,
    agent_name   VARCHAR(100) NOT NULL,
    router_path  VARCHAR(500),
    api_prefix   VARCHAR(100) NOT NULL,
    sql_path     VARCHAR(500),
    has_app      INTEGER      NOT NULL DEFAULT 0,
    has_front    INTEGER      NOT NULL DEFAULT 0,
    agent_type   TEXT         NOT NULL DEFAULT 'app',
    meta_json    TEXT,
    is_builtin   INTEGER      NOT NULL DEFAULT 0,
    is_active    INTEGER      NOT NULL DEFAULT 1,
    uploaded_by  VARCHAR(50),
    uploaded_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 설정 (F9, key-value)
CREATE TABLE IF NOT EXISTS tbl_settings (
    key          VARCHAR(100) PRIMARY KEY,
    value        TEXT,
    description  VARCHAR(200),
    updated_at   TIMESTAMP
);

-- Agent Registry — 외부 Standalone Agent (F12 + F23)
CREATE TABLE IF NOT EXISTS tbl_agent_registry (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_key          VARCHAR(50)  NOT NULL UNIQUE,
    agent_name         VARCHAR(100) NOT NULL,
    protocol           VARCHAR(10)  NOT NULL DEFAULT 'a2a',
    agent_card_url     VARCHAR(500),
    mcp_endpoint       VARCHAR(500),
    auth_token         TEXT,
    agent_type         TEXT         NOT NULL DEFAULT 'service',
    capabilities_json  TEXT,
    agent_card_json    TEXT,
    lifecycle_state    TEXT         NOT NULL DEFAULT 'active',
    health_score       REAL         NOT NULL DEFAULT 1.0,
    last_heartbeat_at  TIMESTAMP,
    lease_expires_at   TIMESTAMP,
    is_active          INTEGER      NOT NULL DEFAULT 1,
    last_seen_at       TIMESTAMP,
    created_by         VARCHAR(50),
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Addon Agent Capability 인덱스 (F23)
CREATE TABLE IF NOT EXISTS tbl_addon_agent_capabilities (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_key      VARCHAR(50)  NOT NULL,
    capability_key VARCHAR(100) NOT NULL,
    verb           VARCHAR(50)  NOT NULL,
    domain         VARCHAR(200) NOT NULL,
    description    TEXT,
    input_schema   TEXT,
    output_schema  TEXT,
    qos_json       TEXT,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_key, capability_key)
);

-- MCP Proxy 설정 (F12 MCP)
CREATE TABLE IF NOT EXISTS tbl_mcp_configs (
    agent_key    VARCHAR(50)  PRIMARY KEY,
    port         INTEGER,
    extra_args   TEXT,
    is_enabled   INTEGER      NOT NULL DEFAULT 1,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP
);

-- 감사 로그
CREATE TABLE IF NOT EXISTS tbl_audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    VARCHAR(50),
    action     VARCHAR(100) NOT NULL,
    target     VARCHAR(200),
    detail     TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 사용자별 대화 세션 (R18-2)
CREATE TABLE IF NOT EXISTS tbl_chat_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key VARCHAR(50)  NOT NULL,
    user_id     VARCHAR(50)  NOT NULL,
    agent_key   VARCHAR(50),
    title       VARCHAR(200),
    model       VARCHAR(100),
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP,
    UNIQUE(user_id, session_key)
);

-- 대화 메시지 (R18-2)
CREATE TABLE IF NOT EXISTS tbl_chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER      NOT NULL,
    role        VARCHAR(20)  NOT NULL,
    content     TEXT         NOT NULL,
    model       VARCHAR(100),
    latency_ms  INTEGER,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON tbl_chat_messages(session_id);

-- 응답 만족도 피드백 (R18-3, rating: bad|fine|good)
CREATE TABLE IF NOT EXISTS tbl_chat_feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  INTEGER      NOT NULL,
    user_id     VARCHAR(50)  NOT NULL,
    rating      VARCHAR(10)  NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP,
    UNIQUE(message_id, user_id)
);

-- 관리자(운영자) 건의 (R18-4)
CREATE TABLE IF NOT EXISTS tbl_suggestions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     VARCHAR(50)  NOT NULL,
    title       VARCHAR(200) NOT NULL,
    content     TEXT         NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'new',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Marketplace (F-MP) — 카탈로그 자산 + 설치 트랜잭션 (tenant_id 선반영 §7.4) ──
CREATE TABLE IF NOT EXISTS marketplace_assets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     VARCHAR(64)  NOT NULL DEFAULT 'default',
    asset_key     VARCHAR(64)  NOT NULL,
    version       VARCHAR(32)  NOT NULL DEFAULT '0.1.0',
    kind          VARCHAR(32)  NOT NULL DEFAULT 'agent',   -- agent|workflow|rag-pipeline|tool-proxy
    name          VARCHAR(128) NOT NULL,
    name_en       VARCHAR(128) DEFAULT '',
    description   TEXT         DEFAULT '',
    category      VARCHAR(64)  DEFAULT 'general',
    min_platform_version VARCHAR(32) DEFAULT '0.1.0',
    governance    TEXT         DEFAULT '',
    required_env  TEXT         DEFAULT '',
    checksum      VARCHAR(128) DEFAULT '',
    source        VARCHAR(16)  DEFAULT 'local',            -- local|remote
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, asset_key, version)
);

CREATE TABLE IF NOT EXISTS marketplace_installs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     VARCHAR(64)  NOT NULL DEFAULT 'default',
    asset_key     VARCHAR(64)  NOT NULL,
    version       VARCHAR(32)  NOT NULL,
    status        VARCHAR(16)  NOT NULL DEFAULT 'installed', -- installed|failed|rolled_back|uninstalled
    active        INTEGER      NOT NULL DEFAULT 1,
    installed_by  VARCHAR(128) DEFAULT '',
    error         TEXT         DEFAULT '',
    agent_config_key VARCHAR(50),
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_assets_key ON marketplace_assets(tenant_id, asset_key);
CREATE INDEX IF NOT EXISTS idx_mp_installs_key ON marketplace_installs(tenant_id, asset_key, active);

-- ── Marketplace 로컬 자산 ZIP 저장소 (F-MP §7.6) — 로컬 install 실 hot-deploy 용 ──
CREATE TABLE IF NOT EXISTS marketplace_asset_blobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     VARCHAR(64)  NOT NULL DEFAULT 'default',
    asset_key     VARCHAR(64)  NOT NULL,
    version       VARCHAR(32)  NOT NULL DEFAULT '0.1.0',
    filename      VARCHAR(256) DEFAULT '',
    checksum      VARCHAR(128) DEFAULT '',
    blob          BLOB         NOT NULL,
    uploaded_by   VARCHAR(128) DEFAULT '',
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, asset_key, version)
);

-- ── Workflow (F-WF) — DAG 정의 + 실행 + 노드 실행 기록 (tenant_id 선반영 §7.4) ──
CREATE TABLE IF NOT EXISTS workflows (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id           VARCHAR(64)  NOT NULL DEFAULT 'default',
    name                VARCHAR(128) NOT NULL,
    description         TEXT         DEFAULT '',
    definition_json     TEXT         NOT NULL DEFAULT '{}',   -- {nodes:[], edges:[]}
    trigger_type        VARCHAR(32)  NOT NULL DEFAULT 'manual',
    trigger_config_json TEXT         NOT NULL DEFAULT '{}',
    enabled             INTEGER      NOT NULL DEFAULT 1,
    version             INTEGER      NOT NULL DEFAULT 1,
    created_by          VARCHAR(128) DEFAULT '',
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       VARCHAR(64)  NOT NULL DEFAULT 'default',
    workflow_id     INTEGER      NOT NULL,
    status          VARCHAR(16)  NOT NULL DEFAULT 'pending', -- pending|running|waiting_hitl|completed|failed|cancelled
    trigger_source  VARCHAR(32)  NOT NULL DEFAULT 'manual',
    input_json      TEXT         NOT NULL DEFAULT '{}',
    output_json     TEXT         NOT NULL DEFAULT '{}',
    error           TEXT         DEFAULT '',
    waiting_node_id VARCHAR(64)  DEFAULT '',
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_node_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id    VARCHAR(64)  NOT NULL DEFAULT 'default',
    run_id       INTEGER      NOT NULL,
    node_id      VARCHAR(64)  NOT NULL,
    node_type    VARCHAR(32)  NOT NULL,
    status       VARCHAR(16)  NOT NULL DEFAULT 'pending',
    attempts     INTEGER      NOT NULL DEFAULT 0,
    input_json   TEXT         NOT NULL DEFAULT '{}',
    output_json  TEXT         NOT NULL DEFAULT '{}',
    error        TEXT         DEFAULT '',
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_wf_runs_wf ON workflow_runs(tenant_id, workflow_id);
CREATE INDEX IF NOT EXISTS idx_wf_node_runs_run ON workflow_node_runs(run_id);

-- ── RAG (F-RAG) — 컬렉션·문서·청크(임베딩+BM25 텀) (tenant_id 선반영 §7.4) ──
CREATE TABLE IF NOT EXISTS rag_collections (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id          VARCHAR(64)  NOT NULL DEFAULT 'default',
    name               VARCHAR(128) NOT NULL,
    description        TEXT         DEFAULT '',
    sensitivity        VARCHAR(16)  NOT NULL DEFAULT 'general', -- general|sensitive
    embedding_dim      INTEGER      NOT NULL DEFAULT 256,
    embedding_version  VARCHAR(32)  NOT NULL DEFAULT 'local-hash-v1',
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

CREATE TABLE IF NOT EXISTS rag_documents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id      VARCHAR(64)  NOT NULL DEFAULT 'default',
    collection_id  INTEGER      NOT NULL,
    title          VARCHAR(256) DEFAULT '',
    source         VARCHAR(256) DEFAULT '',
    text           TEXT         DEFAULT '',
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id      VARCHAR(64)  NOT NULL DEFAULT 'default',
    collection_id  INTEGER      NOT NULL,
    document_id    INTEGER      NOT NULL,
    ordinal        INTEGER      NOT NULL DEFAULT 0,
    text           TEXT         DEFAULT '',
    embedding_json TEXT         DEFAULT '[]',
    terms_json     TEXT         DEFAULT '{}',
    token_count    INTEGER      NOT NULL DEFAULT 0,
    norm           REAL         NOT NULL DEFAULT 0.0,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rag_docs_coll ON rag_documents(collection_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_coll ON rag_chunks(collection_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(document_id);

-- ── Playground (F-PG) — 프롬프트/모델/RAG 조합 실험 기록 (tenant_id 선반영 §7.4) ──
CREATE TABLE IF NOT EXISTS playground_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id         VARCHAR(64)  NOT NULL DEFAULT 'default',
    prompt            TEXT         NOT NULL,
    system_prompt     TEXT         DEFAULT '',
    model             VARCHAR(64)  DEFAULT '',
    rag_collection_id INTEGER,
    response_text     TEXT         DEFAULT '',
    provider          VARCHAR(16)  DEFAULT '',   -- ollama | degraded
    latency_ms        INTEGER      NOT NULL DEFAULT 0,
    input_tokens      INTEGER      NOT NULL DEFAULT 0,
    output_tokens     INTEGER      NOT NULL DEFAULT 0,
    citations_json    TEXT         DEFAULT '[]',
    created_by        VARCHAR(128) DEFAULT '',
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_runs_tenant ON playground_runs(tenant_id, created_at);

-- ── Guardrails (F-GRD) — 도메인 스코프는 SeCMP 소유(§7.8.3, 업스트림 미강제) ──
CREATE TABLE IF NOT EXISTS guardrails_domain_catalog (
    domain_key      VARCHAR(64) PRIMARY KEY,
    display_name    VARCHAR(128) NOT NULL,
    status          VARCHAR(16)  NOT NULL DEFAULT 'catalog_only',  -- functional | catalog_only
    rule_count      INTEGER      NOT NULL DEFAULT 0,
    last_synced_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_guardrail_config (
    agent_key   VARCHAR(50) NOT NULL,
    domain_key  VARCHAR(64) NOT NULL,
    enabled     INTEGER     NOT NULL DEFAULT 0,
    io_scope    VARCHAR(8)  NOT NULL DEFAULT 'both',   -- input | output | both
    updated_by  VARCHAR(128) DEFAULT '',
    updated_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_key, domain_key)
);

CREATE TABLE IF NOT EXISTS guardrails_decision_log (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_key          VARCHAR(50)  NOT NULL,
    decision_id        VARCHAR(64)  NOT NULL,
    domain_key         VARCHAR(64)  NOT NULL,
    decision           VARCHAR(16)  NOT NULL,
    risk_score         REAL         NOT NULL DEFAULT 0.0,
    matched_rule_count INTEGER      NOT NULL DEFAULT 0,
    tenant_id          VARCHAR(64)  NOT NULL DEFAULT 'default',
    session_id         VARCHAR(64)  DEFAULT '',
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_grd_decisions_agent ON guardrails_decision_log(agent_key, created_at);
