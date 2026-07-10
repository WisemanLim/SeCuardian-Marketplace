# 시험 결과 — impl/45 (물리 test/impl/43): §7.6.4-5·6 설치됨 탭 카테고리 그룹핑 + 해제 잔존 결함

- 날짜: 2026-07-10
- 판정: **PASS** (12/12)
- 실행: `uv run python test/impl/43/test_installed_grouping.py` (정적 + 로직 시뮬레이션 + dev DB 재현 확인)

| # | 케이스 | 결과 |
|---|---|---|
| A1 | 대소문자 무시 카탈로그 매칭 (`toLowerCase` 필터·맵) | ✅ 2건 |
| A2 | dev DB 결함 재현 데이터(usermanager config + UserManager 자산) 확인 | ✅ |
| B1 | 그룹 순서 — builtin 최우선 → security → utilities → general | ✅ 2건 |
| B2 | 설치됨 탭 `mp.cat.*` 헤더 + 그룹별 grid 렌더 | ✅ |
| B3 | 그룹 내 정렬(builtin=config 순서, 카탈로그 그룹=카탈로그 순) | ✅ |
| C1 | `mp.cat.builtin` 로케일 ko/en 패리티 | ✅ |
| D1 | 필터/그룹 로직 시뮬레이션 — 해제 숨김(대소문자 불일치 포함)·설치 표시·그룹 순서·builtin 순서 유지 | ✅ 4건 |
| — | `tsc --noEmit` | ✅ 0오류 |

## 회귀

impl/42·41·40·39·1 전부 OK. 이 중 impl/41(B1·B2)·impl/39(D2 mp.cat 키셋) 3건은 impl/45 가
사양을 개정(단일 그리드 정렬→카테고리 그룹핑, mp.cat 에 builtin 추가)하면서 **구세대 시험의
구현 세부 단정이 낡은 것** — 신 사양 기준으로 단정을 정정(코드 결함 아님, 주석 명기).

## 결함 원인 (사용자 보고: 해제해도 설치됨 탭 잔존)

addon upload 파이프라인이 config 키를 소문자화(`usermanager`)해 자산 키(`UserManager`)와
불일치 → 설치됨 탭 필터가 카탈로그 외(builtin)로 오분류해 항상 표시. 대소문자 무시 매칭으로 수정.
dev DB 의 `usermanager` config 행은 유지해도 무해(필터가 숨김) — 재설치 시 재사용된다.
