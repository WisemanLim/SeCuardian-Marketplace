# 시험 시나리오 — Marketplace-host 공개 카탈로그 API (§7.3.5, impl/47 · 물리 test/impl/45)

배경(사용자 요구 2026-07-10, SeCuardian R21 상호 싱크): SeCuardian addon agent 배포 방식을
scaffold·zip·marketplace 3종으로 확장하기 위해, SeCMP 가 **host(레지스트리 서버)** 로서
카테고리별 자산 목록을 **설치유무 무관 전량** 제공해야 한다. 종전에는 remote **클라이언트**
(`/api/marketplace-remote`)만 있고 host 측 서빙 API 가 없었다.

대상: app/routers/router_marketplace_host.py(신규, `/api/marketplace-host` —
ping/catalog/catalog/{key}/download/{key}), app/core/config.py(`marketplace_host_api_key`),
app/main.py(라우터 등록), `.env.example`·`.env.{local,dev,staging,prod}`(`MARKETPLACE_HOST_API_KEY`).

| ID | 입력 | 기대 |
|----|------|------|
| TC-45-01 | `GET /ping` | `ok=true`, `service=SeCuardian-Marketplace`, categories = marketplace-assets/ 하위 디렉터리(addon·builtin·security·utilities), total = 전체 zip 수 |
| TC-45-02 | `GET /catalog` (필터 없음) | total == 파일시스템 zip 전량, groups 키 == categories, 대표 자산 4종(Board=addon·rag=builtin·agentic-soc=security·UserManager=utilities) 포함 — **DB(marketplace_installs/tbl_addon_agents) 미참조** = 설치유무 무관 |
| TC-45-03 | `GET /catalog?category=security` | security 그룹만 반환, 자산 수 == security/ 디렉터리 zip 수 |
| TC-45-04 | `GET /catalog/Board` 상세 | asset_key/category/version(meta)·`checksum` == 실 ZIP SHA256·`download_path=/download/Board`·다국어 names/descriptions dict |
| TC-45-05 | `GET /download/Board` | FileResponse 경로 == 실 zip 파일, 파일 바이트 SHA256 == 상세 checksum (mtime 캐시 일관성) |
| TC-45-06 | `MARKETPLACE_HOST_API_KEY` 설정 시 인증 | 헤더 없음/오류 키 → 401, `Bearer <키>` 일치 → 통과, 미설정 → 개방 |
| TC-45-07 | 경로 탐색/미존재 키 | `../etc`·`x/y` 형식 → 404(정규식 거부), 미존재 키 → 404 |
| TC-45-08 | 정적 검증 | main.py 라우터 등록, config `marketplace_host_api_key`, `.env.*` 5파일 `MARKETPLACE_HOST_API_KEY` 키(빈 값 + 인라인 주석 금지 — dotenv 파싱 결함 방지), ruff 0오류 |

실행: `uv run python test/impl/45/test_marketplace_host.py`
