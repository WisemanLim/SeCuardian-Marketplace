# 시험 결과 — impl/46 (물리 test/impl/44): 다국어 언어셋 dict 일원화 + UserManager 중복 결함

- 날짜: 2026-07-10
- 판정: **PASS** (18/18)

## 실행

```bash
uv run python test/impl/44/test_i18n_langmap.py   # 18/18 PASS
cd front && pnpm exec tsc --noEmit                # 0오류 (SeCuardian front 도 0오류)
```

| # | 케이스 | 결과 |
|---|---|---|
| A1 | meta.json 전수(29종) display_name·description dict ko/en | ✅ bad=0 |
| A2 | zip 재빌드 반영 (zip 내 meta = 디렉터리 meta) | ✅ mismatch=0 |
| B1 | `norm_descriptions` — dict 형·레거시 split·display_name dict | ✅ 3케이스 |
| B2 | `parse_lang_map`/`lang_json` 왕복 + repr 오염 문자열 안전 | ✅ |
| B3 | `_parse_zip_meta`(UserManager.zip) — 소문자 키·ko/en·dict | ✅ key=usermanager |
| C1 | dev DB raw dict repr 잔존 | ✅ 0건 (복구 전 board·usermanager 2건 → 복구) |
| C2 | dev DB asset_key 소문자 통일 | ✅ 0건 (UserManager→usermanager 정규화) |
| C3 | config 대소문자 중복 (usermanager 단일행) | ✅ dups=0 (기존 UserManager 행 제거) |
| C4 | 자산 20종 names/descriptions ko+en | ✅ bad=0 |
| D1 | GET /api/marketplace/catalog — names/descriptions JSON·repr 누출 없음 | ✅ 20종 |
| D2 | GET /api/agent-config/ — builtin 7종 agent_names/descriptions ko/en | ✅ |
| E1 | install seam — cfg_key 소문자 + dict 전파 | ✅ |
| F1 | `tsc --noEmit` (Marketplace·SeCuardian) | ✅ 0오류 |
| F2 | locales ko/en `assetNameEn`/`assetDescEn` 패리티 | ✅ |
| G1 | SeCuardian addon-agents/zip 13종 meta·zip 동기 | ✅ diff=0 |
| G2 | SeCuardian tbl_agent_config agent_names/descriptions ko/en | ✅ general·chat·보안13종 |

## 수정 요약 (RCA → Fix)

| 결함 | 원인 | 수정 |
|---|---|---|
| 카탈로그 카드 `{'ko': …}` raw repr 노출 | `seed_assets.py`·`_parse_zip_meta` 가 `str(meta["description"])` | 공통함수 `app/core/i18n.norm_descriptions` 로 정규화 후 저장, 기존 오염 행은 `_repair_dict_repr_rows` 로 멱등 복구 |
| 언어 전환해도 카탈로그 설명 ko 고정 | marketplace_assets 에 en 설명 저장 위치 없음 | `names`/`descriptions` **JSON dict 컬럼** 추가 (split 컬럼 금지 — 언어 확장 시 데이터만 추가) + 프론트 `parseLangMap`+`pickDescription` 공통 체인 |
| 설치됨 탭 UserManager 2중 카드 | install seam 은 "UserManager"(원형)·addon 배포는 "usermanager"(소문자)로 config 2행 | asset_key·cfg_key 소문자 통일 + `_normalize_legacy_keys` 멱등 정규화(중복 행 제거, installs·blobs 키 동기, 빈 nav_group 복구) |
| meta.json 23종 plain 문자열/누락 | 초기 작성 형식 불일치 | 전 자산(builtin 5·security 13·utilities 5 + 기존 dict 6) `display_name`/`description` = `{"ko":…, "en":…}` 통일, zip 재빌드 |
| SeCuardian 미반영 | — | `app/core/i18n.py`·`front/src/store/locale.ts` 동기, `seed_security.py` 에 agent_names JSON 저자 추가, `addon-agents/zip` 13종 meta+zip 복제, dev DB 시드 적용 |

## 비고

- `make test`(uv run pytest)는 **기존** `test/impl/1/test_marketplace.py` 가 import 시
  `sys.exit()` 하는 스크립트형이라 pytest 수집 단계에서 INTERNALERROR — 본 변경과 무관한
  기존 이슈 (해당 스크립트 자체 검증은 exit 0 = PASS). 차수별 스크립트 직접 실행이 현행 규약.
- `ruff check` 잔여: `app/main.py` E402(기존), SeCuardian `router_ai_eval.py` F401(기존) — 미수정 파일.
- 언어 확장 절차(신규): meta.json `display_name`/`description` 에 `"jp": "…"` 키만 추가
  → seed/업로드 → UI 는 `pickDescription` fallback 체인으로 자동 반영 (코드 수정 불필요).
