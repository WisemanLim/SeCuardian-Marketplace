# ISMS-P 컴플라이언스 증거 수집 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트의 "worker" 는 별도 바이너리가 아니라 **증거 소스가 되는 연동 보안 Addon 들**입니다.
> 연동 Addon 이 설치·활성화되어 있어야 통제항목이 COMPLIANT 로 판정됩니다.

---

## 1. Worker 개요

- **역할**: KISA ISMS-P(2023) 통제항목 10종의 증거를 자동 수집 — 연동 Addon `/status` 스냅숏(api_snapshot) + 문서 존재 확인(document) → 준수율 보고서 생성
- **연결 방식**: SeCuardian 자기 자신(`ISMS_INTERNAL_BASE_URL`, 기본 `http://localhost:8200`)의 `/api/addon/{key}/...` 를 호출자 JWT 로 호출
- **참고**: 기존 Addon `isms-p-evidence` 와 역할이 겹칩니다. 둘 중 하나만 설치하세요.

## 2. 통제항목 ↔ 증거 소스

| 통제 | 제목 | 증거 소스 | 필요한 Addon / 문서 |
|------|------|-----------|--------------------|
| 2.1.1 | 정보보호 정책 승인·공표 | 문서 `COMPLIANCE.md` | `ISMS_DOC_ROOT` 기준 |
| 2.5.2 / 2.5.3 | IAM/SSO, MFA | `GET /api/addon/keycloak-monitor/status` | keycloak-monitor |
| 2.6.2 | 권한계정 세션 녹화 | `GET /api/addon/teleport-pam/sessions` | teleport-pam |
| 2.7.1 | Vault PKI/TLS | `GET /api/addon/vault-monitor/status` | vault-monitor |
| 2.8.3 | 개인정보 가명처리 DLP | `GET /api/addon/neosync-dlp/status` | neosync-dlp |
| 2.9.1 | 시크릿 누출 방지 CI/CD | 문서 `.github/workflows/secret-scan.yml` | 저장소 워크플로 |
| 2.11.1 | 사고 대응 SOAR | `GET /api/addon/shuffle-soar/status` | shuffle-soar |
| 2.11.2 | 취약점 관리 | `GET /api/addon/vasca-cve/status` | vasca-cve |
| 2.12.1 | SIEM 로그 수집·보존 | `GET /api/addon/wazuh-siem/status` | wazuh-siem |

연동 Addon 이 없으면 `api_status=NOT_INSTALLED`, 백엔드 미기동이면 `ERROR:503` 으로 기록되어 해당 통제는 NON_COMPLIANT 가 됩니다.

## 3. 설치 절차

1. 에이전트 관리 → ZIP 업로드로 필요한 연동 Addon 을 먼저 설치·활성화합니다 (각 Addon 의 worker-guide 참조).
2. `compliance-isms` 를 설치·활성화합니다.
3. (선택) 문서 증거를 위해 `COMPLIANCE.md`, `.github/workflows/secret-scan.yml` 을 `ISMS_DOC_ROOT` 아래에 둡니다.

SeCuardian 저장소의 Makefile 대응 타깃(`make isms-status / isms-collect / isms-report`)은 내장판 경로(`/api/isms/...`)를 호출하므로, Addon 판은 아래 5절 명령을 사용하세요.

## 4. 에이전트 연결 (SeCuardian-Basic `.env`) — 모두 선택

```bash
ISMS_INTERNAL_BASE_URL=http://localhost:8200   # 자기 자신 호출 주소 (컨테이너: http://127.0.0.1:${PORT})
ISMS_DOC_ROOT=/app                             # 문서 증거 탐색 루트 (기본: 프로세스 CWD)
ISMS_AUTO_COLLECT=false                        # 표시용 — 스케줄 수집은 외부 cron 으로 POST /evidence 호출
ISMS_REPORT_DIR=reports/isms                   # 표시용
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
BASE=http://localhost:8200/api/addon/compliance-isms
curl -s -H "Authorization: Bearer $TOKEN" $BASE/status
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '[]' $BASE/evidence
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"requester":"audit-team"}' $BASE/report
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/evidence?control_id=2.12.1"
```

| 증상 | 조치 |
|------|------|
| `api_status: NOT_INSTALLED` | 해당 연동 Addon 설치·활성화 |
| `api_status: UNREACHABLE` | `ISMS_INTERNAL_BASE_URL` 이 현재 프로세스에서 도달 가능한지 확인 |
| `api_status: ERROR:401` | 호출자 JWT 만료 — 재로그인 후 재수집 |
| `doc_exists: false` | `ISMS_DOC_ROOT` 와 문서 경로 확인 |
| 재시작 후 증거 소실 | 인메모리 저장소 — 보고서는 5년 보존 요건상 외부 저장 필요 |
