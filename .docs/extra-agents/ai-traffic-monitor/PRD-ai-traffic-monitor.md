# PRD — AI Traffic Monitor Addon Agent (`ai-traffic-monitor`)

> 근거 문서 / Source: [Perplexity-브라우저 등에서 자동으로 연결되는 AI 도우미와의 대화시의 트래픽.md](./Perplexity-브라우저%20등에서%20자동으로%20연결되는%20AI%20도우미와의%20대화시의%20트래픽.md)
> 대상 / Target: `addon-agents/zip/ai-traffic-monitor/` (순수 ADDON, `emb_` 접두사 없음 — 내장 유래 아님)
> 유형 / Type: `service` (CLI 래핑 모니터링, 화면 없음 → AI 어시스턴트 Q&A)

---

## 1. 배경 / Why

크롬·엣지 등 브라우저에 자동 연결되는 AI 도우미(Perplexity, Gemini-in-Chrome, ChatGPT,
Claude, Copilot)는 사용자 의식 없이 외부로 트래픽을 발생시킨다. SeCuardian 관점에서
**"대화 내용"이 아니라 "사용량(트래픽량)"** 을 정량 측정해 Shadow-AI 사용 현황을 관측하는
것이 목표다. 근거 문서가 정리한 CLI 도구 3단 구성을 에이전트로 래핑한다.

- 프로세스 기준: `nethogs` (브라우저 프로세스 순간 대역폭)
- 인터페이스 누적: `vnstat` (일/월/시간 집계, `--json`)
- 목적지 기준: `dig`→IP 해석 → `tcpdump` 캡처 → `tshark` 바이트/패킷 집계

**비목표 / Non-goals**: 평문 payload 복호화, 대화 내용 수집, TLS MITM, 장기 pcap 보관,
Prometheus/Grafana exporter(문서 §7 — 차기 이터레이션으로 이관).

## 2. 사용자 / Who

- SOC/보안 운영자 (supervisor/admin): 캡처·프로세스 스냅샷 등 특권 작업 수행.
- 일반 로그인 사용자: 도구 가용성·도메인 카탈로그·인터페이스 누적 사용량 조회(읽기).
- AI 어시스턴트(Orchestrator): capability 라우팅으로 "AI 트래픽 얼마나 썼어?" 질의 응답.

## 3. 범위 / Scope (이번 이터레이션)

마운트: `/api/addon/ai-traffic-monitor/...` (동적 로더가 `router` 를 prefix 없이 마운트)

| # | Method | Path | 권한 | 설명 |
|---|--------|------|------|------|
| 1 | GET | `/status` | 로그인 | 도구 가용성(`which`) + 설정 요약 |
| 2 | GET | `/domains` | 로그인 | AI 도우미 도메인 카탈로그(env 설정 가능) |
| 3 | POST | `/resolve` | 로그인 | 도메인 → IP 집합 해석(`dig`, fallback `getent`) |
| 4 | GET | `/usage` | 로그인 | `vnstat --json` 인터페이스 누적 사용량(일/월/총) |
| 5 | POST | `/snapshot` | supervisor/admin | `nethogs -t` N초 스냅샷 → 프로세스별 송/수신 |
| 6 | POST | `/capture` | supervisor/admin | AI IP 필터 `tcpdump` N초 캡처 → `tshark` 바이트/패킷 집계 |
| 7 | POST | `/analyze` | supervisor/admin | 기존 pcap 을 `tshark` 로 재집계(바이트/패킷/IO stat) |
| 8 | GET | `/config` | supervisor/admin | 환경변수 설정 조회(시크릿 없음) |

### 도메인 기본 카탈로그
`perplexity.ai`, `www.perplexity.ai`, `gemini.google.com`,
`generativelanguage.googleapis.com`, `chatgpt.com`, `chat.openai.com`,
`api.openai.com`, `claude.ai`, `api.anthropic.com`, `copilot.microsoft.com`.
→ `AITM_DOMAINS`(CSV)로 오버라이드.

## 4. 비기능 / NFR · 보안

`ShellAgent` 실행 안전 모델 준용:
- 모든 외부 실행은 **`shell=False`** + 내부 조립 argv(사용자 자유 문자열 실행 금지).
- 바이너리 allowlist: `dig getent vnstat nethogs tcpdump tshark`.
- **입력 검증**: interface `^[A-Za-z0-9._-]{1,32}$`, domain `^[A-Za-z0-9.-]{1,253}$`,
  IP 는 `ipaddress` 로 파싱, `seconds` 클램프 `[1, AITM_MAX_CAPTURE_SEC]`.
- **경로 봉쇄**: pcap 경로는 `AITM_CAPTURE_DIR` 하위 + `.pcap`/`.pcapng` 만 허용(경로 탈출 차단).
- 타임아웃(작업별), 출력 캡(64KB), 특권 작업(capture/snapshot/analyze/config)은 `require_role`.
- 도구 미설치 시 **우아한 저하**: 503 + 명확한 안내(설치 명령 포함). macOS 개발환경에서도 안전.
  - **설치됐으나 미구성**(vnstat DB/데몬 없음·인터페이스 미등록)도 동일하게 503 + 구성 안내로 저하 —
    502(오케스트레이터 "API 오류")로 어시스턴트가 중단되지 않도록 실패 메시지를 분류(§6.1-impl53).
