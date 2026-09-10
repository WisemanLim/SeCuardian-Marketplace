# Multi-Agent Registry Blueprint

대규모 멀티에이전트 플랫폼에서는 Agent Registry를 단순 주소록이 아니라 capability 기반 discovery, schema 검증, 상태 기반 라우팅, 보안 검증의 제어면으로 설계해야 한다.[cite:37][cite:61] Microsoft의 Multi-agent Reference Architecture는 Registry가 agent identity, metadata, status, version, tags를 중앙에서 관리하고 Orchestrator가 현재 작업에 가장 적합한 Agent를 검색하도록 설계해야 한다고 설명한다.[cite:37] AGNTCY ADS는 capability indexing과 content location을 분리하고, 계층형 taxonomy와 cryptographic signing을 통해 검증 가능한 discovery를 제공하는 구조를 제시한다.[cite:61][cite:74]

## Architecture blueprint

확장형 Registry의 권장 구조는 `control API + metadata store + capability index + lease/health plane + policy plane + discovery cache`의 6계층이다.[cite:37][cite:61] 이 구조는 정의 데이터와 동적 상태 데이터를 분리하여 stale registry, 잘못된 endpoint 선택, schema drift 같은 운영 문제를 줄이는 데 유리하다.[cite:37][cite:68]

### Core components

| Component | Responsibility | Resilience role |
|---|---|---|
| Registry API | 등록, 갱신, 검색, 비활성화 처리 [cite:37] | 입력 검증, optimistic concurrency |
| Metadata store | Agent 정의, 버전, 소유자, 정책 저장 [cite:37] | 정규화된 schema, 감사 추적 |
| Capability index | capability/tag/semantic 검색 [cite:61][cite:68] | 의미 기반 fallback discovery |
| Lease & health plane | heartbeat, TTL, probe, quarantine [cite:37] | stale endpoint 제거 |
| Policy plane | 호출자 권한, 데이터 등급, 지역 정책 [cite:37][cite:71] | 잘못된 호출 차단 |
| Discovery cache | Orchestrator의 단기 캐시 | lookup latency 절감, thundering herd 완화 |

### Schema-driven resilience

Schema-driven resilience의 핵심은 Agent를 자유 형식 JSON으로만 저장하지 않고, `identity schema`, `capability schema`, `endpoint schema`, `security schema`, `health schema`를 분리한 뒤 버전 관리하는 것이다.[cite:61][cite:74] 이 방식은 새 Agent가 등록될 때 계약 위반을 조기에 검출하고, 런타임에서는 capability mismatch, protocol mismatch, required auth 누락을 차단하는 데 효과적이다.[cite:37][cite:71]

권장 검증 흐름은 다음과 같다.

1. Agent Card JSON schema 검증.[cite:62][cite:71]
2. 필수 capability와 endpoint 프로토콜 검사.[cite:37][cite:62]
3. 인증 방식과 신원 문서 확인.[cite:71][cite:74]
4. active probe로 health endpoint 및 invoke endpoint 확인.[cite:37]
5. lease 발급 후 일정 주기 heartbeat 요구.[cite:37]
6. 미갱신 또는 probe 실패 시 quarantine 전이.[cite:37]

## Failure simulator

멀티에이전트 장애 시뮬레이터는 단순 부하 테스트보다 cascade scenario를 재현하는 데 초점을 맞춰야 한다. 대표적으로 `misroute cascade`, `registry staleness`, `retry storm`, `partial completion`, `reviewer bottleneck`, `tool timeout amplification` 시나리오를 넣는 것이 좋다.[cite:40][cite:47]

### Simulation scenarios

| Scenario | Injected fault | Expected breaker behavior |
|---|---|---|
| Misroute cascade | Router confidence 저하로 잘못된 Worker 선택 | Supervisor가 fallback route 또는 abort 선택 |
| Registry staleness | dead endpoint가 ready로 남아 있음 | lease expiry 또는 active probe 실패로 candidate 제거 |
| Retry storm | 하위 Agent timeout + 무제한 재시도 | circuit breaker open, retry budget 소진 후 degraded response |
| Partial completion | 5개 중 2개 하위 task 실패 | quorum 정책에 따라 partial artifact 반환 |
| Reviewer bottleneck | reviewer queue 적체 | reviewer bypass 금지, async finalize 또는 SLA timeout 적용 |
| MCP timeout amplification | 느린 tool server 다중 fan-out | per-tool timeout, bulkhead, cancellation propagation |

