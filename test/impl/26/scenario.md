# 시험 시나리오 — impl/28(물리 test/impl/26): F-WF Dify DSL Import 어댑터(모드 A)

> 논리 순번은 impl/28(직전 impl/27=편집형 캔버스, 물리 test/impl/25). 물리 디렉터리는
> `test/impl/*` 자동증가값(26). PRD §7.2.2·§7.2.6 근거.

- 대상: `app/services/dify_dsl_adapter.py`(신규), `app/routers/router_workflow.py`
  (`import_dify_workflow`), `sql/{sqlite,pg}/01_init.sql`(`workflows.dify_dsl_source`/
  `dify_dsl_version`), `app/db.py`(컬럼 마이그레이션), 프론트 `WorkflowPage.tsx`
  (`DifyImportPanel`)·`api/workflow.ts`(`importDifyDsl`).

## 검증 항목

1. **노드 매핑 전종류** — 합성 Dify DSL 픽스처(start·llm·if-else·knowledge-retrieval·
   http-request·tool·answer·code·미인식 타입)를 가져와 §7.2.2 매핑표대로 변환되는지 확인:
   - `start→trigger`, `llm→llm`(prompt_template 에서 system/user 최선노력 추출),
     `if-else→condition`(comparison_operator→SeCMP op 매핑), `knowledge-retrieval→agent(rag)`,
     `http-request→http`(method 대문자화), `tool→agent`(agent_key 공란), `answer→notify`,
     **`code`(미지원)·미인식 타입 → `transform` 플레이스홀더**.
2. **엣지 매핑** — `sourceHandle: "true"/"false"` → SeCMP `when`, 그 외 무조건 엣지.
   **미존재 노드를 참조하는 엣지는 크래시 대신 skip + warnings 기록**.
3. **warnings 배열** — code/tool/knowledge-retrieval/미인식타입/스킵된엣지 전부 warnings 에 등장.
4. **항상 비활성 생성** — 가져온 워크플로우는 `enabled=false`(사람 검토 강제, §7.2.6).
5. **데이터 모델** — 응답에 `dify_dsl_version`(DSL `version:` 필드)·`dify_dsl_source`(원본 YAML)
   포함(스키마 컬럼 실존 확인 겸).
6. **RBAC** — user 권한 가져오기 시도 → 403.
7. **오류 처리** — 잘못된 YAML 문법 → 422(크래시 아님).
8. **관용적 파싱** — 노드 없는 빈 DSL 도 크래시 없이 201 + warnings 로 안내.
9. **실행 안전성(보너스)** — 가져온 워크플로우를 시험 내부에서 활성화 후 실행 시, 매핑이 불완전한
   노드(tool, agent_key 공란)가 있어도 **크래시 없이** `completed` 또는 `failed` 로 종료(500 없음).
10. **회귀** — 백엔드 스키마 변경(신규 컬럼)이 기존 워크플로우 CRUD/실행에 영향 없음
    (`test/impl/2`·`23`·`24` 재실행).
11. **프론트** — `tsc --noEmit`·`vite build` 0오류(완료), `DifyImportPanel` 정적 검증
    (impl/3·18·25 관례대로 브라우저 시험은 API 계약 시험으로 대체).

## 판정 기준
전 항목 PASS + test/impl/2·23·24 회귀 PASS.
