# AI Red Team — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(실제 작업 수행 도구)가 설치되어야 동작합니다.
> This agent requires an external worker to be installed before it can function.

> **격리 필수**: 이 worker는 `redteam-isolated` 네트워크(외부 인터넷 차단)에서만 실행해야 합니다.
> 실행 전 `deploy/config/redteam/approval-checklist.md` 서면 승인이 **반드시** 필요합니다.

---

## 1. Worker 개요 (What the worker is)

- **도구 이름**: [pentagi](https://github.com/vxcontrol/pentagi) v0.5.0 (vxcontrol, MIT 라이선스)
- **역할**: MITRE ATT&CK 기반 자율 AI 침투 테스트 에이전트. LLM 탈옥, 프롬프트 인젝션, 데이터 유출 등 적대적 스캔 수행
- **에이전트 연결 방식**:
  - `REDTEAM_ENABLED=true` 설정 시 에이전트 엔드포인트 활성화
  - `REDTEAM_NETWORK=redteam-isolated` 설정 시 네트워크 격리 강제
  - `PYRIT_ENDPOINT` / `SKILLSPECTOR_URL` 미설정 시 mock 모드로 동작
- **격리 네트워크**: `redteam-isolated` (bridge, internal=true, 외부 인터넷 차단, subnet: `172.30.0.0/24`)

---

## 2. 요구 사항 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|-------------|
| Docker Engine | 24.0 이상 |
| Docker Compose | v2.20 이상 |
| 서면 승인 | `deploy/config/redteam/approval-checklist.md` 완료 필수 |
| 격리 네트워크 | `redteam-isolated` (compose가 자동 생성) |
| LLM API 키 | Vault에서 주입 (하드코딩 금지) |
| 실행 환경 | 격리 스테이징 환경 전용 — 프로덕션 금지 |

---

## 3. 설치 (Install)

### 3-1. 사전 승인 체크리스트 확인

```bash
# 승인 체크리스트 내용 확인
make redteam-checklist
# 또는
cat deploy/config/redteam/approval-checklist.md
```

### 3-2. Worker 기동

```bash
# Makefile 타겟 사용 (승인 여부 안내 포함, 권장)
make redteam-up

# 또는 직접 Compose 실행
docker compose -f deploy/docker/docker-compose.redteam.yml up -d
```

### 3-3. 독립 설치 (플랫폼 저장소 없이)

```yaml
# redteam-standalone.yml
# ⚠️ 격리 네트워크(internal: true) — 외부 인터넷 차단 필수
services:
  pentagi:
    image: ghcr.io/vxcontrol/pentagi:v0.5.0
    container_name: secuardian-pentagi
    restart: "no"
    ports:
      - "127.0.0.1:8088:8088"
    volumes:
      - pentagi-data:/app/data
      - ./config/redteam:/app/config:ro
    environment:
      PENTAGI_CONFIG: /app/config/pentagi.yaml
      # ANTHROPIC_API_KEY: Vault에서 주입 — 하드코딩 금지
    networks:
      - redteam-isolated

volumes:
  pentagi-data:

networks:
  redteam-isolated:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: "172.30.0.0/24"
```

```bash
docker compose -f redteam-standalone.yml up -d
```

---

## 4. SeCuardian 연동 설정 (Wire-up)

SeCuardian `.env` 파일에 아래 변수를 설정합니다 (`addon-agents/zip/ai-redteam/ai-redteam-meta.json` 기준):

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `REDTEAM_ENABLED` | `false` | `true`로 설정해야 모든 엔드포인트 활성화 (필수) |
| `REDTEAM_NETWORK` | (없음) | `redteam-isolated`로 반드시 설정 — 네트워크 격리 강제 |
| `PYRIT_ENDPOINT` | (없음) | PyRIT 서비스 base URL. 미설정 시 mock 모드 |
| `PYRIT_API_KEY` | (없음) | PyRIT 엔드포인트 인증 API 키 |
| `SKILLSPECTOR_URL` | (없음) | SkillSpector 서비스 URL. 미설정 시 mock 모드 |

---

## 5. 확인 (Verify)

```bash
# Makefile 타겟 사용
make redteam-status

# SeCuardian 에이전트 API 통해 확인
curl -sf http://localhost:8200/api/redteam/status | python3 -m json.tool

# pentagi UI 접근 (localhost 전용)
# 브라우저에서: http://localhost:8088

# 격리 네트워크 확인
docker network inspect secuardian_redteam_isolated
```

---

## 6. 운영·중단 (Operate / Stop)

```bash
# 로그 스트리밍
docker compose -f deploy/docker/docker-compose.redteam.yml logs -f

# LLM 적대적 스캔 실행 (REDTEAM_ENABLED=true 필요)
curl -X POST http://localhost:8200/api/redteam/scan/llm \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"target_url":"http://staging-llm:8000","strategy":"jailbreak"}'

# Worker 중단 (restart: "no" — 자동 재시작 없음)
make redteam-down
# 또는
docker compose -f deploy/docker/docker-compose.redteam.yml down
```

---

## English Summary

**Worker**: [pentagi](https://github.com/vxcontrol/pentagi) v0.5.0 (vxcontrol, MIT) — MITRE ATT&CK-based autonomous AI pen-test agent.

- **Critical**: written approval via `deploy/config/redteam/approval-checklist.md` required before starting
- **Start**: `make redteam-up` or `docker compose -f deploy/docker/docker-compose.redteam.yml up -d`
- **Port**: `127.0.0.1:8088` (pentagi UI, localhost-only)
- **Network**: `redteam-isolated` bridge with `internal: true` (no outbound internet), subnet `172.30.0.0/24`
- **Key env vars**: `REDTEAM_ENABLED=true` (required), `REDTEAM_NETWORK=redteam-isolated` (required), `PYRIT_ENDPOINT`, `PYRIT_API_KEY`, `SKILLSPECTOR_URL` (all optional; mock mode if unset)
- **LLM API key**: must be injected via Vault — never hardcoded
- **Verify**: `make redteam-status` or `curl http://localhost:8200/api/redteam/status`
- **Stop**: `make redteam-down` (restart policy is "no" — no auto-restart)
