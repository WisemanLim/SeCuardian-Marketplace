# Harbor 레지스트리 스캐너 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(Harbor 레지스트리 + Trivy 스캐너)가 기동되어 있어야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [Harbor](https://goharbor.io/) v2.11+ (Apache-2.0) — Trivy 스캐너 내장
- **역할**: 컨테이너 이미지 레지스트리, 자동 취약점 스캔, Critical CVE 배포 차단, Cosign 서명 검증
- **연결 방식**: `HARBOR_URL` 로 REST API (`/api/v2.0/health`, `/projects/{p}`, `/scanners`), 정책 조회는 Basic Auth (`HARBOR_ADMIN_USER`/`HARBOR_ADMIN_PASSWORD`)
- **포트**: `8083` (HTTP, 호스트) / `8443` (HTTPS)

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| Docker Engine / Compose | 24.0+ / v2.20+ |
| 디스크 | 인스톨러 ~780MB + 이미지 저장 공간 |
| 환경 파일 | `.env.local` 에 `deploy/docker/harbor.env.example` 항목 추가 |
| (선택) cosign CLI | `make harbor-cosign` |

## 3. 설치 (SeCuardian 저장소 Makefile 기준)

```bash
make harbor-install   # bash deploy/scripts/harbor_install.sh — 오프라인 인스톨러 다운로드 + harbor.yml 생성 (1회)
make harbor-up        # docker compose -f deploy/docker/docker-compose.harbor.yml up -d
make harbor-status    # GET /api/v2.0/health
make harbor-setup     # 프로젝트 secuardian + Robot Account 생성 → HARBOR_ROBOT_SECRET 출력
make harbor-policy    # Trivy 자동 스캔 + Critical CVE 차단(prevent_vul) 정책 — bash deploy/scripts/harbor_policy.sh
make harbor-cosign    # Cosign 키 쌍 생성 → COSIGN_PUB_KEY 경로
make harbor-logs / make harbor-down
```

### 독립 설치 (저장소 없이)

```bash
HV=v2.11.2
curl -LO https://github.com/goharbor/harbor/releases/download/$HV/harbor-offline-installer-$HV.tgz
tar xzf harbor-offline-installer-$HV.tgz && cd harbor
cp harbor.yml.tmpl harbor.yml
# hostname, http.port: 8083, harbor_admin_password, data_volume 수정 (https 블록은 주석)
sudo ./install.sh --with-trivy
```

Harbor UI → Projects → `secuardian` → Configuration 에서 **Automatically scan images on push** 와 **Prevent vulnerable images from running (Critical)** 를 활성화합니다.

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
HARBOR_URL=http://localhost:8083          # 필수
HARBOR_PROJECT=secuardian                 # 선택 (기본값)
HARBOR_ADMIN_USER=admin                   # 선택 (기본값)
HARBOR_ADMIN_PASSWORD=<admin 비밀번호>    # /scan-policy 조회에 필요 (미설정 시 configured=false 응답)
HARBOR_ROBOT_NAME=robot$secuardian-ci     # 선택 (표시용)
HARBOR_ROBOT_SECRET=<robot secret>        # 선택 (표시용)
COSIGN_PUB_KEY=/path/to/cosign.pub        # 선택 — cosign_configured 표시
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/harbor-scanner/status
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/harbor-scanner/scan-policy
```

| 증상 | 조치 |
|------|------|
| 503 `Harbor 연결 실패` | `HARBOR_URL`/포트, `docker compose ps` 확인 |
| `status: DOWN` + http_status | Harbor 컴포넌트(core/registry/trivy) 기동 대기 후 재시도 |
| `trivy_registered: false` | `./install.sh --with-trivy` 또는 `make harbor-policy` 재실행 |
