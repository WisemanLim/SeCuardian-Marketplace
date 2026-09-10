"""secuardian — settings (env-driven)."""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_env_file = f".env.{os.getenv('ENV', 'local')}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    app_name: str = "secuardian"  # [CUSTOMIZE]
    env: str = "local"

    # Database
    database_url: str = "sqlite:///./local.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Claude API (Orchestrator + Domain Agents)
    anthropic_api_key: str = ""
    orchestrator_model: str = "claude-sonnet-4-6"
    domain_agent_model: str = "claude-haiku-4-5-20251001"

    # OpenAI (선택)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Google Gemini (선택)
    google_api_key: str = ""
    google_model: str = "gemini-1.5-flash"

    # Ollama (로컬 LLM 폴백)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    # Ollama 예열(warmup): (재)구동 후 첫 토큰 콜드스타트 지연 방지 — "hi" 선요청으로 모델 상주
    ollama_warmup_enabled: bool = True
    ollama_warmup_interval: int = 240   # 초. 주기 재예열(ollama 독립 재구동 대응). 0 이하면 1회만

    # R19-1: 로컬 LLM 다중 백엔드 — 기본 provider 선택 (ollama|llamacpp|vllm)
    local_llm_provider: str = "ollama"
    llamacpp_base_url: str = "http://localhost:8180"   # llama.cpp server (OpenAI 호환)
    llamacpp_model: str = ""                            # 서버가 단일 모델 서빙 시 생략 가능
    vllm_base_url: str = "http://localhost:8100"        # vLLM OpenAI 호환 서버
    vllm_model: str = ""
    # R19-4: 히스토리 토큰 예산 (추정 토큰 초과 시 head/tail 축약) — 0 이하 = 무압축
    llm_context_budget: int = 8000
    # AI 어시스턴트 tool-call 최대 루프 횟수 (API 오류 자가수정 재시도 상한)
    llm_tool_max_rounds: int = 6

    # CORS — str 타입 유지: pydantic-settings가 list[str]에 json.loads를 시도해 crash하는 것 방지
    # 파싱은 main.py의 _parse_cors_origins()에서 수행 (JSON array OR 쉼표 구분 모두 지원)
    cors_origins: str = "http://localhost:4100"

    # Setup Wizard
    setup_completed: bool = False

    # Default admin (첫 구동 시 시드) — 미설정 시 생성 안 함
    default_admin_user_id: str | None = None
    default_admin_password: str | None = None

    # Agent 생성 UI 모드 제어: both | scaffold | upload
    agent_create_mode: str = "both"

    # MCP URL 외부 노출 호스트 (Docker/NAT 환경에서 host IP 명시)
    mcp_host: str = ""

    # MCP 서비스 인증 — Authorization 헤더 없는 MCP tools/call 처리 (#5)
    # 클라이언트가 x-api-key 헤더로 MCP_API_KEY 를 제시하면 MCP_AUTH_USER(tbl_users
    # 실계정)로 JWT(JWT_SECRET_KEY 서명)를 발급해 권한 부여. per-agent 는
    # tbl_mcp_configs.extra_args 의 `api_key:<키>` / `auth_user:<user_id>` 가 우선.
    mcp_api_key: str = ""    # MCP_API_KEY — 🔴 커밋 금지
    mcp_auth_user: str = ""  # MCP_AUTH_USER

    # Standalone Agent (F12)
    agent_standalone: bool = False
    agent_key: str = ""
    agent_port: int = 8001
    agent_base_url: str = "http://localhost:8001"
    agent_expose_protocol: str = ""  # "a2a,mcp" or ""

    # ── SeCMP 내장 에이전트 (F-MP / F-RAG / F-GRD / 멀티테넌시) ────────────────────
    # Vector 백엔드 (F-RAG, §7.5)
    vector_backend: str = "pgvector"          # pgvector | qdrant
    qdrant_url: str = "http://localhost:6333"  # VECTOR_BACKEND=qdrant 시 서버 URL (impl/57)
    qdrant_api_key: str = ""                    # Qdrant Cloud/보호형 배포 API 키(선택)
    qdrant_collection: str = "secmp_rag"        # 단일 컬렉션(청크=포인트, payload.collection_id 필터)

    # Marketplace 원격 레지스트리 (F-MP, §7.3)
    marketplace_remote_enabled: bool = False   # true 시 원격 카탈로그 병합 조회
    marketplace_host_mode: str = "onprem"      # onprem | saas
    marketplace_host_url: str = ""             # onprem: 사내 URL / saas: 제공사 URL
    marketplace_tenant_id: str = ""            # SaaS 멀티테넌시 테넌트 식별자
    marketplace_api_key: str = ""              # Bearer 인증 (시크릿 매니저 권장)
    marketplace_tls_verify: bool = True        # 사설 CA 사용 시 CA 번들 경로로 대체 가능
    marketplace_tls_ca_bundle: str = ""        # 사설 CA 번들 경로(서버 인증서 검증)
    marketplace_tls_client_cert: str = ""      # mTLS 클라이언트 인증서 경로(PEM)
    marketplace_tls_client_key: str = ""       # mTLS 클라이언트 키 경로(PEM)
    marketplace_gpg_pubkey_path: str = ""      # GPG 서명 검증용 공개키(armored) 경로
    marketplace_sync_interval_sec: int = 3600  # 카탈로그 캐시 갱신 주기(초)
    marketplace_install_verify_checksum: bool = True     # 다운로드 ZIP SHA256 검증 강제
    marketplace_install_require_signature: bool = False  # GPG 서명 검증(엔터프라이즈 옵션)

    # Marketplace-host 공개 카탈로그 API (§7.3.5) — 외부 SeCuardian 이 소비하는 host 측 인증키
    marketplace_host_api_key: str = ""  # 설정 시 Bearer 필수, 미설정 시 개방(폐쇄망 온프렘 기본)

    # 멀티테넌시 (§7.4)
    tenant_isolation_level: str = "off"        # off | namespace | physical
    tenant_db_strategy: str = "shared"         # shared | schema-per-tenant | db-per-tenant
    tenant_vector_strategy: str = "shared"     # shared | namespace-per-tenant | collection-per-tenant
    tenant_default_id: str = "default"

    # Workflow 엔진 (F-WF, §7.2)
    workflow_node_max_retries: int = 3   # 노드 실패 재시도 횟수 (max_attempts = +1)
    workflow_webhook_rate_limit_per_min: int = 30   # webhook 트리거 인메모리 rate limit(단일 프로세스, §7.2.4.1)

    # RAG (F-RAG, §7.5)
    rag_embedding_dim: int = 256   # 로컬 해싱 임베더 차원(오프라인/폐쇄망 기본, pgvector 확장 시 재검토)
    rag_rrf_k: int = 60            # RRF 융합 상수
    rag_default_top_k: int = 10

    # Guardrails 내장 에이전트 (F-GRD, §7.8) — wise-Guardrails MCP Server 연동
    guardrails_enabled: bool = True
    guardrails_mcp_url: str = "http://localhost:8080"
    guardrails_api_key: str = ""               # MCP_HTTP_AUTH=required 인 경우만 필요
    guardrails_default_domain: str = "global"  # 1차 실판정 도메인(§7.8.0), 나머지는 카탈로그 전용
    # 완전판정(LLM classifier, §7.8.7) — 기본 off·비결정적. on 시 /test 가 regex 후 LLM 으로 패러프레이즈 판정
    guardrails_classifier_enabled: bool = False
    guardrails_classifier_max_rules: int = 40   # 도메인당 LLM 메뉴 제시 규칙 수(비용/지연 제어)


settings = Settings()
