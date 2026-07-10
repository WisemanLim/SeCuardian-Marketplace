# 시험 결과 — impl/41 (물리 test/impl/39): §7.6.2 자산 등록 UX 개선 + 카테고리 카탈로그

- 날짜: 2026-07-10
- 판정: **PASS** (25/25)
- 실행: `uv run python test/impl/39/test_asset_register_ux.py` (격리 sqlite + TestClient)

| # | 케이스 | 결과 |
|---|---|---|
| A1 | asset_key 자동부여 (name="Security Utils" → `security-utils`) | ✅ 201 |
| A2 | 자동부여 충돌 접미 (`security-utils-2`) | ✅ |
| A3 | 비ASCII name → `asset` 폴백 슬러그 | ✅ |
| A4 | asset_key 명시 등록(하위호환) | ✅ |
| A5 | 명시 중복 → 409 (회귀) | ✅ |
| B1 | ZIP 2개 동시 등록 — meta.json 기반 key/name/version/checksum | ✅ 201, 4건 검증 |
| B2 | 동일 ZIP 재업로드 멱등(중복 행 없음, description 갱신) | ✅ |
| B3 | 비 ZIP → 400 | ✅ |
| B4 | user 권한 → 403 | ✅ |
| B5 | ZIP 등록 자산 install → installed + agent_config upsert | ✅ (스텁 zip 이라 deployed=false — 설계상 배포 실패는 설치 기록 무효화 안 함) |
| C1 | seed_assets — utilities 6종(category=utilities)·security 13종 | ✅ |
| C2 | seed_assets 재실행 멱등 (총 25 == 25) | ✅ |
| D1 | 프론트 `tsc --noEmit` | ✅ 0오류 |
| D2 | locales ko/en 키 패리티(신규 4키 + legacy `assetKeyNameRequired` 제거) | ✅ |

## 회귀

| 시험 | 결과 |
|---|---|
| test/impl/1/test_marketplace.py (F-MP CRUD·설치 수명주기) | ✅ ALL PASS |
| test/impl/34/test_unified_agent_mgmt.py (§7.6.1 탭 통합) | ✅ exit 0 |
| test/impl/36/test_asset_reorg.py (§7.6.1-7 자산 디렉터리) | ✅ exit 0 |

## 비고

- `uv run pytest`(전체 수집)는 **기존부터** `test/impl/1` 등 스크립트형 시험의 module-level
  `sys.exit` 로 collection INTERNALERROR — 본 변경과 무관(스크립트 개별 실행이 표준 방식).
- `ruff check` 통과, 백엔드 `import app.routers.router_marketplace` OK.
