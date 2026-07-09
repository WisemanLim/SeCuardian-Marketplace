# 시험 결과 — impl/28(물리 test/impl/26): F-WF Dify DSL Import 어댑터(모드 A)

- 날짜: 2026-07-09
- 판정: **PASS** (30/30 assert)
- 환경: fresh sqlite temp DB, FastAPI TestClient, `SeCuardian-Marketplace/.venv`

## 실행 결과 (요약)
```
PASS user import -> 403 (403)
PASS invalid YAML -> 422 (422)
PASS full DSL import -> 201 (201)
PASS name mapped (Support Triage)
PASS imported workflow disabled by default (False)
PASS dify_dsl_version stored (0.1.0)
PASS dify_dsl_source stored (original YAML)
PASS start->trigger / llm->llm / if-else->condition / knowledge-retrieval->agent(rag) /
     http-request->http / tool->agent(blank) / answer->notify / code->transform /
     unrecognized->transform  — 전종류 매핑 확인
PASS missing-node edge skipped, 8 edges kept (8)
PASS true/false branch when preserved
PASS warnings 배열에 code/tool/knowledge-retrieval/미인식타입/댕글링엣지 전부 포함
PASS empty-graph DSL -> 201 no crash + warnings
PASS imported workflow runs without crash (201), terminal state reached (failed, no 500)

=== RESULT: ALL PASS
```

## 검증 항목
- §7.2.2 노드 매핑표(2026-07-08 Dify 공식문서 실측 근거) 전종류 구현 확인.
- **관용적 파싱**: 매핑 불가/미인식 노드는 크래시 대신 `transform` 플레이스홀더 + `warnings[]`.
  댕글링 엣지(존재하지 않는 노드 참조)도 크래시 대신 skip + 경고.
- **항상 비활성 생성**(`enabled=false`) — 사람 검토 강제(§7.2.6).
- 데이터 모델: `dify_dsl_source`(원본 YAML)·`dify_dsl_version`(DSL `version:`) 응답 확인.
- RBAC(user 거부)·YAML 문법 오류(422) 정상 처리.
- **실행 안전성(보너스)**: 매핑이 불완전한 노드(tool, agent_key 공란)를 포함해도 실제 DAG
  엔진으로 실행 시 500 크래시 없이 `completed`/`failed` 터미널 상태로 종료.

## 전체 회귀
- `test/impl/2` 21/21, `test/impl/23` 18/18, `test/impl/24` 15/15 PASS — 회귀 없음.
- 전체 impl/1~26 재실행 — 전부 PASS(신규 `workflows` 컬럼 2종 추가가 기존 CRUD/실행에 영향 없음).
- `ruff check app/ test/impl/26/` — 0 오류.
- 프론트 `tsc --noEmit`·`vite build` — 0 오류.

## 변경 요약
- 신규: `app/services/dify_dsl_adapter.py`(순수 매핑 함수, PyYAML — 기존 transitive 의존성 재사용,
  신규 설치 없음), `POST /api/workflows/import/dify-dsl`(router_workflow.py).
- 스키마: `workflows.dify_dsl_source`/`dify_dsl_version` 컬럼 — `sql/{sqlite,pg}/01_init.sql`(신규
  설치) + `app/db.py` 컬럼 마이그레이션(기존 설치, 멱등) 양쪽 반영.
- 프론트: `api/workflow.ts`(`importDifyDsl`), `WorkflowPage.tsx`(`DifyImportPanel` — YAML 붙여넣기+
  가져오기+warnings 표시).

## 미결/후속 (PRD §7.2.2·§7.2.6 유보)
- 모드 B(Delegate 실행)·모드 C(Round-trip) — 로드맵 그대로 유지.
- 파일 업로드(ZIP/멀티파트) 미지원 — 1차는 YAML 텍스트 붙여넣기만.
- 실제 Dify Studio 에서 export 한 YAML 로는 미검증(합성 픽스처 기준) — §7.2.2 전제대로 실제 도입 전
  대상 Dify 버전 고정·DSL 스키마 재검증 필요.
