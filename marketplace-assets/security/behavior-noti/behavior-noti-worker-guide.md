# BehaviorNotiService C++ — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 **BehaviorNotiService_worker**(자체 개발 C++ 행위 기반 알림 데몬)가
> 감시 대상 호스트(서버·PC·Edge 디바이스)에 설치되어야 동작합니다. 에이전트는 worker 가
> 웹훅으로 보내는 이상 행위 이벤트를 수신·분석·질의하는 역할만 합니다.
> This agent requires the **BehaviorNotiService_worker** (in-house C++ behavior-based
> alerting daemon) installed on each monitored host. The agent only receives, analyzes and
> answers queries on the anomaly events the worker sends via webhook.

## 1. Worker 개요

- 이름: `BehaviorNotiService_worker` (C++17 데몬, REST 포트 `8300`)
- 역할: 호스트 로그(`/var/log`) 감시 → 이상 행위 탐지 룰 평가 → SeCuardian 웹훅
  (`POST /api/behavior/events`)·Slack·Wazuh(syslog) 알림 전송. 탐지 이력은 SQLite
  (`/var/lib/bns`)에 저장.
- 배포 패키지: `BehaviorNotiService_worker.zip` (C++ 소스 + `CMakeLists.txt` + `Dockerfile`
  + `config/behavior_noti.yaml` + `VERSION`)
  - 플랫폼 내 다운로드: `GET /api/addon-agents/behavior-noti/worker-package`
  - 저장소 위치: `addon-agents/zip/BehaviorNotiService_worker/`

## 2. 요구 사항

- Docker 설치(권장 경로 — 멀티스테이지 빌드로 컴파일러 불필요), 또는
- 네이티브 빌드: CMake 3.20+, g++ (C++17), `libsqlite3-dev`, `libyaml-cpp-dev`

## 3. 설치

### A. Docker Compose (권장)

SeCuardian 저장소가 있는 호스트:

```bash
make behavior-build   # docker compose -f deploy/docker/docker-compose.behavior.yml build
make behavior-up      # 기동 — REST API: http://localhost:8300
```

독립 설치(저장소 없이 — worker 패키지만으로):

```bash
unzip BehaviorNotiService_worker.zip && cd BehaviorNotiService_worker
docker build -t secuardian/behavior-noti:1.0.0 .
docker run -d --name behavior-noti --restart unless-stopped \
  -p 127.0.0.1:8300:8300 \
  -v behavior_db:/var/lib/bns \
  -v /var/log:/var/log/host:ro \
  -v "$PWD/config/behavior_noti.yaml:/etc/bns/behavior_noti.yaml:ro" \
  -e SLACK_WEBHOOK_URL="" \
  secuardian/behavior-noti:1.0.0
```

### B. 네이티브 빌드

```bash
cd BehaviorNotiService_worker
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
./build/behavior_noti --config config/behavior_noti.yaml
```

## 4. SeCuardian 연동 설정

| 위치 | 키 | 기본값 | 설명 |
|------|----|--------|------|
| SeCuardian `.env.*` | `BEHAVIOR_NOTI_ENABLED` | `true` | 이벤트 수신 활성화 |
| SeCuardian compose | `BEHAVIOR_NOTI_URL` | `http://host.docker.internal:8300` | worker REST 접근 URL |
| worker 환경변수 | `SLACK_WEBHOOK_URL` | (없음) | Slack 알림 (선택) |
| worker 환경변수 | `WAZUH_HOST` / `WAZUH_PORT` | (없음) / `514` | Wazuh syslog 전달 (선택) |

worker → SeCuardian 웹훅 대상과 탐지 룰은 `config/behavior_noti.yaml` 에서 설정합니다
(HMAC 서명 사용 시 서버의 behavior HMAC 설정과 일치 필요).

## 5. 확인

```bash
make behavior-status                              # worker(8300) → 서버 API 순 확인
curl -sf http://localhost:8300/status             # worker 데몬 직접 확인
curl -sf http://localhost:8200/api/behavior/status # 에이전트 수신 상태
```

## 6. 운영·중단

```bash
make behavior-logs    # docker compose logs -f
make behavior-down    # 중단
```

## English Summary

- **Worker**: `BehaviorNotiService_worker` — C++17 daemon (REST port `8300`) that watches
  host logs (`/var/log`), evaluates behavior detection rules, and pushes anomaly events to
  SeCuardian (`POST /api/behavior/events`), Slack, or Wazuh (syslog). History in SQLite.
- **Get it**: download `BehaviorNotiService_worker.zip` via
  `GET /api/addon-agents/behavior-noti/worker-package` (full source + Dockerfile +
  `config/behavior_noti.yaml` + `VERSION`).
- **Install (Docker, recommended)**: `make behavior-build && make behavior-up` from the repo,
  or standalone `docker build -t secuardian/behavior-noti:1.0.0 . && docker run -d
  -p 127.0.0.1:8300:8300 -v /var/log:/var/log/host:ro ...` from the unzipped package.
- **Native build**: CMake 3.20+, g++ (C++17), `libsqlite3-dev`, `libyaml-cpp-dev`.
- **Server env**: `BEHAVIOR_NOTI_ENABLED=true`, `BEHAVIOR_NOTI_URL`
  (default `http://host.docker.internal:8300`).
- **Verify**: `curl http://localhost:8300/status`, `make behavior-status`.
