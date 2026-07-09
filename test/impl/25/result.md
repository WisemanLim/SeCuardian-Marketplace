# 시험 결과 — impl/27(물리 test/impl/25): F-WF 편집형(드래그) 캔버스

- 날짜: 2026-07-09
- 판정: **PASS**
- 환경: 프론트 정적 검증(tsc/build) + 코드 리뷰 체크리스트 + 기존 백엔드 시험 회귀(백엔드 무변경)

## 실행 결과
```
$ pnpm exec tsc --noEmit          → 0 오류
$ pnpm exec vite build            → ✓ 2201 modules transformed, built in 1.27s (신규 오류 없음)
$ python test/impl/2/test_workflow.py             → ALL PASS (21/21)
$ python test/impl/23/test_workflow_components.py → ALL PASS (18/18)
$ python test/impl/24/test_workflow_webhook.py    → ALL PASS (15/15)
```

## 검증 항목 결과
| 항목 | 결과 |
|---|---|
| 정적 검증(tsc/build) | PASS |
| 읽기전용 하위호환(`onChange` 미전달) | PASS — `editable = !!onChange` 분기, `nodesDraggable/nodesConnectable/elementsSelectable` 모두 `editable` 종속 |
| 드래그 이동 → `position` 병합 | PASS — `applyNodeChanges` 결과를 `posById` 맵으로 상위 `nodes` 배열에 병합 |
| 연결 드래그 → 엣지 추가 | PASS — `onConnect` 이 `{source,target}` append |
| 삭제(노드/엣지) | PASS — `remove` 타입 감지, 노드 삭제 시 연결 엣지 동반 제거 |
| 엣지 식별자 안정성 | PASS — `edgeId` 합성키(source→target→when)로 인덱스 비의존 식별 |
| KWCAG 2.2 대체편집기 병행 | PASS — `WorkflowPage.tsx` 에서 `DefinitionEditor`·`WorkflowCanvas` 모두 동일 `setNodes`/`setEdges` 공유 |
| 회귀(백엔드 무변경) | PASS — test/impl/2·23·24 전항목 유지 |

## 변경 요약
- `WorkflowCanvas.tsx`: 읽기전용 시각화 → `onChange` prop 지정 시 편집형(드래그 이동·핸들 연결·Backspace/Delete 삭제) 승격. `http` 노드 색상 누락(impl/25 컴포넌트 팔레트에서 추가된 타입) 추가 보완.
- `WorkflowPage.tsx`: 캔버스에 `onChange={(n,e)=>{setNodes(n);setEdges(e);}}` 배선(폼 편집기와 동일 핸들러 공유), 안내 문구 갱신.
- `api/workflow.ts`: `WorkflowNode.position?: {x,y}` 선택적 필드 추가(백엔드 `definition_json` 은 스키마 없는 JSON 컬럼이라 무변경).

## 미결/후속 (PRD §7.2.5 유보)
- 캔버스에서 엣지 `when`(조건 분기) 값 직접 편집 UI 없음 — 폼 편집기에서 설정.
- 노드 리사이즈·그룹핑·undo/redo 미포함 — 로드맵.
- 중복 엣지·자기순환 연결에 대한 캔버스 측 방지 UX 없음(백엔드는 참조 무결성만 검증) — 필요 시 후속.
