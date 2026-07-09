# 시험 결과 — 에이전트 통합 관리 (§7.6.1, impl/36 · 물리 test/impl/34)

> **판정**: PASS (8/8 + 회귀 impl/1·impl/2 ALL PASS + tsc/build 0오류)
> **실행일**: 2026-07-09
> **환경**: macOS darwin 25.5.0 / local SQLite(격리 tmp DB) / uv + pytest / node(vite)

## 실행 명령

```bash
uv run pytest test/impl/34/ -q                       # → 8 passed
uv run python test/impl/1/test_marketplace.py        # → ALL PASS (F-MP 회귀)
uv run python test/impl/2/test_workflow.py           # → ALL PASS (F-WF 회귀)
cd front && npx tsc --noEmit && npm run build        # → 0오류, built
uv run ruff check app/routers/router_addon_agent.py scripts/seed.py scripts/seed_security.py test/impl/34/
# → All checks passed!
```

## 결과 상세

| ID | 판정 | 비고 |
|----|------|------|
| TC-34-01 | PASS | seed.py 기반 시드만 — security config 행 0 |
| TC-34-02 | PASS | marketplace_assets 13종(category=security) + blob 13종 sha256 일치, 2회 실행 멱등 |
| TC-34-03 | PASS | GET /catalog?category=security → 13종, installed=false, kind=agent |
| TC-34-04 | PASS | install/teler-ids 201 — config nav_group='marketplace' upsert, blob hot-deploy 호출(deploy_zip 모킹) |
| TC-34-05 | PASS | 자산 등록 + POST /catalog/{key}/zip 201, checksum·blob 저장 (zip 스캐폴드 등록 UI 백엔드 계약) |
| TC-34-06 | PASS | zip/ 에 보안 emb_ 13종 부재, marketplace-assets/security/ 13종(+zip), _templates=Board, 이동 템플릿 5종 zip/ |
| TC-34-07 | PASS | templates list 6종·download/UserManager 200·scaffold(rag) 200 — fallback |
| TC-34-08 | PASS | locales ko/en — agent.system/noSystem 제거, assetZip/assetZipHint 추가 |

## 실 DB 확인 (local.db)

```bash
make seed            # 기반 시드만
make seed-security   # → marketplace_assets 13 · marketplace_asset_blobs 13 확인
```

## 비고

- 프론트 통합 탭: `AgentsPage.tsx` Tab = `builtin | addon`, 기존 시스템 카드가 내장 탭에 합류,
  자산 카탈로그(`MarketplacePage`)·'자산 등록' 버튼도 내장 탭으로 이동. Addon 탭 무변경.
- 자산 등록 모달에 addon ZIP 첨부(선택) 입력 추가 — `uploadAssetZip()` 신설(`api/marketplace.ts`).
