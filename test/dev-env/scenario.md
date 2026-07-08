# 시험 시나리오 — dev-env 검증 (최초 1회)

- 날짜: 2026-07-08
- 목적: 표준 개발환경(런타임·도구·부팅·프론트) 정상성 확인 후 구현 진행.
- 프로파일: python-fastapi × ict-saas(govtech·security 오버레이)

## 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | Python 런타임 | 3.11+ (`uv` 관리) |
| 2 | uv | 설치됨 |
| 3 | Node | 22+ (`.nvmrc`=22) |
| 4 | pnpm | 9+ (corepack) |
| 5 | Docker Compose | v2+ |
| 6 | 백엔드 부팅 | `import app.main` 성공, 라우터 노출 |
| 7 | 프론트 dev | vite :4100 응답(HTTP 200) |
| 8 | DB 마이그레이션 | sqlite 01_init/02_seed 적용, 기본 에이전트 시드 |
