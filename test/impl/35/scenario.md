# 시험 시나리오 — emb_ 규약 폐지 (§7.6.1-6, impl/37 · 물리 test/impl/35)

배경(PRD §7.6.1-6, SeCuardian PRD §20.4 연동, 사용자 오류 수정 요구 2026-07-09):
모든 패키지에서 **`emb_` prefix 제거**(emb_rag → rag 등) — `addon-agents/zip/` 6종
(marketplace·workflow·rag·playground·guardrails·server-shell) + `marketplace-assets/security/` 13종
rename(디렉터리·zip·내부 파일명·meta key), `scripts/seed_security.py` 블롭 경로 `{key}.zip` 동기.

| ID | 입력 | 기대 |
|----|------|------|
| TC-35-01 | zip/ 구조 | emb_* 0건 — marketplace·workflow·rag·playground·guardrails·server-shell + 템플릿 5종 + 순수 4종(무 prefix) |
| TC-35-02 | marketplace-assets/security/ | 13종(무 prefix) 디렉터리+zip, meta `key` == 디렉터리명 |
| TC-35-03 | `make seed-security`(격리 sqlite) | 자산 13종 + blob 13종 — filename `{key}.zip`, sha256 일치 |
| TC-35-04 | guardrails.zip | `guardrails-app.py` + `data/guardrails/*.json` 구조 보존 |
| TC-35-05 | 소스 grep | zip/·marketplace-assets/ 텍스트에 `emb_` 문자열 0건 |
| TC-35-06 | 회귀 | impl/34(개정판)·impl/1·impl/2 전건 PASS |
