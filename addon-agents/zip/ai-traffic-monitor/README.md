# AI 트래픽 모니터 (`ai-traffic-monitor`)

> 🌐 [English](./README.en.md) · SeCuardian Addon Agent (순수 ADDON, `emb_` 없음)
> PRD: [../../.docs/PRD-ai-traffic-monitor.md](../../.docs/PRD-ai-traffic-monitor.md)
> 근거: [브라우저 AI 도우미 트래픽 모니터링 조사](../../.docs/Perplexity-브라우저%20등에서%20자동으로%20연결되는%20AI%20도우미와의%20대화시의%20트래픽.md)

## 개요

브라우저에 자동 연결되는 AI 도우미(Perplexity·Gemini·ChatGPT·Claude·Copilot)의 **대화 내용이 아닌
트래픽 사용량(바이트/패킷)** 을 CLI 도구로 정량 측정한다. Shadow-AI 사용 현황 관측용.

- `agent_type`: `service` · governance: `human_approval_required=true`, `audit_level=high`
- 화면 없음 → AI 어시스턴트 Q&A / capability 라우팅으로 사용
- 마운트: `/api/addon/ai-traffic-monitor/...`

## 아키텍처 (문서 3단 구성 래핑)

| 계층 | 도구 | 용도 |
|------|------|------|
| 인터페이스 누적 | `vnstat --json` | 일/월/총 사용량 |
| 프로세스 순간 | `nethogs -t` | 브라우저 프로세스별 송/수신 |
| 목적지 집계 | `dig` → `tcpdump` → `tshark` | AI IP HTTPS 트래픽 바이트/패킷 |

모든 실행은 **shell=False + 내부 조립 argv**, 바이너리 allowlist(`dig getent vnstat nethogs tcpdump tshark`),
입력 검증(정규식·ipaddress·경로 봉쇄). 도구 미설치 시 **503 + 설치 안내**.

## 엔드포인트

| Method | Path | 권한 | 설명 |
|--------|------|------|------|
| GET | `/status` | 로그인 | 도구 가용성 + 설정 요약 |
| GET | `/domains` | 로그인 | AI 도메인 카탈로그 |
| POST | `/resolve` | 로그인 | 도메인 → IP 집합 |
| GET | `/usage` | 로그인 | vnstat 누적 사용량 |
| POST | `/snapshot` | supervisor/admin | nethogs N초 프로세스 스냅샷 |
| POST | `/capture` | supervisor/admin | AI IP tcpdump N초 → tshark 집계 |
| POST | `/analyze` | supervisor/admin | 기존 pcap 재집계 |
| GET | `/config` | supervisor/admin | 환경변수 조회 |

## 환경변수 (모두 선택)

| Key | 기본값 | 설명 |
|-----|--------|------|
| `AITM_INTERFACE` | `eth0` | 대상 NIC |
| `AITM_DOMAINS` | (내장 카탈로그) | CSV 오버라이드 |
| `AITM_CAPTURE_DIR` | `/tmp/ai-traffic` | pcap 저장 경로(봉쇄 루트) |
| `AITM_MAX_CAPTURE_SEC` | `60` | 캡처 최대 초 |
| `AITM_MAX_SNAPSHOT_SEC` | `30` | 스냅샷 최대 초 |

> 설정 위치: 상세 주석은 repo root `.env.example` 참조. `.env.local`(호스트 직접 실행) = `en0`,
> `.env.dev`/`.env.staging`/`.env.prod`(Docker) = `eth0` 로 최소 적용되어 있다. 나머지 선택 변수는
> 필요 시에만 추가(미기재 시 코드 기본값).

## 배포 / 실행

1. 에이전트 관리 → 새 Agent → **ZIP 업로드** → `zip/ai-traffic-monitor.zip`
2. `/api/addon/ai-traffic-monitor` 로 즉시 핫 디플로이

> ⚠️ `snapshot`/`capture` 는 raw 패킷 접근으로 **root** 또는 `CAP_NET_RAW`/`CAP_NET_ADMIN` 필요.
> 컨테이너 배포 시 해당 capability 부여 또는 호스트 네트워크 모드 검토.

## API 예시

```bash
# 도구 가용성
curl -s /api/addon/ai-traffic-monitor/status
# → {"tools":{"dig":true,"tcpdump":true,"vnstat":false,...},"all_available":false,...}

# 도메인 → IP 해석
curl -s -X POST /api/addon/ai-traffic-monitor/resolve \
  -H 'Content-Type: application/json' -d '{"domains":["claude.ai"]}'
# → {"resolved":{"claude.ai":["160.79.104.10"]},"unique_ips":[...],"ip_count":1}

# 30초 캡처 + 집계 (supervisor/admin, root)
curl -s -X POST /api/addon/ai-traffic-monitor/capture \
  -H 'Content-Type: application/json' -d '{"seconds":30}'
# → {"packets":842,"bytes":1183920,"pcap":"/tmp/ai-traffic/aitm-eth0-30s-9ips.pcap",...}
```

## 테스트

```bash
python3 test/impl/51/run_test.py    # repo root 에서 실행 → 10/10 PASS
```

**통합 시험**: `./ITManually.sh 13` (또는 대화형 메뉴 13번) — zip 업로드 후 `status`/`domains`/`resolve`/`usage`
API + Frontend(AI 어시스턴트) 라우팅을 점검한다. 미리보기: `DRYRUN=1 ./ITManually.sh 13`.
가이드: [.docs/ITManually.md](../../../.docs/ITManually.md).

## 트러블슈팅

| 증상 | 원인/해결 |
|------|-----------|
| `/usage` 503 | `vnstat` 미설치/미구성 → 설치 후 `vnstat --add -i <iface>` + 데몬 기동(Linux `systemctl enable --now vnstat`, macOS `brew services start vnstat`). 데이터 누적까지 수 분. DB/데몬 미준비는 502 아닌 503(graceful) 로 안내 |
| `/chat` 질의가 존재하지 않는 path(`/interface/eth0/usage` 등)를 호출해 404 | Ollama 가 query 파라미터(`?interface=`)를 모르고 REST 관례를 추측 — 플랫폼 결함(orchestrator `_openapi_endpoint_lines`), impl/54 에서 수정. 수정 후 백엔드 재기동 시 해결(addon 재업로드 불필요) |
| `/capture` pcap 미생성 | root/capability 부족 또는 잘못된 interface(`/status` 확인) |
| resolve IP 비어있음 | CDN/DoH 환경 — 재시도 또는 `AITM_DOMAINS` 조정 |

## 다음 단계 (PRD §7)

- tshark 집계 → Prometheus textfile exporter(`ai_domain_bytes_total{domain=}`) → Grafana
- ring buffer 장기 캡처, DNS+TLS SNI 상관분석
- `-front.tsx` 도메인별 사용량 대시보드