- ⚠️ `from __future__ import annotations` 금지(동적 로더 pydantic 이슈).

## 5. 성공 지표 / Success

- `GET /status` 가 각 도구 설치 여부를 정확히 반환(macOS: dig/tshark 유, nethogs/vnstat 무 가능).
- `POST /resolve` 가 실제 도메인의 IP 집합을 반환하거나 도구 부재 시 503.
- 미설치 도구 호출 시 500 아닌 503 + 안내.
- 잘못된 interface/domain/seconds/pcap 경로 입력 시 400/403 (인젝션·경로탈출 차단).
- `make`/py_compile 문법 검증 통과, `router` export 확인, zip 패키징 성공.

## 6. 산출물 / Deliverables

- `ai-traffic-monitor-app.py` — FastAPI `router` (8 엔드포인트)
- `ai-traffic-monitor-meta.json` — `service`, capabilities(query/inspect/capture), governance=high
- `ai-traffic-monitor.zip` — flat 패키지
- `test/impl/51/{scenario,result}.md` — 시험 시나리오·결과 (repo root `test/`)
- README(한/영) 갱신 — addon-agents/README.md 내장/ADDON 목록에 추가
- **통합 시험 배치** — `ITManually.sh` Batch 13 + `.docs/ITManually.md` (아래 §6.1)

### 6.1 통합 시험 배치 / Integration test batch (ITManually)

`ITManually.sh` 에 **Batch 13 — AI Traffic Monitor** 추가. SeCuardian 통합 시험 도우미로
이 ADDON 을 CLI+Frontend 로 점검한다.

- zip 존재 확인 → 에이전트 관리 업로드 안내 (순수 ADDON, seed 미등록 → 업로드 후 활성).
- 인증 API 점검(`api` 헬퍼): `/api/addon/ai-traffic-monitor/{status,domains,resolve,usage}`.
  - `resolve` 는 POST(`{"domains":["claude.ai"]}`).
  - `snapshot`/`capture` 는 root+CAP_NET_RAW+도구 필요 → 미충족 시 503(graceful) 안내만.
- Frontend 가이드: `/agents` 업로드/ON 확인, `/chat` "AI 도우미 트래픽 사용량 모니터 상태 알려줘" 라우팅.
- 메뉴/`all` 루프 범위 `0-12` → `0-13` 확장.
- 배치 내 환경 자동구성: OS 기본 NIC 감지(macOS en0/Linux eth0) + vnstat 데몬 선기동→DB 생성→`--add` 순서.

### 6.2 `.env.*` 표준화

`AITM_INTERFACE`(필수 인지) + `AITM_DOMAINS`/`AITM_CAPTURE_DIR`/`AITM_MAX_CAPTURE_SEC`/`AITM_MAX_SNAPSHOT_SEC`(선택)를
다른 ADDON 섹션(Keycloak/Vault 등)과 동일한 표준을 따라 전 프로파일에 배치:

- **`.env.example`** — 상세 주석(용도·기본값·graceful 저하 조건) + 전 변수 예시(주석 처리, 값 문서화 목적).
- **`.env.local`/`.env.dev`/`.env.staging`/`.env.prod`** — 헤더 한 줄 + 필수 변수만 최소 적용(선택 변수는 코드 기본값 사용, 미기재).
  - `local`(호스트 직접 실행) = `AITM_INTERFACE=en0` (macOS 실제 NIC).
  - `dev`/`staging`/`prod`(Docker) = `AITM_INTERFACE=eth0` (컨테이너 기본 NIC).

## 7. 기술 메모 / 차기 이터레이션

- 문서 §7: `tshark` 집계 → Node Exporter textfile(`ai_domain_bytes_total{domain=}`) → Prometheus/Grafana.
- ring buffer 장기 캡처(`tcpdump -G/-W`), DNS+TLS SNI 상관분석.
- `-front.tsx` 대시보드(도메인별 일일 바이트 차트) — 현재는 화면 없음(Q&A).

## 변경 이력 / Changelog
- 2026-07-04 최초 작성. 근거: Perplexity 트래픽 모니터링 조사 문서.
- 2026-07-04 통합 시험 배치 추가(§6.1) — `ITManually.sh` Batch 13 + `.docs/ITManually.md`.
- 2026-07-04 `/usage` 우아한 저하 개선(impl/53) — vnstat 설치됐으나 DB/데몬 미구성 시 502→503+구성 안내.
- 2026-07-04 ITManually Batch 13 환경 자동구성(§6.1) + `.env.*` 표준화(§6.2) — AITM_INTERFACE 등 전 프로파일 배치.
- 2026-07-04 플랫폼 결함 발견·수정(impl/54) — `/chat` 질의 시 Ollama 가 `/usage` 의 query 파라미터
  (`?interface=`)를 몰라 존재하지 않는 path 를 만들어 404. `app/agents/orchestrator.py`
  `_openapi_endpoint_lines()` 가 query 파라미터를 LLM 프롬프트에 노출하도록 수정(플랫폼 코어,
  모든 내장/ADDON 에이전트에 적용되는 일반 수정 — addon 코드/zip 변경 없음).
