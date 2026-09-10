# impl/53 시험 시나리오 — E9 보안 에이전트 자산 확장 (7종)

대상: `marketplace-assets/security/` 신규 보안 ADDON 7종 (extra-agents 후보 A~G).
실행: `.venv/bin/python test/impl/53/run.py` (standalone, test-runner §3 방식).
방법: 각 `{key}-app.py` 를 동적 로더와 동일하게 spec_from_file_location 로드 → FastAPI 마운트 →
      `get_current_user` dependency override(role=admin/user) → TestClient 로 엔드포인트 검증.

| TC | 대상 | 수용 기준 |
|---|---|---|
| TC-53-00 | 7종 공통 | `router` 노출 + meta.json(agent_type=service·version·display_name·description·capabilities) + `from __future__ import` 미사용 |
| TC-53-01 | B agentic-threat-model | scan-config 가 하드코딩 시크릿(TM-01)·고위험도구(TM-02)·인젝션(TM-03)·무인증MCP(TM-04) 탐지; clean 설정 0건; scan-mcp 는 user 권한 403 |
| TC-53-02 | A attack-surface-recon | status 200; recon 이 allowlist 미설정 시 403·대상외 403; scan 잘못된 도메인 400 |
| TC-53-03 | C api-vuln-scan | analyze-spec 가 BOLA(API1)·취약인증(API2)·평문서버(API7) 탐지; 잘못된 spec 422 |
| TC-53-04 | G cicd-security-scan | scan-workflows 가 스크립트인젝션(CI-02)·셀프호스트(CI-03)·write-all(CI-04)·미고정액션(CI-06)·curl\|sh(CI-07) 탐지; 빈 files 422 |
| TC-53-05 | F ad-security-scan | analyze 가 Kerberoast(AD-01)·AS-REP(AD-02)·비만료암호(AD-03) 탐지; scan allowlist 미설정 403 |
| TC-53-06 | D malware-hunt | check-packages 가 IOC 매치(ctx) 1건; hunt 는 user 권한 403 |
| TC-53-07 | E soc-intel-fusion | lookup 오프라인 모드 구조 응답(offline=true·fusion); 잘못된 CVE 400 |

부가: 전 파일 `ruff check` 통과, 7종 `.zip` 패키징(app+meta), `seed_assets` 자동 발견(meta+zip).
회귀: `app.main` import 부팅(추가 전용 변경이라 기존 소스 무수정).