### Circuit-breaker verification

Circuit-breaker는 Agent 단위, capability 단위, endpoint 단위로 구분해 검증하는 것이 좋다. endpoint breaker는 개별 URL 장애를 격리하고, capability breaker는 특정 종류의 작업 전체를 잠시 제한하며, supervisor breaker는 fan-out 폭주 자체를 차단한다.[cite:40][cite:47]

검증 항목은 다음이 적절하다.

- Open 조건: 최근 N회 중 실패율, p95 latency, timeout 비율 초과.
- Half-open 조건: 제한된 probe 요청만 허용.
- Recovery 조건: 연속 성공 횟수 또는 SLA 회복 확인.
- Fallback 정책: 대체 Agent, degraded response, async completion 중 하나 선택.
- Blast radius 측정: breaker가 상위 orchestration 전체 장애를 얼마나 줄였는지 계산.

## PostgreSQL DDL guide

PostgreSQL 기반 Registry는 정의 테이블과 hot-state 테이블을 분리해야 한다. Microsoft 구조에서 Registry는 metadata와 status를 모두 다루지만, 실제 구현에서는 write pattern이 완전히 다르므로 분리하지 않으면 lock 경합과 vacuum 비용이 커진다.[cite:37]

### DDL principles

- 정의 데이터와 health/lease 데이터를 분리한다.[cite:37]
- JSONB는 확장 필드에만 사용하고, 자주 조회하는 조건은 컬럼으로 승격한다.
- capability 검색은 `GIN(tsvector)`와 `pgvector`를 병행하는 것이 유리하다.[cite:61][cite:68]
- endpoint 우선순위, auth mode, region scope는 별도 컬럼으로 관리한다.
- audit과 health history는 append-only 테이블로 분리한다.

### Recommended DDL

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agents (
  agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  agent_type TEXT NOT NULL CHECK (agent_type IN ('orchestrator','supervisor','worker','reviewer','knowledge','execution','gateway','tool-proxy')),
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('draft','active','quarantined','retired')),
  owner_team TEXT NOT NULL,
  owner_contact TEXT,
  home_region TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_versions (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  semver TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  model_ref TEXT,
  prompt_ref TEXT,
  image_ref TEXT,
  is_active BOOLEAN NOT NULL DEFAULT FALSE,
  manifest JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(agent_id, semver)
);

CREATE TABLE agent_capabilities (
  capability_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  capability_key TEXT NOT NULL,
  verb TEXT NOT NULL,
  domain TEXT NOT NULL,
  description TEXT NOT NULL,
  input_schema JSONB NOT NULL,
  output_schema JSONB NOT NULL,
  qos JSONB,
  embedding VECTOR(1536),
  search_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(capability_key,'') || ' ' || coalesce(domain,'') || ' ' || coalesce(description,''))
  ) STORED,
  UNIQUE(agent_id, capability_key)
);

CREATE INDEX idx_agent_capabilities_tsv ON agent_capabilities USING GIN(search_tsv);

CREATE TABLE agent_endpoints (
  endpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  protocol TEXT NOT NULL CHECK (protocol IN ('https','grpc','a2a','mcp','nats')),
  url TEXT NOT NULL,
  auth_mode TEXT NOT NULL CHECK (auth_mode IN ('mtls','oauth2','jwt','workload-identity','none')),
  auth_ref TEXT,
  region TEXT,
  priority INT NOT NULL DEFAULT 100,
  timeout_ms INT NOT NULL DEFAULT 10000,
  concurrency_limit INT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE(agent_id, protocol, url)
);

CREATE TABLE agent_security_profiles (
  agent_id UUID PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  data_classification TEXT NOT NULL,
  pii_scope TEXT NOT NULL,
  approval_required BOOLEAN NOT NULL DEFAULT FALSE,
  allowed_callers JSONB,
  allowed_regions JSONB,
  secrets_profile JSONB,
  trust_attestation JSONB
);

