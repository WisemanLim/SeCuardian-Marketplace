# 시험 시나리오 — impl/1: Addon 핫디플로이 복원 + F-ENV + F-MP(Marketplace) 백엔드

- 날짜: 2026-07-08
- 대상 기능: Addon 핫디플로이 복원(결정 A), F-ENV 환경키, F-MP Marketplace 카탈로그·설치 API
- 실행: `PYTHONPATH=. python test/impl/1/test_marketplace.py` (fresh sqlite temp DB, FastAPI TestClient)

## 범위
1. **Addon 핫디플로이 복원** — `app/addon_agent_loader.py`·`router_addon_agent.py`·`addon-agents/` 복원, `main.py` lifespan `addon_init`·`addon_guard` 미들웨어 재배선, `router_mcp`/`router_agent_config` addon 연동 원복.
2. **F-ENV** — `.env.example`·`config.py` 에 `VECTOR_BACKEND`/`MARKETPLACE_*`/`TENANT_*`/`GUARDRAILS_*` 키 추가(v0 참조).
3. **F-MP** — `marketplace_assets`·`marketplace_installs` DDL(sqlite+pg, `tenant_id` 선반영), `router_marketplace.py`(raw-SQL), `tbl_agent_config` 마켓플레이스 시드, install=hot-deploy seam(config upsert), 단일 활성 버전.

## 시험 케이스 (Given-When-Then)
| # | 케이스 | 기대 |
|---|---|---|
| 0 | 부팅 + `marketplace` 에이전트 시드 | health 200, agent-config 에 `marketplace` 포함 |
| 1 | 빈 카탈로그 조회 | `assets == []` |
| 2 | user 역할이 자산 등록 | 403 (require_role admin/supervisor) |
| 3 | agent 자산 등록 | 201, `installed=false` |
| 4 | 동일 key@version 중복 등록 | 409 |
| 5 | 잘못된 kind 등록 | 422 |
| 6 | 설치 | 201, `status=installed`, `agent_config_key=cve-scanner` |
| 7 | 설치 후 상세 조회 | `installed=true`, `active_version=1.0.0` |
| 8 | hot-deploy seam | `tbl_agent_config` 에 `cve-scanner` 활성 등록 |
| 9 | 설치 목록 | 1건 |
| 10 | 상위 버전 재설치 | 201, 활성 버전 1건만(1.1.0), 이전(1.0.0) 비활성 |
| 11 | 해제 | 200, 이후 `installed=false`, 재해제 404 |
| 12 | 무토큰 접근 | 401/403 |

## 판정 기준
- 12개 케이스(총 20개 assert) 전부 PASS = PASS.
- `import app.main` 부팅 성공 + `ruff check` 신규파일 0 오류(기존 E402 제외).
