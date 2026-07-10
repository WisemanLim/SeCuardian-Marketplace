# 시험 결과 — impl/44 (물리 test/impl/42): §7.6.5 해제 시 hot-deploy 잔재 완전 정리 + 상단 설명

- 날짜: 2026-07-10
- 판정: **PASS** (19/19)
- 실행: `uv run python test/impl/42/test_uninstall_cleanup.py` (격리 sqlite + TestClient, 실 FS E2E)

| # | 케이스 | 결과 |
|---|---|---|
| A1 | 유효 addon ZIP 등록+install → deployed=true·디렉터리·addon 행 생성 | ✅ 4건 |
| A2 | uninstall → `undeployed:true` — deployed 디렉터리·addon 행·MCP 설정 삭제 | ✅ 4건 |
| A3 | config 행 유지 + `is_enabled=0` (재설치 대비) | ✅ |
| A4 | 재설치 → 재생성 → 재해제 → 재정리 (왕복 무결) | ✅ 2건 |
| A5 | 메타-only 자산 uninstall → `undeployed:false`, 오류 없음 | ✅ |
| B1 | delete_addon 헬퍼 리팩터 회귀 — 404 가드 유지 | ✅ |
| C1 | cleanup 스크립트 — 고아 디렉터리 제거 + 멱등 재실행 | ✅ 2건 |
| D1 | pageDesc 자산 카탈로그 포함 (ko/en) | ✅ 2건 |
| D2 | 설치/해제 시 `agentConfigChanged` 발행(2개소, 네비 즉시 동기화) | ✅ |
| D3 | Makefile `cleanup-addons` 타겟 | ✅ |
| D4 | `tsc --noEmit` | ✅ 0오류 |

## dev 환경 실정리 (C2 — 사용자 결함 보고 해소)

`make cleanup-addons` 실행 결과: **addon 잔재 9건**(usermanager·agentic-soc·ai-eval-gate·
ai-traffic-monitor·board·caddy-proxy·grafana-dashboard·server-shell·truffle-scan) +
**고아 deployed 디렉터리 5건**(helloaddon·localaddon·remote-scanner·tabtest·zip-agent-two) 제거.
`addon-agents/deployed/` 비움, `tbl_addon_agents` 0행 — 좌측 네비 잔존 메뉴(셀 진단·사용자 관리) 해소.

## 회귀

| 시험 | 결과 |
|---|---|
| test/impl/41 (§7.6.4 3탭) · impl/40 (§7.6.3) · impl/39 (§7.6.2) · impl/1 (F-MP 수명주기) | ✅ 전부 OK |
| 시험 종료 후 실 FS 잔재 | ✅ 0건 (finally 원복 + uninstall 자체 정리) |

## 비고

- 고아 deployed 디렉터리 5건 중 tabtest·zip-agent-two 는 impl/39·40 시험의 hot-deploy 가
  실 FS 에 쓴 부수효과 — impl/42 시험부터 finally 원복으로 재발 방지.
- 라이브 마운트된 라우터의 완전 제거는 기존 계약대로 앱 재시작 필요(메뉴·목록·디렉터리는 즉시 정리).
- `addon-agents/` 디렉터리 자체는 deployed/ 가 compose bind-mount·loader 경로로 런타임 필수라 유지.
