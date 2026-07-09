# 시험 결과 — impl/32(물리 test/impl/30): F-WF 풀스크린 워크플로우 빌더(§7.2.8)

- 날짜: 2026-07-09
- 판정: **PASS** (백엔드 17/17 + 프론트 tsc/build 0오류 + 회귀 3건 전건 PASS)
- 환경: fresh sqlite + FastAPI TestClient(`ENV=local`, `AGENT_STANDALONE=1`), 프론트 pnpm(vite 7 / tsc)

## A. 백엔드 — PATCH 부분 편집 (`test_workflow_builder_patch.py`) — 17/17 PASS

| # | 항목 | 결과 |
|---|---|---|
| 1 | `enabled` 단독 PATCH 하위호환 + version 불변 | PASS |
| 2 | `name`/`description` 부분 편집 — 미전달 필드 보존·version 불변 | PASS |
| 3 | `definition_json` 편집 왕복 일치 | PASS |
| 4 | 빌더 `position` 좌표 포함 왕복(스키마 없는 JSON 컬럼) | PASS |
| 3′ | definition 변경 시 **version +1** | PASS |
| 5 | 결합 PATCH(name+definition) | PASS |
| 6 | 미지원 노드 type → 422 / 유령 노드 엣지 → 422 / 이후 정의·version 불변 | PASS |
| 7 | 빈 바디 `{}` → 422 "no fields to update" | PASS |
| 8 | user role → 403, 미존재 id → 404 | PASS |
| 9 | 편집 후 run → completed, 노드 실행 순서 = 새 정의(trigger→llm→notify) | PASS |

## B. 프론트 — 정적 검증

- `npx tsc --noEmit` — **0 오류**.
- `npx vite build` — 성공(904KB 번들, 기존과 동일한 chunk 크기 경고만 — 코드 스플리팅은 로드맵).
- 수동 코드 체크(§7.2.8 설계 항목): 팔레트 HTML5 드래그(`application/secmp-workflow-node`
  전용 MIME, 외부 드롭 무시) + 클릭 삽입 병행(키보드 폴백), `screenToFlowPosition` 드롭 좌표,
  커스텀 노드(타입 색상 헤더·config 요약·trigger 는 target 핸들 없음), 인스펙터 타입별 폼
  (agent/llm/condition/http/notify + hitl/trigger/transform 안내) + JSON 폴백 + **엣지 `when`
  직접 편집**(§7.2.5 유보 해소), 노드 ID 변경 시 엣지 자동 리매핑·중복 ID 거부,
  자기참조/중복 엣지 방지, 신규(POST)/기존(:id, PATCH) 저장 분기, webhook 시크릿 1회 배너.

## C. 회귀 — 전건 PASS

| 시험 | 대상 | 결과 |
|---|---|---|
| test/impl/28 | enabled 토글(PATCH 스키마 확장 하위호환) | ALL PASS |
| test/impl/26 | Dify DSL Import | ALL PASS |
| test/impl/2 | 워크플로우 엔진 21케이스 | ALL PASS |

## 비고

- KWCAG 2.2: 빌더 캔버스는 마우스 중심(§7.2.5 원칙 승계) — 팔레트 클릭 삽입 + 인스펙터
  표준 label 폼 + 기존 `WorkflowPage` a11y 폼 편집기(신규 생성 경로) 병행 유지.
- 라이선스: Flowise(Apache-2.0)/Dify UX 패턴만 참조, 코드 복제 없음 — React Flow(MIT,
  `@xyflow/react` 12.11.2) 기반 자체 구현.
- 유보(로드맵, §7.2.8): undo/redo, 노드 그룹핑·복사/붙여넣기, 자동 레이아웃 버튼,
  실행 결과 캔버스 오버레이, 번들 코드 스플리팅.
