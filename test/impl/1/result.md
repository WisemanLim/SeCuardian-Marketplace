# 시험 결과 — impl/1

- 날짜: 2026-07-08
- 판정: **PASS** (20/20 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian/.venv`(동일 pyproject 의존성)

## 실행 결과
```
PASS health 200
PASS marketplace seeded in agent-config (got ['general', 'chat', 'marketplace'])
PASS empty catalog
PASS user register -> 403
PASS register 201
PASS registered not-installed
PASS duplicate -> 409
PASS bad kind -> 422
PASS install 201
PASS install upserts agent_config_key
PASS asset installed+active_version
PASS cve-scanner in agent-config enabled
PASS installs list = 1
PASS reinstall latest 1.1.0
PASS single active version (['1.1.0:1', '1.0.0:0'])
PASS uninstall 200
PASS after uninstall not-installed
PASS uninstall again -> 404
PASS no token -> 401/403

=== RESULT: ALL PASS
```

## 검증 항목
- Addon 핫디플로이 복원 후 부팅 OK (routes 19 → 20, marketplace 라우터 포함).
- `ruff check` 신규 파일(`router_marketplace.py`·`config.py`) 0 오류. `main.py` E402 는 클론 이전부터 존재하는 기존 이슈(원본 SeCuardian 동일).
- 단일 활성 버전 불변식(재설치 시 이전 install `active=0` 전이) 확인.
- RBAC(require_role admin/supervisor) 등록·설치·해제에 적용 확인.

## 미결/후속 (이번 차수 범위 밖)
- **F-MP 프론트 화면**(`front/src/pages/marketplace/`) 미구현 — 백엔드 API 만. 다음 차수.
- 원격 레지스트리(§7.3 `/api/marketplace-remote`) 미구현 — E1.5.
- install 이 실제 addon ZIP 업로드 파이프라인(router_addon_agent)까지 연결하는 것은 §7.6 후속(현재는 config upsert seam).
- F-WF / F-RAG / F-PG / F-GRD 미착수 — 다음 차수(v0 참조 이식).
