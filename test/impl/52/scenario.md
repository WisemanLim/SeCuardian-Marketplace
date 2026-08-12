# 시험 시나리오 — 설치·배포 경로 중복 확인 일원화 (SeCuardian R22-7 동일 적용, test/impl/52)

배경(SeCuardian 사용자 보고 2026-08-12): 마켓플레이스 경로의 중복 등록이 사용자 확인 없이
진행됐다. SeCMP 도 동일 계열 결함을 보유 —
① 로컬 install 은 `tbl_agent_config` 를 무조건 upsert 해 **마켓플레이스 출처가 아닌
   (내장) 에이전트 설정 행을 조용히 점유**하고, 동일 버전 재설치도 확인 없이 진행.
② 원격 install 의 hot-deploy 는 `deploy_zip` 을 항상 `force=true` 로 호출 → 기등록 키를
   무통보 덮어쓰기, 게다가 409 를 흡수해 사용자에게 알리지 않았다.
③ 스캐폴드 경로에 키 사전 확인·덮어쓰기 확인 수단 부재(업로드 탭만 보유).

대상: `app/routers/router_marketplace.py`, `app/routers/router_marketplace_remote.py`,
`app/routers/router_addon_agent.py`, `app/services/addon_deploy.py`,
`app/routers/router_marketplace_host.py`(worker→에이전트 `agent_key` 노출),
`front/src/api/{marketplace,marketplaceRemote,addonAgents}.ts`,
`front/src/pages/marketplace/MarketplacePage.tsx`,
`front/src/pages/agents/AgentBuilderModal.tsx`, `front/src/locales/{ko,en}.json`,
`marketplace-assets/security/{VASCA,BehaviorNotiService}_worker/*-meta.json`.

| ID | 입력 | 기대 |
|----|------|------|
| TC-52-01 | 로컬 install — `tbl_agent_config` 에 nav_group≠marketplace 행 점유, force 없음 | 409 `install_conflict`·`reason=agent_config_occupied`·`overwritable=true` |
| TC-52-02 | 로컬 install — 동일 버전 활성 설치 존재, force 없음 | 409 `install_conflict`·`reason=already_installed` |
| TC-52-03 | 로컬 install — 충돌 없음 | 통과(예외 없음) |
| TC-52-04 | 로컬 install — 충돌 존재 + force=true | 판정 스킵(예외 없음) |
| TC-52-05 | 로컬 install — 마켓플레이스 출처 설치본(nav_group=marketplace) 재설치, 비활성 | 통과 — 자기 출처 갱신은 확인 불필요 |
| TC-52-06 | `deploy_zip(force=False/True)` | upload 파이프라인에 `force=false`/`true` 전달 |
| TC-52-07 | 원격 install hot-deploy 가 409 반환 | 흡수 금지 — 409 로 상위 전달(카탈로그 편입 전) |
| TC-52-08 | `GET /api/addon-agents/key-check/{key}` | 미사용=available, 내장=`builtin_conflict`, 기등록=`duplicate`, 형식 위반=400 |
| TC-52-09 | worker 자산 카탈로그 엔트리 | `kind=worker` + `agent_key`(짝 에이전트) 노출, 에이전트 자산은 `agent_key=""` |
| TC-52-10 | 프론트 배선 | install 409 → ConfirmDialog(force 재요청), 스캐폴드 `checkAgentKey`·덮어쓰기 배너, ko/en 문구 |
| TC-52-11 | 정적 검증 | `ruff check`(변경 파일) + `npx tsc --noEmit` 0오류 |

실행: `uv run pytest test/impl/52 -q` (+ 회귀 `test/impl/51`, `python test/impl/45/test_marketplace_host.py`),
`cd front && npx tsc --noEmit`
