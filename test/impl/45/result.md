# 시험 결과 — Marketplace-host 공개 카탈로그 API (§7.3.5, impl/47 · 물리 test/impl/45)

- 실행일: 2026-07-10
- 명령: `uv run python test/impl/45/test_marketplace_host.py`
- 판정: **PASS (34/34)**

| ID | 결과 | 비고 |
|----|------|------|
| TC-45-01 | ✅ PASS (3) | ping ok, categories 4종(addon·builtin·security·utilities), total 29 |
| TC-45-02 | ✅ PASS (7) | 전량 29종 == 파일시스템, groups==categories, 대표 4종 카테고리 일치, DB 미참조(설치유무 무관) |
| TC-45-03 | ✅ PASS (2) | security 필터 → 13종만 |
| TC-45-04 | ✅ PASS (4) | Board 상세 — checksum==실 ZIP SHA256, download_path, 다국어 names dict |
| TC-45-05 | ✅ PASS (2) | download FileResponse == 실 zip, 바이트 SHA256 == checksum |
| TC-45-06 | ✅ PASS (4) | 키 설정 시: 무헤더/오류키 401·일치 통과, 미설정 개방 |
| TC-45-07 | ✅ PASS (5) | `../etc`·`a/b`·`..`·`.hidden`·미존재 → 404 |
| TC-45-08 | ✅ PASS (7) | main.py 배선, config 필드, `.env.*` 5파일 키(빈 값 인라인 주석 금지 형식) |

## 시험 중 발견·수정

1. **`.env` 빈 값 + 인라인 주석 파싱 결함(구현 반영)** — python-dotenv 는 `KEY=   # 주석` 형식에서
   빈 값일 때 주석 텍스트를 값으로 파싱한다. 신규 `MARKETPLACE_*` 빈 값 키의 인라인 주석을
   윗줄 주석으로 이동(SeCuardian `.env.*` 포함 양 저장소 동일 적용).
2. 시나리오 스크립트 자체 결함 2건 수정 — ① DB 미참조 검사가 독스트링 문구에 오탐 →
   `from app.db`/`fetch_` import 부재 검사로 교체 ② `\s+` 가 re.M 에서 개행을 넘어 다음 섹션
   주석까지 매칭 → `[ \t]+` 로 한정.

## 부가 확인

- `.env.local`/`.env.prod` — `MARKETPLACE_HOST_API_KEY` 임의 발급 키(openssl rand -hex 32) 설정,
  SeCuardian `.env.local`/`.env.prod` 의 `MARKETPLACE_API_KEY` 와 페어 일치 확인.
- ruff: `router_marketplace_host.py`·`config.py` 0오류 (main.py E402 는 기존 이슈).
- 클라이언트 측 시험: SeCuardian `test/impl/61` (R21) 참조.
