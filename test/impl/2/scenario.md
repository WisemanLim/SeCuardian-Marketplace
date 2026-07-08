# 시험 시나리오 — impl/2: F-WF (Workflow) 백엔드

- 날짜: 2026-07-08
- 대상: Workflow DAG 엔진 (F-WF, PRD §7.2) — v0 ORM→raw-SQL 이식
- 실행: `PYTHONPATH=. python test/impl/2/test_workflow.py` (fresh sqlite, FastAPI TestClient)

## 범위
- DDL: `workflows`·`workflow_runs`·`workflow_node_runs` (sqlite+pg, `tenant_id` 선반영)
- `app/services/workflow_engine.py` — async DAG 실행기(topo fire/prune, retry, HITL, 템플릿/`$ref` 해석)
- `app/routers/router_workflow.py` — CRUD + run + nodes + hitl + cancel + SSE stream
- 노드 7종: trigger/agent/llm/condition/hitl/transform/notify
- `tbl_agent_config` `workflow` 시드

## 시험 케이스 (Given-When-Then)
| # | 케이스 | 기대 |
|---|---|---|
| 0 | `workflow` 에이전트 시드 | agent-config 에 포함 |
| 1 | user 워크플로우 생성 | 403 |
| 2 | 잘못된 node type | 422 |
| 3 | edge 미존재 노드 참조 | 422 |
| 4 | 선형 trigger→transform→notify + `$ref`/`{{템플릿}}` | completed, transform `msg=world`, notify `hi world` |
| 5 | condition 분기(n>5, true) | completed, true 분기 fire·false prune, lo 노드런 없음 |
| 6 | condition 분기(n=1, false) | lo fire·hi prune |
| 7 | HITL 일시정지 | `waiting_hitl`, waiting_node_id=h |
| 8 | user HITL 승인 | 403 |
| 9 | HITL 승인 재개 | completed |
| 10 | HITL 거부 | failed |
| 11 | agent 노드(chat, 활성) | completed, invoked=true |
| 12 | agent 노드(미존재) | run failed, 노드 attempts=4(retry 소진) |
| 13 | 대기 run 취소 | cancelled |
| 14 | 무토큰 | 401/403 |

## 판정 기준
- 21개 assert 전부 PASS = PASS. `ruff check` 신규파일 0 오류.
