# 시험 결과 — impl/10

- 날짜: 2026-07-08
- 판정: **PASS** (8/8) + 기존 impl/9 회귀 무영향

## 실행 결과
```
PASS addon route absent pre-install (404)
PASS remote install 201
PASS deployed=true (real hot-deploy)
PASS catalog asset source=remote
PASS addon route LIVE after remote install (200 {"addon":"helloaddon","ok":true})
PASS addon registered in addon registry (['helloaddon'])
PASS asset in marketplace catalog (['helloaddon'])
PASS hot_deploy=false -> catalog only (False)

=== RESULT: ALL PASS
```

## 검증 항목
- **원격 install → 실 hot-deploy 무중단 마운트 확인**: 설치 전 `/api/addon/helloaddon/ping` 404 → 설치 후 200(재시작 없음).
  이는 §7.6 요구("설치 = 기존 hot-deploy 파이프라인")의 실동작 증명.
- **함수 재사용(§7.3.3)**: 별도 재구현 없이 기존 `/api/addon-agents/upload` 엔드포인트를 in-process ASGI 로 호출 —
  extract→SQL→`load_router()`→`tbl_addon_agents`/`tbl_agent_config` 등록이 전부 그대로 실행됨(deploy_result.body 확인).
- 유효하지 않은 addon ZIP(rag-pipeline 등)·`hot_deploy=false` 는 catalog 편입만(무중단 흡수).
- boot 25 routes, `ruff check` 0오류, 전체 백엔드 시험(impl/1,2,4,5,6,7,9,10) ALL PASS.

## 발견/조치
- addon 배포 경로 `_DEPLOYED = Path("addon-agents/deployed")` 는 import 시점 상수라 `ADDON_DEPLOYED_PATH`(compose 볼륨 변수)로
  격리되지 않음 → 시험이 리포 `addon-agents/deployed/`(gitignore 대상)에 산출물 생성. 시험 후 수동 정리.
  (해당 경로는 `.gitignore` 로 커밋 제외되므로 리포 오염 없음.)
- 최초 시험 작성 시 addon app.py 에 `APIRouter(prefix=...)` 를 중복 정의 → load_router 가 다시 prefix 부여해
  이중 prefix 404 발생. addon 규약(app.py 라우터는 prefix 없이 정의, 로더가 `/api/addon/{key}` 부여)에 맞춰 수정.

## 미결/후속
- **로컬 marketplace install 의 실 ZIP hot-deploy** — 로컬 `marketplace_assets` 는 ZIP 바이트를 저장하지 않으므로(메타만),
  로컬 자산의 실 배포는 별도 ZIP 저장소 또는 scaffold 연계 필요. 현재는 원격 경로만 실 hot-deploy 지원(로컬은 config-upsert seam).
- GPG 서명 검증, mTLS CA 번들(impl/9 잔여).
