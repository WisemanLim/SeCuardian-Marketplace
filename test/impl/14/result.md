# 시험 결과 — impl/14

- 날짜: 2026-07-08
- 판정: **PASS** (10/10) + impl/1 회귀 무영향

## 실행 결과
```
PASS register asset (201)
PASS install w/o zip -> deployed false (False)
PASS addon route absent (no zip)
PASS user zip upload -> 403
PASS non-zip -> 400
PASS zip attached w/ checksum (201)
PASS install w/ zip -> deployed true (True)
PASS addon route LIVE after local install (200 {"addon":"localaddon","ok":true})
PASS addon registered via reused pipeline
PASS asset meta checksum synced
=== RESULT: ALL PASS
```

## 검증 항목
- 로컬 카탈로그 자산에 ZIP 저장(`marketplace_asset_blobs`) 후 install → **실 hot-deploy 무중단 마운트**(설치 전 404 → 후 200).
- `deploy_zip` 공용 서비스로 원격(impl/10)·로컬(impl/14) install 이 동일 파이프라인(`/api/addon-agents/upload`) 재사용 — 중복 제거.
- ZIP 미첨부 자산은 config seam 만(deployed=false) — 기존 동작(impl/1) 보존.
- RBAC(admin/supervisor), non-zip 400, checksum 동기화.
- boot·`ruff check` 0오류, 테스트 산출물(`addon-agents/deployed/localaddon`, gitignore 대상) 실행 후 정리.

## 미결/후속
- ZIP 블롭 크기 상한(현재 addon upload 의 10MB 제한이 배포 단계에서 적용). 카탈로그 저장 단계 상한은 후속.
