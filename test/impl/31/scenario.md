# 시험 시나리오 — SeCuardian impl/55 복제 싱크 (다국어 구조 + Local LLM 다양화) (impl/31)

배경: SeCuardian 의 R18-7(에이전트 설명 다국어 확장 구조 — `descriptions` JSON + 선호언어)
및 R19(Local LLM 다양화 — Ollama/llama.cpp/vLLM provider 추상화·LLM Route·Metering·Token 압축)
구현(SeCuardian test/impl/55, 10/10 PASS)을 **코드 복제**로 SeCMP 에 싱크.
동일 파일 13종+신규 6종 복사, 분기 파일 11종 patch 적용, main.py 3개소 수동 병합,
`_templates` 6종 meta dict 형 + zip 재패키징 동기.

시험 DB: 격리 sqlite (`mp31.db`) — local.db 무변경.

| ID | 입력 | 기대 |
|----|------|------|
| TC-31-01 | 서버 기동 (마이그레이션+백필) | descriptions·preferred_lang 컬럼, tbl_llm_usage 생성 |
| TC-31-02 | GET /api/agent-config/ | 전 에이전트 `descriptions` dict 반환 |
| TC-31-03 | PATCH/GET /api/auth/me preferred_lang | `en` 저장·반영 |
| TC-31-04 | GET /api/llm/models | local 옵션(value=`ollama`) 반환 |
| TC-31-05 | PUT /api/llm/routes → GET /api/llm/usage | 라우팅 저장 200, 사용량 집계 응답 정상 |
| TC-31-06 | 정적 검증 | `app.main` import OK, ruff 신규 오류 0, front `tsc --noEmit` PASS, compose config OK |
