# 시험 시나리오 — impl/14: 로컬 자산 실 ZIP 배포 (F-MP §7.6)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "로컬 자산 실 ZIP 배포(ZIP 저장소)". 로컬 카탈로그 자산에 ZIP 첨부 → install 시 무중단 hot-deploy.
- 실행: `PYTHONPATH=. python test/impl/14/test_local_zip_deploy.py`

## 범위
- DDL `marketplace_asset_blobs`(sqlite BLOB / pg BYTEA) — 자산별 ZIP 저장(tenant_id, checksum).
- `app/services/addon_deploy.py` — `deploy_zip(blob, asset_key, user)` 공용 헬퍼(원격 impl/10 `_hot_deploy` 를 서비스로 추출, remote 라우터도 위임).
- `router_marketplace.py`:
  - `POST /catalog/{asset_key}/zip`(admin) — ZIP 첨부·SHA256·자산 메타 checksum 동기화.
  - `install`: ZIP 블롭 존재 시 `deploy_zip` in-proc 재사용 → 실 hot-deploy, `deployed` 플래그. 없으면 config seam 만.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 자산 등록 | 201 |
| 2 | ZIP 없이 install | deployed=false, addon route 404 |
| 3 | user ZIP 첨부 | 403 |
| 4 | non-zip 첨부 | 400 |
| 5 | ZIP 첨부 | 201, checksum |
| 6 | ZIP 첨부 후 install | deployed=true |
| 7 | 설치 후 addon route | `/api/addon/localaddon/ping` 200(무중단) |
| 8 | addon 레지스트리 등록 | upload 파이프라인 재사용 |
| 9 | 자산 메타 checksum 동기화 | SHA 일치 |

## 판정 기준
- 10개 assert 전부 PASS + impl/1 회귀 무영향 = PASS.
