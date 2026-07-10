# AI Security Eval Gate — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **보안 주의**: `AI_EVAL_GATE_ENABLED` 기본값은 `false`입니다. 활성화 전 보안팀 승인이 필요합니다.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: AI Eval Gate 스텁 서비스 + AI 보안 평가 도구 (PyRIT / SkillSpector / agentshield)
- **컨테이너 이미지**: `python:3.12-slim` (런타임 stb 서버) + PyRIT 로컬 설치
- **구성 도구**:
  - [PyRIT](https://github.com/microsoft/pyrit) (Microsoft, MIT) — 프롬프트 인젝션·탈옥 취약점 평가
  - [SkillSpector](https://github.com/NVIDIA/SkillSpector) (NVIDIA, Apache-2.0) — AI 에이전트 스킬 취약점 스캔
  - [agentshield](https://github.com/affaan-m/agentshield) (MIT) — AI 에이전트 취약점 스캐너
- **에이전트 연결 방식**: 평가 도구 실행 결과를 `POST /api/ai-eval/scans`로 전송하면, 에이전트가 `AI_EVAL_URL`(기본: `http://localhost:9450`)로 집계하여 게이트 판정 수행

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 (configs 지원 필요) |
| Python | 3.10 이상 (PyRIT 로컬 실행 시) |
| `secuardian-internal` Docker network | `docker network create secuardian-internal` 로 사전 생성 필요 |
| 보안팀 승인 | `AI_EVAL_GATE_ENABLED=true` 설정 전 필수 |

---

## 3. 설치 (Install)

### 3-1. Compose 기동 (게이트 스텁 서버)

```bash
# Makefile 타겟 사용 (권장)
make ai-eval-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.ai-eval.yml up -d
```

### 3-2. PyRIT 로컬 설치 (평가 실행용)

```bash
pip install pyrit
# 평가 스크립트 실행 후 결과를 SeCuardian으로 전송
python scripts/pyrit_scan.py
# 결과 전송
curl -X POST http://localhost:8200/api/ai-eval/scans \
  -H "Content-Type: application/json" \
  -d '{"tool":"pyrit","severity":"high","target":"...","finding":"..."}'
```

### 3-3. 독립 설치 (플랫폼 저장소 없이)

```yaml
# ai-eval-standalone.yml
services:
  ai-eval-gate:
    image: python:3.12-slim
    container_name: ai-eval-gate
    restart: unless-stopped
    ports:
      - "127.0.0.1:8401:8401"
    environment:
      - AI_EVAL_PORT=8401
      - PYRIT_DBTYPE=duckdb
      - AI_EVAL_MIN_SEVERITY=${AI_EVAL_MIN_SEVERITY:-high}
    volumes:
      - ai_eval_data:/app/data
    command: ["sh", "-c", "pip install pyrit --quiet 2>/dev/null || true; python /app/health_stub.py"]
    networks:
      - secuardian-internal

volumes:
  ai_eval_data:

networks:
  secuardian-internal:
    external: true
```

```bash
docker compose -f ai-eval-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/ai-eval-gate/ai-eval-gate-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `AI_EVAL_GATE_ENABLED` | `false` | 게이트 판정 엔드포인트 활성화 (보안팀 승인 필요) |
| `AI_EVAL_URL` | `http://localhost:9450` | 외부 AI 평가 도구 base URL |

Worker 자체 환경 변수 (compose 파일 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `AI_EVAL_PORT` | `8401` | 게이트 스텁 서버 포트 |
| `PYRIT_DBTYPE` | `duckdb` | PyRIT 결과 저장 DB 유형 |
| `AI_EVAL_MIN_SEVERITY` | `high` | 게이트 실패 기준 최소 심각도 |

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make ai-eval-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/ai-eval/status | python3 -m json.tool

# Worker 직접 확인
curl -sf http://localhost:8401/

# 스캔 결과 조회
make ai-eval-scans
# 또는
curl -sf http://localhost:8200/api/ai-eval/scans | python3 -m json.tool
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
docker compose -f deploy/docker/docker-compose.ai-eval.yml logs -f

# 게이트 판정 요청 (AI_EVAL_GATE_ENABLED=true 설정 후)
curl -X POST http://localhost:8200/api/ai-eval/gate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"model_id":"my-llm-v1"}'

# Worker 중단
make ai-eval-down
# 또는
docker compose -f deploy/docker/docker-compose.ai-eval.yml down
```

---

## English Summary

**Worker**: `python:3.12-slim` stub server + PyRIT (Microsoft, MIT) / SkillSpector (NVIDIA, Apache-2.0) / agentshield (MIT) evaluation tools.

- **Start**: `make ai-eval-up` or `docker compose -f deploy/docker/docker-compose.ai-eval.yml up -d`
- **Port**: `127.0.0.1:8401` (gate stub health endpoint)
- **Network**: requires external `secuardian-internal` Docker network
- **Key env vars**: `AI_EVAL_GATE_ENABLED=false` (default, needs security-team approval to enable), `AI_EVAL_URL=http://localhost:9450`
- **Usage flow**: run PyRIT/SkillSpector/agentshield externally → POST results to `/api/ai-eval/scans` → call `POST /api/ai-eval/gate` for pass/fail verdict
- **Verify**: `curl http://localhost:8401/` and `make ai-eval-status`
- **Stop**: `make ai-eval-down`
