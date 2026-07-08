# 시험 시나리오 — impl/10: 실 addon ZIP hot-deploy 연결 (F-MP §7.6)

- 날짜: 2026-07-08
- 대상: §9.5 최우선 잔여 "실 addon ZIP hot-deploy 파이프라인 연결". 원격 install(impl/9)이 검증한 ZIP 을
  기존 `/api/addon-agents/upload` 파이프라인으로 **in-process 재사용** 배포 → 무중단 라이브 마운트.
- 실행: `PYTHONPATH=. python test/impl/10/test_remote_hotdeploy.py` (유효 addon ZIP in-memory 생성 + 원격 fetch monkeypatch)

## 설계 (PRD §7.3.3 "별도 재구현 금지 — 함수 재사용")
- `router_marketplace_remote._hot_deploy(blob, asset_key, user)` — 다운로드 ZIP 을 httpx ASGITransport
  in-process 클라이언트로 `/api/addon-agents/upload` 에 multipart POST(`force=true`). Orchestrator 의
  `_exec_api_call` 자기호출과 동일 패턴. 서비스 토큰은 호출자(admin/supervisor) 클레임으로 재발급.
- `install` 흐름: 원격 메타 → 다운로드 → SHA256 검증 → **`_hot_deploy`(hot_deploy=true 기본)** → marketplace_assets(source='remote') 편입.
- 유효 addon ZIP 이 아니면(예: rag-pipeline) upload 실패를 흡수하고 catalog 편입만(무중단).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 설치 전 addon route | 404(미마운트) |
| 2 | 유효 addon ZIP 원격 install | 201, `deployed=true` |
| 3 | catalog 자산 source | 'remote' |
| 4 | **설치 후 addon route** | `/api/addon/helloaddon/ping` → 200(무중단 라이브 마운트) |
| 5 | addon 레지스트리 등록 | `tbl_addon_agents` 에 helloaddon(upload 파이프라인 재사용 결과) |
| 6 | 마켓 카탈로그 | helloaddon 노출 |
| 7 | `hot_deploy=false` | `deployed=false`, catalog 편입만 |

## 판정 기준
- 8개 assert 전부 PASS + 기존 impl/9 회귀(deployed=false 흡수) 무영향 = PASS.
