# 시험 시나리오 — ADDON 등록 파이프라인 오류 수정 (test/impl/51, SeCuardian R22-6 동일 적용)

배경: SeCuardian 에서 보고된 결함 4건이 SeCMP `upload_addon` 에도 동일하게 존재
(코드 계보 공통). 원인·조치는 SeCuardian `test/impl/64` 와 같다.

1. 내장 에이전트 키와 중복되는 ZIP 이 조용히 `is_builtin=1` 로 등록 → ADDON 목록
   (`is_builtin=0` 필터)에서 사라짐
2. 재업로드 시 영문 원문 `'{key}' already exists. Use force=true to overwrite.` — UI 에
   force 수단 없음
3. 등록 불가 ZIP(worker 배포본 등)이 `addon-agents/deployed/` 에 압축 해제된 채 잔류
4. 활성 상태가 `tbl_agent_config.is_enabled` 와 어긋나 비활성 에이전트 라우터가 열림

대상: `app/routers/router_addon_agent.py`(`_check_safe_names`·`_invalid_package_message`·
`_conflict_detail`·`upload_addon`·`_parse_meta_json`), `app/addon_agent_loader.py`
(`_load_all_from_disk`), `front/src/api/addonAgents.ts`, `front/src/pages/agents/
AgentBuilderModal.tsx`, `front/src/locales/{ko,en}.json`.

| ID | 입력 | 기대 |
|----|------|------|
| TC-51-01 | 내장 키(`vasca-cve`) 업로드, force 무관 | 409 `builtin_conflict`·`overwritable=false`, DB 쓰기·라우터 로드 0건, `deployed/` 미생성 |
| TC-51-02 | 이미 등록된 ADDON 재업로드 | 409 `duplicate`·`overwritable=true`, `force=true` 영문 원문 미노출 |
| TC-51-03 | worker 배포본 ZIP | 400 + worker 전용 안내, `deployed/` 압축 해제 없음 |
| TC-51-04 | 순수 addon | 활성 등록 + 라우터 로드, meta `type` 폴백(`service`) |
| TC-51-05 | app.py 로드 실패 | 500 + 신규 배포 디렉터리 롤백 |
| TC-51-06 | 복원 쿼리 | `LEFT JOIN tbl_agent_config` + `COALESCE(c.is_enabled,1)=1`, 소스 없는 등록분 경고 스킵 |
| TC-51-07 | 프론트 배선 | `parseDeployError`, 내장 충돌은 오류 표시·일반 중복만 `handleOverwrite`, ko/en 문구 3종 |

실행: `uv run pytest test/impl/51 -q` + `cd front && npx tsc --noEmit`
