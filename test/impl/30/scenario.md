# 시험 시나리오 — impl/32(물리 test/impl/30): F-WF 풀스크린 워크플로우 빌더(§7.2.8)

> 논리 순번은 impl/32(직전 impl/31=pgvector 실측, 물리 test/impl/29). 물리 디렉터리는
> `test/impl/*` 자동증가값(30). PRD §7.2.8 근거 — impl/27 미니 캔버스 "실사용 불가" 피드백
> (2026-07-09) 접수 후 Flowise/Dify 준용 3분할 빌더(팔레트 drag&drop → 캔버스 → 인스펙터)로
> 재구현. **코드 복제 없음**(React Flow MIT 자체 구현, 상용/추가조건 라이선스 구성요소 제외).

- 대상(백엔드): `app/routers/router_workflow.py` — `PATCH /api/workflows/{id}` 부분 편집 확장
  (`enabled`/`name`/`description`/`definition_json`, definition 변경 시 `version` +1,
  `{"enabled"}` 단독 하위호환).
- 대상(프론트): `front/src/pages/workflow/WorkflowBuilderPage.tsx`(신규),
  `front/src/api/workflow.ts`(`updateWorkflow`), `front/src/App.tsx`(`/workflow/builder(/:id)`),
  `front/src/pages/workflow/WorkflowPage.tsx`(빌더 진입 버튼).

## 검증 항목

### A. 백엔드 — PATCH 부분 편집 (`test_workflow_builder_patch.py`)
1. `enabled` 단독 PATCH 하위호환(impl/30 동작 유지, version 불변).
2. `name`/`description` 부분 편집 — 미전달 필드 보존, version 불변.
3. `definition_json` 편집 — 저장 후 재조회 일치 + **version +1**.
4. `definition_json` 에 빌더 `position` 좌표 포함 시 그대로 왕복(스키마 없는 JSON 컬럼).
5. 결합 PATCH(name+definition) — 두 필드 반영 + version +1.
6. 잘못된 definition(미지원 type / 미지정 엣지 참조) → 422, 기존 정의·version 불변.
7. 빈 바디 `{}` → 422 "no fields to update".
8. RBAC: user role → 403. 미존재 id → 404.
9. 편집 후 run 정상 동작(새 정의 기준으로 실행).

### B. 프론트 — 정적 검증
10. `tsc --noEmit` 0 오류.
11. `vite build` 성공.
12. 빌더 코드 리뷰 체크(수동): 팔레트 HTML5 드래그(`application/secmp-workflow-node`) +
    클릭 삽입 병행(키보드 폴백), `screenToFlowPosition` 드롭 좌표, 커스텀 노드(타입 색상·요약),
    인스펙터 타입별 폼 + JSON 폴백 + 엣지 `when` 편집(§7.2.5 유보 해소), 신규/기존(:id) 저장 분기.

### C. 회귀
13. 기존 test/impl/28(enabled 토글) 재실행 — PATCH 스키마 확장(전 필드 optional)이
    기존 `{"enabled": bool}` 호출을 깨지 않음.
14. 기존 test/impl/2(엔진 21케이스)·26(dify import) 재실행 무영향.
