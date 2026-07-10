# 시험 시나리오 — impl/46 (물리 test/impl/44): 다국어 언어셋 dict 일원화 + UserManager 중복 결함

- 날짜: 2026-07-10
- 대상: 전 자산 meta.json ko/en dict 통일, `app/core/i18n.py` 공통 파서 신설,
  marketplace_assets `names/descriptions` JSON 컬럼, 카탈로그 카드 다국어 렌더,
  asset_key 소문자 통일(설치됨 탭 UserManager 이중 노출 해소), SeCuardian 복제.

## 배경 결함

1. meta.json 23종이 plain 문자열(ko 단일) — display_name 누락 다수.
2. `seed_assets.py`·`_parse_zip_meta` 가 `str(dict)` 저장 → 카탈로그 카드에
   `{'ko': …, 'en': …}` raw repr 노출 (UserManager·board).
3. marketplace_assets 에 en 설명 저장 위치 없음 → 언어 전환해도 카드 설명 ko 고정.
4. install seam 은 asset_key 원형("UserManager")·addon 배포는 소문자("usermanager")로
   tbl_agent_config 에 2행 생성 → 에이전트(설치됨) 탭 중복 카드.
5. 설계 원칙: 언어 확장(jp/ch/…) 시 **코드 수정 없이 데이터만 추가** —
   split 컬럼(description_en …) authoring 금지, `{"ko":…, "en":…}` JSON dict + 공통 파서.

## 케이스

| # | 케이스 | 기대 |
|---|---|---|
| A1 | meta.json 전수(29종) display_name·description | dict 형 + ko/en 모두 비어있지 않음 |
| A2 | zip 재빌드 반영 | zip 내 meta 와 디렉터리 meta 동일 |
| B1 | `norm_descriptions` 단위 | dict 형·레거시(split)·혼합 입력 모두 {ko,en,…} 정규화 |
| B2 | `parse_lang_map`/`lang_json` 왕복 | JSON TEXT ↔ dict 왕복, 오염 문자열('{'…repr) 안전 |
| B3 | `_parse_zip_meta` (UserManager.zip) | asset_key 소문자, name=ko, name_en=en, names/descriptions dict |
| C1 | dev DB: raw dict repr 잔존 | marketplace_assets·tbl_agent_config 0건 |
| C2 | dev DB: asset_key 소문자 통일 | 대문자 포함 키 0건 |
| C3 | dev DB: config 대소문자 중복 | LOWER(agent_key) 그룹 중복 0건 (usermanager 단일행) |
| C4 | dev DB: names/descriptions JSON | security·utilities 자산 전수 ko+en 보유 |
| D1 | GET /api/marketplace/catalog (in-proc) | 각 자산에 names/descriptions JSON 포함, repr 노출 없음 |
| D2 | GET /api/agent-config/ (in-proc) | descriptions/agent_names dict 확장 반환 (builtin 7종 ko/en) |
| E1 | install seam 로직 시뮬레이션 | cfg_key=소문자, agent_names/descriptions JSON 전파 |
| F1 | 프론트 `tsc --noEmit` (양 저장소) | 0오류 |
| F2 | locales ko/en 패리티 | agent.assetNameEn·agent.assetDescEn 양측 존재 |
| G1 | SeCuardian 복제 검증 | addon-agents/zip 13종 meta = marketplace-assets/security meta, zip 갱신 |
| G2 | SeCuardian seed_security | tbl_agent_config agent_names/descriptions ko/en (13종+general/chat) |

## 실행

```bash
uv run python test/impl/44/test_i18n_langmap.py
cd front && pnpm exec tsc --noEmit
```
