# impl/49 — 중복 등록 사용자 확인 + 시드 보호 범위 축소 + 카탈로그 삭제 시 시드 자산 반환 (§7.6.6 v0.47)

## 배경 (사용자 요구 2026-07-10)
1. 동일 에이전트(asset_key)를 별도 카탈로그로 등록하려 하면 "이미 등록됨" 정보를 보여주고,
   등록 여부는 사용자가 판단해 확인 시 등록(요청 카탈로그로 이동)되어야 함.
2. `marketplace-assets/addon`(스캐폴드 템플릿) 유래라도 사용자가 카탈로그를 생성하며 등록한
   자산은 삭제 가능해야 함 — 시드 보호는 seed 대상(security/utilities)만.
3. 사용자가 등록한 카탈로그는 삭제 가능해야 함 — 시드 자산이 이동돼 있으면 원 카탈로그로 반환.

## 시험 항목
| # | 시나리오 | 기대 결과 |
|---|---------|----------|
| 1 | 신규 key ZIP 등록(cat1) — 중복 아님 | 201, confirm 불필요 |
| 2 | 동일 key ZIP 을 cat2 로 confirm 없이 등록 | 409 `{"code":"duplicate","assets":[{asset_key,name,category}]}` |
| 3 | 동일 key ZIP 을 cat2 로 `confirm=true` 등록 | 201, category=cat2 이동, 중복 행 없음 |
| 4 | addon 디스크 보유 key(toolproxyagent) 사용자 등록 | `deletable=true`, DELETE 200 |
| 5 | 시드 디스크 보유 key(vasca-cve) 등록 | `deletable=false`, DELETE 403 |
| 6 | 시드 key 를 사용자 카탈로그(mixcat)로 등록 후 카탈로그 삭제 | 200 — 시드 key 는 security 로 반환(returned), 일반 key 는 삭제(deleted) |
| 7 | 설치 중 자산 포함 카탈로그 삭제 | 409 (먼저 해제) |

## 실행
```bash
uv run python test/impl/49/test_asset_dup_and_delete.py
```
