# 시험 결과 — 설치·배포 경로 중복 확인 일원화 (SeCuardian R22-7 준용, test/impl/52)

판정: **PASS** (10/10, 회귀 test/impl/51 7/7 · test/impl/45 PASS 34/FAIL 0, `npx tsc --noEmit` 0오류)

실행 일시: 2026-08-12

## 결과 요약

| ID | 판정 | 근거 |
|----|------|------|
| TC-52-01 | PASS | `nav_group=security` 점유 → 409 `install_conflict`·`reason=agent_config_occupied`·`overwritable=true`(한/영 문구) |
| TC-52-02 | PASS | 동일 버전 활성 설치 → 409 `reason=already_installed`, 메시지에 버전 표기 |
| TC-52-03 | PASS | 충돌 없음 → 예외 없이 통과 |
| TC-52-04 | PASS | force=true → 충돌 판정 스킵 |
| TC-52-05 | PASS | `nav_group=marketplace`(자기 출처) 는 확인 불필요 |
| TC-52-06 | PASS | `deploy_zip(force=False/True)` → upload 파이프라인 `force=false`/`true` 전달 |
| TC-52-07 | PASS | 원격 install: `force=body.force` 전달 + hot-deploy 409 흡수 금지(상위 409) |
| TC-52-08 | PASS | key-check 3판정 + 형식 위반 400 |
| TC-52-09 | PASS | `BehaviorNotiService_worker→behavior-noti`, `VASCA_worker→vasca-cve`, 에이전트 자산은 `agent_key=""` |
| TC-52-10 | PASS | MarketplacePage ConfirmDialog(force 재요청)·스캐폴드 확인 배너·`mp.installConflictTitle` 등 ko/en |
| TC-52-11 | PASS | `ruff check`(변경 4파일) All checks passed, `npx tsc --noEmit` 0오류 |

## 미결/후속

- SeCMP 백엔드(:8100) 재시작 후 `agent_key`·`force`·key-check 가 적용된다.
- `app/main.py:27` 의 기존 `E402`(모듈 임포트 위치) 린트 경고는 본 변경과 무관한 선재 항목.
