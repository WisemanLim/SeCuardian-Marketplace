# 시험 결과 — dev-env 검증

- 날짜: 2026-07-08
- 판정: **PASS**

| # | 케이스 | 결과 |
|---|---|---|
| 1 | Python | ✅ 3.13.12 |
| 2 | uv | ✅ 0.10.9 |
| 3 | Node | ⚠→✅ `nvm install 22` → v22.23.1, default=22, `.nvmrc`=22 (셸 초기 20 감지, 신규 셸 22) |
| 4 | pnpm | ✅ corepack → 11.10.0 |
| 5 | Docker Compose | ✅ v2+ |
| 6 | 백엔드 부팅 | ✅ `import app.main` OK, routes 21 |
| 7 | 프론트 dev | ✅ pm2 `secmp-fe` online, `curl :4100` → HTTP 200 |
| 8 | DB 마이그레이션 | ✅ sqlite 01_init/02_seed 적용, 시드 에이전트 general/chat/marketplace/workflow |

## 이번 환경에서 해결한 이슈
- pnpm 11 `verifyDepsBeforeRun` 가 esbuild ignored-build 로 `pnpm dev` 사전검사 exit 1 → pm2 fe 크래시루프. `front/pnpm-workspace.yaml` `verifyDepsBeforeRun: false` 로 해결.
- `package.json` deprecated `pnpm.onlyBuiltDependencies` 필드 제거(WARN 소거).