CREATE TABLE agent_health_current (
  agent_id UUID PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  serving_status TEXT NOT NULL CHECK (serving_status IN ('ready','degraded','down','quarantined')),
  health_score NUMERIC(5,4) NOT NULL DEFAULT 1.0000,
  p95_latency_ms INT,
  error_rate NUMERIC(8,5),
  inflight_requests INT,
  last_heartbeat_at TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,
  last_probe_status TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_health_history (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  serving_status TEXT NOT NULL,
  health_score NUMERIC(5,4) NOT NULL,
  p95_latency_ms INT,
  error_rate NUMERIC(8,5),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_leases (
  lease_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  renewable BOOLEAN NOT NULL DEFAULT TRUE,
  lease_nonce TEXT NOT NULL,
  UNIQUE(agent_id)
);

CREATE TABLE agent_tags (
  agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  tag_key TEXT NOT NULL,
  tag_value TEXT NOT NULL,
  PRIMARY KEY(agent_id, tag_key, tag_value)
);

CREATE TABLE agent_relationships (
  parent_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  child_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('supervises','reviews','fallback-for','depends-on','owns-tool')),
  PRIMARY KEY(parent_agent_id, child_agent_id, relation_type)
);

CREATE TABLE discovery_audit_log (
  id BIGSERIAL PRIMARY KEY,
  caller_agent_id UUID,
  query JSONB NOT NULL,
  matched_agents JSONB NOT NULL,
  decision_reason JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Scaling notes

파티셔닝이 필요한 첫 후보는 `agent_health_history`와 `discovery_audit_log`이다. 둘은 쓰기량이 크고 기간 기반 보존 정책이 잘 맞기 때문에 월 단위 range partition이 적합하다. capability가 수십만 건 이상으로 늘어나면 `agent_capabilities`를 domain 단위로 샤딩하거나 읽기 전용 검색 인덱스를 별도 서비스로 분리하는 편이 안전하다.[cite:61][cite:68]

## Standard Agent Card JSON schema

표준 Agent Card는 A2A와 MCP 양쪽을 포괄해야 하므로 `identity`, `capabilities`, `endpoints`, `security`, `interaction`, `tools/mcp`, `artifacts`, `governance` 블록으로 나누는 것이 좋다. A2A discovery 문서는 agent card 기반 discovery를 전제로 하며, MCP는 tools, resources, prompts 같은 노출 객체와 인증 메커니즘이 중요하다.[cite:62][cite:71]

### Required sections

| Section | Purpose |
|---|---|
| `identity` | agent 고유 식별자, 이름, 소유 조직 |
| `version` | card schema와 agent 구현 버전 |
| `capabilities` | 수행 가능한 작업 단위, 입출력 schema |
| `endpoints` | A2A, HTTPS, gRPC, MCP endpoint 목록 |
| `security` | auth 방식, mTLS/OAuth/JWT, trust claims |
| `interaction` | sync/async, callback, streaming 지원 여부 |
| `mcp` | tools/resources/prompts 노출 정보 |
| `governance` | data class, approval, audit, policy labels |
| `observability` | health, metrics, trace propagation 규칙 |

### JSON Schema outline

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/agent-card.schema.json",
  "title": "Agent Card",
  "type": "object",
  "required": ["identity", "version", "capabilities", "endpoints", "security"],
  "properties": {
    "identity": {
      "type": "object",
      "required": ["agent_id", "name", "organization"],
      "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "organization": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}}
      }
    },
    "version": {
      "type": "object",
      "required": ["card_schema_version", "agent_version"],
      "properties": {
        "card_schema_version": {"type": "string"},
        "agent_version": {"type": "string"},
        "model_ref": {"type": "string"}
      }
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["key", "verb", "domain", "input_schema", "output_schema"],
        "properties": {
          "key": {"type": "string"},
          "verb": {"type": "string"},
          "domain": {"type": "string"},
          "description": {"type": "string"},
          "input_schema": {"type": "object"},
          "output_schema": {"type": "object"},
          "qos": {"type": "object"}
        }
      }
    },
    "endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["protocol", "url", "auth_mode"],
        "properties": {
          "protocol": {"enum": ["https", "grpc", "a2a", "mcp"]},
          "url": {"type": "string", "format": "uri"},
          "auth_mode": {"enum": ["mtls", "oauth2", "jwt", "workload-identity", "none"]},
          "timeout_ms": {"type": "integer"},
          "region": {"type": "string"}
        }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "mtls_required": {"type": "boolean"},
        "oauth_scopes": {"type": "array", "items": {"type": "string"}},
        "signed_attestation": {"type": "string"},
        "allowed_callers": {"type": "array", "items": {"type": "string"}}
      }
    },
    "interaction": {
      "type": "object",
      "properties": {
        "supports_sync": {"type": "boolean"},
        "supports_async": {"type": "boolean"},
        "supports_streaming": {"type": "boolean"},
        "callback_url": {"type": "string", "format": "uri"}
      }
    },
    "mcp": {
      "type": "object",
      "properties": {
        "tools": {"type": "array", "items": {"type": "object"}},
        "resources": {"type": "array", "items": {"type": "object"}},
        "prompts": {"type": "array", "items": {"type": "object"}}
      }
    },
    "governance": {
      "type": "object",
      "properties": {
        "data_classification": {"type": "string"},
        "human_approval_required": {"type": "boolean"},
        "audit_level": {"type": "string"}
      }
    }
  }
}
```

### Example Agent Card

```json
{
  "identity": {
    "agent_id": "agent-legal-reviewer-01",
    "name": "LegalReviewSupervisor",
    "organization": "example-corp",
    "description": "Supervises legal analysis, clause extraction, and compliance review tasks",
    "tags": ["legal", "review", "supervisor"]
  },
  "version": {
    "card_schema_version": "1.0.0",
    "agent_version": "2.3.1",
    "model_ref": "gpt-5-class"
  },
  "capabilities": [
    {
      "key": "contract-risk-review",
      "verb": "review",
      "domain": "legal.contract",
      "description": "Assess contractual clauses and produce structured risk findings",
      "input_schema": {"type": "object"},
      "output_schema": {"type": "object"},
      "qos": {"max_latency_ms": 8000, "supports_async": true}
    }
  ],
  "endpoints": [
    {
      "protocol": "a2a",
      "url": "https://legal-review.example.com/a2a",
      "auth_mode": "mtls",
      "timeout_ms": 10000,
      "region": "ap-northeast-2"
    },
    {
      "protocol": "mcp",
      "url": "https://legal-review.example.com/mcp",
      "auth_mode": "oauth2",
      "timeout_ms": 10000,
      "region": "ap-northeast-2"
    }
  ],
  "security": {
    "mtls_required": true,
    "oauth_scopes": ["agent.invoke", "agent.read"],
    "signed_attestation": "sigstore://bundle/example",
    "allowed_callers": ["agent-orchestrator-core", "agent-supervisor-legal"]
  },
  "interaction": {
    "supports_sync": true,
    "supports_async": true,
    "supports_streaming": false,
    "callback_url": "https://legal-review.example.com/callback"
  },
  "mcp": {
    "tools": [
      {"name": "search_clause_library", "description": "Search internal clause library"}
    ],
    "resources": [
      {"name": "policy_manual", "uri": "resource://policy-manual"}
    ],
    "prompts": [
      {"name": "risk_review_system", "description": "Standard legal review prompt"}
    ]
  },
  "governance": {
    "data_classification": "confidential",
    "human_approval_required": true,
    "audit_level": "full"
  }
}
```

## Implementation recommendations

초기 단계에서는 중앙 PostgreSQL Registry로 시작하되, capability 규모와 조직 경계가 커지면 AGNTCY ADS 같은 content-addressed 또는 federation-friendly 모델을 참고해 계층형 디렉터리로 확장하는 것이 현실적이다.[cite:61][cite:72][cite:74] 또한 A2A discovery와 MCP metadata를 하나의 Agent Card로 통합하더라도, 런타임 transport와 정책 집행은 gateway 계층에서 분리하는 편이 운영상 안전하다.[cite:62][cite:71]
