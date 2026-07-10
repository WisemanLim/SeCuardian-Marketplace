# Agentic SOC Platform — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: `secuardian/agentic-soc` (기반: [FunnyWolf/agentic-soc-platform](https://github.com/FunnyWolf/agentic-soc-platform), MIT 라이선스)
- **역할**: 보안 에이전트들을 A2A(Agent-to-Agent) 메시징으로 오케스트레이션하고, 인시던트 트리아지와 플레이북을 실행하는 플랫폼
- **에이전트 연결 방식**: SeCuardian이 `SECUARDIAN_BASE_URL` 환경변수를 통해 A2A 에이전트 카드를 광고하고, worker는 포트 `8400`에서 A2A/REST 요청을 처리합니다
- **주의**: 공식 Docker 이미지가 배포되지 않으므로 **로컬 빌드가 필수**입니다

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| Git | 로컬 빌드용 |
| `secuardian-internal` Docker network | `docker network create secuardian-internal` 로 사전 생성 필요 |
| TheHive (선택) | SOAR 연동 시 필요 |
| Wazuh (선택) | SIEM 연동 시 필요 |

---

## 3. 설치 (Install)

### 3-1. 이미지 로컬 빌드 (필수)

```bash
git clone https://github.com/FunnyWolf/agentic-soc-platform
cd agentic-soc-platform
docker build -t secuardian/agentic-soc:0.1.0 .
```

Makefile 타겟을 사용하면 동일한 가이드 출력과 함께 빌드를 시도합니다:

```bash
make agentic-soc-build
```

### 3-2. Worker 기동

```bash
# SeCuardian 저장소 루트에서 실행 (권장)
make agentic-soc-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.agentic-soc.yml up -d
```

### 3-3. 독립 설치 (플랫폼 저장소 없이)

이미지를 로컬 빌드한 뒤 아래 compose를 별도 디렉터리에 저장하고 실행합니다:

```yaml
# agentic-soc-standalone.yml
services:
  agentic-soc:
    image: secuardian/agentic-soc:0.1.0
    container_name: agentic-soc
    restart: unless-stopped
    ports:
      - "127.0.0.1:8400:8400"
    environment:
      - PORT=8400
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - THEHIVE_URL=${THEHIVE_URL:-http://thehive:9000}
      - THEHIVE_API_KEY=${THEHIVE_API_KEY:-}
      - WAZUH_API_URL=${WAZUH_API_URL:-https://wazuh:55000}
      - WAZUH_API_USER=${WAZUH_API_USER:-wazuh}
      - WAZUH_API_PASSWORD=${WAZUH_API_PASSWORD:-}
    volumes:
      - agentic_soc_data:/app/data
    networks:
      - secuardian-internal

volumes:
  agentic_soc_data:

networks:
  secuardian-internal:
    external: true
```

```bash
docker compose -f agentic-soc-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/agentic-soc/agentic-soc-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `AGENTIC_SOC_ENABLED` | `true` | Agentic SOC 활성화 여부 |
| `AGENTIC_SOC_FINDINGS_MAX` | `1000` | 메모리에 유지할 최대 findings 수 (deque maxlen) |
| `SECUARDIAN_BASE_URL` | `http://localhost:8200` | SeCuardian 플랫폼 URL (A2A 에이전트 카드에 광고됨) |

Worker 자체 연결 환경 변수 (compose 파일 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `OPENAI_API_KEY` | (없음) | OpenAI LLM 연동 키 |
| `ANTHROPIC_API_KEY` | (없음) | Anthropic LLM 연동 키 |
| `THEHIVE_URL` | `http://thehive:9000` | TheHive SOAR URL |
| `THEHIVE_API_KEY` | (없음) | TheHive API 키 |
| `WAZUH_API_URL` | `https://wazuh:55000` | Wazuh API URL |
| `WAZUH_API_USER` | `wazuh` | Wazuh API 사용자명 |
| `WAZUH_API_PASSWORD` | (없음) | Wazuh API 비밀번호 |

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make agentic-soc-status

# 직접 curl 확인 (SeCuardian 에이전트 API 통해)
curl -sf http://localhost:8200/api/agentic-soc/status | python3 -m json.tool

# Worker 직접 확인
curl -sf http://localhost:8400/status

# A2A 에이전트 카드 확인
curl -sf http://localhost:8400/.well-known/agent.json | python3 -m json.tool

# 플레이북 목록 확인
make agentic-soc-playbooks
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
make agentic-soc-logs
# 또는
docker compose -f deploy/docker/docker-compose.agentic-soc.yml logs -f

# 인시던트 목록 조회
make agentic-soc-incidents

# 플레이북 목록 조회
make agentic-soc-playbooks

# Worker 중단
make agentic-soc-down
# 또는
docker compose -f deploy/docker/docker-compose.agentic-soc.yml down
```

---

## English Summary

**Worker**: `secuardian/agentic-soc:0.1.0` (based on FunnyWolf/agentic-soc-platform, MIT). No official image published — local build required.

- **Build**: `git clone https://github.com/FunnyWolf/agentic-soc-platform && docker build -t secuardian/agentic-soc:0.1.0 .`
- **Start**: `make agentic-soc-up` or `docker compose -f deploy/docker/docker-compose.agentic-soc.yml up -d`
- **Port**: `127.0.0.1:8400` (A2A + REST API)
- **Network**: requires external `secuardian-internal` Docker network
- **Key env vars for SeCuardian**: `AGENTIC_SOC_ENABLED=true`, `AGENTIC_SOC_FINDINGS_MAX=1000`, `SECUARDIAN_BASE_URL=http://localhost:8200`
- **Worker env vars**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `THEHIVE_URL`, `THEHIVE_API_KEY`, `WAZUH_API_URL`, `WAZUH_API_USER`, `WAZUH_API_PASSWORD`
- **Verify**: `curl http://localhost:8400/.well-known/agent.json`
- **Stop**: `make agentic-soc-down`
