# 시험 시나리오 — impl/18: F-WF React Flow 캔버스 (E3 확장, PRD §7.11)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "F-WF React Flow 캔버스". a11y 폼 편집기(1차)에 DAG 시각화 캔버스 추가.
- 실행: 프론트 tsc/build (순수 프론트, 백엔드 무관).

## 범위
- `@xyflow/react` 설치(승인됨).
- `WorkflowCanvas.tsx` — nodes/edges 를 위상 깊이별 좌→우 배치 렌더. 타입별 색상, 엣지 화살표+when, Background/Controls/MiniMap. 읽기전용.
- `WorkflowPage` 생성폼에 "DAG 미리보기" 통합.

## 설계
- a11y 폼 편집기(PRD §7.11 KWCAG 하드요구)가 1차 편집수단 유지 — 캔버스는 읽기전용 시각화 보조(접근성 회귀 없음).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | @xyflow/react 설치 | 의존성 등록 |
| 2 | tsc --noEmit | 0 오류 |
| 3 | vite build | 성공(2201 modules) |

## 판정 기준
- tsc/build 0오류 = PASS(백엔드 무변경).
