# 시험 시나리오 — impl/41 (물리 test/impl/39): §7.6.2 자산 등록 UX 개선 + 카테고리 카탈로그

- 날짜: 2026-07-10
- 대상: `app/routers/router_marketplace.py`(asset_key 자동부여 + ZIP 다중 등록), `scripts/seed_assets.py`,
  프론트 `api/marketplace.ts`·`AgentsPage.tsx`(AssetRegisterModal)·`MarketplacePage.tsx`(카테고리 그룹), locales

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | `POST /api/marketplace/catalog` — asset_key 미지정, name="Security Utils" | 201, asset_key=`security-utils` 자동부여 |
| A2 | 동일 name 재등록(자동부여) | 201, asset_key=`security-utils-2` (충돌 접미) |
| A3 | 한글 name(슬러그 불가) | 201, asset_key=`asset`(폴백) 계열 |
| A4 | asset_key 명시 등록(하위호환) | 201, 지정 키 그대로 |
| A5 | asset_key 명시 중복 | 409 (기존 동작 회귀) |
| B1 | `POST /api/marketplace/catalog/zip` — 스캐폴드 ZIP 2개 동시 업로드 | 201, ZIP 별 meta.json 기반 자산 2건 등록(asset_key/name/version/description) |
| B2 | 동일 ZIP 재업로드 | 201, 중복 생성 없이 메타·블롭 갱신(멱등) |
| B3 | .zip 아닌 파일 | 400 |
| B4 | user 권한 | 403 (RBAC) |
| B5 | ZIP 등록 자산 install | 201 installed, `tbl_agent_config` upsert(agent_config_key) |
| C1 | `scripts/seed_assets.py` 실행(실 marketplace-assets 스캔) | utilities 6종 category=utilities 등록, security 13종 존재(중복 INSERT 없음) |
| C2 | seed_assets 재실행 | 멱등(기존 등록 스킵, 카운트 불변) |
| D1 | 프론트 `tsc --noEmit` | 0 오류 |
| D2 | locales ko/en 키 패리티(agent.assetNameRequired·assetKeyAuto·mp.cat.*) | 양측 존재 |

## 실행

```bash
uv run python test/impl/39/test_asset_register_ux.py   # 스크립트 실행 방식(impl/1 패턴)
cd front && pnpm exec tsc --noEmit
```
