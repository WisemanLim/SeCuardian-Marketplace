# impl/48 — 자산 등록 회귀 수정: 카탈로그(category) 반영 + 폼 입력 반영 (§7.6.2·§7.6.6)

## 배경 (버그)
d06c8b7 에서 등록 모달이 ZIP-only 경로로 통합되며 두 가지 회귀 발생:
1. `/catalog/zip` UPDATE 분기(동일 key@version 존재)가 `category` 를 갱신하지 않아,
   기존 자산 ZIP 을 새 카탈로그명으로 등록해도 카탈로그가 생성되지 않고 자산도 이동하지 않음.
2. 모달의 필수 입력(자산명·설명·종류)이 서버로 전송되지 않아 ZIP meta 가 항상 우선 —
   사용자가 입력한 이름으로 자산을 찾을 수 없음.

## 시험 항목
| # | 시나리오 | 기대 결과 |
|---|---------|----------|
| 1 | 단일 ZIP + 폼(name/desc/kind=workflow) + 신규 category `testcat` 등록 | 자산 생성, category=testcat, name=폼 값, kind=workflow |
| 2 | 동일 key@version ZIP 을 다른 category `movecat` 로 재등록 | 중복 생성 없이 category 가 movecat 으로 이동 |
| 3 | `/catalog?category=movecat` 조회 | 이동된 자산 노출 (신규 카탈로그에서 확인 가능) |
| 4 | 다중 ZIP + 폼 name 전송 | 폼 name 무시, 각 ZIP meta name 사용, 둘 다 요청 category 소속 |
| 5 | 폼 미전송(레거시 호출) 단일 ZIP 등록 | meta 기반 등록 (하위호환) |

## 실행
```bash
uv run python test/impl/48/test_asset_register_catalog.py
```
