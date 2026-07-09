# 시험 시나리오 — impl/27(물리 test/impl/25): F-WF 편집형(드래그) 캔버스

> 논리 순번은 impl/27(직전 impl/26=webhook 트리거, 물리 test/impl/24). 물리 디렉터리는
> `test/impl/*` 자동증가값(25). PRD §7.2.5 근거. **백엔드 변경 없음**(`definition_json` 이 스키마
> 없는 JSON 컬럼이라 `position` 필드 추가가 DB/검증 로직에 영향 없음) — 프론트 전용 변경이므로
> impl/3·8·12·18 관례대로 정적 검증(tsc/build) + 코드 리뷰 체크리스트로 시험한다.

- 대상: `front/src/pages/workflow/WorkflowCanvas.tsx`(재작성), `WorkflowPage.tsx`(onChange 배선),
  `front/src/api/workflow.ts`(`WorkflowNode.position` 필드 추가).

## 검증 항목

1. **정적 검증** — `tsc --noEmit` 0오류, `vite build` 성공(신규 오류 없음).
2. **읽기전용 하위호환** — `onChange` 미전달 시 기존과 동일하게 `nodesDraggable=false` 등 읽기전용
   동작 유지(코드 리뷰: `editable = !!onChange` 분기로 회귀 없음 확인).
3. **드래그 이동** — `onNodesChange` 의 `position` 타입 변경을 `applyNodeChanges` 로 반영 후
   해당 노드의 `position` 을 상위 `nodes` 배열에 병합(코드 리뷰: `posById` 맵 생성·병합 로직).
4. **연결 드래그** — `onConnect` 이 `{source, target}` 을 상위 `edges` 배열에 추가(간단 append,
   중복/자기순환 방지는 1차 미포함 — 필요 시 백엔드 `_validate_definition` 이 이미 unknown-node 참조는
   막고 자기순환은 DAG 실행기의 위상 처리(§7.2.1)에서 무한루프 없이 처리됨 확인은 test/impl/2 회귀 범위).
5. **삭제** — `onNodesChange`/`onEdgesChange` 의 `remove` 타입을 감지해 노드 삭제 시 연결된
   엣지까지 함께 제거(코드 리뷰: `removed` Set 필터링 로직).
6. **엣지 식별자 안정성** — `edgeId(e) = "${source}->${target}->${when??''}"` 합성키로 배열
   인덱스가 아닌 값 기반 식별 — 노드/엣지 배열이 재정렬돼도 삭제 대상이 어긋나지 않음.
7. **KWCAG 2.2** — 캔버스는 마우스 중심(대상 아님), `DefinitionEditor`(a11y 폼)가 동일
   `nodes`/`edges` 상태를 공유하는 대체편집기로 계속 병행(`WorkflowPage.tsx` 양쪽 다 동일
   `setNodes`/`setEdges` 핸들러 사용 확인).
8. **회귀** — 백엔드 무변경이므로 `test/impl/2`(21/21)·`test/impl/23`(18/18)·`test/impl/24`(15/15)
   재실행으로 사이드이펙트 없음 확인.

## 판정 기준
tsc/build 0오류 + 코드 리뷰 체크리스트 전항목 확인 + 기존 백엔드 시험 3종 회귀 PASS.
